import torch
from ..utils import concater


class StateVariable(torch.Tensor):
    """
    Implements a custom state variable for easier usage when performing indexing in functions, while still retaining
    compatibility with pytorch functionality.
    """

    def __new__(cls, data):
        out = torch.Tensor._make_subclass(cls, data)
        out.requires_grad = data.requires_grad
        return out

    def __getitem__(self, item):
        return self.data[..., item]

    def __setitem__(self, key, value):
        self.data[..., key] = value


def tensor_caster(func):
    """
    Function for helping out when it comes to multivariate models. Returns a torch.Tensor
    :param func: The function to pass
    :type func: callable
    :rtype: torch.Tensor
    """

    def wrapper(obj, x):
        if obj._inputdim > 1:
            x = StateVariable(x)

        return concater(func(obj, x))

    return wrapper