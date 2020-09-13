import copy
from abc import ABC
from ..timeseries import StateSpaceModel
from tqdm import tqdm
import torch
from ..utils import choose
from ..module import Module
from .utils import enforce_tensor, FilterResult
from typing import Tuple, Union
from .state import BaseState


class BaseFilter(Module, ABC):
    def __init__(self, model: StateSpaceModel, save_means=True):
        """
        The basis for filters. Take as input a model and specific attributes.
        :param model: The model
        :param save_means: Whether to record the means, or to ignore
        """

        self._dummy = torch.tensor(0.)

        super().__init__()

        if not isinstance(model, StateSpaceModel):
            raise ValueError(f'`model` must be `{StateSpaceModel.__name__:s}`!')

        self._model = model
        self._n_parallel = None
        self._result = FilterResult()
        self._save_means = save_means

    @property
    def result(self) -> FilterResult:
        """
        Returns the filtering result object.
        """

        return self._result

    @property
    def ssm(self) -> StateSpaceModel:
        """
        Returns the SSM as an object.
        """
        return self._model

    @property
    def n_parallel(self) -> torch.Size:
        return self._n_parallel

    def viewify_params(self, shape: Union[int, torch.Size]):
        """
        Defines views to be used as parameters instead
        :param shape: The shape to use. Please note that
        :return: Self
        """

        self.ssm.viewify_params(shape)

        return self

    def set_nparallel(self, n: int):
        """
        Sets the number of parallel filters to use
        :param n: The number of parallel filters
        """

        raise NotImplementedError()

    def initialize(self) -> BaseState:
        """
        Initializes the filter.
        :return: Self
        """

        raise NotImplementedError()

    @enforce_tensor
    def filter(self, y: Union[float, torch.Tensor], state: BaseState) -> BaseState:
        """
        Performs a filtering the model for the observation `y`.
        :param y: The observation
        :param state: The previous state
        :return: Self and log-likelihood
        """

        state = self._filter(y, state)

        if self._save_means:
            self._result.append(state.get_mean(), state.get_loglikelihood())
        else:
            self._result.append(None, state.get_loglikelihood())

        return state

    def _filter(self, y: Union[float, torch.Tensor], state: BaseState) -> BaseState:
        raise NotImplementedError()

    def longfilter(self, y: Union[torch.Tensor, Tuple[torch.Tensor, ...]], bar=True) -> BaseState:
        """
        Filters the entire data set `y`.
        :param y: An array of data. Should be {# observations, # dimensions (minimum of 1)}
        :param bar: Whether to print a progressbar
        :return: Self
        """

        astuple = tuple(y) if not isinstance(y, tuple) else y
        iterator = tqdm(astuple, desc=str(self.__class__.__name__)) if bar else astuple

        state = self.initialize()
        for yt in iterator:
            state = self.filter(yt, state)

        return state

    def copy(self):
        """
        Returns a copy of itself.
        :return: Copy of self
        """

        res = copy.deepcopy(self)
        res.viewify_params(torch.Size([]))
        return res

    def predict(self, state: BaseState, steps: int, *args, **kwargs) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predicts `steps` ahead using the latest available information.
        :param state: The state to go from
        :param steps: The number of steps forward to predict
        :param kwargs: Any key worded arguments
        """

        raise NotImplementedError()

    def resample(self, inds: torch.Tensor, entire_history: bool = False):
        """
        Resamples the filter, used in cases where we use nested filters.
        :param inds: The indices
        :param entire_history: Whether to resample entire history
        :return: Self
        """
        if entire_history:
            self._result.resample(inds)

        self.ssm.p_apply(lambda u: choose(u.values, inds))

        return self

    def reset(self):
        """
        Resets the filter by nullifying the filter specific attributes.
        :return: Self
        """

        self._result = FilterResult()

        return self

    def exchange(self, filter_, inds: torch.Tensor):
        """
        Exchanges the filters.
        :param filter_: The new filter
        :type filter_: BaseFilter
        :param inds: The indices
        :return: Self
        """

        self._model.exchange(inds, filter_.ssm)
        self._result.exchange(filter_._result, inds)

        return self

    def populate_state_dict(self):
        return {
            "_model": self.ssm.state_dict(),
            "_n_parallel": self._n_parallel,
            "_result": self.result
        }


class BaseKalmanFilter(BaseFilter, ABC):
    def set_nparallel(self, n):
        self._n_parallel = torch.Size([n])

        return self