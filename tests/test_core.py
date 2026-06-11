import unittest
import sqlite3
import os

from inventory_manager.database import initialize_database, get_db_connection
from inventory_manager import core, reports

class TestInventoryManager(unittest.TestCase):
    def setUp(self):
        # Use a temporary file database for tests
        self.db_path = "test_inventory.db"
        # Clean up any leftover file before starting
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        initialize_database(self.db_path)

    def tearDown(self):
        # Remove the temporary test database
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_add_product_success(self):
        # Add a new product
        success = core.add_product(
            sku="PROD-001",
            name="Test Widget",
            description="A high-quality test widget",
            category="Widgets",
            price=19.99,
            quantity=10,
            reorder_level=5,
            db_path=self.db_path
        )
        self.assertTrue(success)

        # Retrieve and verify details
        product = core.get_product_by_sku("PROD-001", db_path=self.db_path)
        self.assertIsNotNone(product)
        self.assertEqual(product["name"], "Test Widget")
        self.assertEqual(product["price"], 19.99)
        self.assertEqual(product["quantity"], 10)

        # Verify initial transaction history
        txs = reports.get_transaction_history(db_path=self.db_path)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["sku"], "PROD-001")
        self.assertEqual(txs[0]["transaction_type"], "IN")
        self.assertEqual(txs[0]["quantity"], 10)

    def test_add_product_duplicate_sku(self):
        # Add first product
        core.add_product(
            sku="PROD-001",
            name="Widget A",
            description="First widget",
            category="Widgets",
            price=10.0,
            quantity=5,
            reorder_level=2,
            db_path=self.db_path
        )
        
        # Add second product with the same SKU (should raise ValueError)
        with self.assertRaises(ValueError) as context:
            core.add_product(
                sku="PROD-001",
                name="Widget B",
                description="Second widget",
                category="Widgets",
                price=12.0,
                quantity=3,
                reorder_level=1,
                db_path=self.db_path
            )
        self.assertIn("already exists", str(context.exception))

    def test_update_stock_in_and_out(self):
        core.add_product(
            sku="PROD-001",
            name="Test Widget",
            description="Desc",
            category="Widgets",
            price=15.0,
            quantity=10,
            reorder_level=5,
            db_path=self.db_path
        )

        # Stock-in 5 items
        core.update_stock("PROD-001", 5, "IN", "Restocking supply", db_path=self.db_path)
        prod = core.get_product_by_sku("PROD-001", db_path=self.db_path)
        self.assertEqual(prod["quantity"], 15)

        # Stock-out 7 items (passed as negative number for change, but absolute is logged in transaction)
        core.update_stock("PROD-001", -7, "OUT", "Customer purchase", db_path=self.db_path)
        prod = core.get_product_by_sku("PROD-001", db_path=self.db_path)
        self.assertEqual(prod["quantity"], 8)

        # Try to stock-out more than available (should raise ValueError)
        with self.assertRaises(ValueError) as context:
            core.update_stock("PROD-001", -10, "OUT", "Excessive purchase", db_path=self.db_path)
        self.assertIn("Insufficient stock", str(context.exception))

    def test_delete_product_cascade(self):
        core.add_product(
            sku="PROD-001",
            name="Test Widget",
            description="Desc",
            category="Widgets",
            price=15.0,
            quantity=10,
            reorder_level=5,
            db_path=self.db_path
        )

        # Delete product
        success = core.delete_product("PROD-001", db_path=self.db_path)
        self.assertTrue(success)

        # Confirm product is gone
        prod = core.get_product_by_sku("PROD-001", db_path=self.db_path)
        self.assertIsNone(prod)

        # Confirm transactions were cascade-deleted
        txs = reports.get_transaction_history(db_path=self.db_path)
        self.assertEqual(len(txs), 0)

    def test_search_products(self):
        core.add_product("WID-001", "Alpha Widget", "", "Widgets", 5.0, 10, 2, db_path=self.db_path)
        core.add_product("GAD-002", "Beta Gadget", "", "Electronics", 15.0, 5, 2, db_path=self.db_path)
        core.add_product("WID-003", "Gamma Item", "", "Widgets", 8.0, 2, 1, db_path=self.db_path)

        # Search by SKU keyword
        results = core.search_products("WID", db_path=self.db_path)
        self.assertEqual(len(results), 2)
        skus = [r["sku"] for r in results]
        self.assertIn("WID-001", skus)
        self.assertIn("WID-003", skus)

        # Search by Name keyword
        results = core.search_products("Beta", db_path=self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Beta Gadget")

        # Search by Category keyword
        results = core.search_products("Widgets", db_path=self.db_path)
        self.assertEqual(len(results), 2)

    def test_reports_and_dashboard(self):
        # Add products - some in low stock state
        # 1. Widgets: SKU WID-01, qty 2, reorder 5 (Low Stock)
        core.add_product("WID-01", "Low Stock Widget", "", "Widgets", 10.0, 2, 5, db_path=self.db_path)
        # 2. Electronics: SKU GAD-01, qty 20, reorder 5 (Good Stock)
        core.add_product("GAD-01", "Good Stock Gadget", "", "Electronics", 20.0, 20, 5, db_path=self.db_path)

        # Verify Low Stock Report
        low_stock = reports.get_low_stock_report(db_path=self.db_path)
        self.assertEqual(len(low_stock), 1)
        self.assertEqual(low_stock[0]["sku"], "WID-01")

        # Verify Dashboard Summary
        summary = reports.get_inventory_summary(db_path=self.db_path)
        self.assertEqual(summary["total_products"], 2)
        self.assertEqual(summary["total_quantity"], 22)
        self.assertEqual(summary["total_value"], (2 * 10.0) + (20 * 20.0))
        self.assertEqual(summary["low_stock_count"], 1)
        self.assertEqual(summary["total_transactions"], 2)

        # Check category breakdown
        categories = {c["category"]: c for c in summary["categories"]}
        self.assertIn("Widgets", categories)
        self.assertEqual(categories["Widgets"]["product_count"], 1)
        self.assertEqual(categories["Widgets"]["total_stock"], 2)
        self.assertEqual(categories["Widgets"]["total_value"], 20.0)

        self.assertIn("Electronics", categories)
        self.assertEqual(categories["Electronics"]["product_count"], 1)
        self.assertEqual(categories["Electronics"]["total_stock"], 20)
        self.assertEqual(categories["Electronics"]["total_value"], 400.0)

if __name__ == "__main__":
    unittest.main()
