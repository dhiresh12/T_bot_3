import re
import shutil
import subprocess

import pytest

from app.core import BotEngine
from app.mini_app import create_app


def _extract_main_script(html):
    blocks = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)
    return blocks[-1]


def _strip_jinja(js):
    js = re.sub(r"\{\{.*?\}\}", "null", js, flags=re.S)
    js = re.sub(r"\{%.*?%\}", "", js, flags=re.S)
    return js


def test_bonus_endpoint_updates_wallet():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-bonus.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.post("/api/bonus/777", json={"name": "Nadia"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["wallet"] >= 0.05

    profile_response = client.get("/api/profile/777")
    assert profile_response.status_code == 200
    profile = profile_response.get_json()
    assert profile["wallet"] >= 0.05


def test_homepage_exposes_dashboard_and_action_hooks():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-home.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/api/dashboard" in html
    assert "Spin for a Gift!" in html
    assert "Withdraw Funds" in html


def test_homepage_contains_interactive_dashboard_controls():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-controls.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="user-id"' in html
    assert 'id="task-list"' in html
    assert 'id="withdraw-amount"' in html
    assert 'id="invite-link"' in html


def test_quests_status_returns_serializable_json():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-quests.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/api/quests/status/777")
    assert response.status_code == 200
    payload = response.get_json()
    assert "steps" in payload
    assert "completed" in payload
    assert "all_completed" in payload
    assert isinstance(payload["steps"], list)
    for step in payload["steps"]:
        assert "id" in step
        assert "title" in step
        assert "desc" in step


def test_events_claim_route_registered():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-events.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.post("/api/events/claim/777")
    assert response.status_code in (200, 404)
    payload = response.get_json()
    assert "success" in payload


def test_mini_app_script_parses_without_syntax_errors():
    import os
    import tempfile

    engine = BotEngine(storage_path="/tmp/bot3-miniapp-syntax.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    js = _strip_jinja(_extract_main_script(html))

    node = shutil.which("node")
    if not node:
        pytest.skip("node not available to validate JS syntax")

    fd, path = tempfile.mkstemp(suffix=".js")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(js)
        proc = subprocess.run(
            [node, "--check", path],
            text=True,
            capture_output=True,
            timeout=30,
        )
    finally:
        os.unlink(path)
    assert proc.returncode == 0, proc.stderr


def test_beforeinstallprompt_handler_is_closed():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-bis.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "window.addEventListener('beforeinstallprompt', function(e) {" in html
    # The handler must be closed so the rest of the script is not nested inside it.
    assert "deferredPrompt = e;\n          });" in html


def test_crate_daily_limit_prevents_unlimited_farming():
    engine = BotEngine(storage_path="/tmp/bot3-crate-limit.json")
    engine.crate_cooldown_seconds = 0  # ignore cooldown in this test
    uid = 912345
    profile = engine.get_profile(uid)
    profile.coins = 1000000
    engine._save_user(profile)

    opened = 0
    for _ in range(100):
        success, message, reward = engine.open_crate(uid, "basic_crate")
        if success:
            opened += 1
        else:
            break

    assert opened == engine.daily_crate_open_limit
    success, message, reward = engine.open_crate(uid, "basic_crate")
    assert success is False
    assert "limit" in message.lower()


def test_ad_block_id_injected_into_template():
    import os
    os.environ["AD_BLOCK_ID"] = "TEST_BLOCK_123"
    try:
        engine = BotEngine(storage_path="/tmp/bot3-adblock.json")
        app = create_app(engine)
        client = app.test_client()
        response = client.get("/")
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "TEST_BLOCK_123" in html
        assert "adsgram.ai/static/js/sdk-v1.js" in html
    finally:
        del os.environ["AD_BLOCK_ID"]

