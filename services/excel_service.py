import os
import shutil
from copy import copy
from datetime import datetime
from openpyxl import load_workbook
from services.normalizer_service import normalize_barcode, normalize_product, normalize_lote, normalize_date, make_key

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODELO_PATH = os.path.join(BASE_DIR, "modelos", "produtos_2026-05-29.xlsx")
DATA_DIR = os.path.join(BASE_DIR, "data")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
EXCEL_ATUAL_PATH = os.path.join(DATA_DIR, "produtos_atualizado.xlsx")

SHEET_NAME = "Relatório"
HEADER_ROW = 4
FIRST_DATA_ROW = 5

DEFAULTS = {
    "categoria": "Materiais",
    "local": "Almoxarifado",
    "aberto_em": "-",
    "vence_apos_aberto": "-",
    "limite_alerta": 1,
    "status": "Produto OK",
}

EXPECTED_HEADERS = {
    "produto": ["PRODUTO"],
    "categoria": ["CATEGORIA"],
    "local": ["LOCAL"],
    "codigo_barras": ["CÓDIGO DE BARRAS", "CODIGO DE BARRAS", "BARRAS", "EAN", "GTIN"],
    "lote": ["LOTE"],
    "validade": ["VENCIMENTO", "VALIDADE"],
    "aberto_em": ["ABERTO EM"],
    "vence_apos_aberto": ["VENCE APÓS ABERTO", "VENCE APOS ABERTO"],
    "estoque": ["ESTOQUE"],
    "estoque_padrao": ["ESTOQUE PADRÃO", "ESTOQUE PADRAO"],
    "limite_alerta": ["LIMITE ALERTA"],
    "status": ["STATUS"],
}

def ensure_workbook_exists():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists(EXCEL_ATUAL_PATH):
        if os.path.exists(MODELO_PATH):
            shutil.copy(MODELO_PATH, EXCEL_ATUAL_PATH)
        else:
            create_default_workbook(EXCEL_ATUAL_PATH)

def create_default_workbook(path):
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = SHEET_NAME
    ws["A1"] = "Controle Oftalmo"
    ws["A2"] = "Relatório geral de produtos — Todos os estoques"
    headers = [
        "Produto", "Categoria", "Local", "Código de Barras", "Lote", "Vencimento",
        "Aberto em", "Vence após aberto", "Estoque", "Estoque padrão",
        "Limite alerta", "Status"
    ]
    for col, value in enumerate(headers, start=1):
        ws.cell(row=HEADER_ROW, column=col).value = value
    wb.save(path)

def create_backup():
    if not os.path.exists(EXCEL_ATUAL_PATH):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"produtos_backup_{timestamp}.xlsx")
    shutil.copy(EXCEL_ATUAL_PATH, backup_path)
    return backup_path

def save_items_to_excel(itens):
    ensure_workbook_exists()
    backup_path = create_backup()

    wb = load_workbook(EXCEL_ATUAL_PATH)
    ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active

    header_map = detect_headers(ws)
    existing = build_existing_index(ws, header_map)

    adicionados = 0
    atualizados = 0

    for item in itens:
        clean = clean_item(item)
        key = make_key(clean)

        if key in existing:
            row = existing[key]
            col_estoque = header_map["estoque"]

            atual = ws.cell(row=row, column=col_estoque).value or 0
            try:
                atual = int(atual)
            except Exception:
                atual = 0

            ws.cell(row=row, column=col_estoque).value = atual + int(clean["quantidade"])

            if clean["codigo_barras"]:
                cell = ws.cell(row=row, column=header_map["codigo_barras"])
                cell.value = str(clean["codigo_barras"])
                cell.number_format = "@"

            ws.cell(row=row, column=header_map["validade"]).value = clean["validade"]
            ws.cell(row=row, column=header_map["status"]).value = DEFAULTS["status"]

            atualizados += 1
        else:
            row = find_next_empty_row(ws, header_map)
            copy_style_from_previous_row(ws, row)
            write_item(ws, row, header_map, clean)
            existing[key] = row
            adicionados += 1

    wb.save(EXCEL_ATUAL_PATH)

    return {
        "adicionados": adicionados,
        "atualizados": atualizados,
        "backup": backup_path,
    }

def find_product_by_barcode(codigo):
    ensure_workbook_exists()

    wb = load_workbook(EXCEL_ATUAL_PATH, data_only=True)
    ws = wb[SHEET_NAME] if SHEET_NAME in wb.sheetnames else wb.active
    header_map = detect_headers(ws)

    codigo_limpo = normalize_barcode(codigo)
    encontrado = None

    for row in range(FIRST_DATA_ROW, ws.max_row + 1):
        codigo_cell = normalize_barcode(ws.cell(row=row, column=header_map["codigo_barras"]).value)

        if codigo_cell and codigo_cell == codigo_limpo:
            encontrado = {
                "codigo_barras": codigo_limpo,
                "produto": str(ws.cell(row=row, column=header_map["produto"]).value or ""),
                "quantidade": ws.cell(row=row, column=header_map["estoque"]).value,
                "lote": str(ws.cell(row=row, column=header_map["lote"]).value or ""),
                "validade": str(ws.cell(row=row, column=header_map["validade"]).value or ""),
            }

    return encontrado

def detect_headers(ws):
    mapping = {}

    for cell in ws[HEADER_ROW]:
        value = str(cell.value or "").upper().strip()
        for field, aliases in EXPECTED_HEADERS.items():
            if any(alias in value for alias in aliases):
                mapping[field] = cell.column

    required = ["produto", "codigo_barras", "lote", "validade", "estoque", "status"]
    missing = [field for field in required if field not in mapping]
    if missing:
        raise ValueError(f"Cabeçalhos não encontrados no Excel: {', '.join(missing)}")

    return mapping

def build_existing_index(ws, header_map):
    existing = {}

    for row in range(FIRST_DATA_ROW, ws.max_row + 1):
        item = {
            "produto": ws.cell(row=row, column=header_map["produto"]).value,
            "lote": ws.cell(row=row, column=header_map["lote"]).value,
        }

        key = make_key(item)

        if all(key):
            existing[key] = row

    return existing

def clean_item(item):
    return {
        "codigo_barras": normalize_barcode(item.get("codigo_barras", "")),
        "produto": normalize_product(item.get("produto", "")),
        "quantidade": int(item.get("quantidade", 0)),
        "lote": normalize_lote(item.get("lote", "")),
        "validade": normalize_date(item.get("validade", "")),
    }

def find_next_empty_row(ws, header_map):
    produto_col = header_map["produto"]

    for row in range(FIRST_DATA_ROW, ws.max_row + 2):
        produto = ws.cell(row=row, column=produto_col).value
        if produto in [None, ""]:
            return row

    return ws.max_row + 1

def copy_style_from_previous_row(ws, row):
    source_row = row - 1 if row > FIRST_DATA_ROW else FIRST_DATA_ROW

    for col in range(1, ws.max_column + 1):
        source = ws.cell(row=source_row, column=col)
        target = ws.cell(row=row, column=col)

        if source.has_style:
            target._style = copy(source._style)
            target.number_format = source.number_format
            target.font = copy(source.font)
            target.fill = copy(source.fill)
            target.border = copy(source.border)
            target.alignment = copy(source.alignment)

def set_if_exists(ws, row, header_map, field, value):
    if field in header_map:
        ws.cell(row=row, column=header_map[field]).value = value

def write_item(ws, row, header_map, item):
    set_if_exists(ws, row, header_map, "produto", item["produto"])
    set_if_exists(ws, row, header_map, "categoria", DEFAULTS["categoria"])
    set_if_exists(ws, row, header_map, "local", DEFAULTS["local"])

    if "codigo_barras" in header_map:
        cell = ws.cell(row=row, column=header_map["codigo_barras"])
        cell.value = str(item["codigo_barras"]) if item["codigo_barras"] else "-"
        cell.number_format = "@"

    set_if_exists(ws, row, header_map, "lote", item["lote"])
    set_if_exists(ws, row, header_map, "validade", item["validade"])
    set_if_exists(ws, row, header_map, "aberto_em", DEFAULTS["aberto_em"])
    set_if_exists(ws, row, header_map, "vence_apos_aberto", DEFAULTS["vence_apos_aberto"])
    set_if_exists(ws, row, header_map, "estoque", int(item["quantidade"]))
    set_if_exists(ws, row, header_map, "estoque_padrao", int(item["quantidade"]))
    set_if_exists(ws, row, header_map, "limite_alerta", DEFAULTS["limite_alerta"])
    set_if_exists(ws, row, header_map, "status", DEFAULTS["status"])
