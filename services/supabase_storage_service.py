import os
import datetime
import requests

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
BUCKET = os.environ.get("SUPABASE_BACKUP_BUCKET", "backups")
MAIN_FILE_NAME = "produtos_atualizado.xlsx"


def is_configured():
    return bool(SUPABASE_URL and SERVICE_ROLE_KEY and BUCKET)


def headers(content_type=None):
    h = {
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "apikey": SERVICE_ROLE_KEY,
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def download_latest_excel(destination_path):
    if not is_configured():
        return False, "Supabase não configurado."

    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{MAIN_FILE_NAME}"

    try:
        r = requests.get(url, headers=headers(), timeout=30)

        if r.status_code == 404:
            return False, "Nenhum Excel salvo no Supabase ainda."

        if not r.ok:
            return False, f"Erro ao baixar Excel: {r.status_code} - {r.text}"

        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        with open(destination_path, "wb") as f:
            f.write(r.content)

        return True, "Excel baixado do Supabase."

    except Exception as e:
        return False, f"Erro ao baixar Excel do Supabase: {e}"


def upload_excel(file_path):
    if not is_configured():
        return False, "Supabase não configurado."

    if not os.path.exists(file_path):
        return False, "Excel local não encontrado."

    ok, msg = upload_file(file_path, MAIN_FILE_NAME, upsert=True)

    if not ok:
        return False, msg

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"historico/produtos_backup_{timestamp}.xlsx"
    ok_backup, msg_backup = upload_file(file_path, backup_path, upsert=False)

    if not ok_backup:
        return True, f"Excel principal enviado. Histórico não enviado: {msg_backup}"

    return True, "Excel enviado ao Supabase com backup histórico."


def upload_file(file_path, storage_path, upsert=True):
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{storage_path}"

    h = headers("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if upsert:
        h["x-upsert"] = "true"

    try:
        with open(file_path, "rb") as f:
            r = requests.post(url, headers=h, data=f, timeout=60)

        if r.status_code in [200, 201]:
            return True, f"Upload concluído: {storage_path}"

        return False, f"Erro upload Supabase: {r.status_code} - {r.text}"

    except Exception as e:
        return False, f"Erro ao enviar Excel para Supabase: {e}"
