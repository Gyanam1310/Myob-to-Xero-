import pandas as pd, re
from config import get_file

# ── 1. Load ──────────────────────────────────────────────────────────
df  = pd.read_excel(get_file("MYOB_COA"))              
df1 = pd.read_excel(get_file("RAW_ACCOUNT_FILE"), skiprows=4)    # holds *old* codes

# ── 2. Trim column names & smart‑rename ─────────────────────────────
df.columns  = df.columns.str.strip()
df1.columns = df1.columns.str.strip()

df.rename(columns={'Account Number': 'New Code'}, inplace=True)
# helper to rename flexibly
def smart_rename(df_, logical, new):
    logical = logical.lower().replace(" ", "")
    for c in df_.columns:
        if c.lower().replace(" ", "") == logical:
            df_.rename(columns={c: new}, inplace=True); return
    raise KeyError(f"Column like ‘{logical}’ not found")

smart_rename(df1, "Account Code",  "Old Code")
smart_rename(df1, "Account Name",  "Old Account Name")

df1.dropna(how="all", inplace=True)

# ── 3. Canonicalise Account Names in *both* files ───────────────────
def canonical(s):
    if pd.isna(s): return s
    s = str(s).strip()
    s = re.sub(r"\s*-\s*", "-", s)   # trim around hyphens
    s = re.sub(r"\s+",  " ", s)      # collapse spaces
    return s

df["Account Name"]       = df["Account Name"].apply(canonical)
df1["Old Account Name"]  = df1["Old Account Name"].apply(canonical)

# ── 4. Clean dash‑only OLD codes *before* mapping ───────────────────
dash_regex = r"^[\s\u002D\u2010-\u2015]+$"
df1["Old Code"] = df1["Old Code"].astype(str).str.strip() \
                               .replace(dash_regex, pd.NA, regex=True)

# ── 5. Merge to bring in Old Account Name + Old Code ────────────────
merged = (
    df.merge(                      # left‑join keeps every row in df
        df1[["Old Account Name", "Old Code"]],
        how="left",
        left_on="Account Name",
        right_on="Old Account Name"
    )
)

# ── 6. Final reorder & export ───────────────────────────────────────
final_cols = ["Old Account Name", "Account Name", "Account Type",
   "Parent Account Number", "Old Code", "New Code"
    
]

final_df=merged.reindex(columns=final_cols)
final_df.to_excel(get_file("MYOB_COA_MAPPING"), index=False)
print("✅ Mapping finished.")

# # # import pandas as pd

# # # # Load main file
# # # df = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA.xlsx")
# # # df1 = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\Raw Account List.xlsx", skiprows=4)

# # # # Clean column names (don't change case of values)
# # # df.columns = df.columns.str.strip()
# # # df1.columns = df1.columns.str.strip()

# # # # Rename for consistency
# # # df1=df1.rename(columns={'Account Code': 'Old Code'})
# # # df = df.rename(columns={'Account Number': 'New Code'})
# # # df1 = df1.rename(columns={'Account Name': 'Old Account Name'})

# # # # Clean column names for both files
# # # df.columns = df.columns.str.strip()
# # # df1.columns = df1.columns.str.strip()

# # # # Show columns to confirm
# # # print("df1 Columns:", df1.columns.tolist())

# # # # Confirm the actual column name for old account names
# # # # Use exact match ignoring case
# # # match = [col for col in df1.columns if col.strip().lower() == 'account name']

# # # if not match:
# # #     raise KeyError("Column 'Account Name' not found in df1. Check for typos or spacing issues.")
# # # else:
# # #     df1 = df1.rename(columns={match[0]: 'Old Account Name'})

# # # # Drop completely empty rows
# # # df1.dropna(how='all', inplace=True)

# # # # Clean value strings (strip, but no title-casing)
# # # df['Account Name'] = df['Account Name'].astype(str).str.strip()
# # # df1['Old Account Name'] = df1['Old Account Name'].astype(str).str.strip()

# # # # Create a mapping dictionary: key = Account Name, value = Old Account Name
# # # mapping_dict = dict(zip(df1['Old Account Name'], df1['Old Account Name']))

# # # # Apply mapping (match by exact Account Name)
# # # df['Old Account Name'] = df['Account Name'].map(mapping_dict)

# # # # Create a dictionary: key = Old Account Name, value = Old Code (even if empty)
# # # code_map = dict(zip(df1['Old Account Name'], df1['Old Code']))

# # # # Map Old Code based on Account Name
# # # df1['Old Code'] = df['Account Name'].map(code_map)


# # # # Final column order
# # # final_columns = [
# # #     "Old Account Name",
# # #     "Account Name",
# # #     "Account Type",
# # #     "Parent Account Number",
# # #     "Old Code",
# # #     "New Code"
# # # ]

# # # # Filter and reorder the columns, only keep if they exist
# # # final_df = df[[col for col in final_columns if col in df.columns]]

# # # # Export to Excel
# # # final_df.to_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA-Mapping.xlsx", index=False)

# # # print("Conversion successful.")
# # import pandas as pd

# # # 1) Load
# # df  = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA.xlsx")
# # df1 = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\Raw Account List.xlsx", skiprows=4)

# # # 2) Trim column names
# # df.columns  = df.columns.str.strip()
# # df1.columns = df1.columns.str.strip()

# # # 3) Rename for consistency
# # df  = df.rename(columns={'Account Number': 'New Code'})
# # df1 = df1.rename(columns={'Account Code' : 'Old Code',
# #                           'Account Name' : 'Old Account Name'})

# # # 4) Remove blank rows in df1
# # df1.dropna(how="all", inplace=True)

# # # 5) Strip the name columns (values)
# # df['Account Name']      = df['Account Name'].astype(str).str.strip()
# # df1['Old Account Name'] = df1['Old Account Name'].astype(str).str.strip()

# # # 6) Build look‑up dictionaries
# # name_exists = set(df1['Old Account Name'])
# # code_map    = dict(zip(df1['Old Account Name'], df1['Old Code']))

# # # 7) Add Old‑side columns to df
# # df['Old Account Name'] = df['Account Name'].where(df['Account Name'].isin(name_exists))
# # df['Old Code']         = df['Account Name'].map(code_map)        # stays NaN/blank if not found

# # # 8) Re‑order & export
# # final_columns = [
# #     "Old Account Name", "Account Name", "Account Type",
# #     "Parent Account Number", "Old Code", "New Code"
# # ]
# # final_df = df[[c for c in final_columns if c in df.columns]]
# # final_df.to_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA-Mapping.xlsx", index=False)

# # print("Conversion successful.")
# import pandas as pd

# # 1) Load
# df  = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA.xlsx")
# df1 = pd.read_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\Raw Account List.xlsx", skiprows=4)

# # 2) Trim column names
# df.columns  = df.columns.str.strip()
# df1.columns = df1.columns.str.strip()

# # 3) Robust rename
# def smart_rename(df, logical_name, new_name):
#     logical = logical_name.lower().replace(" ", "")
#     for col in df.columns:
#         if col.lower().replace(" ", "") == logical:
#             df.rename(columns={col: new_name}, inplace=True)
#             return
#     raise KeyError(f"Column matching ‘{logical_name}’ not found in df.")

# df.rename(columns={'Account Number': 'New Code'}, inplace=True)
# smart_rename(df1, "Account Code",  "Old Code")
# smart_rename(df1, "Account Name",  "Old Account Name")

# # 4) Remove blank rows in df1
# df1.dropna(how="all", inplace=True)

# # 5) Strip value strings
# df['Account Name']      = df['Account Name'].astype(str).str.strip()
# df1['Old Account Name'] = df1['Old Account Name'].astype(str).str.strip()
# import re

# def canonical_name(s):
#     """
#     Strip, collapse inner whitespace, remove spaces around hyphens.
#     Return pd.NA unchanged.
#     """
#     if pd.isna(s):
#         return s
#     s = str(s).strip()
#     s = re.sub(r"\s*-\s*", "-", s)   # trim around hyphen
#     s = re.sub(r"\s+", " ", s)       # collapse runs of spaces
#     return s

# # apply to *both* dataframes
# df['Account Name']       = df['Account Name'].apply(canonical_name)
# df1['Old Account Name']  = df1['Old Account Name'].apply(canonical_name)

# # --- clean Old Code first ---------------------------------------------
# dash_regex = r"^[\s\u002D\u2010-\u2015]+$"
# df1["Old Code"] = (df1["Old Code"]
#                    .astype(str).str.strip()
#                    .replace(dash_regex, pd.NA, regex=True))

# # 6) Look‑ups  (now the codes are clean)
# code_map = dict(zip(df1['Old Account Name'], df1['Old Code']))



# df['Old Account Name'] = df['Account Name'].where(
#     df['Account Name'].isin(df1['Old Account Name'])
# )
# df['Old Code'] = df['Account Name'].map(code_map)   # stays blank/NaN if missing
# # df['Old Code']=df["Old Code"].str.replace('-',pd.NA)
# # Clean Old Code to replace hyphen-only values with NaN
# # Replace ANY dash‑only cell (ASCII, en‑dash, em‑dash, etc.) with NA
# dash_regex = r"^[\s\u002D\u2010-\u2015]+$"   # spaces + any dash char only
# df1["Old Code"] = (
#     df1["Old Code"]
#         .astype(str).str.strip()
#         .replace(dash_regex,"nan", pd.NA, regex=True)
# )
# df["Old Code"] = (
#     df["Old Code"]
#         .astype(str).str.strip()
#         .replace(dash_regex,"nan", pd.NA, regex=True)
# )

# # 7) Export
# final_columns = [
#     "Old Account Name", "Account Name", "Account Type",
#     "Parent Account Number", "Old Code", "New Code"
# ]
# final_df = df[[c for c in final_columns if c in df.columns]]
# final_df.to_excel(r"D:\RishiWork\4-Personal\internship 2\reckon one to MYOB\COA\MYOB-COA-Mapping.xlsx", index=False)

# print("Conversion successful.")

