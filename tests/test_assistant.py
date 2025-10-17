from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from dentassist.assistant import DentAssist


class TempStorage:
    """Context manager that provides a temporary JSON file for tests."""

    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "data.json"

    def __enter__(self):
        return self.path

    def __exit__(self, exc_type, exc, tb):
        if self.path.exists():
            self.path.unlink()


def test_add_and_list_appointments(tmp_path):
    with TempStorage(tmp_path) as storage:
        app = DentAssist(storage_path=storage)
        app.add_appointment(
            patient="Jamie",
            start=datetime(2024, 6, 1, 9, 0),
            duration_minutes=45,
            procedure="Cleaning",
        )
        appointments = app.list_appointments(date(2024, 6, 1))
        assert len(appointments) == 1
        assert appointments[0].patient == "Jamie"
        assert appointments[0].procedure == "Cleaning"


def test_inventory_restock_alert(tmp_path):
    with TempStorage(tmp_path) as storage:
        app = DentAssist(storage_path=storage)
        item = app.upsert_inventory("Floss", quantity=5, reorder_threshold=10)
        assert item.needs_restock is True
        summary = app.day_summary(date(2024, 6, 1))
        assert summary["low_stock"]
        assert summary["low_stock"][0]["name"] == "Floss"


def test_tasks_summary_grouped_by_category(tmp_path):
    with TempStorage(tmp_path) as storage:
        app = DentAssist(storage_path=storage)
        app.add_task("Sterilize tools", category="sterilization")
        app.add_task("Confirm insurance", category="admin")
        summary = app.day_summary(date(2024, 6, 1))
        categories = {bucket["category"] for bucket in summary["reminders"]}
        assert {"sterilization", "admin"} == categories
