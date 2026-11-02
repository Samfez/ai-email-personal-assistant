from typing import Any, Dict
from pydantic import BaseModel


class WebhookEvent(BaseModel):
    specversion: str
    type: str
    source: str
    id: str
    time: int
    webhook_delivery_attempt: int
    data: Dict[str, Any]