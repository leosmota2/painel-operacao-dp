import streamlit as st
import pandas as pd
import plotly.express as px
import io 
import time
import json
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh 

st.set_page_config(page_title="Portal Conac RH", page_icon="🏢", layout="wide")

# =========================================================
# 1. ESTILIZAÇÃO CSS
# =========================================================
st.markdown("""
    <style>
    footer {visibility: hidden;}
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stAppViewContainer"] { opacity: 1 !important; transition: none !important; }
    html, body, [class*="css"] { font-family: 'Visby CF', sans-serif; }
    
    @media (prefers-color-scheme: dark) {
        h1, h2, h3, h4, h5, h6 { color: #FFFFFF !important; }
        html, body, p, span, [class*="css"] { color: #E0E0E0 !important; }
        .stApp { background-color: #121212 !important; } 
    }
    @media (prefers-color-scheme: light) {
        h1, h2, h3, h4, h5, h6 { color: #103149 !important; font-weight: 800; }
        html, body, p, span, [class*="css"] { color: #444444 !important; }
        .stApp { background-color: #FFFFFF !important; }
    }
    
    div.kpi-card { background-color: #103149 !important; padding: 25px !important; border-radius: 12px !important; box-shadow: 4px 6px 15px rgba(0,0,0,0.25) !important; border-left: 8px solid #E55523 !important; margin-bottom: 20px !important; }
    div.kpi-card .kpi-title { color: #FFFFFF !important; font-size: 1.1rem !important; opacity: 0.9 !important; margin-bottom: 5px !important; }
    div.kpi-card .kpi-value { color: #E55523 !important; font-size: 3rem !important; font-weight: 900 !important; line-height: 1 !important; }
    @media (max-width: 768px) {
        div.kpi-card { padding: 15px !important; margin-bottom: 15px !important; }
        div.kpi-card .kpi-title { font-size: 0.9rem !important; }
        div.kpi-card .kpi-value { font-size: 2rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 2. CONEXÃO COM O BANCO DE DADOS (GOOGLE SHEETS)
# =========================================================
@st.cache_resource
def conectar_google():
    credenciais_dict = json.loads(st.secrets["google_json"])
    escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(credenciais_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client

try:
    bd_ferias = conectar_google().open("Base_Ferias_Conac")
    aba_pedidos = bd_ferias.worksheet("Pedidos")
    aba_gestores = bd_ferias.worksheet("Acessos_Gestores")
except Exception as e:
    st.error("❌ Ops! Não consegui conectar na planilha. Verifique se o e-mail do robô tem permissão de Editor.")
    st.stop()

# =========================================================
# 3. MENU LATERAL DE NAVEGAÇÃO
# =========================================================
st.sidebar.title("🏢 Conac RH")
menu_principal = st.sidebar.radio("Navegação:", ["🌴 Portal de Férias", "🔒 Painel DP (Férias)", "🔒 Painel DP (Fechamento)"])

# =========================================================
# MÓDULO A: PORTAL DE FÉRIAS (PÚBLICO)
# =========================================================
if menu_principal == "🌴 Portal de Férias":
    st.title("🌴 Portal de Férias")
    perfil_ferias = st.radio("Selecione seu perfil de acesso:", ["Colaborador", "Gestor (Aprovação)"], horizontal=True)
    st.write("---")

    # -----------------------------------------------------
    # VISÃO COLABORADOR
    # -----------------------------------------------------
    if perfil_ferias == "Colaborador":
        st.write("Preencha os dados abaixo para enviar o pedido ao seu gestor.")
        with st.form("form_ferias", clear_on_submit=True):
            nome = st.text_input("Seu Nome Completo")
            gestor = st.text_input("E-mail do seu Gestor Direto (ex: coordenacao@conac.com.br)")
            
            col_d1, col_d2 = st.columns(2)
            inicio = col_d1.date_input("Data de Início", format="DD/MM/YYYY")
            fim = col_d2.date_input("Data de Retorno", format="DD/MM/YYYY")
            
            st.write("### Opções Adicionais")
            vender_ferias = st.checkbox("Desejo vender 1/3 das minhas férias (Abono Pecuniário)")
            adiantar_13 = st.checkbox("Desejo adiantar a 1ª parcela do meu 13º salário")
            obs = st.text_area("Observações (Opcional)", placeholder="Algum apontamento importante?")
            
            if st.form_submit_button("Enviar Solicitação", type="primary"):
                if nome and gestor:
                    texto_abono = "Sim" if vender_ferias else "Não"
                    texto_13 = "Sim" if adiantar_13 else "Não"
                    
                    aba_pedidos.append_row([nome, gestor, inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"), texto_abono, texto_13, obs, "Pendente"])
                    st.success("✅ Solicitação enviada com sucesso para aprovação!")
                else:
                    st.warning("⚠️ Preencha seu nome e o e-mail do gestor!")

    # -----------------------------------------------------
    # VISÃO GESTOR
    # -----------------------------------------------------
    elif perfil_ferias == "Gestor (Aprovação)":
        
        if "gestor_logado" not in st.session_state:
            st.session_state.gestor_logado = False
            st.session_state.email_logado = ""

        if not st.session_state.gestor_logado:
            st.write("Área restrita para aprovação de solicitações da equipe.")
            col_g1, col_g2 = st.columns(2)
            email_gestor = col_g1.text_input("Seu e-mail corporativo:")
            senha_gestor = col_g2.text_input("Sua senha de acesso:", type="password")
            
            if st.button("Acessar Painel", type="primary"):
                if email_gestor and senha_gestor:
                    try:
                        registros_gestores = aba_gestores.get_all_records()
                        if not registros_gestores:
                            dados_gestores = pd.DataFrame(columns=["E-mail do Gestor", "Senha"])
                        else:
                            dados_gestores = pd.DataFrame(registros_gestores)
                    except:
                        dados_gestores = pd.DataFrame(columns=["E-mail do Gestor", "Senha"])

                    if email_gestor not in dados_gestores["E-mail do Gestor"].values:
                        aba_gestores.append_row([email_gestor, senha_gestor])
                        st.success("🎉 Primeiro acesso detectado! Sua senha foi cadastrada e seu painel liberado.")
                        st.session_state.gestor_logado = True
                        st.session_state.email_logado = email_gestor
                        time.sleep(2)
                        st.rerun()
                    else:
                        senha_correta = dados_gestores.loc[dados_gestores["E-mail do Gestor"] == email_gestor, "Senha"].values[0]
                        if str(senha_correta) == str(senha_gestor):
                            st.session_state.gestor_logado = True
                            st.session_state.email_logado = email_gestor
                            st.rerun()
                        else:
                            st.error("❌ Senha incorreta. Tente novamente.")
        else:
            st.write(f"Bem-vindo(a), **{st.session_state.email_logado}**!")
            if st.button("Sair da Conta"):
                st.session_state.gestor_logado = False
                st.session_state.email_logado = ""
                st.rerun()
            
            st.write("---")
            st.write("### Pedidos Aguardando Análise")
            
            try:
                registros_pedidos = aba_pedidos.get_all_records()
                if not registros_pedidos:
                    pendentes = pd.DataFrame()
                else:
                    df_pedidos = pd.DataFrame(registros_pedidos)
                    pendentes = df_pedidos[(df_pedidos["E-mail do Gestor"] == st.session_state.email_logado) & (df_pedidos["Status"] == "Pendente")]
            except:
                pendentes = pd.DataFrame()

            if pendentes.empty:
                st.info("🎉 Nenhuma solicitação pendente para a sua equipe no momento.")
            else:
                for idx, row in pendentes.iterrows():
                    linha_planilha = idx + 2 
                    with st.expander(f"👤 {row['Colaborador']} | 📅 {row['Data de Início']} até {row['Data de Fim']}"):
                        st.write(f"**Abono Pecuniário (Venda de Férias):** {row.get('Abono', 'Não')}")
                        st.write(f"**Adiantamento da 1ª parc. do 13º:** {row.get('Adiantamento_13', 'Não')}")
                        if row.get('Observações', '') != "":
                            st.write(f"**Observações:** {row['Observações']}")
                        
                        st.write("")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Aprovar Pedido", key=f"apr_{idx}", type="primary"):
                            aba_pedidos.update_cell(linha_planilha, 8, "Aprovado") 
                            st.success(f"Férias de {row['Colaborador']} aprovadas!")
                            time.sleep(1)
                            st.rerun()
                            
                        if c2.button("❌ Recusar", key=f"rep_{idx}"):
                            aba_pedidos.update_cell(linha_planilha, 8, "Recusado")
                            st.error(f"Pedido de {row['Colaborador']} foi recusado.")
                            time.sleep(1)
                            st.rerun()

# =========================================================
# MÓDULOS DE SEGURANÇA (DP)
# =========================================================
elif menu_principal in ["🔒 Painel DP (Férias)", "🔒 Painel DP (Fechamento)"]:
    
    if "acesso_liberado" not in st.session_state:
        st.session_state.acesso_liberado = False

    if not st.session_state.acesso_liberado:
        st.title("🔒 Área Restrita")
        st.write("Este painel é de uso exclusivo do Departamento Pessoal.")
        senha = st.text_input("Digite a senha de acesso:", type="password")
        if st.button("Destravar Painel", type="primary"):
            if senha == "Conac2026": 
                st.session_state.acesso_liberado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    
    else:
        st.sidebar.write("---")
        if st.sidebar.button("Sair / Bloquear Tela 🔒", use_container_width=True):
            st.session_state.acesso_liberado = False
            st.rerun()

        # =========================================================
        # MÓDULO DP - FÉRIAS
        # =========================================================
        if menu_principal == "🔒 Painel DP (Férias)":
            st.title("🗂️ Gestão de Férias (DP)")
            st.write("Gerencie os pedidos aprovados pelos gestores e acompanhe o histórico da empresa.")
            
            try:
                regs_ferias = aba_pedidos.get_all_records()
                if regs_ferias:
                    df_todas_ferias = pd.DataFrame(regs_ferias)
                    
                    # 1. AÇÃO DE PROGRAMAR (PENDÊNCIAS DO DP)
                    st.subheader("📌 Aguardando Lançamento (Aprovadas pelo Gestor)")
                    aprovadas = df_todas_ferias[df_todas_ferias["Status"] == "Aprovado"]
                    
                    if aprovadas.empty:
                        st.info("🏆 Excelente! Nenhuma solicitação aprovada aguardando programação no momento.")
                    else:
                        for idx, row in aprovadas.iterrows():
                            linha_planilha = idx + 2
                            with st.expander(f"⚠️ {row['Colaborador']} | 📅 {row['Data de Início']} até {row['Data de Fim']}"):
                                st.write(f"**Aprovado por (Gestor):** {row['E-mail do Gestor']}")
                                st.write(f"**Abono (Venda):** {row.get('Abono', 'Não')} | **13º:** {row.get('Adiantamento_13', 'Não')}")
                                if row.get('Observações', '') != "":
                                    st.write(f"**Obs:** {row['Observações']}")
                                
                                if st.button("✅ Marcar como Programado", key=f"dp_prog_{idx}", type="primary"):
                                    aba_pedidos.update_cell(linha_planilha, 8, "Programado")
                                    st.success(f"Férias de {row['Colaborador']} marcadas como programadas!")
                                    time.sleep(1)
                                    st.rerun()
                                    
                    st.write("---")
                    
                    # 2. FILTROS E BASE COMPLETA
                    st.subheader("📊 Base Completa e Filtros")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        f_colab = st.text_input("🔍 Buscar Colaborador:")
                    with col_f2:
                        lista_gestores = df_todas_ferias["E-mail do Gestor"].unique().tolist()
                        f_gestor = st.multiselect("Filtro por Gestor:", lista_gestores)
                    with col_f3:
                        lista_status = df_todas_ferias["Status"].unique().tolist()
                        f_status = st.multiselect("Filtro por Status:", lista_status, default=lista_status)
                        
                    # Aplicando os filtros
                    df_filtrado = df_todas_ferias.copy()
                    if f_colab:
                        df_filtrado = df_filtrado[df_filtrado["Colaborador"].str.contains(f_colab, case=False, na=False)]
                    if f_gestor:
                        df_filtrado = df_filtrado[df_filtrado["E-mail do Gestor"].isin(f_gestor)]
                    if f_status:
                        df_filtrado = df_filtrado[df_filtrado["Status"].isin(f_status)]
                    
                    # Formatando as cores
                    def colorir_ferias(val):
                        if val == 'Pendente': return 'background-color: #FFF3E0; color: #E65100; font-weight: bold;' # Laranja
                        elif val == 'Aprovado': return 'background-color: #E3F2FD; color: #1565C0; font-weight: bold;' # Azul
                        elif val == 'Programado': return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;' # Verde
                        elif val == 'Recusado': return 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;' # Vermelho
                        return ''
                    
                    st.dataframe(df_filtrado.style.map(colorir_ferias, subset=['Status']), use_container_width=True, hide_index=True)
                    
                    # 3. EXPORTAR PARA EXCEL
                    buffer_ferias = io.BytesIO()
                    with pd.ExcelWriter(buffer_ferias, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Base_Ferias')
                    
                    st.write("")
                    st.download_button(
                        label="📥 Baixar Relatório de Férias (Excel)",
                        data=buffer_ferias.getvalue(),
                        file_name="Relatorio_Ferias_Conac.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="secondary"
                    )

                else:
                    st.info("Ainda não há solicitações de férias registradas.")
            except Exception as e:
                st.error(f"Erro ao carregar dados de férias. Detalhe: {e}")


        # =========================================================
        # MÓDULO DP - FECHAMENTO
        # =========================================================
        elif menu_principal == "🔒 Painel DP (Fechamento)":
            link_compartilhamento = "https://docs.google.com/spreadsheets/d/1QzO8FrhW-C4pH8JldKdOkVPwcZXEly76lDixSzPu9Uo/edit?usp=sharing" 
            link_excel = link_compartilhamento.split('/edit')[0] + '/export?format=xlsx'

            @st.cache_data(ttl=1800)
            def carregar_planilha_completa(url):
                return pd.read_excel(url, sheet_name=None)

            try:
                todas_as_abas = carregar_planilha_completa(link_excel)
                lista_abas = list(todas_as_abas.keys())

                col_titulo, col_mes, col_btn = st.columns([2.5, 1.5, 1])
                with col_titulo:
                    st.title("🚀 Operação DP")
                    st.write("Acompanhe a distribuição da carteira e os indicadores de fechamento.")
                with col_mes:
                    aba_selecionada = st.selectbox("📅 Mês de Referência:", lista_abas, index=len(lista_abas)-1)
                with col_btn:
                    st.write("") 
                    st.write("")
                    if st.button("🔄 Atualizar Painel", use_container_width=True):
                        carregar_planilha_completa.clear()
                        st.rerun()

                df = todas_as_abas[aba_selecionada]
                
                df = df.dropna(subset=['CÓD. COND.', 'CONDOMÍNIO']).copy()
                df['RESP'] = df['RESP'].astype(str).str.strip()
                df['FUNC'] = pd.to_numeric(df['FUNC'], errors='coerce').fillna(0).astype(int)
                df['CÓD. COND.'] = df['CÓD. COND.'].astype(str).str.replace('.0', '', regex=False)
                df['Possui Síndico Prof.'] = df['SÍNDICO PROFISSIONAL '].apply(lambda x: "Sim" if pd.notna(x) and str(x).strip() not in ['0', '0.0', 'nan'] else "Não")

                if 'Status do Fechamento' not in df.columns: df['Status do Fechamento'] = 'A Fazer'

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

            except Exception as erro_leitura:
                st.error(f"Erro ao ler a planilha principal. Detalhe: {erro_leitura}")

            st.subheader("🤖 Auditoria de FGTS (Sistema x Robô de Guias)")
            st.write("Arraste os arquivos do seu sistema e do robô abaixo para cruzar os dados.")

            if "uploader_key" not in st.session_state:
                st.session_state.uploader_key = 0

            col_upload1, col_upload2 = st.columns(2)
            with col_upload1:
                arquivo_sistema = st.file_uploader("📂 Base do Sistema", type=["xls", "xlsx"], key=f"file_sistema_{st.session_state.uploader_key}")
            with col_upload2:
                arquivo_robo = st.file_uploader("🤖 Base do Robô", type=["xls", "xlsx"], key=f"file_robo_{st.session_state.uploader_key}")

            if arquivo_sistema and arquivo_robo:
                if st.button("🔍 Cruzar Dados e Gerar Planilha", type="primary"):
                    with st.spinner("Lendo planilhas e calculando divergências..."):
                        try:
                            CODIGOS_CONSIGNADOS = [716, 717, 718, 719, 720]
                            df_robo_fgts = pd.read_excel(arquivo_robo)
                            df_robo_fgts = df_robo_fgts.rename(columns={"Código": "Cod_Empresa", "Valor Guia": "Valor_Robo", "Cond": "Nome_Condominio"})
                            df_robo_fgts["Cod_Empresa"] = pd.to_numeric(df_robo_fgts["Cod_Empresa"], errors="coerce")

                            df_bases = pd.read_excel(arquivo_sistema, sheet_name="TotalEmpresaBaseCalculo")
                            df_fgts = df_bases[df_bases["codigo_movto"] == 901].copy()
                            df_fgts["valor"] = df_fgts["valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                            df_fgts["valor"] = pd.to_numeric(df_fgts["valor"], errors="coerce").fillna(0)
                            df_fgts = df_fgts[["empresa", "valor"]].rename(columns={"empresa": "Cod_Empresa", "valor": "Valor_FGTS"})
                            df_fgts["Cod_Empresa"] = pd.to_numeric(df_fgts["Cod_Empresa"], errors="coerce")

                            df_salarios = pd.read_excel(arquivo_sistema, sheet_name="TotalEmpresaSal")
                            df_consig = df_salarios[df_salarios["codigo_movto"].isin(CODIGOS_CONSIGNADOS)].copy()
                            
                            if not df_consig.empty:
                                df_consig["valor"] = df_consig["valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                                df_consig["valor"] = pd.to_numeric(df_consig["valor"], errors="coerce").fillna(0)
                                df_consig = df_consig.groupby("empresa")["valor"].sum().reset_index()
                                df_consig = df_consig.rename(columns={"empresa": "Cod_Empresa", "valor": "Valor_Consignado"})
                                df_consig["Cod_Empresa"] = pd.to_numeric(df_consig["Cod_Empresa"], errors="coerce")
                            else:
                                df_consig = pd.DataFrame(columns=["Cod_Empresa", "Valor_Consignado"])

                            df_folha_consolidada = pd.merge(df_fgts, df_consig, on="Cod_Empresa", how="outer").fillna(0)
                            df_folha_consolidada["Valor_Folha_Total"] = df_folha_consolidada["Valor_FGTS"] + df_folha_consolidada["Valor_Consignado"]
                            comparativo = pd.merge(df_folha_consolidada, df_robo_fgts, on="Cod_Empresa", how="left", indicator=True)
                            comparativo["Valor_Folha_Total"] = comparativo["Valor_Folha_Total"].fillna(0)
                            comparativo["Valor_Robo"] = comparativo["Valor_Robo"].fillna(0)
                            comparativo["Diferenca"] = comparativo["Valor_Folha_Total"] - comparativo["Valor_Robo"]

                            def definir_status(linha):
                                if linha["_merge"] == "left_only": return "ALERTA: Guia não baixada"
                                elif abs(linha["Diferenca"]) > 0.50: return "ERRO: Valores não batem"
                                else: return "OK"

                            comparativo["Status da Conferência"] = comparativo.apply(definir_status, axis=1)
                            comparativo["Nome_Condominio"] = comparativo["Nome_Condominio"].fillna("Nome não encontrado no robô")
                            colunas_finais = ["Cod_Empresa", "Nome_Condominio", "Valor_Folha_Total", "Valor_Robo", "Diferenca", "Status da Conferência"]
                            comparativo = comparativo[colunas_finais]

                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                comparativo.to_excel(writer, index=False, sheet_name='Auditoria_FGTS')

                            st.success("✅ Auditoria finalizada! Clique no botão abaixo para baixar o relatório.")
                            def limpar_uploaders(): st.session_state.uploader_key += 1
                            st.download_button(label="📥 Baixar Planilha", data=buffer.getvalue(), file_name="Auditoria_FGTS.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary", on_click=limpar_uploaders)
                        except Exception as e:
                            st.error(f"❌ Erro ao cruzar os dados. Detalhe técnico: {e}")

            if not (arquivo_sistema or arquivo_robo):
                st_autorefresh(interval=1800000, limit=None, key="atualizacao_dp")
