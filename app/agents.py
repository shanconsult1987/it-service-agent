from app.agent import (
    classify_incident,
    load_knowledge
)

from app.state import update_state

from app.memory import append_memory


class TriageAgent:

    name = "TriageAgent"

    def run(self, description):

        result = classify_incident(
            description
        )

        update_state(
            category=result["category"],
            priority=result["priority"],
            assigned_agent=result["agent"],
            status="Triaged"
        )

        return {
            "agent": self.name,
            "category":
                result["category"],
            "priority":
                result["priority"],
            "assigned_agent":
                result["agent"]
        }


class KnowledgeAgent:

    name = "KnowledgeAgent"

    def run(
        self,
        description,
        category
    ):

        knowledge = load_knowledge()

        matches = []

        for section in knowledge.split(
            "\n## "
        ):

            if category.lower() in (
                section.lower()
            ):

                matches.append(
                    section
                )

        evidence = (
            "\n## ".join(matches)
            if matches
            else
            "No approved knowledge was found."
        )

        return {
            "agent": self.name,
            "evidence": evidence
        }


class ResolutionAgent:

    name = "ResolutionAgent"

    def run(
        self,
        description,
        evidence
    ):

        if (
            not evidence
            or
            "No approved knowledge"
            in evidence
        ):

            return {
                "agent": self.name,
                "resolution":
                    "Escalate to a human.",
                "confidence":
                    0.2
            }

        return {
            "agent": self.name,
            "resolution":
                "Use the approved "
                "enterprise troubleshooting "
                "procedure.",
            "confidence":
                0.9
        }


class PolicyAgent:

    name = "PolicyAgent"

    def run(
        self,
        priority,
        confidence
    ):

        if confidence < 0.7:

            decision = "ESCALATE"

        elif priority == "High":

            decision = "HUMAN_APPROVAL"

        else:

            decision = "RESOLVE"

        return {
            "agent": self.name,
            "decision": decision
        }


class HumanEscalationAgent:

    name = "HumanEscalationAgent"

    def run(self, reason):

        update_state(
            status="Escalated",
            escalation_required=True,
            last_action="Human escalation"
        )

        append_memory(
            "Escalations",
            f"- {reason}"
        )

        return {
            "agent": self.name,
            "status": "Escalated",
            "reason": reason
        }