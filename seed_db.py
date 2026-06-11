import sqlite3
import os
from inventory_manager.database import initialize_database, get_db_connection
from inventory_manager import core
from inventory_manager.utils import Colors, colorize

def seed_data():
    """Seeds the database with sample products and transactions if it's empty."""
    print(colorize("Checking database for seeding...", Colors.BLUE))
    
    # Ensure database tables exist
    initialize_database()
    
    products_count = 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        products_count = cursor.fetchone()[0]
        
    if products_count > 0:
        print(colorize("Database already contains data. Seeding skipped.", Colors.WARNING))
        return
        
    print(colorize("Database is empty. Seeding sample inventory data...", Colors.GREEN))
    
    # Define sample products
    sample_products = [
        # SKU, Name, Description, Category, Price, Quantity, Reorder
        ("LAP-001", "Lenovo ThinkPad L14", "Business laptop with Intel i7, 16GB RAM, 512GB SSD", "Electronics", 899.99, 12, 5),
        ("MOU-002", "Logitech MX Master 3S", "Ergonomic wireless mouse with silent clicks", "Electronics", 99.99, 3, 10),
        ("DES-003", "Ergonomic Office Desk", "Height-adjustable motorized standing desk, 55x30 inches", "Furniture", 249.50, 0, 3),
        ("MON-004", "Dell 27-Inch 4K Monitor", "IPS UltraSharp monitor with USB-C hub", "Electronics", 349.99, 15, 5),
        ("KEY-005", "Keychron K2 Keyboard", "Wireless mechanical keyboard with Gateron Blue switches", "Electronics", 79.99, 25, 8),
        ("CHA-006", "Mesh Office Task Chair", "High-back mesh chair with lumbar support", "Furniture", 149.00, 2, 5),
        ("NOT-007", "Muji A5 Grid Notebook", "Hardcover spiral grid notebook, 80 sheets", "Stationery", 4.50, 120, 20),
        ("PEN-008", "Pilot G2 Gel Pens (12-pack)", "Fine point black gel ink pens", "Stationery", 12.99, 45, 15),
    ]
    
    # Insert products (initial transaction logs are created automatically inside core.add_product)
    for prod in sample_products:
        core.add_product(
            sku=prod[0],
            name=prod[1],
            description=prod[2],
            category=prod[3],
            price=prod[4],
            quantity=prod[5],
            reorder_level=prod[6]
        )
        print(f"  Added product: {prod[1]} ({prod[0]})")
        
    # Add some subsequent stock movements to create audit history
    extra_transactions = [
        # SKU, change, type, notes
        ("LAP-001", -2, "OUT", "Dispatched 2 laptops to new hires in engineering"),
        ("MOU-002", -8, "OUT", "Sales department order fulfillment"),
        ("MON-004", 5, "IN", "Restock shipment received from supplier"),
        ("KEY-005", -5, "OUT", "Fulfillment for order #100234"),
        ("CHA-006", -1, "OUT", "Showroom model replacement"),
        ("NOT-007", -30, "OUT", "Bulk supply checkout for marketing workshop"),
        ("PEN-008", 20, "IN", "Reordered extra pens for office reception desk"),
        ("MOU-002", 2, "ADJUST", "Inventory audit: corrected discrepancy (+2 found in cabinet)")
    ]
    
    print("\nLogging additional stock transactions...")
    for tx in extra_transactions:
        try:
            core.update_stock(
                sku=tx[0],
                quantity_change=tx[1],
                transaction_type=tx[2],
                notes=tx[3]
            )
            sign = "+" if tx[1] > 0 else ""
            print(f"  Updated stock for {tx[0]}: {sign}{tx[1]} ({tx[2]}) - {tx[3]}")
        except Exception as e:
            print(f"  Error updating stock for {tx[0]}: {e}")
            
    print(colorize("\nDatabase seeding completed successfully!", Colors.GREEN))

if __name__ == "__main__":
    seed_data()
