import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import BotEngine


def test_bonus_and_wallet_flow(tmp_path):
    storage_path = tmp_path / "bot3-test.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 1001
    engine.register_user(user_id, "Ali")

    reply = engine.handle_command(user_id, "bonus")
    assert "0.05" in reply
    assert engine.get_profile(user_id).wallet_bot >= 0.05


def test_task_completion_and_leaderboard(tmp_path):
    storage_path = tmp_path / "bot3-test2.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 2001
    engine.register_user(user_id, "Sara")

    reply = engine.handle_command(user_id, "task")
    assert "Join Telegram" in reply

    completed, completed_msg = engine.complete_task(user_id, "join_channel")
    assert completed is True
    assert engine.get_profile(user_id).completed_tasks[0] == "join_channel"
    # Completing a task grants coins. The leaderboard ranks by wallet_bot, so
    # sync wallet_bot from the earned coins to make the user appear on it.
    profile = engine.get_profile(user_id)
    profile.wallet_bot = round(profile.coins * engine.coins_to_rupee_rate, 4)
    engine._save_user(profile)
    leaderboard = engine.get_leaderboard()
    assert leaderboard


def test_wallet_command_persists_profile(tmp_path):
    """Bug #4: _handle_wallet must call _save_user so the synced wallet is persisted."""
    storage_path = tmp_path / "bot3-wallet-save.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 3001
    engine.register_user(user_id, "WalletUser")
    profile = engine.get_profile(user_id)
    profile.coins = 50000  # Worth ₹5 at default rate
    engine._save_user(profile)

    # Call the wallet command which syncs wallet_bot from coins
    engine.handle_command(user_id, "wallet")

    # Verify the synced wallet_bot was persisted to the backing store
    stored = engine.users_collection.find_one({"_id": user_id})
    assert stored is not None
    assert stored["wallet_bot"] == round(50000 * engine.coins_to_rupee_rate, 4)


def test_nav_ads_translation_keys_exist():
    """Bug #3: nav_ads key must exist in en and hi translation packs."""
    from app.support import SupportService

    support = SupportService()
    assert "nav_ads" in support.translations["en"]["ui"]
    assert "nav_ads" in support.translations["hi"]["ui"]
    assert support.translations["en"]["ui"]["nav_ads"] == "Ads"
    assert support.translations["hi"]["ui"]["nav_ads"] == "विज्ञापन"


def test_spin_wheel_returns_gift_dictionary(tmp_path):
    """The gift spin must return a gift dict (not a float) and bump the snap streak."""
    storage_path = tmp_path / "bot3-spin-gift.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 4001
    engine.register_user(user_id, "Spinner")

    success, message, gift = engine.spin_wheel(user_id)
    assert success is True
    assert isinstance(gift, dict), "gift should be a dict"
    assert "name" in gift and "coins" in gift
    # The selected gift must be a valid spin_gifts entry
    assert any(g["name"] == gift["name"] for g in engine.spin_gifts)
    # Coins must be credited if the gift pays out
    profile = engine.get_profile(user_id)
    if gift["coins"] > 0:
        assert profile.coins >= gift["coins"]
    # Snap-style streak bumps on every daily spin
    assert profile.snap_streak == 1


def test_spin_wheel_daily_limit(tmp_path):
    """Only one daily spin is allowed; the second call is blocked."""
    storage_path = tmp_path / "bot3-spin-limit.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 4002
    engine.register_user(user_id, "Spinner2")

    first_ok, _, _ = engine.spin_wheel(user_id)
    assert first_ok is True
    second_ok, message, _ = engine.spin_wheel(user_id)
    assert second_ok is False
    assert "daily spin" in message.lower()
