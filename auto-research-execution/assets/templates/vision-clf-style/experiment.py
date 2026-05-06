from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    model_name: str
    image_size: int
    learning_rate: float


class ResearchExperiment:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def train(self) -> None:
        raise NotImplementedError("Implement the vision training step here.")
