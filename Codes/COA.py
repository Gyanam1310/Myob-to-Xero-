import pandas as pd
import random
import os
from config import get_file

# 1️⃣  Load the raw file

FILE_IN  = (get_file("RAW_ACCOUNT_FILE"))
FILE_OUT = get_file("MYOB_COA")

def read_file(path: str, skiprows: int = 0) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path, skiprows=skiprows)
    if ext in (".xls", ".xlsx"):
        return pd.read_excel(path, skiprows=skiprows)
    if ext == ".txt":
        return pd.read_csv(path, delimiter="\t", skiprows=skiprows)
    raise ValueError(f"Unsupported file type: {ext}")

df = read_file(FILE_IN, skiprows=4)


# 2️⃣  Basic clean‑up & renaming
df.columns = df.columns.str.strip().str.title()
df.dropna(how="all", inplace=True)

field_mapping = {
    "Account Code":"Account Number",
    "Account Name":"Account Name",
    "Type":"Account Type",
    "Default Tax Code":"Tax Code",
}
df = df.rename(columns=field_mapping)
df["Header"] = pd.NA

# Normalise account types
df["Account Type"] = df["Account Type"].str.title()
type_mapping = {
    "Bank": "Bank",  "Cost Of Goods Sold": "CostofSales",
    "Credit Card": "Creditcard",           "Equity": "Equity",
    "Income": "Income",                    "Other Current Asset": "OtherCurrentAsset",
    "Other Asset": "OtherCurrentAsset",    "Other Current Liability": "OtherCurrentLiability",
    "Fixed Asset": "FixedAsset",           "Expense": "Expense",
    "Long Term Liability": "LongTermLiability",
    "Suspense": "LongTermLiability",       "Non-Posting": "OtherCurrentLiability",
    "Other Income": "OtherIncome",         "Other Expense": "OtherExpense",
    "Other Liability": "OtherCurrentLiability",
    "Cost Of Sales": "CostofSales",        "Current Asset": "OtherCurrentAsset",
    "Other Non-Current Asset": "OtherCurrentAsset",
}
df["Account Type"] = df["Account Type"].map(type_mapping)

# Tax‑code mapping
tax_code_mapping = {
    "AJS":"GST","CAF":"FRE","CAG":"GST","FRE":"FRE","GST":"GST","INP":"INP","NCF":"FRE",
    "NCG":"GST","NTD":"FRE","CDS":"CDS","CDC":"CDC","WC":"WC","EXP":"FRE","WGST":"WGST",
    "NCI":"N-T","CAI":"N-TWET","WET":"WET","":"N-T",
}
df["Tax Code"] = (
    df["Tax Code"].astype(str)
    .str.strip()
    .replace("-", "")
    .map(tax_code_mapping)
)
import re

# ──🆕  Clean up Account Name formatting ───────────────────────────────
def clean_account_name(name):
    if pd.isna(name):
        return name
    name = str(name).strip()
    name = re.sub(r"\s*-\s*", "-", name)  # remove spaces around hyphen
    name = re.sub(r"\s+", " ", name)      # collapse multiple spaces to one
    return name

df["Account Name"] = df["Account Name"].apply(clean_account_name)

# 3️⃣  Fill *missing* Account Numbers
#     (existing values remain exactly as they are)
# 3a. normalise the column
df["Account Number"] = (
    df["Account Number"]
    .astype(str)
    .str.strip()
    .replace({"": pd.NA, "-": pd.NA, "nan": pd.NA})
)

# 3b. pick prefix from Account Type
type_to_prefix = {
    "Bank":"1", "OtherCurrentAsset":"1", "FixedAsset":"1",
    "OtherCurrentLiability":"2", "Creditcard":"2", "LongTermLiability":"2",
    "Equity":"3",
    "Income":"4",
    "CostofSales":"5",
    "Expense":"6",
    "OtherIncome":"8",
    "OtherExpense":"9",
}

def fill_missing_account_numbers(df_: pd.DataFrame) -> None:
    used_suffixes = (
        df_["Account Number"]
        .dropna()
        .str.extract(r"(\d{4})")[0]
        .dropna()
        .astype(int)
        .tolist()
    )
    pool = list(set(range(1000, 10000)) - set(used_suffixes))

    needed = df_["Account Number"].isna().sum()
    if needed > len(pool):
        raise ValueError("Not enough unique 4‑digit codes left.")

    new_codes = random.sample(pool, needed)
    na_rows   = df_[df_["Account Number"].isna()].index

    for idx, suffix in zip(na_rows, new_codes):
        acc_type = df_.at[idx, "Account Type"]
        prefix   = type_to_prefix.get(acc_type, "0")  # fallback '0'
        df_.at[idx, "Account Number"] = f"{prefix}-{suffix:04d}"
# ──🆕 3c. replace “‑0000” with a unique random suffix ─────────────────────────
def replace_0000_suffixes(df_: pd.DataFrame) -> None:
    """
    For every Account Number of the form  X-0000  (4 zeros after the hyphen),
    pick a unique 4‑digit number that is **not** already in use anywhere else
    in the column and rewrite the code in‑place.
    """
    # rows that need a new suffix
    zero_mask = df_["Account Number"].str.fullmatch(r"\d-\s*0000", na=False)

    if not zero_mask.any():
        return                                  # nothing to do

    # all 4‑digit numbers currently present (after any hyphen)
    used_suffixes = (
        df_["Account Number"]
        .dropna()
        .str.extract(r"(\d{4})")[0]
        .dropna()
        .astype(int)
        .tolist()
    )
    pool = list(set(range(1000, 10000)) - set(used_suffixes))

    needed = zero_mask.sum()
    if needed > len(pool):
        raise ValueError("Not enough unique 4‑digit codes left to replace '-0000'.")

    new_codes = random.sample(pool, needed)

    for idx, suffix in zip(df_[zero_mask].index, new_codes):
        prefix = df_.at[idx, "Account Number"].split("-", 1)[0]  # keep the left part
        df_.at[idx, "Account Number"] = f"{prefix}-{suffix:04d}"

# ──🆕  Convert 5‑digit numbers to "X‑YYYY" format ──────────────
def hyphenate_if_5_digits(val):
    """
    62222  ->  6-2222
    23456  ->  2-3456
    Already hyphenated or not 5 digits → unchanged.
    """
    if pd.isna(val):
        return val
    s = str(val).strip()
    if "-" in s:                         # already hyphenated
        return s
    if s.isdigit() and len(s) == 5:      # pure 5‑digit code
        return f"{s[0]}-{s[1:]}"
    return s

df["Account Number"] = df["Account Number"].apply(hyphenate_if_5_digits)
fill_missing_account_numbers(df)
replace_0000_suffixes(df)   

# 4️⃣  Derive hierarchy
#     Account Number  ➜  Parent  ➜  Classification
# ------------------------------------------------------------
# 4️⃣  Derive Parent & Classification from Account Number
# ------------------------------------------------------------
def parent_from_account(acc_num):
    """'1-2345' → '1-0000'; returns pd.NA if acc_num is missing."""
    if pd.isna(acc_num):
        return pd.NA
    s = str(acc_num).strip()
    prefix = s.split("-", 1)[0]    # text before first hyphen
    prefix = prefix[:1]            # ensure single digit
    return f"{prefix}-0000"

df["Parent Account Number"] = df["Account Number"].apply(parent_from_account)
df["Classification"] = df["Parent Account Number"].str.extract(r"^(\d)")

# 5️⃣  Clean‑ups
# Drop last blank row if the file always has one
df = df.iloc[:-1]

# Remove A/R and A/P rows
pattern = lambda txt: df.astype(str).apply(lambda col: col.str.contains(txt, case=False, na=False))
df = df[~pattern("Accounts Receivable").any(axis=1)]
df = df[~pattern("Accounts Payable").any(axis=1)]

# Safety checks
assert df["Account Number"].is_unique, "Duplicate Account Numbers!"
assert df["Parent Account Number"].notna().all(), "Unmapped prefixes!"
assert df["Classification"].notna().all(), "Classification missing!"


# 6️⃣  Re‑order columns & save
cols = [
    "Account Number", "Account Name", "Account Type", "Header",
    "Parent Account Number", "Tax Code", "Classification",
]
df = df[[c for c in cols if c in df.columns]]

df.to_excel(FILE_OUT, sheet_name="COA", index=False)

print(df.head())
print("Conversion successful!")
