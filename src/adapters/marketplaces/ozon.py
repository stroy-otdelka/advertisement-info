import asyncio
import logging
from typing import Any
import requests
from src.application.interfaces.api_client import AbstractOzonApiClient, AbstractApiClient

logger = logging.getLogger(__name__)


class OzonApiClient(AbstractOzonApiClient):
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
        tasks = [self.get_product(product_id, seller) for product_id in product_id]
        tasks_chunked = [tasks[i:i + 10] for i in range(0, len(tasks), 10)]
        for chunk in tasks_chunked:
            res = await asyncio.gather(*chunk)
            result.extend(res)
            await asyncio.sleep(1)
        return result

    async def get_product(self, vendor_code_wb: str, seller: str) -> dict:
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

    async def _get_adv_object_id(self, seller: str, campaign_id: int) -> str:
        """
        Возвращает ID рекламируемого объекта для конкретной кампании.
        """
        response = await self._api_client.get(
            f"https://api-performance.ozon.ru:443/api/client/campaign/{campaign_id}/objects",
            headers={"Authorization": f"Bearer {await self._get_token(seller)}"}
        )       
        if response and response.get("list"):
            return response["list"][0]["id"]
        return ""

    async def get_adv_info(self, seller: str, **kwargs: Any) -> dict[str, set] | None:
        """
        Возвращает все артикулы товаров, 
        которые в активных рекламных компаниях (Трафарет и продвижение в поиске)
        и айди рекламируемного объекта
        """
        if self._keys[seller].get("ozon") is None:
            return dict()
        
        sku_ads_campaigns = await self._get_all_adv(seller)
        result = {"sku": set(), "search": set(), "adv_id": ""}

        tasks = []
        api_interaction_limit = 5
        for index in range(0, len(sku_ads_campaigns), api_interaction_limit):
            batch = []
            for difference in range(min(len(sku_ads_campaigns) - index, api_interaction_limit)):
                batch += [self._get_detail_adv(seller, sku_ads_campaigns[index + difference]['id'])]
            tasks.append(batch)

        for task_group in tasks:
            batch_result = await asyncio.gather(*task_group)
            for campaign in batch_result:
                for product in campaign:
                    result["sku"].add(int(product['sku']))
            await asyncio.sleep(1)

        search_ads = await self._get_all_search_adv(seller)

        for search_ad in search_ads:
            result["search"].add(int(search_ad['sku']))

        if sku_ads_campaigns:
            result["adv_id"] = await self._get_adv_object_id(seller, sku_ads_campaigns[0]["id"])

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

