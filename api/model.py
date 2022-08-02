from uuid import UUID
from typing import Literal, Optional

from pydantic import BaseModel, HttpUrl


class HandOff(BaseModel):
    circuitId: str
    vlan: str


class Service(BaseModel):
    class ServiceDetails(BaseModel):
        class Data(BaseModel):
            downloadSpeedKbps: int
            uploadSpeedKbps: int

        data: Data

    type: str
    detail: ServiceDetails


class CallbackUrls(BaseModel):
    success: HttpUrl
    error: HttpUrl
    status: HttpUrl

    def __getitem__(self, item):
        return self.__dict__[item]


class ServiceRequest(BaseModel):
    type: Literal["provision", "replace", "unprovision"]
    provider_handoff: Optional[HandOff]
    new_provider_handoff: Optional[HandOff]
    old_provider_handoff: Optional[HandOff]
    service: Optional[Service]
    new_service: Optional[Service]
    old_service: Optional[Service]
    callback_urls: CallbackUrls
    subscription_id: Optional[UUID]
    new_subscription_id: Optional[UUID]
    old_subscription_id: Optional[UUID]
    underline_account_id: UUID
    sonar_account_id: int

    class Config:
        fields = {
            "type": {"exclude": True},
            "callback_urls": {"exclude": True},
            "underline_account_id": {"exclude": True},
        }

    def json(self, *args, **kwargs):
        return super().json(*args,
                            exclude_none=True,
                            indent=None,
                            separators=(",", ":"),
                            **kwargs)
