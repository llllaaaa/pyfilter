from ..state import AlgorithmState
from .varapprox import ParameterMeanField, StateMeanField
import torch


class BatchState(AlgorithmState):
    def __init__(self, converged: bool, final_loss: float, iterations: int):
        self.converged = converged
        self.final_loss = final_loss
        self.iterations = iterations


class VariationalState(BatchState):
    def __init__(self, converged: bool, final_loss: float, iterations: int, param_approx: ParameterMeanField,
                 state_approx: StateMeanField = None):
        super().__init__(converged, final_loss, iterations)
        self.param_approx = param_approx
        self.state_approx = state_approx


class PMMHState(AlgorithmState):
    def __init__(self, initial_sample: torch.Tensor):
        self.samples = [initial_sample]

    def update(self, sample: torch.Tensor):
        self.samples.append(sample)

