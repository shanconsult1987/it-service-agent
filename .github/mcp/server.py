from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "Contoso IT Service Tools"
)


MISSIONS = {
    "INC1001": {
        "status": "Investigating",
        "owner": "Network Team"
    },
    "INC1002": {
        "status": "Resolved",
        "owner": "Endpoint Team"
    },
    "INC1003": {
        "status": "Escalated",
        "owner": "Service Desk"
    }
}


@mcp.tool()
def get_mission_status(
    incident_id: str
) -> dict:
    """
    Return the current status
    and owner of an IT incident.
    """

    mission = MISSIONS.get(
        incident_id
    )

    if not mission:

        return {
            "incident_id":
                incident_id,
            "status":
                "Unknown",
            "owner":
                "Unassigned"
        }

    return {
        "incident_id":
            incident_id,
        **mission
    }


@mcp.tool()
def list_active_missions() -> list:
    """
    Return currently tracked incidents.
    """

    return [
        {
            "incident_id":
                incident_id,
            **details
        }
        for incident_id, details
        in MISSIONS.items()
    ]


if __name__ == "__main__":

    mcp.run(
        transport="stdio"
    )