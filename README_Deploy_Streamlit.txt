
# Deploy no Streamlit Community Cloud

## Passo a passo
1. Crie um repositório no GitHub (pode chamar `dashboard-vendas-streamlit`).
2. Envie os **3 arquivos** deste pacote: `app.py`, `requirements.txt` e `README.txt` (opcional).
3. Acesse https://streamlit.io/cloud → **New app** → conecte seu GitHub → selecione o repo e o `app.py`.
4. Python version: 3.10+ (padrão). Não precisa de secrets.
5. Clique em **Deploy**.

## Sincronização com Google Sheets (CSV publicado)
- Já deixei a URL de CSV padrão configurada no app (sidebar). Se quiser mudar, cole outra URL `.../pub?output=csv` no campo da barra lateral.
- O app usa cache de 5 minutos para estabilidade. Para ver mudanças imediatas, clique em **🔄 Atualizar agora**.
- Opcional: ative *Auto-refresh* na barra lateral e defina o intervalo em segundos.

## Observações
- Se o deploy falhar por limitação de memória, desative *Auto-refresh* ou aumente o intervalo.
- Verifique se a planilha está publicada: **Arquivo → Publicar na Web → CSV** da guia correta.
