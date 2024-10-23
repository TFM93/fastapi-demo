from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    tenant: str


class UserResp(BaseModel):
    id: int
    email: EmailStr
    tenant: str
    created_at: datetime

    class Config:
        orm_mode = True


class ImageCreate(BaseModel):
    filename: str
    data: bytes


class ImageUpdate(BaseModel):
    filename: str


class ImageResp(BaseModel):
    id: int
    filename: str
    user_id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        orm_mode = True
