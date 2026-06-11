import sqlite3
from inventory_manager.database import get_db_connection
from inventory_manager.logger import logger
def add_product(sku: str, name: str, description: str, category: str, 
                price: float, quantity: int, reorder_level: int, db_path=None) -> bool:
    """
    Inserts a new product into the database.
    Normalizes SKU to uppercase and Category to Title Case before saving.
    Creates an initial transaction record if the starting quantity is greater than zero.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    
    # Normalize input fields for database consistency
    sku = sku.strip().upper()
    category = category.strip().title()
    name = name.strip()
    if description:
        description = description.strip()
    logger.info(f"Attempting to add product SKU: {sku}, Name: {name}")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            
            # Insert product
            cursor.execute(
                """
                INSERT INTO products (sku, name, description, category, price, quantity, reorder_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sku, name, description, category, price, quantity, reorder_level)
            )
            product_id = cursor.lastrowid
            
            # If initial quantity > 0, log an initial IN transaction
            if quantity > 0:
                cursor.execute(
                    """
                    INSERT INTO transactions (product_id, transaction_type, quantity, notes)
                    VALUES (?, 'IN', ?, 'Initial stock setup')
                    """,
                    (product_id, quantity)
                )
                
            conn.commit()
            logger.info(f"Product SKU {sku} added successfully (ID: {product_id}).")
            return True
            
    except sqlite3.IntegrityError as e:
        logger.warning(f"Failed to add product SKU {sku}: SKU already exists. Error: {e}")
        raise ValueError(f"A product with SKU '{sku}' already exists.")
    except sqlite3.Error as e:
        logger.error(f"Database error when adding product SKU {sku}: {e}", exc_info=True)
        raise RuntimeError("An error occurred while saving the product to the database.")
def get_product_by_sku(sku: str, db_path=None):
    """
    Retrieves a product record by its SKU.
    Returns sqlite3.Row if found, or None if not found.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE sku = ?", (sku,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Database error when fetching product by SKU {sku}: {e}", exc_info=True)
        raise RuntimeError("An error occurred while fetching product details.")
def update_stock(sku: str, quantity_change: int, transaction_type: str, notes: str, db_path=None) -> bool:
    """
    Updates stock quantity of an existing product (positive for stock-in, negative for stock-out).
    Adds a record to the transaction history.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info(f"Attempting stock update for SKU {sku}: change={quantity_change}, type={transaction_type}")
    if transaction_type not in ('IN', 'OUT', 'ADJUST'):
        raise ValueError("Invalid transaction type. Must be 'IN', 'OUT', or 'ADJUST'.")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            
            # Check if product exists and get its current quantity and ID
            cursor.execute("SELECT id, quantity, name FROM products WHERE sku = ?", (sku,))
            product = cursor.fetchone()
            
            if not product:
                logger.warning(f"Stock update failed: Product SKU {sku} not found.")
                raise ValueError(f"Product with SKU '{sku}' does not exist.")
                
            product_id = product['id']
            current_qty = product['quantity']
            product_name = product['name']
            
            # Calculate new quantity
            new_qty = current_qty + quantity_change
            if new_qty < 0:
                logger.warning(f"Stock update failed for SKU {sku}: Insufficient stock. Current: {current_qty}, Requested change: {quantity_change}")
                raise ValueError(
                    f"Insufficient stock for '{product_name}' ({sku}). Current stock: {current_qty}. Cannot decrease by {abs(quantity_change)}."
                )
            
            # Update product quantity
            cursor.execute(
                "UPDATE products SET quantity = ? WHERE id = ?",
                (new_qty, product_id)
            )
            
            # Insert transaction record
            cursor.execute(
                """
                INSERT INTO transactions (product_id, transaction_type, quantity, notes)
                VALUES (?, ?, ?, ?)
                """,
                (product_id, transaction_type, abs(quantity_change), notes)
            )
            
            conn.commit()
            logger.info(f"Stock updated for SKU {sku}. New Quantity: {new_qty}. Transaction logged.")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Database error during stock update for SKU {sku}: {e}", exc_info=True)
        raise RuntimeError("An error occurred while updating stock in the database.")
def delete_product(sku: str, db_path=None) -> bool:
    """
    Deletes a product by its SKU.
    Cascades transaction history deletion automatically (enabled by SQLite ON DELETE CASCADE).
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info(f"Attempting to delete product SKU: {sku}")
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            
            # Check if product exists first
            cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
            product = cursor.fetchone()
            if not product:
                logger.warning(f"Delete failed: Product SKU {sku} not found.")
                raise ValueError(f"Product with SKU '{sku}' does not exist.")
                
            # Perform deletion
            cursor.execute("DELETE FROM products WHERE sku = ?", (sku,))
            conn.commit()
            logger.info(f"Product SKU {sku} deleted successfully.")
            return True
            
    except sqlite3.Error as e:
        logger.error(f"Database error when deleting product SKU {sku}: {e}", exc_info=True)
        raise RuntimeError("An error occurred while deleting the product from the database.")
def search_products(search_term: str, db_path=None) -> list:
    """
    Searches products by SKU, Name, or Category using partial matching.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    logger.info(f"Searching products with term: '{search_term}'")
    
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            like_term = f"%{search_term}%"
            cursor.execute(
                """
                SELECT sku, name, category, price, quantity, reorder_level 
                FROM products 
                WHERE sku LIKE ? OR name LIKE ? OR category LIKE ?
                ORDER BY category, name
                """,
                (like_term, like_term, like_term)
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error searching products: {e}", exc_info=True)
        raise RuntimeError("An error occurred while searching for products.")
def get_all_products(db_path=None) -> list:
    """
    Retrieves all products from the database.
    """
    db_kwargs = {"db_path": db_path} if db_path else {}
    try:
        with get_db_connection(**db_kwargs) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sku, name, category, price, quantity, reorder_level 
                FROM products 
                ORDER BY category, name
                """
            )
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error retrieving all products: {e}", exc_info=True)
        raise RuntimeError("An error occurred while retrieving products.")

