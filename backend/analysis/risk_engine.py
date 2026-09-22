"""
backend/analysis/risk_engine.py
─────────────────────────────────
Risk engine stub — implementation pending.
Scores and prioritises findings from multiple agents.
"""


class RiskEngine:
    """Aggregates agent findings and assigns overall risk scores."""

    def __init__(self, findings: list):
        self.findings = findings

    def score(self) -> dict:
        raise NotImplementedError("RiskEngine not yet implemented")

