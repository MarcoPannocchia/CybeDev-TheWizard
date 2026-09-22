import os
import time
import asyncio
import json
import asyncpg


# ════════════════════════════════════════════════════════════════════════
# CONNECTION / POOL MANAGEMENT
# ════════════════════════════════════════════════════════════════════════
#
# asyncpg is fully async end-to-end: socket I/O, wire-protocol parsing and
# query execution all yield to the event loop instead of blocking it --
# unlike psycopg2, which is sync and would need asyncio.to_thread (the way
# Socket_Port_Scanner is wrapped in ModulesTheWidzard_v082.py) to avoid
# freezing the loop.
#
# What can still slow things down even with asyncpg:
#   - Pool exhaustion: pool.acquire() awaits until a connection is free.
#     If a scan fans out many concurrent DB calls at once, a small pool
#     serializes them -- not a blocked loop, but a self-imposed rate cap.
#     Size WIZARD_DB_POOL_MAX to the expected concurrency.
#   - Holding a connection across an unrelated await (e.g. an aiohttp
#     call inside the same transaction) locks it away from every other
#     concurrent task for that whole duration.
#   - Large result sets: decoding a big fetch() is CPU-bound Python/C
#     work on the loop thread -- not a blocking syscall, but it still
#     consumes time other scheduled tasks are waiting on.
#   - Row-by-row writes: many individual execute() calls means many
#     network round-trips; use executemany() or bulk inserts instead
#     (see add_words_bulk below).
#
# Call init_pool() once, early (e.g. before Cast_Spell starts), rather
# than lazily on first use -- DNS resolution and the TLS handshake add
# real wall-clock latency to the first connect.

_pool: asyncpg.Pool | None = None


def _env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"[DB CONFIG ERROR] required environment variable {name} is not set")
    return value


async def _init_connection(conn):
    # asyncpg does not decode json/jsonb columns on its own -- without this
    # codec, every JSONB column (wizard_metadata.metadata,
    # wizard_zap_alerts.raw, wizard_k6_configs.config) comes back as a raw
    # JSON string instead of a dict/list, breaking every caller that reads
    # it as one (e.g. get_metadata()[0]["metadata"]["Author"]).
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
    )


async def init_pool():
    """Create (once) and return the shared connection pool. Idempotent."""
    global _pool
    if _pool is not None:
        return _pool

    ssl_mode = _env("WIZARD_DB_SSL", "require")  # "require" | "disable"

    try:
        _pool = await asyncpg.create_pool(
            host=_env("WIZARD_DB_HOST", "localhost"),
            port=int(_env("WIZARD_DB_PORT", "5432")),
            database=_env("WIZARD_DB_NAME", required=True),
            user=_env("WIZARD_DB_USER", required=True),
            password=_env("WIZARD_DB_PASSWORD", required=True),
            ssl=None if ssl_mode == "disable" else ssl_mode,
            min_size=int(_env("WIZARD_DB_POOL_MIN", "1")),
            max_size=int(_env("WIZARD_DB_POOL_MAX", "10")),
            command_timeout=int(_env("WIZARD_DB_TIMEOUT", "10")),
            init=_init_connection,
        )
    except asyncpg.PostgresError as e:
        print(f"[DB ERROR] Could not create connection pool: {e}")
        raise

    await _init_schema(_pool)
    return _pool


async def close_pool():
    """Close the shared pool. Call once at process shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# ════════════════════════════════════════════════════════════════════════
# SCHEMA
# ════════════════════════════════════════════════════════════════════════
# Additive by design: append new CREATE TABLE statements to
# _SCHEMA_STATEMENTS instead of altering the existing ones, so old rows
# and old code paths keep working when a new table is added later (e.g.
# persisted scan results/history).

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS wizard_wordlist (
        id      SERIAL PRIMARY KEY,
        word    TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_security_headers (
        id      SERIAL PRIMARY KEY,
        header  TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_urls (
        id      SERIAL PRIMARY KEY,
        url     TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_emails (
        id              SERIAL PRIMARY KEY,
        target          TEXT NOT NULL,
        email           TEXT NOT NULL,
        discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (target, email)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_metadata (
        id              SERIAL PRIMARY KEY,
        target          TEXT NOT NULL,
        source_url      TEXT NOT NULL,
        file_type       TEXT NOT NULL,
        metadata        JSONB NOT NULL,
        discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (target, source_url)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_k6_configs (
        id              SERIAL PRIMARY KEY,
        target          TEXT NOT NULL,
        config          JSONB NOT NULL,
        script          TEXT NOT NULL,
        created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_zap_alerts (
        id              SERIAL PRIMARY KEY,
        target          TEXT NOT NULL,
        url             TEXT NOT NULL,
        risk            TEXT NOT NULL,
        alert_name      TEXT NOT NULL,
        description     TEXT,
        raw             JSONB NOT NULL,
        discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS wizard_arp_hosts (
        id              SERIAL PRIMARY KEY,
        subnet          TEXT NOT NULL,
        ip              TEXT NOT NULL,
        mac             TEXT NOT NULL,
        vendor          TEXT,
        discovered_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (subnet, ip, mac)
    )
    """,
)


async def _init_schema(pool):
    async with pool.acquire() as conn:
        async with conn.transaction():
            for statement in _SCHEMA_STATEMENTS:
                await conn.execute(statement)


# ════════════════════════════════════════════════════════════════════════
# GENERIC LIST TABLE ACCESS
# ════════════════════════════════════════════════════════════════════════
# wordlist, security_headers and urls all share the same shape: an id and
# one unique text column. Table/column names are looked up from this
# fixed, hardcoded whitelist rather than ever being built from caller
# input -- parameterized queries ($1, $2, ...) only protect *values*, not
# identifiers, so every identifier used below comes from this dict, never
# from an argument.

_LIST_TABLES = {
    "wordlist": ("wizard_wordlist", "word"),
    "security_headers": ("wizard_security_headers", "header"),
    "urls": ("wizard_urls", "url"),
}


async def _get_list(pool, list_name):
    table, column = _LIST_TABLES[list_name]
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT {column} FROM {table} ORDER BY id")
    return [row[column] for row in rows]


async def _add_to_list(pool, list_name, value):
    table, column = _LIST_TABLES[list_name]
    async with pool.acquire() as conn:
        await conn.execute(
            f"INSERT INTO {table} ({column}) VALUES ($1) ON CONFLICT ({column}) DO NOTHING",
            value,
        )


async def _add_many_to_list(pool, list_name, values):
    """Bulk insert -- one round-trip instead of one execute() per value."""
    table, column = _LIST_TABLES[list_name]
    async with pool.acquire() as conn:
        await conn.executemany(
            f"INSERT INTO {table} ({column}) VALUES ($1) ON CONFLICT ({column}) DO NOTHING",
            [(v,) for v in values],
        )


async def _remove_from_list(pool, list_name, value):
    table, column = _LIST_TABLES[list_name]
    async with pool.acquire() as conn:
        await conn.execute(f"DELETE FROM {table} WHERE {column} = $1", value)


# ────────────────────────────────────────────────────────────────────────
# Public, purpose-named wrappers -- these are what
# ModulesTheWidzard_v082.py / TheWizard_v082.py should actually call.

async def get_wordlist(pool):
    return await _get_list(pool, "wordlist")

async def add_word(pool, word):
    await _add_to_list(pool, "wordlist", word)

async def add_words_bulk(pool, words):
    await _add_many_to_list(pool, "wordlist", words)

async def remove_word(pool, word):
    await _remove_from_list(pool, "wordlist", word)


async def get_security_headers(pool):
    return await _get_list(pool, "security_headers")

async def add_security_header(pool, header):
    await _add_to_list(pool, "security_headers", header)

async def remove_security_header(pool, header):
    await _remove_from_list(pool, "security_headers", header)


async def get_urls(pool):
    return await _get_list(pool, "urls")

async def add_url(pool, url):
    await _add_to_list(pool, "urls", url)

async def remove_url(pool, url):
    await _remove_from_list(pool, "urls", url)


_load_lock = asyncio.Lock()
_last_load_at = 0.0
_last_load_result = None


async def load_config_lists(pool, cooldown=None):
    """Fetch all three config lists in one call, e.g. to seed TheWizard's
    class attributes at startup instead of the hardcoded lists.

    Rate-limited: this is "the database loading point" -- a caller (e.g. a
    future UI re-loading state, or a retry loop) that calls this repeatedly
    within `cooldown` seconds gets back the last result instead of hitting
    Postgres again. Override the default via WIZARD_DB_LOAD_COOLDOWN.
    """
    global _last_load_at, _last_load_result
    if cooldown is None:
        cooldown = float(_env("WIZARD_DB_LOAD_COOLDOWN", "2"))

    async with _load_lock:
        now = time.monotonic()
        if _last_load_result is not None and (now - _last_load_at) < cooldown:
            return _last_load_result

        result = {
            "wordlist": await get_wordlist(pool),
            "security_headers": await get_security_headers(pool),
            "urls": await get_urls(pool),
        }
        _last_load_result = result
        _last_load_at = now
        return result


# ════════════════════════════════════════════════════════════════════════
# FINDINGS: emails, document metadata, k6 configs
# ════════════════════════════════════════════════════════════════════════
# Unlike the config lists above, these tables hold scan *output* keyed by
# the target that produced them. Table names are again a hardcoded
# whitelist (_FINDINGS_TABLES), never caller-controlled.

_FINDINGS_TABLES = ("wizard_emails", "wizard_metadata", "wizard_k6_configs", "wizard_zap_alerts")


async def save_email(pool, target, email):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO wizard_emails (target, email) VALUES ($1, $2) "
            "ON CONFLICT (target, email) DO NOTHING",
            target, email,
        )


async def save_emails_bulk(pool, target, emails):
    """Bulk insert -- one round-trip instead of one execute() per email."""
    if not emails:
        return
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO wizard_emails (target, email) VALUES ($1, $2) "
            "ON CONFLICT (target, email) DO NOTHING",
            [(target, e) for e in emails],
        )


async def get_emails(pool, target=None):
    async with pool.acquire() as conn:
        if target is None:
            rows = await conn.fetch("SELECT target, email, discovered_at FROM wizard_emails ORDER BY id")
        else:
            rows = await conn.fetch(
                "SELECT target, email, discovered_at FROM wizard_emails WHERE target = $1 ORDER BY id",
                target,
            )
    return [dict(row) for row in rows]


async def save_metadata(pool, target, source_url, file_type, metadata):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO wizard_metadata (target, source_url, file_type, metadata) "
            "VALUES ($1, $2, $3, $4::jsonb) "
            "ON CONFLICT (target, source_url) DO UPDATE SET "
            "file_type = EXCLUDED.file_type, metadata = EXCLUDED.metadata, discovered_at = now()",
            target, source_url, file_type, metadata,
        )


async def get_metadata(pool, target=None):
    async with pool.acquire() as conn:
        if target is None:
            rows = await conn.fetch(
                "SELECT target, source_url, file_type, metadata, discovered_at FROM wizard_metadata ORDER BY id"
            )
        else:
            rows = await conn.fetch(
                "SELECT target, source_url, file_type, metadata, discovered_at "
                "FROM wizard_metadata WHERE target = $1 ORDER BY id",
                target,
            )
    return [dict(row) for row in rows]


async def save_k6_config(pool, target, config, script):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO wizard_k6_configs (target, config, script) VALUES ($1, $2::jsonb, $3)",
            target, config, script,
        )


async def get_k6_configs(pool, target=None):
    async with pool.acquire() as conn:
        if target is None:
            rows = await conn.fetch(
                "SELECT target, config, script, created_at FROM wizard_k6_configs ORDER BY id"
            )
        else:
            rows = await conn.fetch(
                "SELECT target, config, script, created_at FROM wizard_k6_configs "
                "WHERE target = $1 ORDER BY id",
                target,
            )
    return [dict(row) for row in rows]


async def save_zap_alerts_bulk(pool, target, alerts):
    """`alerts` is the raw list of alert dicts from ZAP's
    /JSON/core/view/alerts/ -- a malformed entry (missing risk/alert) is
    skipped rather than failing the whole batch, same principle as
    CVE_Lookup's per-item guard."""
    rows = []
    for a in alerts:
        try:
            rows.append((
                target,
                a.get("url", target),
                a["risk"],
                a["alert"],
                a.get("description", "")[:2000],
                a,
            ))
        except KeyError:
            continue
    if not rows:
        return
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO wizard_zap_alerts (target, url, risk, alert_name, description, raw) "
            "VALUES ($1, $2, $3, $4, $5, $6::jsonb)",
            rows,
        )


async def get_zap_alerts(pool, target=None):
    async with pool.acquire() as conn:
        if target is None:
            rows = await conn.fetch(
                "SELECT target, url, risk, alert_name, description, raw, discovered_at "
                "FROM wizard_zap_alerts ORDER BY id"
            )
        else:
            rows = await conn.fetch(
                "SELECT target, url, risk, alert_name, description, raw, discovered_at "
                "FROM wizard_zap_alerts WHERE target = $1 ORDER BY id",
                target,
            )
    return [dict(row) for row in rows]


async def save_arp_hosts_bulk(pool, subnet, hosts):
    """`hosts` is a list of {"ip", "mac", "vendor"} dicts, as returned by
    Network_tool.ARP_Scanner."""
    if not hosts:
        return
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO wizard_arp_hosts (subnet, ip, mac, vendor) VALUES ($1, $2, $3, $4) "
            "ON CONFLICT (subnet, ip, mac) DO NOTHING",
            [(subnet, h["ip"], h["mac"], h.get("vendor")) for h in hosts],
        )


async def get_arp_hosts(pool, subnet=None):
    async with pool.acquire() as conn:
        if subnet is None:
            rows = await conn.fetch("SELECT subnet, ip, mac, vendor, discovered_at FROM wizard_arp_hosts ORDER BY id")
        else:
            rows = await conn.fetch(
                "SELECT subnet, ip, mac, vendor, discovered_at FROM wizard_arp_hosts WHERE subnet = $1 ORDER BY id",
                subnet,
            )
    return [dict(row) for row in rows]


async def clear_findings(pool, target=None):
    """Empty the findings tables (emails, metadata, k6 configs, ZAP
    alerts). With no target, clears everything across all targets --
    including ARP hosts, which aren't per-target and so are only cleared
    in this "everything" case. With a target, clears only that target's
    rows in the per-target tables. Config tables (wordlist/
    security_headers/urls) are untouched -- those aren't findings."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            for table in _FINDINGS_TABLES:
                if target is None:
                    await conn.execute(f"DELETE FROM {table}")
                else:
                    await conn.execute(f"DELETE FROM {table} WHERE target = $1", target)
            if target is None:
                await conn.execute("DELETE FROM wizard_arp_hosts")
