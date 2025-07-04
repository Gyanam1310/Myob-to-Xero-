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
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Item Inv.csv"
df_coa_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
df_item_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Items.csv"
df_jobs_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"
# Check if all required files exist
if not all(os.path.exists(f) for f in [csv_path, df_coa_path, df_jobs_path, df_item_path]):
    raise FileNotFoundError("One or more required files are missing.")

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

with open(df_coa_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(df_coa_path))

with open(df_jobs_path, 'rb') as f:
    df_jobs = read_file(f, os.path.basename(df_jobs_path))

with open(df_item_path, 'rb') as f:
    df_item = read_file(f, os.path.basename(df_item_path))
# 
# Clean column names
df.columns = df.columns.str.strip()
df_jobs.columns = df_jobs.columns.str.strip()
df_item.columns = df_item.columns.str.strip()
df_coa.columns = df_coa.columns.str.strip()

# Drop empty rows
df.dropna(how='all', inplace=True)

# Load column mappings
column_mapping = {
    "ContactName": "*ContactName",
    "Invoice No.": "*InvoiceNumber",
    "Date": "*InvoiceDate",
    "Customer PO": "Reference",
    "Item Number": "InventoryItemCode",
    "Quantity": "*Quantity",
    "Description": "*Description",
    "Price": "*UnitAmount",
    "Discount": "Discount",
    "Job": "TrackingOption1",
    "Tax Code": "*TaxType",
    "Tax Amount": "TaxAmount",
    "Currency Code": "Currency",
    "Exchange Rate": "Exchange Rate"
}

# Create ContactName by combining First Name and Last Name (only if those columns exist)
if "First Name" in df.columns and "Co./Last Name" in df.columns:
    df["ContactName"] = df["First Name"].fillna("") + " " + df["Co./Last Name"].fillna("")

# Rename columns using mapping (only for present columns)
df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping}, inplace=True)

# Set DueDate equal to InvoiceDate (only if *InvoiceDate exists)
if "*InvoiceDate" in df.columns:
    df["*DueDate"] = df["*InvoiceDate"]

# Replace blank descriptions with "." (only if *Description exists)
if "*Description" in df.columns:
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

# Map tax codes based on account type
def map_tax_code(row):
    if "*AccountCode" not in row or "*TaxType" not in row:
        return "BAS Excluded"

    account_code = str(int(float(row["*AccountCode"]))) if pd.notna(row["*AccountCode"]) else ""
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

    elif tax_code == "GST":
        if account_type == "Income":
            return tax_code_mapping.get("GST_Income", tax_code)
        elif account_type == "Expense":
            return tax_code_mapping.get("GST_Expense", tax_code)
        else:
            return "BAS Excluded"

    else:
        return tax_code_mapping.get(tax_code, tax_code)

# Map account code only if InventoryItemCode column exists
def map_account_code(item_number): 
    row = df_item[df_item["Item Number"] == item_number]
    row = df_item[df_item["Item Number"] == item_number]
    if not row.empty:
        return row["Income Acct"].iloc[0]
    else:
        return None

if "InventoryItemCode" in df.columns:
    df["*AccountCode"] = df["InventoryItemCode"].apply(map_account_code)
else:
    df["*AccountCode"] = None

# Apply map_tax_code only if required columns exist
if "*AccountCode" in df.columns and "*TaxType" in df.columns:
    df["*TaxType"] = df.apply(map_tax_code, axis=1)
else:
    if "*TaxType" not in df.columns:
        df["*TaxType"] = None

# Map tracking option only if TrackingOption1 exists
# def map_tracking_option(row):
#     if "TrackingOption1" not in row:
#         return None
#     matching_row = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
#     if not matching_row.empty:
#         return matching_row["Job Number"].values[0] + "-" + matching_row["Job Name"].values[0]
#     else:
#         return None
def map_tracking_option(row):
    matching_row = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
    if not matching_row.empty:
        return f"{matching_row['Job Number'].values[0]}-{matching_row['Job Name'].values[0]}"
    return row["TrackingOption1"]  # Fallback to original

# if "TrackingOption1" in df.columns:
#     df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
# else:
#     df["TrackingOption1"] = None

# df["TrackingName1"] = df["TrackingOption1"].apply(lambda x: "Job" if pd.notna(x) and x != "" else "")

if "TrackingOption1" in df.columns:
    df["TrackingOption1"] = df["TrackingOption1"].apply(lambda x: str(int(x)) if pd.notna(x) and str(x).strip().replace('.', '', 1).isdigit() else str(x).strip())
    df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
else:
    df["TrackingOption1"] = None
import numpy as np

df.replace(to_replace=[np.nan, None, 'nan', 'NaN', 'None'], value='', inplace=True)
# Set TrackingName1 if TrackingOption1 is non-empty
df["TrackingName1"] = df["TrackingOption1"].apply(lambda x: "Job" if pd.notna(x) and x != "" else "")


# --- Insert Freight Rows with Deduplication ---
freight_col = "Freight Amount"
freight_tax_code_col = "Freight Tax Code"
freight_tax_amt_col = "Freight TaxAmount"

new_rows = []
freight_tracker = set()

for _, row in df.iterrows():
    new_rows.append(row)

    # Parse and clean freight amount for comparison, only if freight_col exists
    raw_freight = row.get(freight_col, "0") if freight_col in df.columns else "0"
    try:
        freight_amount = float(str(raw_freight).replace("$", "").replace(",", "").strip() or "0")
    except:
        freight_amount = 0

    if freight_amount > 0:
        freight_key = (
            row.get("*ContactName", "") if "*ContactName" in df.columns else "",
            row.get("*InvoiceNumber", "") if "*InvoiceNumber" in df.columns else "",
            row.get("*InvoiceDate", "") if "*InvoiceDate" in df.columns else "",
            freight_amount,
            row.get(freight_tax_code_col, "") if freight_tax_code_col in df.columns else "",
            row.get(freight_tax_amt_col, 0) if freight_tax_amt_col in df.columns else 0
        )

        if freight_key not in freight_tracker:
            freight_tracker.add(freight_key)

            freight_row = row.copy()
            freight_row["InventoryItemCode"] = "" if "InventoryItemCode" in df.columns else None
            freight_row["*AccountCode"] = "" if "*AccountCode" in df.columns else None
            freight_row["*Quantity"] = 1 if "*Quantity" in df.columns else None
            freight_row["*Description"] = "Freight Charge" if "*Description" in df.columns else None
            freight_row["*UnitAmount"] = freight_amount if "*UnitAmount" in df.columns else None
            freight_row["Discount"] = 0 if "Discount" in df.columns else None
            freight_row["TrackingName1"] = "" if "TrackingName1" in df.columns else None
            freight_row["TrackingOption1"] = "" if "TrackingOption1" in df.columns else None
            freight_row["*TaxType"] = row.get(freight_tax_code_col, "") if "*TaxType" in df.columns else None
            freight_row["TaxAmount"] = row.get(freight_tax_amt_col, 0) if "TaxAmount" in df.columns else None

            new_rows.append(freight_row)

# Final DataFrame and export
df = pd.DataFrame(new_rows).copy(deep=True)
# Define required column order
columns_order = [
    "*ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
    "POCity", "PORegion", "POPostalCode", "POCountry",
    "*InvoiceNumber", "Reference", "*InvoiceDate", "*DueDate", "Total", "InventoryItemCode",
    "*Description", "*Quantity", "*UnitAmount", "Discount", "*AccountCode", "*TaxType", "TaxAmount",
    "TrackingName1", "TrackingOption1", "TrackingName2", "TrackingOption2", "Currency", "BrandingTheme",
    "Exchange Rate"
]

# Add missing columns with empty values
for col in columns_order:
    if col not in df.columns:
        df[col] = ""

# Reorder columns
df = df[columns_order]

# Clean columns if they exist
if "*UnitAmount" in df.columns:
    df.loc[:, '*UnitAmount'] = df['*UnitAmount'].replace({r'\$': ''}, regex=True)
if "TaxAmount" in df.columns:
    df.loc[:, 'TaxAmount'] = df['TaxAmount'].replace({r'\$': ''}, regex=True)

df.replace(to_replace=[np.nan, None, 'nan', 'NaN', 'None'], value='', inplace=True)
df.to_csv(
    r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_SALES_ITEM_INVOICE.csv",
    index=False,
    encoding="utf-8"
)

print("File saved successfully!")
