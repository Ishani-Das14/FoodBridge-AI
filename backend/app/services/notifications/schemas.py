import datetime
from pydantic import BaseModel
from typing import Dict, Optional

class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str

class PushSubscription(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys

class SubscriptionPayload(BaseModel):
    subscription: PushSubscription

class NotificationOut(BaseModel):
    id: int
    title: str
    body: str
    is_read: bool
    created_at: datetime.datetime

    class Config:
        orm_mode = True
        from_attributes = True
