# DentAssist

DentAssist is a lightweight command line helper designed to make day-to-day life
in a dental practice a little easier. It keeps track of patient appointments,
inventory levels for consumables, and team reminders in a single streamlined
workflow.

## Features

* **Appointment board** – record upcoming visits with their procedures and
  statuses.
* **Inventory monitor** – log the quantity and reorder threshold for supplies to
  quickly spot items that need to be restocked.
* **Task list** – capture front desk or assistant follow-ups such as sterilizing
  equipment or preparing lab cases.
* **Daily summary** – generate a printable overview that combines the schedule,
  outstanding reminders, and low stock alerts.

All data is saved to a small JSON file (by default `~/.dentassist.json`) so it is
simple to sync or back up.

## Installation

DentAssist is a pure Python project. You can install the package in an existing
virtual environment or simply run it in-place:

```bash
pip install --user -e .
```

Alternatively, invoke the CLI module directly without installation:

```bash
python -m dentassist.cli --help
```

## Usage examples

Add an appointment and review the daily schedule:

```bash
python -m dentassist.cli add-appointment "Jamie Rivera" "2024-06-01 09:00" 45 "Hygiene recall" --notes "Prefers numbing gel"
python -m dentassist.cli add-appointment "Sam Patel" "2024-06-01 10:15" 60 "Crown prep"
python -m dentassist.cli list-appointments --day 2024-06-01
```

Track inventory and get alerted when supplies run low:

```bash
python -m dentassist.cli update-inventory "Composite A2" 15 10 --notes "Order from Shine Dental"
python -m dentassist.cli adjust-inventory "Composite A2" -12
python -m dentassist.cli list-inventory
```

Keep the team aligned with task lists and daily summaries:

```bash
python -m dentassist.cli add-task "Prepare sterilization bags" --category sterilization
python -m dentassist.cli add-task "Confirm lab case arrival" --category admin
python -m dentassist.cli summary --day 2024-06-01
```

## Development

Run the basic unit tests with:

```bash
python -m pytest
```

The tests rely on the built-in `tempfile` module so they do not modify your
actual data file.
