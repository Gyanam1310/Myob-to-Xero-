import pandas as pd
import random
import os 

# # Load CSV
df = pd.read_csv("/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/OPEN BILL/Aged creditor transactions.csv",skiprows=3)

# Clean column names and values
df.columns = df.columns.str.strip()
df["TYPE"] = df["TYPE"].astype(str).str.strip()

# Keep only 'Bill' entries
df = df[df["TYPE"] == "Bill"].reset_index(drop=True)

# Create new columns
df["Bill number"] = df["NUMBER"]
df["Supplier invoice number"] = df["NUMBER"]

# Rename necessary columns
field_mapping = {
    "SUPPLIER": "Supplier",
    "DATE": "Transaction date",
    "DUE DATE": "Due date",         
    "BALANCE": "Unit Price",
    "REFERENCE": "Description"
}
df = df.rename(columns=field_mapping)

# Add constant and placeholder columns
df["Amounts are"] = "Tax exclusive"
df["No. of Unit"] = "1"
df["Account No."] = "3-8000"
df["Tax code"] = "N-T"
df["Tax amount ($)"] = "0"
df["Item"] = pd.NA
df["Job No."] = pd.NA
df["Job name"] = pd.NA
df["Discount %"] = pd.NA

df["Unit Price"] = df["Unit Price"].astype(str) \
    .str.replace('$', '', regex=False) \
    .str.replace(',', '') \
    .str.strip()

df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors='coerce')

# Make Amount ($) same as Unit Price
df["Amount ($)"] = df["Unit Price"]



from dateutil import parser

def parse_date_safe(date_str):
    try:
        return parser.parse(str(date_str)).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return pd.NA  # Or use '' if you want blank

df["Transaction date"] = df["Transaction date"].apply(parse_date_safe)


def parse_date_safe(date_str):
    try:
        return parser.parse(str(date_str)).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return pd.NA  # You can use '' instead if blank is preferred

df["Due date"] = df["Due date"].apply(parse_date_safe)



# Desired column order
columns_order = [
    "Bill number", "Supplier", "Transaction date", "Due date", "Supplier invoice number",
    "Amounts are", "Item", "Description", "Account No.", "No. of Unit",
    "Unit Price", "Discount %", "Amount ($)", "Tax code", "Tax amount ($)", "Job No.", "Job name"
]

# Keep only available columns
final_columns = [col for col in columns_order if col in df.columns]
df = df[final_columns]

# Export to Excel
output_path = r"/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/OPEN BILL/OPEN_BILL.xlsx"
df.to_excel(output_path, sheet_name="Bill", index=False)

print(df.head())
print("✅ Conversion Successful! Due date column mapped correctly.")