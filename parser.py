import re
from datetime import datetime

# Regex patterns for common Indian Bank transaction messages
# These cover debit/payment alerts from HDFC, SBI, ICICI, Axis, Paytm, PhonePe, and GPay.
PATTERNS = [
    # Pattern 1: Debited/spent to a merchant (e.g., "Rs. 150 spent on card ... at MERCHANT")
    r"(?i)(?:rs\.?|inr)\s*([\d,]+\.?\d*)\s*(?:spent|debited|paid|transferr?ed|sent)\s*(?:to|at|on)?\s*([^.]+?)(?:\s*on|\s*via|\s*ref|\.|$)",
    
    # Pattern 2: Paid to merchant via UPI (e.g., "Paid Rs. 50 to RAMESH KUMAR. Ref: UPI:12345678")
    r"(?i)paid\s*(?:rs\.?|inr)\s*([\d,]+\.?\d*)\s*to\s*([^.]+?)(?:\.|\s*ref|\s*from|$)",
    
    # Pattern 3: A/c debited (e.g., "A/c ... debited by Rs. 200.00 ... transfer to RAMESH KUMAR")
    r"(?i)debited\s*by\s*(?:rs\.?|inr)\s*([\d,]+\.?\d*).*?transfer\s*(?:to)?\s*([^.]+?)(?:\s*ref|\s*on|$)",
]

def clean_merchant_name(name):
    """
    Cleans up raw merchant strings by removing common noise words,
    extra spaces, transaction IDs, or UPI suffixes.
    """
    if not name:
        return "UNKNOWN"
        
    name = name.strip()
    
    # Remove things like "Ref No...", "UPI Ref...", "VPA...", "ending in..."
    name = re.sub(r"(?i)(?:ref|upi|vpa|txn|transaction|acc|a/c|card|ending|info|using).*$", "", name)
    
    # Remove trailing non-alphanumeric chars except space
    name = re.sub(r"[^\w\s\.-]", "", name)
    
    # Replace multiple spaces with a single space
    name = re.sub(r"\s+", " ", name)
    
    name = name.strip()
    
    # If cleaned name is too short or empty, return default
    if len(name) < 2:
        return "UNKNOWN"
        
    return name.upper()

def parse_sms(sms_body):
    """
    Parses an incoming SMS body to extract transaction details.
    Returns a dict with success=True and details, or success=False if not a transaction.
    """
    # Quick filter: If it doesn't contain credit/debit indicators or currency, skip it
    if not re.search(r"(?i)rs\.?|inr", sms_body):
        return {"success": False, "reason": "Not a financial SMS"}
        
    # Determine type (Debit vs Credit)
    is_credit = bool(re.search(r"(?i)credited|received|deposited|added", sms_body))
    is_debit = bool(re.search(r"(?i)debited|spent|paid|transferr?ed|sent", sms_body))
    
    if not (is_credit or is_debit):
        return {"success": False, "reason": "Could not determine transaction type"}
        
    txn_type = "CREDIT" if is_credit else "DEBIT"
    
    amount = 0.0
    raw_merchant = "UNKNOWN"
    
    # Apply regex patterns to find Amount and Merchant
    for pattern in PATTERNS:
        match = re.search(pattern, sms_body)
        if match:
            try:
                # Extract amount and clean commas
                amt_str = match.group(1).replace(",", "")
                amount = float(amt_str)
                
                # Extract raw merchant name
                raw_merchant = match.group(2).strip()
                break
            except (ValueError, IndexError):
                continue
                
    # If regex failed but it's a debit, try a fallback match for amount
    if amount == 0.0:
        amt_match = re.search(r"(?i)(?:rs\.?|inr)\s*([\d,]+\.?\d*)", sms_body)
        if amt_match:
            try:
                amount = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                pass
                
    cleaned_merchant = clean_merchant_name(raw_merchant)
    
    return {
        "success": True,
        "type": txn_type,
        "amount": amount,
        "raw_merchant": raw_merchant,
        "merchant": cleaned_merchant,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

if __name__ == "__main__":
    # Test cases
    test_sms = [
        "Alert: You've spent Rs. 150.00 on your HDFC Bank Debit Card at RAMESH KUMAR on 2026-05-28. Ref. 12345.",
        "Your a/c no. XX1234 debited by Rs.500.00 transfers to SHYAM SUNDAR Ref No 98765.",
        "Paid Rs.50 to TEA STALL vendor successfully. UPI Ref: 112233.",
        "Rs 20.00 credited to your a/c ending 5678 from AMIT SHARMA."
    ]
    
    print("Testing parser rules:")
    for sms in test_sms:
        print(f"\nSMS: {sms}")
        print(f"Parsed: {parse_sms(sms)}")
