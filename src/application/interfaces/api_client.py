from abc import abstractmethod, ABC
from typing import Any

class AbstractApiClient(ABC):
    @abstractmethod
    async def get(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError

    @abstractmethod
    async def post(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError

    @abstractmethod
    async def patch(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError


class AbstractOzonApiClient(ABC):

    @abstractmethod
    async def get_products(self, seller: str) -> list:
        raise NotImplementedError

    @abstractmethod
    async def _get_all_adv(self, seller: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError

    @abstractmethod
    async def _get_detail_adv(self, seller: str, campaign_id: int, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError

    @abstractmethod
    async def _get_all_search_adv(self, seller: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """

    @abstractmethod
    async def get_ozon_product(self, vendor_code_wb: str, seller: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def get_adv_info(self, seller: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        raise NotImplementedError

