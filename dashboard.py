import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os

st.set_page_config(page_title="Painel de DP - Conac", layout="wide")

# =========================================================
# 1. CABEÇALHO, LOGO E ESTILIZAÇÃO VISUAL (TEMA FIXO)
# =========================================================
if os.path.exists("logo.png"):
    st.image("logo.png", width=220)

st.markdown("""
    <style>
    /* Força o fundo da página a ser branco para destacar as cores da marca */
    .stApp { background-color: #FFFFFF !important; }
    
    /* Fonte oficial e textos comuns no Cinza da Conac */
    html, body, p, span, [class*="css"] { 
        font-family: 'Visby CF', sans-serif; 
        color: #444444 !important; 
    }
    
    /* Títulos sempre no Azul Conac */
    h1, h2, h3, h4, h5, h6 { 
        color: #103149 !important; 
        font-weight: 800; 
    }
    
    /* Exceção: Protege os textos de dentro dos nossos cartões para não ficarem cinzas */
    div[style*="background-color: #103149"] p { color: #FFFFFF !important; }
    div[style*="background-color: #103149"] h1 { color: #E55523 !important; }
    </style>
""", unsafe_allow_html=True)

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
# 3. CARTÕES DE INDICADORES (COM RELEVO E SOMBRA 3D)
# =========================================================
total_condominios = len(df)
total_funcionarios = df['FUNC'].sum()
total_sindicos_prof = len(df[df['Possui Síndico Prof.'] == 'Sim'])

st.write("---")
col1, col2, col3 = st.columns(3)

# Função para desenhar os cartões bonitos à prova de falhas do Streamlit
def desenhar_cartao(titulo, valor):
    return f"""
    <div style="background-color: #103149; padding: 25px; border-radius: 12px; 
                box-shadow: 4px 6px 15px rgba(0,0,0,0.25); border-left: 8px solid #E55523;
                margin-bottom: 20px;">
        <p style="color: #FFFFFF; margin: 0; font-size: 1.1rem; opacity: 0.9;">{titulo}</p>
        <h1 style="color: #E55523 !important; margin: 0; font-size: 3rem; font-weight: 900;">{valor}</h1>
    </div>
    """

col1.markdown(desenhar_cartao("Condomínios Ativos", total_condominios), unsafe_allow_html=True)
col2.markdown(desenhar_cartao("Funcionários na Base", f"{int(total_funcionarios):,}".replace(",", ".")), unsafe_allow_html=True)
col3.markdown(desenhar_cartao("Síndicos Profissionais", total_sindicos_prof), unsafe_allow_html=True)
st.write("---")

# =========================================================
# 4. GRÁFICOS GERENCIAIS COM PLOTLY (VÍVIDOS E COM RELEVO)
# =========================================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("👥 Volume de Condomínios")
    carteira_analista = df['RESP'].value_counts().reset_index()
    carteira_analista.columns = ['Analista', 'Qtd']
    
    # Gráfico Plotly Azul
    fig1 = px.bar(carteira_analista, x='Analista', y='Qtd', text_auto=True)
    fig1.update_traces(marker_color='#103149', marker_line_color='#091a26', marker_line_width=2, opacity=0.95)
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                       font_family="Visby CF", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig1, use_container_width=True)

with col_graf2:
    st.subheader("🧑‍💼 Volume de Funcionários")
    funcs_analista = df.groupby('RESP')['FUNC'].sum().reset_index()
    funcs_analista.columns = ['Analista', 'Qtd']
    
    # Gráfico Plotly Laranja
    fig2 = px.bar(funcs_analista, x='Analista', y='Qtd', text_auto=True)
    fig2.update_traces(marker_color='#E55523', marker_line_color='#b33e14', marker_line_width=2, opacity=0.95)
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                       font_family="Visby CF", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig2, use_container_width=True)

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
