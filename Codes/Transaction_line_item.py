import pandas as pd
from config import get_file

# ── 1. Paths ────────────────────────────────────────────────────────────────
RAW_PATH        = get_file("Transaction_line_item")
SEPARATED_PATH  = get_file("MYOB_SEPARATED_FUNCTION")
PAYMENT_PATH    = get_file("MYOB_PAYMENT")
RECEIPT_PATH    = get_file("MYOB_RECEIPT")

# ── 2. Read raw file & separate by “Type” ────────────────────────────────────
df = pd.read_excel(RAW_PATH, skiprows=0)
df.columns = df.columns.str.title()  # Ensure consistent capitalisation

with pd.ExcelWriter(SEPARATED_PATH, engine="openpyxl") as writer:
    for type_name, group in df.groupby("Type"):
        sheet = str(type_name).strip().replace("/", "_")[:31]
        group.to_excel(writer, sheet_name=sheet, index=False)

print(f"\n✅ Step‑1 complete – saved {SEPARATED_PATH}")

# ── 3. Reload workbook and export raw Payment/Receipt sheets ────────────────
all_sheets = pd.read_excel(SEPARATED_PATH, sheet_name=None)

print("\n📄 Exporting raw Payment and Receipt sheets...")
for sheet_name in ("Payment", "Receipt"):
    df_raw = all_sheets.get(sheet_name)
    if df_raw is None or df_raw.empty:
        print(f"⚠️ Sheet “{sheet_name}” not found – skipping export.")
        continue

    out_path = get_file("LINE_ITEM_DIR") / f"{sheet_name}.xlsx"
    df_raw.to_excel(out_path, index=False)
    print(f"✅ Exported raw {sheet_name} sheet → {out_path}")

# ── 4. Split sheets into AP / AR and export ─────────────────────────────────
def split_and_export(sheet_name: str, output_path: str):
    """
    Split a Payment or Receipt sheet into AP / AR / Other *without* altering case
    and write the three sheets to `output_path`.
    """
    df_sheet = all_sheets.get(sheet_name)
    if df_sheet is None or df_sheet.empty:
        print(f"⚠️ No “{sheet_name}” sheet found – skipping.")
        return

    # Masks – case-insensitive search, original text stays intact
    mask_ap = df_sheet['Account Name'].str.contains(r'Accounts Payable', case=False, na=False)
    mask_ar = df_sheet['Account Name'].str.contains(r'Accounts Receivable', case=False, na=False)

    ap   = df_sheet[mask_ap]
    ar   = df_sheet[mask_ar]
    main = df_sheet[~(mask_ap | mask_ar)]  # Everything else

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        main.to_excel(writer, sheet_name=sheet_name, index=False)
        ap.to_excel(writer, sheet_name=f"{sheet_name}_AP", index=False)
        ar.to_excel(writer, sheet_name=f"{sheet_name}_AR", index=False)

    print(f"✅ Exported final split file → {output_path}")

# Run the splitting logic
print("\n Splitting and exporting final Payment and Receipt sheets...")
split_and_export("Payment", PAYMENT_PATH)
split_and_export("Receipt", RECEIPT_PATH)
