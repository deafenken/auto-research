from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    model_name: str
    dataset_name: str
    learning_rate: float


class ResearchExperiment:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def build_trainer(self) -> None:
        raise NotImplementedError("Wire HuggingFace Trainer or TRL objects here.")
