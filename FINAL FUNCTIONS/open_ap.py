import pandas as pd
import os
import re

def find_header_line(file_obj, ext):
    """
    Detects the correct header row (line number) by scanning the file.
    Returns the index of the header row.
    """
    file_obj.seek(0)
    lines = file_obj.readlines()

    for idx, line in enumerate(lines):
        try:
            decoded = line.decode('utf-8').strip()
        except UnicodeDecodeError:
            decoded = line.decode('ISO-8859-1').strip()
        
        # Split by tab or comma depending on file type
        delimiter = '\t' if ext == "txt" else ','

        parts = [part.strip() for part in decoded.split(delimiter) if part.strip()]
        
        # Heuristic: header row has at least 2-3 non-empty columns and likely keywords
        if len(parts) >= 3 and any(keyword in decoded.lower() for keyword in ["account", "debit", "credit", "id", "name"]):
            return idx  # this is likely the header row

    raise ValueError("Header row could not be detected.")

def read_file(file_obj, filename):
    ext = filename.split('.')[-1].lower()

    # Find likely header line index
    header_line_index = find_header_line(file_obj, ext)

    # Reset file pointer
    file_obj.seek(0)

    if ext == "csv":
        try:
            df = pd.read_csv(file_obj, encoding='utf-8', skiprows=header_line_index)
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, encoding='ISO-8859-1', skiprows=header_line_index)

    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_obj, skiprows=header_line_index)

    elif ext == "txt":
        file_obj.seek(0)
        try:
            df = pd.read_csv(file_obj, sep='\t', skiprows=header_line_index, engine='python', encoding='utf-8')
        except Exception:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, delimiter='\t', skiprows=header_line_index, encoding='ISO-8859-1')
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    df.columns = df.columns.astype(str).str.strip()
    return df

file_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Open AP.xlsx"

with open(file_path, 'rb') as f:  # Open in binary mode for pandas compatibility
    df = read_file(f, file_path)

# Define column mappings
column_mapping = {
    "ID No.": "*InvoiceNumber",
    "Date": "*InvoiceDate",
    "Orig. Curr.": "Currrency",
    "Total Due": "*UnitAmount"
}

# Store a copy before renaming
df_original = df.copy()

# --- Step 1: Add *CustomerName column ---
current_customer = None
customer_names = []

# Function to determine if a string is a valid customer name
def is_valid_customer_name(name):
    return bool(re.match(r'^[A-Za-z\s]+$', name)) and len(name.split()) > 1  # Must have at least 2 words and be alphabetic

for idx, row in df.iterrows():
    # Check if only the first column (customer info) is non-null (indicating a new group)
    non_empty_cols = row.notna().sum()
    first_col = row.iloc[0]

    # If we encounter a new customer group (first non-empty row with valid text)
    if non_empty_cols == 1 and pd.notna(first_col) and not str(first_col).startswith(("*", "Total", "Grand")):
        # Ensure this is a valid customer name, i.e., not a phone number or any numeric data
        if isinstance(first_col, str) and is_valid_customer_name(first_col):
            current_customer = str(first_col).strip()

    customer_names.append(current_customer)

df['*ContactName'] = customer_names

# --- Step 2: Filter only valid transaction rows ---
# Keep rows that have valid Invoice Date and Total Due (i.e., remove any rows with "Total:" or "Grand Total:")
df = df[df['Date'].notna() & df['Total Due'].notna()]

# --- Step 3: Rename columns ---
df.rename(columns=column_mapping, inplace=True)

# --- Step 4: Keep only needed columns ---
# Now we want to keep only the relevant columns including the new *CustomerName
df = df[list(column_mapping.values()) + ['*ContactName']]
print(df.head())
# --- Step 5: Add extra columns ---
df['*DueDate'] = df['*InvoiceDate']
df['Description'] = "."
df['*Quantity'] = 1
df["*TaxType"] = "BAS Excluded"
df['LineAmountType'] = "Exclusive"
df["*AccountCode"] = "960"

df = df[df['*InvoiceNumber'].notna()]

columns_order = [
    "*ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3",
    "POAddressLine4", "POCity", "PORegion", "POPostalCode", "POCountry", "*InvoiceNumber",
    "Reference", "*InvoiceDate", "*DueDate", "Total", "InventoryItemCode", "Description",
    "*Quantity", "*UnitAmount", "Discount", "*AccountCode", "*TaxType", "TaxAmount",
    "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2", "Currency", "BrandingTheme"
]

df = df.reindex(columns=columns_order, fill_value="")

# Optional: Save output to CSV if needed
df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_OPEN_AP.csv", index=False)
print(df.head())
print("File saved successfully.")
