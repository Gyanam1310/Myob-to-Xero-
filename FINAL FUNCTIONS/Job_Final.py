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


# Load the Excel file using read_file
file_path = r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\MYOB-RAW-DATA\Jobs .csv"
with open(file_path, 'rb') as f:
    df = read_file(f, os.path.basename(file_path))

if {"Job Number", "Job Name"}.issubset(df.columns):
    df["Job"] = df["Job Number"].astype(str) + "-" + df["Job Name"].astype(str)
    df.drop(columns=["Job Name"], inplace=True)
    df = df[["Job"]]
    df.to_csv(r"C:\Users\gyana\OneDrive\Desktop\MMC CONVERT\Myob To Xero Python\Data Sets\Infracorr Consulting Pty Ltd (Neharika)\XERO DATA\XERO_Job.csv", index=False)
    print("Converted Successfully")
else:
    print("Warning: Required columns 'Job Number' and/or 'Job Name' are missing.")
