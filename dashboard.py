import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Configuração inicial da página
st.set_page_config(page_title="Painel de DP - Conac", layout="wide")

# =========================================================
# 1. ESTILIZAÇÃO ADAPTATIVA E REMOÇÃO DE MENUS
# =========================================================
st.markdown("""
    <style>
    /* Esconde o menu do Streamlit (os três pontinhos), cabeçalho e rodapé */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilo Geral - Fonte e Cores Base */
    html, body, [class*="css"] { font-family: 'Visby CF', sans-serif; }
    
    /* Configuração para o Modo Escuro Automático */
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
        html, body, p, span, [class*="css"] { color: #E0E0E0 !important; }
        .stApp { background-color: #121212 !important; } 
    }

    /* Configuração para o Modo Claro Automático */
    @media (prefers-color-scheme: light) {
        h1, h2, h3, h4, h5, h6 { color: #103149 !important; font-weight: 800; }
        html, body, p, span, [class*="css"] { color: #444444 !important; }
        .stApp { background-color: #FFFFFF !important; }
    }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Operação DP")
st.write("Acompanhe a distribuição da carteira e os indicadores de fechamento da folha.")

# =========================================================
# 2. LEITURA DOS DADOS 
# =========================================================
arquivo_excel = "Controle_Folha_Com_Filtro.xlsx"
aba = "Agosto-2026" 

# Lê a planilha e limpa dados em branco
df = pd.read_excel(arquivo_excel, sheet_name=aba)
df = df.dropna(subset=['CÓD. COND.', 'CONDOMÍNIO']).copy()

# Tratamento das colunas
df['RESP'] = df['RESP'].astype(str).str.strip()
df['Possui Síndico Prof.'] = df['SÍNDICO PROFISSIONAL '].apply(
    lambda x: "Sim" if pd.notna(x) and str(x).strip() not in ['0', '0.0', 'nan'] else "Não"
)

# Garante que a coluna de Status exista
if 'Status do Fechamento' not in df.columns:
    df['Status do Fechamento'] = 'A Fazer'

# =========================================================
# 3. CARTÕES DE INDICADORES (NOVO VISUAL CLARO E CONTRASTADO)
# =========================================================
total_condominios = len(df)
total_funcionarios = df['FUNC'].sum()
total_sindicos_prof = len(df[df['Possui Síndico Prof.'] == 'Sim'])

st.write("---")
col1, col2, col3 = st.columns(3)

# Cartão com fundo claro, texto Azul Conac e números em Laranja Conac
def desenhar_cartao(titulo, valor):
    return f"""
    <div style="background-color: #F8F9FA; padding: 25px; border-radius: 12px; 
                box-shadow: 2px 4px 10px rgba(0,0,0,0.1); border-left: 8px solid #E55523;
                border: 1px solid #EAEAEA; margin-bottom: 20px;">
        <div style="color: #103149 !important; font-size: 1.2rem; font-weight: 700; margin-bottom: 5px;">{titulo}</div>
        <div style="color: #E55523 !important; font-size: 3.5rem; font-weight: 900 !important; line-height: 1;">{valor}</div>
    </div>
    """

col1.markdown(desenhar_cartao("Condomínios Ativos", total_condominios), unsafe_allow_html=True)
col2.markdown(desenhar_cartao("Funcionários na Base", f"{int(total_funcionarios):,}".replace(",", ".")), unsafe_allow_html=True)
col3.markdown(desenhar_cartao("Síndicos Profissionais", total_sindicos_prof), unsafe_allow_html=True)
st.write("---")

# =========================================================
# 4. GRÁFICOS GERENCIAIS COM PLOTLY
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

# Aplica filtro de código
if busca_codigo:
    df_exibicao['Código Limpo'] = df_exibicao['CÓD. COND.'].astype(str).str.replace('.0', '', regex=False)
    df_exibicao = df_exibicao[df_exibicao['Código Limpo'].str.contains(busca_codigo, na=False, case=False)]

# Aplica filtro de status
if status_selecionado:
    df_exibicao = df_exibicao[df_exibicao['Status do Fechamento'].isin(status_selecionado)]

# Função para pintar a célula dependendo do status
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

# Renderiza a tabela estilizada
tabela_estilizada = df_exibicao[colunas_exibicao].style.map(colorir_status, subset=['Status do Fechamento'])
st.dataframe(tabela_estilizada, use_container_width=True, hide_index=True)

# =========================================================
# 6. ATUALIZAÇÃO AUTOMÁTICA
# =========================================================
time.sleep(30)
st.rerun()
