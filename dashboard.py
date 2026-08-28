import streamlit as st
import pandas as pd
import plotly.express as px
import io 
import time
from streamlit_autorefresh import st_autorefresh 

# Configuração inicial da página (MUITO IMPORTANTE: Deve ser a primeira linha do Streamlit)
st.set_page_config(page_title="Portal Conac RH", page_icon="🏢", layout="wide")

# =========================================================
# 1. ESTILIZAÇÃO E BLINDAGEM CSS GLOBAL
# =========================================================
st.markdown("""
    <style>
    footer {visibility: hidden;}
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="stAppViewContainer"] { opacity: 1 !important; transition: none !important; }
    [data-testid="stHeader"] { opacity: 1 !important; }
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
# 2. MENU LATERAL DE NAVEGAÇÃO
# =========================================================
st.sidebar.title("🏢 Conac RH")
menu_principal = st.sidebar.radio("Navegação:", ["🌴 Portal de Férias", "🔒 Painel DP (Fechamento)"])

# =========================================================
# MÓDULO A: PORTAL DE FÉRIAS (PÚBLICO)
# =========================================================
if menu_principal == "🌴 Portal de Férias":
    # Banco de Dados Temporário (Simulação visual até conectarmos ao Google Cloud)
    if 'bd_ferias' not in st.session_state:
        st.session_state.bd_ferias = pd.DataFrame(columns=["Colaborador", "Gestor", "Início", "Fim", "Status"])
        
    st.title("🌴 Portal de Férias")
    perfil_ferias = st.radio("Selecione seu perfil de acesso:", ["Colaborador", "Gestor (Aprovação)"], horizontal=True)
    st.write("---")

    if perfil_ferias == "Colaborador":
        st.write("Preencha os dados abaixo para enviar o pedido ao seu gestor.")
        with st.form("form_ferias", clear_on_submit=True):
            nome = st.text_input("Seu Nome Completo")
            gestor = st.text_input("E-mail do seu Gestor Direto")
            col_d1, col_d2 = st.columns(2)
            inicio = col_d1.date_input("Data de Início", format="DD/MM/YYYY")
            fim = col_d2.date_input("Data de Retorno", format="DD/MM/YYYY")
            
            if st.form_submit_button("Enviar Solicitação", type="primary"):
                nova_linha = {"Colaborador": nome, "Gestor": gestor, "Início": inicio.strftime("%d/%m/%Y"), "Fim": fim.strftime("%d/%m/%Y"), "Status": "Pendente"}
                st.session_state.bd_ferias = pd.concat([st.session_state.bd_ferias, pd.DataFrame([nova_linha])], ignore_index=True)
                st.success("✅ Solicitação enviada com sucesso para aprovação!")

    elif perfil_ferias == "Gestor (Aprovação)":
        email_gestor = st.text_input("Digite seu e-mail para ver os pedidos da sua equipe:")
        if email_gestor:
            pedidos = st.session_state.bd_ferias[(st.session_state.bd_ferias["Gestor"] == email_gestor) & (st.session_state.bd_ferias["Status"] == "Pendente")]
            if pedidos.empty:
                st.info("🎉 Nenhuma solicitação pendente para você no momento.")
            else:
                st.write("### Pedidos Aguardando Análise")
                st.dataframe(pedidos, use_container_width=True, hide_index=True)
                st.warning("⚠️ Os botões de 'Aprovar' e 'Reprovar' serão ativados após conectarmos a planilha oficial do Google.")

# =========================================================
# MÓDULO B: PAINEL DP (PROTEGIDO POR SENHA)
# =========================================================
elif menu_principal == "🔒 Painel DP (Fechamento)":
    
    # 1. Sistema de Travamento de Tela
    if "acesso_liberado" not in st.session_state:
        st.session_state.acesso_liberado = False

    if not st.session_state.acesso_liberado:
        st.title("🔒 Área Restrita")
        st.write("Este painel é de uso exclusivo do Departamento Pessoal.")
        senha = st.text_input("Digite a senha de acesso:", type="password")
        if st.button("Destravar Painel", type="primary"):
            if senha == "Conac2026": # <-- Você pode mudar a senha aqui!
                st.session_state.acesso_liberado = True
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    
    # 2. Tela Liberada (O Painel Antigo)
    else:
        st.sidebar.write("---")
        if st.sidebar.button("Sair / Bloquear Tela 🔒", use_container_width=True):
            st.session_state.acesso_liberado = False
            st.rerun()

        # Link de compartilhamento do fechamento
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

        # Atualização automática a cada 30 min (Só funciona se estiver no Painel e sem arquivos de auditoria)
        if not (arquivo_sistema or arquivo_robo):
            st_autorefresh(interval=1800000, limit=None, key="atualizacao_dp")
