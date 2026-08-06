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
    assert engine.get_profile(user_id).wallet >= 0.05


def test_task_completion_and_leaderboard(tmp_path):
    storage_path = tmp_path / "bot3-test2.json"
    engine = BotEngine(storage_path=str(storage_path))
    user_id = 2001
    engine.register_user(user_id, "Sara")

    reply = engine.handle_command(user_id, "task")
    assert "Join Telegram" in reply

    completed = engine.complete_task(user_id, "join_channel")
    assert completed is True
    assert engine.get_profile(user_id).completed_tasks[0] == "join_channel"
    leaderboard = engine.get_leaderboard()
    assert leaderboard
