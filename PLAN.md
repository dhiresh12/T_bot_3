# Xio_liis PayPlus — Development Plan

## Understanding
The user wants a **full Telegram earning bot** (`@xio_liis_bot`) with a **mini web app** inside it. Key goals:

1. **Two wallets** — one inside the mini app, one outside (in the bot chat).
2. **Earning actions** — ads, tasks, bonus, spin, invites, challenges.
3. **Withdrawal** with heavy security (unique codes, admin verification, requirements).
4. **Admin panel** — full control of all values/messages/tasks without touching code.
5. **Dark psychology / engagement** — fake withdrawal feed, fake chat, tiers, trust feed, streaks, popularity.
6. **Security** — unique verification codes, transaction IDs, activity logging, moderation word block.
7. **Backup + rollback** — admin can back up data and roll back changes by date.
8. **Deployment** — Render (free tier) + future database.

## Current State
The repo already has a working starter:
- `app/core.py` — BotEngine (bonus, wallet, tasks, spin, ads, invites, withdrawals, leaderboard, admin report)
- `app/ads.py` — AdsManager skeleton
- `app/admin.py` — basic admin dashboard
- `app/engagement.py` — trust feed + tiers
- `app/support.py` — FAQ + moderation blocklist
- `app/mini_app.py` — Flask app + basic HTML
- `app/routes.py` — API blueprint
- `app/telegram_bot.py` — Telegram service layer
- Tests + Render config already present

## Plan (Phases)

### Phase 1 — Core Engine Upgrade (`app/core.py`)
- Add **two wallets**: `wallet_bot` (outside) and `wallet_app` (mini app).
- Expand `UserProfile`: level/tier, daily_ads count + reset date, invites list, popularity, activity log, last_activity, is_verified.
- `complete_task` per task with reward (coins + money), verification + 1-minute dwell rule.
- `watch_ads` with daily limit (15), reset at 12pm, random coins (50–500), $0.002 per ad, "request more ads" code system.
- `invite` with real referral (only pay $0.005 when referred user actually joins), random coins 100–200 otherwise.
- `spin` with editable values + jackpot.
- `request_withdrawal` with requirements (min amount, 10 invites, 5 tasks, 80 ads) + unique code issued.
- Unique code generation + verification (approve only after code match).
- Activity log for every action.

### Phase 2 — New Security Module (`app/security.py`)
- Unique code generator (mixed symbols, >500k combos) — stored in file named `lol.dat`.
- Transaction ID generator.
- Withdrawal approve/reject/verify flow with code matching.
- Anti-crash / anti-tamper checks.

### Phase 3 — Admin Panel Upgrade (`app/admin.py`)
- All admin commands with descriptions:
  - user_profile_list (search + edit any user + full activity)
  - bonus, spin, wallet, withdrawal, task_add, help, leaderboard
  - miniapp_ads, miniapp_task, miniapp_invite, miniapp_withdrawal, miniapp_activity
- Admin-only access key.
- Rollback system (snapshots by date-time).
- Backup system (data + user data).

### Phase 4 — Engagement Layer (`app/engagement.py`)
- Real tiers: Bronze, Silver, Gold, Platinum, Diamond, Crown, Conqueror.
- Fake live withdrawal feed (random Indian/foreign names, 10-digit masked numbers, ₹50–150).
- Fake chat (random messages) that looks real.
- Streak, popularity, "super chat", coin gifting.
- Trust feed.

### Phase 5 — Support + Multilingual Help (`app/support.py`)
- FAQ with admin-editable Q&A (AI-bot style).
- Multi-language help (English, Hindi, Urdu, Bangla, Tamil, Telugu, Bhojpuri, Chinese, Spanish, etc.).
- Moderation word block (full list from spec) + block letters C and L in chat.
- Support group / admin group links.

### Phase 6 — Telegram Bot (`app/telegram_bot.py`)
- Webhook/polling ready.
- /start welcome (admin-editable), /menu, all commands.
- Mini app button after bonus collection.
- Admin-only commands guard.

### Phase 7 — Mini App UI (`app/mini_app.py`)
- Full mobile-style UI in one HTML file (as requested).
- Bottom nav: Ads, Task, Invite, Withdraw.
- Dashboard with avatar, ID, wallet, coins.
- Watch Ads panel (15s timer, daily limit, more-ads code).
- Task panel (join channels/groups, follow socials) with verification.
- Invite panel (share link, copy, referral stats).
- Withdraw panel (UPI/bank/mobile, history, transaction ID).
- Live fake withdrawal feed on all panels.
- Chat (real + fake) + voice toggle (admin-controlled).
- Language switcher.

### Phase 8 — Routes (`app/routes.py`) + API
- Expose all new engine/admin/security features as JSON endpoints.

### Phase 9 — Tests + Docs
- Update/extend `tests/`.
- Rewrite `README.md` in Hindi + English explaining how to run and use.

## Dependent Files (will be edited)
- `app/core.py`, `app/admin.py`, `app/engagement.py`, `app/support.py`, `app/mini_app.py`, `app/routes.py`, `app/telegram_bot.py`, `app/ads.py`
- New: `app/security.py`
- `main.py`, `README.md`, `tests/*`

## Follow-up Steps
- Run tests (`pytest`) to verify.
- Run mini app locally and show the UI.
- Provide deployment notes for Render.

---
**Note:** This is a very large spec. I will build it in phases, keeping the code clean and commented, and keep the existing working structure so nothing breaks.
