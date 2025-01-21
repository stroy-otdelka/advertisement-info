from src.adapters.marketplaces.ozon import OzonApiClient
from src.application.events import FoundZeroStockEvent
from itertools import chain
from src.adapters.api_client import APIClient
from src.config import CONFIG
from src.utils.event_publisher import EventPublisher
import logging

class OzonAdvInfoUseCase:
    async def get_adv_info_ozon():
        ozon = OzonApiClient(api_keys=CONFIG.API_KEYS, request=APIClient())
        publisher = EventPublisher(project_id=CONFIG.PROJECT_ID)

        amo_action_skus = await ozon.get_adv_info("amodecor")
        amo_products = await ozon.get_products("amodecor")
        amo = [*amo_action_skus["sku"], *amo_action_skus["search"]]

        so_action_skus = await ozon.get_adv_info("stroy_otdelka")
        so_products = await ozon.get_products("stroy_otdelka")
        so = [*so_action_skus["sku"], *so_action_skus["search"]]

        orion_action_skus = await ozon.get_adv_info("orion")
        orion_products = await ozon.get_products("orion")
        orion = [*orion_action_skus["sku"], *orion_action_skus["search"]]

        zero_stock_skus = [
            product["sku"]
            for product in chain(amo_products, so_products, orion_products)
            if product["stocks"]["present"] == 0
        ]

        for sku in zero_stock_skus:
            event = None
            if sku in amo:
                event = FoundZeroStockEvent(sku=sku, legal_entity='Амодекор', adv_id=...)
                print(sku, "Амодекор")
            elif sku in so:
                event = FoundZeroStockEvent(sku=sku, legal_entity='СтройОтделка', adv_id=...)
                print(sku, "СтройОтделка")
            elif sku in orion:
                event = FoundZeroStockEvent(sku=sku, legal_entity='Орион', adv_id=...)
                print(sku, "Орион")

            if event:
                try:
                    publisher.registration(
                        event=event,
                        topic=...
                    )
                except Exception as e:
                    logging.exception(f"Failed to publish event for sku {sku}: {e}")

    # TODO: перенести ключи и токены в .енв
    # ---------------------------------------------- 
    # Пабсаб менеджер вытащить из stock-service
    # Там же можно посмотреть как сделать на functions_framework код.