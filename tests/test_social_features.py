import pytest
from app.core import BotEngine
from app.mini_app import create_app


@pytest.fixture
def engine(tmp_path):
    storage = tmp_path / "bot3-social.json"
    return BotEngine(storage_path=str(storage))


@pytest.fixture
def client(engine):
    app = create_app(engine)
    client = app.test_client()
    engine._test_client = client
    return client


@pytest.fixture
def auth_headers(engine, client):
    def _auth(user_id):
        engine.register_user(user_id, "TestUser")
        r = client.post("/api/auth/login", json={"user_id": user_id, "name": "TestUser"})
        assert r.status_code == 200
        token = r.get_json()["token"]
        return {"X-User-Token": token}
    return _auth


def test_send_and_accept_friend_request(engine):
    user1 = 6001
    user2 = 6002
    engine.register_user(user1, "Alice")
    engine.register_user(user2, "Bob")

    success, msg = engine.send_friend_request(user1, user2)
    assert success is True
    assert "sent" in msg.lower()

    requests = engine.get_friend_requests(user2)
    assert len(requests) == 1
    assert requests[0]["from_user_id"] == user1

    success2, msg2 = engine.accept_friend_request(user2, requests[0]["request_id"])
    assert success2 is True
    assert "friends" in msg2.lower()

    friends = engine.get_friends(user1)
    assert len(friends) == 1
    assert friends[0]["user_id"] == user2


def test_reject_friend_request(engine):
    user1 = 6003
    user2 = 6004
    engine.register_user(user1, "Charlie")
    engine.register_user(user2, "Dana")

    engine.send_friend_request(user1, user2)
    requests = engine.get_friend_requests(user2)
    success, msg = engine.reject_friend_request(user2, requests[0]["request_id"])
    assert success is True
    assert len(engine.get_friend_requests(user2)) == 0


def test_cannot_send_duplicate_or_self_request(engine):
    user1 = 6005
    engine.register_user(user1, "Eve")

    success, msg = engine.send_friend_request(user1, user1)
    assert success is False

    user2 = 6006
    engine.register_user(user2, "Frank")
    engine.send_friend_request(user1, user2)
    success2, msg2 = engine.send_friend_request(user1, user2)
    assert success2 is False


def test_update_bio(engine):
    user_id = 6007
    engine.register_user(user_id, "BioUser")
    success, msg = engine.update_bio(user_id, "Hello, I love earning coins!")
    assert success is True
    profile = engine.get_profile(user_id)
    assert profile.bio == "Hello, I love earning coins!"


def test_public_profile_shows_only_coins_not_wallet(engine):
    user1 = 6008
    user2 = 6009
    engine.register_user(user1, "Viewer")
    engine.register_user(user2, "Target")
    profile = engine.get_profile(user2)
    profile.wallet_bot = 50.0
    profile.coins = 5000
    engine._save_user(profile)

    public = engine.get_public_profile(user1, user2)
    assert "wallet_bot" not in public
    assert public["coins"] == 5000
    assert public["is_friend"] is False
    assert public["bio"] == ""


def test_public_profile_shows_bio_to_friends(engine):
    user1 = 6010
    user2 = 6011
    engine.register_user(user1, "Friend1")
    engine.register_user(user2, "Friend2")
    engine.get_profile(user2).bio = "My secret bio"
    engine._save_user(engine.get_profile(user2))
    engine.get_profile(user1).friends = [user2]
    engine._save_user(engine.get_profile(user1))

    public = engine.get_public_profile(user1, user2)
    assert public["bio"] == "My secret bio"
    assert public["is_friend"] is True


def test_translation_system(engine):
    result = engine.translate_text("hello", "en", "hi")
    assert result["translated_text"] == "नमस्ते"
    assert result["from_lang"] == "en"
    assert result["to_lang"] == "hi"

    result2 = engine.translate_text("hello", "en", "fr")
    assert result2["translated_text"] == "bonjour"

    result3 = engine.translate_text("hello", "en", "en")
    assert result3["translated_text"] == "hello"


def test_translation_word_by_word(engine):
    result = engine.translate_text("hello friend", "en", "hi")
    assert "नमस्ते" in result["translated_text"]
    assert "दोस्त" in result["translated_text"]


def test_chat_message_endpoint(client):
    response = client.post("/api/chat/send/7001", json={"message": "Hello everyone!", "type": "text"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_translate_api_endpoint(client):
    response = client.post("/api/translate", json={"text": "hello", "from_lang": "en", "to_lang": "hi"})
    assert response.status_code == 200
    data = response.get_json()
    assert "translated_text" in data


def test_view_profile_api_endpoint(client):
    response = client.get("/api/profile/view/8001/8002")
    assert response.status_code == 200
    data = response.get_json()
    assert "user_id" in data
    assert "coins" in data
    assert "wallet_bot" not in data


def test_update_bio_api_endpoint(client):
    response = client.post("/api/profile/bio/8003", json={"bio": "My awesome bio"})
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def test_friend_request_api_endpoint(client):
    response = client.post("/api/friends/request/8010", json={"to_user_id": 8011})
    assert response.status_code == 200
    data = response.get_json()
    assert "success" in data


def test_friends_list_api_endpoint(client):
    response = client.get("/api/friends/list/8020")
    assert response.status_code == 200
    data = response.get_json()
    assert "friends" in data


def test_friend_requests_api_endpoint(client):
    response = client.get("/api/friends/requests/8030")
    assert response.status_code == 200
    data = response.get_json()
    assert "requests" in data
