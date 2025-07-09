# # import pandas as pd
# # import os
# # file_path=(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\Item list (1).xlsx")
# # def read_file(file_path,index=False):
# #     # this below line is to separete file name and extension and and store it in the form of list where [0] is file name and [1] is extension 
# #     ext = os.path.splitext(file_path)[1].lower()
      
# #     if ext == '.csv':
# #         return pd.read_csv(file_path, skiprows=3)
# #     elif ext in ['.xls', '.xlsx']:
# #         return pd.read_excel(file_path, skiprows=3)
# #     elif ext == '.txt':
# #         return pd.read_csv(item_file_path, delimiter='\t', skiprows=3)  
# #     else:
# #         raise ValueError(f"Unsupported file type: {ext}")
# # item_file_path= read_file(file_path)
# # item_file_path.dropna(how='all',inplace=True)
# # converted_item_file_path=pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\MYOB-item.xlsx")
# # item_file_path=item_file_path
# # # clean
# # item_file_path.columns=item_file_path.columns.str.strip().str.title()
# # converted_item_file_path.columns=converted_item_file_path.columns.str.strip().str.title()
# # item_file_path.dropna(how='all', inplace=True)
# # item_file_path = item_file_path.rename(columns={'Name': 'Old Name'})
# # converted_item_file_path.dropna(how='all', inplace=True)

# # converted_item_file_path['Name'] = converted_item_file_path['Name'].astype(str).str.strip().str.title()
# # item_file_path['Old Name'] = item_file_path['Old Name'].astype(str).str.strip().str.title()

# # merged_df = pd.merge(
# #     converted_item_file_path[['Name','Item Id']],item_file_path[['Old Name']],
# #     left_on='Name',
# #     right_on='Old Name',
# #     how='left'
# # )
# # final_columns=[
# #     "Old Name","Name","Item Id"
# # ]
# # final_df = merged_df[[col for col in final_columns if col in merged_df.columns]]

# # # Export to Excel
# # final_df.to_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\MYOB-item-Mapping.xlsx", index=False)

# # print("Conversion successful.")
import pandas as pd
import os
import re
from config import get_file

# --- Step 1: File paths ---
item_list_path = get_file("ITEM_LIST_FILE")
myob_item_path = get_file("MYOB_ITEM")
output_path = get_file("MYOB_ITEM_MAPPING")

# Trimming function
def trim_column_keep_last_words(text, max_length):
    if pd.isna(text):
        return ""
    words = re.findall(r'\b[\w&]+(?:\'[\w]+)?\b', str(text))
    result = ""
    for word in reversed(words):
        temp = word + " " + result if result else word
        if len(temp) > max_length:
            break
        result = temp
    return result.strip()

# --- Step 3: Load Reckon item list ---
df_item_list = pd.read_excel(item_list_path, skiprows=3)
df_item_list.columns = df_item_list.columns.str.strip().str.title()
df_item_list.dropna(how='all', inplace=True)

# Rename 'Name' to 'Old Name'
if "Name" in df_item_list.columns:
    df_item_list = df_item_list.rename(columns={"Name": "Old Name"})

# Remove extra header row if 'active' is found
first_row = df_item_list.iloc[0].astype(str).str.lower().str.strip()
if 'active' in first_row.values:
    df_item_list = df_item_list.drop(df_item_list.index[0])

# --- Step 4: Load MYOB item list ---
df_myob = pd.read_excel(myob_item_path, sheet_name="item")
df_myob.columns = df_myob.columns.str.strip().str.title()

# Clean string columns
df_myob["Name"] = df_myob["Name"].astype(str).str.strip()
df_myob["Item Id"] = df_myob["Item Id"].astype(str).str.strip()
df_item_list["Old Name"] = df_item_list["Old Name"].astype(str).str.strip()

# --- Step 5: Merge on full name match ---
merged_df = pd.merge(
    df_item_list,
    df_myob[["Name", "Item Id"]],
    left_on="Old Name",
    right_on="Name",
    how="left"
)

# --- Step 6: Trim final output values from Old Name ---
merged_df["MYOB Name"] = merged_df["Old Name"].apply(lambda x: trim_column_keep_last_words(x, 30))
merged_df["MYOB Item ID"] = merged_df["Old Name"].apply(lambda x: trim_column_keep_last_words(x, 20))

# --- Step 7: Final export DataFrame ---
final_df = merged_df[["Old Name", "MYOB Name", "MYOB Item ID"]]

# --- Step 8: Export to Excel ---
final_df.to_excel(output_path, index=False, sheet_name="MYOB-Item-Mapping")
print("✅ Mapping complete. File saved to:", output_path)

# import pandas as pd
# import os

# # Define file paths
# item_list_path = r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\Item list (1).xlsx"
# myob_item_path = r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\MYOB-item.xlsx"
# output_path = r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\item\MYOB-item-Mapping.xlsx"

# # Custom file reader function
# def read_file(file_path, index=False):
#     # This below line is to separate file name and extension and store it in the form of a list
#     # where [0] is the file name and [1] is the extension 
#     ext = os.path.splitext(file_path)[1].lower()
    
#     if ext == '.csv':
#         return pd.read_csv(file_path, skiprows=3)
#     elif ext in ['.xls', '.xlsx']:
#         return pd.read_excel(file_path, skiprows=3)
#     elif ext == '.txt':
#         return pd.read_csv(file_path, delimiter='\t', skiprows=3)  
#     else:
#         raise ValueError(f"Unsupported file type: {ext}")

# # Load files using the custom read_file function
# df_item_list = read_file(item_list_path)
# df_myob_item = pd.read_excel(myob_item_path, sheet_name="item")  # Adjust sheet name as needed

# # Normalize column names
# df_item_list.columns = df_item_list.columns.str.strip().str.title()
# df_myob_item.columns = df_myob_item.columns.str.strip().str.title()

# # Drop empty rows
# first_row = df_item_list.iloc[1 ].astype(str).str.strip().str.title()
# if 'active' in first_row.values:
#     df_item_item = df_item_list.drop(df_item_list.index[0])
# df_item_list.dropna(how='all', inplace=True)
# df_myob_item.dropna(how='all', inplace=True)

# # Rename 'Name' in df_item_list to 'Old Name'
# df_item_list = df_item_list.rename(columns={"Name": "Old Name"})

# # Standardize strings for matching
# df_item_list["Old Name"] = df_item_list["Old Name"].astype(str).str.strip().str.title()
# df_myob_item["Name"] = df_myob_item["Name"].astype(str).str.strip().str.title()

# # Merge on item name
# merged_df = pd.merge(
#     df_item_list[["Old Name"]],
#     df_myob_item[["Name", "Item Id"]],
#     left_on="Old Name",
#     right_on="Name",
#     how="left"
# )

# # Final column selection and renaming
# final_df = merged_df[["Old Name", "Name", "Item Id"]]
# final_df.columns = ["Old Name", "MYOB Name", "MYOB Item ID"]

# # Export result to Excel
# final_df.to_excel(output_path, sheet_name="MYOB-Item-Mapping", index=False)

# print("Mapping successful.")
