"""Data insights with user consent."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class InsightsService:
    def __init__(self) -> None:
        self.consent_records: Dict[int, Dict[str, Any]] = {}
        self.insights: List[Dict[str, Any]] = []

    def set_consent(self, user_id: int, analytics: bool = False, personalization: bool = False, ads_personalization: bool = False) -> Dict[str, Any]:
        self.consent_records[user_id] = {
            "user_id": user_id,
            "analytics": analytics,
            "personalization": personalization,
            "ads_personalization": ads_personalization,
            "updated_at": self._utcnow().isoformat(),
        }
        return self.consent_records[user_id]

    def get_consent(self, user_id: int) -> Dict[str, Any]:
        return self.consent_records.get(user_id, {
            "user_id": user_id,
            "analytics": False,
            "personalization": False,
            "ads_personalization": False,
        })

    def record_event(self, user_id: int, event_name: str, properties: Optional[Dict[str, Any]] = None) -> None:
        consent = self.get_consent(user_id)
        if not consent.get("analytics"):
            return
        self.insights.append({
            "user_id": user_id,
            "event": event_name,
            "properties": properties or {},
            "timestamp": self._utcnow().isoformat(),
        })

    def get_aggregated_insights(self) -> Dict[str, Any]:
        from collections import Counter
        event_counts = Counter(i.get("event") for i in self.insights)
        return {
            "total_events": len(self.insights),
            "event_counts": dict(event_counts.most_common(20)),
            "users_tracked": len({i.get("user_id") for i in self.insights}),
        }

    def get_user_insights(self, user_id: int) -> List[Dict[str, Any]]:
        return [i for i in self.insights if i.get("user_id") == user_id][-50:]

    def _utcnow(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).replace(tzinfo=None)
