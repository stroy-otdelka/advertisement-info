from src.adapters.marketplaces.ozon import OzonApiClient
from src.application.events import FoundZeroStockEvent
from src.adapters.api_client import APIClient
from src.config import config as CONFIG
from src.utils.event_publisher import EventPublisher
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


class OzonAdvInfoUseCase:
    async def __call__(self):
        try:
            ozon = OzonApiClient(api_keys=CONFIG.API_KEYS, request=APIClient())
            self.publisher = EventPublisher(project_id=CONFIG.PROJECT_ID)

            amo_action_skus = await ozon.get_adv_info("amodecor")
            so_action_skus = await ozon.get_adv_info("stroy_otdelka")
            orion_action_skus = await ozon.get_adv_info("orion")

            for product_info in amo_action_skus:
                logger.debug(f"Processing Amo - SKU {product_info['sku']}...")
                if not await ozon.check_stock(seller="amodecor", sku=product_info["sku"]):
                    event = FoundZeroStockEvent(
                        sku=product_info["sku"],
                        legal_entity="Амодекор",
                        adv_id=product_info["adv_id"]
                    )
                    logger.info(f"Товар {product_info['sku']} из Амодекора закончился, но в рекламе.")
                    await self._reg_event(event)
            for product_info in so_action_skus:
                logger.debug(f"Processing SO - SKU {product_info['sku']}...")
                if not await ozon.check_stock(seller="stroy_otdelka", sku=product_info["sku"]):
                    event = FoundZeroStockEvent(
                        sku=product_info["sku"],
                        legal_entity="СтройОтделка",
                        adv_id=product_info["adv_id"]
                    )
                    logger.info(f"Товар {product_info['sku']} из СтройОтделки закончился, но в рекламе.")
                    await self._reg_event(event)
            for product_info in orion_action_skus:
                logger.debug(f"Processing Orion - SKU {product_info['sku']}...")
                if not await ozon.check_stock(seller="orion", sku=product_info["sku"]):
                    event = FoundZeroStockEvent(
                        sku=product_info["sku"],
                        legal_entity="Орион",
                        adv_id=product_info["adv_id"]
                    )
                    logger.info(f"Товар {product_info['sku']} из Ориона закончился, но в рекламе.")
                    await self._reg_event(event)
        except Exception as e:
            logger.exception(f"An error occurred: {e}")

    async def _reg_event(self, event: FoundZeroStockEvent):
        try:
            self.publisher.registration(
                event=event,
                topic="zero_stock_adv_ozon",
            )
            logger.info(f"Event for SKU {event.sku} is published.")
        except Exception as e:
            logger.exception(f"Error publishing for SKU {event.sku}: {e}")
