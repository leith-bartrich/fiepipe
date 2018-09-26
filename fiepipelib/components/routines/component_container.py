import abc
import typing

CNT = typing.TypeVar('CNT')


class ComponentContainerRoutines(typing.Generic[CNT]):
    """
    A set of routines for managing the 'container' aspect of a container.
    This can be thought of as an adapter to allow any arbitrary 'container'
    to be controlled by its components for the purposes of laoding and commiting
    the contianer.

    Those that implement this set of routines should:

    get_container:  To allow a component routine to query its "_components" variable directly.

    commit:  To allow a component routine to commit this container to its data/storage.

    load:  To allow a component routine to load this container from its data/storage.

    Ideally, an implementor holds an ID or path to get and set the container, rather than the
    container itself, when instantiated.  Only when 'load' is called, should it actually load into
    memory and hold that instance.  When 'commit' is called, the version in memory should
    be commited to data/storage.  This is because the component routines are expecting to store
    themselves inside the 'container' that they acquired by calling 'get_container'
    """

    @abc.abstractmethod
    def get_container(self) -> CNT:
        """Generic method.  Gets the object that is the 'container' for components."""
        raise NotImplementedError()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def load(self):
        raise NotImplementedError