from __future__ import annotations
from collections import namedtuple
from dataclasses import dataclass
from enum import StrEnum
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ApiKey:
    key: str
    client_id: str | None
    name: str


MatchedNamedProduct = namedtuple(
    "MatchedNamedProduct",
    [
        "notice",
        "ozon_legal_entity",
        "sku_wb",
        "sku_ozon",
        "sku_yandex",
        "ozon_name",
        "wb_price",
        "wb_price_wallet",
        "ozon_price",
        "ozon_card_price",
        "min_price_ozon",
        "yandex_price",
        "diff_price",
        "stock_wb",
        "stock_ozon",
        "stock_yandex",
        "sales_wb",
        "sales_ozon",
        "sales_yandex",
        "ctok",
        "ozon_adv",
        "in_supplies",
        "actions",
    ]
)


class LegalEntitiesEnum(StrEnum):
    AMODECOR = "amodecor"
    DRIVE = "drive"
    CENTURION = "centurion"
    STROY_OTDELKA = "stroy_otdelka"
    ORION = "orion"


class MarketplacesEnum(StrEnum):
    WB = "wb"
    OZON = "ozon"
    YANDEX_MARKET = "yandex_market"


@dataclass
class WBProduct:
    nmID: int
    vendorCode: str
    subjectName: str
    title: str
    seller: str

    def __hash__(self):
        return hash((self.nmID, self.vendorCode))

    def __eq__(self, other):
        if not isinstance(other, WBProduct):
            return False
        return self.nmID == other.nmID and self.vendorCode == other.vendorCode


@dataclass
class YandexProduct:
    """Описывает элемент продукта Яндекса при получении списка товаров через API"""
    vendor_code: str
    name: str
    price: int

    def __hash__(self):
        return hash(self.sku)


@dataclass
class MatchedProduct:
    """Описывает элемент (строчку) результирующего файла"""
    notice: str
    ozon_legal_entity: str
    sku_wb: int
    sku_ozon: int
    sku_yandex: int
    ozon_name: str
    wb_price_wallet: int
    ozon_price: int
    wb_price: int
    ozon_card_price: int
    min_price_ozon: float
    yandex_price: int
    diff_price: int
    """Цена вб - цена озона"""
    stock_wb: int
    stock_ozon: int
    stock_yandex: int
    sales_ozon: int
    sales_wb: int
    sales_yandex: int
    """Реклама Ozon"""
    ozon_adv: str

    in_supplies: int

    actions: str

    def __hash__(self):
        return hash((self.sku_wb, self.sku_ozon, self.sku_yandex))

    def __eq__(self, other):
        if not isinstance(other, MatchedProduct):
            return False
        return self.sku_wb == other.sku_wb and self.sku_ozon == other.sku_ozon and self.sku_yandex == other.sku_yandex

    def to_namedtuple(self):
        """Преобразует объект в namedtuple"""
        try:
            ctok = float(self.stock_ozon / self.sales_ozon) if self.sales_ozon > 0 else -1
        except Exception:
            ctok = -1
        try:
            ozon_min_price = float(self.min_price_ozon)
        except ValueError:
            ozon_min_price = "Неизвестно"
        return MatchedNamedProduct(
            notice=self.notice,
            ozon_legal_entity=self.ozon_legal_entity,
            sku_wb=int(self.sku_wb),
            sku_ozon=int(self.sku_ozon),
            sku_yandex=int(self.sku_yandex),
            ozon_name=self.ozon_name,
            wb_price=int(self.wb_price),
            wb_price_wallet=int(self.wb_price_wallet),
            ozon_price=int(self.ozon_price),
            ozon_card_price=int(self.ozon_card_price),
            min_price_ozon=ozon_min_price,
            yandex_price=int(self.yandex_price),
            diff_price=int(self.diff_price),
            stock_wb=int(self.stock_wb),
            stock_ozon=int(self.stock_ozon),
            stock_yandex=int(self.stock_yandex),
            sales_wb=int(self.sales_wb),
            sales_ozon=int(self.sales_ozon),
            sales_yandex=int(self.sales_yandex),
            ctok=ctok,
            ozon_adv=str(self.ozon_adv),
            in_supplies=int(self.in_supplies),
            actions=str(self.actions),
        )

@dataclass
class DTO:
    def to_dict(self):
        return asdict(self)


@dataclass
class SalesAndAvailabilityReport(DTO):
    """
    Отчет о продажах и наличии товара

    :param start_date: Начальная дата периода
    :param end_date: Конечная дата периода
    :param sales_quantity: Количество продаж за период
    :param availability_in_days: Количество дней в наличии за период
    :param is_theoretical: являются ли данные теоретическими
    """

    availability_in_days: int
    sales_quantity: int
    period: int
    start_date: datetime
    end_date: datetime
    is_theoretical: bool


@dataclass
class Notification(DTO):
    """
    Уведомление об остатках товара

    :param name: Имя товара
    :param vendor_code: Артикул поставщика
    :param sku: Артикул товара на площадке
    :param mp: Название Площадки
    :param url_on_product: Ссылка на товар
    :param sales_for_period: продажи за период
    :param stock_sum: Сумма количества остатков fbo и fbs
    :param stock_fbo: Количество остатков по fbo
    :param stock_fbs: Количество остатков по fbs
    :param status_product: Статус продукта ProductStatus
    :status_notification: Статус уведомлений
    """

    seller: str
    name: str
    vendor_code: str
    sku: str
    mp: str
    url_on_product: str
    sales_for_period: int
    stock_sum: int
    stock_fbo: int
    stock_fbs: int
    status_product: str
    status_notification: int


@dataclass
class Sku(DTO):
    sku: str
    vendor_code: str
    marketplace: str


@dataclass
class Sale(DTO):
    quantity: int
    date: datetime
    sku: str
    in_stock: int



@dataclass
class Product(DTO):
    sku: Sku
    name: str
    url: str
    seller: str
    stock_fbo: int
    stock_fbs: int
    sales: list[Sale]
    internal_id: int | None = "NoneTestSTR"
