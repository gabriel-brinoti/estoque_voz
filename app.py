import os
import re
from flask import Flask, render_template, request, send_file, flash, jsonify
from services.excel_service import (
    ensure_workbook_exists,
    save_items_to_excel,
    EXCEL_ATUAL_PATH,
    find_product_by_barcode,
)

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
        return jsonify({
            "found": True,
            "produto": produto.get("produto", ""),
            "codigo_barras": codigo,
            "validade": produto.get("validade", ""),
            "lote": produto.get("lote", ""),
        })

    return jsonify({"found": False, "codigo_barras": codigo})


@app.route("/salvar", methods=["POST"])
def salvar():
    item = {
        "produto": request.form.get("produto", "").strip(),
        "codigo_barras": request.form.get("codigo_barras", "").strip(),
        "quantidade": request.form.get("quantidade", "").strip(),
        "lote": request.form.get("lote", "").strip(),
        "validade": request.form.get("validade", "").strip(),
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
    for campo in ["produto", "quantidade", "lote", "validade"]:
        if not item.get(campo):
            return f"O campo {campo} é obrigatório."

    if item.get("codigo_barras") and not item["codigo_barras"].replace(" ", "").isdigit():
        return "O código de barras precisa conter apenas números."

    if not item["quantidade"].isdigit():
        return "A quantidade precisa ser número inteiro."

    if int(item["quantidade"]) <= 0:
        return "A quantidade precisa ser maior que zero."

    if not re.match(r"^\d{2}/\d{2}/\d{4}$", item["validade"]):
        return "O vencimento precisa estar no formato DD/MM/AAAA."

    return None


if __name__ == "__main__":
    ensure_workbook_exists()
    app.run(host="0.0.0.0", port=5000, debug=True)
