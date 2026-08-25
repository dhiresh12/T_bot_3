import pytest
from datetime import datetime, timedelta, timezone
from app.core import BotEngine
from app.mini_app import create_app


@pytest.fixture
def engine(tmp_path):
    storage = tmp_path / "bot3-newfeatures.json"
    return BotEngine(storage_path=str(storage))


@pytest.fixture
def client(engine):
    app = create_app(engine)
    return app.test_client()


@pytest.fixture
def auth_headers(engine, client):
    def _auth(user_id):
        engine.register_user(user_id, "TestUser")
        r = client.post("/api/auth/login", json={"user_id": user_id, "name": "TestUser"})
        assert r.status_code == 200
        token = r.get_json()["token"]
        return {"X-User-Token": token}
    return _auth


def test_level_progression_and_xp(engine):
    user_id = 5001
    engine.register_user(user_id, "LevelTest")
    profile = engine.get_profile(user_id)
    assert profile.level == 1
    assert profile.xp == 0

    result = engine.add_xp(user_id, 100)
    assert result["level"] == 2
    assert result["total_xp"] == 100
    profile = engine.get_profile(user_id)
    assert profile.level == 2
    assert profile.xp == 100


def test_achievements_unlock(engine):
    user_id = 5002
    engine.register_user(user_id, "AchTest")
    profile = engine.get_profile(user_id)
    assert len(profile.badges) == 0

    engine.complete_task(user_id, "join_channel")
    unlocked = engine.check_achievements(user_id)
    assert "first_task" in unlocked
    profile = engine.get_profile(user_id)
    assert "first_task" in profile.badges
    assert profile.coins >= 500


def test_daily_challenges(engine):
    user_id = 5003
    engine.register_user(user_id, "ChTest")
    profile = engine.get_profile(user_id)
    profile.daily_ads_watch_count = 5
    engine._save_user(profile)

    success, msg, data = engine.complete_daily_challenge(user_id, "watch_5_ads")
    assert success is True
    assert "completed" in msg.lower()
    profile = engine.get_profile(user_id)
    assert profile.daily_challenge_completed is True


def test_scratch_cards(engine):
    user_id = 5004
    engine.register_user(user_id, "ScratchTest")
    profile = engine.get_profile(user_id)
    profile.scratch_cards_available = 1
    engine._save_user(profile)

    success, msg, data = engine.scratch_card(user_id)
    assert success is True
    profile = engine.get_profile(user_id)
    assert profile.scratch_cards_available == 0
    assert "coins" in data


def test_streak_insurance(engine):
    user_id = 5005
    engine.register_user(user_id, "InsTest")
    profile = engine.get_profile(user_id)
    profile.streak_insurance = 1
    engine._save_user(profile)

    success, msg = engine.use_streak_insurance(user_id)
    assert success is True
    profile = engine.get_profile(user_id)
    assert profile.streak_insurance == 0


def test_referral_tiers(engine):
    user_id = 5006
    engine.register_user(user_id, "RefTest")
    profile = engine.get_profile(user_id)
    assert profile.referral_tier == "Bronze"

    profile.invite_count = 5
    engine._save_user(profile)
    info = engine.process_referral_tier_upgrade(user_id)
    assert info["current_tier"] == "Silver"


def test_super_and_mega_spin(engine):
    user_id = 5007
    engine.register_user(user_id, "SpinTest")
    profile = engine.get_profile(user_id)
    profile.super_spins_available = 1
    profile.mega_spins_available = 1
    engine._save_user(profile)

    success, msg, gift = engine.super_spin(user_id)
    assert success is True
    assert "SUPER SPIN" in msg
    profile = engine.get_profile(user_id)
    assert profile.super_spins_available == 0

    success2, msg2, gift2 = engine.mega_spin(user_id)
    assert success2 is True
    assert "MEGA SPIN" in msg2
    profile = engine.get_profile(user_id)
    assert profile.mega_spins_available == 0


def test_notifications(engine):
    user_id = 5008
    engine.register_user(user_id, "NotifTest")

    engine.add_notification(user_id, "Test", "Hello")
    notifs = engine.get_notifications(user_id)
    assert len(notifs) == 1
    assert notifs[0]["title"] == "Test"

    count = engine.mark_notifications_read(user_id)
    assert count == 1
    assert engine.get_profile(user_id).unread_notifications == 0


def test_social_sharing(engine):
    user_id = 5009
    engine.register_user(user_id, "SocialTest")

    success, msg, data = engine.share_social(user_id, "telegram")
    assert success is True
    profile = engine.get_profile(user_id)
    assert profile.social_shares_count == 1
    assert profile.coins >= 200

    success2, msg2, _ = engine.share_social(user_id, "telegram")
    assert success2 is True


def test_leaderboard_rewards(engine):
    user_id = 5010
    engine.register_user(user_id, "LBTest")
    engine.get_profile(user_id).wallet_bot = 100.0
    engine._save_user(engine.get_profile(user_id))

    info = engine.check_leaderboard_rewards(user_id)
    assert "available" in info


def test_dashboard_includes_new_features(client, auth_headers):
    headers = auth_headers(6001)
    response = client.get("/api/dashboard/6001", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "level" in data
    assert "xp" in data
    assert "badges" in data
    assert "scratch_cards_available" in data
    assert "daily_challenges" in data
    assert "notifications" in data
    assert "social_shares_count" in data
    assert "super_spins_available" in data
    assert "mega_spins_available" in data


def test_challenge_api_endpoint(client, auth_headers):
    headers = auth_headers(6010)
    response = client.get("/api/challenges/6010", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "challenges" in data


def test_achievements_api_endpoint(client, auth_headers):
    headers = auth_headers(6011)
    response = client.get("/api/achievements/6011", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "achievements" in data


def test_scratch_api_endpoint(client, auth_headers):
    headers = auth_headers(6012)
    response = client.post("/api/scratch/6012", headers=headers)
    assert response.status_code == 200


def test_notifications_api_endpoint(client, auth_headers):
    headers = auth_headers(6013)
    response = client.get("/api/notifications/6013", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "notifications" in data


def test_social_share_api_endpoint(client, auth_headers):
    headers = auth_headers(6014)
    response = client.post("/api/social/share/6014", json={"platform": "telegram"}, headers=headers)
    assert response.status_code == 200


def test_level_leaderboard_api_endpoint(client, auth_headers):
    headers = auth_headers(9999)
    response = client.get("/api/leaderboard/level", headers=headers)
    assert response.status_code == 200


def test_leaderboard_rewards_api_endpoint(client, auth_headers):
    headers = auth_headers(6015)
    response = client.get("/api/leaderboard/rewards/6015", headers=headers)
    assert response.status_code == 200


def test_xp_add_api_endpoint(client, auth_headers):
    headers = auth_headers(6016)
    response = client.post("/api/xp/add/6016", json={"amount": 50}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

# --- Daily Streak Rewards Tests ---

def test_daily_streak_claim(engine):
    user_id = 7001
    profile = engine.register_user(user_id, "StreakUser")
    assert profile.daily_login_streak == 0
    success, message, data = engine.claim_daily_login_reward(user_id)
    assert success is True
    assert profile.daily_login_streak == 1
    assert data["coins"] == 50
    assert data["streak"] == 1

def test_daily_streak_miss_resets(engine):
    user_id = 7002
    profile = engine.register_user(user_id, "StreakUser2")
    profile.last_login_date = "2020-01-01"
    profile.daily_login_streak = 3
    success, message, data = engine.claim_daily_login_reward(user_id)
    assert success is True
    assert profile.daily_login_streak == 1

def test_daily_streak_duplicate_claim(engine):
    user_id = 7003
    profile = engine.register_user(user_id, "StreakUser3")
    profile.last_login_date = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    success, message, data = engine.claim_daily_login_reward(user_id)
    assert success is False
    assert "Already claimed" in message

def test_streak_info_api(client, auth_headers):
    headers = auth_headers(7004)
    response = client.get("/api/streak/info/7004", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "streak" in data
    assert "claimed_today" in data

def test_streak_claim_api(client, auth_headers):
    headers = auth_headers(7005)
    response = client.post("/api/streak/claim/7005", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

# --- Limited-Time Events Tests ---

def test_active_event(engine):
    engine.active_events = [
        {"id": "evt1", "start": "2020-01-01T00:00:00", "end": "2099-01-01T00:00:00", "title": "Test Event", "reward": {"coins": 100}}
    ]
    event = engine.get_active_event()
    assert event is not None
    assert event["id"] == "evt1"

def test_claim_event_reward(engine):
    user_id = 7011
    profile = engine.register_user(user_id, "EventUser")
    engine.active_events = [
        {"id": "evt2", "start": "2020-01-01T00:00:00", "end": "2099-01-01T00:00:00", "title": "Test Event", "reward": {"coins": 100, "xp": 50}}
    ]
    success, message, data = engine.claim_event_reward(user_id, "evt2")
    assert success is True
    assert profile.coins == 100
    assert "evt2" in profile.claimed_event_rewards

def test_event_duplicate_claim(engine):
    user_id = 7012
    profile = engine.register_user(user_id, "EventUser2")
    profile.claimed_event_rewards.append("evt3")
    engine.active_events = [
        {"id": "evt3", "start": "2020-01-01T00:00:00", "end": "2099-01-01T00:00:00", "title": "Test", "reward": {}}
    ]
    success, message, data = engine.claim_event_reward(user_id, "evt3")
    assert success is False

def test_event_api_active(client, auth_headers):
    headers = auth_headers(7013)
    response = client.get("/api/events/active", headers=headers)
    assert response.status_code == 200

def test_event_api_claim(client, auth_headers):
    headers = auth_headers(7014)
    response = client.post("/api/events/claim/7014", headers=headers)
    assert response.status_code in (200, 404, 400)

# --- PIN Lock Tests ---

def test_set_and_verify_pin(engine):
    user_id = 7021
    profile = engine.register_user(user_id, "PinUser")
    success, message = engine.set_pin(user_id, "1234")
    assert success is True
    assert profile.pin_set is True
    assert engine.verify_pin(user_id, "1234") is True
    assert engine.verify_pin(user_id, "0000") is False

def test_pin_length_validation(engine):
    user_id = 7022
    profile = engine.register_user(user_id, "PinUser2")
    success, message = engine.set_pin(user_id, "123")
    assert success is False
    success, message = engine.set_pin(user_id, "1234567")
    assert success is False

def test_pin_api(client, auth_headers):
    headers = auth_headers(7023)
    response = client.post("/api/security/set-pin/7023", json={"pin": "1234"}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

def test_pin_verify_api(client, auth_headers):
    headers = auth_headers(7024)
    client.post("/api/security/set-pin/7024", json={"pin": "1234"}, headers=headers)
    response = client.post("/api/security/verify-pin/7024", json={"pin": "1234"}, headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True

# --- A/B Testing Tests ---

def test_ab_variant_assignment(engine):
    user_id = 7031
    profile = engine.register_user(user_id, "ABUser")
    variant = engine.get_ab_variant(user_id, "withdrawal_countdown")
    assert variant in ["3min", "5min", "10min"]

def test_ab_variant_consistency(engine):
    user_id = 7032
    profile = engine.register_user(user_id, "ABUser2")
    v1 = engine.get_ab_variant(user_id, "fee_structure")
    v2 = engine.get_ab_variant(user_id, "fee_structure")
    assert v1 == v2

def test_ab_api(client, auth_headers):
    headers = auth_headers(7033)
    response = client.get("/api/ab/variant/7033?test=withdrawal_countdown", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "variant" in data

# --- Achievement Sharing Tests ---

def test_record_share_reward(engine):
    user_id = 7041
    profile = engine.register_user(user_id, "ShareUser")
    success, message, data = engine.record_share_reward(user_id, "first_task")
    assert success is True
    assert profile.coins == 20
    assert "first_task" in profile.shared_achievements

def test_share_reward_duplicate(engine):
    user_id = 7042
    profile = engine.register_user(user_id, "ShareUser2")
    profile.shared_achievements.append("first_task")
    success, message, data = engine.record_share_reward(user_id, "first_task")
    assert success is False

def test_share_api(client, auth_headers):
    headers = auth_headers(7043)
    response = client.post("/api/achievements/share/7043", json={"achievement_id": "first_task"}, headers=headers)
    assert response.status_code == 200

# --- Admin Analytics v2 Tests ---

def test_admin_analytics_v2(engine):
    user_id = 7051
    profile = engine.register_user(user_id, "AdminUser")
    profile.admin = True
    data = engine.get_admin_analytics_v2()
    assert "total_users" in data
    assert "active_today" in data
    assert "retention_rate" in data
    assert "top_tasks" in data

def test_admin_analytics_api(client, auth_headers):
    headers = auth_headers(7052)
    client.post("/api/auth/login/7052", json={"name": "Admin2", "password": "test123"}, headers=headers)
    response = client.get("/api/admin/analytics/v2", headers=headers)
    assert response.status_code in (200, 403)

# --- Notification Unread Count Tests ---

def test_notification_unread_count_api(client, auth_headers):
    headers = auth_headers(7061)
    response = client.get("/api/notifications/unread-count/7061", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "count" in data

# --- Offline Sync Tests ---

def test_offline_sync_api(client, auth_headers):
    headers = auth_headers(7071)
    response = client.post("/api/offline/sync/7071", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert "synced" in data

# --- PWA Manifest Tests ---

def test_pwa_manifest(client):
    response = client.get("/manifest.json")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == "Xio_PayPlus"
    assert data["start_url"] == "/"
