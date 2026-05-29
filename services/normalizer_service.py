import re
import unicodedata
from datetime import datetime

def remove_accents(value):
    normalized = unicodedata.normalize("NFD", str(value or ""))
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

def only_digits(value):
    return re.sub(r"\D", "", str(value or ""))

def normalize_barcode(value):
    value = str(value or "").strip()
    return "" if value in ["-", "None", "none"] else only_digits(value)

def normalize_product(value):
    return re.sub(r"\s+", " ", str(value or "").upper().strip())

def normalize_product_for_match(value):
    value = remove_accents(value).upper().strip()
    value = re.sub(r"[^A-Z0-9 ]", " ", value)
    return re.sub(r"\s+", " ", value).strip()

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
            return datetime.strptime(value, fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return value

def make_key(item):
    return (normalize_product(item.get("produto", "")), normalize_lote(item.get("lote", "")))


def normalize_text(value):
    return normalize_product(value)
