from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    description: str
    price: int

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: int

    class Config:
        from_attributes = True
