import pytest
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


def test_dashboard_includes_new_features(client):
    response = client.get("/api/dashboard/6001")
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


def test_challenge_api_endpoint(client):
    response = client.get("/api/challenges/6010")
    assert response.status_code == 200
    data = response.get_json()
    assert "challenges" in data


def test_achievements_api_endpoint(client):
    response = client.get("/api/achievements/6011")
    assert response.status_code == 200
    data = response.get_json()
    assert "achievements" in data


def test_scratch_api_endpoint(client):
    response = client.post("/api/scratch/6012")
    assert response.status_code == 200


def test_notifications_api_endpoint(client):
    response = client.get("/api/notifications/6013")
    assert response.status_code == 200
    data = response.get_json()
    assert "notifications" in data


def test_social_share_api_endpoint(client):
    response = client.post("/api/social/share/6014", json={"platform": "telegram"})
    assert response.status_code == 200


def test_level_leaderboard_api_endpoint(client):
    response = client.get("/api/leaderboard/level")
    assert response.status_code == 200


def test_leaderboard_rewards_api_endpoint(client):
    response = client.get("/api/leaderboard/rewards/6015")
    assert response.status_code == 200


def test_xp_add_api_endpoint(client):
    response = client.post("/api/xp/add/6016", json={"amount": 50})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
