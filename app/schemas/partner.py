from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PartnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    org_name: str
    inn: str | None = None
    type: str
    contract_no: str | None = None
    status: str
    price_list_id: int | None = None
    created_at: datetime
