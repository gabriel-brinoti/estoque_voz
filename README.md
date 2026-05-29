# Estoque por Conversa Contínua + Código Opcional + Excel

Fluxo:
- Clique em Iniciar conversa
- O sistema fala a pergunta
- O microfone liga sozinho
- Você responde
- Ele avança automaticamente
- Na revisão, responda "sim" para salvar ou "não" para corrigir

Segue o Excel atualizado:
- Aba: Relatório
- Cabeçalho: linha 4
- Estoque = quantidade
- Vencimento = validade
- Soma por Produto + Lote

## Rodar

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Acesse:
```txt
http://127.0.0.1:5000
```
