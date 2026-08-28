import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Portal de Férias - Conac", page_icon="🌴", layout="centered")

# =========================================================
# BANCO DE DADOS TEMPORÁRIO (Simulação visual)
# =========================================================
if 'bd_ferias' not in st.session_state:
    st.session_state.bd_ferias = pd.DataFrame(columns=["Colaborador", "Gestor", "Início", "Fim", "Status"])

# =========================================================
# MENU LATERAL
# =========================================================
st.sidebar.title("Navegação")
perfil = st.sidebar.radio("Selecione seu perfil:", ["Colaborador", "Gestor", "Departamento Pessoal"])

# =========================================================
# TELA 1: COLABORADOR
# =========================================================
if perfil == "Colaborador":
    st.title("🌴 Solicitação de Férias")
    st.write("Preencha os dados abaixo para enviar o pedido ao seu gestor.")
    
    with st.form("form_ferias", clear_on_submit=True):
        nome = st.text_input("Seu Nome Completo")
        gestor = st.text_input("E-mail do seu Gestor Direto")
        
        col1, col2 = st.columns(2)
        inicio = col1.date_input("Data de Início", format="DD/MM/YYYY")
        fim = col2.date_input("Data de Retorno", format="DD/MM/YYYY")
        
        enviar = st.form_submit_button("Enviar Solicitação", type="primary")

        if enviar:
            nova_linha = {"Colaborador": nome, "Gestor": gestor, "Início": inicio.strftime("%d/%m/%Y"), "Fim": fim.strftime("%d/%m/%Y"), "Status": "Pendente"}
            st.session_state.bd_ferias = pd.concat([st.session_state.bd_ferias, pd.DataFrame([nova_linha])], ignore_index=True)
            st.success("✅ Solicitação enviada com sucesso para aprovação!")

# =========================================================
# TELA 2: GESTOR
# =========================================================
elif perfil == "Gestor":
    st.title("✅ Aprovação de Férias")
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
# TELA 3: DEPARTAMENTO PESSOAL
# =========================================================
elif perfil == "Departamento Pessoal":
    st.title("🗂️ Visão Geral do DP")
    st.write("Acompanhe o status de todas as solicitações da empresa.")
    
    def colorir_ferias(val):
        if val == 'Pendente': return 'background-color: #FFF3E0; color: #E65100; font-weight: bold;'
        elif val == 'Aprovado': return 'background-color: #E8F5E9; color: #2E7D32; font-weight: bold;'
        elif val == 'Recusado': return 'background-color: #FFEBEB; color: #D32F2F; font-weight: bold;'
        return ''
        
    st.dataframe(st.session_state.bd_ferias.style.map(colorir_ferias, subset=['Status']), use_container_width=True, hide_index=True)
