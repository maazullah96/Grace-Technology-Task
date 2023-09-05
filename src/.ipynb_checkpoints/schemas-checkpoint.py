
from pydantic import BaseModel

class UserResponse(BaseModel):
    username: str



class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class UploadResponse(BaseModel):
    message: str


