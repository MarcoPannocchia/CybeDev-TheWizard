# Troubleshooting — Common Errors

## UnboundLocalError: idx_insert

**Symptom:**
```
UnboundLocalError: local variable 'idx_insert' referenced before assignment
```

**Cause:**
`insert_word` was called with a URL that does not contain `//` (e.g. `google.com` instead of `https://google.com`).
The loop never finds the condition `i != "/" and prec_i == "/"`, so `idx_insert` is never assigned.

**Fix:**
Always pass full URLs including protocol:
```python
urls = ["https://google.com"]   # ✅
urls = ["google.com"]           # ❌
```

> See also: [[modules/reconnaissance.md]]

---

## TypeError: ClientSession object is not iterable

**Symptom:**
```
TypeError: 'ClientSession' object is not iterable
```

**Cause:**
Parameters `session` and `url` are swapped in a method call.
`insert_word` receives `session` where it expects a string URL and tries to iterate it.

**Fix:**
Check parameter order — all tool methods follow `(self, session, url)`:
```python
await self.Subdomain_Scanner(session, url)   # ✅
await self.Subdomain_Scanner(url, session)   # ❌
```

---

## TypeError: takes N positional arguments but M were given

**Symptom:**
```
TypeError: method() takes 2 positional arguments but 3 were given
```

**Cause:**
`self` is being passed manually in a method call inside the class.

**Fix:**
Never pass `self` explicitly — Python injects it automatically:
```python
await self.fetch_info(session, url)        # ✅
await self.fetch_info(self, session, url)  # ❌
```

---

## RuntimeWarning: coroutine was never awaited

**Symptom:**
```
RuntimeWarning: coroutine 'method' was never awaited
```

**Cause:**
An `async def` function was called without `await`.

**Fix:**
```python
await self.Header_Analyzer(session, url)   # ✅
self.Header_Analyzer(session, url)         # ❌
```

---

## aiohttp import error — ClientTimeout not found

**Symptom:**
```
NameError: name 'ClientTimeout' is not defined
```

**Fix:**
```python
from aiohttp import ClientTimeout   # ✅
```

> See also: [[architecture/async.md]]
