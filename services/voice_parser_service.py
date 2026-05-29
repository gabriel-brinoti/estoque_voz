import re
from services.normalizer_service import normalize_barcode, normalize_product, normalize_lote, normalize_date

def parse_voice_command(command):
    text = " ".join((command or "").strip().split())

    item = {
        "codigo_barras": normalize_barcode(extract_codigo(text)),
        "produto": normalize_product(extract_produto(text)),
        "quantidade": extract_quantidade(text),
        "lote": normalize_lote(extract_lote(text)),
        "validade": normalize_date(extract_validade(text)),
    }

    return [item]

def extract_codigo(text):
    match = re.search(r"(?:c[oó]digo de barras|codigo de barras|c[oó]digo|codigo|ean|barra)\s*[:\-]?\s*([\d\s]{8,40})", text, re.I)
    if match:
        return match.group(1)

    nums = re.findall(r"\b[\d\s]{8,40}\b", text)
    nums = ["".join(re.findall(r"\d", n)) for n in nums]
    nums = [n for n in nums if len(n) >= 8]
    return sorted(nums, key=len, reverse=True)[0] if nums else ""

def extract_produto(text):
    marker = r"(?:c[oó]digo de barras|codigo de barras|c[oó]digo|codigo|ean|barra|quantidade|qtd|qtde|lote|validade|vencimento)"
    match = re.search(r"produto\s*[:\-]?\s*(.*?)(?=,\s*" + marker + r"|\s+" + marker + r"|$)", text, re.I)
    if match:
        return match.group(1).strip(" ,.-")

    return ""

def extract_quantidade(text):
    match = re.search(r"(?:quantidade|qtd|qtde)\s*[:\-]?\s*(\d+)", text, re.I)
    if match:
        return match.group(1)

    match = re.search(r"\b(\d+)\s*(?:unidades|unidade|un|und|caixas|caixa|cx)\b", text, re.I)
    return match.group(1) if match else "1"

def extract_lote(text):
    marker = r"(?:validade|vencimento|produto|c[oó]digo de barras|codigo de barras|c[oó]digo|codigo|ean|quantidade|qtd|qtde)"
    match = re.search(r"lote\s*[:\-]?\s*([A-Za-z0-9\-\/\. ]{1,30})(?=,\s*" + marker + r"|\s+" + marker + r"|$)", text, re.I)
    return match.group(1).strip(" ,.-") if match else ""

def extract_validade(text):
    match = re.search(r"\b(\d{2}[\/\-.]\d{2}[\/\-.]\d{4})\b", text)
    if match:
        return match.group(1)

    match = re.search(r"(?:validade|vencimento|vence)\s*[:\-]?\s*(\d{2})\s*(?:de\s*)?(\d{2})\s*(?:de\s*)?(\d{4})", text, re.I)
    if match:
        return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

    return ""
