"""Discovery engine - Run the discovery loop.

Hypothesis generation -> simulation -> experiment -> verification -> ranking -> publication
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ncp.research.experiment import Experiment
from ncp.research.hypothesis import Hypothesis
from ncp.research.verification import VerificationEngine
from ncp.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DiscoveryEngine:
    """Runs the discovery loop."""

    verification: VerificationEngine
    hypotheses: List[Hypothesis] = field(default_factory=list)
    experiments: List[Experiment] = field(default_factory=list)

    def generate_hypothesis(self, observation: str,
                            context: Dict[str, Any] = None) -> Hypothesis:
        """Generate hypothesis from observation."""
        hyp = Hypothesis(
            statement=f"Hypothesis about: {observation}",
            confidence=0.5,
            evidence=[observation],
            metadata=context or {},
        )
        self.hypotheses.append(hyp)
        logger.info("Generated hypothesis: %s", hyp.id)
        return hyp

    def run_experiment(self, hypothesis: Hypothesis) -> Experiment:
        """Run experiment for a hypothesis."""
        exp = Experiment(
            name=f"exp_{hypothesis.id}",
            inputs={"hypothesis": hypothesis.statement},
            hypothesis_id=hypothesis.id,
            status="completed",
        )

        # Simulate experiment outcome
        exp.outputs = {"result": "success", "confidence": hypothesis.confidence}
        exp.metrics = {"accuracy": hypothesis.confidence, "cost": 1.0}

        self.experiments.append(exp)
        return exp

    def discover(self, context: Dict[str, Any]) -> List[Hypothesis]:
        """Run full discovery loop."""
        discoveries = []

        for hyp in self.hypotheses:
            if hyp.status == "pending":
                # Run experiment
                self.run_experiment(hyp)

                # Verify
                if self.verification.verify(hyp):
                    hyp.status = "verified"
                    discoveries.append(hyp)
                else:
                    hyp.status = "rejected"

        return discoveries
