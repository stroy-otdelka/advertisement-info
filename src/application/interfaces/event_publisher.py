import abc
from src.application import events


class AbstractEventPublisher(abc.ABC):
    """
    Интерфейс работы с шиной событий для публикации событий
    """

    def registration(self, event: events.Event, topic: str, **kwargs) -> None:
        """
        Регистрация событий

        Параметры:
        - event : Событие
        - topic : Топик
        - kwargs: Атрибуты для фильтрации
        """
        id = self._registration(event, topic, **kwargs)
        return id

    @abc.abstractmethod
    def _registration(self, event: events.Event, topic: str, **kwargs) -> None:
        raise NotImplementedError


