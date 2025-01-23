from dataclasses import dataclass    

class Event:
    pass

class PubSubNotification(Event):
    pass

@dataclass
class FoundZeroStockEvent:
    sku: int
    legal_entity: str
    adv_id: str

