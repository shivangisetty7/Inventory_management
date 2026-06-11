import sys
from inventory_manager.database import initialize_database
from inventory_manager import core, reports, utils
from inventory_manager.utils import Colors, colorize, clear_screen
from inventory_manager.logger import logger

class OperationCancelled(Exception):
    """Exception raised when a user wants to cancel the current operation and return to menu."""
    pass

def prompt_input(prompt_text: str, validator=None, default=None, allow_cancel: bool = True):
    """
    Prompts the user for input, validates it, and handles cancelling or defaults.
    """
    while True:
        try:
            suffix = " (type 'back' to cancel)" if allow_cancel else ""
            default_suffix = f" [{default}]" if default is not None else ""
            
            raw_input = input(f"{prompt_text}{default_suffix}{suffix}: ").strip()
            
            if allow_cancel and raw_input.lower() == 'back':
                raise OperationCancelled()
                
            if not raw_input and default is not None:
                return default
                
            if validator:
                return validator(raw_input)
            else:
                if not raw_input:
                    print(colorize("Error: Input cannot be empty.", Colors.FAIL))
                    continue
                return raw_input
        except ValueError as e:
            print(colorize(f"Error: {e}", Colors.FAIL))

def display_banner():
    """Prints a professional dashboard banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}====================================================================
  ___ _   _ _   _ _____ _   _ _____ ___  ______   __  ___ _____  ___ 
 |_ _| \ | | | | |  ___| \ | |_   _/ _ \ | ___ \  \ \/ / /  ___|/ _ \ 
  | ||  \| | | | | |__ |  \| | | |/ /_\ \| |_/ /   \  /  \ `--./ /_\ \\
  | || . ` | | | |  __|| . ` | | ||  _  ||    /    /  \   `--. \  _  |
 _| || |\  \ \_/ / |___| |\  | | || | | || |\ \   / /\ \ /\__/ / | | |
 \___/\_| \_/\___/\____/\_| \_/ \_/\_| |_/\_| \_| \/_/\_(_)____/\_| |_/
                       INVENTORY MANAGEMENT SYSTEM
===================================================================={Colors.RESET}
    """
    print(banner)

def display_menu():
    """Prints the main interactive menu."""
    print(colorize(f"\n{Colors.BOLD}--- MAIN MENU ---{Colors.RESET}", Colors.BLUE))
    print(f"1. {colorize('Add Product', Colors.CYAN)}")
    print(f"2. {colorize('View Products', Colors.CYAN)}")
    print(f"3. {colorize('Update Stock (Stock In/Out)', Colors.CYAN)}")
    print(f"4. {colorize('Delete Product', Colors.CYAN)}")
    print(f"5. {colorize('Search Product', Colors.CYAN)}")
    print(f"6. {colorize('Low Stock Report', Colors.CYAN)}")
    print(f"7. {colorize('Inventory Summary Dashboard', Colors.CYAN)}")
    print(f"8. {colorize('Transaction History', Colors.CYAN)}")
    print(f"9. {colorize('Exit', Colors.FAIL)}")
    print(colorize("-----------------", Colors.BLUE))

def ui_add_product():
    """UI flow to add a new product."""
    print(colorize(f"\n{Colors.BOLD}=== ADD NEW PRODUCT ==={Colors.RESET}", Colors.BLUE))
    try:
        sku = prompt_input(
            "Enter Product SKU (e.g. PRD-101, uppercase, 3-15 chars)", 
            validator=lambda val: val.upper() if utils.validate_sku(val.upper()) else (_ for _ in ()).throw(ValueError("SKU must be 3-15 alphanumeric chars/hyphens."))
        )
        
        # Check if already exists to save user from inputting everything
        existing = core.get_product_by_sku(sku)
        if existing:
            print(colorize(f"Error: A product with SKU '{sku}' already exists ({existing['name']}).", Colors.FAIL))
            return

        name = prompt_input("Enter Product Name", validator=lambda val: utils.validate_non_empty(val, "Name"))
        description = input("Enter Description (Optional): ").strip()
        category = prompt_input("Enter Category", validator=lambda val: utils.validate_non_empty(val, "Category"))
        price = prompt_input("Enter Unit Price (₹)", validator=utils.validate_price)
        quantity = prompt_input("Enter Initial Quantity", validator=utils.validate_quantity, default=0)
        reorder_level = prompt_input("Enter Reorder Threshold Level", validator=utils.validate_reorder_level, default=10)

        # Execute add
        core.add_product(sku, name, description, category, price, quantity, reorder_level)
        print(colorize(f"\nSuccess: Product '{name}' ({sku}) added successfully!", Colors.GREEN))
        
    except OperationCancelled:
        print(colorize("\nOperation cancelled. Returning to main menu.", Colors.WARNING))

def ui_view_products():
    """UI flow to view all products."""
    print(colorize(f"\n{Colors.BOLD}=== ALL PRODUCTS INVENTORY ==={Colors.RESET}", Colors.BLUE))
    try:
        products = core.get_all_products()
        headers = ["SKU", "Product Name", "Category", "Price (₹)", "Quantity", "Reorder Lvl", "Status"]
        rows = []
        
        for p in products:
            status = "GOOD"
            if p["quantity"] == 0:
                status = colorize("OUT OF STOCK", Colors.FAIL)
            elif p["quantity"] <= p["reorder_level"]:
                status = colorize("LOW STOCK", Colors.WARNING)
            else:
                status = colorize("OK", Colors.GREEN)
                
            rows.append([
                p["sku"],
                p["name"],
                p["category"],
                f"{p['price']:.2f}",
                p["quantity"],
                p["reorder_level"],
                status
            ])
            
        table = utils.create_ascii_table(headers, rows, alignments=['L', 'L', 'L', 'R', 'R', 'R', 'L'])
        print(table)
    except Exception as e:
        print(colorize(f"Error retrieving products: {e}", Colors.FAIL))

def ui_update_stock():
    """UI flow to record stock transaction (IN or OUT or ADJUST)."""
    print(colorize(f"\n{Colors.BOLD}=== UPDATE STOCK (TRANSACTION) ==={Colors.RESET}", Colors.BLUE))
    try:
        sku = prompt_input("Enter Product SKU", validator=lambda val: val.upper())
        product = core.get_product_by_sku(sku)
        if not product:
            print(colorize(f"Error: Product with SKU '{sku}' not found.", Colors.FAIL))
            return
            
        print(f"\nProduct Found: {colorize(product['name'], Colors.BOLD)}")
        print(f"Current Quantity: {colorize(str(product['quantity']), Colors.GREEN if product['quantity'] > product['reorder_level'] else Colors.WARNING)}")
        
        print("\nSelect Transaction Type:")
        print("1. Stock In (Receive items)")
        print("2. Stock Out (Sales / Dispatch)")
        print("3. Stock Adjustment (Inventory audit correction)")
        
        choice = prompt_input("Enter choice (1-3)", validator=lambda x: int(x) if x in ('1', '2', '3') else (_ for _ in ()).throw(ValueError("Choose 1, 2, or 3.")))
        
        qty_change = prompt_input("Enter quantity amount", validator=utils.validate_quantity)
        notes = prompt_input("Enter reference note/reason", validator=lambda val: utils.validate_non_empty(val, "Notes"))
        
        if choice == 1:
            tx_type = "IN"
            actual_change = qty_change
        elif choice == 2:
            tx_type = "OUT"
            actual_change = -qty_change
        else:
            tx_type = "ADJUST"
            adj_choice = prompt_input("Increase (+) or Decrease (-)? Enter (+/-)", validator=lambda x: x.strip() if x.strip() in ('+', '-') else (_ for _ in ()).throw(ValueError("Enter '+' or '-'.")))
            actual_change = qty_change if adj_choice == '+' else -qty_change
            
        core.update_stock(sku, actual_change, tx_type, notes)
        print(colorize(f"\nSuccess: Stock updated successfully for SKU {sku}.", Colors.GREEN))
        
    except OperationCancelled:
        print(colorize("\nOperation cancelled. Returning to main menu.", Colors.WARNING))
    except ValueError as e:
        print(colorize(f"\nError: {e}", Colors.FAIL))

def ui_delete_product():
    """UI flow to delete a product."""
    print(colorize(f"\n{Colors.BOLD}=== DELETE PRODUCT ==={Colors.RESET}", Colors.BLUE))
    try:
        sku = prompt_input("Enter Product SKU to Delete", validator=lambda val: val.upper())
        product = core.get_product_by_sku(sku)
        if not product:
            print(colorize(f"Error: Product with SKU '{sku}' not found.", Colors.FAIL))
            return
            
        print(colorize(f"\nWARNING: You are about to delete product '{product['name']}' ({sku}).", Colors.FAIL))
        print("This will also delete its transaction history (cascade delete).")
        
        confirm = prompt_input("Are you sure? Type 'YES' to confirm", allow_cancel=True)
        if confirm == 'YES':
            core.delete_product(sku)
            print(colorize(f"\nSuccess: Product '{product['name']}' has been permanently deleted.", Colors.GREEN))
        else:
            print(colorize("\nDeletion cancelled. Product was not deleted.", Colors.WARNING))
            
    except OperationCancelled:
        print(colorize("\nOperation cancelled. Returning to main menu.", Colors.WARNING))

def ui_search_product():
    """UI flow to search products."""
    print(colorize(f"\n{Colors.BOLD}=== SEARCH INVENTORY ==={Colors.RESET}", Colors.BLUE))
    try:
        search_term = prompt_input("Enter search term (SKU, Name, or Category)")
        results = core.search_products(search_term)
        
        print(colorize(f"\nSearch Results for '{search_term}' ({len(results)} found):", Colors.BOLD))
        
        headers = ["SKU", "Product Name", "Category", "Price (₹)", "Quantity", "Reorder Lvl"]
        rows = []
        for p in results:
            rows.append([
                p["sku"],
                p["name"],
                p["category"],
                f"{p['price']:.2f}",
                p["quantity"],
                p["reorder_level"]
            ])
            
        table = utils.create_ascii_table(headers, rows, alignments=['L', 'L', 'L', 'R', 'R', 'R'])
        print(table)
    except OperationCancelled:
         print(colorize("\nOperation cancelled. Returning to main menu.", Colors.WARNING))

def ui_low_stock_report():
    """UI flow to display products below reorder thresholds."""
    print(colorize(f"\n{Colors.BOLD}=== LOW STOCK REPORT ==={Colors.RESET}", Colors.BLUE))
    try:
        results = reports.get_low_stock_report()
        print(colorize(f"Products requiring reorder ({len(results)} items):", Colors.WARNING))
        
        headers = ["SKU", "Product Name", "Category", "Current Stock", "Reorder Threshold", "Urgency"]
        rows = []
        for p in results:
            urgency = colorize("CRITICAL (0 stock)", Colors.FAIL) if p["quantity"] == 0 else colorize("LOW", Colors.WARNING)
            rows.append([
                p["sku"],
                p["name"],
                p["category"],
                p["quantity"],
                p["reorder_level"],
                urgency
            ])
            
        table = utils.create_ascii_table(headers, rows, alignments=['L', 'L', 'L', 'R', 'R', 'L'])
        print(table)
    except Exception as e:
        print(colorize(f"Error generating low stock report: {e}", Colors.FAIL))

def ui_dashboard():
    """UI flow to view inventory statistics and summary."""
    print(colorize(f"\n{Colors.BOLD}=== INVENTORY SUMMARY DASHBOARD ==={Colors.RESET}", Colors.BLUE))
    try:
        stats = reports.get_inventory_summary()
        
        # Display overall statistics
        print(f"┌────────────────────────────────────────────────────────┐")
        print(f"│ {colorize('OVERALL METRICS', Colors.BOLD).ljust(63)} │")
        print(f"├────────────────────────────────────────────────────────┤")
        print(f"│ Total Unique Products  : {str(stats['total_products']).ljust(29)} │")
        print(f"│ Total Items in Stock   : {str(stats['total_quantity']).ljust(29)} │")
        print(f"│ Total Valuation        : ₹{f"{stats['total_value']:,.2f}".ljust(28)} │")
        print(f"│ Low Stock Alerts       : {colorize(str(stats['low_stock_count']), Colors.FAIL if stats['low_stock_count'] > 0 else Colors.GREEN).ljust(38)} │")
        print(f"│ Total Transactions Run : {str(stats['total_transactions']).ljust(29)} │")
        print(f"└────────────────────────────────────────────────────────┘")

        # Category distribution
        print(colorize(f"\nCategory Distribution:", Colors.BOLD))
        cat_headers = ["Category", "Unique Products", "Total In-Stock Items", "Valuation (₹)"]
        cat_rows = []
        for c in stats['categories']:
            cat_rows.append([
                c['category'],
                c['product_count'],
                c['total_stock'],
                f"{c['total_value']:.2f}"
            ])
        cat_table = utils.create_ascii_table(cat_headers, cat_rows, alignments=['L', 'R', 'R', 'R'])
        print(cat_table)
        
    except Exception as e:
         print(colorize(f"Error loading dashboard: {e}", Colors.FAIL))

def ui_transaction_history():
    """UI flow to view system transaction audit logs."""
    print(colorize(f"\n{Colors.BOLD}=== TRANSACTION AUDIT HISTORY ==={Colors.RESET}", Colors.BLUE))
    try:
        limit = prompt_input("Enter limit of logs to view", validator=utils.validate_quantity, default=25)
        txs = reports.get_transaction_history(limit=limit)
        
        print(colorize(f"\nRecent transactions (showing up to {limit}):", Colors.BOLD))
        headers = ["Timestamp (UTC)", "SKU", "Product Name", "Type", "Qty", "Notes/Reference"]
        rows = []
        
        for t in txs:
            # Color transaction type
            tx_type = t["transaction_type"]
            if tx_type == "IN":
                colored_type = colorize("IN", Colors.GREEN)
            elif tx_type == "OUT":
                colored_type = colorize("OUT", Colors.FAIL)
            else:
                colored_type = colorize("ADJUST", Colors.WARNING)
                
            rows.append([
                t["timestamp"],
                t["sku"],
                t["name"],
                colored_type,
                t["quantity"],
                t["notes"]
            ])
            
        table = utils.create_ascii_table(headers, rows, alignments=['L', 'L', 'L', 'C', 'R', 'L'])
        print(table)
        
    except OperationCancelled:
        print(colorize("\nOperation cancelled. Returning to main menu.", Colors.WARNING))
    except Exception as e:
        print(colorize(f"Error loading transactions: {e}", Colors.FAIL))

def main():
    """Main program entry point."""
    # Ensure tables exist
    try:
        initialize_database()
    except Exception as e:
        print(colorize(f"CRITICAL: Failed to initialize application database: {e}", Colors.FAIL))
        sys.exit(1)
        
    clear_screen()
    display_banner()
    
    while True:
        display_menu()
        choice = input("Select an option (1-9): ").strip()
        
        if choice == '1':
            ui_add_product()
        elif choice == '2':
            ui_view_products()
        elif choice == '3':
            ui_update_stock()
        elif choice == '4':
            ui_delete_product()
        elif choice == '5':
            ui_search_product()
        elif choice == '6':
            ui_low_stock_report()
        elif choice == '7':
            ui_dashboard()
        elif choice == '8':
            ui_transaction_history()
        elif choice == '9':
            print(colorize("\nThank you for using the Inventory Management System! Exiting...", Colors.GREEN))
            break
        elif not choice:
            continue
        else:
            print(colorize("Invalid selection! Please enter a number between 1 and 9.", Colors.FAIL))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(colorize("\n\nApplication interrupted by user. Exiting...", Colors.FAIL))
        sys.exit(0)
