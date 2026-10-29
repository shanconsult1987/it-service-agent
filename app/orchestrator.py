from app.agents import (
    TriageAgent,
    KnowledgeAgent,
    ResolutionAgent,
    PolicyAgent,
    HumanEscalationAgent
)

from app.state import update_state

from app.memory import append_memory


class ITServiceOrchestrator:

    def __init__(self):

        self.triage = TriageAgent()

        self.knowledge = (
            KnowledgeAgent()
        )

        self.resolution = (
            ResolutionAgent()
        )

        self.policy = PolicyAgent()

        self.escalation = (
            HumanEscalationAgent()
        )

    def process(
        self,
        incident_id,
        description
    ):

        update_state(
            incident_id=incident_id,
            status="Started"
        )

        # Agent 1
        triage_result = (
            self.triage.run(
                description
            )
        )

        # Agent 2
        knowledge_result = (
            self.knowledge.run(
                description,
                triage_result[
                    "category"
                ]
            )
        )

        # Agent 3
        resolution_result = (
            self.resolution.run(
                description,
                knowledge_result[
                    "evidence"
                ]
            )
        )

        # Agent 4
        policy_result = (
            self.policy.run(
                triage_result[
                    "priority"
                ],
                resolution_result[
                    "confidence"
                ]
            )
        )

        # Agent 5
        if policy_result[
            "decision"
        ] in [
            "ESCALATE",
            "HUMAN_APPROVAL"
        ]:

            escalation = (
                self.escalation.run(
                    "Policy requires "
                    "human involvement."
                )
            )

            return {
                "incident_id":
                    incident_id,

                "triage":
                    triage_result,

                "knowledge":
                    knowledge_result,

                "resolution":
                    resolution_result,

                "policy":
                    policy_result,

                "escalation":
                    escalation
            }

        update_state(
            status="Resolved",
            resolution=
                resolution_result[
                    "resolution"
                ],
            confidence=
                resolution_result[
                    "confidence"
                ],
            escalation_required=False,
            last_action=
                "Automated resolution"
        )

        append_memory(
            "Successful Resolutions",
            (
                f"- {incident_id}: "
                f"{resolution_result['resolution']}"
            )
        )

        return {
            "incident_id":
                incident_id,

            "triage":
                triage_result,

            "knowledge":
                knowledge_result,

            "resolution":
                resolution_result,

            "policy":
                policy_result,

            "status":
                "Resolved"
        }