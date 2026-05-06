from dataclasses import dataclass


@dataclass
class ExperimentConfig:
    model_name: str
    dataset_name: str


class ResearchExperiment:
    def __init__(self, config: ExperimentConfig) -> None:
        self.config = config

    def evaluate(self) -> None:
        raise NotImplementedError("Implement the evaluation-only pipeline here.")
