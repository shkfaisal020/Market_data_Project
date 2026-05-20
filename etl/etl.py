import requests
import pandas as pd
from sqlalchemy import create_engine
import time

API_URL = "http://127.0.0.1:8000/v1/market-data"

DB_URL = "postgresql://admin:admin@localhost:5432/marketdb"

engine = create_engine(DB_URL)

while True:

    try:

        response = requests.get(API_URL)

        if response.status_code != 200:
            print("API Error")
            continue

        data = response.json()

        df = pd.DataFrame(data)

        # Data validation
        df = df[
            pd.to_numeric(
                df["price"],
                errors="coerce"
            ).notnull()
        ]

        df.to_sql(
            "market_data",
            engine,
            if_exists="append",
            index=False
        )

        print("Data inserted successfully")

    except Exception as e:
        print("Error:", e)

    time.sleep(10)