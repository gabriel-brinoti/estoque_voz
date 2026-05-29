# Estoque V4 — Supabase Storage

Agora o sistema:
- Baixa o Excel mais recente do Supabase ao iniciar.
- Atualiza o Excel local.
- Envia automaticamente o Excel atualizado para o bucket `backups`.
- Cria também uma cópia histórica em `historico/`.

Variáveis no Render:

SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_BACKUP_BUCKET=backups

Arquivo principal salvo no Supabase:
produtos_atualizado.xlsx
