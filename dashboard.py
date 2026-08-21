import streamlit as st
import pandas as pd
import plotly.express as px
import time

# Configuração inicial da página
st.set_page_config(page_title="Painel de DP - Conac", layout="wide")

# =========================================================
# 1. ESTILIZAÇÃO ADAPTATIVA E BLINDAGEM DOS CARTÕES
# =========================================================
st.markdown("""
    <style>
    /* Escondendo apenas o rodapé (marca d'água do Streamlit). O menu superior CONTINUA ATIVO! */
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
    
    /* BLINDAGEM TOTAL DOS CARTÕES */
    div.kpi-card {
        background-color: #103149 !important;
        padding: 25px !important;
        border-radius: 12px !important;
        box-shadow: 4px 6px 15px rgba(0,0,0,0.25) !important;
        border-left: 8px solid #E55523 !important;
        margin-bottom: 20px !important;
    }
    div.kpi-card .kpi-title { color: #FFFFFF !important; font-size: 1.1rem !important; opacity: 0.9 !important; margin-bottom: 5px !important; }
    div.kpi-card .kpi-value { color: #E55523 !important; font-size: 3rem !important; font-weight: 900 !important; line-height: 1 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Operação DP")
st.write("Acompanhe a distribuição da carteira e os indicadores de fechamento da folha.")

# =========================================================
# 2. LEITURA DOS DADOS (CONECTADO AO GOOGLE SHEETS)
# =========================================================
# Link direto da sua planilha no Google
link_google = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTMUmPETtYMKsb0IpZSIlXoYHcdSRiE7TxofU-CIoQjYn-aBGAB03frKpEs5e4cy6JrjpvFOF8jssNL/pub?output=csv" 

df = pd.read_csv(link_google)
df = df.dropna(subset=['CÓD. COND.', 'CONDOMÍNIO']).copy()
df['RESP'] = df['RESP'].astype(str).str.strip()
df['FUNC'] = pd.to_numeric(df['FUNC'], errors='coerce').fillna(0).astype(int)
df['CÓD. COND.'] = df['CÓD. COND.'].astype(str).str.replace('.0', '', regex=False)
df['Possui Síndico Prof.'] = df['SÍNDICO PROFISSIONAL '].apply(lambda x: "Sim" if pd.notna(x) and str(x).strip() not in ['0', '0.0', 'nan'] else "Não")

if 'Status do Fechamento' not in df.columns: df['Status do Fechamento'] = 'A Fazer'

# =========================================================
# 3. CARTÕES DE INDICADORES
# =========================================================
total_condominios = len(df)
total_funcionarios = df['FUNC'].sum()
total_sindicos_prof = len(df[df['Possui Síndico Prof.'] == 'Sim'])

st.write("---")
col1, col2, col3 = st.columns(3)

def desenhar_cartao(titulo, valor):
    return f"""<div class="kpi-card"><div class="kpi-title">{titulo}</div><div class="kpi-value">{valor}</div></div>"""

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
    fig1 = px.bar(carteira_analista, x='Analista', y='Qtd', text_auto=True)
    fig1.update_traces(marker_color='#103149', marker_line_color='#091a26', marker_line_width=2, opacity=0.95)
    fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family="Visby CF", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig1, use_container_width=True)

with col_graf2:
    st.subheader("🧑‍💼 Volume de Funcionários")
    funcs_analista = df.groupby('RESP')['FUNC'].sum().reset_index()
    funcs_analista.columns = ['Analista', 'Qtd']
    fig2 = px.bar(funcs_analista, x='Analista', y='Qtd', text_auto=True)
    fig2.update_traces(marker_color='#E55523', marker_line_color='#b33e14', marker_line_width=2, opacity=0.95)
    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family="Visby CF", margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig2, use_container_width=True)

st.write("---")

# =========================================================
# 5. TABELA DE GESTÃO DO FECHAMENTO
# =========================================================
st.subheader("📑 Gestão do Fechamento de Folha")
col_filtro1, col_filtro2 = st.columns(2)
with col_filtro1: busca_codigo = st.text_input("🔍 Buscar por Código do Condomínio:")
with col_filtro2: 
    lista_status = df['Status do Fechamento'].unique().tolist()
    status_selecionado = st.multiselect("📊 Filtrar por Status da Folha:", options=lista_status, default=lista_status)

df_exibicao = df.copy()
if busca_codigo: df_exibicao = df_exibicao[df_exibicao['CÓD. COND.'].str.contains(busca_codigo, na=False, case=False)]
if status_selecionado: df_exibicao = df_exibicao[df_exibicao['Status do Fechamento'].isin(status_selecionado)]

def colorir_status(val):
    if val == 'A Fazer': return 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;' 
    elif val == 'Concluído': return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;' 
    elif val == 'Em Andamento': return 'background-color: #FFF3E0; color: #E65100; font-weight: bold;' 
    return ''

colunas_exibicao = ['CÓD. COND.', 'CONDOMÍNIO', 'FUNC', 'RESP', 'Status do Fechamento', 'Auditoria FGTS', 'eSocial/DCTFWeb']
st.dataframe(df_exibicao[colunas_exibicao].style.map(colorir_status, subset=['Status do Fechamento']), use_container_width=True, hide_index=True)
st.write("---")

# =========================================================
# 6. SESSÃO DE AUDITORIA AUTOMÁTICA DE FGTS
# =========================================================
st.subheader("🤖 Auditoria de FGTS (Sistema x Robô de Guias)")
st.write("Arraste os arquivos do seu sistema e do robô abaixo para encontrar as divergências em segundos.")

col_upload1, col_upload2 = st.columns(2)
with col_upload1:
    arquivo_sistema = st.file_uploader("📂 Base do Sistema (FolhaPagtoAnalitica.xls)", type=["xls", "xlsx"])
with col_upload2:
    arquivo_robo = st.file_uploader("🤖 Base do Robô (Relatorio.xlsx)", type=["xls", "xlsx"])

# Lógica da Auditoria blindada contra erros de texto
if arquivo_sistema and arquivo_robo:
    if st.button("🔍 Cruzar Dados Agora", type="primary"):
        with st.spinner("Lendo planilhas e calculando divergências..."):
            try:
                CODIGOS_CONSIGNADOS = [716, 717, 718, 719, 720]

                # 1. Relatório do Robô
                df_robo = pd.read_excel(arquivo_robo)
                df_robo = df_robo.rename(columns={"Código": "Cod_Empresa", "Valor Guia": "Valor_Robo", "Cond": "Nome_Condominio"})
                df_robo["Cod_Empresa"] = pd.to_numeric(df_robo["Cod_Empresa"], errors="coerce")

                # 2. Folha do Sistema (FGTS + Consignados)
                df_bases = pd.read_excel(arquivo_sistema, sheet_name="TotalEmpresaBaseCalculo")
                df_fgts = df_bases[df_bases["codigo_movto"] == 901].copy()
                
                # Conversão forçada para garantir que o Excel não mande texto no FGTS
                df_fgts["valor"] = df_fgts["valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                df_fgts["valor"] = pd.to_numeric(df_fgts["valor"], errors="coerce").fillna(0)
                
                df_fgts = df_fgts[["empresa", "valor"]].rename(columns={"empresa": "Cod_Empresa", "valor": "Valor_FGTS"})
                df_fgts["Cod_Empresa"] = pd.to_numeric(df_fgts["Cod_Empresa"], errors="coerce")

                df_salarios = pd.read_excel(arquivo_sistema, sheet_name="TotalEmpresaSal")
                df_consig = df_salarios[df_salarios["codigo_movto"].isin(CODIGOS_CONSIGNADOS)].copy()
                
                if not df_consig.empty:
                    # Conversão forçada para garantir que o Excel não mande texto no Consignado
                    df_consig["valor"] = df_consig["valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                    df_consig["valor"] = pd.to_numeric(df_consig["valor"], errors="coerce").fillna(0)
                    
                    df_consig = df_consig.groupby("empresa")["valor"].sum().reset_index()
                    df_consig = df_consig.rename(columns={"empresa": "Cod_Empresa", "valor": "Valor_Consignado"})
                    df_consig["Cod_Empresa"] = pd.to_numeric(df_consig["Cod_Empresa"], errors="coerce")
                else:
                    df_consig = pd.DataFrame(columns=["Cod_Empresa", "Valor_Consignado"])

                df_folha_consolidada = pd.merge(df_fgts, df_consig, on="Cod_Empresa", how="outer").fillna(0)
                df_folha_consolidada["Valor_Folha_Total"] = df_folha_consolidada["Valor_FGTS"] + df_folha_consolidada["Valor_Consignado"]

                # 3. Cruzamento
                comparativo = pd.merge(df_folha_consolidada, df_robo, on="Cod_Empresa", how="left", indicator=True)
                comparativo["Valor_Folha_Total"] = comparativo["Valor_Folha_Total"].fillna(0)
                comparativo["Valor_Robo"] = comparativo["Valor_Robo"].fillna(0)
                comparativo["Diferenca"] = comparativo["Valor_Folha_Total"] - comparativo["Valor_Robo"]

                # 4. Status
                def definir_status(linha):
                    if linha["_merge"] == "left_only": return "⚠️ ALERTA: Guia não baixada"
                    elif abs(linha["Diferenca"]) > 0.50: return "❌ ERRO: Valores não batem"
                    else: return "✅ OK"

                comparativo["Status da Conferência"] = comparativo.apply(definir_status, axis=1)
                comparativo["Nome_Condominio"] = comparativo["Nome_Condominio"].fillna("Nome não encontrado no robô")

                # Organização e Cores
                colunas_finais = ["Cod_Empresa", "Nome_Condominio", "Valor_Folha_Total", "Valor_Robo", "Diferenca", "Status da Conferência"]
                comparativo = comparativo[colunas_finais]

                def cor_auditoria(val):
                    if '✅' in str(val): return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
                    if '❌' in str(val): return 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;'
                    if '⚠️' in str(val): return 'background-color: #FFF3E0; color: #E65100; font-weight: bold;'
                    return ''

                st.success("✅ Auditoria finalizada! Veja os resultados abaixo:")
                st.dataframe(comparativo.style.map(cor_auditoria, subset=['Status da Conferência']), use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ Ocorreu um erro ao processar. Verifique se os arquivos são os corretos. Detalhe técnico: {e}")

# =========================================================
# 7. ATUALIZAÇÃO AUTOMÁTICA (COM PAUSA INTELIGENTE)
# =========================================================
# Só atualiza a página sozinho se o usuário NÃO estiver fazendo uma auditoria
if not (arquivo_sistema or arquivo_robo):
    time.sleep(30)
    st.rerun()

# =========================================================
# 7. ATUALIZAÇÃO AUTOMÁTICA (COM PAUSA INTELIGENTE)
# =========================================================
# Só atualiza a página sozinho se o usuário NÃO estiver fazendo uma auditoria
if not (arquivo_sistema or arquivo_robo):
    time.sleep(30)
    st.rerun()
