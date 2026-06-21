from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    user_id: int
    pin: str = Field(min_length=1, max_length=32)


class ChangePinRequest(BaseModel):
    current_pin: str = Field(min_length=1, max_length=32)
    new_pin: str = Field(min_length=4, max_length=32)


class ActiveUserSummary(BaseModel):
    id: int
    full_name: str

    class Config:
        from_attributes = True


class CurrentUserResponse(BaseModel):
    id: int
    full_name: str
    balance: str
    is_admin: bool
