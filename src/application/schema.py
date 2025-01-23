from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from dataclasses import dataclass, asdict


@dataclass
class ApiKey:
    key: str
    client_id: str | None
    name: str


class LegalEntitiesEnum(StrEnum):
    AMODECOR = "amodecor"
    DRIVE = "drive"
    CENTURION = "centurion"
    STROY_OTDELKA = "stroy_otdelka"
    ORION = "orion"


class MarketplacesEnum(StrEnum):
    OZON = "ozon"


@dataclass
class DTO:
    def to_dict(self):
        return asdict(self)

