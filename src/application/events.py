from dataclasses import dataclass    

@dataclass
class Event:
    pass

class PubSubNotification(Event):
    pass

@dataclass
class FoundZeroStockEvent(Event):
    sku: int
    legal_entity: str
    adv_id: str

