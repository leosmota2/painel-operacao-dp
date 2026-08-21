import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Painel de DP - Conac", layout="wide")

# =========================================================
# 1. ESTILIZAÇÃO (SUPORTE INTELIGENTE CLARO/ESCURO)
# =========================================================
st.markdown("""
    <style>
    html, body, [class*="css"]  { font-family: 'Visby CF', sans-serif; color: #444444; }
    h1, h2, h3, h4, h5, h6 { color: #103149 !important; font-weight: 800; }
    
    div[data-testid="metric-container"] {
        background-color: #103149;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        border-left: 8px solid #E55523;
    }
    
    div[data-testid="metric-container"] label { color: #FFFFFF !important; font-weight: 600; opacity: 0.9; }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #E55523 !important; font-weight: 900; font-size: 2.5rem; }

    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
        html, body, [class*="css"] { color: #E0E0E0; }
        div[data-testid="metric-container"] { border: 1px solid #333333; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Painel de Controle - Operação DP")
st.write("Acompanhe a distribuição da carteira e os indicadores de fechamento da folha em tempo real.")

# =========================================================
# 2. LEITURA DOS DADOS 
# =========================================================
arquivo_excel = "Controle_Folha_Com_Filtro.xlsx"
aba = "Agosto-2026" 

df = pd.read_excel(arquivo_excel, sheet_name=aba)
df = df.dropna(subset=['CÓD. COND.', 'CONDOMÍNIO']).copy()
df['RESP'] = df['RESP'].astype(str).str.strip()
df['Possui Síndico Prof.'] = df['SÍNDICO PROFISSIONAL '].apply(
    lambda x: "Sim" if pd.notna(x) and str(x).strip() not in ['0', '0.0', 'nan'] else "Não"
)

if 'Status do Fechamento' not in df.columns:
    df['Status do Fechamento'] = 'A Fazer'

# =========================================================
# 3. INDICADORES (KPIs)
# =========================================================
total_condominios = len(df)
total_funcionarios = df['FUNC'].sum()
total_sindicos_prof = len(df[df['Possui Síndico Prof.'] == 'Sim'])

st.write("---")
col1, col2, col3 = st.columns(3)
col1.metric(label="Total de Condomínios Ativos", value=f"{total_condominios}")
col2.metric(label="Total de Funcionários na Base", value=f"{int(total_funcionarios):,}".replace(",", "."))
col3.metric(label="Síndicos Profissionais Atendidos", value=f"{total_sindicos_prof}")
st.write("---")

# =========================================================
# 4. GRÁFICOS GERENCIAIS (ATUALIZADO)
# =========================================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("👥 Volume de Condomínios")
    # Conta quantos condomínios cada analista tem
    carteira_analista = df['RESP'].value_counts().reset_index()
    carteira_analista.columns = ['Analista', 'Qtd Condomínios']
    st.bar_chart(carteira_analista.set_index('Analista'), color="#103149")

with col_graf2:
    st.subheader("🧑‍💼 Volume de Funcionários")
    # Soma a quantidade de funcionários para cada analista
    funcs_analista = df.groupby('RESP')['FUNC'].sum().reset_index()
    funcs_analista.columns = ['Analista', 'Qtd Funcionários']
    st.bar_chart(funcs_analista.set_index('Analista'), color="#E55523")

st.write("---")

# =========================================================
# 5. TABELA COM FILTROS E CORES CONDICIONAIS
# =========================================================
st.subheader("📑 Gestão do Fechamento de Folha")

col_filtro1, col_filtro2 = st.columns(2)
with col_filtro1:
    busca_codigo = st.text_input("🔍 Buscar por Código do Condomínio:")
with col_filtro2:
    lista_status = df['Status do Fechamento'].unique().tolist()
    status_selecionado = st.multiselect("📊 Filtrar por Status da Folha:", options=lista_status, default=lista_status)

df_exibicao = df.copy()

if busca_codigo:
    df_exibicao['Código Limpo'] = df_exibicao['CÓD. COND.'].astype(str).str.replace('.0', '', regex=False)
    df_exibicao = df_exibicao[df_exibicao['Código Limpo'].str.contains(busca_codigo, na=False, case=False)]

if status_selecionado:
    df_exibicao = df_exibicao[df_exibicao['Status do Fechamento'].isin(status_selecionado)]

def colorir_status(val):
    cor = ''
    if val == 'A Fazer':
        cor = 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;' 
    elif val == 'Concluído':
        cor = 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;' 
    elif val == 'Em Andamento':
        cor = 'background-color: #FFF3E0; color: #E65100; font-weight: bold;' 
    return cor

colunas_exibicao = ['CÓD. COND.', 'CONDOMÍNIO', 'FUNC', 'RESP', 'Status do Fechamento', 'Auditoria FGTS', 'eSocial/DCTFWeb']

tabela_estilizada = df_exibicao[colunas_exibicao].style.map(colorir_status, subset=['Status do Fechamento'])

st.dataframe(tabela_estilizada, use_container_width=True, hide_index=True)

# =========================================================
# 6. ATUALIZAÇÃO AUTOMÁTICA
# =========================================================
time.sleep(30)
st.rerun()
