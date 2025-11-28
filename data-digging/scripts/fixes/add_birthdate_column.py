import argparse
from google.cloud import bigquery

def add_birthdate_column(client: bigquery.Client) -> None:
    """Add birth_date column to the players table."""
    
    # Step 1: Create new table with birth_date column
    print("Creating new players table with birth_date column...")
    create_query = """
    CREATE TABLE `fantasy-snipe-ai.nhl_raw.players_new` (
      id INT64,
      full_name STRING,
      birth_date DATE
    )
    """
    client.query(create_query).result()
    print("✓ Created new table structure")
    
    # Step 2: Copy existing data with NULL birth_date
    print("Copying existing data...")
    copy_query = """
    INSERT INTO `fantasy-snipe-ai.nhl_raw.players_new` (id, full_name, birth_date)
    SELECT id, full_name, CAST(NULL AS DATE) as birth_date
    FROM `fantasy-snipe-ai.nhl_raw.players`
    """
    client.query(copy_query).result()
    print("✓ Copied existing data")
    
    # Step 3: Drop old table
    print("Dropping old table...")
    client.query("DROP TABLE `fantasy-snipe-ai.nhl_raw.players`").result()
    print("✓ Dropped old table")
    
    # Step 4: Rename new table
    print("Renaming new table...")
    client.query("ALTER TABLE `fantasy-snipe-ai.nhl_raw.players_new` RENAME TO `fantasy-snipe-ai.nhl_raw.players`").result()
    print("✓ Renamed table")
    
    print("Successfully added birth_date column to players table!")

def main():
    parser = argparse.ArgumentParser(description='Add birth_date column to players table')
    args = parser.parse_args()
    
    client = bigquery.Client()
    add_birthdate_column(client)

if __name__ == "__main__":
    main()
