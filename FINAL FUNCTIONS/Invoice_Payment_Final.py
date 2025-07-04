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

csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\INVOICEPAYMENT.TXT"

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

column_mapping = {
    'date1': 'Date',
    'bankcode': 'Bank',
    'Ref': 'Reference', 
    'amount': 'Amount',
    'INVNO': 'Invoice No',
    "Exchange": "Exchange"
}

df = df.rename(columns=column_mapping)

df['Date'] = df['Date'].astype(str).str.extract(r'DatD:(.*)')

df['Bank'] = df['Bank'].astype(str).str.extract(r'Code-(\d)-(\d+)$').agg(''.join, axis=1)

df['Reference'] = [f"{val}-{i+1}" for i, val in enumerate(df['Reference'].astype(str))]

columns_order = ["Date", "Invoice No", "Amount", "Bank", "Reference", "Currency rate"]

df = df.reindex(columns=columns_order, fill_value="")

df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\XERO_INVOICE_PAYMENT.csv", index=False)

print("File converted successfully!")