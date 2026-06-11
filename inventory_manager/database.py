import sqlite3
import os
from contextlib import contextmanager
from inventory_manager.logger import logger

DEFAULT_DB_PATH = "inventory.db"

@contextmanager
def get_db_connection(db_path=DEFAULT_DB_PATH):
    """
    Context manager for SQLite database connection.
    Enforces foreign keys and ensures the connection is closed.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # SQLite foreign key support is disabled by default and must be enabled per-connection.
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # Access columns by name like dictionary keys
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}", exc_info=True)
        raise e
    finally:
        if conn:
            conn.close()

def initialize_database(db_path=DEFAULT_DB_PATH):
    """
    Initializes the SQLite database with the required schema.
    Creates tables if they do not exist.
    """
    logger.info(f"Initializing database at {db_path}")
    
    schema_products = """
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
        reorder_level INTEGER NOT NULL DEFAULT 10 CHECK(reorder_level >= 0),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    schema_transactions = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        transaction_type TEXT NOT NULL CHECK(transaction_type IN ('IN', 'OUT', 'ADJUST')),
        quantity INTEGER NOT NULL,
        notes TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """
    
    # Trigger to update updated_at on product update
    schema_trigger = """
    CREATE TRIGGER IF NOT EXISTS update_product_timestamp
    AFTER UPDATE ON products
    FOR EACH ROW
    BEGIN
        UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = old.id;
    END;
    """

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(schema_products)
            cursor.execute(schema_transactions)
            cursor.execute(schema_trigger)
            conn.commit()
        logger.info("Database initialization completed successfully.")
    except sqlite3.Error as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
        raise e
