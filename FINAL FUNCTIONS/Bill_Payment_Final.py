import pandas as pd
import os 
from pandasgui import show 

def read_file(file_obj, filename):
    """
    Reads a file-like object (from web upload) based on its extension.
    Returns a pandas DataFrame.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(file_obj, encoding='utf-8')
    elif ext in [".xls", ".xlsx"]:
        df = pd.read_excel(file_obj)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

    return df

csv_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\BILLPAYMENT.TXT"

with open(csv_path, 'rb') as f:
    df = read_file(f, os.path.basename(csv_path))

column_mapping = {
    'date1': 'Date',
    'bankcode': 'Bank',
    'Ref': 'Reference', 
    'amount': 'Amount',
    'billNO': 'Invoice No',
    "Exchange": "Exchange"
}

df = df.rename(columns=column_mapping)

df['Date'] = df['Date'].str.extract(r'DatD:(.*)')

df['Bank'] = df['Bank'].astype(str).str.extract(r'Code-(\d)-(\d+)$').agg(''.join, axis=1)

df['Reference'] = [f"{val}-{i+1}" for i, val in enumerate(df['Reference'].astype(str))]

columns_order = ["Date", "Invoice No", "Amount", "Bank", "Reference", "Currency rate"]

df = df.reindex(columns=columns_order, fill_value="")

df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\XERO_Bill_Payment.csv", index=False)

print("File converted successfully!")