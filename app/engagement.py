from __future__ import annotations

import random
from typing import Dict, List


class EngagementLayer:
    def __init__(self) -> None:
        self.trust_messages = [
            "Thousands of users are earning every day.",
            "Your reward is waiting after the next step.",
            "Small actions build your streak faster.",
        ]
        # Phase 4: Dark Pattern - Fake names for social proof
        self.fake_names = [
            "Aarav S.", "Rohan V.", "Priya K.", "Ananya M.", "Vikram R.", "Aditya B.",
            "John D.", "Maria S.", "Alex T.", "Fatima Z.", "Wei L.", "Kenji T."
        ]
        # Phase 4: Dark Pattern - Fake chat messages to create a sense of community
        self.fake_chat_messages = [
            "Wow, this bot is amazing!",
            "Just got my payment, thanks admin!",
            "How many invites do I need for the next level?",
            "The spin wheel is lucky today.",
            "Anyone completed the new task?",
            "Keep going everyone! 🔥",
            "This is the best earning bot for sure.",
        ]
        # Phase 4: Expanded tiers as per plan (Dark Pattern: makes users feel they are progressing)
        self.progress_tiers = [
            {"name": "Bronze", "min": 0, "emoji": "🥉"},
            {"name": "Silver", "min": 5000, "emoji": "🥈"},
            {"name": "Gold", "min": 25000, "emoji": "🥇"},
            {"name": "Platinum", "min": 100000, "emoji": "💎"},
            {"name": "Diamond", "min": 500000, "emoji": "💍"},
            {"name": "Crown", "min": 2000000, "emoji": "👑"},
            {"name": "Conqueror", "min": 10000000, "emoji": "🏆"},
        ]

    def build_trust_feed(self) -> List[str]:
        return self.trust_messages

    def generate_fake_withdrawal_feed(self) -> str:
        """Generates a single, realistic-looking fake withdrawal notification."""
        name = random.choice(self.fake_names)
        amount = random.randint(55, 160)
        # Mask the number to look real but be anonymous
        phone_part1 = random.randint(6, 9)
        phone_part2 = random.randint(1000, 9999)
        return f"🎉 Just now: {name} withdrew ₹{amount:.2f} (UPI: {phone_part1}*****{phone_part2})"

    def get_fake_chat_message(self) -> str:
        """Returns a random fake chat message to make the bot feel alive."""
        name = random.choice(self.fake_names)
        return f"💬 {name}: {random.choice(self.fake_chat_messages)}"

    def get_tier(self, coins: int) -> Dict[str, object]:
        for tier in reversed(self.progress_tiers):
            if coins >= tier["min"]:
                return {"name": f"{tier['emoji']} {tier['name']}", "min": tier["min"]}
        return {"name": "🥉 Bronze", "min": 0}

    def build_progress_snapshot(self, wallet: float, coins: int) -> Dict[str, object]:
        tier = self.get_tier(coins)
        return {
            "wallet": round(wallet, 2),
            "coins": coins,
            "tier": tier["name"],
            "next_tier": self._next_tier_name(coins) or "Max Level 🏆",
        }

    def _next_tier_name(self, coins: int) -> str:
        for tier in self.progress_tiers:
            if coins < tier["min"]:
                return f"{tier['emoji']} {tier['name']}"
        return ""
