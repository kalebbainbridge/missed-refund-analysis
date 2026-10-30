from contextlib import contextmanager
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "prototype"
    / "missed_refunds_prototype.db"
)


@contextmanager
def get_connection(database_path=DATABASE_PATH):
    database_path = Path(database_path).resolve()

    if not database_path.is_file():
        raise FileNotFoundError(
            f"Database not found: {database_path}"
        )

    connection = sqlite3.connect(
        database_path.as_uri() + "?mode=rw",
        uri=True,
        timeout=10,
    )

    try:
        connection.execute("PRAGMA foreign_keys = ON;")

        yield connection

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
