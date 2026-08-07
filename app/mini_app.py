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

    # Phase 7: Complete UI Overhaul for the Mini App
    # This is a single-file template to keep it simple as requested.
    HTML = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{app_name}</title>
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
          .lang-switcher { font-size: 14px; color: var(--text-muted); }
          .lang-switcher button { background: none; border: none; color: var(--text-muted); cursor: pointer; font-weight: bold; padding: 4px; }
          .lang-switcher button.active { color: var(--primary); }
          /* Task List Styles */
          .task-item { background-color: var(--bg-light); padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
          .task-item.completed { opacity: 0.6; }
          .task-info h3 { margin: 0 0 4px; font-size: 16px; }
          .task-info p { margin: 0; font-size: 12px; color: var(--text-muted); }
          .task-item .completed-badge { color: var(--accent); font-weight: bold; }
          /* Withdraw Page Styles */
          .req-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
          .req-item { background-color: var(--bg-light); padding: 12px; border-radius: 8px; font-size: 13px; }
          .req-item .progress { font-weight: bold; font-size: 16px; }
          .withdraw-form input { width: calc(100% - 24px); padding: 12px; margin-bottom: 12px; background-color: var(--bg-light); border: 1px solid #334155; color: white; border-radius: 8px; }
          .history-item { background-color: var(--bg-light); padding: 12px; border-radius: 8px; margin-bottom: 8px; font-size: 13px; display: flex; justify-content: space-between; }
          .history-item .status { font-weight: bold; text-transform: capitalize; }
          /* Spin Wheel Styles */
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
        </style>
      </head>
      <body>
        <div class="container">
          <!-- Dashboard Page -->
          <div id="page-home" class="page active">
            <div class="header">
              <div id="avatar" class="avatar"></div>
              <div class="user-info">
                <h1 id="user-name">...</h1>
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
            <p id="spin-status" style="text-align:center; margin-top: 10px;"></p>

            <div class="live-feed" id="live-feed">
              <p data-translate-key="connecting_feed">Connecting to live feed...</p>
            </div>
          </div>

          <!-- Tasks Page -->
          <div id="page-tasks" class="page">
            <button class="back-button" onclick="showPage('home')">← Back</button>
            <h1 data-translate-key="tasks_title">Tasks</h1>
            <div id="task-list">
              <!-- Tasks will be dynamically inserted here -->
            </div>
            <p id="task-status" style="text-align:center; margin-top: 10px;"></p>
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
              <!-- Requirements will be dynamically inserted here -->
            </div>

            <h2 data-translate-key="withdraw_form_title">Request Payout</h2>
            <div class="withdraw-form">
              <input id="withdraw-amount" type="number" placeholder="Amount">
              <input id="withdraw-details" type="text" placeholder="UPI ID">
              <button class="button" onclick="requestWithdrawal()" data-translate-key="withdraw_button">Request Withdrawal</button>
              <p id="withdraw-status" style="text-align:center; margin-top: 10px;"></p>
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
          <button class="nav-item active" data-page="home" data-translate-key="nav_home"><div>🏠</div>Home</button>
          <button class="nav-item" data-page="tasks" data-translate-key="nav_tasks"><div>📋</div>Tasks</button>
          <button class="nav-item" data-page="invite" data-translate-key="nav_invite"><div>👥</div>Invite</button>
          <button class="nav-item" data-page="wallet" data-translate-key="nav_wallet"><div>💰</div>Wallet</button>
        </div>

        <script>
          const tg = window.Telegram.WebApp;
          tg.expand(); // Expand the mini app to full height

          const user = tg.initDataUnsafe?.user;
          const userId = user?.id || '777'; // Fallback for local testing
          const userName = user?.first_name || 'Guest';

          const translations = {translations_json};
          let currentLang = 'en';

          const liveFeedEl = document.getElementById('live-feed');

          async function fetchData() {
            const response = await fetch(`/api/dashboard/${"{"}userId{"}"}`);
            const data = await response.json();
            updateUI(data);
          }

          function translateUI() {
            document.querySelectorAll('[data-translate-key]').forEach(el => {
              const key = el.dataset.translateKey;
              if (translations[currentLang]?.ui[key]) {
                // For nav items, only translate the text part, not the emoji
                if (el.classList.contains('nav-item')) {
                    el.childNodes[1].nodeValue = ` ${"{"}translations[currentLang].ui[key]{"}"}`;
                } else {
                    el.innerText = translations[currentLang].ui[key];
                }
              }
            });
          }

          function updateUI(data) {
            document.getElementById('avatar').innerText = data.name.charAt(0);
            document.getElementById('user-name').innerText = data.name;
            document.getElementById('user-id').innerText = `ID: ${"{"}data.user_id{"}"}`;
            document.getElementById('balance-amount').innerText = `₹${"{"}data.wallet_rupee_equivalent.toFixed(4){"}"}`;
            document.getElementById('balance-coins').innerHTML = `${"{"}data.coins.toLocaleString(){"}"} <span data-translate-key="coins">${"{"}(translations[currentLang]?.ui?.coins || 'Coins'){"}"}</span>`;
            document.getElementById('current-tier').innerText = data.engagement.tier;
            document.getElementById('next-tier').innerText = `${"{"}translations[currentLang].ui.next_tier_prefix{"}"} ${"{"}data.engagement.next_tier{"}"}`;
            document.getElementById('invites-count').innerText = data.invites;
            document.getElementById('tasks-count').innerText = data.tasks?.length || 0;
            document.getElementById('invite-link').value = `https://t.me/{bot_username}?start=${"{"}data.user_id{"}"}`;
            
            // Update live feed (Dark Pattern)
            const feedItem = document.createElement('p');
            feedItem.innerText = data.live_feed[Math.floor(Math.random() * data.live_feed.length)];
            liveFeedEl.prepend(feedItem);
            if (liveFeedEl.children.length > 10) {
              liveFeedEl.lastChild.remove();
            }

            // --- New: Update Tasks Page ---
            const taskListEl = document.getElementById('task-list');
            taskListEl.innerHTML = ''; // Clear previous list

            for (const taskId in data.available_tasks) {
                const task = data.available_tasks[taskId];
                const isCompleted = data.tasks.includes(taskId);

                const taskItem = document.createElement('div');
                taskItem.className = `task-item ${"{"}isCompleted ? 'completed' : ''{"}"}`;
                
                let actionHtml = isCompleted
                    ? `<span class="completed-badge" data-translate-key="task_completed_badge">Completed</span>`
                    : `<button class="button" onclick="completeTask('${"{"}taskId{"}"}')" data-translate-key="task_complete_button">Complete</button>`;

                taskItem.innerHTML = `
                  <div class="task-info">
                    <h3>${"{"}task.title{"}"}</h3>
                    <p><span data-translate-key="task_reward">Reward</span>: ${"{"}task.reward_coins{"}"} <span data-translate-key="coins">Coins</span></p>
                  </div>
                  ${"{"}actionHtml{"}"}
                `;
                taskListEl.appendChild(taskItem);
            }

            // --- New: Update Withdraw Page ---
            const reqGridEl = document.getElementById('req-grid');
            const reqs = data.withdrawal_reqs;
            reqGridEl.innerHTML = `
                <div class="req-item">
                    <span data-translate-key="min_invites">Min Invites</span><br>
                    <span class="progress ${"{"}data.invites >= reqs.min_invites ? 'text-green-400' : ''{"}"}">${"{"}data.invites{"}"} / ${"{"}reqs.min_invites{"}"}</span>
                </div>
                <div class="req-item">
                    <span data-translate-key="min_tasks">Min Tasks</span><br>
                    <span class="progress ${"{"}data.tasks.length >= reqs.min_tasks ? 'text-green-400' : ''{"}"}">${"{"}data.tasks.length{"}"} / ${"{"}reqs.min_tasks{"}"}</span>
                </div>
                <div class="req-item">
                    <span data-translate-key="min_ads">Min Ads</span><br>
                    <span class="progress ${"{"}data.completed_ads >= reqs.min_ads ? 'text-green-400' : ''{"}"}">${"{"}data.completed_ads{"}"} / ${"{"}reqs.min_ads{"}"}</span>
                </div>
            `;

            const historyListEl = document.getElementById('history-list');
            if (data.withdrawal_history && data.withdrawal_history.length > 0) {
                historyListEl.innerHTML = data.withdrawal_history.reverse().map(item => `
                    <div class="history-item">
                        <div>
                            <b>₹${"{"}item.amount.toFixed(2){"}"}</b><br>
                            <small>${"{"}new Date(item.timestamp).toLocaleString(){"}"}</small>
                        </div>
                        <div class="status" style="color: ${"{"}item.status === 'approved' ? 'var(--accent)' : (item.status === 'pending' ? '#f59e0b' : '#ef4444'){"}"}">${"{"}item.status{"}"}</div>
                    </div>
                `).join('');
            } else {
                historyListEl.innerHTML = `<div class="history-item"><span data-translate-key="no_history">No withdrawal history yet.</span></div>`;
            }

            // Set placeholders
            document.getElementById('withdraw-amount').placeholder = translations[currentLang].ui.amount_placeholder;
            document.getElementById('withdraw-details').placeholder = translations[currentLang].ui.upi_placeholder;

            translateUI(); // Ensure UI is translated after data update
          }
          
          async function completeTask(taskId) {
              const response = await fetch(`/api/tasks/complete/${"{"}userId{"}"}/${"{"}taskId{"}"}`, { method: 'POST' });
              const data = await response.json();
              document.getElementById('task-status').innerText = data.message;
              fetchData(); // Refresh data after action
          }

          function shareInvite() {
              tg.openTelegramLink(`https://t.me/share/url?url=${"{"}encodeURIComponent(document.getElementById('invite-link').value){"}"}&text=Join and earn money!`);
          }

          async function requestWithdrawal() {
              const amount = document.getElementById('withdraw-amount').value;
              const details = document.getElementById('withdraw-details').value;
              const statusEl = document.getElementById('withdraw-status');

              if (!amount || !details) {
                  statusEl.innerText = 'Please fill in both amount and UPI ID.';
                  return;
              }

              const response = await fetch(`/api/withdraw/${"{"}userId{"}"}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ amount: parseFloat(amount), details: details }) });
              const data = await response.json();
              statusEl.innerText = data.message;
              fetchData(); // Refresh data
          }

          async function spinWheel() {
              const spinButton = document.getElementById('spin-button');
              const wheel = document.getElementById('wheel');
              const spinStatus = document.getElementById('spin-status');

              spinButton.disabled = true;
              spinStatus.innerText = 'Spinning...';

              const response = await fetch(`/api/spin/${"{"}userId{"}"}`, { method: 'POST' });
              const data = await response.json();

              if (!data.success) {
                  spinStatus.innerText = data.message;
                  spinButton.disabled = false;
                  return;
              }

              // Calculate rotation
              const spinValues = [0.10, 0.15, 0.20, 0.00]; // Must match CSS
              const segmentIndex = spinValues.indexOf(data.value);
              const segmentAngle = 90; // 360 / 4 segments
              const randomOffset = Math.random() * (segmentAngle - 20) + 10;
              const finalAngle = (segmentIndex * segmentAngle) + randomOffset + 360 * 5; // 5 full rotations

              wheel.style.transform = `rotate(${'${'}finalAngle}deg)`;

              setTimeout(() => {
                  spinStatus.innerText = data.message;
                  spinButton.disabled = false;
                  fetchData(); // Refresh balance
              }, 4500); // Match CSS transition time + buffer
          }

          function setLanguage(lang) {
            currentLang = lang;
            document.querySelectorAll('.lang-switcher button').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`lang-${"{"}lang{"}"}`).classList.add('active');
            translateUI();
            // You could also save this preference to localStorage
          }

          function showPage(pageName) {
              const pageId = `page-${"{"}pageName{"}"}`;
              document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
              document.getElementById(pageId)?.classList.add('active');
              
              document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
              document.querySelector(`.nav-item[data-page="${"{"}pageName{"}"}"]`)?.classList.add('active');
          }

          // Navigation
          document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
              showPage(item.dataset.page);
            });
          });

          // Initial Load
          window.addEventListener('load', () => {
            fetchData();
            translateUI();
            setInterval(fetchData, 7000); // Refresh data and feed every 7 seconds
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
