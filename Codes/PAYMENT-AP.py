import pandas as pd
import random 
import os

df = pd.read_csv("/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/PAYMENT AP/payment raw sheet.xlsx - Sheet1.csv")
df_COA = pd.read_csv("/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/RECIEPT/MYOB-COA-Mapping.xlsx - Sheet1-2.csv")


field_mapping = {
    "Contact": "Supplier",
    "Number": "Reference number",
    "Date": "Date",
    "Balancing Account Name": "Bank account",
    "Description": "Description of transaction",
    # "Description": "Bill Number",
    "Amount": "Amount Paid"
}

df = df.rename(columns=field_mapping)


from dateutil import parser

def parse_date_safe(date_str):
    try:
        return parser.parse(str(date_str)).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return pd.NA  # Or use '' if you want blank

df["Date"] = df["Date"].apply(parse_date_safe)

# Extract the last word in the Description assuming it's always the bill number
df["Bill Number"] = df["Description of transaction"].str.extract(r'(BIL\d+)', expand=False)


# Strip spaces and prepare mapping
df["Bank account"] = df["Bank account"].astype(str).str.strip()
df_COA["Account Name"] = df_COA["Account Name"].astype(str).str.strip()
df_COA["New Code"] = df_COA["New Code"].astype(str).str.strip()

# Create mapping dictionary
bank_account_map = dict(zip(df_COA["Account Name"], df_COA["New Code"]))

# Apply mapping function
def map_bank_account(value):
    value_clean = str(value).strip()
    value_clean = value_clean.split(":")[-1].strip() if ":" in value_clean else value_clean
    return bank_account_map.get(value_clean, f"UNMAPPED:{value_clean}")

df["Bank account"] = df["Bank account"].apply(map_bank_account)



# Desired column order
columns_order = [
    "Supplier", "Reference number", "Date", "Bank account", "Description of transaction", "Bill Number", "Amount Paid"
]

# Keep only available columns
final_columns = [col for col in columns_order if col in df.columns]
df = df[final_columns]

# Export to Excel
output_path = r"/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/PAYMENT AP/MYOB - COA - PAYMENT_AP.xlsx"
df.to_excel(output_path, sheet_name="Supplier Payment", index=False)

print(df.head())
print("✅ Conversion Successful! Due date column mapped correctly.")