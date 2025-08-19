from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class Pagination(BaseModel):
    page: int = 1
    size: int = 20


class Page(BaseModel):
    items: list
    total: int
    page: int
    size: int
