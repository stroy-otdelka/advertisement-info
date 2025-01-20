from typing import Union
from uuid import uuid4
from datetime import datetime
from dataclasses import dataclass, field

from . import model
from src.application.schema import Notification, Sku, Product


class Event:
    pass


@dataclass
class StartedCheckStocksWb(Event):
    """
    Событие, сигнализирующее о начале проверке данных остатков на wb
    """

    seller: str


@dataclass
class StartedCheckStocksOzon(Event):
    """
    Событие, сигнализирующее о начале проверке данных остатков на Ozon
    """

    seller: str


@dataclass
class FetchedProduct(Event):
    sku: Sku
    new_product: Product = None

    def to_stock_over(self) -> Union["StockFBOOver", None]:
        if self.new_product is None:
            return
        return StockFBOOver(
            seller=self.new_product.seller,
            name=self.new_product.name,
            vendor_code=self.new_product.sku.vendor_code,
            sku=self.sku.sku,
            mp=self.new_product.sku.marketplace,
            url_on_product=self.new_product.url,
            sales_for_period=model.Product.create(
                self.new_product,
                self.new_product.internal_id,
                None
            ).get_sales_and_availability_by_period(
                30).sales_quantity,
            stock_fbo=self.new_product.stock_fbo,
            stock_fbs=self.new_product.stock_fbs
        )

    def to_stock_received(self) -> Union["StockFBOReceived", None]:
        if self.new_product is None:
            return
        return StockFBOReceived(
            seller=self.new_product.seller,
            name=self.new_product.name,
            vendor_code=self.new_product.sku.vendor_code,
            sku=self.sku.sku,
            mp=self.new_product.sku.marketplace,
            url_on_product=self.new_product.url,
            sales_for_period=model.Product.create(
                self.new_product,
                self.new_product.internal_id,
                None
            ).get_sales_and_availability_by_period(
                30).sales_quantity,
            stock_fbo=self.new_product.stock_fbo,
            stock_fbs=self.new_product.stock_fbs
        )


class PubSubNotification(Event):
    pass


@dataclass
class FBONotification(PubSubNotification):
    seller: str
    name: str
    vendor_code: str
    sku: str
    mp: str
    url_on_product: str
    sales_for_period: int
    stock_fbo: int
    stock_fbs: int

    def to_dict(self) -> dict:
        return {
            "seller": self.seller,
            "name": self.name,
            "vendor_code": self.vendor_code,
            "sku": self.sku,
            "mp": self.mp,
            "url_on_product": self.url_on_product,
            "sales_for_period": self.sales_for_period,
            "stock_fbo": self.stock_fbo,
            "stock_fbs": self.stock_fbs,
        }


@dataclass
class StockFBOOver(FBONotification, Event):
    pass


@dataclass
class StockFBOReceived(FBONotification, Event):
    pass


@dataclass
class LowOnStock(PubSubNotification, Event):
    """
    Событие, публикуется при низких остатках товара
    Содержит информацию о поставках, продажах и товаре
    """

    source: str = field(default_factory=lambda: "stock_service")
    guid: str = field(default_factory=lambda: str(uuid4()))
    time: datetime = field(default_factory=lambda: datetime.utcnow())
    data: dict[str, Notification] = field(
        default_factory=lambda: {"notification": None}
    )

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "guid": self.guid,
            "time": self.time.isoformat(),
            "data": {"notification": self.data.get("notification").to_dict()},
        }
