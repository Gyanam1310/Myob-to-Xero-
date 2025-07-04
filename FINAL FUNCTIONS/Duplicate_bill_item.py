import pandas as pd
import os
import numpy as np


def read_file(file_obj, filename, skip_rows=0):
    ext = filename.split('.')[-1].lower()

    if ext == "csv":
        df = pd.read_csv(file_obj, encoding='utf-8', skiprows=skip_rows, na_values=[], keep_default_na=False)
    elif ext in ["xls", "xlsx"]:
        # Read all sheets into a dict of DataFrames
        excel_file = pd.ExcelFile(file_obj)
        sheet_dfs = []
        for sheet_name in excel_file.sheet_names:
            df_sheet = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=skip_rows, na_values=[], keep_default_na=False)

            df_sheet['SheetName'] = sheet_name  # optional: add sheet info
            sheet_dfs.append(df_sheet)
        df = pd.concat(sheet_dfs, ignore_index=True)
    elif ext == "txt":
        df = pd.read_csv(file_obj, delimiter='\t', encoding='utf-8', skiprows=skip_rows, na_values=[], keep_default_na=False)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    return df

# Example usage
csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\SAMPLE DATA SETS\ItemBills.xlsx"
coa_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\SAMPLE DATA SETS\ACCOUNTS rahul sir.csv"

try:
    with open(csv_path, 'rb') as f:
        df = read_file(f, os.path.basename(csv_path))
    with open(coa_path, 'rb') as f:
        df_coa = read_file(f, os.path.basename(coa_path) )
except Exception as e:
    print("Error reading file:", e)
print(df.head())
columns_mapping = {
    'C-Name': '*ContactName',
    'ID': '*InvoiceNumber',
    "Number": 'Reference',
    "Item-no": 'InventoryItemCode',
    'date': '*InvoiceDate',
    'Quantity': '*Quantity',
    "Description": '*Description',
    'Uprice': '*UnitAmount',
    'AccountCode': '*AccountCode',
    'TaxCode': '*TaxType',
    'Job': 'TrackingName1',
    'IsTaxInclusive': 'LineAmountTypes'
}
print(df.head())
tax_code_mapping = {
    "CAP": "GST on Capital",
    "GST_Expense": "GST on Expenses",
    "GST_Income": "GST on Income",
    "FRE_Expense": "GST Free Expenses",
    "FRE_Income": "GST Free Income",
    "IMP": "GST on Imports",
    "INP": "Input Taxed"
}

df.rename(columns=columns_mapping, inplace=True)

def map_tax_codes(row):
    tax_code = row['*TaxType']
    account_code = row['*AccountCode']

    # Find matching row in COA
    coa_row = df_coa[df_coa['Account Number'].astype(str).str.strip() == str(account_code).strip()]
    
    if not coa_row.empty:
        account_type = coa_row['Account Type'].values[0]
        if tax_code == 'GST':
            if account_type == 'Expense':
                return tax_code_mapping.get('GST_Expense', 'BAS Excluded')
            elif account_type == 'Income':
                return tax_code_mapping.get('GST_Income', 'BAS Excluded')

        elif tax_code == 'FRE':
            if account_type == 'Expense':
                return tax_code_mapping.get('FRE_Expense', 'BAS Excluded')
            elif account_type == 'Income':
                return tax_code_mapping.get('FRE_Income', 'BAS Excluded')
    
    return tax_code_mapping.get(tax_code, 'BAS Excluded')

    
df['*InvoiceDate'] = df['*InvoiceDate'].str.split(':').str[1]
df['*DueDate'] = df['*InvoiceDate']
df['*Description'] = df['*Description'].fillna('.')
df['*Quantity'] = df['*Quantity'].fillna('1')
df['*AccountCode'] = df['*AccountCode'].astype(str).replace(r'ACC:|\-', '', regex=True)
print(df.head())
df['*TaxType'] = df.apply(map_tax_codes, axis=1)
df['TrackingOption1'] = np.where(
    df['Job-no'].notna() & df['Job-Name'].notna() & 
    (df['Job-no'].astype(str).str.strip() != '') & 
    (df['Job-Name'].astype(str).str.strip() != ''),
    df['Job-no'].astype(str).str.strip() + '-' + df['Job-Name'].astype(str).str.strip(),
    ''
)
df['TrackingName1'] = df['TrackingOption1'].apply(lambda x: 'Job' if str(x)!='' else '')

df['LineAmountTypes'] = df['LineAmountTypes'].apply(lambda x: 'Inclusive' if str(x).lower()=='true' else ('Exclusive' if str(x).lower()=='false' else '')) 

# df['*InvoiceNumber'] = (
#     df['Number'].astype(str).str.strip() + '-' +
#     df['*InvoiceNumber'].astype(str).str.strip().str.split('-').str[0]
# )

# Step 1: Preserve original ID before transforming
df['OriginalID'] = df['*InvoiceNumber']  # backup original 'ID'

# Step 2: Find Numbers that are repeated
duplicate_numbers = df['Reference'].value_counts()
duplicate_numbers = duplicate_numbers[duplicate_numbers > 1].index
duplicate_numbers_rows = df[df['Reference'].isin(duplicate_numbers)]

# Step 3: Find Numbers with multiple unique OriginalIDs
id_uniqueness = duplicate_numbers_rows.groupby('Reference')['OriginalID'].nunique()
numbers_with_multiple_ids = id_uniqueness[id_uniqueness > 1].index

# Step 4: Generate new *InvoiceNumber
def create_invoice_number(row):
    if row['Reference'] in numbers_with_multiple_ids:
        return f"{row['Reference']}-{row['OriginalID'][:8]}"
    else:
        return row['Reference']

df['*InvoiceNumber'] = df.apply(create_invoice_number, axis=1)
print(df['*InvoiceNumber'].head())

column_order = [
    "*ContactName", "EmailAddress", "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
    "POCity", "PORegion", "POPostalCode", "POCountry", "*InvoiceNumber", "Reference",
    "*InvoiceDate", "*DueDate", "Total", "InventoryItemCode", "Description", "*Quantity", "*UnitAmount",
    "*AccountCode", "*TaxType", "TaxAmount", "TrackingName1", "TrackingOption1",
    "TrackingName2", "TrackingOption2", "Currency", "LineAmountTypes"
]


for col in column_order:
    if col not in df.columns:
        df[col] = ''

df = df[column_order]

df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\XERO_Duplicate_Bill_Item.csv", index=False, encoding='utf-8-sig')
print("File processed and saved successfully.")


