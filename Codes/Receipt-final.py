import pandas as pd
import random  
import os 
df = pd.read_csv("/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/RECIEPT/receipt.xlsx - Sheet1.csv")
df_COA = pd.read_csv("/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/RECIEPT/MYOB-COA-Mapping.xlsx - Sheet1-2.csv")

field_mapping = {
    "Balancing Account Name": "Bank Account",
    "Contact": "Contact",
    "Number": "Reference number",
    "Date": "Date",
    "Account Name": "Account",
    "Amount": "Amount",
    "Description": "Description",
    "Tax Code": "Tax Code"
}

df = df.rename(columns=field_mapping)

df["Description of transaction"] = pd.NA
df["Amounts are"] = "Tax exclusive"
df["Quantity"] = pd.NA
df["Job"] = pd.NA

Tax_Code_Mapping = {
    "AJS": "GST",
    "CAF": "FRE",
    "CAG": "GST",
    "FRE": "FRE",
    "GST": "GST",
    "INP": "INP",
    "NCF": "FRE",
    "NCG": "GST",   # problem solved 
    "NTD": "FRE",
    "CDS": "CDS",
    "CDC": "CDC",
    "WC": "WC",
    "EXP": "FRE",
    "WGST": "WGST",
    "NCI": "N-T",
    "CAI": "N-T",
    "WET": "WET",
    "": "N-T",
    "AJA": "GST"
}

df["Tax Code"] = df["Tax Code"].map(Tax_Code_Mapping)
df['Tax Code'] = df['Tax Code'].replace(r'^\s*$', pd.NA, regex=True)
# Replace NA (including None) with 'N-T'
df['Tax Code'] = df['Tax Code'].fillna('N-T')

# date Conversion 

# Convert 'Date' column to datetime if it's not already
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# Format date as M/D/YYYY (no leading zeros)
df['Date'] = df['Date'].dt.strftime('%-d/%-m/%Y')



# ✅ Map Account using Account Name → New Code
df["Account"] = df["Account"].astype(str).str.strip()
df_COA["Account Name"] = df_COA["Account Name"].astype(str).str.strip()
df_COA["New Code"] = df_COA["New Code"].astype(str).str.strip()

# Create mapping dictionary
account_map = dict(zip(df_COA["Account Name"], df_COA["New Code"]))

# Apply mapping to Account column
def map_account(account):
    account = str(account).strip()
    account_cleaned = account.split(":")[-1].strip() if ":" in account else account
    return account_map.get(account_cleaned, f"UNMAPPED:{account_cleaned}")

df["Account"] = df["Account"].apply(map_account)



# Clean 'Bank Account' values
df["Bank Account"] = df["Bank Account"].astype(str).str.strip()

# Reuse the same mapping dictionary from Old Account Name → New Code
# (already created as `account_map` above)

# Map Bank Account column using same mapping
def map_bank_account(bank_account):
    bank_account = str(bank_account).strip()
    bank_account_cleaned = bank_account.split(":")[-1].strip() if ":" in bank_account else bank_account
    return account_map.get(bank_account_cleaned, f"UNMAPPED:{bank_account_cleaned}")

df["Bank Account"] = df["Bank Account"].apply(map_bank_account)




columns_order = [
    "Bank Account", "Contact", "Description of transaction", "Reference number", "Date", "Amounts are", "Account", "Amount", 
    "Quantity", "Description", "Job", "Tax Code"
]

final_columns = [col for col in columns_order if col in df.columns]
df = df[final_columns]

# Export final file
output_path = r"/Users/vedantkanojiya/Desktop/MMC INTERNSHIP/RECKON ONE TO MYOB/FILE/RECIEPT/RECIEVE MONEY TO MYOB.xlsx"
df.to_excel(output_path, sheet_name="Recieve Money", index=False)

print(df.head())
print("✅ Conversion Successful!")