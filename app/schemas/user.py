from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.schemas.common import ORMModel


class UserBase(ORMModel):
    username: str
    email: EmailStr
    status: str


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
