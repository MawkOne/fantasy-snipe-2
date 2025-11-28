import os
import sys
from sqlalchemy.orm import sessionmaker

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connection import connect_with_connector
from src.database.models import Game, Player, Team, PlayerGameStats

def count_records(session, model):
    """Counts the number of records for a given model."""
    try:
        return session.query(model).count()
    except Exception as e:
        print(f"Error counting {model.__tablename__}: {e}")
        return 0

def check_database_counts():
    """
    Connects to the database and prints the record counts for each table.
    """
    print("Connecting to the database...")
    engine = connect_with_connector()
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Database connection successful.")

    try:
        num_teams = count_records(session, Team)
        num_players = count_records(session, Player)
        num_games = count_records(session, Game)
        num_player_stats = count_records(session, PlayerGameStats)
        
        print("\n--- Database Record Counts ---")
        print(f"Teams: {num_teams}")
        print(f"Players: {num_players}")
        print(f"Games: {num_games}")
        print(f"Player Game Stats: {num_player_stats}")
        print("------------------------------\n")

    except Exception as e:
        print(f"A critical error occurred: {e}")
    finally:
        session.close()
        print("Database session closed.")

if __name__ == "__main__":
    check_database_counts()
