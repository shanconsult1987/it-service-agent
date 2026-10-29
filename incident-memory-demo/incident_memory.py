
import os
import json
from datetime import datetime, timezone

from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential


DATABASE_NAME = "IncidentDB"
CONTAINER_NAME = "IncidentMemory"

ENDPOINT = os.environ.get("COSMOS_ENDPOINT")

if not ENDPOINT:
    raise RuntimeError(
        "Set COSMOS_ENDPOINT before running the application."
    )

credential = DefaultAzureCredential()
client = CosmosClient(ENDPOINT, credential=credential)

database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_incident():
    """Create or update the sample high-priority incident."""

    incident = {
        "id": "INC-1001",
        "customer": "Contoso Energy",
        "incidentType": "Production outage",
        "priority": "High",
        "status": "Investigating",
        "memory": [
            {
                "timestamp": utc_now(),
                "event": "Production API became unavailable",
                "action": "Incident reported"
            },
            {
                "timestamp": utc_now(),
                "event": "Restart attempted; issue persists",
                "action": "Restart backend service"
            }
        ],
        "nextAction": (
            "Investigate backend dependency failures"
        )
    }

    container.upsert_item(incident)
    print("Incident INC-1001 saved.")


def get_incident(incident_id):
    """Retrieve persistent incident memory."""

    query = """
        SELECT * FROM c
        WHERE c.id = @incident_id
    """

    results = list(
        container.query_items(
            query=query,
            parameters=[
                {
                    "name": "@incident_id",
                    "value": incident_id
                }
            ],
            enable_cross_partition_query=True
        )
    )

    return results[0] if results else None


def add_memory(incident_id, event, action):
    """Append a new event to an existing incident."""

    incident = get_incident(incident_id)

    if not incident:
        print(f"Incident {incident_id} not found.")
        return

    incident.setdefault("memory", []).append({
        "timestamp": utc_now(),
        "event": event,
        "action": action
    })

    # Keep priority unchanged; update the next action.
    incident["nextAction"] = action

    container.upsert_item(incident)
    print(f"Memory updated for {incident_id}.")


def show_incident(incident_id):
    """Display incident details and its history."""

    incident = get_incident(incident_id)

    if not incident:
        print("Incident not found.")
        return

    print("\n--- INCIDENT DETAILS ---")
    print(f"ID: {incident['id']}")
    print(f"Customer: {incident['customer']}")
    print(f"Priority: {incident['priority']}")
    print(f"Status: {incident['status']}")
    print(f"Next action: {incident['nextAction']}")

    print("\n--- PERSISTENT MEMORY ---")

    for entry in incident.get("memory", []):
        print(f"\nTime: {entry['timestamp']}")
        print(f"Event: {entry['event']}")
        print(f"Action: {entry['action']}")


def main():
    while True:
        print("\n=== Incident Memory Demo ===")
        print("1. Create/reset sample incident")
        print("2. View incident and memory")
        print("3. Record a new incident event")
        print("4. Exit")

        choice = input("Select an option: ").strip()

        if choice == "1":
            create_incident()

        elif choice == "2":
            show_incident("INC-1001")

        elif choice == "3":
            event = input("What happened? ").strip()
            action = input("Action or next step: ").strip()

            if event and action:
                add_memory("INC-1001", event, action)
            else:
                print("Event and action are required.")

        elif choice == "4":
            break

        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
