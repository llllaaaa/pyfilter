from abc import ABC
import torch
from ...logging import LoggingWrapper
from ..base import BaseAlgorithm, BaseFilterAlgorithm
from .state import BatchState


class OptimizationBatchAlgorithm(BaseAlgorithm, ABC):
    def __init__(self, max_iter: int):
        """
        Algorithm for batch inference.
        """
        super(OptimizationBatchAlgorithm, self).__init__()
        self._max_iter = int(max_iter)

    def is_converged(self, old_loss, new_loss):
        raise NotImplementedError()

    def _fit(self, y: torch.Tensor, logging_wrapper: LoggingWrapper, **kwargs) -> BatchState:
        self.initialize(y)

        old_loss = torch.tensor(float('inf'))
        loss = -old_loss
        it = 0

        try:
            logging_wrapper.set_num_iter(self._max_iter)
            while not self.is_converged(old_loss, loss) and it < self._max_iter:
                old_loss = loss
                loss = self._step(y)
                logging_wrapper.do_log(it, self, y)
                it += 1

        except Exception as e:
            logging_wrapper.close()
            raise e

        logging_wrapper.close()

        return BatchState(self.is_converged(old_loss, loss), loss, it)

    def _step(self, y) -> float:
        raise NotImplementedError()


class BatchFilterAlgorithm(BaseFilterAlgorithm, ABC):
    def __init__(self, filter_):
        """
        Implements a class of inference algorithms using filters for inference.
        """

        super().__init__(filter_)
