"""Command line interface for DentAssist."""
from __future__ import annotations

import argparse
from datetime import datetime, date
from typing import List

from .assistant import DentAssist
from .models import Appointment, InventoryItem, Task

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DentAssist – a lightweight organizer for dental practices",
    )
    parser.add_argument(
        "--storage",
        help="Optional path to a custom storage file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # appointments
    appointment_parser = subparsers.add_parser("add-appointment", help="Add a patient visit")
    appointment_parser.add_argument("patient")
    appointment_parser.add_argument("start", help=f"Start time in '{DATETIME_FORMAT}' format")
    appointment_parser.add_argument("duration", type=int, help="Duration in minutes")
    appointment_parser.add_argument("procedure", help="Planned procedure")
    appointment_parser.add_argument("--notes", default="", help="Optional visit notes")

    list_appointments = subparsers.add_parser(
        "list-appointments", help="Show appointments sorted by time"
    )
    list_appointments.add_argument(
        "--day",
        help=f"Filter to a specific day in '{DATE_FORMAT}' format",
    )

    update_appointment = subparsers.add_parser("update-appointment", help="Update appointment status")
    update_appointment.add_argument("index", type=int, help="Index from list-appointments")
    update_appointment.add_argument("status", help="New status label, e.g. completed")

    # inventory
    inventory_parser = subparsers.add_parser("update-inventory", help="Add or update inventory items")
    inventory_parser.add_argument("name")
    inventory_parser.add_argument("quantity", type=int)
    inventory_parser.add_argument("threshold", type=int, help="Reorder threshold")
    inventory_parser.add_argument("--notes", default="", help="Optional notes about supplier, etc")

    inventory_adjust = subparsers.add_parser("adjust-inventory", help="Modify inventory quantity by a delta")
    inventory_adjust.add_argument("name")
    inventory_adjust.add_argument("delta", type=int, help="Positive to add stock, negative to subtract")

    subparsers.add_parser("list-inventory", help="Display the current inventory and restock alerts")

    # tasks
    task_parser = subparsers.add_parser("add-task", help="Record a team reminder")
    task_parser.add_argument("description")
    task_parser.add_argument("--category", default="general", help="Category such as sterilization")

    complete_task = subparsers.add_parser("complete-task", help="Mark a task as done")
    complete_task.add_argument("index", type=int)

    list_tasks = subparsers.add_parser("list-tasks", help="Show outstanding tasks")
    list_tasks.add_argument(
        "--all",
        action="store_true",
        help="Include completed tasks",
    )

    # summary
    summary = subparsers.add_parser("summary", help="Generate a snapshot of the day")
    summary.add_argument(
        "--day",
        help=f"Optional day in '{DATE_FORMAT}' format (defaults to today)",
    )

    return parser


def parse_day(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, DATE_FORMAT).date()


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_FORMAT)


def format_appointments(appointments: List[Appointment]) -> str:
    lines = []
    for idx, appointment in enumerate(appointments):
        lines.append(
            f"[{idx}] {appointment.start.strftime(DATETIME_FORMAT)} | {appointment.patient} | {appointment.procedure} | {appointment.status}"
        )
        if appointment.notes:
            lines.append(f"    Notes: {appointment.notes}")
    return "\n".join(lines) if lines else "No appointments recorded."


def format_inventory(items: List[InventoryItem]) -> str:
    lines = []
    for item in items:
        status = "⚠ restock" if item.needs_restock else "stock ok"
        base = f"- {item.name}: {item.quantity} units (threshold {item.reorder_threshold}) -> {status}"
        if item.notes:
            base += f"\n    Notes: {item.notes}"
        lines.append(base)
    return "\n".join(lines) if lines else "No inventory tracked yet."


def format_tasks(tasks: List[Task]) -> str:
    lines = []
    for idx, task in enumerate(tasks):
        status = "✓" if task.completed else "•"
        lines.append(f"[{idx}] {status} {task.description} ({task.category})")
    return "\n".join(lines) if lines else "No tasks available."


def render_summary(summary: dict) -> str:
    lines = [f"DentAssist summary for {summary['date']}"]
    lines.append("\nAgenda:")
    if summary["agenda"]:
        for item in summary["agenda"]:
            lines.append(
                f"  {item['time']} – {item['patient']} ({item['procedure']}) [{item['status']}]"
            )
    else:
        lines.append("  No appointments scheduled.")

    lines.append("\nReminders:")
    if summary["reminders"]:
        for bucket in summary["reminders"]:
            lines.append(f"  {bucket['category']}:")
            for task in bucket["items"]:
                lines.append(f"    - {task}")
    else:
        lines.append("  No outstanding tasks – nice work!")

    lines.append("\nLow stock:")
    if summary["low_stock"]:
        for item in summary["low_stock"]:
            lines.append(
                f"  {item['name']}: {item['quantity']} units remaining (threshold {item['reorder_threshold']})"
            )
            if item.get("notes"):
                lines.append(f"    Notes: {item['notes']}")
    else:
        lines.append("  All inventory above thresholds.")

    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    assistant = DentAssist(storage_path=args.storage)

    if args.command == "add-appointment":
        appointment = assistant.add_appointment(
            patient=args.patient,
            start=parse_datetime(args.start),
            duration_minutes=args.duration,
            procedure=args.procedure,
            notes=args.notes,
        )
        print("Added appointment:")
        print(format_appointments([appointment]))
        return 0

    if args.command == "list-appointments":
        appointments = assistant.list_appointments(parse_day(args.day))
        print(format_appointments(appointments))
        return 0

    if args.command == "update-appointment":
        appointment = assistant.update_appointment_status(args.index, args.status)
        print("Updated appointment:")
        print(format_appointments([appointment]))
        return 0

    if args.command == "update-inventory":
        item = assistant.upsert_inventory(
            name=args.name,
            quantity=args.quantity,
            reorder_threshold=args.threshold,
            notes=args.notes,
        )
        print("Inventory updated:")
        print(format_inventory([item]))
        return 0

    if args.command == "adjust-inventory":
        try:
            item = assistant.adjust_inventory(args.name, args.delta)
        except KeyError as exc:
            parser.error(str(exc))
        print("Inventory adjusted:")
        print(format_inventory([item]))
        return 0

    if args.command == "list-inventory":
        items = assistant.list_inventory()
        print(format_inventory(items))
        return 0

    if args.command == "add-task":
        task = assistant.add_task(args.description, category=args.category)
        print("Added task:")
        print(format_tasks([task]))
        return 0

    if args.command == "complete-task":
        task = assistant.complete_task(args.index)
        print("Completed task:")
        print(format_tasks([task]))
        return 0

    if args.command == "list-tasks":
        tasks = assistant.list_tasks(include_completed=args.all)
        print(format_tasks(tasks))
        return 0

    if args.command == "summary":
        summary_data = assistant.day_summary(parse_day(args.day))
        print(render_summary(summary_data))
        return 0

    parser.error("Unknown command")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
