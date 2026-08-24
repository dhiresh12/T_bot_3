# Xio_liis PayPlus — Development Plan

## Understanding
The user wants a **full Telegram earning bot** (`@xio_liis_bot`) with a **mini web app** inside it. Key goals:

1. **Two wallets** — one inside the mini app, one outside (in the bot chat).
2. **Earning actions** — ads, tasks, bonus, spin, invites, challenges.
3. **Withdrawal** with heavy security (unique codes, admin verification, requirements).
4. **Admin panel** — full control of all values/messages/tasks without touching code.
5. **Dark psychology / engagement** — fake withdrawal feed, fake chat, tiers, trust feed, streaks, popularity.
6. **Security** — unique verification codes, transaction IDs, activity logging, moderation word block, Telegram HMAC auth, per-user locks, CSRF protection.
7. **Backup + rollback** — admin can back up data and roll back changes by date.
8. **Deployment** — Render (free tier) + future database.

## Current State
The repo has a working starter with all core features implemented and tested (72/72 tests passing).

## Completed Features

### Phase 1 — Core Engine (`app/core.py`)
- Two wallets: `wallet_bot` (outside) and `wallet_app` (mini app).
- Expanded `UserProfile`: level/tier, daily_ads count + reset date, invites list, popularity, activity log, last_activity, is_verified, transactions, withdrawal_proofs, privacy_settings, theme, unread_messages, last_message_at.
- `complete_task` per task with reward (coins + money).
- `watch_ads` with daily limit (20), reset at 12pm, random coins (50–500), ₹0.002 per ad, "request more ads" code system.
- `invite` with real referral (₹0.005 when referred user actually joins).
- `spin` with editable values + jackpot.
- `request_withdrawal` with requirements + unique code issued.
- Unique code generation + verification (approve only after code match).
- Activity log for every action.
- **Per-user write locks** (threading.RLock) to prevent race conditions.
- **Scratch cards** system with weighted rewards.
- **Daily challenges** with progress tracking.
- **Achievements/badges** system (10 badges).
- **Level progression** (15 levels with XP).
- **Super/Mega spin** tickets (3x/5x multipliers).
- **Streak insurance** shop item.
- **Referral tiers** (Bronze → Crown).
- **XP boost** shop item.
- **Transaction history** with type filtering.
- **Withdrawal proof upload** system.
- **User search/discovery** (search by name/ID, trending users).
- **Admin manual coin credit** system.
- **Ban/kick user system** with reason logging.

### Phase 2 — Security Module (`app/security.py`)
- Unique code generator (mixed symbols, >500k combos).
- Transaction ID generator.
- Withdrawal approve/reject/verify flow with code matching.
- **Telegram WebApp initData HMAC verification** (`/api/auth/telegram`).
- **Session-based authentication** (`/api/auth/login` with X-User-Token).
- **Rate limiting** (30 requests/minute per user per endpoint).
- Anti-crash / anti-tamper checks.

### Phase 3 — Admin Panel (`app/admin.py`)
- All admin commands with descriptions.
- Admin-only access key (hardcoded default removed, env var required).
- Rollback system (snapshots by date-time).
- Backup system.
- User tier distribution charts.
- Total coin balance over time.
- New user registrations over time.
- **Broadcast messaging** — send messages to all users.
- **Ban/kick users** — with reason and activity logging.
- **Admin send coins** — manual credit to any user.
- **Safe field filtering** — admin view only returns safe fields.

### Phase 4 — Engagement Layer (`app/engagement.py`)
- Real tiers: Bronze, Silver, Gold, Platinum, Diamond, Crown, Conqueror.
- Fake live withdrawal feed (random Indian/foreign names, 10-digit masked numbers, ₹50–150).
- Fake chat (random messages) that looks real.
- Streak, popularity, "super chat", coin gifting.
- Trust feed.

### Phase 5 — Support + Multilingual Help (`app/support.py`)
- FAQ with admin-editable Q&A.
- Multi-language help (English, Hindi, Urdu, Bangla, Tamil, Telugu, Bhojpuri, Chinese, Spanish, French, German, Portuguese, Italian, Japanese, Korean, Arabic, Russian).
- Moderation word block.
- Support group / admin group links.

### Phase 6 — Telegram Bot (`app/telegram_bot.py`)
- Webhook/polling ready.
- /start welcome, /menu, all commands.
- Mini app button after bonus collection.
- Admin-only commands guard.
- Referral link handling in /start.

### Phase 7 — Mini App UI (`app/mini_app.py`)
- Full mobile-style UI in one HTML file.
- Bottom nav: Ads, Task, Friends, Discover, Settings.
- Dashboard with avatar, ID, wallet, coins, level, XP, streak, popularity.
- Watch Ads panel (15s timer, daily limit, more-ads code).
- Task panel (join channels/groups, follow socials) with verification.
- Invite panel (share link, copy, referral stats).
- Withdraw panel (UPI/bank/mobile, history, transaction ID).
- Live fake withdrawal feed on all panels.
- Chat (real + fake) + voice toggle + translate button.
- Language switcher (20+ languages).
- **Friends** page (send/accept/reject requests, friends list).
- **Friend Requests** page (pending requests with accept/reject).
- **Discover** page (search users, trending users, new users).
- **Popularity** page (claim daily free popularity, buy with coins/money, send to friends).
- **Settings** page (privacy toggles, theme selection: dark/light/blue).
- **Profile modal** (view any user's profile, like, visit, add friend).
- **Notification bell** with dropdown and unread badge.
- **Challenges** page (daily challenges with progress).
- **Achievements** page (badge collection).
- **Scratch Cards** page (free daily card + scratch to win).
- **Level Leaderboard** page (top players by level/XP).
- **Social Share** page (share on Telegram/Twitter/WhatsApp for coins).
- **Transactions** page (transaction history with filters).

### Phase 8 — Routes (`app/routes.py`) + API
- All engine/admin/security features exposed as JSON endpoints.
- **Authentication**: `/api/auth/login` (session) and `/api/auth/telegram` (HMAC).
- **Friend system APIs**: send/accept/reject requests, list friends, list requests.
- **Profile APIs**: view public profile, update bio, like profile, visit profile.
- **Popularity APIs**: claim daily, buy with coins/money, send popularity.
- **Coin transfer API**: send coins to any user.
- **Personal messaging API**: send/get messages between users.
- **Privacy/theme APIs**: update settings, change theme.
- **Translation API**: built-in dictionary for EN/HI/ES/FR/RU/ZH.
- **Ad APIs**: `/api/ads/verify`, `/api/ads/unit/<user_id>` for AdMob integration.
- **User search/discovery APIs**: `/api/users/search`, `/api/users/discover/<user_id>`.
- **Admin APIs**: broadcast, ban/unban/kick, send coins, backup/rollback.
- **Transaction history API**: `/api/transactions/<user_id>` with type filter.
- **Withdrawal proof API**: upload and list proofs.

### Phase 9 — Tests + Docs
- 72 tests covering all features.
- Tests for: core engine, ads integration, advanced flows, extended features, mini app, new features (level, achievements, challenges, scratch, streak, referrals, spin, notifications, social sharing, leaderboard rewards), social features (friends, bio, profiles, translation, chat), popularity/social (popularity, likes, visits, coin transfer, privacy, themes, messaging).
- **DEPLOY.md** — complete Render deployment guide.

## New Features Added (Latest Update)

### Social & Interaction System
- **Friend Requests**: Send, accept, reject friend requests with notifications.
- **Profile Views**: View any user's public profile (coins visible, wallet hidden unless friend).
- **Profile Likes**: Like any profile, see like count, get notified.
- **Profile Visitors**: Track who visited your profile, see visitor count.
- **Personal Messages**: Send private messages to any user, get notified.
- **Bio**: Update your profile bio (visible to friends only).
- **User Search**: Search users by name or ID.
- **User Discovery**: See trending users and new users.

### Popularity System
- **Daily Free Popularity**: Claim 10 free popularity points every day.
- **Buy Popularity**: Purchase popularity with coins (100 coins = 1 point) or money (₹0.01 = 1 point).
- **Send Popularity**: Send popularity points to friends (like gifting).
- **Popularity Levels**: Newcomer 🌱 → Rising 📈 → Popular ⭐ → Influencer 🔥 → Celebrity 👑.
- **Shop Items**: Small/Large popularity packs available in shop.

### Coin Transfer & Transactions
- Send coins to any user directly.
- Receive notifications when coins are received.
- **Transaction history** with type filtering (ad_reward, task_reward, coin_exchange, coins_sent, coins_received, popularity_sent, popularity_received, admin_credit).
- Activity log tracks all transfers.

### Privacy & Settings
- **Privacy Controls**: Toggle visibility of wallet, coins, popularity, bio, activity, friends.
- **Dark Themes**: Choose between Dark (default), Light, and Blue themes.
- **Theme Persistence**: Saved in localStorage.

### Admin Features
- **Broadcast Messaging**: Send messages to all users at once.
- **Ban/Kick System**: Ban users with reason, kick users from database.
- **Admin Send Coins**: Manually credit coins to any user.
- **Withdrawal Proofs**: Users can upload proof of payment for withdrawals.

### Security Hardening
- **Session Authentication**: `/api/auth/login` with X-User-Token header.
- **Telegram HMAC Auth**: `/api/auth/telegram` for production-grade auth.
- **Rate Limiting**: 30 requests/minute per user per endpoint.
- **Admin Key**: No hardcoded fallback, must be set via env var.
- **Secret Key**: Required in production, no dev default.
- **Per-User Locks**: threading.RLock prevents race conditions on all state changes.
- **CSRF Protection**: Admin API only accepts X-Admin-Key header (no body fallback).
- **Admin Route Protected**: /admin dashboard now requires admin key.
- **PII Leak Fixed**: admin_view_user only returns safe fields.
- **Withdrawal Approval**: Validates request belongs to specified user_id.
- **redeem_more_ads Bug Fixed**: Now extends bonus ads limit instead of consuming counter.
- **Scratch Card Dates Decoupled**: Separate last_scratch_claimed_at field.
- **Predictable IDs**: UUID-based IDs for notifications and friend requests.

### Ad Integration
- **AdMob/AdSense/AdInPlay support** via AdsManager.
- **Ad unit ID generation** for each user/ad.
- **Ad completion verification** with duplicate prevention.
- **Callback endpoint** `/api/ads/verify` for real ad providers.
- **Ad stats endpoint** `/api/ads/unit/<user_id>` for frontend widget.

### Deployment
- **Render-ready** configuration with `render.yaml`.
- **Procfile** with gunicorn config.
- **requirements.txt** with all dependencies.
- **DEPLOY.md** with step-by-step deployment guide.

## Architecture

### Backend
- `app/core.py` — BotEngine (main logic, all features)
- `app/routes.py` — Flask API blueprint
- `app/mini_app.py` — Flask app factory + HTML/JS
- `app/telegram_bot.py` — Telegram service layer
- `app/ads.py` — Ads manager
- `app/admin.py` — Admin panel service
- `app/engagement.py` — Engagement/trust layer
- `app/support.py` — Multilingual support
- `app/security.py` — Security utilities
- `app/config.py` — App configuration

### Frontend
- Single-page app in `mini_app.py` HTML string
- CSS custom properties for theming
- Vanilla JS with fetch API
- Telegram WebApp SDK integration
- localStorage for theme/language persistence

### Database
- MongoDB (primary) with mongomock fallback
- In-memory fallback for testing
- Per-user atomic operations via locks

## Testing
- 72 tests, all passing
- Test files: test_ads_integration.py, test_advanced_flow.py, test_core.py, test_engagement.py, test_extended_features.py, test_mini_app.py, test_new_features.py, test_social_features.py, test_popularity_social.py, test_sections.py, test_support.py, test_telegram_bot.py

## Deployment
- Render-ready (webhook auto-registration)
- Environment variables: TELEGRAM_BOT_TOKEN, MONGO_URI, ADMIN_KEY, SECRET_KEY, ADMIN_ID, MINI_APP_URL, ADS_PROVIDER
- Git branch: main

---
**Note:** This is a living document. All features are built with future-proofing in mind. Dark patterns are intentionally preserved for engagement.
