import asyncio
import logging
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
import requests
from src.application.interfaces.api_client import AbstractOzonApiClient, AbstractApiClient

logger = logging.getLogger(__name__)


class OzonApiClient(AbstractOzonApiClient):
    # TODO: удалить лишнее
    def __init__(self, request: AbstractApiClient, api_keys: dict):
        self._api_client = request
        self._keys = api_keys

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

    def _get_headers(self, seller):
        headers = requests.utils.default_headers()
        headers["Client-Id"] = self._keys[seller]["ozon"]["client_id"]
        headers["Api-Key"] = self._keys[seller]["ozon"]["api_key"]
        return headers

    async def get_products(self, seller: str) -> list:
        """
        Возвращает все активные продукты с озона
        docs: https://docs.ozon.ru/api/seller/#operation/ProductAPI_GetProductList
        docs: https://docs.ozon.ru/api/seller/#operation/ProductAPI_GetProductInfoV2
        """
        if self._keys[seller].get("ozon") is None:
            return []
        product_id = []
        result = []
        body = {"limit": 1000, "last_id": "", "filter": {"visibility": "VISIBLE"}}
        while True:
            res = await self._api_client.post(
                url="https://api-seller.ozon.ru/v2/product/list",
                headers=self._get_headers(seller),
                json=body
            )
            if not res["result"]["items"]:
                break
            product_id.extend(product["offer_id"] for product in res["result"]["items"])
            body["last_id"] = res["result"]["last_id"]
            await asyncio.sleep(1)

        # Получение подробной инфы о продуктах
        tasks = [self.get_ozon_product(product_id, seller) for product_id in product_id]
        tasks_chunked = [tasks[i:i + 10] for i in range(0, len(tasks), 10)]
        for chunk in tasks_chunked:
            res = await asyncio.gather(*chunk)
            result.extend(res)
            await asyncio.sleep(1)
        return result

    async def get_sale_ozon(self, seller: str) -> dict:
        """Акции"""
        if self._keys[seller].get("ozon") is None:
            return dict()
        actions = await self._api_client.get(
            "https://api-seller.ozon.ru/v1/actions",
            headers=self._get_headers(seller)
        )
        result = {}

        if not actions:
            return {}

        actions = actions["result"]

        for action in actions:
            product_ids = set()
            offset = 0
            limit = 100

            while True:
                products_ozon: dict = await self._api_client.post(
                    url="https://api-seller.ozon.ru/v1/actions/products",
                    headers=self._get_headers(seller),
                    json={"action_id": action["id"], "limit": limit, "offset": offset}
                )

                if not products_ozon["result"]["products"]:
                    break

                for product in products_ozon["result"]["products"]:
                    product_ids.add(product["id"])

                offset += limit

            result[(action["id"], action["title"])] = product_ids

        return result

    async def get_sales_ozon(self, seller: str) -> list:
        """Продажи"""
        if self._keys[seller].get("ozon") is None:
            return []
        while True:
            body = {
                "date_from": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "date_to": datetime.now().strftime("%Y-%m-%d"),
                "metrics": ["ordered_units"],
                "dimension": ["sku", "month"],
                "filters": [],
                "sort": [{"key": "ordered_units", "order": "DESC"}],
                "limit": 1000,
                "offset": 0,
            }
            res = await self._api_client.post(
                url="https://api-seller.ozon.ru/v1/analytics/data",
                headers=self._get_headers(seller),
                json=body,
            )
            if not res:
                await asyncio.sleep(random.randint(10, 20))
                continue
            break

        return res.get("result", {}).get("data", [])

    async def get_ozon_product(self, vendor_code_wb: str, seller: str) -> dict:
        if self._keys[seller].get("ozon") is None:
            return dict()
        vendor_codes = [vendor_code_wb, vendor_code_wb.upper(), self.transliterate(vendor_code_wb)]
        for code in vendor_codes:
            body = {"offer_id": code}
            res = await self._api_client.post(
                url="https://api-seller.ozon.ru/v2/product/info", headers=self._get_headers(seller), json=body
            )

            if not res:
                continue
            return res["result"]

        return {}

    async def _get_token(self, seller: str) -> str:
        body = {
            "client_id": self._keys[seller]["ozon"]["client_adv_id"],
            "client_secret": self._keys[seller]["ozon"]["client_adv_secret"],
            "grant_type": "client_credentials"
        }
        actions = await self._api_client.post("https://api-performance.ozon.ru/api/client/token",
                                              json=body)
        return actions['access_token'] if actions else ''

    async def _get_all_adv(self, seller: str, **kwargs: Any) -> list | None:
        """
        Возвращает все рекламные кампании селлера

        Returns:
            set: Множество id рекламных компаний
        """
        actions = await self._api_client.get(
            "https://api-performance.ozon.ru:443/api/client/campaign",
            headers={"Authorization": f"Bearer {await self._get_token(seller)}"},
            params={
                "advObjectType": "SKU",
                "state": "CAMPAIGN_STATE_RUNNING",
            }
        )

        if not actions:
            return []

        return actions['list']

    async def _get_detail_adv(self, seller: str, campaign_id: int, **kwargs: Any) -> list | None:
        """
        Возвращает полные данные определённой рекламной кампании
        """
        result = []
        page = 0
        while True:
            actions = await self._api_client.get(
                f"https://api-performance.ozon.ru:443/api/client/campaign/{campaign_id}/v2/products",
                headers={"Authorization": f"Bearer {await self._get_token(seller)}"}
            )

            if not actions:
                return result

            actions = actions["products"]
            result.extend(actions)
            if len(actions) < 100:
                break
            page += 1

        return result

    async def _get_all_search_adv(self, seller: str, **kwargs: Any) -> list | None:
        """
        Возвращает данные все продвигаемые в поиске товары
        """
        result = []
        page = 0
        while True:
            actions = await self._api_client.post(
                f"https://api-performance.ozon.ru:443/api/client/campaign/search_promo/v2/products",
                headers={"Authorization": f"Bearer {await self._get_token(seller)}"},
                params={
                    "pageSize": 100,
                    "page": page,
                }
            )

            if not actions:
                return result

            result.extend(actions["products"])
            if int(actions['total']) < 100:
                break
            page += 1

        return result

    async def get_adv_info(self, seller: str, **kwargs: Any) -> dict[str, set] | None:
        """
        Возвращает все артикулы товаров, которые в активных рекламных компаниях (Трафарет и продвижение в поиске)
        """
        if self._keys[seller].get("ozon") is None:
            return dict()
        sku_ads_campaigns = await self._get_all_adv(seller)
        result = {"sku": set(), "search": set()}

        # Создание задач для выполнения запросов асинхронно по лимиту api
        tasks = []
        api_interaction_limit = 5
        for index in range(0, len(sku_ads_campaigns), api_interaction_limit):
            batch = []
            for difference in range(min(len(sku_ads_campaigns) - index, api_interaction_limit)):
                batch += [self._get_detail_adv(seller, sku_ads_campaigns[index + difference]['id'])]
            tasks.append(batch)

        # Выполнение задач через asyncio.gather()
        for task_group in tasks:
            batch_result = await asyncio.gather(*task_group)
            for campaign in batch_result:
                for product in campaign:
                    result["sku"].add(int(product['sku']))
            await asyncio.sleep(1)

        search_ads = await self._get_all_search_adv(seller)

        for search_ad in search_ads:
            result["search"].add(int(search_ad['sku']))

        return result

    async def _get_supplies_id_list(self, seller: str) -> list[int]:
        body = {
            "filter": {
                "states": [
                    "ORDER_STATE_DATA_FILLING",
                    "ORDER_STATE_DATA_FILLING",
                    "ORDER_STATE_READY_TO_SUPPLY",
                    "ORDER_STATE_ACCEPTED_AT_SUPPLY_WAREHOUSE",
                    "ORDER_STATE_IN_TRANSIT",
                    "ORDER_STATE_ACCEPTANCE_AT_STORAGE_WAREHOUSE"
                ]
            },
            "paging": {
                "from_supply_order_id": 0,
                "limit": 100
            }
        }
        while True:
            res = await self._api_client.post(
                url="https://api-seller.ozon.ru/v2/supply-order/list",
                json=body,
                headers=self._get_headers(seller)
            )
            if not res:
                return []
            if res.get("last_supply_order_id", 0) == 0:
                return res.get("supply_order_id", [])
            body["paging"]["from_supply_order_id"] = res["last_supply_order_id"]

    async def _get_bundle_id_for_supplies(
            self, seller: str,
            supply_order_id_list: list[int]
    ) -> set[str]:
        body = {
            "order_ids": []
        }
        result = set()
        # Разделение на порции по 50 элементов
        chunks = [supply_order_id_list[i:i + 50] for i in range(0, len(supply_order_id_list), 50)]

        for chunk in chunks:
            body["order_ids"] = chunk
            response = await self._api_client.post(
                url="https://api-seller.ozon.ru/v2/supply-order/get",
                json=body,
                headers=self._get_headers(seller)
            )
            if not response:
                continue

            for order in response["orders"]:
                for supply in order["supplies"]:
                    result.add(supply["bundle_id"])

        return result

    async def _get_sku_to_quantity_from_bundle(self, seller: str, bundle_ids: set[str]) -> dict[int, int]:
        body = {
            "bundle_ids": list(bundle_ids),
            "is_asc": True,
            "limit": 100,
            "sort_field": "UNSPECIFIED",
        }

        result = defaultdict(int)
        while True:
            res = await self._api_client.post(
                url="https://api-seller.ozon.ru/v1/supply-order/bundle",
                json=body,
                headers=self._get_headers(seller)
            )
            if not res:
                return result
            for item in res["items"]:
                result[item["sku"]] += item["quantity"]
            if not res["has_next"]:
                return result
            body["last_id"] = res["last_id"]

    async def get_sku_to_quantity(self, seller: str) -> dict[int, int]:
        """Получение словаря sku -> quantity"""
        if self._keys[seller].get("ozon") is None:
            return dict()
        supply_ids = await self._get_supplies_id_list(seller)
        bundle_ids = await self._get_bundle_id_for_supplies(seller, supply_ids)
        return await self._get_sku_to_quantity_from_bundle(seller, bundle_ids)

    @staticmethod
    def transliterate(text):
        # Словарь для транслитерации с учетом регистра
        translit_dict = {
            'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E', 'Ж': 'Zh',
            'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O',
            'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts',
            'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ы': 'Y', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh',
            'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
            'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya'
        }

        # Транслитерация с сохранением регистра
        transliterated_text = ''.join([translit_dict.get(char, char) for char in text])

        return transliterated_text

