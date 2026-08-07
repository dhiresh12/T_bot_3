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
          .icon-btn { background: var(--bg-light); color: var(--text-light); border: none; border-radius: 50%; width: 34px; height: 34px; font-size: 16px; cursor: pointer; }
          .page { display: none; animation: fadeIn 0.3s; }
          .page.active { display: block; }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
          .user-header { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
          .avatar { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), #60a5fa); display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; border: 2px solid #475569; }
          .user-info { flex-grow: 1; }
          .user-info h1 { margin: 0; font-size: 18px; }
          .user-info p { margin: 0; color: var(--text-muted); font-size: 13px; }
          .balance-card { background: linear-gradient(135deg, #1d4ed8, #7c3aed); padding: 22px; border-radius: 18px; text-align: center; margin-bottom: 18px; position: relative; overflow: hidden; }
          .balance-card .label { font-size: 13px; opacity: 0.85; }
          .balance-card .amount { font-size: 38px; font-weight: 800; margin: 4px 0; }
          .balance-card .coins { font-size: 15px; opacity: 0.95; }
          .tier-progress { display: flex; justify-content: space-between; font-size: 12px; margin-top: 14px; background: rgba(0,0,0,0.2); padding: 8px 12px; border-radius: 10px; }
          .progress-bar { height: 6px; background: rgba(255,255,255,0.2); border-radius: 4px; margin-top: 8px; overflow: hidden; }
          .progress-fill { height: 100%; background: linear-gradient(90deg, #84cc16, #facc15); border-radius: 4px; }
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
          .chat-msg { margin-bottom: 8px; font-size: 13px; }
          .chat-msg .who { font-weight: 700; color: var(--primary); }
          .chat-input { display: flex; gap: 8px; margin-top: 10px; }
          .chat-input input { flex: 1; padding: 10px; background: var(--bg-dark); border: 1px solid #334155; border-radius: 10px; color: white; }
          .chat-input button { background: var(--primary); color: white; border: none; border-radius: 10px; padding: 0 14px; font-size: 16px; cursor: pointer; }
          .ad-box { text-align: center; padding: 28px 16px; background: linear-gradient(135deg, #1e293b, #0f172a); border: 1px solid #334155; border-radius: 16px; margin-top: 8px; }
          .ad-circle { width: 90px; height: 90px; border-radius: 50%; background: var(--bg-light); border: 4px solid var(--primary); display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 800; margin: 0 auto 16px; color: var(--text-light); }
          .ad-timer { font-size: 14px; color: var(--text-muted); margin-top: 8px; }
          .daily-limit { display: flex; justify-content: space-between; background: var(--bg-light); padding: 10px 14px; border-radius: 12px; margin-top: 14px; font-size: 14px; }
          .daily-limit .n { font-weight: 700; color: var(--gold); }
          .task-item { background-color: var(--bg-light); padding: 14px; border-radius: 14px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
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
          .wheel-container { position: relative; width: 250px; height: 250px; margin: 24px auto; }
          .wheel { width: 100%; height: 100%; border-radius: 50%; background-image: conic-gradient(#ef4444 0deg 90deg, #f97316 90deg 180deg, #84cc16 180deg 270deg, #3b82f6 270deg 360deg); transition: transform 4s cubic-bezier(0.25, 0.1, 0.25, 1); border: 6px solid #facc15; }
          .wheel-pointer { position: absolute; top: -12px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 18px solid transparent; border-right: 18px solid transparent; border-top: 26px solid #facc15; z-index: 2; }
          .wheel-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-weight: bold; font-size: 17px; text-shadow: 1px 1px 3px black; }
          .status-msg { text-align: center; margin-top: 12px; color: var(--accent); font-weight: 600; min-height: 20px; }
          .support-box { padding: 16px; margin-top: 12px; }
          .support-box textarea { width: 100%; height: 100px; padding: 12px; background: var(--bg-light); border: 1px solid #334155; border-radius: 12px; color: white; font-family: inherit; }
          .nav { position: fixed; bottom: 0; left: 0; right: 0; background: var(--bg-light); border-top: 1px solid #334155; display: flex; justify-content: space-around; padding: 8px 0 calc(8px + env(safe-area-inset-bottom)); z-index: 100; }
          .nav-item { color: var(--text-muted); background: none; border: none; cursor: pointer; text-align: center; font-size: 10px; padding: 0; flex: 1; font-family: inherit; }
          .nav-item.active { color: var(--primary); }
          .nav-item .em { font-size: 22px; display: block; }
          .badge-note { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.4); color: #fcd34d; padding: 10px 14px; border-radius: 12px; font-size: 12px; margin-top: 12px; }
          .flash { animation: flash 1s ease; }
          @keyframes flash { 0% { opacity: 0.3;} 100% { opacity: 1; } }
        </style>
      </head>
      <body>
        <div class="app-header">
          <div class="brand">Xio_PayPlus<small>Earn • Play • Win</small></div>
          <div class="header-actions">
            <button class="icon-btn" id="support-btn" onclick="openSupport()">💬</button>
            <button class="icon-btn" id="lang-btn" onclick="cycleLang()">🌐</button>
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

            <div class="grid">
              <div class="grid-card"><div id="invites-count" class="value">0</div><div class="label" data-translate-key="invites">Invites</div></div>
              <div class="grid-card"><div id="tasks-count" class="value">0</div><div class="label" data-translate-key="tasks_done">Tasks Done</div></div>
            </div>

            <div class="section-title" data-translate-key="spin_title">🎡 Daily Spin</div>
            <div class="wheel-container">
              <div class="wheel-pointer"></div>
              <div id="wheel" class="wheel">
                <div class="wheel-text" style="position:absolute;top:18%;left:50%;transform:translateX(-50%);">₹0.10</div>
                <div class="wheel-text" style="position:absolute;top:50%;left:85%;transform:translate(-50%,-50%);">₹0.20</div>
                <div class="wheel-text" style="position:absolute;bottom:18%;left:50%;transform:translateX(-50%);">₹0.15</div>
                <div class="wheel-text" style="position:absolute;top:50%;left:15%;transform:translate(-50%,-50%);">0</div>
              </div>
            </div>
            <button id="spin-button" class="btn btn-gold" onclick="spinWheel()">🎰 Spin for a Prize!</button>
            <p id="spin-status" class="status-msg"></p>

            <div class="live-feed" id="live-feed">
              <p data-translate-key="connecting_feed">Connecting to live feed...</p>
            </div>

            <div class="chat-box">
              <div style="font-weight:700;font-size:13px;margin-bottom:8px;">💬 Community Chat <span style="color:var(--text-muted);font-weight:400;font-size:11px;">• 2,341 online</span></div>
              <div id="chat-messages">
                <div class="chat-msg"><span class="who">Priya:</span> Watching ads to reach my target 💪</div>
                <div class="chat-msg"><span class="who">Rahul:</span> Just withdrew ₹120! Thank you Xio 🙏</div>
              </div>
              <div class="chat-input">
                <input id="chat-input" placeholder="Type a message...">
                <button onclick="sendChat()">➤</button>
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
              <button id="watch-ad-btn" class="btn btn-green" onclick="watchAdStart()">▶ Watch Ad & Earn</button>
              <div class="ad-timer" id="ad-timer">Each ad takes just 15 seconds</div>
              <div class="daily-limit"><span>📺 Daily Ads</span><span class="n" id="daily-ads-count">0 / 15</span></div>
            </div>
            <div class="ad-box" id="more-ads-box" style="display:none;">
              <p style="font-size:13px;color:var(--text-muted);margin:0 0 8px;">Hit your daily limit? Get 10 more ads!</p>
              <div class="invite-link-box">
                <input id="more-ads-code" placeholder="Enter more-ads code" style="flex:1;">
                <button class="btn-sm" onclick="redeemMoreAds()">Redeem</button>
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
              <button onclick="copyInvite()">📋</button>
            </div>
            <button class="btn btn-gold" onclick="shareInvite()" data-translate-key="share_invite_button">🚀 Share Invite Link</button>
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
              <button class="btn btn-green" onclick="requestWithdrawal()">💸 Request Withdrawal</button>
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
            <p style="color:var(--text-muted);font-size:13px;">Ask us anything - our AI bot replies instantly!</p>
            <div id="faq-list" style="margin-top:12px;"></div>
            <div class="support-box">
              <textarea id="support-message" placeholder="Type your problem here..."></textarea>
              <button class="btn" onclick="sendSupport()">📨 Send & Join Support Group</button>
              <p id="support-status" class="status-msg"></p>
            </div>
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
          const botUsername = '{{bot_username}}';
          let currentLang = localStorage.getItem('xio_lang') || 'en';

          let selectedMethod = 'upi';
          let adTimer = null;
          const AD_SECONDS = 15;

          const fakeNames = ['Aarav','Priya','Rohit','Ananya','Vikram','Sneha','Karan','Neha','John','Maria','Rahul','Sara','Amit','Pooja','Deepak','Ritu','Kavita','Sunil','Ravi','Fatima','Wei','Kenji','Alex','Sofia','Arjun','Meera'];
          const fakeNumbers = [];
          for (let i = 0; i < 30; i++) {
            let d = String(Math.floor(6000000000 + Math.random() * 3999999999));
            fakeNumbers.push(d.slice(0,2) + '*****' + d.slice(7));
          }
          const fakeFeedTemplates = [
            (n,nu,amt)=>n + ' ' + nu + ' ₹' + amt.toFixed(2) + ' successfully withdrawal',
            (n,nu,amt)=>n + ' just withdrew ₹' + amt.toFixed(2) + ' (UPI ' + nu + ')',
            (n,nu,amt)=> n + ' earned ₹' + amt.toFixed(2) + ' payout sent!',
            (n,nu,amt)=>n + ' ' + nu + ' withdrew ₹' + amt.toFixed(2) + ' Successfully',
            (n,nu,amt)=>'Payment confirmed: ' + n + ' → ₹' + amt.toFixed(2)
          ];

          function fakeFeedLine() {
            const n = fakeNames[Math.floor(Math.random() * fakeNames.length)];
            const nu = fakeNumbers[Math.floor(Math.random() * fakeNumbers.length)];
            const amt = 50 + Math.random() * 100;
            const tmpl = fakeFeedTemplates[Math.floor(Math.random() * fakeFeedTemplates.length)];
            return tmpl(n, nu, amt);
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
          function cycleLang() {
            const langs = ['en','hi'];
            let idx = langs.indexOf(currentLang);
            idx = (idx + 1) % langs.length;
            currentLang = langs[idx];
            try { localStorage.setItem('xio_lang', currentLang); } catch (e) {}
            translateUI();
            fetchData(true);
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

            document.getElementById('invites-count').innerText = data.invites || 0;
            document.getElementById('tasks-count').innerText = (data.tasks && data.tasks.length) || 0;
            document.getElementById('invite-link').value = 'https://t.me/' + botUsername + '?start=' + data.user_id;
            document.getElementById('invite-count-box').innerText = data.invites || 0;
            document.getElementById('invite-earned-box').innerText = '₹' + (Number(data.invites||0) * 0.005).toFixed(3);
            document.getElementById('daily-ads-count').innerText = (data.completed_ads || 0) + ' / ' + (data.withdrawal_reqs?.min_ads || 80);

            injectFeed('live-feed');
            injectFeed('live-feed-ads');
            injectFeed('live-feed-invite');
            injectFeed('live-feed-withdraw');

            renderTasks(data);
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
              const div = document.createElement('div');
              div.className = 'task-item' + (isDone ? ' completed' : '');
              const badge = isDone
                ? '<span class="completed-badge">✔ ' + t('task_completed_badge') + '</span>'
                : '<button class="btn btn-sm btn-green" onclick="completeTask(\'' + id + '\')">' + t('task_complete_button') + '</button>';
              div.innerHTML = '<div class="task-info"><h3>' + (task.title || id) + '</h3><p>' + t('task_reward') + ': ' + (task.reward_coins||0) + ' ' + t('coins') + '</p></div>' + badge;
              listEl.appendChild(div);
            }
            if (!has) listEl.innerHTML = '<div class="task-item"><span>No tasks available.</span></div>';
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

          async function watchAdStart() {
            const btn = document.getElementById('watch-ad-btn');
            const circle = document.getElementById('ad-circle');
            const timer = document.getElementById('ad-timer');
            if (adTimer) return;
            btn.disabled = true;
            let sec = AD_SECONDS;
            circle.innerText = sec;
            timer.innerText = 'Ad playing... watch until the end to earn!';
            adTimer = setInterval(function(){
              sec--;
              circle.innerText = sec;
              if (sec <= 0) {
                clearInterval(adTimer);
                adTimer = null;
                circle.innerText = '✅';
                timer.innerText = 'Ad complete! Crediting your reward...';
                claimAdReward();
                btn.disabled = false;
              }
            }, 1000);
          }

          async function claimAdReward() {
            try {
              const r = await fetch('/api/ads/watch/' + userId, { method: 'POST' });
              const data = await r.json();
              document.getElementById('ad-timer').innerText = data.message || 'Reward credited!';
              document.getElementById('ad-circle').innerText = '💰';
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
            document.getElementById('invite-link').placeholder = 'Copied!';
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
            const d = document.createElement('div');
            d.className = 'chat-msg';
            d.innerHTML = '<span class="who">You:</span> ' + input.value.replace(/</g,'<');
            box.appendChild(d);
            input.value = '';
            setTimeout(function(){
              const n = fakeNames[Math.floor(Math.random() * fakeNames.length)];
              const msgs = ['Nice! Keep earning 💪','How many ads do you watch daily?','Just hit my target today 🎯','This app pays for real 🔥','Keep it up bro!','Refer 10 friends to unlock withdraw'];
              const r = document.createElement('div');
              r.className = 'chat-msg';
              r.innerHTML = '<span class="who">' + n + ':</span> ' + msgs[Math.floor(Math.random()*msgs.length)];
              box.appendChild(r);
            }, 1800);
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

          async function spinWheel() {
            const btn = document.getElementById('spin-button');
            const wheel = document.getElementById('wheel');
            const status = document.getElementById('spin-status');
            btn.disabled = true;
            status.innerText = '🎰 Spinning... Good luck!';
            try {
              const r = await fetch('/api/spin/' + userId, { method: 'POST' });
              const data = await r.json();
              if (!data.success) { status.innerText = data.message || ''; btn.disabled = false; return; }
              const idx = Math.floor(Math.random() * 4);
              const finalAngle = (idx * 90) + Math.floor(Math.random() * 60) + 360 * 5;
              wheel.style.transform = 'rotate(' + finalAngle + 'deg)';
              setTimeout(function(){
                status.innerText = data.message + ' (spin again tomorrow!)';
                btn.disabled = false;
                fetchData();
              }, 4500);
            } catch (e) { status.innerText = 'Spin error.'; btn.disabled = false; }
          }

          function openSupport() {
            showPage('support');
            loadFaq();
          }
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
          async function sendSupport() {
            const msg = document.getElementById('support-message').value;
            const url = 'https://t.me/+QserNlqLSqZjN2U9';
            try { await fetch('/api/support/message', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ message: msg }) }); } catch (e) {}
            if (tg) { try { tg.openTelegramLink(url); return; } catch (e) {} }
            window.open(url, '_blank');
            document.getElementById('support-status').innerText = 'Message sent! Support group opened.';
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
              box.innerHTML = '<div class="chat-msg"><span class="who">'+fakeNames[0]+':</span> Anyone hitting 80 ads today?</div><div class="chat-msg"><span class="who">'+fakeNames[1]+':</span> 12 more and I reach withdrawal!</div>';
            }
          }

          function initChatRotation() {
            setInterval(function(){
              const box = document.getElementById('chat-messages');
              if (!box) return;
              const msgs = ['Wow just got ₹120! 🎉','Joined yesterday, already loving it 💰','Which task pays best?','Another day, another payout 🔥','10 invites done, trying withdrawal now!','This is legit guys 👌'];
              const n = fakeNames[Math.floor(Math.random() * fakeNames.length)];
              if (box.children.length > 12) box.removeChild(box.firstChild);
              const d = document.createElement('div');
              d.className = 'chat-msg';
              d.innerHTML = '<span class="who">' + n + ':</span> ' + msgs[Math.floor(Math.random()*msgs.length)];
              box.appendChild(d);
            }, 9000);
          }

          window.addEventListener('load', function(){
            fetchData();
            translateUI();
            initChatRotation();
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
            bot_username=os.getenv("TELEGRAM_BOT_USERNAME", "xio_liis_bot"),
            provider=ads_manager.get_config()["provider"],
        )

    return app


app = create_app()

if __name__ == "__main__":
    config = load_config()
    app.run(host=config.host, port=config.port, debug=(config.environment == "development"))

