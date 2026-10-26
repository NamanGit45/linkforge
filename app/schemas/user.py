import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):

    email: EmailStr 
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):

    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserInDB(UserResponse):

    hashed_password: str
