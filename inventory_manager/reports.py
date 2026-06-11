import sqlite3
from inventory_manager.database import get_db_connection
from inventory_manager.logger import logger

def get_low_stock_report(db_path=None) -> list:
    """
    Returns products that are at or below their reorder level.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info("Generating Low Stock Report")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sku, name, category, price, quantity, reorder_level 
                FROM products 
                WHERE quantity <= reorder_level 
                ORDER BY quantity ASC
                """
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error during low stock report: {e}", exc_info=True)
        raise RuntimeError("An error occurred while generating the low stock report.")

def get_inventory_summary(db_path=None) -> dict:
    """
    Calculates inventory statistics for the dashboard:
    - Total unique products
    - Total items in stock
    - Total valuation (quantity * price)
    - Total transactions logged
    - Count of low stock products
    - Category breakdown (category name, product count, stock sum, valuation)
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info("Generating Inventory Summary Dashboard statistics")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            
            # Overall metrics
            cursor.execute(
                """
                SELECT 
                    COUNT(id) as total_products,
                    COALESCE(SUM(quantity), 0) as total_quantity,
                    COALESCE(SUM(quantity * price), 0.0) as total_value
                FROM products
                """
            )
            overall = dict(cursor.fetchone())
            
            # Low stock items count
            cursor.execute("SELECT COUNT(id) FROM products WHERE quantity <= reorder_level")
            overall['low_stock_count'] = cursor.fetchone()[0]
            
            # Total transactions
            cursor.execute("SELECT COUNT(id) FROM transactions")
            overall['total_transactions'] = cursor.fetchone()[0]
            
            # Category breakdown
            cursor.execute(
                """
                SELECT 
                    category,
                    COUNT(id) as product_count,
                    COALESCE(SUM(quantity), 0) as total_stock,
                    COALESCE(SUM(quantity * price), 0.0) as total_value
                FROM products
                GROUP BY category
                ORDER BY total_value DESC
                """
            )
            category_breakdown = [dict(row) for row in cursor.fetchall()]
            overall['categories'] = category_breakdown
            
            return overall
    except sqlite3.Error as e:
        logger.error(f"Database error during inventory summary: {e}", exc_info=True)
        raise RuntimeError("An error occurred while generating the inventory summary dashboard.")

def get_transaction_history(limit: int = 50, db_path=None) -> list:
    """
    Retrieves the transaction logs joined with product details.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info(f"Retrieving Transaction History (limit={limit})")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    t.timestamp,
                    p.sku,
                    p.name,
                    t.transaction_type,
                    t.quantity,
                    t.notes
                FROM transactions t
                JOIN products p ON t.product_id = p.id
                ORDER BY t.timestamp DESC, t.id DESC
                LIMIT ?
                """,
                (limit,)
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving transactions: {e}", exc_info=True)
        raise RuntimeError("An error occurred while retrieving transaction history.")
