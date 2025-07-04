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
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Supplier .csv"

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

# Step 2: Clean Column Names (Remove Unicode & Strip Spaces)
df.columns = df.columns.str.strip()

# Step 3: Define Column Mapping Inline (instead of loading from JSON file)
column_mapping = {
    "Co./Last Name": "*ContactName",
    "Card ID": "AccountNumber",
    "Addr 1 - Email": "EmailAddress",
    "First Name": "FirstName",
    "Addr 1 - Line 1": "POAddressLine1",
    "Addr 1 - Line 2": "POAddressLine2",
    "Addr 1 - Line 3": "POAddressLine3",
    "Addr 1 - Line 4": "POAddressLine4",
    "Addr 1 - City": "POCity",
    "Addr 1 - State": "PORegion",
    "Addr 1 - Postcode": "POZipCode",
    "Addr 1 - Country": "POCountry",
    "Addr 2 - Line 1": "SAAddressLine1",
    "Addr 2 - Line 2": "SAAddressLine2",
    "Addr 2 - Line 3": "SAAddressLine3",
    "Addr 2 - Line 4": "SAAddressLine4",
    "Addr 2 - City": "SACity",
    "Addr 2 - State": "SARegion",
    "Addr 2 - Postcode": "SAZipCode",
    "Addr 2 - Country": "SACountry",
    "Addr 1 - Phone No. 1": "PhoneNumber",
    "Addr 1 - Fax No.": "FaxNumber",
    "Account Name": "BankAccountName",
    "Account Number": "BankAccountNumber",
    "Statement Text": "BankAccountParticulars",
    "A.B.N.": "TaxNumber",
    " - Balance Due Days": "DueDateBillDay",
    "Terms - Payment is Due": "DueDateBillTerm",
    "Account": "PurchasesAccount"
}


# Step 5: Merge First & Last Name into ContactName
if "First Name" in df.columns and "Co./Last Name" in df.columns:
    df["*ContactName"] = df["First Name"].fillna("") + " " + df["Co./Last Name"].fillna("")
    df["*ContactName"] = df["*ContactName"].str.strip()  # Remove extra spaces

print(df.columns)
# Step 6: Merge BSB and Account Number 
if "BSB" in df.columns and "Account Number" in df.columns:
    df["Account Number"] = df["BSB"].fillna("").astype(str) + df["Account Number"].fillna("").astype(str)
else:
    print("Warning: 'BSB' or 'Account Number' column is missing! Skipping merge operation.")

# Step 7: Rename Columns as per Mapping
df = df.rename(columns=column_mapping)

# Step 8: Clean AccountNumber Column (Remove Asterisks & Replace 'None' with Blank)
if "AccountNumber" in df.columns:
    df["AccountNumber"] = df["AccountNumber"].astype(str).str.replace(r'\*', '', regex=True)  
    df["AccountNumber"] = df["AccountNumber"].replace("None", "").str.strip()

# Step 10: Define Required Column Order
final_column_order = [
    "*ContactName", "AccountNumber", "EmailAddress", "FirstName", "LastName",
    "POAttentionTo", "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
    "POCity", "PORegion", "POZipCode", "POCountry", "SAAttentionTo",
    "SAAddressLine1", "SAAddressLine2", "SAAddressLine3", "SAAddressLine4",
    "SACity", "SARegion", "SAZipCode", "SACountry", "PhoneNumber",
    "FaxNumber", "MobileNumber", "DDINumber", "SkypeName",
    "BankAccountName", "BankAccountNumber", "BankAccountParticulars",
    "TaxNumberType", "TaxNumber", "DueDateBillDay", "DueDateBillTerm", "PurchasesAccount"
]

# Remove duplicate columns before reordering
df = df.loc[:, ~df.columns.duplicated()]

# Reorder columns safely
df = df.reindex(columns=[col for col in final_column_order if col in df.columns])

# Step 12: Save Final Processed File
df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_VENDOR.csv", index=False, encoding="ascii", errors="ignore")  # ASCII removes all Unicode
print("Conversion Completed Successfully!")
