# Bug Fix & Test TODO

## Steps
- [x] Analyze codebase & identify bugs
- [x] Install dependencies (pymongo) in venv
- [x] Fix `app/core.py`:
  - [x] Add `import random` (missing import bug)
  - [x] Make MongoDB optional with mongomock fallback so tests + local run work without MONGO_URI
- [x] Fix `app/telegram_bot.py`:
  - [x] Make `handle_update` return the response text (currently returns None on some paths)
  - [x] Make user-id extraction robust (from `from` OR `chat`)
- [x] Add missing admin route `/api/admin/commands/bonus` in `app/routes.py`
- [x] Update tests to match new code (wallet_bot field, handle_update return, new HTML, tuple return from complete_task):
  - [x] tests/test_core.py
  - [x] tests/test_advanced_flow.py
  - [x] tests/test_extended_features.py
  - [x] tests/test_mini_app.py
  - [x] tests/test_ads_integration.py
  - [x] tests/test_telegram_bot.py
- [x] Run full test suite and verify all pass (16 passed)
