import asyncio
import logging
import random
from typing import Any

import aiohttp
from aiohttp import ClientTimeout, TCPConnector

from src.application.interfaces.api_client import AbstractApiClient

logger = logging.getLogger(__name__)


class APIClient(AbstractApiClient):
    """
    Реализация API Клиента
    """

    def __getstate__(self):
        return self.__dict__.copy()

    def __setstate__(self, state):
        self.__dict__.update(state)

    async def _make_request(
            self, method: str, url: str, **kwargs: dict[str, Any]
    ) -> dict[str, Any] | None | str | list:
        """
        :param method: Метод запроса
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """

        for _ in range(5):
            try:
                timeout = ClientTimeout(total=30)
                connector = TCPConnector(
                    limit=100,  # Максимальное количество одновременно открытых соединений
                    limit_per_host=10,  # Лимит соединений для одного хоста
                    ttl_dns_cache=300,  # Кэш DNS-запросов на 300 секунд
                    enable_cleanup_closed=True,  # Очистка закрытых соединений из пула
                )
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status >= 400:
                            logger.warning(f"status - {response.status}, url - {url}")
                        else:
                            logger.debug(f"status - {response.status}, url - {url}")
                        response.raise_for_status()
                        return await response.json()
            except Exception as e:
                logger.exception(f"Error occurred while making request, {e}")
                await asyncio.sleep(random.uniform(5, 20))

    async def get(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        return await self._make_request("GET", url, **kwargs)  # type: ignore

    async def patch(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        return await self._make_request("PATCH", url, **kwargs)  # type: ignore

    async def post(self, url: str, **kwargs: Any) -> dict | None:
        """
        :param url: Адрес Запроса
        :param kwargs: Параметры Запроса
        """
        return await self._make_request("POST", url, **kwargs)  # type: ignore
