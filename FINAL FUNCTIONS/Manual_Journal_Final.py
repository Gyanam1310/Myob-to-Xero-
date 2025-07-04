import pandas as pd
import os

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

# --- Column mapping ---
column_mapping = {
    "ID No.": "Narration",
    "Account No.": "AccountCode",
    "Debit": "Amount",
    "Credit": "Credit",
    "Memo": "Description",
    "Job No.": "TrackingOption1"
}

# --- Step 1: Read files ---

csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\General Journal.csv"
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

print(df.head())
print(df_coa.head())    
# --- Step 2: Rename columns and clean ---
df.rename(columns=column_mapping, inplace=True)
df.dropna(how='all', inplace=True)

# --- Step 3: Extract Date from AccountCode before modifying it ---
df['Date'] = None
df.loc[df['Narration'] == 'GJ', 'Date'] = df['AccountCode']

# --- Step 4: Map TrackingOption1 ---
def map_tracking_option(row):
    matching_row = df_jobs[df_jobs["Job Number"] == row["TrackingOption1"]]
    if not matching_row.empty:
        # Corrected the typo here to .values[0]
        return matching_row["Job Number"].astype(str).values[0] + "-" + matching_row["Job Name"].astype(str).values[0]
    else:
        return ""

df["TrackingOption1"] = df.apply(map_tracking_option, axis=1)
df["TrackingName1"] = df["TrackingOption1"].apply(lambda x: "Job" if pd.notna(x) and x != "" else "")
# --- Step 5: Map AccountCode, handle restricted types ---
restricted_types = {'Bank', 'Accounts Receivable', 'Accounts Payable'}

def map_account_code(row):
    coa_row = df_coa[df_coa["Account Number"] == row["AccountCode"]]
    if not coa_row.empty and coa_row.iloc[0]["Account Type"] in restricted_types:
        return '7777'
    else:
        return row["AccountCode"]

df["AccountCode"] = df.apply(map_account_code, axis=1)
df["AccountCode"] = df["AccountCode"].astype(str).str.replace('-', '', regex=False)

# --- Step 6: Final formatting ---
df["TaxRate"] = "BAS Excluded"
df["Status"] = "DRAFT"
if 'Description' not in df.columns:
    df["Description"] = '.'
else:
    df["Description"] = df["Description"].fillna(".")
df['Amount'] = df['Amount'].replace({r'[^\d.]': ''}, regex=True).fillna(0).astype(float)
df['Credit'] = df['Credit'].replace({r'[^\d.]': ''}, regex=True).fillna(0).astype(float)
df['Amount'] = df['Amount'] - df['Credit']
df['Date'] = df['Date'].ffill()
df['LineAmountType'] = 'Exclusive'

# --- Step 7: Finalize required columns ---
required_columns = [ 
    'Narration', 'Date', 'Description', 'AccountCode', 'TaxRate', 'Amount', 'TrackingName1', 
    'TrackingOption1', 'TrackingName2', 'TrackingOption2', 'LineAmountType', 'Status'
]

df = df.reindex(columns=required_columns, fill_value="")

df = df[df['Narration'] != 'GJ']

# --- Step 8: Export ---
output_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_MANUAL_JOURNAL.csv"; df.to_csv(output_path, index=False)

print("Successful")
