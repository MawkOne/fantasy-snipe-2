import os
import sys

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import create_tables


def main() -> None:
    create_tables()


if __name__ == "__main__":
    main()

