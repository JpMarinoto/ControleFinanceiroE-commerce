# app.py
import streamlit as st
from pages.dashboard import page_dashboard
from pages.relatorios import page_relatorios
from pages.cadastrosGerais import page_cadastros_gerais
from pages.importarVendas import page_importar_vendas

st.set_page_config(page_title="Gestor E-commerce", page_icon="📈", layout="wide")

st.sidebar.title("Navegação")
paginas = {
    "Dashboard": page_dashboard,
    "Relatórios": page_relatorios,
    "Cadastros Gerais": page_cadastros_gerais,
    "Importar Vendas": page_importar_vendas,
}
pagina_selecionada = st.sidebar.radio("Selecione uma página:", paginas.keys())

paginas[pagina_selecionada]()