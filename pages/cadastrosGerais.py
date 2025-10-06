# pages/cadastros_gerais.py
import streamlit as st
import pandas as pd
from database import SessionLocal, Categoria, ProdutoPai, Variacao
from sqlalchemy import delete

def page_cadastros_gerais():
    st.header("⚙️ Cadastros Gerais (Categorias, Produtos e SKUs)")
    db_gen = SessionLocal(); db = db_gen
    
    tab_cat, tab_prod, tab_var = st.tabs(["🏷️ Categorias", "🧩 Produtos Pai", "🎨 Variações (SKUs)"])

    # --- ABA 1: CATEGORIAS ---
    with tab_cat:
        # ... (código completo do CRUD de categorias, sem alterações)
        pass

    # --- ABA 2: PRODUTOS PAI ---
    with tab_prod:
        # ... (código completo do CRUD de produtos pai, sem alterações)
        pass
        
    # --- ABA 3: VARIAÇÕES (SKUs) ---
    with tab_var:
        # ... (código completo do CRUD de variações, sem alterações)
        pass
    
    db.close()