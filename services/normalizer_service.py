import re
from datetime import datetime

def only_digits(value):
    return re.sub(r"\D", "", str(value or ""))

def normalize_barcode(value):
    value = str(value or "").strip()
    if value in ["-", "None", "none"]:
        return ""
    return only_digits(value)

def normalize_product(value):
    value = str(value or "").upper().strip()
    return re.sub(r"\s+", " ", value)

def normalize_lote(value):
    value = str(value or "").upper().strip()
    if value in ["-", "NONE"]:
        return ""
    return re.sub(r"\s+", "", value)

def normalize_date(value):
    if not value:
        return ""

    value = str(value).strip().replace("-", "/").replace(".", "/")

    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            pass

    return value

def make_key(item):
    return (
        normalize_product(item.get("produto", "")),
        normalize_lote(item.get("lote", "")),
    )
