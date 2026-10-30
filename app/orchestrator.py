
from app.agents import (
    TriageAgent,
    KnowledgeAgent,
    ResolutionAgent,
    PolicyAgent,
    HumanEscalationAgent
)
from app.state import update_state
from app.memory import append_memory
from app.guardrails import (
    validate_incident_description,
    validate_incident_id
)
from app.audit import write_audit_event


class ITServiceOrchestrator:

    def __init__(self):
        self.triage = TriageAgent()
        self.knowledge = KnowledgeAgent()
        self.resolution = ResolutionAgent()
        self.policy = PolicyAgent()
        self.escalation = HumanEscalationAgent()

    def process(
        self,
        incident_id,
        description,
        correlation_id="LOCAL-ORCHESTRATION"
    ):
        id_result = validate_incident_id(incident_id)

        if not id_result["allowed"]:
            write_audit_event(
                "guardrail_rejection",
                "rejected",
                correlation_id,
                reason_code=id_result["code"]
            )
            return {
                "status": "Rejected",
                "guardrail": id_result,
                "correlation_id": correlation_id
            }

        incident_id = id_result["incident_id"]

        input_result = validate_incident_description(description)

        if not input_result["allowed"]:
            write_audit_event(
                "guardrail_rejection",
                "rejected",
                correlation_id,
                incident_id=incident_id,
                reason_code=input_result["code"]
            )
            return {
                "incident_id": incident_id,
                "status": "Rejected",
                "guardrail": input_result,
                "correlation_id": correlation_id
            }

        description = input_result["description"]

        write_audit_event(
            "incident_processing",
            "started",
            correlation_id,
            incident_id=incident_id
        )

        update_state(
            incident_id=incident_id,
            status="Started"
        )

        # Agent 1: triage and classification.
        triage_result = self.triage.run(description)

        # Agent 2: retrieve approved knowledge.
        knowledge_result = self.knowledge.run(
            description,
            triage_result["category"]
        )

        # Agent 3: propose a resolution from the evidence.
        resolution_result = self.resolution.run(
            description,
            knowledge_result["evidence"]
        )

        # Agent 4: apply existing priority/confidence policy.
        policy_result = self.policy.run(
            triage_result["priority"],
            resolution_result["confidence"]
        )

        # Agent 5: escalate if policy requires human involvement.
        if policy_result["decision"] in (
            "ESCALATE",
            "HUMAN_APPROVAL"
        ):
            escalation = self.escalation.run(
                "Policy requires human involvement."
            )

            write_audit_event(
                "incident_escalation",
                "human_required",
                correlation_id,
                incident_id=incident_id,
                reason_code=policy_result["decision"]
            )

            return {
                "incident_id": incident_id,
                "correlation_id": correlation_id,
                "triage": triage_result,
                "knowledge": knowledge_result,
                "resolution": resolution_result,
                "policy": policy_result,
                "escalation": escalation
            }

        update_state(
            status="Resolved",
            resolution=resolution_result["resolution"],
            confidence=resolution_result["confidence"],
            escalation_required=False,
            last_action="Automated resolution"
        )

        append_memory(
            "Successful Resolutions",
            (
                f"- {incident_id}: "
                f"{resolution_result['resolution']}"
            )
        )

        write_audit_event(
            "incident_processing",
            "resolved",
            correlation_id,
            incident_id=incident_id
        )

        return {
            "incident_id": incident_id,
            "correlation_id": correlation_id,
            "triage": triage_result,
            "knowledge": knowledge_result,
            "resolution": resolution_result,
            "policy": policy_result,
            "status": "Resolved"
        }
