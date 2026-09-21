from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Commerce API", version="1.0")

class Product(BaseModel):
    id: int
    name: str
    price: float

class User(BaseModel):
    id: int
    email: str

@app.get("/products")
def list_products():
    return []

@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {}

@app.post("/products")
def create_product(product: Product):
    return product

@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    return {"deleted": True}

@app.get("/users")
def list_users():
    return []

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {}

@app.post("/users")
def create_user(user: User):
    return user
