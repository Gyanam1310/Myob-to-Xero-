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

# Load data files
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Service Inv.csv"
coa_myob_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
job_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"

# Check if all required files exist
if not all(os.path.exists(f) for f in [csv_path, coa_myob_path, job_path]):
    raise FileNotFoundError("One or more required files are missing.")

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

with open(coa_myob_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(coa_myob_path))

with open(job_path, 'rb') as f:
    df_jobs = read_file(f, os.path.basename(job_path))

df = df.dropna(how='all')
# Standardize column names
df.columns = df.columns.str.strip()
df_jobs.columns = df_jobs.columns.str.strip()

column_mapping = {
  "Co./Last Name": "*ContactName",
  "Invoice No.": "*InvoiceNumber",
  "Date": "*InvoiceDate",
  "Balance Due Days": "*DueDate",
  "Customer PO": "Reference",
  "Description": "*Description",
  "Account No.": "*AccountCode",
  "Amount": "*UnitAmount",
  "Job": "TrackingOption1",
  "Tax Code": "*TaxType",
  "Tax Amount": "TaxAmount",
  "Currency Code": "Currency",
  "Exchange Rate": "Exchange Rate"
}

df = df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping})

# Fix 'Co./Last Name' column
df["*ContactName"] = df["First Name"].fillna('').astype(str) + " " + df["*ContactName"].fillna('').astype(str)

# Fill missing values
df["*DueDate"] = df["*InvoiceDate"]
df["*Description"] = df["*Description"].fillna(".")

# Load tax code mapping
tax_code_mapping = {
    "CAP": "GST on Capital",
    "FRE_Expense": "GST Free Expenses",
    "FRE_Income": "GST Free Income",
    "GST_Expense": "GST on Expenses",
    "GST_Income": "GST on Income",
    "IMP": "GST on Imports",
    "INP": "Input Taxed",
    "N-T": "BAS Excluded",
    "ITS": "BAS Excluded",
    "EXP": "BAS Excluded",
    "": "BAS Excluded"
}

def map_tax_code(row):
    if "*AccountCode" not in row or "*TaxType" not in row:
        return "BAS Excluded"

    account_code = str(row["*AccountCode"]) if pd.notna(row["*AccountCode"]) else ""
    tax_code = row["*TaxType"]

    df_coa["Account Number"] = df_coa["Account Number"].astype(str)
    coa_row = df_coa[df_coa["Account Number"] == account_code]

    if coa_row.empty:
        return tax_code_mapping.get(tax_code, "BAS Excluded")

    account_type = coa_row.iloc[0]["Account Type"]

    if tax_code == "FRE":
        if account_type == "Income":
            return tax_code_mapping.get("FRE_Income", tax_code)
        elif account_type == "Expense":
            return tax_code_mapping.get("FRE_Expense", tax_code)
        else:
            return "BAS Excluded"

    # Handle GST tax codes
    elif tax_code == "GST":
        if account_type == "Income":
            return tax_code_mapping.get("GST_Income", tax_code)
        elif account_type == "Expense":
            return tax_code_mapping.get("GST_Expense", tax_code)
        else:
            return "BAS Excluded"

    else:
        return tax_code_mapping.get(tax_code, tax_code)

def map_tracking_option(row):
    matching_row = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
    if not matching_row.empty:
        # Corrected the typo here to .values[0]
        return matching_row["Job Number"].values[0] + "-" + matching_row["Job Name"].values[0]
    else:
        return ""


# Apply mappings
df["*TaxType"] = df.apply(map_tax_code, axis=1).fillna("BAS Excluded")
df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
df["TrackingName1"] = df["TrackingOption1"].apply(lambda x: "Job" if x != "" else "")
df["*Quantity"] = 1

columns_order = [
    "*ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
    "POCity", "PORegion", "POPostalCode", "POCountry", "*InvoiceNumber", "Reference", "*InvoiceDate", "*DueDate", "Total",
    "InventoryItemCode", "*Description", "*Quantity", "*UnitAmount", "Discount", "*AccountCode", "*TaxType", "TaxAmount",
    "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2", "Currency", "BrandingTheme", "Exchange Rate"
]

# Remove dollar signs from specific columns if they exist
if "*UnitAmount" in df.columns:
    df["*UnitAmount"] = df["*UnitAmount"].replace({r'\$': ''}, regex=True)
if "TaxAmount" in df.columns:
    df["TaxAmount"] = df["TaxAmount"].replace({r'\$': ''}, regex=True)

# Add missing columns with empty string values
for col in columns_order:
    if col not in df.columns:
        df[col] = ""

# Reorder columns as per the required order
df = df[columns_order]

# Remove dollar signs from all fields (optional but consistent cleanup)
df = df.replace({r'\$': ''}, regex=True)

# Save the reordered DataFrame to CSV
df.to_csv(
    r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_SERVICE_INOVICE_2.csv",
    index=False
)

print(" File successfully saved!")
