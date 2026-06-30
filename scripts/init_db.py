import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.hotels import list_hotels
from app.db.lifecycle import init_db, reset_db
from app.db.session import DB_PATH, SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the demo SQLite database.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and reseed demo data.",
    )
    args = parser.parse_args()

    if args.reset:
        reset_db()
        action = "Reset"
    else:
        init_db()
        action = "Initialized"

    with SessionLocal() as db:
        hotels = list_hotels(db)
    print(f"{action} database: {DB_PATH}")
    print(f"Hotel rows: {len(hotels)}")
    for hotel in hotels:
        print(
            f"- {hotel['id']}: {hotel['room_type']} "
            f"base_price={hotel['base_price']} occupancy={hotel['occupancy']}"
        )


if __name__ == "__main__":
    main()
