from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str # Tambahkan ini
    username: str # Tambahkan ini juga untuk kemudahan frontend

class TokenData(BaseModel):
    username: Optional[str] = None

class DivisionBase(BaseModel):
    name: str

class DivisionCreate(DivisionBase):
    pass

class Division(DivisionBase):
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    username: str
    division_id: int

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "employee"

class User(UserBase):
    id: int
    role: str

    class Config:
        orm_mode = True

class ReportBase(BaseModel):
    text: str
    photo_path: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    timestamp: datetime
    owner_id: int

    class Config:
        orm_mode = True
