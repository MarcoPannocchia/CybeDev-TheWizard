# `OSINT_tool`

[← Index](../index.md)

#verified — expanded significantly in v0.8.2

Previously a thin wrapper around `Subdomain_Scanner` only (see [CHANGELOG.md](../CHANGELOG.md)). As of v0.8.2 it also does passive email harvesting and document-metadata extraction, all from pages already fetched elsewhere in the flow — no extra requests beyond the documents themselves.

---

## Subdomain scanning

`Subdomain_Scanner`/`_word_scan`/`insert_word` are actually defined on `Reconnaissance_Tool`, not `OSINT_tool` — see [reconnaissance.md](reconnaissance.md#subdomain-scanner-block) for the implementation. `OSINT_tool` reuses them through `TheWizard`'s multiple inheritance (all mixins share the same `self`), which is why `OSINT_tool` isn't self-sufficient on its own — it depends on also being mixed in alongside `Reconnaissance_Tool`. This coupling predates v0.8.2 and is unchanged.

---

## Email harvester (new in v0.8.2)

### `async Email_Harvester(self, session, url)`

**Description:** passive only — regexes over the HTML body already fetched for this target via `fetch_info`, no extra requests.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Returns:** `list[str]` — sorted, de-duplicated emails found; also prints `[EMAIL] <address>` for each.

**Implementation note:** matched addresses are stripped of trailing punctuation (`.,);:'"`) that a naive regex would otherwise include from surrounding prose/markup.

---

## Document metadata extractor (new in v0.8.2)

### `async Metadata_Extractor(self, session, url)`

**Description:** finds `.pdf`/`.docx` links on the already-fetched page, downloads a bounded number of them, and reads their embedded metadata (author, timestamps, title, …) with pure-Python parsers — no external binary dependency.

**Parameters:** `session: aiohttp.ClientSession`, `url: str`

**Returns:** `list[tuple[str, str, dict]]` — `(doc_url, file_type, metadata)` for each document that yielded metadata; also prints `[METADATA] <doc_url> (<file_type>): <metadata>`.

**Bounds:**
- `_MAX_DOCS_PER_TARGET = 5` — at most 5 documents per page
- `_MAX_DOC_BYTES = 5 * 1024 * 1024` (5 MB) — enforced via `_download_bounded` against **both** `Content-Length` *and* an actual capped read (`r.content.read(_MAX_DOC_BYTES + 1)`), so a server lying about its `Content-Length` can't force a huge read

**Parsers:**
- `.pdf` → `pypdf.PdfReader(...).metadata`, keys stripped of the leading `/`
- `.docx` → `docx.Document(...).core_properties` — `author`, `last_modified_by`, `created`, `modified`, `title`, `subject`, `keywords`, `revision`

A parse failure on one document is caught and logged as `[METADATA ERROR] Failed to parse <doc_url>: <ExceptionType>: <e>` — doesn't interrupt the loop over other documents.

---

## Orchestration

### `async OSINT_Spell(self, session, url)`

**Flow:**
1. `Subdomain_Scanner(session, url)`
2. `Email_Harvester(session, url)` — results saved to Postgres (`db.save_emails_bulk`) if any and if `db_pool` is set
3. `Metadata_Extractor(session, url)` — results saved to Postgres (`db.save_metadata`, one row per document) if any and if `db_pool` is set

**Returns:** `None`

> `Network_tool.ZAP_Scanner` also feeds ZAP-spidered pages into `Email_Harvester`/`Metadata_Extractor` via `_harvest_spidered_pages` — see [network.md](network.md) — so OSINT findings for a target aren't limited to the single entry-point URL passed to `OSINT_Spell`.
