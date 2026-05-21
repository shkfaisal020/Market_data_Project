import os
from dotenv import load_dotenv
import requests
import pandas as pd
import time
import logging
load_dotenv()

from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, text
from datetime import datetime

# =========================
# Logging Configuration
# =========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# =========================
# Database Connection
# =========================

DB_URL = f"""

postgresql://
{os.getenv('POSTGRES_USER')}:
{os.getenv('POSTGRES_PASSWORD')}@
{os.getenv('POSTGRES_HOST')}:
{os.getenv('POSTGRES_PORT')}/
{os.getenv('POSTGRES_DB')}

""".replace("\n", "")

engine = create_engine(DB_URL)

# =========================
# API URL
# =========================

API_URL = "http://127.0.0.1:8000/v1/market-data"

# =========================
# Pydantic Schema Validation
# =========================

class MarketData(BaseModel):

    instrument_id: str
    price: float
    volume: float
    timestamp: str

# =========================
# Infinite ETL Loop
# =========================

while True:

    start_time = time.time()

    processed_records = 0
    dropped_records = 0

    try:

        # =========================
        # API Extraction
        # =========================

        response = requests.get(
            API_URL,
            timeout=5
        )

        # Handle faulty responses
        if response.status_code != 200:

            logging.error(
                f"API Error: {response.status_code}"
            )

            time.sleep(10)
            continue

        raw_data = response.json()

        validated_data = []

        # =========================
        # Schema Validation
        # =========================

        for record in raw_data:

            try:

                validated_record = MarketData(**record)

                validated_data.append(
                    validated_record.dict()
                )

            except ValidationError as e:

                dropped_records += 1

                logging.warning(
                    f"Validation Failed: {record}"
                )

        # No valid records
        if not validated_data:

            logging.warning("No valid data found")

            time.sleep(10)
            continue

        # =========================
        # Create DataFrame
        # =========================

        df = pd.DataFrame(validated_data)

        # =========================
        # VWAP Calculation
        # =========================

        vwap_df = (
            df.groupby("instrument_id")
            .apply(
                lambda x:
                (x["price"] * x["volume"]).sum()
                / x["volume"].sum()
            )
            .reset_index(name="vwap")
        )

        df = df.merge(
            vwap_df,
            on="instrument_id",
            how="left"
        )

        # =========================
        # Average Price Per Instrument
        # =========================

        avg_price_df = (
            df.groupby("instrument_id")["price"]
            .mean()
            .reset_index(name="avg_price")
        )

        df = df.merge(
            avg_price_df,
            on="instrument_id",
            how="left"
        )

        # =========================
        # Outlier Detection
        # =========================

        df["is_outlier"] = (
            abs(df["price"] - df["avg_price"])
            > (0.15 * df["avg_price"])
        )

        # =========================
        # Remove Duplicate Records
        # =========================

        unique_rows = []

        for _, row in df.iterrows():

            query = text("""

                SELECT COUNT(*)

                FROM market_data

                WHERE instrument_id = :instrument_id

                AND timestamp = :timestamp

            """)

            result = engine.execute(
                query,
                {
                    "instrument_id":
                    row["instrument_id"],

                    "timestamp":
                    row["timestamp"]
                }
            ).scalar()

            if result == 0:
                unique_rows.append(row)

        final_df = pd.DataFrame(unique_rows)

        # =========================
        # Insert Into PostgreSQL
        # =========================

        if not final_df.empty:

            final_df.to_sql(
                "market_data",
                engine,
                if_exists="append",
                index=False
            )

            processed_records = len(final_df)

        # =========================
        # Structured Logging
        # =========================

        execution_time = (
            time.time() - start_time
        )

        logging.info(
            f"""
            Records Processed: {processed_records}
            Records Dropped: {dropped_records}
            Execution Time: {execution_time:.2f} sec
            """
        )

    except requests.exceptions.Timeout:

        logging.error("API Timeout Error")

    except Exception as e:

        logging.error(f"Unexpected Error: {e}")

    # Poll every 10 sec
    time.sleep(10)