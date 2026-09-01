"""Seeding logic for Allen + Clarke Knowledge Base."""

import json
from pathlib import Path
from typing import Any, Dict
from radar.db.database import DatabaseManager
from radar.models import ServiceLine, Client


def seed_database(db: DatabaseManager, force: bool = False) -> Dict[str, Any]:
    """Idempotently seeds Allen + Clarke service lines and NZ/AU client registry."""
    db.initialize()

    data_dir = Path(__file__).parent.parent / "data"
    service_lines_file = data_dir / "seed_service_lines.json"
    clients_file = data_dir / "seed_clients.json"

    sl_count = 0
    cl_count = 0

    if service_lines_file.exists():
        with open(service_lines_file, "r", encoding="utf-8") as f:
            service_lines_data = json.load(f)
            for item in service_lines_data:
                sl = ServiceLine(**item)
                db.save_service_line(sl)
                sl_count += 1

    if clients_file.exists():
        with open(clients_file, "r", encoding="utf-8") as f:
            clients_data = json.load(f)
            for item in clients_data:
                client = Client(**item)
                db.save_client(client)
                cl_count += 1

    return {
        "service_lines_seeded": sl_count,
        "clients_seeded": cl_count,
    }
