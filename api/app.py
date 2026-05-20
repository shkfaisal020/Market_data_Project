from fastapi import FastAPI, HTTPException
from random import random, choice, uniform
from datetime import datetime

app = FastAPI()

instruments = [
    "AAPL",
    "BTC-USD",
    "ETH-USD",
    "GOOGL"
]

@app.get("/v1/market-data")
def get_market_data():

    fault = random()

    # 5% fault injection
    if fault < 0.05:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )

    data = []

    for _ in range(5):

        record = {
            "instrument_id": choice(instruments),
            "price": round(uniform(100, 50000), 2),
            "volume": round(uniform(1, 1000), 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        data.append(record)

    return data