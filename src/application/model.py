from __future__ import annotations
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.application import events, schema

logger = logging.getLogger(__name__)


class ProductStatus(Enum):
    ORDINARY = "ordinary"
    NEW = "new"
    ABSOLUTE_NEW = "absolute_new"
    DEFAULT = ""


@dataclass
class Sku:
    id: int | None
    vendor_code: str
    sku: str
    marketplace: str

@dataclass
class Sale:
    """Объект-значение, представляющая информацию о продаже"""
    quantity: int
    date: datetime
    product_id: int
    in_stock: int
    product: schema.Product

    def update(self, sale_data: schema.Sale, internal_product_id: int):
        # Обновляем свойства основного класса продукта
        if internal_product_id is None or self.product_id is None:
            raise ValueError("Internal product ID is None")
        self.product_id = internal_product_id
        self.date = sale_data.date
        self.in_stock = sale_data.in_stock
        self.quantity = sale_data.quantity


class Product:
    """
    Агрегат, представляющий собой товар
    """

    def __init__(
            self,
            id: int,
            sku: Sku,
            name: str,
            url: str,
            seller: str,
            stock_fbo: int,
            stock_fbs: int,
            sales: list[Sale],
            _status: str = "",
            pre_replenishment_inventory: int = None,
    ):
        self.id = id
        self.sku = sku
        self.name = name
        self.url = url
        self.seller = seller
        self._status = _status
        self.stock_fbo = stock_fbo
        self.stock_fbs = stock_fbs
        if pre_replenishment_inventory:
            self.pre_replenishment_inventory = pre_replenishment_inventory
        else:
            self.pre_replenishment_inventory = stock_fbs + stock_fbo
        self.sales = sales
        self.events: list[events.Event] = []

    @property
    def status(self):
        return ProductStatus(self._status)

    @status.setter
    def status(self, pr_status: ProductStatus):
        self._status = pr_status.value

    @property
    def stock(self):
        return self.stock_fbo + self.stock_fbs

    @classmethod
    def create(cls, product: schema.Product, internal_id: int, sku_id: int| None):
        sales = [
            Sale(
                quantity=sl.quantity,
                date=sl.date,
                product_id=internal_id,
                in_stock=sl.in_stock,
                product=product
            )
            for sl in product.sales
        ]
        product = cls(
            id=internal_id,
            sku=Sku(
                sku=product.sku.sku,
                vendor_code=product.sku.vendor_code,
                marketplace=product.sku.marketplace,
                id=sku_id
            ),
            name=product.name,
            url=product.url,
            seller=product.seller,
            _status="",
            stock_fbo=product.stock_fbo,
            stock_fbs=product.stock_fbs,
            sales=sales,
            pre_replenishment_inventory=product.stock_fbo + product.stock_fbs,
        )
        for sale in product.sales:
            sale.product = product
        return product

    @classmethod
    def create_without_sales(cls, product: schema.Product):
        product = cls(
            id=product.internal_id if isinstance(product.internal_id, int) else None,
            sku=Sku(
                sku=product.sku.sku,
                vendor_code=product.sku.vendor_code,
                marketplace=product.sku.marketplace,
                id=None
            ),
            name=product.name,
            url=product.url,
            seller=product.seller,
            _status="",
            stock_fbo=product.stock_fbo,
            stock_fbs=product.stock_fbs,
            sales=[],
            pre_replenishment_inventory=product.stock_fbo + product.stock_fbs,
        )
        return product

    def update(self, product: schema.Product):
        if self.id is None:
            raise Exception("Cannot update product without id")
        self.name = product.name
        if self.stock < product.stock_fbo + product.stock_fbs:
            self.pre_replenishment_inventory = product.stock_fbs + product.stock_fbo
        self.stock_fbs = product.stock_fbs
        self.stock_fbo = product.stock_fbo
        sales_dict = {(sale.product.sku.sku, sale.date): sale for sale in self.sales}

        # Итерируем по product.sales
        for sl_data in product.sales:
            # Получаем ключ для словаря
            key = (product.sku.sku, sl_data.date)

            # Проверяем, есть ли продажа с таким ключом в словаре
            if key in sales_dict:
                # Обновляем существующую продажу
                sales_dict[key].update(sl_data, self.id)
                sales_dict[key].product = self
            else:
                # Создаем новую продажу и добавляем ее в словарь
                new_sale = Sale(
                    quantity=sl_data.quantity,
                    date=sl_data.date,
                    product_id=self.id,
                    product=self,
                    in_stock=sl_data.in_stock,
                )
                sales_dict[key] = new_sale
                self.sales.append(new_sale)

        # Если потребуется, обновляем список self.sales
        self.sales = list(sales_dict.values())

    def update_status(self):
        self.sales.sort(key=lambda x: x.date, reverse=True)
        if self.status == ProductStatus.DEFAULT:
            is_absolute_new = not bool([sale for sale in self.sales if sale.in_stock])
            if is_absolute_new:
                self.status = ProductStatus.ABSOLUTE_NEW
                return
            is_new = not bool([sale for sale in self.sales[0:15] if sale.in_stock])
            if is_new:
                self.status = ProductStatus.NEW
                return
            self.status = ProductStatus.ORDINARY
        elif self.status == ProductStatus.ORDINARY:
            is_new = not bool([sale for sale in self.sales[0:15] if sale.in_stock])
            if is_new:
                self.status = ProductStatus.NEW
                return
        else:
            info_month = [sale for sale in self.sales[0:30] if sale.in_stock]
            is_stock = bool([sale for sale in self.sales[0:15] if sale.in_stock])
            if len(info_month) > 15 and is_stock:
                self.status = ProductStatus.ORDINARY
                return

    def check_stocks(self):
        self.events.append(events.FetchedProduct(self.sku))

    def _get_sales_and_quantity(
            self, period_start: int, period_end: int
    ) -> tuple | None:
        """
        Метод возвращает количество продаж за период, и высчитывает теоретические данные
        """
        period = (period_end - period_start).days
        period_sales = [
            s for s in self.sales if period_start <= s.date <= period_end and s.in_stock
        ]
        sale_period_qty = sum(s.quantity for s in period_sales)
        in_stock_days = len(period_sales)
        # если товар в наличии был больше периода высчитываем теоритические данные
        if in_stock_days >= period / 2:
            sale_period_qty = int((sale_period_qty / in_stock_days) * period)
            return in_stock_days, sale_period_qty, True
        return in_stock_days, sale_period_qty, False

    def get_sales_and_availability_by_period(
            self, days: int
    ) -> schema.SalesAndAvailabilityReport:
        """
        Метод по периоду возвращающий продажи(фактические или теоретические)
        за этот период и наличие товара в периоде
        """
        period_start = (datetime.utcnow() - timedelta(days)).replace(
            second=0, microsecond=0
        )
        period_end = datetime.utcnow().replace(second=0, microsecond=0)
        # случай 1 товар был весь текущий период или частично
        cur_availability, cur_quantity, is_availability = self._get_sales_and_quantity(
            period_start,
            period_end
        )
        if is_availability:
            # Товар был весь период
            if cur_availability == days:
                return schema.SalesAndAvailabilityReport(
                    availability_in_days=cur_availability,
                    sales_quantity=cur_quantity,
                    period=days,
                    start_date=period_start,
                    end_date=period_end,
                    is_theoretical=False,
                )
            # Товар был в периоде частично(теоретические данные)
            return schema.SalesAndAvailabilityReport(
                availability_in_days=cur_availability,
                sales_quantity=cur_quantity,
                period=days,
                start_date=period_start,
                end_date=period_end,
                is_theoretical=True,
            )

        # # случай 2 товара не было в текущем периоде
        period_start = (datetime.utcnow() - timedelta(days * 2)).replace(
            second=0, microsecond=0
        )
        (
            past_availability,
            past_quantity,
            is_availability,
        ) = self._get_sales_and_quantity(period_start, period_end - timedelta(days))
        if is_availability:
            return schema.SalesAndAvailabilityReport(
                availability_in_days=past_availability,
                sales_quantity=past_quantity,
                period=days,
                start_date=period_start,
                end_date=period_end - timedelta(days),
                is_theoretical=True,
            )

        # случай 3 товар был в наличии меньше прошлого
        # и текущего периода или вообще отсутствовал
        return schema.SalesAndAvailabilityReport(
            availability_in_days=cur_availability + past_availability,
            sales_quantity=cur_quantity + past_quantity,
            period=days * 2,
            start_date=period_start,
            end_date=period_end,
            is_theoretical=False,
        )


class Notification:
    def __init__(self, status: str, sku: Sku):
        self.status = status
        self.sku = sku
        self.events: list[events.Event] = []

    def _change_status(self, new_status: str):
        self.status = new_status

    def _can_send(self, ban_status: str):
        return self.status != ban_status

    def _send_notification_low_stock(self, notification: schema.Notification):
        logger.info("added new event - LowOnStock")
        self.events.append(events.LowOnStock(data={"notification": notification}))

    def _check_and_send(
            self, notification: schema.Notification, ratio: float, thresholds: list[dict]
    ) -> bool:
        for threshold in thresholds:
            if threshold.get("coef_min") <= ratio < threshold.get("coef_max"):
                ban_status = threshold.get("status")
                if self._can_send(ban_status):
                    logger.info(f"threshold: {threshold} ratio: {ratio}")
                    notification.status_notification = threshold.get("count_sent")
                    self._send_notification_low_stock(notification)
                    self._change_status(ban_status)
                    return True
        return False

    def check_and_send_notification(
            self,
            product: Product,
    ) -> bool:
        if product.stock == 0:
            logger.warning("Cannot create notification: product stock is zero")
            return False
        if product.stock > 50:
            logger.warning("Cannot create notification: product stock is more than 50")
            return False
        sales_report = product.get_sales_and_availability_by_period(days=30)
        self.checkers = {
            ProductStatus.ORDINARY: sales_report.sales_quantity / product.stock,
            ProductStatus.ABSOLUTE_NEW: product.pre_replenishment_inventory
                                        / product.stock,
            ProductStatus.NEW: product.pre_replenishment_inventory / product.stock,
        }
        self.thresholds = {
            ProductStatus.ORDINARY: [
                {
                    "coef_min": 12.2,
                    "coef_max": 1000,
                    "status": "sent_12",
                    "count_sent": 3,
                },
                {
                    "coef_min": 6.2,
                    "coef_max": 12.2,
                    "status": "sent_6",
                    "count_sent": 2,
                },
            ],
            ProductStatus.ABSOLUTE_NEW: [
                {
                    "coef_min": 12.2,
                    "coef_max": 1000,
                    "status": "sent_12",
                    "count_sent": 3,
                },
                {
                    "coef_min": 6.2,
                    "coef_max": 12.2,
                    "status": "sent_6",
                    "count_sent": 2,
                },
                {"coef_min": 3, "coef_max": 6.2, "status": "sent_3", "count_sent": 1},
            ],
            ProductStatus.NEW: [
                {
                    "coef_min": 12.2,
                    "coef_max": 1000,
                    "status": "sent_12",
                    "count_sent": 3,
                },
                {
                    "coef_min": 6.2,
                    "coef_max": 12.2,
                    "status": "sent_6",
                    "count_sent": 2,
                },
                {"coef_min": 3, "coef_max": 6.2, "status": "sent_3", "count_sent": 1},
            ],
        }
        notification = schema.Notification(
            seller=product.seller,
            name=product.name,
            vendor_code=product.sku.vendor_code,
            sku=self.sku.sku,
            mp=self.sku.marketplace,
            url_on_product=product.url,
            sales_for_period=sales_report.sales_quantity,
            stock_sum=product.stock,
            stock_fbo=product.stock_fbo,
            stock_fbs=product.stock_fbs,
            status_product=product.status.value,
            status_notification=0,
        )
        res = self._check_and_send(
            notification=notification,
            ratio=self.checkers[product.status],
            thresholds=self.thresholds[product.status],
        )
        return res
