from __future__ import annotations

from app.core import BotEngine


def main() -> None:
    engine = BotEngine(storage_path="bot_data.json")
    print("Xio PayPlus starter bot is ready.")
    print("Commands: bonus, wallet, tasks, ads, spin, profile, leaderboard, withdraw, exit")
    print("Type 'exit' to quit.")
    while True:
        command = input("> ").strip().lower()
        if command in {"exit", "quit"}:
            break
        if not command:
            continue
        if command.startswith("register"):
            _, user_id, name = command.split(maxsplit=2)
            print(engine.register_user(int(user_id), name))
            continue
        if command.startswith("user"):
            _, user_id = command.split(maxsplit=1)
            print(engine.handle_command(int(user_id), "profile"))
            continue
        print(engine.handle_command(1, command))


if __name__ == "__main__":
    main()
