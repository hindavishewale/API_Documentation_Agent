from fastapi import Depends, FastAPI
from pydantic import BaseModel

app = FastAPI(title="Commerce API", version="2.0")

class Product(BaseModel):
    id: int
    name: str
    price: float
    currency: str

class User(BaseModel):
    id: int
    email: str
    display_name: str

@app.get("/products")
def list_products():
    return []

@app.get("/products/{product_id}")
def get_product(product_id: str):
    return {}

@app.post("/products")
def create_product(product: Product, current_user=Depends(get_current_user)):
    return product

@app.patch("/products/{product_id}")
def update_product(product_id: str, product: Product):
    return product

@app.get("/users")
def list_users():
    return []

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {}

@app.post("/users")
def create_user(user: User):
    return user

@app.post("/orders")
def create_order():
    return {"id": "new"}
