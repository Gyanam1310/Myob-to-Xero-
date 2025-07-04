import pandas as pd
import re

bad_line_count = 0
bad_line_numbers = []

def count_bad_lines(line):
    global bad_line_count, bad_line_numbers
    bad_line_count += 1
    count_bad_lines.line_number += 1
    bad_line_numbers.append(count_bad_lines.line_number)
    return None

def detect_header_line(file_obj, max_lines=100):
    """
    Try to find a proper header line:
    - Prefer lines containing 'ID No.' and 'Account No.'
    - Skip lines with only symbols, empty, or garbage like '{}'
    - As fallback, use first line with at least 4 fields
    """
    file_obj.seek(0)
    lines = file_obj.readlines()
    fallback_candidate = None

    for i, line in enumerate(lines[:max_lines]):
        decoded = line.decode('utf-8', errors='ignore') if isinstance(line, bytes) else line
        cleaned = re.sub(r'[{}£$€]', '', decoded).strip()

        # Skip lines that are empty or noise
        if not cleaned or cleaned in ['-', '–', '—']:
            continue

        # Preferred match: known column headers
        if re.search(r'\bID\s*No\.?\b.*\bAccount\s*No\.?\b', cleaned, re.IGNORECASE):
            return i

        # Save a fallback if it has 4+ columns after splitting
        split_cols = re.split(r'\s{2,}|\t+', cleaned)
        if len(split_cols) >= 4 and fallback_candidate is None:
            fallback_candidate = i

    return fallback_candidate if fallback_candidate is not None else 0


def read_file(file_obj, filename):
    global bad_line_count, bad_line_numbers
    bad_line_count = 0
    bad_line_numbers = []

    ext = filename.split('.')[-1].lower()

    # Detect header line
    file_obj.seek(0)
    header_line = detect_header_line(file_obj)
    file_obj.seek(0)

    # For TXT files: use flexible separator and skip header lines
    if ext == "txt":
        print("TXT file detected, attempting flexible read...")
        count_bad_lines.line_number = header_line + 1
        try:
            df = pd.read_csv(file_obj, sep=r'\s{2,}|\t+', skiprows=header_line, engine='python',
                             encoding='utf-8', on_bad_lines=count_bad_lines)
        except Exception:
            file_obj.seek(0)
            count_bad_lines.line_number = header_line + 1
            df = pd.read_csv(file_obj, sep=r'\s{2,}|\t+', skiprows=header_line, engine='python',
                             encoding='ISO-8859-1', on_bad_lines=count_bad_lines)

    elif ext in ["csv"]:
        try:
            df = pd.read_csv(file_obj, skiprows=header_line, encoding='utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, skiprows=header_line, encoding='ISO-8859-1')

    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_obj, skiprows=header_line)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    # Remove currency symbols and curly braces from all string fields
    df = df.map(lambda x: re.sub(r'[£$€{}]', '', str(x)).strip() if isinstance(x, str) else x)

    # Drop rows that are completely empty
    df.dropna(how='all', inplace=True)

    return df

# --- Step 1: File paths ---
import os
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Payroll Journal.csv"
coa_myob_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
job_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"
# Check if all files exist
if not all(os.path.exists(f) for f in [csv_path, coa_myob_path, job_path]):
    raise FileNotFoundError("One or more required files are missing.")

# --- Step 2: Read data ---

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

with open(coa_myob_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(coa_myob_path))

with open(job_path, 'rb') as f:
    df_jobs = read_file(f, os.path.basename(job_path))

# print(df.head())
# print(df_coa.head())
# print(df_jobs.head())

print(f"Bad lines encountered: {bad_line_count}")
if bad_line_numbers:
    print("Bad line numbers:", bad_line_numbers)
else:
    print("✅ No bad lines encountered.")
# --- Step 3: Rename columns ---

column_mapping = {
    "ID No.": "Date",
    "Account No.": "Account Code",
    "Debit": "Amount",
    "TrackingName1": "TrackingOption1"
}

df.rename(columns=column_mapping, inplace=True)
if 'Bank' not in df.columns:
    df['Bank'] = ''
# --- Step 4: Map TrackingOption1 if present ---

if "TrackingOption1" in df.columns:
    def map_tracking_option(row):
        match = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
        return match.iloc[0]["Job Number Xero"] if not match.empty else None

    df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
    df["TrackingName1"] = "Job"

# --- Step 5: Add fixed columns ---

df['Description'] = "Payroll"
df["Transaction type"] = "SPEND"
df["Tax"] = "BAS EXCLUDED"

# --- Step 6: Numeric conversion and amount adjustment ---
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
df["Amount"] = df["Amount"] - df["Credit"]

# --- Step 7: Clean and format Date column to keep only date (no time) ---
import numpy as np
df['Date'] = df['Date'].apply(lambda x: np.nan if isinstance(x, int) else x)
df['Date'] = df['Date'].ffill()
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Date'] = df['Date'].ffill()
df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')  # Drop time part, keep date string

# --- Step 8: Create Reference column based on Date and add unique suffix ---

df['Reference'] = df['Date'].copy()
df['Reference'] = df['Reference'].astype(str) + '-' + df.index.astype(str)

# --- Step 9: Separate Payee and Account Code based on numeric or not ---

df['Payee'] = df['Account Code'][~df['Account Code'].astype(str).str.replace('.', '', regex=False).str.isnumeric()]
df['Account Code'] = df['Account Code'][df['Account Code'].astype(str).str.replace('.', '', regex=False).str.isnumeric()]
df['Payee'] = df['Payee'].ffill()
df = df[df['Account Code'].notna()]

# --- Step 10: Bank Account Handling ---

# 1. Extract bank account codes from Chart of Accounts
bank_account_codes = df_coa[df_coa["Account Type"] == "Bank"]["Account Number"].astype(str).str.strip()

# 2. Clean 'Account Code' in df
df["Account Code"] = df["Account Code"].astype(str).str.strip()
# 3. Fill missing Reference values (downwards)
df["Reference"] = df["Reference"].ffill()
df['Bank'] = df.groupby('Payee')['Bank'].transform(lambda x: x.dropna().iloc[0] if x.notna().any() else np.nan)
print(df)
# 4. Extract rows where Account Code is a bank account code
bank_rows = df[df["Account Code"].isin(bank_account_codes)].copy()

# 5. Group bank rows by Reference and get first bank account code for each group
bank_codes = (
    bank_rows.groupby("Reference")["Account Code"]
    .first()
    .rename("Bank")
)

df['Bank'] = df['Reference'].map(bank_codes)
df['Bank'] = df.groupby('Payee')['Bank'].transform(lambda x: x.dropna().iloc[0] if x.notna().any() else np.nan)
print(df)
# --- Step 11: Add unique suffix to Reference again after bank row removal ---

grouped = df.groupby('Reference')
suffix_dict = {ref: i+1 for i, ref in enumerate(grouped.groups)}
df['Reference'] = df['Reference'].apply(lambda x: f"{x}-{suffix_dict[x]}")
columns_order = ["Date", "Amount", "Description", "Payee", "Reference", "Transaction type", "Account Code", "Tax", "Bank", "Item Code", "Currency rate", "TrackingName1", "TrackingOption1"]
df = df.reindex(columns=columns_order, fill_value="")
# --- Step 13: Save to CSV ---

df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_PAYROLL.csv", index=False)
print(f"Bad lines encountered: {bad_line_count}")
if bad_line_numbers:
    print("Bad line numbers:", bad_line_numbers)
else:
    print("✅ No bad lines encountered.")
print("Conversion Completed Successfully!")
