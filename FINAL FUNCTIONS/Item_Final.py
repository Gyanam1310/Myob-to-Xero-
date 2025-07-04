import pandas as pd
import os

def read_file(file_obj, filename):
    ext = filename.split('.')[-1].lower()

    # Read the first line to check if it's a garbage row
    file_obj.seek(0)
    first_line = file_obj.readline().decode(errors='ignore').strip()

    # Determine if first line contains valid headers or junk (e.g., '{}')
    skiprows = 1 if first_line.startswith("{") or first_line == "" else 0

    # Reset the file pointer
    file_obj.seek(0)

    if ext == "csv":
        try:
            df = pd.read_csv(file_obj, encoding='utf-8', skiprows=skiprows)
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, encoding='ISO-8859-1', skiprows=skiprows)

    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_obj, skiprows=skiprows)

    elif ext == "txt":
        file_obj.seek(0)
        try:
            df = pd.read_csv(file_obj, sep='\t', skiprows=skiprows, engine='python', encoding='utf-8')
        except Exception:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, delimiter='\t', skiprows=skiprows, encoding='ISO-8859-1')

    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    # Clean column names
    df.columns = df.columns.astype(str).str.strip()

    return df


# File Paths
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Items.csv"
coa_myob_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\COA.csv"

# Check if all required files exist
if not all(os.path.exists(f) for f in [csv_path, coa_myob_path]):
    raise FileNotFoundError("One or more required files are missing.")

# Load files using the read_file function
with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

with open(coa_myob_path, 'rb') as f:
    df_coa = read_file(f, os.path.basename(coa_myob_path))
print(df.head())
print(df_coa.head())

# print(f"Bad lines encountered: {bad_line_count}")
# if bad_line_numbers:
#     print("Bad line numbers:", bad_line_numbers)
# else:
#     print("✅ No bad lines encountered.")
# print("Conversion Completed Successfully!")

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

column_mapping = {
  "Item Number": "*ItemCode",
  "Item Name": "ItemName",
  "Description": "PurchasesDescription",
  "Standard Cost": "PurchasesUnitPrice",
  "Expense/COS Acct": "PurchasesAccount",
  "Tax Code When Bought": "PurchasesTaxRate",
  "Selling Price": "SalesUnitPrice",
  "Income Acct": "SalesAccount",
  "Tax Code When Sold": "SalesTaxRate"
}

# Rename columns based on mapping
df.rename(columns=column_mapping, inplace=True)

# Tax Code Mapping Function
def map_tax_code(row):
    # Find the corresponding row in the COA dataframe using the SalesAccount field
    coa_row = df_coa[df_coa["Account Number"] == row["SalesAccount"]]
    
    # If no matching COA row is found, return the default tax code or the SalesTaxRate itself
    if coa_row.empty:
        return tax_code_mapping.get(row["SalesTaxRate"], row["SalesTaxRate"])
    
    # Get the account type from the COA row
    account_type = coa_row.iloc[0]["Account Type"]
    tax_code = row["SalesTaxRate"]

    # Handle FRE (Free) tax codes
    if tax_code == "FRE":
        # If the Account Type is "Income" or "Other Income"
        if account_type in ["Income", "Other Income"]:
            return tax_code_mapping.get("FRE_Income", "GST Free Income")
        # If the Account Type is "Cost of Sales", "Expense" or "Other Expense"
        elif account_type in ["Cost of Sales", "Expense", "Other Expense"]:
            return tax_code_mapping.get("FRE_Expense", "GST Free Expenses")
        else:
            return "BAS Excluded"

    # Handle GST tax codes
    elif tax_code == "GST":
        # If the Account Type is "Income" or "Other Income"
        if account_type in ["Income", "Other Income"]:
            return tax_code_mapping.get("GST_Income", "GST on Income")
        # If the Account Type is "Cost of Sales", "Expense" or "Other Expense"
        elif account_type in ["Cost of Sales", "Expense", "Other Expense"]:
            return tax_code_mapping.get("GST_Expense", "GST on Expenses")
        else:
            return "BAS Excluded"

    else:
        return tax_code_mapping.get(tax_code, tax_code)

# Apply tax code mapping
df['SalesTaxRate'] = ''
df["SalesTaxRate"] = df.apply(map_tax_code, axis=1).fillna("BAS Excluded")

# Ensure required columns exist and fill missing ones
df["PurchasesDescription"] = df["PurchasesDescription"].fillna(".")
df["SalesDescription"] = df["PurchasesDescription"]

# Final columns ordering
final_columns = ["*ItemCode", "ItemName", "PurchasesDescription", "PurchasesUnitPrice", "PurchasesAccount", 
                 "PurchasesTaxRate", "SalesDescription", "SalesUnitPrice", "SalesAccount", "SalesTaxRate"]

df = df.reindex(columns=final_columns, fill_value="")

df['PurchasesUnitPrice'] = df['PurchasesUnitPrice'].replace({r'\$': ''}, regex=True)
df['SalesUnitPrice'] = df['SalesUnitPrice'].replace({r'\$': ''}, regex=True)

# Save final CSV
df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_ITEM.csv", index=False, encoding="utf-8")
# print(f"Bad lines encountered: {bad_line_count}")
print("Conversion Completed Successfully!")