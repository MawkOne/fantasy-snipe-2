
import os
import sys
import pandas as pd
from google.cloud import bigquery
from sqlalchemy.orm import sessionmaker
import logging

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud settings from environment variables
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BIGQUERY_DATASET_ID = os.getenv("BIGQUERY_DATASET_ID")
BIGQUERY_TABLE_ID = os.getenv("BIGQUERY_TABLE_ID")

def get_db_session():
    """Creates a new database session using Cloud SQL Connector."""
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    return Session()

def fetch_player_game_logs():
    """Fetches player game logs from the database."""
    logger.info("Fetching player game logs from the database...")
    session = get_db_session()
    try:
        query = "SELECT * FROM player_game_logs"
        df = pd.read_sql(query, session.bind)
        logger.info(f"Successfully fetched {len(df)} records from the database.")
        return df
    finally:
        session.close()

def upload_to_bigquery(df):
    """Uploads a DataFrame to a BigQuery table."""
    if df.empty:
        logger.info("DataFrame is empty. No data to upload to BigQuery.")
        return

    logger.info(f"Uploading {len(df)} records to BigQuery...")
    client = bigquery.Client(project=GCP_PROJECT_ID)
    table_ref = client.dataset(BIGQUERY_DATASET_ID).table(BIGQUERY_TABLE_ID)

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Overwrite the table
    )

    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Wait for the job to complete
    logger.info(f"Successfully uploaded data to {BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}")

if __name__ == "__main__":
    player_game_logs_df = fetch_player_game_logs()
    upload_to_bigquery(player_game_logs_df)
