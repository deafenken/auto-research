from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    env_id: str
    learning_rate: float
    total_steps: int


class ResearchExperiment:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def train(self) -> None:
        raise NotImplementedError("Implement the RL training loop here.")
