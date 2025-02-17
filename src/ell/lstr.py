"""
LM string that supports logits and keeps track of it's _origin_trace even after mutation.
"""

import numpy as np
from typing import (
    Optional,
    Set,
    SupportsIndex,
    Union,
    FrozenSet,
    Iterable,
    List,
    Tuple,
    Any,
    Callable,
)
from typing_extensions import override


class lstr(str):
    """
    A string class that supports logits and keeps track of its _origin_trace even after mutation.
    This class is designed to be used in prompt engineering libraries where it is essential to associate
    logits with generated text and track the origin of the text.

    The `lstr` class inherits from the built-in `str` class and adds two additional attributes: `logits` and `_origin_trace`.
    The `logits` attribute is an optional NumPy array that represents the logits associated with the string.
    The `_origin_trace` attribute is a frozen set of strings that represents the _origin_trace(s) of the string.

    The class provides various methods for manipulating the string, such as concatenation, slicing, splitting, and joining.
    These methods ensure that the logits and _origin_trace(s) are updated correctly based on the operation performed.

    The `lstr` class is particularly useful in LLM libraries for tracing the flow of prompts through various language model calls.
    By tracking the _origin_trace of each string, it is possible to visualize how outputs from one language model program influence
    the inputs of another, allowing for a detailed analysis of interactions between different large language models. This capability
    is crucial for understanding the propagation of prompts in complex LLM workflows and for building visual graphs that depict these interactions.

    It is important to note that any modification to the string (such as concatenation or replacement) will invalidate the associated logits.
    This is because the logits are specifically tied to the original string content, and any change would require a new computation of logits.
    The logic behind this is detailed elsewhere in this file.

    Example usage:
    ```
    # Create an lstr instance with logits and an _origin_trace
    logits = np.array([1.0, 2.0, 3.0])
    _origin_trace = "4e9b7ec9"
    lstr_instance = lstr("Hello", logits, _origin_trace)

    # Concatenate two lstr instances
    lstr_instance2 = lstr("World", None, "7f4d2c3a")
    concatenated_lstr = lstr_instance + lstr_instance2

    # Get the logits and _origin_trace of the concatenated lstr
    print(concatenated_lstr.logits)  # Output: None
    print(concatenated_lstr._origin_trace)  # Output: frozenset({'4e9b7ec9', '7f4d2c3a'})

    # Split the concatenated lstr into two parts
    parts = concatenated_lstr.split()
    print(parts)  # Output: [lstr('Hello', None, frozenset({'4e9b7ec9', '7f4d2c3a'})), lstr('World', None, frozenset({'4e9b7ec9', '7f4d2c3a'}))]
    ```
    Attributes:
        logits (Optional[np.ndarray]): The logits associated with the string.
        _origin_trace (FrozenSet[str]): A frozen set of strings representing the _origin_trace(s) of the string.

    Methods:
        __new__: Create a new instance of lstr.
        __repr__: Return a string representation of the lstr instance.
        __add__: Concatenate this lstr instance with another string or lstr instance.
        __mod__: Perform a modulo operation between this lstr instance and another string, lstr, or a tuple of strings and lstrs.
        __mul__: Perform a multiplication operation between this lstr instance and an integer or another lstr.
        __rmul__: Perform a right multiplication operation between an integer or another lstr and this lstr instance.
        __getitem__: Get a slice or index of this lstr instance.
        __getattr__: Get an attribute from this lstr instance.
        join: Join a sequence of strings or lstr instances into a single lstr instance.
        split: Split this lstr instance into a list of lstr instances based on a separator.
        rsplit: Split this lstr instance into a list of lstr instances based on a separator, starting from the right.
        splitlines: Split this lstr instance into a list of lstr instances based on line breaks.
        partition: Partition this lstr instance into three lstr instances based on a separator.
        rpartition: Partition this lstr instance into three lstr instances based on a separator, starting from the right.
    """

    def __new__(
        cls,
        content: str,
        logits: Optional[np.ndarray] = None,
        _origin_trace: Optional[Union[str, FrozenSet[str]]] = None,
    ):
        """
        Create a new instance of lstr. The `logits` should be a numpy array and `_origin_trace` should be a frozen set of strings or a single string.

        Args:
        content (str): The string content of the lstr.
        logits (np.ndarray, optional): The logits associated with this string. Defaults to None.
        _origin_trace (Union[str, FrozenSet[str]], optional): The _origin_trace(s) of this string. Defaults to None.
        """
        instance = super(lstr, cls).__new__(cls, content)
        instance._logits = logits
        if isinstance(_origin_trace, str):
            instance.__origin_trace = frozenset({_origin_trace})
        else:
            instance.__origin_trace = (
                frozenset(_origin_trace) if _origin_trace is not None else frozenset()
            )
        return instance

    _logits: Optional[np.ndarray]
    __origin_trace: FrozenSet[str]

    @property
    def logits(self) -> Optional[np.ndarray]:
        """
        Get the logits associated with this lstr instance.

        Returns:
            Optional[np.ndarray]: The logits associated with this lstr instance, or None if no logits are available.
        """
        return self._logits

    @property
    def _origin_trace(self) -> FrozenSet[str]:
        """
        Get the _origin_trace(s) of this lstr instance.

        Returns:
            FrozenSet[str]: A frozen set of strings representing the _origin_trace(s) of this lstr instance.
        """
        return self.__origin_trace

    ########################
    ## Overriding methods ##
    ########################
    def __repr__(self) -> str:
        """
        Return a string representation of this lstr instance.

        Returns:
            str: A string representation of this lstr instance, including its content, logits, and _origin_trace(s).
        """
        return super().__repr__()

    def __add__(self, other: Union[str, "lstr"]) -> "lstr":
        """
        Concatenate this lstr instance with another string or lstr instance.

        Args:
            other (Union[str, "lstr"]): The string or lstr instance to concatenate with this instance.

        Returns:
            lstr: A new lstr instance containing the concatenated content, with the _origin_trace(s) updated accordingly.
        """
        if type(other) is str:
            new_content = super(lstr, self).__add__(other)
            return lstr(new_content, None, self.__origin_trace)
        elif isinstance(other, lstr):
            new_content = super(lstr, self).__add__(other)
            new__origin_trace = self.__origin_trace.union(other.__origin_trace)
            return lstr(new_content, None, new__origin_trace)
        return NotImplemented

    def __mod__(
        self, other: Union[str, "lstr", Tuple[Union[str, "lstr"], ...]]
    ) -> "lstr":
        """
        Perform a modulo operation between this lstr instance and another string, lstr, or a tuple of strings and lstrs,
        tracing the operation by logging the operands and the result.

        Args:
            other (Union[str, "lstr", Tuple[Union[str, "lstr"], ...]]): The right operand in the modulo operation.

        Returns:
            lstr: A new lstr instance containing the result of the modulo operation, with the _origin_trace(s) updated accordingly.
        """
        # If 'other' is a tuple, we need to handle each element
        if isinstance(other, tuple):
            result_content = super(lstr, self).__mod__(tuple(str(o) for o in other))
            new__origin_traces = set(self.__origin_trace)
            for item in other:
                if isinstance(item, lstr):
                    new__origin_traces.update(item.__origin_trace)
            new__origin_trace = frozenset(new__origin_traces)
        else:
            result_content = super(lstr, self).__mod__(other)
            if isinstance(other, lstr):
                new__origin_trace = self.__origin_trace.union(other.__origin_trace)
            else:
                new__origin_trace = self.__origin_trace

        return lstr(result_content, None, new__origin_trace)

    def __mul__(self, other: SupportsIndex) -> "lstr":
        """
        Perform a multiplication operation between this lstr instance and an integer or another lstr,
        tracing the operation by logging the operands and the result.

        Args:
            other (Union[SupportsIndex, "lstr"]): The right operand in the multiplication operation.

        Returns:
            lstr: A new lstr instance containing the result of the multiplication operation, with the _origin_trace(s) updated accordingly.
        """
        if isinstance(other, SupportsIndex):
            result_content = super(lstr, self).__mul__(other)
            new__origin_trace = self.__origin_trace
        else:
            return NotImplemented

        return lstr(result_content, None, new__origin_trace)

    def __rmul__(self, other: SupportsIndex) -> "lstr":
        """
        Perform a right multiplication operation between an integer or another lstr and this lstr instance,
        tracing the operation by logging the operands and the result.

        Args:
            other (Union[SupportsIndex, "lstr"]): The left operand in the multiplication operation.

        Returns:
            lstr: A new lstr instance containing the result of the multiplication operation, with the _origin_trace(s) updated accordingly.
        """
        return self.__mul__(other)  # Multiplication is commutative in this context

    def __getitem__(self, key: Union[SupportsIndex, slice]) -> "lstr":
        """
        Get a slice or index of this lstr instance.

        Args:
            key (Union[SupportsIndex, slice]): The index or slice to retrieve.

        Returns:
            lstr: A new lstr instance containing the sliced or indexed content, with the _origin_trace(s) preserved.
        """
        result = super(lstr, self).__getitem__(key)
        # This is a matter of opinon. I believe that when you Index into a language model output, you or divorcing the lodges of the indexed result from their contacts which produce them. Therefore, it is only reasonable to directly index into the lodges without changing the original context, and so any mutation on the string should invalidate the logits.
        # try:
        #     logit_subset = self._logits[key] if self._logits else None
        # except:
        #   logit_subset = None
        logit_subset = None
        return lstr(result, logit_subset, self.__origin_trace)

    def __getattribute__(self, name: str) -> Union[Callable, Any]:
        """
        Get an attribute from this lstr instance.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            Union[Callable, Any]: The requested attribute, which may be a method or a value.
        """
        # Get the attribute from the superclass (str)
        # First, try to get the attribute from the current class instance

        # Get the attribute using the superclass method
        attr = super().__getattribute__(name)

        # Check if the attribute is a callable and not defined in lstr class itself

        if name == "__class__":
            return type(self)

        if callable(attr) and name not in lstr.__dict__:

            def wrapped(*args: Any, **kwargs: Any) -> Any:
                result = attr(*args, **kwargs)
                # If the result is a string, return an lstr instance
                if isinstance(result, str):
                    _origin_traces = self.__origin_trace
                    for arg in args:
                        if isinstance(arg, lstr):
                            _origin_traces = _origin_traces.union(arg.__origin_trace)
                    for key, value in kwargs.items():
                        if isinstance(value, lstr):
                            _origin_traces = _origin_traces.union(value.__origin_trace)
                    return lstr(result, None, _origin_traces)

                return result

            return wrapped

        return attr

    @override
    def join(self, iterable: Iterable[Union[str, "lstr"]]) -> "lstr":
        """
        Join a sequence of strings or lstr instances into a single lstr instance.

        Args:
            iterable (Iterable[Union[str, "lstr"]]): The sequence of strings or lstr instances to join.

        Returns:
            lstr: A new lstr instance containing the joined content, with the _origin_trace(s) updated accordingly.
        """
        parts = [str(item) for item in iterable]
        new_content = super(lstr, self).join(parts)
        new__origin_trace = self.__origin_trace
        for item in iterable:
            if isinstance(item, lstr):
                new__origin_trace = new__origin_trace.union(item.__origin_trace)
        return lstr(new_content, None, new__origin_trace)

    @override
    def split(
        self, sep: Optional[Union[str, "lstr"]] = None, maxsplit: SupportsIndex = -1
    ) -> List["lstr"]:
        """
        Split this lstr instance into a list of lstr instances based on a separator.

        Args:
            sep (Optional[Union[str, "lstr"]], optional): The separator to split on. Defaults to None.
            maxsplit (SupportsIndex, optional): The maximum number of splits to perform. Defaults to -1.

        Returns:
            List["lstr"]: A list of lstr instances containing the split content, with the _origin_trace(s) preserved.
        """
        return self._split_helper(super(lstr, self).split, sep, maxsplit)

    @override
    def rsplit(
        self, sep: Optional[Union[str, "lstr"]] = None, maxsplit: SupportsIndex = -1
    ) -> List["lstr"]:
        """
        Split this lstr instance into a list of lstr instances based on a separator, starting from the right.

        Args:
            sep (Optional[Union[str, "lstr"]], optional): The separator to split on. Defaults to None.
            maxsplit (SupportsIndex, optional): The maximum number of splits to perform. Defaults to -1.

        Returns:
            List["lstr"]: A list of lstr instances containing the split content, with the _origin_trace(s) preserved.
        """
        return self._split_helper(super(lstr, self).rsplit, sep, maxsplit)

    @override
    def splitlines(self, keepends: bool = False) -> List["lstr"]:
        """
        Split this lstr instance into a list of lstr instances based on line breaks.

        Args:
            keepends (bool, optional): Whether to include the line breaks in the resulting lstr instances. Defaults to False.

        Returns:
            List["lstr"]: A list of lstr instances containing the split content, with the _origin_trace(s) preserved.
        """
        return [
            lstr(p, None, self.__origin_trace)
            for p in super(lstr, self).splitlines(keepends=keepends)
        ]

    @override
    def partition(self, sep: Union[str, "lstr"]) -> Tuple["lstr", "lstr", "lstr"]:
        """
        Partition this lstr instance into three lstr instances based on a separator.

        Args:
            sep (Union[str, "lstr"]): The separator to partition on.

        Returns:
            Tuple["lstr", "lstr", "lstr"]: A tuple of three lstr instances containing the content before the separator, the separator itself, and the content after the separator, with the _origin_trace(s) updated accordingly.
        """
        return self._partition_helper(super(lstr, self).partition, sep)

    @override
    def rpartition(self, sep: Union[str, "lstr"]) -> Tuple["lstr", "lstr", "lstr"]:
        """
        Partition this lstr instance into three lstr instances based on a separator, starting from the right.

        Args:
            sep (Union[str, "lstr"]): The separator to partition on.

        Returns:
            Tuple["lstr", "lstr", "lstr"]: A tuple of three lstr instances containing the content before the separator, the separator itself, and the content after the separator, with the _origin_trace(s) updated accordingly.
        """
        return self._partition_helper(super(lstr, self).rpartition, sep)

    def _partition_helper(
        self, method, sep: Union[str, "lstr"]
    ) -> Tuple["lstr", "lstr", "lstr"]:
        """
        Helper method for partitioning this lstr instance based on a separator.

        Args:
            method (Callable): The partitioning method to use (either partition or rpartition).
            sep (Union[str, "lstr"]): The separator to partition on.

        Returns:
            Tuple["lstr", "lstr", "lstr"]: A tuple of three lstr instances containing the content before the separator, the separator itself, and the content after the separator, with the _origin_trace(s) updated accordingly.
        """
        part1, part2, part3 = method(sep)
        new__origin_trace = (
            self.__origin_trace | sep.__origin_trace
            if isinstance(sep, lstr)
            else self.__origin_trace
        )
        return (
            lstr(part1, None, new__origin_trace),
            lstr(part2, None, new__origin_trace),
            lstr(part3, None, new__origin_trace),
        )

    def _split_helper(
        self,
        method,
        sep: Optional[Union[str, "lstr"]] = None,
        maxsplit: SupportsIndex = -1,
    ) -> List["lstr"]:
        """
        Helper method for splitting this lstr instance based on a separator.

        Args:
            method (Callable): The splitting method to use (either split or rsplit).
            sep (Optional[Union[str, "lstr"]], optional): The separator to split on. Defaults to None.
            maxsplit (SupportsIndex, optional): The maximum number of splits to perform. Defaults to -1.

        Returns:
            List["lstr"]: A list of lstr instances containing the split content, with the _origin_trace(s) preserved.
        """
        _origin_traces = (
            self.__origin_trace | sep.__origin_trace
            if isinstance(sep, lstr)
            else self.__origin_trace
        )
        parts = method(sep, maxsplit)
        return [lstr(part, None, _origin_traces) for part in parts]
