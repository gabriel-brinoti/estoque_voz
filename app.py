import os
import re
from flask import Flask, render_template, request, send_file, flash, jsonify
from services.excel_service import ensure_workbook_exists, save_items_to_excel, EXCEL_ATUAL_PATH, find_product_by_barcode
from services.produto_matcher_service import suggest_product_name

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "backups"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "modelos"), exist_ok=True)

app = Flask(__name__)
app.secret_key = "troque-essa-chave-em-producao"

@app.route("/")
def index():
    ensure_workbook_exists()
    return render_template("index.html")

@app.route("/buscar_codigo", methods=["POST"])
def buscar_codigo():
    data = request.get_json(silent=True) or {}
    codigo = re.sub(r"\D", "", data.get("codigo", ""))
    if not codigo:
        return jsonify({"found": False, "error": "Código vazio"}), 400
    produto = find_product_by_barcode(codigo)
    if produto:
        return jsonify({"found": True, **produto, "codigo_barras": codigo})
    return jsonify({"found": False, "codigo_barras": codigo})

@app.route("/sugerir_produto", methods=["POST"])
def sugerir_produto():
    data = request.get_json(silent=True) or {}
    produto_falado = data.get("produto", "").strip()
    return jsonify(suggest_product_name(produto_falado))

@app.route("/salvar", methods=["POST"])
def salvar():
    item = {
        "produto": request.form.get("produto", "").strip(),
        "categoria": request.form.get("categoria", "").strip(),
        "local": request.form.get("local", "").strip(),
        "codigo_barras": request.form.get("codigo_barras", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "validade": request.form.get("validade", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
        "estoque_padrao": request.form.get("estoque_padrao", "").strip(),
        "limite_alerta": request.form.get("limite_alerta", "").strip(),
    }
    erro = validar_item(item)
    if erro:
        flash(erro)
        return render_template("index.html", item=item)
    resultado = save_items_to_excel([item])
    return render_template("sucesso.html", resultado=resultado, item=item)

@app.route("/download")
def download():
    ensure_workbook_exists()
    return send_file(EXCEL_ATUAL_PATH, as_attachment=True, download_name="produtos_atualizado.xlsx")

def validar_item(item):
    obrigatorios = ["produto", "categoria", "local", "quantidade", "lote", "validade", "estoque_padrao", "limite_alerta"]
    for campo in obrigatorios:
        if not item.get(campo):
            return f"O campo {campo} é obrigatório."
    if item.get("codigo_barras") and not item["codigo_barras"].replace(" ", "").isdigit():
        return "O código de barras precisa conter apenas números."
    for campo in ["quantidade", "estoque_padrao", "limite_alerta"]:
        if not item[campo].isdigit():
            return f"O campo {campo} precisa ser número inteiro."
        if int(item[campo]) < 0:
            return f"O campo {campo} não pode ser negativo."
    if int(item["quantidade"]) <= 0:
        return "O estoque precisa ser maior que zero."
    if not re.match(r"^\d{2}/\d{2}/\d{4}$", item["validade"]):
        return "O vencimento precisa estar no formato DD/MM/AAAA."
    return None

if __name__ == "__main__":
    ensure_workbook_exists()
    app.run(host="0.0.0.0", port=5000, debug=True)
