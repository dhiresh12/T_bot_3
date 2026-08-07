# Xio PayPlus — Mini App Real Functionality + Dark Patterns TODOs

Goal: Make every mini-app panel actually work per project_info.txt, add dark
patterns/earning math, keep all 16 tests passing.

## Steps

- [ ] 1. app/ads.py — Add Google AdSense provider + revenue-share config (40-55% user share)
- [ ] 2. app/core.py — Tasks: reward 1000 coins + real platform urls (Telegram/YouTube/WhatsApp/Facebook)
- [ ] 3. app/core.py — watch_ads: $0.002 + coins 50-500, add `more_ads_codes` store + `redeem_more_ads(user_id, code)` (10 bonus ads)
- [ ] 4. app/core.py — process_successful_invite: real referral = +$0.005 wallet_bot (+ fewer coins)
- [ ] 5. app/core.py — request_withdrawal: UPI / bank / mobile detail validation (regex)
- [ ] 6. app/routes.py — Add `/api/ads/more/<user_id>` endpoint for more-ads code redeem
- [ ] 7. app/mini_app.py — Ads panel: back-to-back two 15s ads per completion, show ₹/$ + coins, more-ads backend, AdSense placeholder
- [ ] 8. app/mini_app.py — Task panel: "Join/Visit" real link + 1-minute verify timer → complete; reward 1000 + ₹0.01
- [ ] 9. app/mini_app.py — Invite panel: show real-referral $0.005 stats + dark urgency
- [ ] 10. app/mini_app.py — Withdraw panel: UPI/bank/mobile client-side validation + dark patterns
- [ ] 11. app/mini_app.py — Dark patterns: fake "X users withdrawing", streak/next-tier nudges, realistic fake users
- [ ] 12. Run tests (16 pass) + verify mini app locally

## Accepted
- Back-to-back two ads per completion
- Dark patterns: my pick (urgency, social proof, streak, loss-aversion)
- Google AdSense placeholder + 40-55% user revenue share

