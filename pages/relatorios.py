# pages/relatorios.py
import streamlit as st
import pandas as pd
from database import SessionLocal, Categoria, ProdutoPai, Variacao, LancamentosVendas
import re

def page_relatorios():
    st.header("📈 Relatórios de Vendas")
    db_gen = SessionLocal(); db = db_gen

    try:
        vendas_df = pd.read_sql(db.query(LancamentosVendas).statement, db.bind)
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind)
        produtos_pai_df = pd.read_sql(db.query(ProdutoPai).statement, db.bind)
        categorias_df = pd.read_sql(db.query(Categoria).statement, db.bind)
    except Exception:
        st.info("Ainda não há dados de vendas para gerar relatórios."); return
    finally:
        db.close()

    if vendas_df.empty:
        st.info("Nenhuma venda processada ainda para gerar relatórios."); return

    dados_completos = pd.merge(vendas_df, variacoes_df, left_on='skuVenda', right_on='skuVariacao')
    dados_completos = pd.merge(dados_completos, produtos_pai_df, on='idProdutoPai')
    # Renomeia a coluna 'nome' da categoria para evitar conflito antes do merge
    categorias_df = categorias_df.rename(columns={'nome': 'nome_categoria'})
    dados_completos = pd.merge(dados_completos, categorias_df, left_on='categoria_id', right_on='id')
    dados_completos['dataPedido'] = pd.to_datetime(dados_completos['dataPedido'])
    
    st.sidebar.header("Filtros do Relatório")
    
    plataformas_disponiveis = dados_completos['plataforma'].unique()
    plataformas_selecionadas_report = st.sidebar.multiselect("Filtrar por Plataforma", options=plataformas_disponiveis, key="report_platform_filter")

    categorias_dict = {cat.id: cat.nome_categoria for _, cat in categorias_df.iterrows()}
    categorias_selecionadas = st.sidebar.multiselect("Filtrar por Categoria", options=list(categorias_dict.keys()), format_func=lambda x: categorias_dict[x], key="report_cat_filter")
    
    min_date = dados_completos['dataPedido'].min().date(); max_date = dados_completos['dataPedido'].max().date()
    date_range = st.sidebar.date_input("Selecione o Período", (min_date, max_date), min_value=min_date, max_value=max_date, key="report_date_filter")

    dados_filtrados = dados_completos.copy()
    if plataformas_selecionadas_report: dados_filtrados = dados_filtrados[dados_filtrados['plataforma'].isin(plataformas_selecionadas_report)]
    if categorias_selecionadas: dados_filtrados = dados_filtrados[dados_filtrados['categoria_id'].isin(categorias_selecionadas)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        dados_filtrados = dados_filtrados[(dados_filtrados['dataPedido'].dt.date >= start_date) & (dados_filtrados['dataPedido'].dt.date <= end_date)]

    if dados_filtrados.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados."); return

    st.subheader("Relatório de Vendas por Grupo de Produto")
    
    dados_filtrados['unidadesVendidas'] = dados_filtrados['quantidade'] * dados_filtrados['quantidadeKit']
    dados_filtrados['gastoProduto'] = (dados_filtrados['custoUnidade'] * dados_filtrados['quantidadeKit']) * dados_filtrados['quantidade']

    def extrair_grupo(nome):
        return re.split(r' - | \d+', nome)[0].strip()

    dados_filtrados['grupoProduto'] = dados_filtrados['nomeVariacao'].apply(extrair_grupo)

    # Agrega os valores, agora incluindo a categoria no agrupamento
    relatorio_grupo = dados_filtrados.groupby(['grupoProduto', 'nome_categoria']).agg(
        unidadesVendidas=('unidadesVendidas', 'sum'),
        gastoTotal=('gastoProduto', 'sum')
    ).reset_index()
    
    relatorio_grupo = relatorio_grupo.sort_values(by='unidadesVendidas', ascending=False)
    
    # Renomeia as colunas para exibição
    relatorio_grupo = relatorio_grupo.rename(columns={
        'grupoProduto': 'Grupo de Produto', 
        'nome_categoria': 'Categoria',
        'unidadesVendidas': 'Total de Unidades Vendidas',
        'gastoTotal': 'Gasto Total (sem insumos)'
    })
    
    # Reordena as colunas para uma melhor visualização
    relatorio_grupo = relatorio_grupo[['Grupo de Produto', 'Categoria', 'Total de Unidades Vendidas', 'Gasto Total (sem insumos)']]

    # Aplica o estilo para centralizar o texto
    st.dataframe(
        relatorio_grupo.style.format({
            "Gasto Total (sem insumos)": "R$ {:,.2f}"
        }).set_properties(**{'text-align': 'center'}),
        use_container_width=True
    )