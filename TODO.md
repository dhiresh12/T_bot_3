# TASKS - Xio PayPlus Mini-App Improvements

## Plan (approved by user)

### 1. Shop Panel - Expanded with dark patterns
- [ ] Add new shop items: Coins→Money Exchange, Extra Spin Ticket, Bonus Ads Pack, Streak Boost
- [ ] Add server-side `exchange_coins_to_money` method in BotEngine
- [ ] Add `/api/shop/exchange-coins` endpoint
- [ ] Update shop UI to render new items + exchange section

### 2. Spin Mystery Box Fix
- [ ] Fix "Claim it" button so the surprise box closes properly
- [ ] Ensure reward is credited and box closes on claim

### 3. Tasks - 20-second join + heart (2 steps)
- [ ] Add 20-second countdown timer when user opens task channel
- [ ] Add "Send ❤️" heart step (2-step verification feel)
- [ ] Enable "I've Joined - Get Reward" only after timer + 2 steps

### 4. Realistic Online/Paid numbers
- [ ] Reduce online count to realistic range (130-260)
- [ ] Reduce paid today to realistic range
- [ ] Slow gradual fluctuation

### 5. Support Redirect
- [ ] On submit, redirect user directly to support channel with message

### 6. UI/UX + Lighting/Glow effects
- [ ] Add glow/shimmer effects to cards, buttons, wheel, balance
- [ ] Premium social-media-like visual polish

## Backend (core.py)
- [ ] Add `exchange_coins_to_money` method
- [ ] Add new shop items to `shop_items`
- [ ] Add `spin_ticket`, `bonus_ads`, `streak_boost` effects

## Routes (routes.py)
- [ ] Add `/api/shop/exchange-coins` endpoint
- [ ] Add `/api/shop/buy/extra-spin` etc. if needed

## Tests
- [ ] Add tests for new shop items and exchange
- [ ] Run full test suite (30+ tests must pass)
- [ ] Validate JS (no `=>`, `?.`, `??`)
