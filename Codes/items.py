import pandas as pd
import os
from config import get_file
item_file_path=get_file("ITEM_LIST_FILE")
def read_file(path: str, skiprows: int = 0) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path, skiprows=skiprows)
    if ext in (".xls", ".xlsx"):
        return pd.read_excel(path, skiprows=skiprows)
    if ext == ".txt":
        return pd.read_csv(path, delimiter="\t", skiprows=skiprows)
    raise ValueError(f"Unsupported file type: {ext}")

item= read_file(item_file_path,skiprows=3)
coa_file_path=get_file("MYOB_COA")
coa=pd.read_excel(coa_file_path)
coa.columns=coa.columns.str.strip().str.title()
# # Only drop if the first row is a header placeholder or irrelevant
# if item.iloc[0].isna().all():
#     item = item.drop(item.index[0])
    # Strip whitespace, normalize case
first_row = item.iloc[0].astype(str).str.strip().str.lower()

# Check if the first row has suspicious values like 'active'
if 'active' in first_row.values:
    item = item.drop(item.index[0])
print(item.head())
item.columns=item.columns.str.strip().str.title()
item.dropna(how='all',inplace=True)

field_mapping={
    "Sale Price (Net)":"Selling Price",
    "Sale Account":"Income account for tracking sales",
    "Sale Tax Code":"Tax Code - Income",
    "Purchase Price (Net)":"Buying Price",
    "Purchase Account":"Expense account for tracking purchases",
    "Purchase Tax Code":"Tax Code - Purchase"
}
item=item.rename(columns=field_mapping)
item["Primary supplier for reorders"]=pd.NA
item["Default reorder quantity (per buying unit)"]=pd.NA
item["Item ID"]=pd.NA
item["Description"]=pd.NA
print(item.head())

"""
    Trims the values in a column so that they do not exceed `char_limit`,
    keeping the last words (not the first) if trimming is needed.
    
    Parameters:
    - df: pandas DataFrame
    - column_name: name of the column to process
    - char_limit: max allowed characters for each entry
    
    Returns:
    - DataFrame with updated column
    """
# def trim_column_keep_last_words(df, column, max_length):
#     trimmed_values = []

#     for val in df[column]:
#         if pd.isna(val):
#             trimmed_values.append(val)
#             continue

#         words = str(val).split()
#         result = ""
#         for word in reversed(words):
#             if result:
#                 temp = word + " " + result
#             else:
#                 temp = word

#             if len(temp) > max_length:
#                 break
#             result = temp

#         trimmed_values.append(result.strip())

#     return pd.Series(trimmed_values)
def trim_column_keep_last_words(df, column, max_length):
    def trim(val):
        if pd.isna(val):
            return val
        words = str(val).split()
        result = ""
        for word in reversed(words):
            temp = word + " " + result if result else word
            if len(temp) > max_length:
                break
            result = temp
        return result.strip()
    
    return df[column].apply(trim)
print(item.head())


def make_column_unique(item, column):
    seen = {}
    new_values = []

    for val in item[column]:
        if pd.isna(val):
            new_values.append(val)
            continue

        if val not in seen:
            seen[val] = 0
            new_values.append(val)
        else:
            seen[val] += 1
            new_values.append(f"{val}_{seen[val]}")

    item[column] = new_values
    return item
item = make_column_unique(item,"Name")
item = make_column_unique(item,"Item ID")

item["Item ID"] =trim_column_keep_last_words(item,'Name',20)
item["Name"]=trim_column_keep_last_words(item,'Name',30)
print(item.head())

# removing dollar symbols and all andthen replacing blank by 0
item['Selling Price'] = item['Selling Price'].astype(str).str.replace(r'[$₹€,]', '', regex=True).str.strip()
item["Selling Price"]=item["Selling Price"].replace('','0')
item["Selling Price"]=item["Selling Price"].replace('-','0')
item['Buying Price'] = item['Buying Price'].astype(str).replace(r'[$₹€,]', '', regex=True).str.strip()
item["Buying Price"]=item["Buying Price"].replace('-','0')
item["Buying Price"]=item["Buying Price"].replace('','0')

# item["Income account for tracking sales"]= item["Income account for tracking sales"].replace('-','Income')
# item["Expense account for tracking purchases"]=item["Expense account for tracking purchases"].replace('-','Expense')
# income_accounts = coa[coa["Account Type"].str.strip().str.title() == "Income"]
# if len(item) <= len(income_accounts):
#     item["Income account for tracking sales"] = income_accounts["Account Number"][:len(item)].values
# else:
#     raise ValueError("Not enough income accounts to map to all item rows.")
# Purchase_accounts = coa[coa["Account Type"].str.strip().str.title() == "Expense"]
# if len(item) <= len(Purchase_accounts):
#     item["Expense account for tracking purchases"] = income_accounts["Account Number"][:len(item)].values
# else:
#     raise ValueError("Not enough purchases accounts to map to all item rows.")
# Find the first account number where Account Type is Income
income_row = coa[coa["Account Type"].str.strip().str.title() == "Income"].iloc[0]
income_account_number = income_row["Account Number"]

# Assign to item file
item["Income account for tracking sales"] = income_account_number
# Find the first account number where Account Type is Income
Purchase_row = coa[coa["Account Type"].str.strip().str.title() == "Expense"].iloc[0]
Purchase_account_number = Purchase_row["Account Number"]

# Assign to item file
item["Expense account for tracking purchases"] = Purchase_account_number


item["Primary supplier for reorders"]=pd.NA
item["Default reorder quantity (per buying unit)"]=pd.NA

# tax code mapping
Tax_Code_Mapping ={
    "AJS":"GST",
    "CAF":"FRE",
    "CAG":"GST",
    "FRE":"FRE",
    "GST":"GST",
    "INP":"INP",
    "NCF":"FRE",
    "NCG":"GST",
    "NTD":"FRE",
    "CDS":"CDS",
    "CDC":"CDC",
    "WC":"WC",
    "EXP":"FRE",
    "WGST":"WGST",
    "NCI":"N-T",
    "CAI":"N-TWET",
    "WET":"WET",
    "":"N-T"
}

print(item["Tax Code - Income"].head())
item["Tax Code - Income"]=item["Tax Code - Income"].replace('-',"").replace(' ',"")
item["Tax Code - Income"]=item["Tax Code - Income"].map(Tax_Code_Mapping).rename("Tax Code")
print(item["Tax Code - Income"].head())
item["Tax Code - Purchase"]=item["Tax Code - Purchase"].replace('-',"").replace(' ',"")
item["Tax Code - Purchase"]=item["Tax Code - Purchase"].map(Tax_Code_Mapping).rename("Tax code")

item["Item ID"] = item["Item ID"].str.replace('- ', '', regex=False)


columns_order=["Name","Description","Item ID","Selling Price","Income account for tracking sales","Tax Code","Buying Price","Expense account for tracking purchases","Tax code","Primary supplier for reorders","Default reorder quantity (per buying unit)"]
final_columns = [col for col in columns_order if col in item.columns]
item = item[final_columns]

# new file output
item.to_excel(get_file("MYOB_ITEM"),sheet_name='item',index=False)

# checking if any syntax error 
print("Conversion successful!")