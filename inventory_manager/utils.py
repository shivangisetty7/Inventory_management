import re

# ANSI Escape Sequences for Terminal Styling
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text: str, color: str) -> str:
    """Wraps text with ANSI escape sequence for coloring."""
    return f"{color}{text}{Colors.RESET}"

def clear_screen():
    """Clears the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Validators ---

def validate_sku(sku: str) -> bool:
    """
    SKUs must be alphanumeric (plus hyphens/underscores), uppercase, between 3 and 15 characters.
    """
    pattern = r"^[A-Z0-9\-_]{3,15}$"
    return bool(re.match(pattern, sku))

def validate_price(price_str: str) -> float:
    """
    Validates and converts price string. Must be a float >= 0.
    Raises ValueError with descriptive message if invalid.
    """
    try:
        price = float(price_str)
        if price < 0:
            raise ValueError("Price cannot be negative.")
        return price
    except ValueError as e:
        if "negative" in str(e):
            raise e
        raise ValueError("Price must be a valid number.")

def validate_quantity(qty_str: str) -> int:
    """
    Validates and converts quantity string. Must be an integer >= 0.
    Raises ValueError with descriptive message if invalid.
    """
    try:
        qty = int(qty_str)
        if qty < 0:
            raise ValueError("Quantity cannot be negative.")
        return qty
    except ValueError as e:
        if "negative" in str(e):
            raise e
        raise ValueError("Quantity must be a valid whole number.")

def validate_reorder_level(reorder_str: str) -> int:
    """
    Validates and converts reorder level string. Must be an integer >= 0.
    Raises ValueError if invalid.
    """
    try:
        level = int(reorder_str)
        if level < 0:
            raise ValueError("Reorder level cannot be negative.")
        return level
    except ValueError as e:
        if "negative" in str(e):
            raise e
        raise ValueError("Reorder level must be a valid whole number.")

def validate_non_empty(val: str, field_name: str) -> str:
    """
    Validates that the string is not empty. Returns the stripped string.
    Raises ValueError if empty.
    """
    stripped = val.strip()
    if not stripped:
        raise ValueError(f"{field_name} cannot be empty.")
    return stripped


# --- ASCII Table Formatter ---

def create_ascii_table(headers: list, rows: list, alignments: list = None) -> str:
    """
    Generates a beautifully formatted ASCII table.
    
    :param headers: List of column header names.
    :param rows: List of lists (or tuples) containing row data.
    :param alignments: List of alignments per column ('L' for Left, 'R' for Right). Defaults to 'L'.
    :return: String representation of the table.
    """
    if not headers:
        return ""
    
    num_cols = len(headers)
    if alignments is None:
        alignments = ['L'] * num_cols
    elif len(alignments) < num_cols:
        alignments += ['L'] * (num_cols - len(alignments))

    # Convert all cell values to strings
    string_rows = []
    for row in rows:
        string_rows.append([str(cell) if cell is not None else "" for cell in row])

    # Find the maximum width for each column (minimum width of 3)
    col_widths = [len(h) for h in headers]
    for row in string_rows:
        for i in range(num_cols):
            col_widths[i] = max(col_widths[i], len(row[i]))

    # Helper to build separator line (e.g. +------+-----+------+ )
    border_line = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

    # Build Header Row
    header_cells = []
    for i, h in enumerate(headers):
        w = col_widths[i]
        # Align header
        if alignments[i] == 'R':
            cell_val = h.rjust(w)
        elif alignments[i] == 'C':
            cell_val = h.center(w)
        else:
            cell_val = h.ljust(w)
        header_cells.append(f" {cell_val} ")
    header_row = "|" + "|".join(header_cells) + "|"

    # Build Data Rows
    data_rows = []
    for row in string_rows:
        row_cells = []
        for i, cell in enumerate(row):
            w = col_widths[i]
            if alignments[i] == 'R':
                cell_val = cell.rjust(w)
            elif alignments[i] == 'C':
                cell_val = cell.center(w)
            else:
                cell_val = cell.ljust(w)
            row_cells.append(f" {cell_val} ")
        data_rows.append("|" + "|".join(row_cells) + "|")

    # Combine everything
    table_lines = [
        border_line,
        header_row,
        border_line,
    ]
    if data_rows:
        table_lines.extend(data_rows)
    else:
        # If empty rows, print empty table indicator
        empty_msg = "No data available".center(sum(col_widths) + (num_cols * 3) - 1)
        table_lines.append(f" {empty_msg} ")
    
    table_lines.append(border_line)
    return "\n".join(table_lines)
