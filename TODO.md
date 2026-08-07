# Mini App Fix Plan (based on project_info.txt)

## Objective
Make every mini-app function work (Ads, Task, Invite, Withdraw, Bonus, Spin) without errors, show user ID, and apply dark patterns.

## Bugs Found
1. `{translations_json}` → must be `{{translations_json|safe}}` (JS object crash → nothing works on click)
2. Ads panel completely missing (bottom nav had no Watch-Ad function)
3. User ID not shown (script crash prevents fetchData)
4. Unique ID needed for browser/direct-link users
5. Dark patterns needed: fake withdrawal feed on ALL panels, fake chat, tier progress, urgency

## Plan
- [x] Read project_info.txt thoroughly
- [x] Read mini_app.py
- [ ] Rebuild mini_app.py:
  - Fix `{{translations_json|safe}}`
  - Add Ads panel (Xio_PayPlus header + support + lang, Watch Ad 15s timer, daily limit 15, coins+$0.002, request-more-ads, live feed, chat)
  - Keep Home panel (spin wheel, dashboard, invites/tasks grid)
  - Task panel (channel/social follows with rewards)
  - Invite panel (referral link + copy/share + 2 bottom columns)
  - Withdraw panel (UPI/Bank/Mobile 3 options + requirements + history)
  - User ID from Telegram, unique browser ID otherwise (localStorage)
  - Dark patterns on every panel
- [ ] Fix/verify backend endpoints used (bonus, ad watch daily limit, withdraw reqs, invite)
- [ ] Run pytest (all pass)
- [ ] Verify all functions online
- [ ] Commit + push (auto-deploy)

