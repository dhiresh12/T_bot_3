from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def migrate_json_to_sqlite(json_path: Path, db_path: Path):
    """
    Reads user data from a JSON file and migrates it to an SQLite database.
    This is a one-time script.
    """
    if not json_path.exists():
        print(f"Error: JSON file not found at '{json_path}'")
        return

    if db_path.exists():
        print(f"Warning: Database file already exists at '{db_path}'. Migration skipped.")
        return

    # Load data from JSON
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        users = data.get("users", [])
    except (json.JSONDecodeError, TypeError):
        print(f"Error: Could not read or parse JSON file at '{json_path}'")
        return

    # Connect to SQLite and create table
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table schema that matches the UserProfile dataclass
    # Complex types like lists and dicts will be stored as JSON strings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT,
        wallet_bot REAL, wallet_app REAL, coins INTEGER, popularity INTEGER,
        bonus_claimed BOOLEAN, completed_tasks TEXT, total_ads_watched INTEGER,
        invite_count INTEGER, invites_list TEXT, withdrawals TEXT,
        last_bonus_at TEXT, daily_ads_watch_count INTEGER, daily_spin_count INTEGER,
        last_spin_at TEXT, last_ad_watched_at TEXT, admin BOOLEAN, registered_at TEXT,
        tier TEXT, activity_log TEXT, last_activity_at TEXT,
        is_verified BOOLEAN, invited_by INTEGER
    )
    """)

    # Insert data
    for user in users:
        # FIX: Map the old 'wallet' key from JSON to the new 'wallet_bot' column
        # This ensures backward compatibility with your old bot_data.json structure.
        if 'wallet' in user and 'wallet_bot' not in user:
            user['wallet_bot'] = user.pop('wallet')
        
        # FIX: Map 'completed_ads' to 'total_ads_watched'
        if 'completed_ads' in user and 'total_ads_watched' not in user:
            user['total_ads_watched'] = user.pop('completed_ads')

        # FIX: Map 'invites' to 'invite_count'
        if 'invites' in user and 'invite_count' not in user:
            user['invite_count'] = user.pop('invites')

        # Convert list/dict fields to JSON strings for storage
        user['completed_tasks'] = json.dumps(user.get('completed_tasks', []))
        user['invites_list'] = json.dumps(user.get('invites_list', []))
        user['withdrawals'] = json.dumps(user.get('withdrawals', []))
        user['activity_log'] = json.dumps(user.get('activity_log', []))
        
        # Ensure all columns defined in the schema exist in the user dict, even if null
        # This prevents "no such column" errors if a user from an old JSON is missing a new field.
        all_columns = [desc[0] for desc in cursor.description]
        for col in all_columns:
            user.setdefault(col, None)

        columns = ', '.join(user.keys())
        placeholders = ', '.join('?' for _ in user)
        sql = f"INSERT INTO users ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(user.values()))

    conn.commit()
    conn.close()

    print(f"✅ Migration successful! {len(users)} users migrated to '{db_path}'.")
    print("Please update your BotEngine to use the new SQLite database.")


if __name__ == "__main__":
    migrate_json_to_sqlite(Path("bot_data.json"), Path("bot_data.db"))