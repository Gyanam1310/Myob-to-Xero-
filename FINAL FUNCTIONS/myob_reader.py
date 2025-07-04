import pandas as pd
import re

bad_line_count = 0
bad_line_numbers = []

def is_probable_header(line):
    """
    Basic heuristic to decide if a line looks like a header:
    For example, contains alphabets and more than 3 columns.
    Customize as needed.
    """
    split_cols = re.split(r'\t+|\s{2,}', line.strip())
    if len(split_cols) < 3:
        return False
    # At least one column should have alphabetic characters
    if any(re.search(r'[A-Za-z]', col) for col in split_cols):
        return True
    return False

def detect_header_line(file_obj, max_lines=10):
    file_obj.seek(0)
    lines = file_obj.readlines()

    for i in range(min(max_lines, len(lines))):
        line = lines[i]
        decoded = line.decode('utf-8', errors='ignore') if isinstance(line, bytes) else line
        cleaned = decoded.strip()

        # Skip junk lines that contain '{}' anywhere or are just dashes or empty
        if '{}' in cleaned or cleaned in ['', '{', '}', '–', '—', '-']:
            continue

        if is_probable_header(cleaned):
            return i

    # fallback if none found
    return 0

def safe_split(line):
    line = line.strip('\n\r')
    return line.split('\t') if '\t' in line else re.split(r'\s{2,}', line)

def read_file(file_obj, filename):
    global bad_line_count, bad_line_numbers
    bad_line_count = 0
    bad_line_numbers = []

    ext = filename.split('.')[-1].lower()

    file_obj.seek(0)
    lines = file_obj.readlines()

    # Decode first line safely
    first_line_decoded = lines[0].decode('utf-8', errors='ignore') if isinstance(lines[0], bytes) else lines[0]

    # If first line contains '{}' anywhere, skip it and start header at next line
    if '{}' in first_line_decoded:
        header_line = 1
    else:
        file_obj.seek(0)
        header_line = detect_header_line(file_obj)

    # Debug prints
    header_preview = lines[header_line].decode('utf-8', errors='ignore') if isinstance(lines[header_line], bytes) else lines[header_line]

    if ext == "txt":
        header_raw = lines[header_line].decode('utf-8', errors='ignore') if isinstance(lines[header_line], bytes) else lines[header_line]
        header = safe_split(header_raw)

        data = []
        for i, line in enumerate(lines[header_line + 1:], start=header_line + 1):
            decoded = line.decode('utf-8', errors='ignore') if isinstance(line, bytes) else line
            fields = safe_split(decoded)

            # Normalize field count to header length
            if len(fields) < len(header):
                fields += [''] * (len(header) - len(fields))
            elif len(fields) > len(header):
                fields = fields[:len(header)]

            data.append(fields)

            # Track bad line count if fields don't match header length exactly
            if len(fields) != len(header):
                bad_line_count += 1
                bad_line_numbers.append(i)

        df = pd.DataFrame(data, columns=[h.strip() for h in header])

    elif ext == "csv":
        file_obj.seek(0)
        try:
            df = pd.read_csv(file_obj, skiprows=header_line, encoding='utf-8')
        except UnicodeDecodeError:
            file_obj.seek(0)
            df = pd.read_csv(file_obj, skiprows=header_line, encoding='ISO-8859-1')

    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_obj, skiprows=header_line)

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Strip column names
    df.columns = df.columns.astype(str).str.strip()

    # Remove currency symbols and curly braces from all cells and strip spaces
    df = df.astype(str).replace(r'[£$€{}]', '', regex=True).apply(lambda col: col.str.strip())

    # Drop rows where all values are NaN or empty after cleaning
    df.replace({'': pd.NA}, inplace=True)
    df.dropna(how='all', inplace=True)

    return df
