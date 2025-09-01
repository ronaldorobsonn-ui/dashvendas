
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from urllib.parse import urlparse

st.set_page_config(page_title="Dashboard de Vendas", page_icon="📊", layout="wide")

st.title("📊 Dashboard de Vendas — Relatório Mensal")
st.caption("Conectado ao Google Sheets (CSV publicado). Atualiza automaticamente.")

# --------------------
# Config Sidebar
# --------------------
with st.sidebar:
    st.header("⚙️ Fonte dos Dados")
    default_csv = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ5DYgRFilhke_zVVKMum5mElJg3KnktxaWWyxUg7c6zopr0ww5TmzRXVrNAZlqlGT-cTv0X753frr9/pub?gid=1020661570&single=true&output=csv"
    gsheets_url = st.text_input(
        "URL CSV publicado do Google Sheets",
        value=default_csv,
        help="Exemplo: https://docs.google.com/spreadsheets/d/e/.../pub?output=csv"
    )
    st.caption("Se precisar, troque o link acima por outra guia publicada em CSV.")

    st.subheader("🔁 Atualização")
    auto_refresh = st.toggle("Auto-refresh", value=True, help="Recarrega os dados periodicamente.")
    refresh_secs = st.number_input("Intervalo (segundos)", min_value=15, max_value=1800, value=120, step=15)
    if st.button("🔄 Atualizar agora"):
        st.cache_data.clear()
        st.experimental_rerun()

# Auto refresh
if auto_refresh:
    st.experimental_set_query_params(_=np.random.randint(0, 1_000_000))
    st.autorefresh = st.experimental_rerun

# --------------------
# Carregamento de dados
# --------------------
@st.cache_data(ttl=300, show_spinner=False)
def load_csv(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={
        "Data da transação": "data",
        "Produto": "produto",
        "Faturamento líquido Afiliado": "fat_afiliado",
        "Faturamento líquido Produtor": "fat_produtor",
        "Nome do Afiliado": "afiliado",
    })
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    for col in ["fat_afiliado", "fat_produtor"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["produto", "afiliado"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

df = None
source_label = "Google Sheets (CSV publicado)"
try:
    parsed = urlparse(gsheets_url)
    if not parsed.scheme.startswith("http"):
        st.error("URL inválida. Forneça um link iniciando com http(s).")
        st.stop()
    df = load_csv(gsheets_url)
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

if df is None or df.empty:
    st.warning("Nenhum dado carregado. Verifique a URL do Google Sheets publicado em CSV.")
    st.stop()

df = normalize_columns(df).dropna(subset=["data"])
if df.empty:
    st.warning("Os dados foram carregados, mas não há linhas válidas (datas podem estar inválidas).")
    st.stop()

st.success(f"Dados carregados de: **{source_label}** — {len(df)} linhas")

# --------------------
# Filtros
# --------------------
min_date = df["data"].min()
max_date = df["data"].max()
st.sidebar.header("🧰 Filtros")
r = st.sidebar.date_input("Período", value=(min_date.date(), max_date.date()), min_value=min_date.date(), max_value=max_date.date())
if isinstance(r, tuple) and len(r) == 2:
    start_date, end_date = pd.to_datetime(r[0]), pd.to_datetime(r[1])
else:
    start_date, end_date = min_date, max_date

produtos = sorted(df["produto"].dropna().unique().tolist()) if "produto" in df.columns else []
afiliados = sorted(df["afiliado"].dropna().unique().tolist()) if "afiliado" in df.columns else []

sel_produtos = st.sidebar.multiselect("Produto(s)", produtos, default=produtos[:10] if len(produtos) > 10 else produtos)
sel_afiliados = st.sidebar.multiselect("Afiliado(s)", afiliados, default=afiliados)

# Aplica filtros
m = (df["data"].between(start_date, end_date))
if sel_produtos:
    m &= df["produto"].isin(sel_produtos)
if sel_afiliados:
    m &= df["afiliado"].isin(sel_afiliados)

dff = df.loc[m].copy()

# --------------------
# KPIs
# --------------------
fat_produtor_total = dff["fat_produtor"].sum() if "fat_produtor" in dff.columns else 0.0
fat_afiliado_total = dff["fat_afiliado"].sum() if "fat_afiliado" in dff.columns else 0.0
pedidos = len(dff)

col1, col2, col3 = st.columns(3)
col1.metric("💰 Faturamento Produtor (R$)", f"{fat_produtor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("🤝 Faturamento Afiliado (R$)", f"{fat_afiliado_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("🧾 Nº de Transações", f"{pedidos:,}".replace(",", "."))

# --------------------
# Gráficos
# --------------------
dff["dia"] = dff["data"].dt.date
by_day = dff.groupby("dia", as_index=False)[["fat_produtor", "fat_afiliado"]].sum()

fig_ts = px.line(
    by_day,
    x="dia",
    y=["fat_produtor", "fat_afiliado"],
    markers=True,
    title="Evolução diária do faturamento",
    labels={"value": "Faturamento (R$)", "variable": "Tipo"},
)
st.plotly_chart(fig_ts, use_container_width=True)

if "produto" in dff.columns:
    by_prod = dff.groupby("produto", as_index=False)[["fat_produtor", "fat_afiliado"]].sum().sort_values("fat_produtor", ascending=False)
    fig_prod = px.bar(
        by_prod,
        x="produto",
        y=["fat_produtor", "fat_afiliado"],
        barmode="group",
        title="Faturamento por produto",
        labels={"value": "Faturamento (R$)", "variable": "Tipo", "produto": "Produto"},
    )
    fig_prod.update_layout(xaxis_tickangle=-20)
    st.plotly_chart(fig_prod, use_container_width=True)

st.subheader("📋 Transações (filtradas)")
show_cols = ["data", "produto", "afiliado", "fat_produtor", "fat_afiliado"]
show_cols = [c for c in show_cols if c in dff.columns]
st.dataframe(dff[show_cols].sort_values("data", ascending=False), use_container_width=True)

st.caption("Dica: Edite a URL do CSV na barra lateral para apontar para outra guia publicada; clique em **Atualizar agora** para forçar a atualização.")
