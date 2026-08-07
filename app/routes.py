from __future__ import annotations

import json
from typing import Any

from app.telegram_bot import TelegramBotService
from flask import Blueprint, current_app, jsonify, request, render_template_string

bp = Blueprint("main", __name__)


@bp.get("/health")
def health() -> tuple[dict, int]:
    return jsonify({"status": "ok"}), 200


@bp.get("/api/ads/config")
def ads_config() -> tuple[dict, int]:
    ads_manager = current_app.config.get("ads_manager")
    if ads_manager is None:
        return jsonify({"provider": "admob"}), 200
    return jsonify(ads_manager.get_config()), 200


@bp.post("/webhook")
def telegram_webhook() -> tuple[dict, int]:
    """
    This is the main entry point for Telegram updates.
    Telegram will send a POST request to this endpoint.
    """
    update = request.get_json(silent=True)
    if not update:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    # We create a new service instance for each request to ensure it's stateless,
    # but it uses the shared engine from the app context.
    engine = current_app.config["engine"]
    telegram_service = TelegramBotService(engine=engine)
    telegram_service.handle_update(update) # The service sends the reply via API call
    return jsonify({"status": "ok"}), 200


@bp.get("/api/sections/<int:user_id>")
def sections(user_id: int) -> tuple[dict, int]:
    engine = current_app.config.get("engine")
    if engine is None:
        return jsonify({"user_id": user_id, "sections": []}), 200
    engine.register_user(user_id, "Guest")
    profile = engine.get_profile(user_id)
    return jsonify(
        {
            "user_id": profile.user_id,
            "sections": [
                {"key": "ads", "title": "Watch Ads", "enabled": True},
                {"key": "tasks", "title": "Daily Tasks", "enabled": True},
                {"key": "invite", "title": "Invite Friends", "enabled": True},
                {"key": "wallet", "title": "Wallet", "enabled": True},
            ],
        }
    ), 200


# --- User-facing API Endpoints (Moved from mini_app.py) ---

@bp.post("/api/bonus/<int:user_id>")
def bonus(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "User")
    current_engine.register_user(user_id, name)
    reply = current_engine.handle_command(user_id, "bonus")
    profile = current_engine.get_profile(user_id)
    return jsonify({"message": reply, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@bp.get("/api/profile/<int:user_id>")
def profile(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    return jsonify(
        {
            "user_id": profile.user_id,
            "name": profile.name,
            "wallet": profile.wallet_bot,
            "coins": profile.coins,
            "activity_count": current_engine.get_activity_count(profile),
        }
    ), 200


@bp.post("/api/ads/watch/<int:user_id>")
def watch_ads(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.watch_ads(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@bp.post("/api/tasks/complete/<int:user_id>/<task_id>")
def complete_task(user_id: int, task_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    completed, message = current_engine.complete_task(user_id, task_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"completed": completed, "message": message, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@bp.post("/api/invite/<int:user_id>")
def invite(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    # The invite_user method is now called by register_user if inviter_id is present.
    # For direct API call, we might need a specific endpoint if it's not handled by /start.
    # For now, we'll simulate the reward for the inviter if this was a direct invite.
    # This might need refinement based on how the mini-app actually triggers invites.
    # For now, let's assume this endpoint is for getting invite count.
    profile = current_engine.get_profile(user_id)
    return jsonify({"invite_count": profile.invite_count, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@bp.get("/api/help/<int:user_id>")
def help_endpoint(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    language = request.args.get("lang", "en")
    current_engine.register_user(user_id, "Guest")
    return jsonify(current_engine.get_help(language)), 200


@bp.get("/api/dashboard/<int:user_id>")
def dashboard(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    return jsonify(current_engine.get_dashboard(user_id)), 200


@bp.get("/api/engagement/<int:user_id>")
def engagement(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    return jsonify(
        {
            "trust_feed": current_engine.engagement.build_trust_feed(),
            "progress": current_engine.engagement.build_progress_snapshot(profile.wallet_bot, profile.coins),
        }
    ), 200


@bp.get("/api/support")
def support() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.support.get_faq()), 200


@bp.post("/api/support/message")
def support_message() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    return jsonify(current_engine.support.build_support_message(payload.get("message", ""))), 200


@bp.get("/api/leaderboard")
def leaderboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.get_leaderboard()), 200


@bp.post("/api/withdraw/<int:user_id>")
def withdraw(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = float(payload.get("amount", current_engine.min_withdrawal))
    method = payload.get("method", "upi")
    details = payload.get("details", "")
    current_engine.register_user(user_id, "Guest")
    message = current_engine.request_withdrawal(user_id, amount, method, details)
    return jsonify({"message": message}), 200


@bp.post("/api/spin/<int:user_id>")
def spin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, value = current_engine.spin_wheel(user_id)
    return jsonify({"success": success, "message": message, "value": value}), 200


# --- Admin API Endpoints (New/Moved) ---

@bp.get("/api/admin/dashboard")
def admin_dashboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    return jsonify(current_engine.admin_service.get_admin_dashboard()), 200


@bp.get("/api/admin/users")
def admin_users() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    return jsonify(current_engine.admin_service.get_all_users_summary()), 200


@bp.get("/api/admin/view_user/<int:user_id>")
def admin_view_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    target_profile = current_engine.admin_service.get_user_full_profile(user_id)
    if not target_profile:
        return jsonify({"error": f"User {user_id} not found."}), 404
    
    # Convert dataclass to dict for JSON serialization
    from dataclasses import asdict
    profile_dict = asdict(target_profile)
    return jsonify(profile_dict), 200


@bp.post("/api/admin/set")
def admin_set_config() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
        
    payload = request.get_json(silent=True) or {}
    setting = payload.get("setting")
    value = payload.get("value")

    if not setting or value is None:
        return jsonify({"error": "Missing 'setting' or 'value' in request body."}), 400
    
    success, message = current_engine.admin_service.update_bot_config(setting, value)
    return jsonify({"success": success, "message": message}), 200


@bp.post("/api/admin/commands/<command>")
def admin_command(command: str) -> tuple[dict, int]:
    """
    Generic admin command endpoint.
    Supports commands like 'bonus' to update a bot-level setting.
    """
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key") or (
        request.get_json(silent=True) or {}).get("admin_key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    value = payload.get("value")

    # Map simple admin commands to engine config attributes
    config_map = {
        "bonus": "bonus_value",
        "min_withdrawal": "min_withdrawal",
        "daily_ads_limit": "daily_ads_limit",
        "daily_spin_limit": "daily_spin_limit",
        "coins_to_rupee_rate": "coins_to_rupee_rate",
        "withdrawal_fee_percent": "withdrawal_fee_percent",
    }
    setting = config_map.get(command)
    if setting is None:
        return jsonify({"error": f"Unknown admin command '{command}'."}), 400

    success, message = current_engine.admin_service.update_bot_config(setting, value)
    return jsonify({"success": success, "message": message}), 200


@bp.post("/api/admin/commands/bonus")
def admin_command_bonus() -> tuple[dict, int]:
    """Admin route to update the daily bonus value."""
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    payload = request.get_json(silent=True) or {}
    # Allow the admin key to be supplied either in the header or in the body.
    body_key = payload.get("admin_key")
    if (not admin_key or admin_key != current_engine.admin_key) and body_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    value = payload.get("value")
    if value is None:
        return jsonify({"error": "Missing 'value' in request body."}), 400

    try:
        current_engine.bonus_value = float(value)
    except (ValueError, TypeError):
        return jsonify({"error": "'value' must be a number."}), 400

    return jsonify({"success": True, "message": f"Bonus value updated to '{current_engine.bonus_value}'."}), 200


@bp.post("/api/admin/backup")
def admin_backup() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    message = current_engine.admin_service.create_backup()
    return jsonify({"message": message}), 200


@bp.post("/api/admin/rollback")
def admin_rollback() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
        
    payload = request.get_json(silent=True) or {}
    filename = payload.get("filename")
    if not filename:
        return jsonify({"error": "Missing 'filename' in request body."}), 400
    
    success = current_engine.admin_service.rollback_to_backup(filename)
    message = "Rollback successful." if success else "Rollback failed. File not found or an error occurred."
    return jsonify({"success": success, "message": message}), 200


@bp.post("/api/admin/approve_withdrawal")
def admin_approve_withdrawal() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    admin_id = 1 # We still need an admin ID to log who approved it.
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    request_id = payload.get("request_id")
    verification_code = payload.get("verification_code")

    if not all([user_id, request_id, verification_code]):
        return jsonify({"error": "Missing user_id, request_id, or verification_code in request body."}), 400
    
    message = current_engine.approve_withdrawal(admin_id, user_id, request_id, verification_code)
    return jsonify({"message": message}), 200


@bp.get("/api/admin/backups")
def admin_backups() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    backups = current_engine.admin_service.list_backups()
    return jsonify(backups), 200

@bp.get("/api/admin/total_balance_over_time")
def admin_total_balance_over_time() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    data = current_engine.admin_service.get_total_coin_balance_over_time()
    return jsonify(data), 200


@bp.get("/api/admin/user_tier_distribution")
def admin_user_tier_distribution() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    data = current_engine.admin_service.get_user_tier_distribution()
    return jsonify(data), 200











@bp.post("/api/admin/edit_user/<int:user_id>")
def admin_edit_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "Missing update data in request body."}), 400

    # Sanitize payload to only allow specific fields to be edited. 'coins' is intentionally left out for now.
    allowed_updates = {
        "admin": payload.get("admin"),
        "invite_count": payload.get("invite_count"),
        "total_ads_watched": payload.get("total_ads_watched"),
        "daily_spin_count": payload.get("daily_spin_count"),
        "wallet_bot": payload.get("wallet_bot"),
        "wallet_app": payload.get("wallet_app"),
    }
    # Filter out None values so we don't accidentally set fields to null
    updates_to_apply = {k: v for k, v in allowed_updates.items() if v is not None}

    success, message = current_engine.admin_service.edit_user_profile(user_id, updates_to_apply)
    return jsonify({"success": success, "message": message}), 200


# --- Admin Dashboard UI ---

@bp.get("/admin")
def admin_ui() -> str:
    """Renders the dedicated Admin Dashboard UI."""
    # In a real app, this route would be protected by admin authentication.
    
    ADMIN_HTML = """
    <!doctype html>
    <html lang="en">
      <head>
                <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Dashboard - Xio PayPlus</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
          :root { --bg-dark: #111827; --bg-light: #1f2937; --primary: #ef4444; --text-light: #f3f4f6; --text-muted: #9ca3af; }
          body { font-family: sans-serif; background-color: var(--bg-dark); color: var(--text-light); margin: 0; padding: 24px; }

          h1, h2 { color: white; border-bottom: 1px solid #374151; padding-bottom: 8px; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 24px; }
          .card { background-color: var(--bg-light); padding: 20px; border-radius: 12px; }
          .card .label { font-size: 14px; color: var(--text-muted); }
          .card .value { font-size: 28px; font-weight: bold; margin-top: 8px; }
          table { width: 100%; border-collapse: collapse; margin-top: 16px; }
          th, td { padding: 12px; text-align: left; border-bottom: 1px solid #374151; }
          th { background-color: #374151; }
          .button { background-color: var(--primary); color: white; border: none; padding: 8px 12px; border-radius: 8px; cursor: pointer; }
          .button-secondary { background-color: #4f46e5; }
          input { background-color: #374151; color: white; border: 1px solid #4b5563; padding: 8px; border-radius: 6px; }
          .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.6); }
          .modal-content { background-color: var(--bg-light); margin: 15% auto; padding: 20px; border: 1px solid #888; width: 80%; max-width: 400px; border-radius: 12px; }
          .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Admin Dashboard</h1>
          
          <div id="stats-grid" class="grid"></div>

          <h2>Pending Withdrawals</h2>
          <div class="card">
            <table id="pending-withdrawals-table">
              <thead><tr><th>User ID</th><th>Request ID</th><th>Amount</th><th>Action</th></tr></thead>
              <tbody><tr><td colspan="4">Loading...</td></tr></tbody>
            </table>
          </div>

          <h2>All Users</h2>
          <div class="card">
            <input type="text" id="user-search" placeholder="Search by User ID or Name..." onkeyup="filterUsers()" style="width: 98%; margin-bottom: 12px;">
            <table id="users-table">
              <thead><tr><th>User ID</th><th>Name</th><th>Coins</th><th>Invites</th><th>Admin?</th></tr></thead>
              <tbody><tr><td colspan="6">Loading...</td></tr></tbody>
            </table>
          </div>
          <p id="edit-status" style="text-align: center; margin-top: 10px; color: var(--accent);"></p>

          <h2>New Users Over Time</h2>
          <div class="card">
          <canvas id="newUsersChart"></canvas>
          </div>

          <h2>Total Coin Balance Over Time</h2>
          <div class="card">
            <canvas id="totalBalanceChart"></canvas>
          </div>

          <h2>User Tier Distribution</h2>
          <div class="card">
            <canvas id="tierDistributionChart"></canvas>
          </div>

          <h2>Bot Settings</h2>
          <div class="card grid">
            <div>
                <label for="setting-rate">Coin-to-Rupee Rate</label><br>
                <input id="setting-rate" type="number" step="0.00001" onchange="updateSetting('coins_to_rupee_rate', this.value)">
            </div>
            <div>
                <label for="setting-fee">Withdrawal Fee (%)</label><br>
                <input id="setting-fee" type="number" step="1" onchange="updateSetting('withdrawal_fee_percent', this.value)">
            </div>
          </div>

          <h2>Data Management</h2>
          <div class="card grid">
            <div>
            <button class="button-secondary" onclick="createBackup()">Create Backup</button>
            <p id="backup-status" style="margin-top: 10px;"></p>
            </div>
            <div>
              <label for="backup-list">Rollback to Backup</label><br>
              <select id="backup-list" style="width: 70%; padding: 8px; background-color: #374151; color: white; border-radius: 6px; border: 1px solid #4b5563;"></select>
              <button class="button" onclick="rollback()" style="width: 25%; margin-left: 5%;">Rollback</button>
            </div>
          </div>

          <h2>Broadcast Message</h2>
          <div class="card">
              <textarea id="broadcast-message" rows="3" style="width: 98%; background-color: #374151; color: white; border-radius: 6px; border: 1px solid #4b5563;" placeholder="Send a message to all users..."></textarea>
              <button class="button-secondary" style="margin-top: 10px;" onclick="sendBroadcast()">Send Broadcast</button>
              <p id="broadcast-status"></p>
          </div>
        </div>

        <script>
          async function api(url, options = {}) {
            const adminKey = localStorage.getItem('adminKey') || 'admin-xio';
            const defaultOptions = { headers: { 'X-Admin-Key': adminKey } };
            const mergedOptions = { ...defaultOptions, ...options, headers: { ...defaultOptions.headers, ...options.headers } };
            const response = await fetch(url, mergedOptions);
            if (!response.ok) throw new Error(`API Error: ${"{"}response.status{"}"}`);
            return response.json();
          }

          async function loadDashboard() {
            const data = await api('/api/admin/dashboard');
            const grid = document.getElementById('stats-grid');
            grid.innerHTML = `
              <div class="card"><div class="label">Active Users</div><div class="value">${"{"}data.active_users{"}"}</div></div>
              <div class="card"><div class="label">Total Wallet Balance</div><div class="value">₹${"{"}data.total_wallet_balance.toFixed(2){"}"}</div></div>
              <div class="card"><div class="label">Pending Withdrawals</div><div class="value">${"{"}data.pending_withdrawals.length{"}"}</div></div>
            `;
            
            const tableBody = document.querySelector('#pending-withdrawals-table tbody');
            if (data.pending_withdrawals.length > 0) {
              tableBody.innerHTML = data.pending_withdrawals.map(req => `
                <tr>
                  <td>${"{"}req.user_id{"}"}</td>
                  <td>${"{"}req.request_id{"}"}</td>
                  <td>₹${"{"}req.amount.toFixed(2){"}"}</td>
                  <td><button class="button" onclick="openApprovalModal('${"{"}req.user_id{"}"}', '${"{"}req.request_id{"}"}')">Approve</button></td>
                </tr>
              `).join('');
            } else {
              tableBody.innerHTML = '<tr><td colspan="4">No pending withdrawals.</td></tr>';
            }
          }

          async function loadUsers() {
            const users = await api('/api/admin/users');
            const tableBody = document.querySelector('#users-table tbody');
            tableBody.innerHTML = users.map(user => `
              <tr>
                <td>${"{"}user.user_id{"}"}</td>
                <td>${"{"}user.name{"}"}</td>
                <td><input type="number" value="${"{"}user.coins{"}"}" onchange="updateUserField(${"{"}user.user_id{"}"}, 'coins', this.value, 'number')"></td>
                <td><input type="number" value="${"{"}user.invite_count{"}"}" onchange="updateUserField(${"{"}user.user_id{"}"}, 'invite_count', this.value, 'number')"></td>
                <td><input type="checkbox" ${"{"}user.is_admin ? 'checked' : ''{"}"} onchange="updateUserField(${"{"}user.user_id{"}"}, 'admin', this.checked, 'boolean')"></td>
              </tr>
            `).join('');
          }

          function filterUsers() {
            const searchTerm = document.getElementById('user-search').value.toLowerCase();
            const rows = document.querySelectorAll('#users-table tbody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
          }

          async function loadBackups() {
            const backups = await api('/api/admin/backups');
            const selectEl = document.getElementById('backup-list');
            selectEl.innerHTML = backups.map(b => `<option value="${"{"}b{"}"}">${"{"}b{"}"}</option>`).join('');
          }

          function openApprovalModal(userId, requestId) {
            document.getElementById('modal-request-id').innerText = requestId;
            document.getElementById('modal-approve-btn').onclick = () => approveWithdrawal(userId, requestId);
            document.getElementById('approvalModal').style.display = 'block';
          }

          function closeModal() {
            document.getElementById('approvalModal').style.display = 'none';
            document.getElementById('verification-code').value = '';
          }

          async function approveWithdrawal(userId, requestId) {
            const code = document.getElementById('verification-code').value;
            if (!code) { alert('Please enter the verification code.'); return; }
            try {
              const result = await api('/api/admin/approve_withdrawal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: parseInt(userId), request_id: requestId, verification_code: code })
              });
              alert(result.message);
              closeModal();
              loadDashboard(); // Refresh dashboard
            } catch (e) {
              alert('Approval failed. Check the code and try again.');
            }
          }
          
          async function updateUserField(userId, field, value, type) {
            let processedValue = value;
            if (type === 'number') processedValue = parseInt(value, 10);
            if (type === 'boolean') processedValue = !!value;

            const statusEl = document.getElementById('edit-status');
            statusEl.innerText = `Updating user ${"{"}userId{"}"}...`;

            try {
              const result = await api(`/api/admin/edit_user/${"{"}userId{"}"}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [field]: processedValue })
              });
              statusEl.innerText = result.message;
            } catch (e) {
              statusEl.innerText = `Error updating user ${"{"}userId{"}"}.`;
            }
          }

          async function updateSetting(setting, value) {
            const result = await api('/api/admin/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ setting, value })
            });
            alert(result.message);
          }

          async function createBackup() {
              const statusEl = document.getElementById('backup-status');
              statusEl.innerText = 'Creating backup...';
              const result = await api('/api/admin/backup', { method: 'POST' });
              statusEl.innerText = result.message;
              loadBackups(); // Refresh backup list
          }

          async function rollback() {
            const filename = document.getElementById('backup-list').value;
            if (!filename || !confirm(`Are you sure you want to roll back to ${"{"}filename{"}"}? This cannot be undone.`)) return;
            
            const result = await api('/api/admin/rollback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });
            alert(result.message);
            window.location.reload(); // Reload the page to see changes
          }

          function sendBroadcast() {
              // This is a placeholder as the backend doesn't have a real broadcast mechanism yet.
              const message = document.getElementById('broadcast-message').value;
              document.getElementById('broadcast-status').innerText = `Broadcast functionality is not yet implemented. Message: "${"{"}message{"}"}"`;
          }

          async function loadNewUsersChart() {
            try {
              const data = await api('/api/admin/user_registrations_over_time');
              const labels = data.map(item => item.date);
              const counts = data.map(item => item.count);

              const ctx = document.getElementById('newUsersChart').getContext('2d');
              new Chart(ctx, {
                type: 'line',
                data: {
                  labels: labels,
                  datasets: [{
                    label: 'New Users',
                    data: counts,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true
                  }]
                },
                options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    y: {
                      beginAtZero: true,
                      title: { display: true, text: 'Number of Users' }
                    }
                  }
                }
              });
            } catch (error) {
              console.error("Error loading new users chart:", error);
            }
          }

          async function loadTotalBalanceChart() {
            try {
              const data = await api('/api/admin/total_balance_over_time');
              const labels = data.map(item => item.date);
              const balances = data.map(item => item.total_coins);

              const ctx = document.getElementById('totalBalanceChart').getContext('2d');
              new Chart(ctx, {
                type: 'line',
                data: {
                  labels: labels,
                  datasets: [{
                    label: 'Total Coins in System',
                    data: balances,
                    borderColor: 'rgb(239, 68, 68)', // var(--primary)
                    tension: 0.1,
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    fill: true
                  }]
                },
                options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  scales: {
                    x: {
                      type: 'time',
                      time: { unit: 'day' },
                      title: { display: true, text: 'Date' }
                    },
                    y: {
                      beginAtZero: true,
                      title: { display: true, text: 'Total Coins' }
                    }
                  }
                }
              });
            } catch (error) {
              console.error("Error loading total balance chart:", error);
            }
          }

          async function loadTierDistributionChart() {
            try {
              const data = await api('/api/admin/user_tier_distribution');
              const labels = data.map(item => item.tier);
              const counts = data.map(item => item.count);

              const ctx = document.getElementById('tierDistributionChart').getContext('2d');
              new Chart(ctx, {
                type: 'pie',
                data: {
                  labels: labels,
                  datasets: [{
                    label: 'Users by Tier',
                    data: counts,
                    backgroundColor: [
                      '#a8a29e', // Bronze (stone)
                      '#94a3b8', // Silver (slate)
                      '#fbbf24', // Gold (amber)
                      '#60a5fa', // Platinum (blue)
                      '#34d399', // Diamond (emerald)
                      '#c084fc', // Crown (purple)
                      '#ef4444'  // Conqueror (red)
                    ],
                    hoverOffset: 4
                  }]
                },
                options: {
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { position: 'right', labels: { color: 'white' } },
                    title: { display: true, text: 'User Tier Distribution', color: 'white' }
                  }
                }
              });
            } catch (error) {
              console.error("Error loading tier distribution chart:", error);
            }
          }

          window.onload = () => {
            loadDashboard();
            loadUsers();
            loadBackups();
            loadNewUsersChart();
            loadTotalBalanceChart();
            loadTierDistributionChart();
          };
        </script>
      </body>

    </html>
    """
    return render_template_string(ADMIN_HTML)
