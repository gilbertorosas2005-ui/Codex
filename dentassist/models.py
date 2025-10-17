"""Core data models for DentAssist."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Any, Dict, List

ISO_FORMAT = "%Y-%m-%dT%H:%M"


@dataclass
class Appointment:
    """Represents a scheduled patient visit."""

    patient: str
    start: datetime
    duration_minutes: int
    procedure: str
    notes: str = ""
    status: str = "scheduled"

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["start"] = self.start.strftime(ISO_FORMAT)
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Appointment":
        start_str = payload.get("start")
        start = datetime.strptime(start_str, ISO_FORMAT)
        return cls(
            patient=payload["patient"],
            start=start,
            duration_minutes=payload["duration_minutes"],
            procedure=payload["procedure"],
            notes=payload.get("notes", ""),
            status=payload.get("status", "scheduled"),
        )

    def is_for_day(self, day: date) -> bool:
        return self.start.date() == day


@dataclass
class InventoryItem:
    """Tracks consumable stock for the practice."""

    name: str
    quantity: int
    reorder_threshold: int
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "InventoryItem":
        return cls(
            name=payload["name"],
            quantity=payload["quantity"],
            reorder_threshold=payload["reorder_threshold"],
            notes=payload.get("notes", ""),
        )

    @property
    def needs_restock(self) -> bool:
        return self.quantity <= self.reorder_threshold


@dataclass
class Task:
    """Represents an actionable reminder for the team."""

    description: str
    category: str = "general"
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Task":
        return cls(
            description=payload["description"],
            category=payload.get("category", "general"),
            completed=payload.get("completed", False),
        )


def appointments_from_state(raw: List[Dict[str, Any]]) -> List[Appointment]:
    return [Appointment.from_dict(item) for item in raw]


def inventory_from_state(raw: List[Dict[str, Any]]) -> List[InventoryItem]:
    return [InventoryItem.from_dict(item) for item in raw]


def tasks_from_state(raw: List[Dict[str, Any]]) -> List[Task]:
    return [Task.from_dict(item) for item in raw]
