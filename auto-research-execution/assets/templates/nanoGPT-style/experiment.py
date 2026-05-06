from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    model_name: str
    learning_rate: float
    max_steps: int


class ResearchExperiment:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def train(self) -> None:
        raise NotImplementedError("Implement the method-specific LM training loop here.")
