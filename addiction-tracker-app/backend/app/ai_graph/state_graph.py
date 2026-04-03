from dataclasses import dataclass, field
from typing import Any

from app.config import settings


@dataclass
class AddictionState:
    craving_level: int
    substance_name: str
    city: str | None = None
    postal_code: str | None = None
    cbt_notes: str | None = None
    route: str | None = None
    response: dict[str, Any] = field(default_factory=dict)


class EvaluationNode:
    def run(self, state: AddictionState) -> AddictionState:
        if state.craving_level >= 8:
            state.route = "Alerte_Locale"
        elif state.craving_level >= 4:
            state.route = "Exercice_TCC"
        else:
            state.route = "Exercice_TCC"
        return state


class ExerciceTCCNode:
    def run(self, state: AddictionState) -> AddictionState:
        state.response = {
            "node": "Exercice_TCC",
            "severity": "moderate" if state.craving_level < 8 else "high",
            "exercise": {
                "name": "STOP + Restructuration cognitive courte",
                "steps": [
                    "Stopper l'automatisme pendant 60 secondes",
                    "Nommer l'envie sans jugement",
                    "Identifier la pensée associée",
                    "Formuler une alternative crédible",
                    "Choisir une action de remplacement pendant 10 minutes"
                ]
            },
            "notes_context": state.cbt_notes,
        }
        return state


class AlerteLocaleNode:
    def run(self, state: AddictionState) -> AddictionState:
        query = " ".join(part for part in [state.city, state.postal_code] if part)
        state.response = {
            "node": "Alerte_Locale",
            "severity": "critical",
            "message": "Craving critique détecté. Prioriser une aide locale et un contact de soutien immédiat.",
            "local_resource": {
                "type": "CSAPA",
                "search_hint": query.strip() or "rechercher le CSAPA le plus proche",
                "directory_url": settings.CSAPA_DIRECTORY_URL,
            },
        }
        return state


class AddictionSupportGraph:
    def __init__(self) -> None:
        self.evaluation = EvaluationNode()
        self.exercice_tcc = ExerciceTCCNode()
        self.alerte_locale = AlerteLocaleNode()

    def run(self, state: AddictionState) -> dict[str, Any]:
        state = self.evaluation.run(state)
        if state.route == "Alerte_Locale":
            state = self.alerte_locale.run(state)
        else:
            state = self.exercice_tcc.run(state)
        return {
            "route": state.route,
            "payload": state.response,
        }
