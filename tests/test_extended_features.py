from app.core import BotEngine
from app.mini_app import create_app


def test_tasks_invites_and_activity_flow():
    engine = BotEngine(storage_path="/tmp/bot3-extended.json")
    app = create_app(engine)
    client = app.test_client()

    task_response = client.post("/api/tasks/complete/501/join_channel")
    assert task_response.status_code == 200

    invite_response = client.post("/api/invite/501")
    assert invite_response.status_code == 200
    payload = invite_response.get_json()
    # The invite endpoint returns the current invite count (0 for a fresh user).
    assert "invite_count" in payload

    # Completing the single task above logs one activity entry.
    profile_response = client.get("/api/profile/501")
    assert profile_response.status_code == 200
    profile = profile_response.get_json()
    assert profile["activity_count"] >= 1


def test_help_and_admin_command_endpoints():
    engine = BotEngine(storage_path="/tmp/bot3-admin.json")
    app = create_app(engine)
    client = app.test_client()

    help_response = client.get("/api/help/701?lang=hi")
    assert help_response.status_code == 200
    help_payload = help_response.get_json()
    assert help_payload["language"] == "hi"

    admin_response = client.post(
        "/api/admin/commands/bonus",
        json={"value": 0.12},
        headers={"X-Admin-Key": "admin-xio"},
    )
    assert admin_response.status_code == 200
    assert engine.bonus_value == 0.12
