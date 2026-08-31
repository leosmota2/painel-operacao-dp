import streamlit as st
import pandas as pd
import plotly.express as px
import io 
import time
import json
import gspread
from google.oauth2.service_account import Credentials
from streamlit_autorefresh import st_autorefresh 
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Portal Conac DP", page_icon="🏢", layout="wide")

# =========================================================
# CONFIGURAÇÃO GERAL
# =========================================================
# Cole o link do seu site aqui (ele será usado no botão do e-mail do Gestor)
LINK_DO_PAINEL = "https://painel-operacao-dp-mmqx3ub3xp5xagyjmrfcfd.streamlit.app/#portal-de-ferias" 

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
# FUNÇÃO: DISPARO DE E-MAILS (GMAIL)
# =========================================================
def disparar_email(destinatario, assunto, mensagem_html):
    try:
        remetente = st.secrets["email"]["remetente"]
        senha = st.secrets["email"]["senha"]
        
        msg = MIMEMultipart()
        msg['From'] = f"Portal Conac DP <{remetente}>"
        msg['To'] = destinatario
        msg['Subject'] = assunto
        
        msg.attach(MIMEText(mensagem_html, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Erro técnico ao enviar e-mail: {e}")
        return False

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
st.sidebar.title("🏢 Conac DP")
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
            col_nome, col_email = st.columns(2)
            nome = col_nome.text_input("Seu Nome Completo")
            email_colab = col_email.text_input("Seu E-mail Corporativo") 
            
            gestor = st.text_input("E-mail do seu Gestor Direto (ex: coordenacao@conac.com.br)")
            
            col_d1, col_d2 = st.columns(2)
            inicio = col_d1.date_input("Data de Início", format="DD/MM/YYYY")
            fim = col_d2.date_input("Data de Retorno", format="DD/MM/YYYY")
            
            st.write("### Opções Adicionais")
            vender_ferias = st.checkbox("Desejo vender 1/3 das minhas férias (Abono Pecuniário)")
            adiantar_13 = st.checkbox("Desejo adiantar a 1ª parcela do meu 13º salário")
            obs = st.text_area("Observações (Opcional)", placeholder="Algum apontamento importante?")
            
            if st.form_submit_button("Enviar Solicitação", type="primary"):
                if nome and gestor and email_colab:
                    texto_abono = "Sim" if vender_ferias else "Não"
                    texto_13 = "Sim" if adiantar_13 else "Não"
                    
                    aba_pedidos.append_row([nome, email_colab, gestor, inicio.strftime("%d/%m/%Y"), fim.strftime("%d/%m/%Y"), texto_abono, texto_13, obs, "Pendente"])
                    
                    # DISPARO DE E-MAIL 1: AVISANDO O GESTOR (COM BOTÃO)
                    assunto = f"Nova Solicitação de Férias: {nome}"
                    msg_html = f"""
                    <div style="font-family: Arial, sans-serif; color: #333; padding: 20px; max-width: 600px; border: 1px solid #eaeaea; border-radius: 10px;">
                        <h2 style="color: #103149;">Portal Conac DP 🌴</h2>
                        <p>Olá! Você tem uma nova solicitação de férias aguardando sua análise.</p>
                        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                            <p style="margin: 5px 0;"><b>Colaborador:</b> {nome}</p>
                            <p style="margin: 5px 0;"><b>Período:</b> {inicio.strftime("%d/%m/%Y")} até {fim.strftime("%d/%m/%Y")}</p>
                            <p style="margin: 5px 0;"><b>Abono (Venda):</b> {texto_abono}</p>
                            <p style="margin: 5px 0;"><b>Adiantamento 13º:</b> {texto_13}</p>
                        </div>
                        <p>Clique no botão abaixo para acessar o Portal do DP, visualizar os detalhes e tomar sua decisão:</p>
                        <div style="text-align: center; margin: 25px 0;">
                            <a href="{LINK_DO_PAINEL}" style="background-color: #E55523; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">Acessar Portal do DP</a>
                        </div>
                    </div>
                    """
                    disparar_email(gestor, assunto, msg_html)
                    
                    st.success("✅ Solicitação enviada com sucesso para o seu gestor! Você será notificado por e-mail quando houver novidades.")
                else:
                    st.warning("⚠️ Preencha seu nome, seu e-mail e o e-mail do gestor!")

    # -----------------------------------------------------
    # VISÃO GESTOR (LISTA VIP)
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
                        dados_gestores = pd.DataFrame(registros_gestores) if registros_gestores else pd.DataFrame(columns=["E-mail do Gestor", "Senha"])
                    except:
                        dados_gestores = pd.DataFrame(columns=["E-mail do Gestor", "Senha"])

                    if email_gestor not in dados_gestores["E-mail do Gestor"].values:
                        st.error("🚫 Acesso Negado: E-mail não pré-cadastrado na base de líderes. Fale com o DP.")
                    else:
                        linha_gestor = dados_gestores[dados_gestores["E-mail do Gestor"] == email_gestor].index[0] + 2
                        senha_cadastrada = dados_gestores.loc[dados_gestores["E-mail do Gestor"] == email_gestor, "Senha"].values[0]
                        
                        if pd.isna(senha_cadastrada) or str(senha_cadastrada).strip() == "":
                            aba_gestores.update_cell(int(linha_gestor), 2, senha_gestor)
                            st.success("🎉 Primeiro acesso! Sua senha foi cadastrada com sucesso.")
                            st.session_state.gestor_logado = True
                            st.session_state.email_logado = email_gestor
                            time.sleep(2)
                            st.rerun()
                        elif str(senha_cadastrada) == str(senha_gestor):
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
                pendentes = pd.DataFrame(registros_pedidos) if registros_pedidos else pd.DataFrame()
                if not pendentes.empty:
                    pendentes = pendentes[(pendentes["E-mail do Gestor"] == st.session_state.email_logado) & (pendentes["Status"] == "Pendente")]
            except:
                pendentes = pd.DataFrame()

            if pendentes.empty:
                st.info("🎉 Nenhuma solicitação pendente para a sua equipe no momento.")
            else:
                for idx, row in pendentes.iterrows():
                    linha_planilha = idx + 2 
                    with st.expander(f"👤 {row['Colaborador']} | 📅 {row['Data de Início']} até {row['Data de Fim']}"):
                        st.write(f"**Abono Pecuniário:** {row.get('Abono', 'Não')} | **Adiant. 13º:** {row.get('Adiantamento_13', 'Não')}")
                        if row.get('Observações', '') != "":
                            st.write(f"**Observações:** {row['Observações']}")
                        
                        st.write("")
                        c1, c2 = st.columns(2)
                        
                        if c1.button("✅ Aprovar Pedido", key=f"apr_{idx}", type="primary"):
                            aba_pedidos.update_cell(linha_planilha, 9, "Aprovado")
                            
                            # DISPARO DE E-MAIL 2: AVISANDO O COLABORADOR (APROVADO)
                            if row.get("E-mail do Colaborador"):
                                assunto = "Boas notícias! Suas férias foram aprovadas ✅"
                                msg_html = f"""
                                <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
                                    <h2 style="color: #2E7D32;">Portal Conac DP 🌴</h2>
                                    <p>Olá {row['Colaborador']}!</p>
                                    <p>Seu pedido de férias para o período de <b>{row['Data de Início']} a {row['Data de Fim']}</b> foi <b>aprovado</b> pelo seu gestor.</p>
                                    <p>O Departamento Pessoal dará andamento à programação e você será notificado quando estiver tudo pronto no sistema.</p>
                                </div>
                                """
                                disparar_email(row['E-mail do Colaborador'], assunto, msg_html)
                                
                            st.success(f"Férias aprovadas!")
                            time.sleep(1.5)
                            st.rerun()
                            
                        if c2.button("❌ Recusar", key=f"rep_{idx}"):
                            aba_pedidos.update_cell(linha_planilha, 9, "Recusado")
                            
                            # DISPARO DE E-MAIL 3: AVISANDO O COLABORADOR (RECUSADO)
                            if row.get("E-mail do Colaborador"):
                                assunto = "Atualização do seu pedido de férias ❌"
                                msg_html = f"""
                                <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
                                    <h2 style="color: #D32F2F;">Portal Conac DP 🌴</h2>
                                    <p>Olá {row['Colaborador']}.</p>
                                    <p>Infelizmente, seu pedido de férias para o período de <b>{row['Data de Início']} a {row['Data de Fim']}</b> foi <b>recusado</b> pelo seu gestor.</p>
                                    <p>Por favor, converse diretamente com a liderança para alinhar um novo período.</p>
                                </div>
                                """
                                disparar_email(row['E-mail do Colaborador'], assunto, msg_html)
                                
                            st.error(f"Pedido recusado.")
                            time.sleep(1.5)
                            st.rerun()

# =========================================================
# MÓDULOS DE SEGURANÇA (DP)
# =========================================================
elif menu_principal in ["🔒 Painel DP (Férias)", "🔒 Painel DP (Fechamento)"]:
    
    if "acesso_liberado" not in st.session_state:
        st.session_state.acesso_liberado = False

    if not st.session_state.acesso_liberado:
        st.title("🔒 Área Restrita")
        st.write("Painel de uso exclusivo do Departamento Pessoal.")
        senha = st.text_input("Digite a senha de acesso (DP):", type="password")
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
        # MÓDULO DP - FÉRIAS (AGORA ANTI-POLUIÇÃO)
        # =========================================================
        if menu_principal == "🔒 Painel DP (Férias)":
            st.title("🗂️ Gestão de Férias (DP)")
            
            try:
                regs_ferias = aba_pedidos.get_all_records()
                if regs_ferias:
                    df_todas_ferias = pd.DataFrame(regs_ferias)
                    
                    st.subheader("📌 Aguardando Lançamento (Aprovadas pelo Gestor)")
                    aprovadas = df_todas_ferias[df_todas_ferias["Status"] == "Aprovado"]
                    
                    if aprovadas.empty:
                        st.info("🏆 Excelente! Nenhuma solicitação aguardando programação.")
                    else:
                        for idx, row in aprovadas.iterrows():
                            linha_planilha = idx + 2
                            with st.expander(f"⚠️ {row['Colaborador']} | 📅 {row['Data de Início']} até {row['Data de Fim']}"):
                                st.write(f"**Gestor:** {row['E-mail do Gestor']} | **E-mail Colab:** {row.get('E-mail do Colaborador', 'Não informado')}")
                                st.write(f"**Abono (Venda):** {row.get('Abono', 'Não')} | **13º:** {row.get('Adiantamento_13', 'Não')}")
                                if row.get('Observações', '') != "":
                                    st.write(f"**Obs:** {row['Observações']}")
                                
                                if st.button("✅ Marcar como Programado", key=f"dp_prog_{idx}", type="primary"):
                                    aba_pedidos.update_cell(linha_planilha, 9, "Programado")
                                    
                                    # DISPARO DE E-MAIL 4: AVISANDO COLABORADOR E GESTOR (PROGRAMADO)
                                    destinatarios = []
                                    if row.get("E-mail do Colaborador"): destinatarios.append(row["E-mail do Colaborador"])
                                    if row.get("E-mail do Gestor"): destinatarios.append(row["E-mail do Gestor"])
                                    
                                    if destinatarios:
                                        assunto = "Férias Programadas pelo DP 🏢"
                                        msg_html = f"""
                                        <div style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
                                            <h2 style="color: #E55523;">Portal Conac DP 🌴</h2>
                                            <p>Olá!</p>
                                            <p>As férias de <b>{row['Colaborador']}</b> para o período de <b>{row['Data de Início']} a {row['Data de Fim']}</b> foram oficialmente <b>programadas no sistema</b> pelo Departamento Pessoal.</p>
                                            <p>Qualquer dúvida, a equipe do DP está à disposição.</p>
                                        </div>
                                        """
                                        disparar_email(", ".join(destinatarios), assunto, msg_html)
                                    
                                    st.success(f"Férias programadas no sistema e avisos enviados!")
                                    time.sleep(1.5)
                                    st.rerun()
                                    
                    st.write("---")
                    
                    st.subheader("📊 Filtro Inteligente da Base")
                    st.caption("Solicitações programadas e recusadas ficam ocultas por padrão. Adicione-as no filtro abaixo se desejar ver o histórico.")
                    col_f1, col_f2, col_f3 = st.columns(3)
                    with col_f1:
                        f_colab = st.text_input("🔍 Buscar Colaborador:")
                    with col_f2:
                        lista_gestores = df_todas_ferias["E-mail do Gestor"].unique().tolist()
                        f_gestor = st.multiselect("Filtro por Gestor:", lista_gestores)
                    with col_f3:
                        lista_status = df_todas_ferias["Status"].unique().tolist()
                        status_padrao = [s for s in lista_status if s in ['Aprovado', 'Pendente']]
                        f_status = st.multiselect("Filtro por Status:", lista_status, default=status_padrao)
                        
                    df_filtrado = df_todas_ferias.copy()
                    if f_colab: df_filtrado = df_filtrado[df_filtrado["Colaborador"].str.contains(f_colab, case=False, na=False)]
                    if f_gestor: df_filtrado = df_filtrado[df_filtrado["E-mail do Gestor"].isin(f_gestor)]
                    if f_status: df_filtrado = df_filtrado[df_filtrado["Status"].isin(f_status)]
                    
                    def colorir_ferias(val):
                        if val == 'Pendente': return 'background-color: #FFF3E0; color: #E65100; font-weight: bold;' 
                        elif val == 'Aprovado': return 'background-color: #E3F2FD; color: #1565C0; font-weight: bold;' 
                        elif val == 'Programado': return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;' 
                        elif val == 'Recusado': return 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;' 
                        return ''
                    
                    st.dataframe(df_filtrado.style.map(colorir_ferias, subset=['Status']), use_container_width=True, hide_index=True)
                    
                    buffer_ferias = io.BytesIO()
                    with pd.ExcelWriter(buffer_ferias, engine='openpyxl') as writer:
                        df_filtrado.to_excel(writer, index=False, sheet_name='Base_Ferias')
                    st.write("")
                    st.download_button(label="📥 Baixar Relatório Filtrado (Excel)", data=buffer_ferias.getvalue(), file_name="Relatorio_Ferias_Conac.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="secondary")

                else:
                    st.info("Ainda não há solicitações de férias registradas.")
            except Exception as e:
                st.error(f"Erro ao carregar dados de férias. Detalhe: {e}")

        # =========================================================
        # MÓDULO DP - FECHAMENTO (MANTIDO INTACTO)
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

            except Exception as e:
                st.error(f"Erro ao carregar fechamento. Detalhe: {e}")
