# time_store.py: The Temporal Layer of UniversalMemory.
# This module emulates a time-series database using a simple, persistent JSON file.
# Its primary responsibilities are generating unique, timestamped node IDs and
# maintaining a chronological log of all recorded events (nodes).

import uuid
import json
import os
from datetime import datetime, timezone, timedelta
from logger import logger


class TimeStore:
    """
    Manages the chronological record of events and generates timestamped IDs.
    """

    def __init__(self, chronicle_path: str):
        self.chronicle_path = chronicle_path
        self._chronicle = self._load_chronicle()
        logger.info(
            "TimeStore",
            "TimeStore initialized.",
            {"path": self.chronicle_path, "records": len(self._chronicle)},
        )

    def _load_chronicle(self) -> dict:
        if not os.path.exists(self.chronicle_path):
            return {}
        try:
            with open(self.chronicle_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {datetime.fromisoformat(ts): event for ts, event in data.items()}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(
                "TimeStore",
                "Failed to load chronicle, a new one will be created.",
                {"error": str(e)},
            )
            return {}

    def save_chronicle(self):
        """Saves the current state of the chronicle to the JSON file."""
        try:
            with open(self.chronicle_path, "w", encoding="utf-8") as f:
                data_to_save = {
                    ts.isoformat(): event for ts, event in self._chronicle.items()
                }
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error("TimeStore", "Failed to save chronicle.", {"error": str(e)})

    def get_new_timestamped_id(self) -> (str, datetime):
        """Generates a new unique node ID and a UTC timestamp."""
        timestamp = datetime.now(timezone.utc)
        node_id = str(uuid.uuid4())
        return node_id, timestamp

    def record(
        self, node_id: str, timestamp: datetime, node_type: str, metadata: dict = None
    ):
        """Records a new event in the chronicle."""
        event_data = {"node_id": node_id, "type": node_type, "metadata": metadata or {}}
        self._chronicle[timestamp] = event_data

    def query_by_range(self, start_time: datetime, end_time: datetime) -> list[str]:
        """Queries for node IDs within a specific time range."""

        result_ids = []
        for ts, event in self._chronicle.items():
            if start_time <= ts <= end_time:
                result_ids.append(event["node_id"])

        return result_ids

    def query_by_relative_time(self, relative_str: str) -> list[str]:
        """Queries for node IDs using relative time expressions (e.g., 'last_hour')."""
        now = datetime.now(timezone.utc)
        if relative_str == "last_hour":
            start_time = now - timedelta(hours=1)
            return self.query_by_range(start_time, now)
        elif relative_str == "yesterday":
            end_of_yesterday = datetime(
                now.year, now.month, now.day, tzinfo=timezone.utc
            )
            start_of_yesterday = end_of_yesterday - timedelta(days=1)
            return self.query_by_range(start_of_yesterday, end_of_yesterday)

        return []
