from __future__ import annotations

import json
import os

from flask import Flask, render_template_string

from app.admin import AdminPanelService
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
          }
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: var(--bg-dark); color: var(--text-light); margin: 0; padding: 16px 16px 80px 16px; }
          .container { max-width: 480px; margin: 0 auto; }
          .header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
          .avatar { width: 56px; height: 56px; border-radius: 50%; background-color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; }
          .user-info { flex-grow: 1; }
          .user-info h1 { margin: 0; font-size: 20px; }
          .user-info p { margin: 0; color: var(--text-muted); font-size: 14px; }
          .balance-card { background: linear-gradient(135deg, var(--primary), #60a5fa); padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 24px; }
          .balance-card .label { font-size: 14px; opacity: 0.8; }
          .balance-card .amount { font-size: 36px; font-weight: bold; margin: 4px 0; }
          .balance-card .coins { font-size: 16px; opacity: 0.9; }
          .tier-progress { display: flex; justify-content: space-between; font-size: 12px; margin-top: 12px; }
          .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
          .grid-card { background-color: var(--bg-light); padding: 16px; border-radius: 12px; text-align: center; }
          .grid-card .value { font-size: 24px; font-weight: 600; margin-bottom: 4px; }
          .grid-card .label { font-size: 12px; color: var(--text-muted); }
          .live-feed { margin-top: 24px; background-color: var(--bg-light); padding: 12px; border-radius: 12px; height: 100px; overflow-y: scroll; font-size: 13px; }
          .live-feed p { margin: 0 0 8px; animation: fadeIn 0.5s; }
          @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
          .nav { position: fixed; bottom: 0; left: 0; right: 0; background-color: var(--bg-light); display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #334155; }
          .nav-item { color: var(--text-muted); text-decoration: none; text-align: center; font-size: 12px; background: none; border: none; cursor: pointer; font-family: inherit; padding: 0; }
          .nav-item.active { color: var(--primary); }
          .nav-item div { font-size: 24px; }
          .page { display: none; }
          .page.active { display: block; }
          .button { background-color: var(--primary); color: white; border: none; padding: 12px; border-radius: 10px; width: 100%; font-size: 16px; font-weight: 600; margin-top: 16px; }
          .back-button { background: none; border: none; color: var(--primary); font-size: 16px; cursor: pointer; margin-bottom: 8px; padding: 0; }
          .lang-switcher { font-size: 14px; color: var(--text-muted); }
          .lang-switcher button { background: none; border: none; color: var(--text-muted); cursor: pointer; font-weight: bold; padding: 4px; }
          .lang-switcher button.active { color: var(--primary); }
          .task-item { background-color: var(--bg-light); padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
          .task-item.completed { opacity: 0.6; }
          .task-info h3 { margin: 0 0 4px; font-size: 16px; }
          .task-info p { margin: 0; font-size: 12px; color: var(--text-muted); }
          .task-item .completed-badge { color: var(--accent); font-weight: bold; }
          .req-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
          .req-item { background-color: var(--bg-light); padding: 12px; border-radius: 8px; font-size: 13px; }
          .req-item .progress { font-weight: bold; font-size: 16px; }
          .withdraw-form input { width: calc(100% - 24px); padding: 12px; margin-bottom: 12px; background-color: var(--bg-light); border: 1px solid #334155; color: white; border-radius: 8px; }
          .history-item { background-color: var(--bg-light); padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between; }
          .history-item .status { font-weight: bold; text-transform: capitalize; }
          .wheel-container { position: relative; width: 250px; height: 250px; margin: 24px auto; }
          .wheel { width: 100%; height: 100%; border-radius: 50%; background-image: conic-gradient( #ef4444 0deg 90deg, #f97316 90deg 180deg, #84cc16 180deg 270deg, #3b82f6 270deg 360deg ); transition: transform 4s cubic-bezier(0.25, 0.1, 0.25, 1); }
          .wheel-pointer { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 30px solid #facc15; }
          .spin-button { background-color: #f59e0b; }
          .wheel-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: white; font-weight: bold; font-size: 18px; text-shadow: 1px 1px 2px black; }
          .wheel-segment { position: absolute; width: 50%; height: 50%; top: 0; left: 50%; transform-origin: 0% 100%; }
          .wheel-segment:nth-child(1) { transform: rotate(22.5deg); }
          .wheel-segment:nth-child(2) { transform: rotate(112.5deg); }
          .wheel-segment:nth-child(3) { transform: rotate(202.5deg); }
          .wheel-segment:nth-child(4) { transform: rotate(292.5deg); }
          .status-msg { text-align: center; margin-top: 10px; color: var(--accent); }
        </style>
      </head>
      <body>
        <div class="container">
          <!-- Dashboard Page -->
          <div id="page-home" class="page active">
            <div class="header">
              <div id="avatar" class="avatar">?</div>
              <div class="user-info">
                <h1 id="user-name">Guest</h1>
                <p id="user-id">ID: ...</p>
              </div>
              <div class="lang-switcher">
                <button id="lang-en" class="active" onclick="setLanguage('en')">EN</button>|
                <button id="lang-hi" onclick="setLanguage('hi')">HI</button>
              </div>
            </div>

            <div class="balance-card">
              <div class="label" data-translate-key="total_balance">Total Balance</div>
              <div id="balance-amount" class="amount">₹0.00</div>
              <div id="balance-coins" class="coins">0 <span data-translate-key="coins">Coins</span></div>
              <div class="tier-progress">
                <span id="current-tier">Bronze</span>
                <span id="next-tier">Next: Silver</span>
              </div>
            </div>

            <div class="grid">
              <div class="grid-card">
                <div id="invites-count" class="value">0</div>
                <div class="label" data-translate-key="invites">Invites</div>
              </div>
              <div class="grid-card">
                <div id="tasks-count" class="value">0</div>
                <div class="label" data-translate-key="tasks_done">Tasks Done</div>
              </div>
            </div>

            <!-- Spin Wheel Section -->
            <div class="wheel-container">
              <div class="wheel-pointer"></div>
              <div id="wheel" class="wheel">
                  <div class="wheel-segment"><div class="wheel-text">₹0.10</div></div>
                  <div class="wheel-segment"><div class="wheel-text">₹0.15</div></div>
                  <div class="wheel-segment"><div class="wheel-text">₹0.20</div></div>
                  <div class="wheel-segment"><div class="wheel-text">₹0.00</div></div>
              </div>
            </div>
            <button id="spin-button" class="button spin-button" onclick="spinWheel()">Spin for a Prize!</button>
            <p id="spin-status" class="status-msg"></p>

            <div class="live-feed" id="live-feed">
              <p data-translate-key="connecting_feed">Connecting to live feed...</p>
            </div>
          </div>

          <!-- Tasks Page -->
          <div id="page-tasks" class="page">
            <button class="back-button" onclick="showPage('home')">← Back</button>
            <h1 data-translate-key="tasks_title">Tasks</h1>
            <div id="task-list">
              <p>Loading tasks...</p>
            </div>
            <p id="task-status" class="status-msg"></p>
          </div>

          <!-- Invite Page -->
          <div id="page-invite" class="page">
            <button class="back-button" onclick="showPage('home')">← Back</button>
            <h1 data-translate-key="invite_title">Invite Friends</h1>
            <p data-translate-key="invite_link_label">Your personal invite link:</p>
            <input id="invite-link" type="text" readonly style="width: 100%; padding: 10px; border-radius: 8px; background-color: var(--bg-light); border: 1px solid #334155; color: white; text-align: center;">
            <button class="button" onclick="shareInvite()" data-translate-key="share_invite_button">Share Invite Link</button>
          </div>

          <!-- Withdraw Page -->
          <div id="page-wallet" class="page">
            <button class="back-button" onclick="showPage('home')">← Back</button>
            <h1 data-translate-key="withdraw_title">Withdraw Funds</h1>

            <h2 data-translate-key="requirements_title">Requirements</h2>
            <div id="req-grid" class="req-grid">
              <div class="req-item">Loading...</div>
            </div>

            <h2 data-translate-key="withdraw_form_title">Request Payout</h2>
            <div class="withdraw-form">
              <input id="withdraw-amount" type="number" placeholder="Amount">
              <input id="withdraw-details" type="text" placeholder="UPI ID">
              <button class="button" onclick="requestWithdrawal()" data-translate-key="withdraw_button">Request Withdrawal</button>
              <p id="withdraw-status" class="status-msg"></p>
            </div>

            <h2 data-translate-key="history_title" style="margin-top: 24px;">History</h2>
            <div id="history-list">
              <div class="history-item">
                <span data-translate-key="no_history">No withdrawal history yet.</span>
              </div>
            </div>

          </div>
        </div>

        <div class="nav">
          <button class="nav-item active" data-page="home" onclick="showPage('home')"><div>🏠</div><span data-translate-key="nav_home">Home</span></button>
          <button class="nav-item" data-page="tasks" onclick="showPage('tasks')"><div>📋</div><span data-translate-key="nav_tasks">Tasks</span></button>
          <button class="nav-item" data-page="invite" onclick="showPage('invite')"><div>👥</div><span data-translate-key="nav_invite">Invite</span></button>
          <button class="nav-item" data-page="wallet" onclick="showPage('wallet')"><div>💰</div><span data-translate-key="nav_wallet">Wallet</span></button>
        </div>

        <script>
          // Telegram WebApp is optional so the mini app also works in a normal browser.
          function getTelegram() {
            try {
              if (window.Telegram && window.Telegram.WebApp) {
                return window.Telegram.WebApp;
              }
            } catch (e) {}
            return null;
          }

          const tg = getTelegram();
          if (tg) { try { tg.expand(); } catch (e) {} }

          // Read the user id (from Telegram if available, else a demo id for testing).
          const userId = (function(){
            try {
              const u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
              if (u && u.id) return u.id;
            } catch (e) {}
            return '777';
          })();
          const userName = (function(){
            try {
              const u = tg && tg.initDataUnsafe && tg.initDataUnsafe.user;
              if (u && u.first_name) return u.first_name;
            } catch (e) {}
            return 'Guest';
          })();

          const translations = {translations_json};
          let currentLang = localStorage.getItem('lang') || 'en';

          const liveFeedEl = document.getElementById('live-feed');

          function t(key) {
            try { return translations[currentLang]?.ui[key] || translations['en'].ui[key] || key; } catch(e) { return key; }
          }

          function translateUI() {
            document.querySelectorAll('[data-translate-key]').forEach(el => {
              const key = el.dataset.translateKey;
              el.innerText = t(key);
            });
            document.querySelectorAll('.lang-switcher button').forEach(btn => btn.classList.remove('active'));
            const activeBtn = document.getElementById('lang-' + currentLang);
            if (activeBtn) activeBtn.classList.add('active');
          }

          async function fetchData() {
            try {
              const response = await fetch('/api/dashboard/' + userId);
              if (!response.ok) throw new Error('Dashboard API error');
              const data = await response.json();
              updateUI(data);
            } catch (e) {
              document.getElementById('user-id').innerText = 'ID: ' + userId;
            }
          }

          function updateUI(data) {
            document.getElementById('avatar').innerText = (data.name || 'G').charAt(0).toUpperCase();
            document.getElementById('user-name').innerText = data.name;
            document.getElementById('user-id').innerText = 'ID: ' + data.user_id;
            document.getElementById('balance-amount').innerText = '₹' + Number(data.wallet_rupee_equivalent || 0).toFixed(2);
            document.getElementById('balance-coins').innerHTML = Number(data.coins || 0).toLocaleString() + ' <span data-translate-key="coins">' + t('coins') + '</span>';
            document.getElementById('current-tier').innerText = (data.engagement && data.engagement.tier) || 'Bronze';
            document.getElementById('next-tier').innerText = (data.engagement && data.engagement.next_tier) ? (t('next_tier_prefix') + ' ' + data.engagement.next_tier) : '';
            document.getElementById('invites-count').innerText = data.invites || 0;
            document.getElementById('tasks-count').innerText = (data.tasks && data.tasks.length) || 0;
            document.getElementById('invite-link').value = 'https://t.me/' + 'xio_liis_bot' + '?start=' + data.user_id;

            // Live feed (Dark Pattern)
            if (data.live_feed && data.live_feed.length) {
              const feedItem = document.createElement('p');
              feedItem.innerText = data.live_feed[Math.floor(Math.random() * data.live_feed.length)];
              liveFeedEl.prepend(feedItem);
              while (liveFeedEl.children.length > 10) {
                liveFeedEl.lastChild.remove();
              }
            }

            // Tasks
            const taskListEl = document.getElementById('task-list');
            taskListEl.innerHTML = '';
            const available = data.available_tasks || {};
            const done = data.tasks || [];
            let hasTask = false;
            for (const taskId in available) {
              hasTask = true;
              const task = available[taskId];
              const isCompleted = done.indexOf(taskId) !== -1;
              const item = document.createElement('div');
              item.className = 'task-item' + (isCompleted ? ' completed' : '');
              const reward = (task.reward_coins || 0) + ' ' + t('coins');
              const badge = isCompleted
                ? '<span class="completed-badge" data-translate-key="task_completed_badge">' + t('task_completed_badge') + '</span>'
                : '<button class="button" style="margin-top:0;width:auto;padding:8px 12px;" onclick="completeTask(\'' + taskId + '\')">' + t('task_complete_button') + '</button>';
              item.innerHTML = '<div class="task-info"><h3>' + (task.title || taskId) + '</h3><p>' + t('task_reward') + ': ' + reward + '</p></div>' + badge;
              taskListEl.appendChild(item);
            }
            if (!hasTask) {
              taskListEl.innerHTML = '<div class="task-item"><span>No tasks available.</span></div>';
            }

            // Withdraw requirements
            const reqGridEl = document.getElementById('req-grid');
            const reqs = data.withdrawal_reqs || {};
            reqGridEl.innerHTML =
              '<div class="req-item"><span data-translate-key="min_invites">' + t('min_invites') + '</span><br><span class="progress">' + (data.invites||0) + ' / ' + (reqs.min_invites||0) + '</span></div>' +
              '<div class="req-item"><span data-translate-key="min_tasks">' + t('min_tasks') + '</span><br><span class="progress">' + (done.length) + ' / ' + (reqs.min_tasks||0) + '</span></div>' +
              '<div class="req-item"><span data-translate-key="min_ads">' + t('min_ads') + '</span><br><span class="progress">' + (data.completed_ads||0) + ' / ' + (reqs.min_ads||0) + '</span></div>';

            // Withdraw history
            const historyListEl = document.getElementById('history-list');
            if (data.withdrawal_history && data.withdrawal_history.length > 0) {
              historyListEl.innerHTML = data.withdrawal_history.slice().reverse().map(function(item){
                var color = item.status === 'approved' ? 'var(--accent)' : (item.status === 'pending' ? '#f59e0b' : '#ef4444');
                var ts = '';
                if (item.timestamp) { try { ts = new Date(item.timestamp).toLocaleString(); } catch(e){} }
                return '<div class="history-item"><div><b>₹' + Number(item.amount||0).toFixed(2) + '</b><br><small>' + ts + '</small></div><div class="status" style="color:' + color + '">' + item.status + '</div></div>';
              }).join('');
            } else {
              historyListEl.innerHTML = '<div class="history-item"><span data-translate-key="no_history">' + t('no_history') + '</span></div>';
            }

            document.getElementById('withdraw-amount').placeholder = t('amount_placeholder');
            document.getElementById('withdraw-details').placeholder = t('upi_placeholder');

            translateUI();
          }

          async function completeTask(taskId) {
            try {
              const response = await fetch('/api/tasks/complete/' + userId + '/' + taskId, { method: 'POST' });
              const data = await response.json();
              document.getElementById('task-status').innerText = data.message || '';
              fetchData();
            } catch (e) {
              document.getElementById('task-status').innerText = 'Error completing task.';
            }
          }

          function shareInvite() {
            const link = document.getElementById('invite-link').value;
            const shareUrl = 'https://t.me/share/url?url=' + encodeURIComponent(link) + '&text=Join and earn money!';
            if (tg) { try { tg.openTelegramLink(shareUrl); return; } catch(e){} }
            window.open(shareUrl, '_blank');
          }

          async function requestWithdrawal() {
            const amount = document.getElementById('withdraw-amount').value;
            const details = document.getElementById('withdraw-details').value;
            const statusEl = document.getElementById('withdraw-status');
            if (!amount || !details) {
              statusEl.innerText = 'Please fill in both amount and UPI ID.';
              return;
            }
            try {
              const response = await fetch('/api/withdraw/' + userId, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: parseFloat(amount), details: details }) });
              const data = await response.json();
              statusEl.innerText = data.message || '';
              fetchData();
            } catch (e) {
              statusEl.innerText = 'Withdrawal error.';
            }
          }

          async function spinWheel() {
            const spinButton = document.getElementById('spin-button');
            const wheel = document.getElementById('wheel');
            const spinStatus = document.getElementById('spin-status');
            spinButton.disabled = true;
            spinStatus.innerText = 'Spinning...';
            try {
              const response = await fetch('/api/spin/' + userId, { method: 'POST' });
              const data = await response.json();
              if (!data.success) {
                spinStatus.innerText = data.message || '';
                spinButton.disabled = false;
                return;
              }
              const spinValues = [0.10, 0.15, 0.20, 0.00];
              const segmentIndex = spinValues.indexOf(data.value);
              const finalAngle = (segmentIndex * 90) + (Math.random() * 60) + (360 * 5);
              wheel.style.transform = 'rotate(' + finalAngle + 'deg)';
              setTimeout(function(){
                spinStatus.innerText = data.message || '';
                spinButton.disabled = false;
                fetchData();
              }, 4500);
            } catch (e) {
              spinStatus.innerText = 'Spin error.';
              spinButton.disabled = false;
            }
          }

          function setLanguage(lang) {
            currentLang = lang;
            localStorage.setItem('lang', lang);
            translateUI();
          }

          function showPage(pageName) {
            const pageId = 'page-' + pageName;
            document.querySelectorAll('.page').forEach(function(p){ p.classList.remove('active'); });
            const target = document.getElementById(pageId);
            if (target) target.classList.add('active');
            document.querySelectorAll('.nav-item').forEach(function(i){ i.classList.remove('active'); });
            const navBtn = document.querySelector('.nav-item[data-page="' + pageName + '"]');
            if (navBtn) navBtn.classList.add('active');
          }

          // Initial Load
          window.addEventListener('load', function(){
            fetchData();
            translateUI();
            setInterval(fetchData, 7000);
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
