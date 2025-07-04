import pandas as pd
import json
import os
import csv

def read_file(file_obj, filename):
    ext = filename.split('.')[-1].lower()

    if ext == "csv":
        try:
            df = pd.read_csv(file_obj, encoding='utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, encoding='ISO-8859-1')

    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_obj)

    elif ext == "txt":
        file_obj.seek(0)
        try:
            df = pd.read_csv(file_obj, sep='\t', skiprows=1, engine='python', encoding='utf-8')
        except Exception:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, delimiter='\t', skiprows=1, encoding='ISO-8859-1')

    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    df.columns = df.columns.astype(str).str.strip()

    # Remove curly braces from the entire DataFrame
    df = df.map(lambda x: str(x).replace("{", "").replace("}", "") if isinstance(x, str) else x)
    
    return df

# Load the Excel file using read_file
file_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"
filename = os.path.basename(file_path)

with open(file_path, 'rb') as f:
    df = read_file(f, filename)
df_columns = list(df.columns)
# print(f"Bad lines encountered: {bad_line_count}")
# if bad_line_numbers:
#     print("Bad line numbers:", bad_line_numbers)
# else:
#     print("No bad lines encountered.")
# print("Conversion Completed Successfully!")

# Define the mandatory columns for MYOB (and their corresponding Xero columns)
mandatory_columns = {
    "Account Number": "*Code",
    "Account Name": "*Name",
    "Account Type": "*Type",
    "Tax Code": "*Tax Code",
    "Description": "Description"
}

# Alert for missing mandatory columns
missing_columns = []
for myob_col, xero_col in mandatory_columns.items():
    if myob_col not in df_columns:
        missing_columns.append(myob_col)

if missing_columns:
    print(f"Alert: The following MYOB columns are missing to convert to Xero format:")
    for col in missing_columns:
        print(f"- {col}")

# Columns Mapping
column_mapping = {
    "Account Number": "*Code",
    "Account Name": "*Name",
    "Account Type": "*Type",
    "Tax Code": "*Tax Code",
    "Description": "Description",
    "Dashboard": "Dashboard",
    "Expense Claims": "Expense Claims",
    "Enable Payments": "Enable Payments"
}

json_columns = list(column_mapping.keys())

common_columns = [cols for cols in df_columns if cols in json_columns]
filtered_mapping = {cols: column_mapping[cols] for cols in common_columns}

df = df.rename(columns=filtered_mapping)

# Tax Code Mapping (Embedded directly)
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
    tax_code = row["*Tax Code"]
    account_type = row["*Type"]

    # Handle FRE tax codes
    if tax_code == "FRE":
        if account_type == "Income" or account_type == "Other Income":
            return tax_code_mapping.get("FRE_Income", tax_code)
        elif account_type == "Expense" or account_type == "Other Expense":
            return tax_code_mapping.get("FRE_Expense", tax_code)
        else:
            return "BAS Excluded"

    # Handle GST tax codes
    elif tax_code == "GST":
        if account_type == "Income" or account_type == "Other Income":
            return tax_code_mapping.get("GST_Income", tax_code)
        elif account_type == "Expense" or account_type == "Other Expense":
            return tax_code_mapping.get("GST_Expense", tax_code)
        else:
            return "BAS Excluded"

    # Default case
    else:
        return tax_code_mapping.get(tax_code, tax_code)

df["*Tax Code"] = df.apply(map_tax_code, axis=1).fillna("BAS Excluded")

# Account Types Mapping (Embedded directly)
type_mapping = {
    "Asset": "Current Asset",
    "Other Asset": "Current Asset",
    "Accounts Payable": "Accounts Payable",
    "Accounts Receivable": "Accounts Receivable",
    "Bank": "Bank",
    "Cost of Sales": "Direct Costs",
    "Credit Card": "Bank",
    "Equity": "Equity",
    "Expense": "Expense",
    "Fixed Asset": "Fixed Asset",
    "Income": "Revenue",
    "Liability": "Liability",
    "Long Term Liability": "Liability",
    "Other Current Asset": "Current Asset",
    "Other Current Liability": "Current Liability",
    "Other Expense": "Expense",
    "Other Income": "Other Income",
    "Other Liability": "Current Liability"
}

df["*Type"] = df["*Type"].map(type_mapping)

# Add missing columns if they don't exist
if "Dashboard" not in df.columns:
    df.insert(6, "Dashboard", df["*Type"].apply(lambda x: "Yes" if x in ["Bank", "Credit Card"] else "No"))

df.insert(7, "Expense Claims", "No")
df.insert(8, "Enable Payments", "No")

# Reorder the columns as per Xero format
columns_order = [
    "*Code", "*Name", "*Type", "*Tax Code",
    "Description", "Dashboard", "Expense Claims", "Enable Payments"
]

final_columns = [col for col in columns_order if col in df.columns]
df = df[final_columns] 

# Save the final output to a new CSV file
df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_COA.csv", index=False)
# print(f"Bad lines encountered: {bad_line_count}")
print("Conversion successful!")
