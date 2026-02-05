from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import json
import qyro_adapters.python_adapter as qyro

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/products")
def get_products():
    qyro.publish("logs", {"service": "api", "msg": "Fetching products"})

    products = [
        {"id": 1, "name": "Laptop", "base_price": 1000},
        {"id": 2, "name": "Phone", "base_price": 500},
        {"id": 3, "name": "Headphones", "base_price": 100},
    ]

    discount = qyro.get("discount_factor")
    if not discount:
        discount = 1.0
    else:
        try:
            discount = float(discount)
        except:
            discount = 1.0

    for p in products:
        p["price"] = p["base_price"] * discount

    return products

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)