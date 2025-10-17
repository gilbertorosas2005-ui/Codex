"""Business logic for the DentAssist command line tool."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, date
from typing import Dict, List, Optional

from .models import (
    Appointment,
    InventoryItem,
    Task,
    appointments_from_state,
    inventory_from_state,
    tasks_from_state,
)
from .storage import load_state, save_state


class DentAssist:
    """High-level manager for appointments, inventory, and tasks."""

    def __init__(self, storage_path=None) -> None:
        self._storage_path = storage_path
        self._state = load_state(storage_path)

    # --- appointments -------------------------------------------------
    def add_appointment(
        self,
        patient: str,
        start: datetime,
        duration_minutes: int,
        procedure: str,
        notes: str = "",
    ) -> Appointment:
        appointment = Appointment(
            patient=patient,
            start=start,
            duration_minutes=duration_minutes,
            procedure=procedure,
            notes=notes,
        )
        self._state.setdefault("appointments", []).append(appointment.to_dict())
        self._persist()
        return appointment

    def list_appointments(self, day: Optional[date] = None) -> List[Appointment]:
        appointments = appointments_from_state(self._state.get("appointments", []))
        if day is None:
            return sorted(appointments, key=lambda item: item.start)
        return sorted(
            [item for item in appointments if item.is_for_day(day)],
            key=lambda item: item.start,
        )

    def update_appointment_status(self, index: int, status: str) -> Appointment:
        appointments = self._state.get("appointments", [])
        appointment_data = appointments[index]
        appointment_data["status"] = status
        self._persist()
        return Appointment.from_dict(appointment_data)

    # --- inventory ----------------------------------------------------
    def upsert_inventory(
        self,
        name: str,
        quantity: int,
        reorder_threshold: int,
        notes: str = "",
    ) -> InventoryItem:
        inventory = self._state.setdefault("inventory", [])
        for existing in inventory:
            if existing["name"].lower() == name.lower():
                existing.update(
                    {
                        "name": name,
                        "quantity": quantity,
                        "reorder_threshold": reorder_threshold,
                        "notes": notes,
                    }
                )
                self._persist()
                return InventoryItem.from_dict(existing)

        new_item = InventoryItem(
            name=name,
            quantity=quantity,
            reorder_threshold=reorder_threshold,
            notes=notes,
        )
        inventory.append(new_item.to_dict())
        self._persist()
        return new_item

    def adjust_inventory(self, name: str, delta: int) -> InventoryItem:
        inventory = self._state.get("inventory", [])
        for existing in inventory:
            if existing["name"].lower() == name.lower():
                existing["quantity"] = max(0, existing["quantity"] + delta)
                self._persist()
                return InventoryItem.from_dict(existing)
        raise KeyError(f"No inventory item named '{name}'")

    def list_inventory(self) -> List[InventoryItem]:
        return inventory_from_state(self._state.get("inventory", []))

    # --- tasks --------------------------------------------------------
    def add_task(self, description: str, category: str = "general") -> Task:
        task = Task(description=description, category=category)
        self._state.setdefault("tasks", []).append(task.to_dict())
        self._persist()
        return task

    def complete_task(self, index: int) -> Task:
        task_data = self._state.get("tasks", [])[index]
        task_data["completed"] = True
        self._persist()
        return Task.from_dict(task_data)

    def list_tasks(self, include_completed: bool = False) -> List[Task]:
        tasks = tasks_from_state(self._state.get("tasks", []))
        if include_completed:
            return tasks
        return [task for task in tasks if not task.completed]

    # --- reporting ----------------------------------------------------
    def day_summary(self, day: Optional[date] = None) -> Dict[str, object]:
        """Return a digest of the most important information for a given day."""
        target_day = day or date.today()
        appointments = self.list_appointments(target_day)
        tasks = self.list_tasks(include_completed=False)
        inventory = self.list_inventory()
        low_stock = [item for item in inventory if item.needs_restock]

        agenda = []
        for appt in appointments:
            agenda.append(
                {
                    "time": appt.start.strftime("%H:%M"),
                    "patient": appt.patient,
                    "procedure": appt.procedure,
                    "status": appt.status,
                }
            )

        reminders = []
        categories = defaultdict(list)
        for task in tasks:
            categories[task.category].append(task.description)
        for category, items in categories.items():
            reminders.append({"category": category, "items": items})

        return {
            "date": target_day.isoformat(),
            "agenda": agenda,
            "reminders": reminders,
            "low_stock": [item.to_dict() for item in low_stock],
        }

    # --- persistence --------------------------------------------------
    def _persist(self) -> None:
        save_state(self._state, self._storage_path)
