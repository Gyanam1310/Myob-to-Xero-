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

# --- Load data files ---
df_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Item Bills.csv"
df_coa_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
df_item_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Items.csv"
df_jobs_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"

with open(df_path, 'rb') as f:
    df = read_file(f, os.path.basename(df_path))

with open(df_coa_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(df_coa_path))

with open(df_jobs_path, 'rb') as f:
    df_jobs = read_file(f, os.path.basename(df_jobs_path))

with open(df_item_path, 'rb') as f:
    df_item = read_file(f, os.path.basename(df_item_path))

# --- Clean column names ---
df.columns = df.columns.str.strip()
df_coa.columns = df_coa.columns.str.strip()
df_item.columns = df_item.columns.str.strip()
df_jobs.columns = df_jobs.columns.str.strip()

# --- Drop empty rows ---
df.dropna(how='all', inplace=True)

column_mapping = {
    "ContactName": "*ContactName",
    "Purchase No.": "*InvoiceNumber",
    "Date": "*InvoiceDate",
    "Item Number": "InventoryItemCode",
    "Quantity": "*Quantity",
    "Description": "*Description",
    "Price": "*UnitAmount",
    "Job": "TrackingOption1",
    "Tax Code": "*TaxType",
    "Tax Amount": "Tax Amount",
    "Currency Code": "Currency",
    "Exchange Rate": "Exchange Rate"
}

# --- Combine First Name and Last Name to create ContactName ---
df["ContactName"] = df["First Name"].fillna("") + " " + df["Co./Last Name"].fillna("")

# --- Rename columns using mapping ---
df.rename(columns={col: column_mapping[col] for col in df.columns if col in column_mapping}, inplace=True)

# --- Set DueDate equal to InvoiceDate ---
df["*DueDate"] = df["*InvoiceDate"]

# --- Fill empty descriptions ---
df["*Description"] = df["*Description"].fillna(".")

# --- Load tax code mapping ---
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

# --- Define tax code mapper ---
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

# --- Map account code based on inventory ---
def map_account_code(item_number):
    row = df_item[df_item["Item Number"] == item_number]
    if not row.empty:
        if pd.notna(row.iloc[0]["Inventory"]) and str(row.iloc[0]["Inventory"]).strip() != "":
            return row.iloc[0]["Asset Acct"]
        else:
            return row.iloc[0]["Income Acct"]
    return None

# df["*AccountCode"] = df["InventoryItemCode"].apply(map_account_code)
df["*TaxType"] = df.apply(map_tax_code, axis=1)

# --- Tracking mapping ---
def map_tracking_option(row):
    match = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
    if not match.empty:
        return match["Job Number Xero"]
    else:
        return None

df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
df["TrackingName1"] = df["TrackingOption1"].apply(lambda x: "Job" if pd.notna(x) and x != "" else "")

# --- Column order for export ---
columns_order = [
    "*ContactName", "*InvoiceNumber", "*InvoiceDate", "*DueDate",
    "InventoryItemCode", "*AccountCode", "*Quantity", "*Description", "*UnitAmount", "Discount",
    "TrackingName1", "TrackingOption1", "*TaxType", "Tax Amount", "Currency", "Exchange Rate",
]

for col in df.columns:
    if df[col].dtype == object and df[col].notna().any():
        df[col] = df[col].replace({r'\$': ''}, regex=True)

# --- Ensure *Quantity and *UnitAmount are numeric and handle negatives, only if columns exist ---
if "*Quantity" in df.columns:
    df["*Quantity"] = pd.to_numeric(df["*Quantity"], errors="coerce")
    mask = df["*Quantity"] < 0
    df.loc[mask, "*Quantity"] = 4
else:
    mask = pd.Series([False]*len(df))  # fallback mask

if "*UnitAmount" in df.columns:
    df["*UnitAmount"] = pd.to_numeric(df["*UnitAmount"], errors="coerce")
    if 'mask' in locals():
        df.loc[mask, "*UnitAmount"] = -df.loc[mask, "*UnitAmount"]

# --- Filter columns_order to those present in df to avoid KeyErrors ---
columns_order_existing = [col for col in columns_order if col in df.columns]

# --- Final export ---
df[columns_order_existing].to_csv(
    r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_PURCHASE_BILL_PRODUCT.csv",
    index=False
)

print("File saved successfully")
