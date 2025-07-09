import pandas as pd 
import os 
from config import get_file
df = df = pd.read_excel(get_file("Payment_list"))
df_COA = pd.read_excel(get_file("MYOB_COA_MAPPING"))


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

# Format date as D/M/YYYY (no leading zeros)
df['Date'] = df['Date'].dt.strftime('%Y/%-m/%-d')



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
# (already created as account_map above)
print("\n🔍 Top 10 unique 'Bank Account' values before mapping:")
print(df["Bank Account"].dropna().unique()[:10])

print("\n🔍 Top 10 unique 'Account Name' values in df_COA:")
print(df_COA["Account Name"].dropna().unique()[:10])