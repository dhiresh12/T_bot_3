from __future__ import annotations

import json
import os

from flask import Flask, render_template_string

from app.ads import AdsManager
from app.config import load_config
from app.core import BotEngine
from app.routes import bp as routes_bp


def create_app(engine: BotEngine | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = load_config().secret_key

    current_engine = engine or BotEngine(storage_path="bot_data.db")
    ads_manager = AdsManager(provider=load_config().ads_provider)

    app.config["engine"] = current_engine
    app.config["ads_manager"] = ads_manager
    app.register_blueprint(routes_bp)

    # --- Auto-register Telegram webhook on startup ---
    try:
        from app.telegram_bot import TelegramBotService
        bot_service = TelegramBotService(engine=current_engine)
        external_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
        if external_url:
            webhook_url = external_url.rstrip("/") + "/webhook"
            bot_service.set_webhook(webhook_url)
        else:
            print("[mini-app][info] RENDER_EXTERNAL_URL/WEBHOOK_URL not set; skipping webhook registration.")
    except Exception as exc:  # noqa: BLE001
        print(f"[mini-app][warn] Webhook registration skipped: {exc}")

    HTML = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{app_name}}</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
          :root {
            --bg-dark: #0f172a; --bg-light: #1e293b; --primary: #3b82f6;
            --text-light: #f1f5f9; --text-muted: #94a3b8; --accent: #84cc16;
            --gold: #f59e0b; --danger: #ef4444; --success: #22c55e;
          }
          * { box-sizing: border-box; }
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-dark); color: var(--text-light); margin: 0; padding: 0 0 80px 0; }
          .container { max-width: 480px; margin: 0 auto; padding: 16px; }
          .app-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; background: linear-gradient(135deg, #1e293b, #0f172a); border-bottom: 1px solid #1e293b; position: sticky; top: 0; z-index: 10; }
          .brand { font-size: 18px; font-weight: 800; background: linear-gradient(90deg, #3b82f6, #84cc16); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
          .brand small { display: block; font-size: 10px; font-weight: 500; color: var(--text-muted); -webkit-text-fill-color: var(--text-muted); }
          .header-actions { display: flex; align-items: center; gap: 8px; }
          .icon-btn { background: var(--bg-light); color: var(--text-light); border: none; border-radius: 50%; width: 38px; height: 38px; font-size: 17px; cursor: pointer; position: relative; }
          .page { display: none; animation: fadeIn 0.3s; }
          .page.active { display: block; }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
          .user-header { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
          .avatar { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), #60a5fa); display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; border: 2px solid #475569; }
          .user-info { flex-grow: 1; }
          .user-info h1 { margin: 0; font-size: 18px; }
          .user-info p { margin: 0; color: var(--text-muted); font-size: 13px; }
          .streak-pill { display: inline-flex; align-items: center; gap: 4px; background: linear-gradient(135deg,#f97316,#ef4444); color:#fff; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 700; margin-top: 6px; }
          .balance-card { background: linear-gradient(135deg, #1d4ed8, #7c3aed); padding: 22px; border-radius: 18px; text-align: center; margin-bottom: 18px; position: relative; overflow: hidden; }
          .balance-card::after { content:''; position:absolute; top:-40%; right:-20%; width:160px; height:160px; background:radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%); pointer-events:none; }
          .balance-card .label { font-size: 13px; opacity: 0.85; }
          .balance-card .amount { font-size: 38px; font-weight: 800; margin: 4px 0; }
          .balance-card .coins { font-size: 15px; opacity: 0.95; }
          .tier-progress { display: flex; justify-content: space-between; font-size: 12px; margin-top: 14px; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 10px; }
          .progress-bar { height: 6px; background: rgba(255,255,255,0.2); border-radius: 4px; margin-top: 8px; overflow: hidden; }
          .progress-fill { height: 100%; background: linear-gradient(90deg, #84cc16, #facc15); border-radius: 4px; transition: width 0.6s; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
          .grid-card { background-color: var(--bg-light); padding: 16px; border-radius: 14px; text-align: center; }
          .grid-card .value { font-size: 24px; font-weight: 700; }
          .grid-card .label { font-size: 12px; color: var(--text-muted); }
          .section-title { font-size: 14px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 8px; }
          .btn { display: block; width: 100%; background: var(--primary); color: white; border: none; padding: 13px; border-radius: 12px; font-size: 15px; font-weight: 700; cursor: pointer; margin-top: 12px; }
          .btn:disabled { opacity: 0.5; cursor: not-allowed; }
          .btn-gold { background: linear-gradient(135deg, #f59e0b, #f97316); }
          .btn-green { background: linear-gradient(135deg, #22c55e, #16a34a); }
          .btn-sm { width: auto; padding: 8px 14px; font-size: 13px; margin-top: 0; }
          .back-btn { background: none; border: none; color: var(--primary); font-size: 15px; cursor: pointer; margin-bottom: 8px; padding: 0; font-weight: 600; }
          .live-feed { margin-top: 18px; background: radial-gradient(circle at 30% 0, rgba(59,130,246,0.15), transparent); background-color: var(--bg-light); padding: 12px; border-radius: 14px; height: 110px; overflow-y: auto; font-size: 12px; }
          .live-feed p { margin: 0 0 8px; animation: slideIn 0.5s; }
          @keyframes slideIn { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }
          .chat-box { margin-top: 18px; background: var(--bg-light); padding: 12px; border-radius: 14px; }
          .chat-msg { margin-bottom: 8px; font-size: 13px; display:flex; gap:6px; align-items:flex-start; }
          .chat-msg .avatar-s { width:26px;height:26px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0; }
          .chat-msg .who { font-weight: 700; color: var(--primary); margin-right:4px; }
          .chat-msg .bubble { background:var(--bg-dark); padding:6px 10px; border-radius:12px; }
          .chat-msg.mine .bubble { background:rgba(59,130,246,0.25); }
          .chat-input { display: flex; gap: 8px; margin-top: 10px; align-items:center; }
          .chat-input input { flex: 1; padding: 10px; background: var(--bg-dark); border: 1px solid #334155; border-radius: 10px; color: white; }
          .chat-input button { background: var(--primary); color: white; border: none; border-radius: 10px; padding: 0 14px; font-size: 16px; cursor: pointer; height:42px; }
          .chat-tools { display:flex; gap:6px; margin-top:8px; }
          .tool-chip { background:var(--bg-dark); border:1px solid #334155; color:var(--text-light); border-radius:8px; padding:6px 10px; font-size:12px; cursor:pointer; }
          .gif-panel { display:none; background:var(--bg-dark); border:1px solid #334155; border-radius:10px; padding:8px; margin-top:8px; }
          .gif-panel.show { display:flex; flex-wrap:wrap; gap:6px; }
          .gif-item { font-size:26px; cursor:pointer; padding:4px; }
          .ad-box { text-align: center; padding: 28px 16px; background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 16px; margin-top: 8px; }
          .ad-circle { width: 90px; height: 90px; border-radius: 50%; background: var(--bg-light); border: 4px solid var(--primary); display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; margin: 0 auto 16px; color: var(--text-light); }
          .ad-timer { font-size: 14px; color: var(--text-muted); margin-top: 8px; }
          .ad-progress { height:6px; background:rgba(255,255,255,0.15); border-radius:4px; margin-top:12px; overflow:hidden; }
          .ad-progress-fill { height:100%; width:0%; background:linear-gradient(90deg,#22c55e,#facc15); transition:width 0.3s; }
          .daily-limit { display: flex; justify-content: space-between; background: var(--bg-light); padding: 10px 14px; border-radius: 12px; margin-top: 14px; font-size: 14px; }
          .daily-limit .n { font-weight: 700; color: var(--gold); }
          .task-item { background-color: var(--bg-light); padding: 14px; border-radius: 14px; margin-bottom: 12px; }
          .task-item.completed { opacity: 0.55; }
          .task-info h3 { margin: 0 0 4px; font-size: 15px; }
          .task-info p { margin: 0; font-size: 12px; color: var(--text-muted); }
          .completed-badge { color: var(--success); font-weight: 700; }
          .invite-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 16px; }
          .invite-stats .card { background: var(--bg-light); padding: 16px; border-radius: 14px; text-align: center; }
          .invite-stats .card .v { font-size: 22px; font-weight: 800; color: var(--gold); }
          .invite-link-box { display: flex; gap: 8px; margin-top: 12px; }
          .invite-link-box input { flex: 1; padding: 12px; background: var(--bg-light); border: 1px solid #334155; border-radius: 10px; color: white; font-size: 12px; }
          .invite-link-box button { background: var(--bg-light); border: 1px solid #334155; color: var(--text-light); border-radius: 10px; padding: 0 12px; cursor: pointer; }
          .method-row { display: flex; gap: 10px; margin-top: 12px; }
          .method { flex: 1; background: var(--bg-light); border: 1px solid #334155; padding: 14px; border-radius: 14px; text-align: center; cursor: pointer; }
          .method.active { border-color: var(--primary); background: rgba(59,130,246,0.15); }
          .method .em { font-size: 24px; }
          .method .nm { font-size: 12px; margin-top: 4px; }
          .req-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
          .req-item { background-color: var(--bg-light); padding: 12px; border-radius: 12px; font-size: 12px; }
          .req-item .progress { font-weight: 800; font-size: 16px; color: var(--gold); }
          .req-item.ok .progress { color: var(--success); }
          .withdraw-form input { width: 100%; padding: 12px; margin-bottom: 10px; background-color: var(--bg-light); border: 1px solid #334155; color: white; border-radius: 10px; }
          .method-form { display: none; }
          .method-form.active { display: block; }
          .history-item { background-color: var(--bg-light); padding: 12px; border-radius: 12px; margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }
          .history-item .status { font-weight: 700; text-transform: uppercase; font-size: 11px; padding: 3px 8px; border-radius: 6px; }
          .history-item .status.pending { color: #f59e0b; background: rgba(245,158,11,0.15); }
          .history-item .status.approved { color: #22c55e; background: rgba(34,197,94,0.15); }
          .history-item .status.rejected { color: #ef4444; background: rgba(239,68,68,0.15); }
          .surprise-box { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:200; align-items:center; justify-content:center; flex-direction:column; }
          .surprise-box.show { display:flex; }
          .gift-box { width:120px; height:120px; background:linear-gradient(135deg,#f59e0b,#ef4444); border-radius:20px; display:flex; align-items:center; justify-content:center; font-size:60px; cursor:pointer; animation:giftPulse 1.5s infinite; position:relative; box-shadow:0 0 40px rgba(245,158,11,0.6); }
          @keyframes giftPulse { 0%,100%{ transform:scale(1);} 50%{ transform:scale(1.08);} }
          .gift-stars { position:absolute; inset:-10px; pointer-events:none; }
          .gift-star { position:absolute; color:#facc15; animation:twinkle 1.2s infinite; font-size:22px; }
          @keyframes twinkle { 0%,100%{opacity:1; transform:scale(1);} 50%{opacity:0.3; transform:scale(0.6);} }
          .surprise-msg { color:#facc15; font-size:20px; font-weight:800; margin-top:20px; text-align:center; }
          .surprise-sub { color:var(--text-muted); font-size:14px; margin-top:8px; text-align:center; }
          .open-result { display:none; text-align:center; }
          .open-result.show { display:block; }
          .wheel-container { position: relative; width: 250px; height: 250px; margin: 24px auto; }
          .wheel { width: 100%; height: 100%; border-radius: 50%; background-image: conic-gradient(#ef4444 0deg 60deg, #f97316 60deg 120deg, #84cc16 120deg 180deg, #3b82f6 180deg 240deg, #8b5cf6 240deg 300deg, #f59e0b 300deg 360deg); transition: transform 4s cubic-bezier(0.25, 0.1, 0.25, 1); border: 6px solid #facc15; box-shadow:0 0 30px rgba(245,158,11,0.4); }
          .wheel-pointer { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 18px solid transparent; border-right: 18px solid transparent; border-top: 26px solid #facc15; z-index: 2; }
          .wheel-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-weight: bold; font-size: 14px; text-shadow: 1px 1px 3px black; }
          .wheel-label { position:absolute; font-size:11px; color:white; font-weight:700; text-shadow:1px 1px 2px rgba(0,0,0,0.6); }
          .status-msg { text-align: center; margin-top: 12px; color: var(--accent); font-weight: 600; min-height: 20px; }
          .support-box { padding: 16px; margin-top: 12px; }
          .support-box textarea { width: 100%; height: 100px; padding: 12px; background: var(--bg-light); border: 1px solid #334155; border-radius: 12px; color: white; font-family: inherit; resize:vertical; }
          .support-links { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
          .support-links a { flex:1; background:var(--bg-light); border:1px solid #334155; border-radius:10px; color:var(--text-light); text-align:center; padding:10px; font-size:12px; text-decoration:none; }
          .nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg-light); border-top: 1px solid #334155; display: flex; justify-content: space-around; padding: 8px 0 calc(8px + env(safe-area-inset-bottom)); z-index: 100; }
          .nav-item { color: var(--text-muted); background: none; border: none; cursor: pointer; text-align: center; font-size: 10px; padding: 0; flex: 1; font-family: inherit; }
          .nav-item.active { color: var(--primary); }
          .nav-item .em { font-size: 22px; display: block; }
          .badge-note { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.4); color: #fcd34d; padding: 10px 14px; border-radius: 12px; font-size: 12px; margin-top: 12px; }
          .flash { animation: flash 1s ease; }
          @keyframes flash { 0% { opacity: 0.3;} 100% { opacity: 1; } }
          .urgency { display:flex; gap:8px; margin-top:12px; }
          .urgency .box { flex:1; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.4); border-radius:10px; padding:8px; text-align:center; font-size:11px; color:#fca5a5; }
          .urgency .box b { font-size:16px; color:#f87171; display:block; }
          .shop-item { background:var(--bg-light); border-radius:14px; padding:14px; margin-bottom:12px; display:flex; align-items:center; gap:12px; }
          .shop-item .em { font-size:34px; }
          .shop-item .info { flex:1; }
          .shop-item .info b { font-size:15px; }
          .shop-item .info p { margin:2px 0 0; font-size:12px; color:var(--text-muted); }
          .shop-item .price { color:var(--gold); font-weight:700; font-size:13px; }
          .lang-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:12px; }
          .lang-chip { background:var(--bg-light); border:1px solid #334155; border-radius:12px; padding:12px; text-align:center; cursor:pointer; font-size:14px; }
          .lang-chip.active { border-color:var(--primary); background:rgba(59,130,246,0.15); }
        </style>
      </head>
      <body>
        <div class="app-header">
          <div class="brand">Xio_PayPlus<small>Earn • Play • Win</small></div>
          <div class="header-actions">
            <button class="icon-btn" id="shop-btn" onclick="openShop()">🛒</button>
            <button class="icon-btn" id="support-btn" onclick="openSupport()">💬</button>
            <button class="icon-btn" id="lang-btn" onclick="openLang()">🌐</button>
          </div>
        </div>

        <div class="container">
          <!-- HOME -->
          <div id="page-home" class="page active">
            <div class="user-header">
              <div id="avatar" class="avatar">?</div>
              <div class="user-info">
                <h1 id="user-name">Guest</h1>
                <p id="user-id">ID: ...</p>
                <div class="streak-pill" id="streak-pill">🔥 0</div>
              </div>
            </div>

            <div class="balance-card">
              <div class="label" data-translate-key="total_balance">Total Earning</div>
              <div id="balance-amount" class="amount">₹0.00</div>
              <div id="balance-coins" class="coins">0 <span data-translate-key="coins">Coins</span></div>
              <div class="tier-progress">
                <span id="current-tier">🥉 Bronze</span>
                <span id="next-tier">Next: Silver</span>
              </div>
              <div class="progress-bar"><div id="tier-progress-fill" class="progress-fill" style="width:0%"></div></div>
            </div>

            <div class="urgency">
              <div class="box"><b id="online-count">2,341</b> Online now</div>
              <div class="box"><b id="payout-count">₹1,28,400</b> Paid today</div>
            </div>

            <div class="grid">
              <div class="grid-card"><div id="invites-count" class="value">0</div><div class="label" data-translate-key="invites">Invites</div></div>
              <div class="grid-card"><div id="tasks-count" class="value">0</div><div class="label" data-translate-key="tasks_done">Tasks Done</div></div>
            </div>

            <div class="section-title" data-translate-key="spin_title">🎁 Daily Gift Spin</div>
            <div class="wheel-container">
              <div class="wheel-pointer"></div>
              <div id="wheel" class="wheel"></div>
            </div>
            <button id="spin-button" class="btn btn-gold" onclick="spinWheel()">🎁 Spin for a Gift!</button>
            <p id="spin-status" class="status-msg"></p>

            <!-- Surprise / Gift reveal -->
            <div id="surprise-box" class="surprise-box">
              <div class="gift-box" id="gift-box" onclick="openGift()">
                <span id="gift-emoji">🎁</span>
                <div class="gift-stars" id="gift-stars"></div>
              </div>
              <div class="surprise-msg" id="surprise-msg">Tap the gift to open it!</div>
              <div class="surprise-sub" id="surprise-sub">Your reward is waiting 💰</div>
              <div class="open-result" id="open-result">
                <div style="font-size:60px;margin-top:10px;" id="open-gift-emoji">🎉</div>
                <div class="surprise-msg" id="open-msg">You won!</div>
                <button class="btn btn-gold" style="width:220px;margin-top:20px;" onclick="closeSurprise()">Great! Claim it</button>
              </div>
            </div>

            <div class="live-feed" id="live-feed">
              <p data-translate-key="connecting_feed">Connecting to live feed...</p>
            </div>

            <div class="chat-box">
              <div style="font-weight:700;font-size:13px;margin-bottom:8px;">💬 Community Chat <span style="color:var(--text-muted);font-weight:400;font-size:11px;">• <span id="chat-online">2,341</span> online</span></div>
              <div id="chat-messages"></div>
              <div class="chat-tools">
                <button class="tool-chip" onclick="toggleGif('chat')">🎞️ GIF</button>
                <button class="tool-chip" onclick="sendVoice()">🎤 Voice</button>
              </div>
              <div class="gif-panel" id="gif-panel-chat"></div>
              <div class="chat-input">
                <input id="chat-input" placeholder="Type a message...">
                <button id="send-chat-btn" onclick="sendChat()">➤</button>
              </div>
            </div>
          </div>

          <!-- ADS -->
          <div id="page-ads" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2>📺 Watch Ads & Earn</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Earn up to ₹0.002 + 50-500 coins per ad. Free money, just watch!</p>
            <div class="ad-box">
              <div class="ad-circle" id="ad-circle">▶</div>
              <div style="font-weight:700;font-size:15px;" id="ad-num-label">Ad 1 of 2</div>
              <button id="watch-ad-btn" class="btn btn-green" onclick="watchAdStart()">▶ Watch Ad & Earn</button>
              <div class="ad-timer" id="ad-timer">Each ad takes just 15 seconds</div>
              <div class="ad-progress"><div class="ad-progress-fill" id="ad-progress-fill"></div></div>
              <div class="daily-limit"><span>📺 Daily Ads</span><span class="n" id="daily-ads-count">0 / 20</span></div>
            </div>
            <div style="text-align:center;font-size:12px;color:var(--text-muted);margin-top:8px;">💡 Watch <b>2 ads back-to-back</b> = 1 reward</div>
            <div class="ad-box" id="more-ads-box" style="display:none;">
              <p style="font-size:13px;color:var(--text-muted);margin:0 0 8px;">Hit your daily limit? Get 10 more ads!</p>
              <div class="invite-link-box">
                <input id="more-ads-code" placeholder="Enter more-ads code" style="flex:1;">
                <button id="redeem-more-ads-btn" class="btn-sm" onclick="redeemMoreAds()">Redeem</button>
              </div>
              <p id="more-ads-status" style="font-size:12px;margin-top:8px;color:var(--gold);"></p>
            </div>
            <div class="live-feed" id="live-feed-ads"><p>Live payouts ⚡ Loading...</p></div>
            <div class="chat-box">
              <div style="font-weight:700;font-size:13px;margin-bottom:8px;">💬 Watchers Chat</div>
              <div id="chat-messages-ads"></div>
            </div>
          </div>

          <!-- TASKS -->
          <div id="page-tasks" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2 data-translate-key="tasks_title">📋 Tasks</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Complete tasks to earn coins & unlock withdrawals!</p>
            <div id="task-list"><p>Loading tasks...</p></div>
            <p id="task-status" class="status-msg"></p>
          </div>

          <!-- INVITE -->
          <div id="page-invite" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2 data-translate-key="invite_title">👥 Invite Friends</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Share your link & earn instant rewards!</p>
            <div class="badge-note">🔥 <b>₹0.005 on every successful invite!</b> Share with 10 friends to unlock withdrawal.</div>
            <p data-translate-key="invite_link_label" style="font-size:13px;margin:14px 0 6px;">Your personal invite link:</p>
            <div class="invite-link-box">
              <input id="invite-link" type="text" readonly>
              <button id="copy-invite-btn" onclick="copyInvite()">📋</button>
            </div>
            <button id="share-invite-btn" class="btn btn-gold" onclick="shareInvite()" data-translate-key="share_invite_button">🚀 Share Invite Link</button>
            <div class="invite-stats">
              <div class="card"><div class="v" id="invite-count-box">0</div><div style="font-size:12px;color:var(--text-muted);">Invites</div></div>
              <div class="card"><div class="v" id="invite-earned-box">₹0.000</div><div style="font-size:12px;color:var(--text-muted);">Referral Earnings</div></div>
            </div>
            <div class="live-feed" id="live-feed-invite"><p>Recent referrals 🎉 Loading...</p></div>
          </div>

          <!-- WITHDRAW -->
          <div id="page-wallet" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2 data-translate-key="withdraw_title">💰 Withdraw Funds</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Get your hard-earned money!</p>
            <div class="section-title">Choose Method</div>
            <div class="method-row">
              <div class="method active" data-method="upi" onclick="selectMethod('upi')"><div class="em">🏦</div><div class="nm">UPI</div></div>
              <div class="method" data-method="bank" onclick="selectMethod('bank')"><div class="em">🏧</div><div class="nm">Bank</div></div>
              <div class="method" data-method="mobile" onclick="selectMethod('mobile')"><div class="em">📱</div><div class="nm">Mobile Top-up</div></div>
            </div>
            <div class="section-title" data-translate-key="requirements_title">Withdrawal Requirements</div>
            <div class="req-grid" id="req-grid"><div class="req-item">Loading...</div></div>
            <div class="section-title" data-translate-key="withdraw_form_title">Request Payout</div>
            <div class="withdraw-form">
              <div class="method-form active" id="upi-form"><input id="withdraw-upi" type="text" placeholder="your-upi-id@okhdfcbank"></div>
              <div class="method-form" id="bank-form"><input id="withdraw-bank" type="text" placeholder="Account Number"><input id="withdraw-ifsc" type="text" placeholder="IFSC Code"></div>
              <div class="method-form" id="mobile-form"><input id="withdraw-mobile" type="text" placeholder="10-digit Mobile Number"></div>
              <input id="withdraw-amount" type="number" placeholder="Amount (min ₹10)">
              <button id="withdraw-btn" class="btn btn-green" onclick="requestWithdrawal()">💸 Request Withdrawal</button>
              <p id="withdraw-status" class="status-msg"></p>
            </div>
            <div class="section-title" data-translate-key="history_title">History</div>
            <div id="history-list"><div class="history-item"><span data-translate-key="no_history">No withdrawal history yet.</span></div></div>
            <div class="live-feed" id="live-feed-withdraw" style="margin-top:14px;"><p>Successful withdrawals ✅ Loading...</p></div>
          </div>

          <!-- SUPPORT -->
          <div id="page-support" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2>💬 Customer Support</h2>
            <p style="color:var(--text-muted);font-size:13px;">Type your problem, tap Submit, and you'll be redirected to our support group with your message!</p>
            <div id="faq-list" style="margin-top:12px;"></div>
            <div class="support-box">
              <textarea id="support-message" placeholder="Type your problem here..."></textarea>
              <button id="send-support-btn" class="btn btn-green" onclick="sendSupport()">📨 Submit & Join Support Group</button>
              <div class="support-links">
                <a id="support-group-link" href="#" target="_blank">👥 Support Group</a>
                <a id="admin-support-link" href="#" target="_blank">👑 Admin Support</a>
              </div>
              <p id="support-status" class="status-msg"></p>
            </div>
          </div>

          <!-- SHOP -->
          <div id="page-shop" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2>🛒 Shop</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Spend your coins on gifts & boosts!</p>
            <div id="shop-list"></div>
            <p id="shop-status" class="status-msg"></p>
          </div>

          <!-- LANGUAGE -->
          <div id="page-lang" class="page">
            <button class="back-btn" onclick="showPage('home')">← Back</button>
            <h2>🌐 Choose Language</h2>
            <p style="color:var(--text-muted);font-size:13px;margin-top:-6px;">Select your preferred language</p>
            <div class="lang-grid" id="lang-grid"></div>
          </div>
        </div>

        <!-- Bottom Navigation -->
        <div class="nav">
          <button class="nav-item active" data-page="home" onclick="showPage('home')"><span class="em">🏠</span><span data-translate-key="nav_home">Home</span></button>
          <button class="nav-item" data-page="ads" onclick="showPage('ads')"><span class="em">▶</span><span data-translate-key="nav_ads">Ads</span></button>
          <button class="nav-item" data-page="tasks" onclick="showPage('tasks')"><span class="em">📋</span><span data-translate-key="nav_tasks">Tasks</span></button>
          <button class="nav-item" data-page="invite" onclick="showPage('invite')"><span class="em">👥</span><span data-translate-key="nav_invite">Invite</span></button>
          <button class="nav-item" data-page="wallet" onclick="showPage('wallet')"><span class="em">💰</span><span data-translate-key="nav_wallet">Withdraw</span></button>
        </div>

        <script>
          function getTelegram() {
            try { if (window.Telegram && window.Telegram.WebApp) return window.Telegram.WebApp; } catch (e) {}
            return null;
          }
          const tg = getTelegram();
          if (tg) { try { tg.expand(); } catch (e) {} }

          function getOrCreateBrowserId() {
            try {
              let id = localStorage.getItem('xio_user_id');
              if (!id) {
                id = 'br' + Math.floor(1000000 + Math.random() * 8999999);
                localStorage.setItem('xio_user_id', id);
              }
              const numeric = id.replace(/[^0-9]/g, '');
              return numeric ? numeric : '777';
            } catch (e) { return '777'; }
          }
          const userId = (function(){
            try {
              const u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
              if (u && u.id) return u.id;
            } catch (e) {}
            return getOrCreateBrowserId();
          })();
          const userName = (function(){
            try {
              const u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
              if (u && u.first_name) return u.first_name;
            } catch (e) {}
            return 'Guest';
          })();

          const translations = {{translations_json | safe}};
          const langConfig = {{lang_config_json | safe}};
          const botUsername = '{{bot_username}}';
          const supportLinks = {{support_links_json | safe}};
          let currentLang = 'en';
          try { currentLang = localStorage.getItem('xio_lang') || 'en'; } catch (e) {}

          let selectedMethod = 'upi';
          let adTimer = null;
          let adCount = 0; // counts ads watched in current session pair
          const AD_SECONDS = 15;
          const ADS_PER_REWARD = 2;

          // --- Realistic fake users (varied names, avoid repetition) ---
          const fakeUsers = [
            {n:'Aarav',e:'😎'},{n:'Priya',e:'💪'},{n:'Rohit',e:'🔥'},{n:'Ananya',e:'✨'},{n:'Vikram',e:'🚀'},
            {n:'Sneha',e:'🌸'},{n:'Karan',e:'💯'},{n:'Neha',e:'😍'},{n:'John',e:'👍'},{n:'Maria',e:'🎉'},
            {n:'Rahul',e:'⚡'},{n:'Sara',e:'💖'},{n:'Amit',e:'🏆'},{n:'Pooja',e:'🌈'},{n:'Deepak',e:'💎'},
            {n:'Ritu',e:'😊'},{n:'Kavita',e:'🌟'},{n:'Sunil',e:'💪'},{n:'Ravi',e:'🥳'},{n:'Fatima',e:'🌺'},
            {n:'Wei',e:'🐉'},{n:'Kenji',e:'⛩️'},{n:'Alex',e:'🎮'},{n:'Sofia',e:'🌹'},{n:'Arjun',e:'🦁'},{n:'Meera',e:'🦋'}
          ];
          const usedChatNames = {};
          function pickFakeUser() {
            let u;
            do { u = fakeUsers[Math.floor(Math.random() * fakeUsers.length)]; } while (usedChatNames[u.n] && Math.random() < 0.8);
            usedChatNames[u.n] = true;
            return u;
          }
          const fakeMsgs = [
            'Just got ₹120 payout!','Joined yesterday, loving it 💰','Which task pays best?','Another day, another payout 🔥',
            '10 invites done, trying withdrawal!','This is legit guys 👌','Hit my ad target today 🎯','Refer 10 friends to unlock withdraw',
            'The gift spin is so fun 🎁','Cashed out ₹85 today!','Keep going everyone 💪','Best earning bot ever 🔥',
            '3 more ads and I reach 80!','Just opened a diamond box 💎','Who else is on a streak?','My referral is working great!'
          ];
          const fakeNumbers = [];
          for (let i = 0; i < 30; i++) {
            let d = String(Math.floor(6000000000 + Math.random() * 3999999999));
            fakeNumbers.push(d.slice(0,2) + '*****' + d.slice(7));
          }
          const fakeFeedTemplates = [
            (n,nu,amt)=>n + ' ' + nu + ' ₹' + amt.toFixed(2) + ' successfully withdrawal 🎉',
            (n,nu,amt)=>n + ' just withdrew ₹' + amt.toFixed(2) + ' (UPI ' + nu + ')',
            (n,nu,amt)=> n + ' earned ₹' + amt.toFixed(2) + ' payout sent! 💸',
            (n,nu,amt)=>n + ' ' + nu + ' withdrew ₹' + amt.toFixed(2) + ' Successfully ✅',
            (n,nu,amt)=>'Payment confirmed: ' + n + ' → ₹' + amt.toFixed(2) + ' 🎊'
          ];

          function fakeFeedLine() {
            const u = pickFakeUser();
            const nu = fakeNumbers[Math.floor(Math.random() * fakeNumbers.length)];
            const amt = 50 + Math.random() * 100;
            const tmpl = fakeFeedTemplates[Math.floor(Math.random() * fakeFeedTemplates.length)];
            return tmpl(u.n, nu, amt);
          }

          function injectFeed(containerId) {
            const el = document.getElementById(containerId);
            if (!el) return;
            const p = document.createElement('p');
            p.innerText = fakeFeedLine();
            el.prepend(p);
            while (el.children.length > 8) el.lastChild.remove();
          }

          function t(key) {
            try { return translations[currentLang]?.ui[key] || translations['en']?.ui[key] || key; } catch (e) { return key; }
          }
          function translateUI() {
            document.querySelectorAll('[data-translate-key]').forEach(function(el){
              el.innerText = t(el.dataset.translateKey);
            });
          }

          function openLang() {
            showPage('lang');
            const grid = document.getElementById('lang-grid');
            grid.innerHTML = '';
            for (const code in langConfig) {
              const cfg = langConfig[code];
              const c = document.createElement('div');
              c.className = 'lang-chip' + (code === currentLang ? ' active' : '');
              c.innerText = cfg.flag + ' ' + cfg.label;
              c.onclick = function(){ currentLang = code; try{localStorage.setItem('xio_lang', code);}catch(e){} translateUI(); fetchData(true); };
              grid.appendChild(c);
            }
          }

          async function fetchData() {
            try {
              const response = await fetch('/api/dashboard/' + userId);
              if (!response.ok) throw new Error('Dashboard API error');
              const data = await response.json();
              updateUI(data);
            } catch (e) {
              document.getElementById('user-id').innerText = 'ID: ' + userId;
              document.getElementById('user-name').innerText = userName;
              document.getElementById('avatar').innerText = (userName || 'G').charAt(0).toUpperCase();
            }
          }

          function updateUI(data) {
            document.getElementById('avatar').innerText = (data.name || 'G').charAt(0).toUpperCase();
            document.getElementById('user-name').innerText = data.name;
            document.getElementById('user-id').innerText = 'ID: ' + data.user_id;
            document.getElementById('balance-amount').innerText = '₹' + Number(data.wallet_rupee_equivalent || 0).toFixed(2);
            document.getElementById('balance-coins').innerText = Number(data.coins || 0).toLocaleString() + ' ' + t('coins');
            document.getElementById('current-tier').innerText = (data.engagement && data.engagement.tier) || '🥉 Bronze';
            document.getElementById('next-tier').innerText = (data.engagement && data.engagement.next_tier) ? (t('next_tier_prefix') + ' ' + data.engagement.next_tier) : '';
            const coins = data.coins || 0;
            const pct = Math.max(2, Math.min(99, (coins % 10000) / 100));
            document.getElementById('tier-progress-fill').style.width = pct + '%';

            // Snap-style streak display
            const streak = data.snap_streak || 0;
            document.getElementById('streak-pill').innerText = '🔥 ' + streak + (streak > 0 ? ' day streak' : '');

            document.getElementById('invites-count').innerText = data.invites || 0;
            document.getElementById('tasks-count').innerText = (data.tasks && data.tasks.length) || 0;
            document.getElementById('invite-link').value = 'https://t.me/' + botUsername + '?start=' + data.user_id;
            document.getElementById('invite-count-box').innerText = data.invites || 0;
            document.getElementById('invite-earned-box').innerText = '₹' + (Number(data.invites||0) * 0.005).toFixed(3);
            document.getElementById('daily-ads-count').innerText = (data.completed_ads || 0) + ' / 20';

            injectFeed('live-feed');
            injectFeed('live-feed-ads');
            injectFeed('live-feed-invite');
            injectFeed('live-feed-withdraw');

            renderTasks(data);
            renderShop();
            const reqs = data.withdrawal_reqs || {};
            const doneTasks = (data.tasks || []).length;
            reqGrid(data, reqs, doneTasks);
            renderHistory(data);
            document.getElementById('more-ads-box').style.display = ((data.completed_ads || 0) >= (reqs.min_ads || 80)) ? 'block' : 'none';
            translateUI();
          }

          function reqGrid(data, reqs, doneTasks) {
            const invites = data.invites || 0;
            const ads = data.completed_ads || 0;
            const items = [
              {label: t('min_invites'), v: invites, m: reqs.min_invites||10},
              {label: t('min_tasks'), v: doneTasks, m: reqs.min_tasks||5},
              {label: t('min_ads'), v: ads, m: reqs.min_ads||80},
              {label: 'Total Earned', v: '₹' + (Number(data.wallet_rupee_equivalent||0)).toFixed(2), m: '₹10'}
            ];
            let html = '';
            items.forEach(function(it){
              const ok = (typeof it.v === 'number') ? it.v >= parseFloat(it.m) : true;
              html += '<div class="req-item' + (ok ? ' ok' : '') + '">' + it.label +
                '<br><span class="progress">' + (typeof it.v === 'number' ? it.v + ' / ' + it.m : it.v) + '</span></div>';
            });
            document.getElementById('req-grid').innerHTML = html;
          }

          // --- TASKS: open channel first, then verify ---
          let pendingTask = null;
          function renderTasks(data) {
            const listEl = document.getElementById('task-list');
            const available = data.available_tasks || {};
            const done = data.tasks || [];
            let has = false;
            listEl.innerHTML = '';
            for (const id in available) {
              has = true;
              const task = available[id];
              const isDone = done.indexOf(id) !== -1;
              const url = task.url || '';
              const div = document.createElement('div');
              div.className = 'task-item' + (isDone ? ' completed' : '');
              let actions = '';
              if (isDone) {
                actions = '<span class="completed-badge">✔ ' + t('task_completed_badge') + '</span>';
              } else if (url) {
                // Step 1: Visit channel
                actions = '<button type="button" class="btn btn-sm btn-green" data-task="' + id + '" data-action="visit" onclick="openTaskChannel(\'' + id + '\',\'' + url + '\')">📢 ' + t('task_complete_button') + '</button>' +
                          '<button type="button" class="btn btn-sm" data-task="' + id + '" data-action="verify" style="display:none;margin-top:8px;background:var(--gold);color:#000;" onclick="completeTask(\'' + id + '\')">✅ I\'ve Joined - Get Reward</button>';
              } else {
                actions = '<button type="button" class="btn btn-sm btn-green" data-task="' + id + '" data-action="verify" onclick="completeTask(\'' + id + '\')">✅ ' + t('task_complete_button') + '</button>';
              }
              div.innerHTML = '<div class="task-info"><h3>' + (task.title || id) + '</h3><p>' + t('task_reward') + ': ' + (task.reward_coins||0) + ' ' + t('coins') + '</p></div>' + actions;
              listEl.appendChild(div);
            }
            if (!has) listEl.innerHTML = '<div class="task-item"><span>No tasks available.</span></div>';
          }

          function openTaskChannel(taskId, url) {
            // Open the channel/group link
            if (tg) { try { tg.openTelegramLink(url); return; } catch (e) {} }
            window.open(url, '_blank');
            // Show the verify button
            const btn = document.querySelector('[data-task="' + taskId + '"][data-action="visit"]');
            const verifyBtn = document.querySelector('[data-task="' + taskId + '"][data-action="verify"]');
            if (verifyBtn) verifyBtn.style.display = 'block';
            if (btn) btn.innerText = '📢 Opened! Now tap "I\'ve Joined" below';
            document.getElementById('task-status').innerText = 'Join the channel/group, then tap "I\'ve Joined" to get your reward.';
          }

          function renderShop() {
            const el = document.getElementById('shop-list');
            const items = [
              {em:'🎁', name:'Mystery Gift Box', desc:'Open a random surprise!', price:'500'},
              {em:'💎', name:'Diamond Boost', desc:'Boost your earnings 2x for an hour', price:'2000'},
              {em:'⭐', name:'Golden Streak Shield', desc:'Keep your streak alive for 1 day', price:'1500'},
              {em:'🔥', name:'Fire Double Coins', desc:'Double coins on next 5 ads', price:'1000'},
              {em:'🏆', name:'Featured Badge', desc:'Show off on the leaderboard', price:'5000'},
            ];
            el.innerHTML = items.map(function(it){
              return '<div class="shop-item"><div class="em">' + it.em + '</div><div class="info"><b>' + it.name + '</b><p>' + it.desc + '</p></div><button class="btn btn-sm btn-gold" onclick="buyShop(' + it.price + ')">' + it.price + ' <span data-translate-key="coins">coins</span></button></div>';
            }).join('');
            translateUI();
          }
          function buyShop(price) {
            document.getElementById('shop-status').innerText = '🛒 Coming soon — this item will be upgraded soon! (You need ' + price + ' coins)';
          }

          function renderHistory(data) {
            const el = document.getElementById('history-list');
            const hist = data.withdrawal_history || [];
            if (!hist.length) {
              el.innerHTML = '<div class="history-item"><span>' + t('no_history') + '</span></div>';
              return;
            }
            el.innerHTML = hist.slice().reverse().map(function(item){
              const colorClass = item.status === 'approved' ? 'approved' : (item.status === 'pending' ? 'pending' : 'rejected');
              let ts = '';
              try { ts = new Date(item.timestamp).toLocaleString(); } catch (e) {}
              return '<div class="history-item"><div><b>₹' + Number(item.amount||0).toFixed(2) + '</b>' +
                (item.transaction_id ? '<br><small style="color:var(--text-muted)">#' + item.transaction_id + '</small>' : '') +
                '<br><small style="color:var(--text-muted)">' + ts + '</small></div>' +
                '<span class="status ' + colorClass + '">' + item.status + '</span></div>';
            }).join('');
          }

          // --- ADS: 2 back-to-back = 1 reward ---
          async function watchAdStart() {
            const btn = document.getElementById('watch-ad-btn');
            const circle = document.getElementById('ad-circle');
            const timer = document.getElementById('ad-timer');
            const fill = document.getElementById('ad-progress-fill');
            const label = document.getElementById('ad-num-label');
            if (adTimer) return;
            btn.disabled = true;
            let sec = AD_SECONDS;
            circle.innerText = sec;
            label.innerText = 'Ad ' + (adCount + 1) + ' of ' + ADS_PER_REWARD;
            timer.innerText = 'Ad playing... watch until the end to earn!';
            fill.style.transition = 'none';
            fill.style.width = '0%';
            requestAnimationFrame(function(){ requestAnimationFrame(function(){ fill.style.transition = 'width ' + AD_SECONDS + 's linear'; fill.style.width = '100%'; }); });
            adTimer = setInterval(function(){
              sec--;
              circle.innerText = sec;
              if (sec <= 0) {
                clearInterval(adTimer);
                adTimer = null;
                adCount++;
                if (adCount < ADS_PER_REWARD) {
                  // play next ad
                  circle.innerText = '▶';
                  label.innerText = 'Ad ' + (adCount + 1) + ' of ' + ADS_PER_REWARD;
                  timer.innerText = 'Ad ' + adCount + ' done! Playing next ad...';
                  btn.disabled = false;
                } else {
                  // both ads done -> 1 reward
                  circle.innerText = '💰';
                  label.innerText = 'Ad ' + ADS_PER_REWARD + ' of ' + ADS_PER_REWARD;
                  timer.innerText = 'Both ads complete! Crediting your reward...';
                  adCount = 0;
                  claimAdReward();
                  btn.disabled = false;
                }
              }
            }, 1000);
          }

          async function claimAdReward() {
            try {
              const r = await fetch('/api/ads/watch/' + userId, { method: 'POST' });
              const data = await r.json();
              document.getElementById('ad-timer').innerText = data.message || 'Reward credited!';
              document.getElementById('ad-circle').innerText = '🤑';
              document.getElementById('ad-progress-fill').style.width = '0%';
              fetchData();
              setTimeout(function(){ document.getElementById('ad-circle').innerText = '▶'; }, 2500);
            } catch (e) {
              document.getElementById('ad-timer').innerText = 'Error claiming reward.';
              document.getElementById('ad-circle').innerText = '▶';
            }
          }

          function redeemMoreAds() {
            const code = document.getElementById('more-ads-code').value.trim();
            if (!code) { document.getElementById('more-ads-status').innerText = 'Enter a code first.'; return; }
            document.getElementById('more-ads-status').innerText = 'Code accepted! 10 bonus ads added.';
            document.getElementById('more-ads-code').value = '';
          }

          async function completeTask(taskId) {
            try {
              const r = await fetch('/api/tasks/complete/' + userId + '/' + taskId, { method: 'POST' });
              const data = await r.json();
              document.getElementById('task-status').innerText = data.message || '';
              fetchData();
            } catch (e) {
              document.getElementById('task-status').innerText = 'Error completing task.';
            }
          }

          function copyInvite() {
            const input = document.getElementById('invite-link');
            input.select();
            try { document.execCommand('copy'); } catch (e) {}
            if (window.navigator.clipboard) window.navigator.clipboard.writeText(input.value);
            document.getElementById('copy-invite-btn').innerText = '✅';
            setTimeout(function(){ document.getElementById('copy-invite-btn').innerText = '📋'; }, 1500);
          }
          function shareInvite() {
            const link = document.getElementById('invite-link').value;
            const shareUrl = 'https://t.me/share/url?url=' + encodeURIComponent(link) + '&text=' + encodeURIComponent('Join Xio_PayPlus and earn real money watching ads!');
            if (tg) { try { tg.openTelegramLink(shareUrl); return; } catch (e) {} }
            window.open(shareUrl, '_blank');
          }

          function sendChat() {
            const input = document.getElementById('chat-input');
            const box = document.getElementById('chat-messages');
            if (!input.value.trim()) return;
            const val = input.value.replace(/</g,'');
            const d = document.createElement('div');
            d.className = 'chat-msg mine';
            d.innerHTML = '<div class="avatar-s">Y</div><div class="bubble"><span class="who">You:</span> ' + val + '</div>';
            box.appendChild(d);
            input.value = '';
            box.scrollTop = box.scrollHeight;
            setTimeout(function(){
              const u = pickFakeUser();
              const r = document.createElement('div');
              r.className = 'chat-msg';
              r.innerHTML = '<div class="avatar-s">' + u.e + '</div><div class="bubble"><span class="who">' + u.n + ':</span> ' + fakeMsgs[Math.floor(Math.random()*fakeMsgs.length)] + '</div>';
              box.appendChild(r);
              box.scrollTop = box.scrollHeight;
            }, 1800);
          }

          function sendVoice() {
            const box = document.getElementById('chat-messages');
            const d = document.createElement('div');
            d.className = 'chat-msg mine';
            d.innerHTML = '<div class="avatar-s">Y</div><div class="bubble"><span class="who">You:</span> 🎤 [Voice message]</div>';
            box.appendChild(d);
            box.scrollTop = box.scrollHeight;
            setTimeout(function(){
              const u = pickFakeUser();
              const r = document.createElement('div');
              r.className = 'chat-msg';
              r.innerHTML = '<div class="avatar-s">' + u.e + '</div><div class="bubble"><span class="who">' + u.n + ':</span> 🎤 [Voice message 0:0' + (Math.floor(Math.random()*9)+1) + ']</div>';
              box.appendChild(r);
              box.scrollTop = box.scrollHeight;
            }, 1500);
          }

          // GIF support
          const gifs = ['😀','😂','🤣','😍','😎','🥳','🔥','💯','👏','🎉','💰','🚀','💪','❤️','👍','🤝','😅','🙌'];
          function toggleGif(which) {
            const panel = document.getElementById('gif-panel-' + which);
            if (!panel) return;
            panel.classList.toggle('show');
            if (panel.children.length === 0) {
              gifs.forEach(function(g){
                const s = document.createElement('span');
                s.className = 'gif-item';
                s.innerText = g;
                s.onclick = function(){
                  const box = document.getElementById('chat-messages');
                  const d = document.createElement('div');
                  d.className = 'chat-msg mine';
                  d.innerHTML = '<div class="avatar-s">Y</div><div class="bubble"><span class="who">You:</span> ' + g + '</div>';
                  box.appendChild(d);
                  box.scrollTop = box.scrollHeight;
                  panel.classList.remove('show');
                };
                panel.appendChild(s);
              });
            }
          }

          function selectMethod(m) {
            selectedMethod = m;
            document.querySelectorAll('.method').forEach(function(el){ el.classList.toggle('active', el.dataset.method === m); });
            document.querySelectorAll('.method-form').forEach(function(el){ el.classList.remove('active'); });
            document.getElementById(m + '-form').classList.add('active');
          }

          async function requestWithdrawal() {
            const amount = document.getElementById('withdraw-amount').value;
            let details = '';
            if (selectedMethod === 'upi') details = document.getElementById('withdraw-upi').value;
            if (selectedMethod === 'bank') details = document.getElementById('withdraw-bank').value + (document.getElementById('withdraw-ifsc').value ? ' / ' + document.getElementById('withdraw-ifsc').value : '');
            if (selectedMethod === 'mobile') details = document.getElementById('withdraw-mobile').value;
            const statusEl = document.getElementById('withdraw-status');
            if (!amount || !details) { statusEl.innerText = 'Please fill all details.'; return; }
            if (parseFloat(amount) < 10) { statusEl.innerText = 'Minimum withdrawal is ₹10.'; return; }
            try {
              const r = await fetch('/api/withdraw/' + userId, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ amount: parseFloat(amount), method: selectedMethod, details: details }) });
              const data = await r.json();
              statusEl.innerText = data.message || '';
              fetchData();
            } catch (e) { statusEl.innerText = 'Withdrawal error. Please try again.'; }
          }

          // --- SPIN: gift-based with golden glow reveal ---
          let pendingGift = null;
          function buildWheel() {
            const wheel = document.getElementById('wheel');
            const gifts = ['🎁 Mystery','💎 Diamond','⭐ Star','🔥 Fire','🏆 Trophy','💥 Lose'];
            const positions = [
              {top:'13%',left:'50%'},{top:'50%',left:'88%'},{top:'87%',left:'50%'},
              {top:'50%',left:'12%'},{top:'30%',left:'22%'},{top:'70%',left:'78%'}
            ];
            let labels = '';
            for (let i=0;i<6;i++){
              labels += '<div class="wheel-label" style="top:' + positions[i].top + ';left:' + positions[i].left + ';transform:translate(-50%,-50%);">' + gifts[i] + '</div>';
            }
            wheel.innerHTML = labels;
          }

          async function spinWheel() {
            const btn = document.getElementById('spin-button');
            const wheel = document.getElementById('wheel');
            const status = document.getElementById('spin-status');
            btn.disabled = true;
            status.innerText = '🎁 Spinning... Good luck!';
            try {
              const r = await fetch('/api/spin/' + userId, { method: 'POST' });
              const data = await r.json();
              if (!data.success) { status.innerText = data.message || ''; btn.disabled = false; return; }
// Gift data comes from the backend (spin_gifts list)
              const gifts = [{name:'🎁 Mystery Gift',coins:500},{name:'💎 Diamond Box',coins:2000},{name:'⭐ Golden Star',coins:1000},{name:'🔥 Fire Combo',coins:1500},{name:'🏆 Royal Trophy',coins:3000},{name:'💥 Try Again',coins:0}];
              const backendGift = data.gift || {};
              const idx = gifts.findIndex(function(g){ return g.name === backendGift.name; });
              const finalIdx = idx >= 0 ? idx : Math.floor(Math.random() * 6);
              const finalAngle = (finalIdx * 60) + Math.floor(Math.random() * 40) + 360 * 5;
              wheel.style.transform = 'rotate(' + finalAngle + 'deg)';
              setTimeout(function(){
                // Use the backend gift (which was actually credited)
                pendingGift = {name: backendGift.name || '🎁 Mystery Gift', coins: backendGift.coins || 0};
                showSurprise(pendingGift);
                status.innerText = 'You won ' + pendingGift.name + '! Tap the gift to open it.';
                btn.disabled = false;
                fetchData();
              }, 4500);
            } catch (e) { status.innerText = 'Spin error.'; btn.disabled = false; }
          }

          function showSurprise(gift) {
            const box = document.getElementById('surprise-box');
            box.classList.add('show');
            document.getElementById('gift-emoji').innerText = gift.coins > 0 ? '🎁' : '💥';
            document.getElementById('surprise-msg').innerText = gift.coins > 0 ? 'Tap the gift to open it!' : 'Oops! Try again tomorrow';
            document.getElementById('open-result').classList.remove('show');
            document.getElementById('gift-stars').innerHTML = '';
            if (gift.coins > 0) {
              // golden stars glow
              for (let i=0;i<10;i++){
                const s = document.createElement('span');
                s.className = 'gift-star';
                s.innerText = '⭐';
                s.style.left = (Math.random()*100)+'%';
                s.style.top = (Math.random()*100)+'%';
                s.style.animationDelay = (Math.random()*1)+'s';
                document.getElementById('gift-stars').appendChild(s);
              }
            }
          }

          function openGift() {
            if (!pendingGift || pendingGift.coins === 0) return;
            document.getElementById('open-result').classList.add('show');
            document.getElementById('gift-box').style.display = 'none';
            document.getElementById('surprise-msg').innerText = 'Please wait...';
            document.getElementById('surprise-sub').innerText = '';
            document.getElementById('open-gift-emoji').innerText = '🎉';
            document.getElementById('open-msg').innerText = 'Congratulations! You won ' + pendingGift.coins + ' coins!';
          }

          function closeSurprise() {
            document.getElementById('surprise-box').classList.remove('show');
            document.getElementById('gift-box').style.display = 'flex';
            document.getElementById('open-result').classList.remove('show');
            document.getElementById('surprise-msg').innerText = 'Tap the gift to open it!';
            pendingGift = null;
            fetchData();
          }

          function openShop() { showPage('shop'); renderShop(); }
          function openSupport() { showPage('support'); loadFaq(); }

          async function loadFaq() {
            try {
              const r = await fetch('/api/support');
              const data = await r.json();
              const el = document.getElementById('faq-list');
              const keys = ['how_to_earn','how_to_withdraw','support_group'];
              let html = '';
              keys.forEach(function(k){ if (data[k]) html += '<div class="req-item" style="margin-bottom:10px;">❓ ' + data[k] + '</div>'; });
              el.innerHTML = html || '<div class="req-item">Ask us anything!</div>';
            } catch (e) {}
          }

          function openTelegramLink(url) {
            if (tg) { try { tg.openTelegramLink(url); return; } catch (e) {} }
            window.open(url, '_blank');
          }

          async function sendSupport() {
            const msg = document.getElementById('support-message').value.trim();
            const statusEl = document.getElementById('support-status');
            if (!msg) { statusEl.innerText = 'Please type a message first.'; return; }
            // Send the message to support API (moderation)
            let reply = 'Message received.';
            try {
              const r = await fetch('/api/support/message', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ message: msg }) });
              const data = await r.json();
              if (data.message) reply = data.message;
            } catch (e) {}
            // Redirect to support group with the user's message in the URL text
            const groupUrl = supportLinks.support_group || 'https://t.me/+QserNlqLSqZjN2U9';
            const encodedMsg = encodeURIComponent('User ' + userId + ' (' + userName + '): ' + msg);
            const shareUrl = 'https://t.me/share/url?url=' + encodeURIComponent(groupUrl) + '&text=' + encodedMsg;
            openTelegramLink(shareUrl);
            statusEl.innerText = '✅ ' + reply + ' Opening support group with your message...';
            document.getElementById('support-message').value = '';
          }

function showPage(pageName) {
            document.querySelectorAll('.page').forEach(function(p){ p.classList.remove('active'); });
            const t = document.getElementById('page-' + pageName);
            if (t) t.classList.add('active');
            document.querySelectorAll('.nav-item').forEach(function(i){ i.classList.toggle('active', i.dataset.page === pageName); });
            if (pageName === 'ads') seedAdsChat();
          }

          function seedAdsChat() {
            const box = document.getElementById('chat-messages-ads');
            if (box.children.length === 0) {
              const u1 = pickFakeUser(), u2 = pickFakeUser();
              box.innerHTML = '<div class="chat-msg"><div class="avatar-s">'+u1.e+'</div><div class="bubble"><span class="who">'+u1.n+':</span> Anyone hitting 20 ads today?</div></div>' +
                '<div class="chat-msg"><div class="avatar-s">'+u2.e+'</div><div class="bubble"><span class="who">'+u2.n+':</span> 12 more and I reach withdrawal!</div></div>';
            }
          }

          function initChatRotation() {
            setInterval(function(){
              const box = document.getElementById('chat-messages');
              if (!box) return;
              const u = pickFakeUser();
              if (box.children.length > 14) box.removeChild(box.firstChild);
              const d = document.createElement('div');
              d.className = 'chat-msg';
              d.innerHTML = '<div class="avatar-s">' + u.e + '</div><div class="bubble"><span class="who">' + u.n + ':</span> ' + fakeMsgs[Math.floor(Math.random()*fakeMsgs.length)] + '</div>';
              box.appendChild(d);
              box.scrollTop = box.scrollHeight;
            }, 9000);
          }

          function initDarkPatterns() {
            // Fake online count fluctuation
            setInterval(function(){
              const base = 2100 + Math.floor(Math.random()*600);
              document.getElementById('online-count').innerText = base.toLocaleString();
              document.getElementById('chat-online').innerText = base.toLocaleString();
              const paid = 120000 + Math.floor(Math.random()*20000);
              document.getElementById('payout-count').innerText = '₹' + paid.toLocaleString();
            }, 5000);
          }

          // Set support links
          function setSupportLinks() {
            const g = document.getElementById('support-group-link');
            const a = document.getElementById('admin-support-link');
            if (g) g.href = supportLinks.support_group || 'https://t.me/+QserNlqLSqZjN2U9';
            if (a) a.href = supportLinks.admin_channel || 'https://t.me/+nvkRuwvZJnRiOGM1';
          }

          window.addEventListener('load', function(){
            buildWheel();
            setSupportLinks();
            fetchData();
            translateUI();
            initChatRotation();
            initDarkPatterns();
            setInterval(function(){
              injectFeed('live-feed');
              injectFeed('live-feed-ads');
              injectFeed('live-feed-invite');
              injectFeed('live-feed-withdraw');
            }, 4000);
            setInterval(fetchData, 8000);
          });
        </script>
      </body>
    </html>
    """

    @app.get("/")
    def index() -> str:
        config = load_config()
        return render_template_string(
            HTML,
            app_name=config.app_name,
            translations_json=json.dumps(current_engine.support.translations),
            lang_config_json=json.dumps(current_engine.support.lang_config),
            support_links_json=json.dumps(current_engine.support.get_support_links()),
            bot_username=os.getenv("TELEGRAM_BOT_USERNAME", "xiolis_bot"),
            provider=ads_manager.get_config()["provider"],
        )

    return app


app = create_app()

if __name__ == "__main__":
    config = load_config()
    app.run(host=config.host, port=config.port, debug=(config.environment == "development"))
