import sqlite3
import os

DB_NAME = "transactions.db"

def get_db_path():
    """
    Returns the path to the database.
    On Android, we want to store it in the app's private files directory.
    On local PC/Windows, store it in the current directory.
    """
    # Check if we are running on Android
    # Kivy sets the 'ANDROID_ARGUMENT' env var
    if 'ANDROID_ARGUMENT' in os.environ:
        from android.storage import app_storage_path
        return os.path.join(app_storage_path(), DB_NAME)
    return DB_NAME

def init_db():
    """
    Initializes the SQLite database tables.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        type TEXT NOT NULL,          -- DEBIT or CREDIT
        amount REAL NOT NULL,
        raw_merchant TEXT NOT NULL,
        resolved_merchant TEXT NOT NULL, -- The user-friendly name
        category TEXT NOT NULL,      -- Groceries, Food, Rent, etc.
        sms_body TEXT,
        is_pending_mapping INTEGER DEFAULT 0  -- 1 if merchant is unknown
    )
    """)
    
    # 2. Merchant Dictionary Table
    # Resolves raw clean names to custom display names and categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS merchant_dictionary (
        raw_name TEXT PRIMARY KEY,
        custom_name TEXT NOT NULL,
        category TEXT NOT NULL
    )
    """)
    
    conn.commit()
    
    # Pre-populate default dictionary if empty
    cursor.execute("SELECT COUNT(*) FROM merchant_dictionary")
    if cursor.fetchone()[0] == 0:
        preseed_defaults(cursor)
        conn.commit()
        
    conn.close()

def preseed_defaults(cursor):
    """
    Pre-populates the merchant dictionary with common national brands.
    """
    defaults = [
        # Food & Dining
        ("ZOMATO", "Zomato", "Food"),
        ("SWIGGY", "Swiggy", "Food"),
        ("DOMINOS", "Dominos Pizza", "Food"),
        ("MCDONALDS", "McDonalds", "Food"),
        ("STARBUCKS", "Starbucks", "Food"),
        
        # Utilities & Bills
        ("JIO", "Reliance Jio", "Bills"),
        ("AIRTEL", "Airtel", "Bills"),
        ("VI", "Vodafone Idea", "Bills"),
        ("BESCOM", "Electricity Bill", "Bills"),
        ("NETFLIX", "Netflix", "Bills"),
        ("SPOTIFY", "Spotify", "Bills"),
        
        # Shopping / E-commerce
        ("AMAZON", "Amazon", "Shopping"),
        ("FLIPKART", "Flipkart", "Shopping"),
        ("MYNTRA", "Myntra", "Shopping"),
        
        # Groceries
        ("BLINKIT", "Blinkit", "Groceries"),
        ("ZEPTO", "Zepto", "Groceries"),
        ("BIGBASKET", "BigBasket", "Groceries"),
        ("INSTAMART", "Swiggy Instamart", "Groceries"),
        
        # Transport & Travel
        ("UBER", "Uber Cab", "Travel"),
        ("OLA", "Ola Cabs", "Travel"),
        ("RAPIDO", "Rapido Bike", "Travel"),
        ("IRCTC", "Railway Ticket", "Travel"),
        ("MAKEMYTRIP", "MakeMyTrip", "Travel"),
    ]
    cursor.executemany("""
    INSERT INTO merchant_dictionary (raw_name, custom_name, category)
    VALUES (?, ?, ?)
    """, defaults)

def add_transaction(parsed_data, sms_body=""):
    """
    Saves a parsed transaction. Checks against the dictionary to resolve categories.
    If the merchant is new/unrecognized, flags it as pending user input.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    raw_merchant = parsed_data["merchant"]
    
    # Look up in the dictionary
    cursor.execute("""
    SELECT custom_name, category FROM merchant_dictionary 
    WHERE raw_name = ?
    """, (raw_merchant,))
    row = cursor.fetchone()
    
    if row:
        resolved_merchant = row[0]
        category = row[1]
        is_pending = 0
    else:
        # Unknown merchant! Default to same name and 'Uncategorized'
        resolved_merchant = raw_merchant
        category = "Uncategorized"
        is_pending = 1
        
    cursor.execute("""
    INSERT INTO transactions (timestamp, type, amount, raw_merchant, resolved_merchant, category, sms_body, is_pending_mapping)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        parsed_data["timestamp"],
        parsed_data["type"],
        parsed_data["amount"],
        raw_merchant,
        resolved_merchant,
        category,
        sms_body,
        is_pending
    ))
    
    conn.commit()
    conn.close()
    
    return is_pending

def update_merchant_mapping(raw_name, custom_name, category):
    """
    Updates the mapping for a merchant.
    Also updates all past and pending transactions for this merchant.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Insert/Replace mapping in dictionary
    cursor.execute("""
    INSERT OR REPLACE INTO merchant_dictionary (raw_name, custom_name, category)
    VALUES (?, ?, ?)
    """, (raw_name, custom_name, category))
    
    # 2. Update existing transactions with this raw merchant name
    cursor.execute("""
    UPDATE transactions 
    SET resolved_merchant = ?, category = ?, is_pending_mapping = 0
    WHERE raw_merchant = ?
    """, (custom_name, category, raw_name))
    
    conn.commit()
    conn.close()

def get_recent_transactions(limit=20):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM transactions 
    ORDER BY timestamp DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_pending_mappings():
    """
    Gets all unique raw merchants that are currently pending categorization.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
    SELECT DISTINCT raw_merchant, resolved_merchant, amount 
    FROM transactions 
    WHERE is_pending_mapping = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_category_spending():
    """
    Calculates total debited amount per category.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT category, SUM(amount) 
    FROM transactions 
    WHERE type = 'DEBIT'
    GROUP BY category
    ORDER BY SUM(amount) DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

if __name__ == "__main__":
    # Test DB ops locally
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    init_db()
    
    print("Database initialized.")
    # Test insert
    test_parsed = {
        "success": True,
        "type": "DEBIT",
        "amount": 250.0,
        "merchant": "ZOMATO",
        "timestamp": "2026-05-28 12:00:00"
    }
    is_pending = add_transaction(test_parsed, "SMS body content")
    print(f"Added Zomato transaction. Pending status: {is_pending}")
    
    test_unknown = {
        "success": True,
        "type": "DEBIT",
        "amount": 100.0,
        "merchant": "RAMESH KUMAR",
        "timestamp": "2026-05-28 12:05:00"
    }
    is_pending = add_transaction(test_unknown, "Paid Rs. 100 to RAMESH KUMAR")
    print(f"Added Ramesh transaction. Pending status: {is_pending}")
    
    print("Recent transactions:")
    print(get_recent_transactions())
    
    print("\nPending mappings:")
    print(get_pending_mappings())
    
    print("\nResolving Ramesh mapping to Groceries...")
    update_merchant_mapping("RAMESH KUMAR", "Ramesh Kirana Store", "Groceries")
    
    print("\nRecent transactions after update:")
    print(get_recent_transactions())
    print("\nPending mappings after update:")
    print(get_pending_mappings())
    
    print("\nCategory spending analysis:")
    print(get_category_spending())
