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