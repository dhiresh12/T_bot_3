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

### Phase 10 — Daily Streak Rewards
- **Daily login streak system** with escalating rewards: Day 1: 50 coins, Day 2: 100 coins, Day 3: 200 coins, Day 4: 350 coins, Day 5: 500 coins, Day 6: 750 coins, Day 7: 1000 coins, Day 8: 1500 coins, Day 9: 2000 coins, Day 10+: 3000 coins.
- Miss a day and streak resets to 0 (dark pattern: creates urgency to return daily).
- Streak rewards page with visual calendar grid showing claimed/unclaimed days.
- Backend: `claim_daily_login_reward()`, `get_daily_login_streak_info()` in `BotEngine`.
- API: `/api/streak/info/<user_id>`, `/api/streak/claim/<user_id>`.

### Phase 11 — Limited-Time Events
- **Rotating event system** with admin-configurable start/end times.
- Event banner on home page with countdown and exclusive rewards.
- One-time claim per user per event.
- Backend: `get_active_event()`, `claim_event_reward()` in `BotEngine`.
- API: `/api/events/active`, `/api/events/claim/<user_id>`.

### Phase 12 — PIN Lock for Withdrawals
- **Optional 4-6 digit PIN** for withdrawal confirmation.
- PIN required before any withdrawal request if set.
- PIN hash stored securely (SHA256, never plaintext).
- PIN setup UI with numeric keypad modal.
- Backend: `set_pin()`, `verify_pin()` in `BotEngine`.
- API: `/api/security/set-pin/<user_id>`, `/api/security/verify-pin/<user_id>`, `/api/security/pin-status/<user_id>`.
- Withdrawal route now checks PIN before processing.

### Phase 13 — A/B Testing Framework
- Lightweight A/B testing for optimizing engagement.
- Variants for: withdrawal countdown duration, fee structure, onboarding flow.
- User assigned to variant based on user_id hash.
- Backend: `get_ab_variant()` in `BotEngine`.
- API: `/api/ab/variant/<user_id>?test=<test_name>`.

### Phase 14 — Achievement Sharing Rewards
- Share achievements to social platforms (Telegram, Twitter, WhatsApp).
- First share per achievement awards 20 coins + 10 XP.
- 24-hour cooldown between share rewards.
- Backend: `record_share_reward()` in `BotEngine`.
- API: `/api/achievements/share/<user_id>`.

### Phase 15 — Admin Analytics v2
- Enhanced admin analytics dashboard with:
  - Real-time active users count.
  - User retention rate (today vs yesterday).
  - Total wallet balance across all users.
  - Top performing tasks by completion count.
  - Daily registration trends (last 7 days).
  - Pending withdrawal count.
- Backend: `get_admin_analytics_v2()` in `BotEngine`.
- API: `/api/admin/analytics/v2` (admin-only).

### Phase 16 — Toast Notification System
- Toast notifications for all API calls (success, error, info, warning).
- Auto-dismiss after 3.5 seconds with swipe-to-dismiss.
- Used for: withdrawal success, streak claims, event rewards, errors.
- Pure CSS/JS, no dependencies.

### Phase 17 — Real-Time Notification Polling
- Background polling every 30 seconds for unread notification count.
- Badge counter auto-updates without page refresh.
- Haptic + sound feedback on new notification.
- Backend: `/api/notifications/unread-count/<user_id>`.

### Phase 18 — PWA + Offline Support
- **Service Worker** for offline caching (`app/static/sw.js`).
- **Web App Manifest** for "Add to Home Screen" (`/manifest.json`).
- Offline action queue: actions performed offline sync when back online.
- Install prompt shown after 30 seconds for eligible browsers.
- Backend: `queue_offline_action()`, `process_offline_actions()` in `BotEngine`.
- API: `/api/offline/sync/<user_id>`.

### Phase 19 — Notification Delivery Receipts
- Track notification delivery status (sent, delivered, read).
- Backend: `record_notification_receipt()` in `BotEngine`.
- Stored in `profile.notification_receipts`.

### Phase 20 — Webhook Retry Queue
- Failed webhook deliveries retry up to 3 times with 2-second delay.
- Dead-letter queue for manual review of permanently failed notifications.
- Backend: `self.webhook_retry_attempts`, `self.webhook_retry_delay_seconds`, `self.webhook_dead_letter_queue` in `BotEngine.__init__`.

## Dark Patterns Implemented (Engagement Layer)

### Countdown Timers
- Withdrawal cooldown timer (`withdraw-cd`) — blocks re-request for 5 minutes after submission.
- **A/B tested variants**: 3min, 5min, 10min countdowns.

### Hidden Costs
- Processing fee reveal on withdraw amount input (`hidden-fee-box`) — 5% fee + ₹2 minimum appears only after user types amount.
- **A/B tested variants**: 5% fee/2min cooldown, 7% fee/0min cooldown, 3% fee/5min cooldown.

### Confirmshaming
- Onboarding skip button: guilt-trip confirm dialog ("Are you sure? Skipping means you might miss out on exclusive beginner bonuses...")
- Back buttons: confirm dialog warning about lost progress/earnings.
- **A/B tested variants**: short, medium, long onboarding flows.

### Disguised Ads
- Sponsored task injection (`injectSponsoredTask`) — random sponsor tasks mixed into task list with dashed gold border and "SPONSORED" badge.

### Fake Social Proof
- Randomized live user counter (`online-count`) — fluctuates between 2,300–3,100.
- Randomized payout counter (`payout-count`) — fluctuates between ₹1,20,000–₹1,70,000.

### Roach Motel
- Extra "Account Verification" step for withdrawals above ₹50 (`roach-step`) — fake 2-4 second verification delay before allowing withdrawal.

### Streak Anxiety
- Daily streak rewards with reset on miss — escalating rewards (50→3000 coins) create strong incentive to return daily.
- Streak freeze available in shop to reduce churn.

### Event Urgency
- Limited-time event banners with countdown timers and exclusive rewards.
- Creates FOMO (fear of missing out) around event participation.

### PIN Lock Friction
- Optional PIN adds perceived security but also creates extra step before withdrawal.
- Dark pattern: increases psychological investment and trust.

### Share Reward Loop
- Share achievements for coins/XP — creates viral marketing loop.
- Cooldown prevents abuse but encourages daily sharing.

### Toast Feedback
- Immediate feedback on all actions creates dopamine loop.
- Success toasts reinforce positive behavior.

---

**Note:** This is a living document. All features are built with future-proofing in mind. Dark patterns are intentionally preserved for engagement.

## Architecture

### Backend
- `app/core.py` — BotEngine (main logic, all features)
- `app/routes/` — Flask API blueprints package (22 isolated modules)
  - `_helpers.py` — shared rate-limit, auth decorators, safe-int
  - `auth.py` — login, Telegram HMAC auth
  - `webhooks.py` — Telegram webhook status + handler
  - `ads.py` — ad config, watch, verify, redeem-more
  - `tasks.py` — tasks, challenges, achievements, scratch, streak, referral tier
  - `social.py` — friends, profile, chat, messages, translate, likes, visits, privacy, theme
  - `popularity.py` — claim/buy/send popularity
  - `withdrawals.py` — withdraw, proofs, transaction history
  - `spin.py` — normal/super/mega spin
  - `shop.py` — catalog, redeem, coin exchange
  - `notifications.py` — list + mark-read
  - `leaderboard.py` — global, level, rewards
  - `admin.py` — all admin endpoints + admin dashboard UI
  - `misc.py` — health, bonus, dashboard, engagement, support, help, XP, search, discover, lucky-hour, goals, calendar, prestige
  - `streaks.py` — streak info + claim
  - `events.py` — active events + claim
  - `security.py` — PIN set/verify/status
  - `achievements_share.py` — achievement share rewards
  - `analytics.py` — dark pattern analytics
  - `retention.py` — streak reminders, weekly summaries, activity feed
  - `withdrawal_proofs.py` — public proof gallery
  - `referral_tournament.py` — referral tournament leaderboard
  - `flash_sale.py` — flash sale endpoints
  - `crates.py` — mystery crate catalog + open
  - `quests.py` — onboarding quest status + claim
- `app/routes.py` — backward-compatible shim (`from app.routes import bp`)
- `app/mini_app.py` — thin Flask app factory (reads HTML from `app/templates/mini_app.html`)
- `app/telegram_bot.py` — Telegram service layer
- `app/ads.py` — Ads manager
- `app/admin.py` — Admin panel service
- `app/engagement.py` — Engagement/trust layer
- `app/support.py` — Multilingual support
- `app/security.py` — Security utilities
- `app/config.py` — App configuration
- `app/push.py` — Web push notification service

### Frontend
- `app/templates/mini_app.html` — main mini-app HTML/JS (extracted from Python)
- `app/templates/admin.html` — admin dashboard HTML/JS (extracted from Python)
- CSS custom properties for theming
- Vanilla JS with fetch API
- Telegram WebApp SDK integration
- localStorage for theme/language persistence
- Pages: Home, Ads, Friends, Discover, More, Streak, Crates + sub-pages (Calendar, Proofs, Tournament, Flash Sale, Quests, Activity Feed)

### Design Principles
- **Error isolation**: each route module is imported independently; one broken module does not crash the app
- **Single responsibility**: each blueprint covers one feature domain
- **Template separation**: HTML lives in `app/templates/`, not embedded in Python strings

### Database
- MongoDB (primary) with mongomock fallback
- In-memory fallback for testing
- Per-user atomic operations via locks

## Testing
- 97 tests, all passing
- Test files: test_ads_integration.py, test_advanced_flow.py, test_core.py, test_engagement.py, test_extended_features.py, test_mini_app.py, test_new_features.py, test_social_features.py, test_popularity_social.py, test_sections.py, test_support.py, test_telegram_bot.py
- Coverage: core engine, ads, advanced flows, extended features, mini app, new features (level, achievements, challenges, scratch, streak, referrals, spin, notifications, social sharing, leaderboard rewards, retention, proof gallery, flash sales, crates, quests, calendar, prestige), social features (friends, bio, profiles, translation, chat), popularity/social (popularity, likes, visits, coin transfer, privacy, themes, messaging)

## Deployment
- Render-ready (webhook auto-registration)
- Environment variables: TELEGRAM_BOT_TOKEN, MONGO_URI, ADMIN_KEY, SECRET_KEY, ADMIN_ID, MINI_APP_URL, ADS_PROVIDER
- Git branch: main

## Dark Patterns Implemented (Engagement Layer)

### Countdown Timers
- Withdrawal cooldown timer (`withdraw-cd`) — blocks re-request for 5 minutes after submission.

### Hidden Costs
- Processing fee reveal on withdraw amount input (`hidden-fee-box`) — 5% fee + ₹2 minimum appears only after user types amount.

### Confirmshaming
- Onboarding skip button: guilt-trip confirm dialog ("Are you sure? Skipping means you might miss out on exclusive beginner bonuses...")
- Back buttons: confirm dialog warning about lost progress/earnings.

### Disguised Ads
- Sponsored task injection (`injectSponsoredTask`) — random sponsor tasks mixed into task list with dashed gold border and "SPONSORED" badge.

### Fake Social Proof
- Randomized live user counter (`online-count`) — fluctuates between 2,300–3,100.
- Randomized payout counter (`payout-count`) — fluctuates between ₹1,20,000–₹1,70,000.

### Roach Motel
- Extra "Account Verification" step for withdrawals above ₹50 (`roach-step`) — fake 2-4 second verification delay before allowing withdrawal.

### Haptic & Audio Feedback
- Telegram Haptics API (`haptic()`) — impactOccurred on nav, spin, coins, success, error.
- Web Audio API synth (`playSound()`) — click, coin, spin, success, error, scratch, reward, nav tones.

### Onboarding Tutorial
- 4-step first-time walkthrough overlay with dot indicators and localStorage persistence (`xio_onboarded`).

---
**Note:** This is a living document. All features are built with future-proofing in mind. Dark patterns are intentionally preserved for engagement.

## Phase 21 — Retention & Engagement Features (Latest)

### Withdrawal Proof Gallery
- Public gallery of verified withdrawal proofs with user names, notes, timestamps.
- Social proof builds trust and increases withdrawal motivation.
- API: `/api/withdrawals/proofs/gallery`
- Frontend: Proof Gallery page with verified/pending badges.

### Daily Login Calendar
- Escalating monthly rewards: Day 1-3: 50 coins, Day 4-7: 150 coins + spin, Day 8-14: 350 coins + scratch card, Day 15-21: 500 coins + 2 spins, Day 22-30: 1000 coins + 3 spins, Day 31: 3000 coins + badge.
- Visual calendar grid with claimed/unclaimed days.
- Backend: `get_login_calendar()`, `claim_calendar_day()` in `BotEngine`.
- API: `/api/calendar/<user_id>`, `/api/calendar/claim/<user_id>`.

### Web Push Notifications
- Service worker + VAPID key support for browser push notifications.
- Notifications for: streak reminders, friend activity, new events, withdrawal status, flash sales.
- Frontend: `requestPushPermission()` function, PWA install banner.
- Backend: `PushNotificationService` in `app/push.py`.

### Referral Tournament
- Weekly referral contest with live leaderboard.
- Top 3 referrers win bonus coins + exclusive badge + highlighted ranking.
- Backend: `get_tournament_leaderboard()` in `BotEngine`.
- API: `/api/tournament/leaderboard`
- Frontend: Tournament page with top 3 highlighted.

### Flash Sales
- Limited-time shop offers with 50-70% discount.
- Creates urgency and impulse purchases.
- Backend: `get_active_flash_sale()` in `BotEngine`.
- API: `/api/flash-sale/active`
- Frontend: Flash Sale page with countdown timer.

### Mystery Crates / Loot Boxes
- Variable reward system with weighted random prizes.
- Basic Crate (200 coins) and Premium Crate (500 coins).
- Prizes range from 50 coins to 10,000 coins + XP.
- Backend: `get_crate_catalog()`, `open_crate()` in `BotEngine`.
- API: `/api/crates/catalog`, `/api/crates/open/<user_id>`
- Frontend: Crates page with open buttons.

### Gamified Onboarding Quest
- 5-step quest: watch ad, spin wheel, send message, invite friend, claim bonus.
- Completing all steps unlocks "Founder" badge + 500 coins + 100 XP.
- Backend: `get_quest_status()`, `claim_quest_reward()` in `BotEngine`.
- API: `/api/quests/status/<user_id>`, `/api/quests/claim/<user_id>`
- Frontend: Quests page with progress tracking.

### Achievement Prestige System
- After reaching max XP, users can prestige to unlock exclusive diamond badges.
- Prestige resets level to 1 but grants +1000 coins and prestige badge.
- Backend: `get_prestige_info()`, `prestige_user()` in `BotEngine`.
- API: `/api/prestige/<user_id>`
- Frontend: Prestige button on profile when eligible.

### Lucky Hour
-特定时间段 (8-10 PM UTC) ads and spins give 2x rewards.
- Live indicator on home page showing active status and next lucky hour.
- Backend: `is_lucky_hour()`, `get_lucky_hour_status()` in `BotEngine`.
- API: `/api/lucky-hour/status`
- Frontend: Lucky hour indicator on home page.

### Personalized Goal Nudges
- Micro-goals displayed on home page: "Just 15 XP away from Level 5!", "1 more invite to Silver tier!".
- Increases completion rates by showing progress.
- Backend: `get_goal_nudges()` in `BotEngine`.
- API: `/api/goals/nudges/<user_id>`
- Frontend: Goal nudges section on home page.

### Additional Security Hardening
- Required `SECRET_KEY` environment variable (no dev fallback).
- 24-hour session expiry with automatic cleanup.
- Admin routes accept `X-Admin-Key` header only (removed body key leak).
- Global `escapeHtml()` in frontend for all user-generated content.
- Backend `_sanitize_text()` applied to all user inputs (name, bio, messages, shop items, events).

## Architecture

### Backend
- `app/core.py` — BotEngine (main logic, all features)
- `app/routes/` — Flask API blueprints package (22 isolated modules)
  - `_helpers.py` — shared rate-limit, auth decorators, safe-int
  - `auth.py` — login, Telegram HMAC auth
  - `webhooks.py` — Telegram webhook status + handler
  - `ads.py` — ad config, watch, verify, redeem-more
  - `tasks.py` — tasks, challenges, achievements, scratch, streak, referral tier
  - `social.py` — friends, profile, chat, messages, translate, likes, visits, privacy, theme
  - `popularity.py` — claim/buy/send popularity
  - `withdrawals.py` — withdraw, proofs, transaction history
  - `spin.py` — normal/super/mega spin
  - `shop.py` — catalog, redeem, coin exchange
  - `notifications.py` — list + mark-read
  - `leaderboard.py` — global, level, rewards
  - `admin.py` — all admin endpoints + admin dashboard UI
  - `misc.py` — health, bonus, dashboard, engagement, support, help, XP, search, discover, lucky-hour, goals, calendar, prestige
  - `streaks.py` — streak info + claim
  - `events.py` — active events + claim
  - `security.py` — PIN set/verify/status
  - `achievements_share.py` — achievement share rewards
  - `analytics.py` — dark pattern analytics
  - `retention.py` — streak reminders, weekly summaries, activity feed
  - `withdrawal_proofs.py` — public proof gallery
  - `referral_tournament.py` — referral tournament leaderboard
  - `flash_sale.py` — flash sale endpoints
  - `crates.py` — mystery crate catalog + open
  - `quests.py` — onboarding quest status + claim
- `app/routes.py` — backward-compatible shim (`from app.routes import bp`)
- `app/mini_app.py` — thin Flask app factory (reads HTML from `app/templates/mini_app.html`)
- `app/telegram_bot.py` — Telegram service layer
- `app/ads.py` — Ads manager
- `app/admin.py` — Admin panel service
- `app/engagement.py` — Engagement/trust layer
- `app/support.py` — Multilingual support
- `app/security.py` — Security utilities
- `app/config.py` — App configuration
- `app/push.py` — Web push notification service
# #   P h a s e   2 2   � �    E a r n i n g   S y s t e m   E n h a n c e m e n t s   ( L a t e s t )  
  
 # # #   M u l t i - A d - N e t w o r k   F a l l b a c k   w i t h   A n t i - F r a u d  
 -   * * P r o v i d e r   f a l l b a c k   c h a i n * * :   A d M o b   - >   A d S e n s e   - >   A d i n P l a y .   I f   o n e   f a i l s ,   n e x t   p r o v i d e r   i s   u s e d   a u t o m a t i c a l l y .  
 -   * * A n t i - f r a u d   c h e c k s * * :   I P   b l o c k i n g ,   d e v i c e   f i n g e r p r i n t i n g ,   c o m p l e t i o n - t i m e   v a l i d a t i o n ,   f r a u d   s c o r i n g .  
 -   * * F r a u d   t h r e s h o l d s * * :   M i n i m u m   3 s   c o m p l e t i o n   t i m e ,   m a x i m u m   1 2 0 s ,   b l o c k s   i f   s c o r e   > =   3 .  
 -   * * D a i l y   s t a t s   t r a c k i n g * * :   p e r - u s e r   d a i l y   a d   c o u n t s ,   r e m a i n i n g   a d s ,   t o t a l   e a r n i n g s .  
 -   * * A d m i n   s t a t s * * :   d a t e ,   a d s   c o m p l e t e d ,   u n i q u e   u s e r s ,   t o t a l   r e v e n u e ,   b l o c k e d   I P s / d e v i c e s .  
 -   B a c k e n d :   e n h a n c e d   A d s M a n a g e r   i n   a p p / a d s . p y   w i t h   v e r i f y _ a d _ c o m p l e t i o n ( ) ,   b l o c k _ i p ( ) ,   b l o c k _ d e v i c e ( ) ,   g e t _ a d m i n _ s t a t s ( ) .  
  
 # # #   S p o n s o r e d   T a s k   M a n a g e m e n t  
 -   A d m i n   c a n   a d d   b r a n d - s p o n s o r e d   t a s k s   w i t h   r e w a r d   c o i n s ,   r e w a r d   m o n e y ,   v e r i f i c a t i o n   t y p e ,   e x p i r y .  
 -   T a s k s   a r e   s a n i t i z e d   s e r v e r - s i d e ;   u s e r s   c a n n o t   c h e a t   b y   e d i t i n g   U I .  
 -   P r o o f   s u b m i s s i o n   f o r   m a n u a l   v e r i f i c a t i o n   t y p e s .  
 -   B a c k e n d :   a d d _ s p o n s o r e d _ t a s k ( ) ,   g e t _ s p o n s o r e d _ t a s k s ( ) ,   c o m p l e t e _ s p o n s o r e d _ t a s k ( )   i n   B o t E n g i n e .  
 -   A P I :   / a p i / s p o n s o r e d - t a s k s / < u s e r _ i d > ,   / a p i / s p o n s o r e d - t a s k s / c o m p l e t e / < u s e r _ i d >  
 -   F r o n t e n d :   S p o n s o r e d   t a s k s   i n j e c t e d   i n t o   t a s k   l i s t   w i t h   v e r i f i c a t i o n   f l o w .  
  
 # # #   W i t h d r a w a l   F e e   H a r d e n i n g   &   A n t i - F r a u d  
 -   * * D a i l y   l i m i t * * :   m a x   3   w i t h d r a w a l s   p e r   d a y .  
 -   * * W e e k l y   l i m i t * * :   m a x   R s 5 0 0   p e r   w e e k .  
 -   * * A m o u n t   g a t e s * * :   R s 1 0 0 +   r e q u i r e s   7 - d a y   s t r e a k ;   R s 5 0 0 +   b l o c k e d   e n t i r e l y .  
 -   * * K Y C   e n f o r c e m e n t * * :   w i t h d r a w a l s   b l o c k e d   u n t i l   K Y C   a p p r o v e d .  
 -   B a c k e n d :   _ c h e c k _ w i t h d r a w a l _ f r a u d ( )   i n   B o t E n g i n e   c a l l e d   f r o m   r e q u e s t _ w i t h d r a w a l ( ) .  
 -   A l l   l i m i t s   e n f o r c e d   s e r v e r - s i d e ;   c l i e n t - s i d e   i s   o n l y   f o r   U X .  
  
 # # #   A f f i l i a t e   &   C o m m i s s i o n   S y s t e m  
 -   * * P r o g r a m s * * :   T e l e g r a m   G a m e s   ( 1 5 %   c o m m i s s i o n ) ,   F i n a n c e   A p p   ( R s 5   f i x e d ) ,   S h o p p i n g   ( 8 %   c o m m i s s i o n ) .  
 -   * * C o o k i e   t r a c k i n g * * :   7 - 3 0   d a y   c o o k i e   w i n d o w   p e r   p r o g r a m .  
 -   * * C o n v e r s i o n   r e c o r d i n g * * :   s a l e   a m o u n t   - >   c o m m i s s i o n   c a l c u l a t i o n .  
 -   * * P a y o u t   t r a c k i n g * * :   p e n d i n g / p a i d   s t a t u s   p e r   c o m m i s s i o n .  
 -   B a c k e n d :   A f f i l i a t e S e r v i c e   i n   a p p / a f f i l i a t e . p y .  
 -   A P I :   / a p i / a f f i l i a t e / p r o g r a m s ,   / a p i / a f f i l i a t e / l i n k / < u s e r _ i d > / < p r o g r a m _ i d > ,   / a p i / a f f i l i a t e / c l i c k / < u s e r _ i d > / < p r o g r a m _ i d > ,   / a p i / a f f i l i a t e / c o n v e r t / < u s e r _ i d > / < p r o g r a m _ i d > ,   / a p i / a f f i l i a t e / c o m m i s s i o n s / < u s e r _ i d > .  
  
 # # #   P r e m i u m   S u b s c r i p t i o n   T i e r s  
 -   * * N o   A d s * * :   R s 2 9 / m o n t h ,   r e m o v e s   a d s   +   1 x   c o i n   b o n u s .  
 -   * * D o u b l e   R e w a r d s * * :   R s 4 9 / m o n t h ,   n o   a d s   +   2 x   c o i n   b o n u s   +   2 x   s p i n   b o o s t .  
 -   * * E x c l u s i v e * * :   R s 9 9 / m o n t h ,   n o   a d s   +   3 x   c o i n   b o n u s   +   3 x   s p i n   b o o s t   +   e x c l u s i v e   c r a t e   a c c e s s .  
 -   S u b s c r i p t i o n   e x p i r y   t r a c k e d   p e r   u s e r ;   b e n e f i t s   a u t o - e x p i r e .  
 -   B a c k e n d :   P r e m i u m S e r v i c e   i n   a p p / p r e m i u m . p y .  
 -   A P I :   / a p i / p r e m i u m / t i e r s ,   / a p i / p r e m i u m / s u b s c r i p t i o n / < u s e r _ i d > ,   / a p i / p r e m i u m / p u r c h a s e / < u s e r _ i d > .  
  
 # # #   D a t a   I n s i g h t s   w i t h   C o n s e n t  
 -   * * G r a n u l a r   c o n s e n t * * :   a n a l y t i c s ,   p e r s o n a l i z a t i o n ,   a d s   p e r s o n a l i z a t i o n   � �    a l l   o p t - i n .  
 -   * * E v e n t   t r a c k i n g * * :   o n l y   r e c o r d s   e v e n t s   f o r   u s e r s   w h o   o p t e d   i n t o   a n a l y t i c s .  
 -   * * A d m i n   s u m m a r y * * :   a g g r e g a t e d   e v e n t   c o u n t s ,   u n i q u e   u s e r s ,   t o p   e v e n t s .  
 -   * * U s e r   i n s i g h t s * * :   l a s t   5 0   e v e n t s   p e r   u s e r   ( i f   c o n s e n t   g i v e n ) .  
 -   B a c k e n d :   I n s i g h t s S e r v i c e   i n   a p p / i n s i g h t s . p y .  
 -   A P I :   / a p i / i n s i g h t s / c o n s e n t / < u s e r _ i d > ,   / a p i / i n s i g h t s / t r a c k / < u s e r _ i d > ,   / a p i / a d m i n / i n s i g h t s / s u m m a r y   ( a d m i n - o n l y ) .  
  
 # #   T e s t i n g  
 -   9 7   t e s t s ,   a l l   p a s s i n g  
 -   T e s t   f i l e s :   t e s t _ a d s _ i n t e g r a t i o n . p y ,   t e s t _ a d v a n c e d _ f l o w . p y ,   t e s t _ c o r e . p y ,   t e s t _ e n g a g e m e n t . p y ,   t e s t _ e x t e n d e d _ f e a t u r e s . p y ,   t e s t _ m i n i _ a p p . p y ,   t e s t _ n e w _ f e a t u r e s . p y ,   t e s t _ s o c i a l _ f e a t u r e s . p y ,   t e s t _ p o p u l a r i t y _ s o c i a l . p y ,   t e s t _ s e c t i o n s . p y ,   t e s t _ s u p p o r t . p y ,   t e s t _ t e l e g r a m _ b o t . p y  
 -   C o v e r a g e :   c o r e   e n g i n e ,   a d s   i n t e g r a t i o n ,   a n t i - f r a u d ,   s p o n s o r e d   t a s k s ,   a f f i l i a t e   c o m m i s s i o n s ,   p r e m i u m   s u b s c r i p t i o n s ,   d a t a   i n s i g h t s   c o n s e n t ,   r e t e n t i o n   f e a t u r e s ,   p r o o f   g a l l e r y ,   f l a s h   s a l e s ,   c r a t e s ,   q u e s t s ,   c a l e n d a r ,   p r e s t i g e ,   s o c i a l   f e a t u r e s   ( f r i e n d s ,   b i o ,   p r o f i l e s ,   t r a n s l a t i o n ,   c h a t ) ,   p o p u l a r i t y / s o c i a l   ( p o p u l a r i t y ,   l i k e s ,   v i s i t s ,   c o i n   t r a n s f e r ,   p r i v a c y ,   t h e m e s ,   m e s s a g i n g )  
  
 # #   D e p l o y m e n t  
 -   R e n d e r - r e a d y   ( w e b h o o k   a u t o - r e g i s t r a t i o n )  
 -   E n v i r o n m e n t   v a r i a b l e s :   T E L E G R A M _ B O T _ T O K E N ,   M O N G O _ U R I ,   A D M I N _ K E Y ,   S E C R E T _ K E Y ,   A D M I N _ I D ,   M I N I _ A P P _ U R L ,   A D S _ P R O V I D E R ,   A F F I L I A T E _ B A S E _ U R L ,   V A P I D _ P R I V A T E _ K E Y ,   V A P I D _ P U B L I C _ K E Y ,   V A P I D _ C O N T A C T  
 -   G i t   b r a n c h :   m a i n  
  
 # #   D a r k   P a t t e r n s   I m p l e m e n t e d   ( E n g a g e m e n t   L a y e r )  
  
 # # #   C o u n t d o w n   T i m e r s  
 -   W i t h d r a w a l   c o o l d o w n   t i m e r   ( w i t h d r a w - c d )   � �    b l o c k s   r e - r e q u e s t   f o r   5   m i n u t e s   a f t e r   s u b m i s s i o n .  
  
 # # #   H i d d e n   C o s t s  
 -   P r o c e s s i n g   f e e   r e v e a l   o n   w i t h d r a w   a m o u n t   i n p u t   ( h i d d e n - f e e - b o x )   � �    5 %   f e e   +   R s 2   m i n i m u m   a p p e a r s   o n l y   a f t e r   u s e r   t y p e s   a m o u n t .  
  
 # # #   C o n f i r m s h a m i n g  
 -   O n b o a r d i n g   s k i p   b u t t o n :   g u i l t - t r i p   c o n f i r m   d i a l o g   ( " A r e   y o u   s u r e ?   S k i p p i n g   m e a n s   y o u   m i g h t   m i s s   o u t   o n   e x c l u s i v e   b e g i n n e r   b o n u s e s . . . " )  
 -   B a c k   b u t t o n s :   c o n f i r m   d i a l o g   w a r n i n g   a b o u t   l o s t   p r o g r e s s / e a r n i n g s .  
  
 # # #   D i s g u i s e d   A d s  
 -   S p o n s o r e d   t a s k   i n j e c t i o n   ( i n j e c t S p o n s o r e d T a s k )   � �    r a n d o m   s p o n s o r   t a s k s   m i x e d   i n t o   t a s k   l i s t   w i t h   d a s h e d   g o l d   b o r d e r   a n d   S P O N S O R E D   b a d g e .  
  
 # # #   F a k e   S o c i a l   P r o o f  
 -   R a n d o m i z e d   l i v e   u s e r   c o u n t e r   ( o n l i n e - c o u n t )   � �    f l u c t u a t e s   b e t w e e n   2 , 3 0 0 � �  3 , 1 0 0 .  
 -   R a n d o m i z e d   p a y o u t   c o u n t e r   ( p a y o u t - c o u n t )   � �    f l u c t u a t e s   b e t w e e n   R s 1 , 2 0 , 0 0 0 � �  R s 1 , 7 0 , 0 0 0 .  
  
 # # #   R o a c h   M o t e l  
 -   E x t r a   A c c o u n t   V e r i f i c a t i o n   s t e p   f o r   w i t h d r a w a l s   a b o v e   R s 5 0   ( r o a c h - s t e p )   � �    f a k e   2 - 4   s e c o n d   v e r i f i c a t i o n   d e l a y   b e f o r e   a l l o w i n g   w i t h d r a w a l .  
  
 # # #   H a p t i c   &   A u d i o   F e e d b a c k  
 -   T e l e g r a m   H a p t i c s   A P I   ( h a p t i c ( ) )   � �    i m p a c t O c c u r r e d   o n   n a v ,   s p i n ,   c o i n s ,   s u c c e s s ,   e r r o r .  
 -   W e b   A u d i o   A P I   s y n t h   ( p l a y S o u n d ( ) )   � �    c l i c k ,   c o i n ,   s p i n ,   s u c c e s s ,   e r r o r ,   s c r a t c h ,   r e w a r d ,   n a v   t o n e s .  
  
 # # #   O n b o a r d i n g   T u t o r i a l  
 -   4 - s t e p   f i r s t - t i m e   w a l k t h r o u g h   o v e r l a y   w i t h   d o t   i n d i c a t o r s   a n d   l o c a l S t o r a g e   p e r s i s t e n c e   ( x i o _ o n b o a r d e d ) .  
  
 # # #   W i t h d r a w a l   A n t i - F r a u d  
 -   D a i l y   l i m i t :   m a x   3   w i t h d r a w a l s / d a y .  
 -   W e e k l y   l i m i t :   m a x   R s 5 0 0 / w e e k .  
 -   A m o u n t   g a t e s :   R s 1 0 0 +   r e q u i r e s   7 - d a y   s t r e a k ;   R s 5 0 0 +   b l o c k e d .  
 -   K Y C   e n f o r c e m e n t   b e f o r e   a n y   w i t h d r a w a l .  
  
 # # #   A d   A n t i - F r a u d  
 -   C o m p l e t i o n   t i m e   v a l i d a t i o n   ( 3 s   m i n ,   1 2 0 s   m a x ) .  
 -   I P   a n d   d e v i c e   f i n g e r p r i n t i n g .  
 -   F r a u d   s c o r i n g   w i t h   a u t o - b l o c k   o n   t h r e s h o l d .  
  
 - - -  
 * * N o t e : * *   T h i s   i s   a   l i v i n g   d o c u m e n t .   A l l   f e a t u r e s   a r e   b u i l t   w i t h   f u t u r e - p r o o f i n g   i n   m i n d .   D a r k   p a t t e r n s   a r e   i n t e n t i o n a l l y   p r e s e r v e d   f o r   e n g a g e m e n t .  
 