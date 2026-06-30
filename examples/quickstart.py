from __future__ import annotations

import os

from trashdb import (
    CreateContainerParams,
    TrashDB,
    TrashDBAPIError,
    TrashDBOptions,
)


def main() -> None:
    api_key = os.environ.get("TRASHDB_API_KEY")
    if not api_key:
        print("Please set TRASHDB_API_KEY environment variable")
        return

    db = TrashDB(TrashDBOptions(api_key=api_key))

    # List available engines
    engines = db.get_engines()
    print("Available engines:")
    for e in engines:
        print(f"  {e.id}: {e.name} (max TTL: {e.max_ttl_minutes} min)")

    # Create a PostgreSQL container
    params = CreateContainerParams(engine="postgres", ttl_minutes=5, name="my-app-db")
    try:
        container = db.create_container(params)
        print(f"\nCreated container {container.id}")
        print(f"  Engine:      {container.engine}")
        print(f"  Port:        {container.port}")
        print(f"  Connection:  {container.connection_string}")
        print(f"  TTL:         {container.ttl_minutes} min")
    except TrashDBAPIError as e:
        print(f"Error creating container: [{e.status}] code={e.code}: {e}")
        return

    # List running containers
    running = db.get_running_containers()
    print(f"\nRunning containers ({len(running)}):")
    for c in running:
        print(f"  {c.id}: {c.engine} on port {c.port}")

    # Fetch logs
    try:
        logs = db.get_container_logs(container.id)
        print(f"\nLogs for {container.id}:\n{logs[:500]}")
    except TrashDBAPIError as e:
        print(f"Could not fetch logs: {e}")

    # Destroy the container
    db.destroy_container(container.id)
    print(f"\nDestroyed container {container.id}")


if __name__ == "__main__":
    main()
