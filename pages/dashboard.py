# pages/dashboard.py
import streamlit as st
import pandas as pd
from database import SessionLocal, Categoria, ProdutoPai, Variacao, LancamentosVendas

def page_dashboard():
    st.header("📊 Dashboard de Análise de Vendas")
    db_gen = SessionLocal(); db = db_gen

    try:
        vendas_df = pd.read_sql(db.query(LancamentosVendas).statement, db.bind)
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind)
        produtos_pai_df = pd.read_sql(db.query(ProdutoPai).statement, db.bind)
        categorias_df = pd.read_sql(db.query(Categoria).statement, db.bind)
    except Exception:
        st.info("Ainda não há dados de vendas. Importe um arquivo na página 'Importar Vendas'.")
        return
    finally:
        db.close()

    if vendas_df.empty:
        st.info("Nenhuma venda processada ainda. Importe um arquivo na página 'Importar Vendas'.")
        return

    dados_completos = pd.merge(vendas_df, variacoes_df, left_on='skuVenda', right_on='skuVariacao')
    dados_completos = pd.merge(dados_completos, produtos_pai_df, on='idProdutoPai')
    dados_completos = pd.merge(dados_completos, categorias_df, left_on='categoria_id', right_on='id', suffixes=('', '_cat'))
    dados_completos['dataPedido'] = pd.to_datetime(dados_completos['dataPedido'])
    
    st.sidebar.header("Filtros do Dashboard")
    
    plataformas_disponiveis = dados_completos['plataforma'].unique()
    plataformas_selecionadas = st.sidebar.multiselect("Filtrar por Plataforma", options=plataformas_disponiveis, key="dash_platform_filter")
    
    categorias_dict = {cat.id: cat.nome for _, cat in categorias_df.iterrows()}
    categorias_selecionadas = st.sidebar.multiselect("Filtrar por Categoria", options=list(categorias_dict.keys()), format_func=lambda x: categorias_dict[x], key="dash_cat_filter")
    
    min_date = dados_completos['dataPedido'].min().date(); max_date = dados_completos['dataPedido'].max().date()
    date_range = st.sidebar.date_input("Selecione o Período", (min_date, max_date), min_value=min_date, max_value=max_date, key="dash_date_filter")
    
    vendas_filtradas = dados_completos.copy()
    if plataformas_selecionadas: vendas_filtradas = vendas_filtradas[vendas_filtradas['plataforma'].isin(plataformas_selecionadas)]
    if categorias_selecionadas: vendas_filtradas = vendas_filtradas[vendas_filtradas['categoria_id'].isin(categorias_selecionadas)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        vendas_filtradas = vendas_filtradas[(vendas_filtradas['dataPedido'].dt.date >= start_date) & (vendas_filtradas['dataPedido'].dt.date <= end_date)]

    if vendas_filtradas.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados."); return

    receita_total_bruta = (vendas_filtradas['receitaBrutaProduto'] * vendas_filtradas['quantidade']).sum()
    custo_produto_total = (vendas_filtradas['custoTotalCalculado'] * vendas_filtradas['quantidade']).sum()
    taxas_total = vendas_filtradas['taxasMarketplace'].sum()
    cupons_total = vendas_filtradas['totalCupons'].sum()
    gasto_total = custo_produto_total + taxas_total + cupons_total
    lucro_total = vendas_filtradas['lucroLiquidoReal'].sum()
    pedidos_total = vendas_filtradas['pedidoId'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Bruta", f"R$ {receita_total_bruta:,.2f}"); col2.metric("Gasto Total", f"R$ {gasto_total:,.2f}", help="Custo dos Produtos + Insumos")
    col3.metric("Lucro Líquido", f"R$ {lucro_total:,.2f}"); col4.metric("Total de Pedidos", f"{pedidos_total}")
    
    st.markdown("---")
    st.subheader("📄 Detalhamento de Lançamentos")
    df_detalhado = vendas_filtradas.copy()
    df_detalhado['Receita Bruta Total'] = df_detalhado['receitaBrutaProduto'] * df_detalhado['quantidade']
    df_detalhado['Custo Total Produto'] = df_detalhado['custoTotalCalculado'] * df_detalhado['quantidade']
    df_final_para_exibir = df_detalhado.rename(columns={'dataPedido': 'Data', 'plataforma': 'Plataforma', 'nomeVariacao': 'Variação', 'totalCupons': 'Cupons', 'taxasMarketplace': 'Taxas', 'valorVendaLiquido': 'Venda Líquida', 'lucroLiquidoReal': 'Lucro Líquido'})

    st.dataframe(
        df_final_para_exibir[['Data', 'Plataforma', 'Variação', 'Receita Bruta Total', 'Cupons', 'Taxas', 'Venda Líquida', 'Custo Total Produto', 'Lucro Líquido']].style.format({
            'Receita Bruta Total': 'R$ {:,.2f}', 'Cupons': 'R$ {:,.2f}', 'Taxas': 'R$ {:,.2f}',
            'Venda Líquida': 'R$ {:,.2f}', 'Custo Total Produto': 'R$ {:,.2f}', 'Lucro Líquido': 'R$ {:,.2f}',
            'Data': '{:%d/%m/%Y %H:%M}'
        }),
        use_container_width=True
    )