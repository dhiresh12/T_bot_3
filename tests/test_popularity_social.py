import pytest
from app.core import BotEngine
from app.mini_app import create_app


@pytest.fixture
def engine(tmp_path):
    storage = tmp_path / "bot3-popularity.json"
    return BotEngine(storage_path=str(storage))


@pytest.fixture
def client(engine):
    app = create_app(engine)
    return app.test_client()


def test_claim_daily_popularity(engine):
    user_id = 7001
    engine.register_user(user_id, "PopUser")
    success, msg, data = engine.claim_daily_popularity(user_id)
    assert success is True
    assert "10" in msg
    profile = engine.get_profile(user_id)
    assert profile.popularity_points == 10
    assert profile.daily_free_popularity_claimed is True

    success2, msg2, _ = engine.claim_daily_popularity(user_id)
    assert success2 is False
    assert "already claimed" in msg2.lower()


def test_buy_popularity_with_coins(engine):
    user_id = 7002
    engine.register_user(user_id, "CoinBuyer")
    profile = engine.get_profile(user_id)
    profile.coins = 1000
    engine._save_user(profile)

    success, msg, data = engine.buy_popularity_with_coins(user_id, 5)
    assert success is True
    assert "5" in msg
    profile = engine.get_profile(user_id)
    assert profile.popularity_points == 5
    assert profile.coins == 1000 - (5 * 100)


def test_buy_popularity_with_money(engine):
    user_id = 7003
    engine.register_user(user_id, "MoneyBuyer")
    profile = engine.get_profile(user_id)
    profile.wallet_bot = 1.0
    engine._save_user(profile)

    success, msg, data = engine.buy_popularity_with_money(user_id, 50)
    assert success is True
    assert "50" in msg
    profile = engine.get_profile(user_id)
    assert profile.popularity_points == 50


def test_send_popularity(engine):
    user1 = 7010
    user2 = 7011
    engine.register_user(user1, "Sender")
    engine.register_user(user2, "Receiver")
    profile1 = engine.get_profile(user1)
    profile1.popularity_points = 100
    engine._save_user(profile1)

    success, msg, data = engine.send_popularity(user1, user2, 20)
    assert success is True
    assert "20" in msg
    p1 = engine.get_profile(user1)
    p2 = engine.get_profile(user2)
    assert p1.popularity_points == 80
    assert p2.popularity_points == 20


def test_like_profile(engine):
    user1 = 7020
    user2 = 7021
    engine.register_user(user1, "Liker")
    engine.register_user(user2, "Liked")

    success, msg, data = engine.like_profile(user1, user2)
    assert success is True
    assert "liked" in msg.lower()
    p1 = engine.get_profile(user1)
    p2 = engine.get_profile(user2)
    assert p2.profile_likes == 1
    assert user2 in p1.likes_given


def test_cannot_like_twice(engine):
    user1 = 7022
    user2 = 7023
    engine.register_user(user1, "Liker1")
    engine.register_user(user2, "Liked1")
    engine.like_profile(user1, user2)
    success, msg, _ = engine.like_profile(user1, user2)
    assert success is False
    assert "already liked" in msg.lower()


def test_visit_profile(engine):
    user1 = 7030
    user2 = 7031
    engine.register_user(user1, "Visitor")
    engine.register_user(user2, "Visited")

    data = engine.visit_profile(user1, user2)
    assert data["profile_visitors"] == 1
    assert data["user_id"] == user2


def test_send_coins_to_user(engine):
    user1 = 7040
    user2 = 7041
    engine.register_user(user1, "Sender")
    engine.register_user(user2, "Receiver")
    p1 = engine.get_profile(user1)
    p1.coins = 500
    engine._save_user(p1)

    success, msg, data = engine.send_coins_to_user(user1, user2, 100)
    assert success is True
    assert "100" in msg
    p1 = engine.get_profile(user1)
    p2 = engine.get_profile(user2)
    assert p1.coins == 400
    assert p2.coins == 100


def test_update_privacy_settings(engine):
    user_id = 7050
    engine.register_user(user_id, "PrivacyUser")
    success, msg = engine.update_privacy_settings(user_id, {"show_wallet": False, "show_coins": True})
    assert success is True
    profile = engine.get_profile(user_id)
    assert profile.privacy_settings["show_wallet"] is False
    assert profile.privacy_settings["show_coins"] is True


def test_send_personal_message(engine):
    user1 = 7060
    user2 = 7061
    engine.register_user(user1, "Msger")
    engine.register_user(user2, "Receiver")

    success, msg = engine.send_personal_message(user1, user2, "Hello there!")
    assert success is True
    p2 = engine.get_profile(user2)
    assert p2.unread_messages == 1
    assert p2.unread_notifications >= 1


def test_dashboard_includes_popularity(client):
    response = client.get("/api/dashboard/7070")
    assert response.status_code == 200
    data = response.get_json()
    assert "popularity_points" in data
    assert "popularity_level" in data
    assert "profile_likes" in data
    assert "profile_visitors" in data
    assert "theme" in data
    assert "unread_messages" in data


def test_popularity_api_endpoints(client):
    client.post("/api/popularity/claim-daily/7080", method="POST")
    response = client.post("/api/popularity/buy-coins/7080", json={"amount": 5}, method="POST")
    assert response.status_code == 200

    response = client.post("/api/popularity/send/7080", json={"to_user_id": 7081, "amount": 10}, method="POST")
    assert response.status_code == 200


def test_like_and_visit_api_endpoints(client):
    response = client.post("/api/profile/like/7090", json={"target_id": 7091}, method="POST")
    assert response.status_code == 200

    response = client.post("/api/profile/visit/7090", json={"target_id": 7091}, method="POST")
    assert response.status_code == 200


def test_send_coins_api_endpoint(client):
    response = client.post("/api/coins/send/7100", json={"to_user_id": 7101, "amount": 50}, method="POST")
    assert response.status_code == 200


def test_privacy_and_theme_api_endpoints(client):
    response = client.post("/api/profile/privacy/7110", json={"settings": {"show_wallet": False}}, method="POST")
    assert response.status_code == 200

    response = client.post("/api/profile/theme/7110", json={"theme": "light"}, method="POST")
    assert response.status_code == 200
    data = response.get_json()
    assert data["theme"] == "light"


def test_personal_messaging_api_endpoint(client):
    response = client.post("/api/messages/send/7120", json={"to_user_id": 7121, "message": "Hi!"}, method="POST")
    assert response.status_code == 200
