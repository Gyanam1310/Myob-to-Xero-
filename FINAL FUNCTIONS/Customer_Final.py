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

# Usage example:
file_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Customer.csv"
filename = os.path.basename(file_path)

with open(file_path, 'rb') as f:
    df = read_file(f, filename)

# print(f"Bad lines encountered: {bad_line_count}")
# if bad_line_numbers:
#     print("Bad line numbers:", bad_line_numbers)
# else:
#     print("✅ No bad lines encountered.")
# print("Conversion Completed Successfully!")

# Column mapping dictionary directly in the script
column_mapping = {
    "Co./Last Name": "*ContactName",
    "Card ID": "AccountNumber",
    "Addr 1 - Line 1": "POAddressLine1",
    "Addr 1 - Line 2": "POAddressLine2",
    "Addr 1 - Line 3": "POAddressLine3",
    "Addr 1 - Line 4": "POAddressLine4",
    "Addr 1 - City": "POCity",
    "Addr 1 - State": "PORegion",
    "Addr 1 - Postcode": "POPostalCode",
    "Addr 1 - Country": "POCountry",
    "Addr 1 - Phone No. 1": "PhoneNumber",
    "Addr 1 - Phone No. 2": "MobileNumber",
    "Addr 1 - Fax No.": "FaxNumber",
    "Addr 1 - Email": "EmailAddress",
    "Addr 1 - WWW": "Website",
    "Addr 1 - Salutation": "SAAttentionTo",
    "Addr 2 - Line 1": "SAAddressLine1",
    "Addr 2 - Line 2": "SAAddressLine2",
    "Addr 2 - Line 3": "SAAddressLine3",
    "Addr 2 - Line 4": "SAAddressLine4",
    "Addr 2 - City": "SACity",
    "Addr 2 - State": "SARegion",
    "Addr 2 - Postcode": "SAPostalCode",
    "Addr 2 - Country": "SACountry",
    "- % Discount": "Discount",
    "Tax ID No.": "TaxNumber",
    "Account Number": "AccountNumber",
    "Account Name": "BankAccountName",
    "A.B.N.": "TaxNumber",
    "Account": "SalesAccount",
    "- Balance Due Days": "DueDateSalesDay",
    "Terms - Payment is Due": "DueDateSalesTerm"
}

# print("Columns found:", df.columns.tolist())

# Combined First Name and Last Name into ContactName
df["ContactName"] = df["First Name"].fillna('') + " " + df["Co./Last Name"].fillna('')

# Handle missing values in BSB and Account Number, default to 'Unknown' if empty
df["BSB"] = df["BSB"].fillna('Unknown')  # You can change 'Unknown' to another default value
df["Account Number"] = df["Account Number"].fillna('Unknown')  # Same here

# Combine BSB and Account Number into the desired format, avoid '-' if both are 'Unknown'
df["Account Number"] = df.apply(
    lambda row: f"{row['BSB']}-{row['Account Number']}" if row['BSB'] != 'Unknown' and row['Account Number'] != 'Unknown' else 'Unknown', 
    axis=1
)

# Removed First Name and Last Name columns
df = df.drop(columns=["First Name", "Co./Last Name"])

# Removed all columns except ContactName and columns in column_mapping
df = df.drop([col for col in df.columns if col not in column_mapping and col != "ContactName"], axis=1)

# Renamed columns as per column_mapping
df = df.rename(columns=column_mapping)

# Clean the AccountNumber column
df['AccountNumber'] = df['AccountNumber'].replace(["Unkown", "Unknown", "*None"], "")

# Rearranged columns so that ContactName is first
cols = ["ContactName"] + [col for col in df.columns if col != "ContactName"]
df = df[cols]

# Final desired columns
final_columns = [
    "ContactName",
    "AccountNumber",
    "POAddressLine1", "POAddressLine2", "POAddressLine3", "POAddressLine4",
    "POCity", "PORegion", "POPostalCode", "POCountry",
    "PhoneNumber", "MobileNumber", "FaxNumber", "EmailAddress", "Website",
    "SAAttentionTo", "SAAddressLine1", "SAAddressLine2", "SAAddressLine3", "SAAddressLine4",
    "SACity", "SARegion", "SAPostalCode", "SACountry",
    "Discount", "TaxNumber",
    "BankAccountNumber", "BankAccountName",
    "SalesAccount", "DueDateSalesDay", "DueDateSalesTerm"
]

# Step 1: Remove fully empty columns
df = df.dropna(axis=1, how='all')

# Step 2: Remove duplicate columns by name (keep first)
df = df.loc[:, ~df.columns.duplicated()]

# Step 3: Add any missing columns as empty strings
for col in final_columns:
    if col not in df.columns:
        df[col] = ''

# Step 4: Reorder to match final structure
df = df[final_columns]

# Replace all NaN with empty string first
df = df.fillna('')

# Then strip whitespace from all string columns
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()

# Save the cleaned DataFrame to a new CSV file

df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\MYOB_CUSTOMER.CSV", index=False)
# print(f"Bad lines encountered: {bad_line_count}")
print("Conversion Completed Successfully!")
# print(df)