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

# --- Step 1: Read files ---

csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\RECEIVEMONEY.csv"
coa_myob_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
job_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"

if not all(os.path.exists(f) for f in [csv_path, coa_myob_path, job_path]):
    raise FileNotFoundError("One or more required files are missing.")

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

with open(coa_myob_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(coa_myob_path))

with open(job_path, 'rb') as f:
    df_jobs = read_file(f, os.path.basename(job_path))

# Define the mapping between source columns and target columns
column_mapping = {
    "Deposit Account": "Bank",
    "ID No.": "Reference",
    "Transaction type": "Transaction type",
    "Date": "Date",
    "Co./Last Name": "Payee",
    "Memo": "Description",
    "Allocation Account No.": "Account Code",
    "Amount": "Amount",
    "Job No.": "Toption",
    "O": "Tname",
    "Tax Code": "Tax",
    "Tax Amount": "Tax Amount",
    "Currency Code": "Currency Name",
    "Exchange Rate": "Currency rate",
    "": "Line Amount Type"
}

# --- Step 2: Rename columns and clean ---
df.rename(columns=column_mapping, inplace=True)
df.dropna(how='all', inplace=True)  # Drop rows with all NaN values

# First, create a helper column to detect where a new block starts
df['is_group_break'] = df['Bank'].notna()  # Assuming 'Bank' is filled only at the start of a new block

# Use cumulative sum to assign group number to each block
df['group_id'] = df['is_group_break'].cumsum()

# Then create a new Reference by combining original Reference + group number
df['Reference'] = df['Reference'].astype(str) + '-' + df['group_id'].astype(str)

df['Bank'] = df['Bank'].ffill()
df = df[(df['Account Code'] != '') & (df['Account Code'].notna())]

# --- Step 3: Clean up "Cheque Account" and "Cheque No."
df['Bank'] = df['Bank'].astype(str).str.replace('-', '', regex=False)
df['Payee'] = df['Payee'].fillna('No Name')
df['Transaction type'] = 'RECIEVE'
df['Description'] = df['Description'].fillna('.')
df['Line Amount Type'] = 'Exclusive'

# Get unique account codes from the cleaned df
account_codes = df['Account Code'].unique()

# Match with df_coa to find which ones are Bank or Credit Card
valid_codes = []
for code in account_codes:
    match = df_coa[df_coa['Account Number'] == code]
    if not match.empty:
        account_type = match.iloc[0]['Account Type']
        if account_type in ['Bank', 'Credit Card']:
            valid_codes.append(code)

# --- Step 4: Map TrackingOption1 ---
def map_tracking_option(row):
    matching_row = df_jobs[df_jobs["Job Number"] == row["Toption"]]
    if not matching_row.empty:
        # Corrected the typo here to .values[0]
        return matching_row["Job Number"].astype(str).values[0] + "-" + matching_row["Job Name"].astype(str).values[0]
    else:
        return ""

df["Toption"] = df.apply(map_tracking_option, axis=1)
# 1. Clean up any null or whitespace-only values in Toption
df['Toption'] = df['Toption'].fillna('').astype(str).str.strip()

# 2. Clear all Tname values first
df['Tname'] = ''

# 3. Set Tname = 'Job' only where Toption is not empty
df.loc[df['Toption'] != '', 'Tname'] = 'Job'

# Define the Tax Code Mapping
tax_code_mapping = {
    "GST_Expense": "GST on Expenses",
    "GST_Income": "GST on Income",
    "FRE_Expense": "GST Free Expenses",
    "FRE_Income": "GST Free Income",
    "": "BAS Excluded",
}

# Filter rows with those account codes
df_bank = df[df['Account Code'].isin(valid_codes)].reset_index(drop=True)
df = df[~df['Account Code'].isin(valid_codes)].reset_index(drop=True)
column_mapping_bank = {
    "Bank": "From Account",
    "Reference": "Reference Number",
    "Date": "Date",
    "Account Code": "To Account",
    "Amount": "Amount"
}

df_bank.rename(columns=column_mapping_bank, inplace=True)

# Step 1: Remove numbers after the hyphen in "Reference Number"
df_bank['Base Reference'] = df_bank['Reference Number'].str.split('-').str[0]

# Step 2: Create a continuous number sequence and append it to the base reference
df_bank['group_id'] = range(1, len(df_bank) + 1)  # Adjust the starting value as needed

# Step 3: Combine the base reference with the continuous number to create the new Reference Number
df_bank['Reference Number'] = df_bank['Base Reference'] + '-' + df_bank['group_id'].astype(str)

# Drop the helper columns
df_bank.drop(['Base Reference', 'group_id'], axis=1, inplace=True)

# Ensure both columns are strings with no whitespace
df["Account Code"] = df["Account Code"].astype(str).str.strip().str.replace('.0', '', regex=False)
df_coa["Account Number"] = df_coa["Account Number"].astype(str).str.strip()

# Define the function to map Tax codes based on Account Type
def map_tax_code(row):
    tax_code = row["Tax"]
    account_code_str = str(row["Account Code"]).strip()

    coa_row = df_coa[df_coa["Account Number"].astype(str).str.strip() == account_code_str]

    if not coa_row.empty:
        account_type = coa_row["Account Type"].values[0]
        if tax_code == "GST":
            return tax_code_mapping.get("GST_Income") if account_type in ['Income', 'Other Income'] else tax_code_mapping.get("GST_Expense")
        elif tax_code == "FRE":
            return tax_code_mapping.get("FRE_Income") if account_type in ['Income', 'Other Income'] else tax_code_mapping.get("FRE_Expense")

    return tax_code_mapping.get(tax_code, "BAS Excluded")

# Apply tax mapping to the main dataframe
df["Tax"] = df.apply(map_tax_code, axis=1)

import re
# print(df_bank["Amount"].head())
df_bank["Amount"] = df_bank["Amount"].astype(str).str.replace(r"[\$,]", "", regex=True).str.replace(r"\((.*?)\)", r"-\1", regex=True)
df["Amount"] = df["Amount"].astype(str).str.replace(r"[\$,]", "", regex=True).str.replace(r"\((.*?)\)", r"-\1", regex=True)
df["Tax Amount"] = df["Tax Amount"].astype(str).str.replace(r"[\$,]", "", regex=True).str.replace(r"\((.*?)\)", r"-\1", regex=True)
df_bank['From Account'], df_bank['To Account'] = df_bank['To Account'].copy(), df_bank['From Account'].copy()
columns_order = ["Date", "Amount", "Description", "Payee", "Reference", "Transaction type", "Account Code", "Tax", "Bank", "ITEM CODE", "Currency rate", "Tname", "Toption", "Tname 1", "Toption1", "Line Amount Type", "Tax Amount", "Currency Name"]
bank_transfer_columns_order = ["Date", "Amount", "From Account", "To Account", "Reference Number"]

df = df.reindex(columns=columns_order, fill_value="")
df_bank = df_bank.reindex(columns=bank_transfer_columns_order, fill_value="")

# Output the dataframes to CSV
df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_RECIEVE_MONEY.csv", index=False)
df_bank.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_BANK_TRANSFER_RECIEVE_MONEY.csv", index=False)
print("Conversion Completed Successfully!")