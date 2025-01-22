from src.adapters.marketplaces.ozon import OzonApiClient
from src.application.events import FoundZeroStockEvent
from itertools import chain
from src.adapters.api_client import APIClient
from src.config import CONFIG
from src.utils.event_publisher import EventPublisher
import logging
import asyncio

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)  

class OzonAdvInfoUseCase:
    async def get_adv_info_ozon():
        try:
            ozon = OzonApiClient(api_keys=CONFIG.API_KEYS, request=APIClient())
            publisher = EventPublisher(project_id=CONFIG.PROJECT_ID)

            amo_action_skus = await ozon.get_adv_info("amodecor")
            await asyncio.sleep(2)
            amo_products = await ozon.get_products("amodecor")
            amo = [*amo_action_skus["sku"], *amo_action_skus["search"]]

            so_action_skus = await ozon.get_adv_info("stroy_otdelka")
            await asyncio.sleep(2)
            so_products = await ozon.get_products("stroy_otdelka")
            so = [*so_action_skus["sku"], *so_action_skus["search"]]

            orion_action_skus = await ozon.get_adv_info("orion")
            await asyncio.sleep(2)
            orion_products = await ozon.get_products("orion")
            orion = [*orion_action_skus["sku"], *orion_action_skus["search"]]

            zero_stock_skus = [
                product["sku"]
                for product in chain(amo_products, so_products, orion_products)
                if product["stocks"]["present"] == 0
            ]

            for sku in zero_stock_skus:
                if sku in amo:
                    event = FoundZeroStockEvent(sku=sku, legal_entity="Амодекор", adv_id=amo_action_skus["adv_id"])
                    logger.info(f"Товар {sku} из Амодекор.")
                elif sku in so:
                    event = FoundZeroStockEvent(sku=sku, legal_entity="СтройОтделка", adv_id=so_action_skus["adv_id"])
                    logger.info(f"Товар {sku} из СтройОтделка.")
                elif sku in orion:
                    event = FoundZeroStockEvent(sku=sku, legal_entity="Орион", adv_id=orion_action_skus["adv_id"])
                    logger.info(f"Товар {sku} из Орион.")

                if event:
                    try:
                        publisher.registration(
                            event=event,
                            topic="zero_stock_adv_ozon",
                        )
                        logger.info(f"Event for SKU {sku} is published.")
                    except Exception as e:
                        logger.exception(f"Error publishing for SKU {sku}: {e}")
        except Exception as e:
            logger.exception(f"Error in get_adv_info_ozon: {e}")
        finally:
            logger.info("Ending get_adv_info_ozon.")
