import streamlit as st
import pandas as pd
from database import SessionLocal, Item, ProdutoPai, Variacao, LancamentosVendas
from sqlalchemy.orm import Session
from sqlalchemy import delete

# --- Configuração da Página ---
st.set_page_config(page_title="Gestor E-commerce", page_icon="📈", layout="wide")

# --- Funções de Banco de Dados (Sessão) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Função de Cálculo de Custo Simplificada ---
def calcular_custo_pelo_produto_pai(db: Session, sku_variacao: str):
    variacao = db.query(Variacao).filter(Variacao.skuVariacao == sku_variacao).first()
    if not variacao or not variacao.idProdutoPai:
        return None
    produto_pai = db.query(ProdutoPai).filter(ProdutoPai.idProdutoPai == variacao.idProdutoPai).first()
    if not produto_pai:
        return None
    custo_total = (produto_pai.custoUnidade * produto_pai.quantidadeKit) + produto_pai.custoInsumos
    return custo_total

# =============================================================================
# PÁGINA DE CADASTROS GERAIS (CRUD COMPLETO)
# =============================================================================
def page_cadastros_gerais():
    st.header("⚙️ Cadastros Gerais (Produtos e SKUs)")

    db_gen = get_db()
    db = next(db_gen)

    tab1, tab2 = st.tabs(["🧩 Produtos Pai", "🎨 Variações (SKUs)"])

    with tab1:
        st.subheader("Gerenciar Produtos Pai")
        produtos_pai_df = pd.read_sql(db.query(ProdutoPai).statement, db.bind)
        st.dataframe(produtos_pai_df, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        
        with c1.expander("📝 Adicionar Novo Produto Pai"):
            with st.form("novo_produto_form", clear_on_submit=True):
                id_produto = st.text_input("ID do Produto Pai*", placeholder="Ex: P001")
                nome = st.text_input("Nome do Produto Pai*", placeholder="Ex: Kit Pele de Verão")
                custo_unidade = st.number_input("Custo por Unidade (R$)", min_value=0.0, format="%.2f")
                quantidade_kit = st.number_input("Quantidade no Kit", min_value=1, step=1)
                custo_insumos = st.number_input("Custo dos Insumos (R$)", min_value=0.0, format="%.2f", help="Embalagem, fita, etc.")
                
                if st.form_submit_button("Salvar Novo Produto"):
                    if not id_produto or not nome:
                        st.warning("Os campos com * são obrigatórios.")
                    else:
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        if db_commit.query(ProdutoPai).filter_by(idProdutoPai=id_produto).first():
                            st.error(f"ID '{id_produto}' já existe!")
                        else:
                            novo_produto = ProdutoPai(
                                idProdutoPai=id_produto, nomeProdutoPai=nome,
                                custoUnidade=custo_unidade, quantidadeKit=quantidade_kit,
                                custoInsumos=custo_insumos
                            )
                            db_commit.add(novo_produto)
                            db_commit.commit()
                            st.success("Produto Pai adicionado!")
                            st.rerun()

        with c2.expander("✏️ Editar Produto Pai Existente"):
            lista_produtos_pai_ids = [p.idProdutoPai for p in db.query(ProdutoPai).all()]
            if not lista_produtos_pai_ids:
                st.info("Nenhum produto para editar.")
            else:
                id_para_editar = st.selectbox("Selecione o Produto para Editar", options=lista_produtos_pai_ids, key="edit_prod")
                produto_selecionado = db.query(ProdutoPai).filter_by(idProdutoPai=id_para_editar).first()
                
                with st.form("edit_produto_form"):
                    st.text(f"Editando: {produto_selecionado.idProdutoPai}")
                    novo_nome = st.text_input("Nome do Produto Pai*", value=produto_selecionado.nomeProdutoPai)
                    novo_custo_unidade = st.number_input("Custo por Unidade (R$)", value=produto_selecionado.custoUnidade, format="%.2f")
                    nova_qtd_kit = st.number_input("Quantidade no Kit", value=produto_selecionado.quantidadeKit, min_value=1, step=1)
                    novo_custo_insumos = st.number_input("Custo dos Insumos (R$)", value=produto_selecionado.custoInsumos, format="%.2f")

                    if st.form_submit_button("Atualizar Produto"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        produto_para_atualizar = db_commit.query(ProdutoPai).filter_by(idProdutoPai=id_para_editar).first()
                        produto_para_atualizar.nomeProdutoPai = novo_nome
                        produto_para_atualizar.custoUnidade = novo_custo_unidade
                        produto_para_atualizar.quantidadeKit = nova_qtd_kit
                        produto_para_atualizar.custoInsumos = novo_custo_insumos
                        db_commit.commit()
                        st.success("Produto Pai atualizado!")
                        st.rerun()

        with c3.expander("❌ Deletar Produto Pai"):
            lista_produtos_pai_ids_del = [p.idProdutoPai for p in db.query(ProdutoPai).all()]
            if not lista_produtos_pai_ids_del:
                st.info("Nenhum produto para deletar.")
            else:
                id_para_deletar = st.selectbox("Selecione o Produto para Deletar", options=lista_produtos_pai_ids_del, key="del_prod")
                st.warning("Atenção: Deletar um Produto Pai também deletará todas as suas Variações (SKUs) associadas.")
                if st.button("Deletar Produto e SKUs Associados"):
                    db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                    db_commit.execute(delete(Variacao).where(Variacao.idProdutoPai == id_para_deletar))
                    db_commit.execute(delete(ProdutoPai).where(ProdutoPai.idProdutoPai == id_para_deletar))
                    db_commit.commit()
                    st.success("Produto Pai e suas variações deletados!")
                    st.rerun()

    with tab2:
        st.subheader("Gerenciar Variações (SKUs)")
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind)
        st.dataframe(variacoes_df, use_container_width=True)
        
        c1_var, c2_var, c3_var = st.columns(3)
        
        with c1_var.expander("📝 Adicionar Nova Variação (SKU)"):
            produtos_pai_lista = [p.idProdutoPai for p in db.query(ProdutoPai).all()]
            if not produtos_pai_lista:
                st.warning("Cadastre um Produto Pai na aba anterior primeiro.")
            else:
                with st.form("nova_variacao_form", clear_on_submit=True):
                    sku_variacao = st.text_input("SKU da Variação*", placeholder="Ex: KV001-AZ")
                    nome_variacao = st.text_input("Nome da Variação*", placeholder="Ex: Kit Pele de Verão - Azul")
                    id_pai_selecionado = st.selectbox("Associar ao Produto Pai*", options=produtos_pai_lista)
                    if st.form_submit_button("Salvar Nova Variação"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        if db_commit.query(Variacao).filter_by(skuVariacao=sku_variacao).first():
                            st.error(f"SKU '{sku_variacao}' já existe!")
                        else:
                            db_commit.add(Variacao(skuVariacao=sku_variacao, nomeVariacao=nome_variacao, idProdutoPai=id_pai_selecionado))
                            db_commit.commit()
                            st.success("Variação adicionada!")
                            st.rerun()

        with c2_var.expander("✏️ Editar Variação (SKU)"):
            lista_variacoes_skus = [v.skuVariacao for v in db.query(Variacao).all()]
            if not lista_variacoes_skus:
                st.info("Nenhuma variação para editar.")
            else:
                sku_para_editar = st.selectbox("Selecione a Variação para Editar", options=lista_variacoes_skus, key="edit_var")
                variacao_selecionada = db.query(Variacao).filter_by(skuVariacao=sku_para_editar).first()
                
                with st.form("edit_variacao_form"):
                    st.text(f"Editando: {variacao_selecionada.skuVariacao}")
                    novo_nome_var = st.text_input("Novo Nome da Variação*", value=variacao_selecionada.nomeVariacao)
                    if st.form_submit_button("Atualizar Variação"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        variacao_para_atualizar = db_commit.query(Variacao).filter_by(skuVariacao=sku_para_editar).first()
                        variacao_para_atualizar.nomeVariacao = novo_nome_var
                        db_commit.commit()
                        st.success("Variação atualizada!")
                        st.rerun()

        with c3_var.expander("❌ Deletar Variação (SKU)"):
            lista_variacoes_skus_del = [v.skuVariacao for v in db.query(Variacao).all()]
            if not lista_variacoes_skus_del:
                st.info("Nenhuma variação para deletar.")
            else:
                sku_para_deletar = st.selectbox("Selecione a Variação para Deletar", options=lista_variacoes_skus_del, key="del_var")
                if st.button("Deletar Variação Selecionada"):
                    db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                    db_commit.execute(delete(Variacao).where(Variacao.skuVariacao == sku_para_deletar))
                    db_commit.commit()
                    st.success("Variação deletada!")
                    st.rerun()

# =============================================================================
# PÁGINA: IMPORTAR VENDAS
# =============================================================================
def page_importar_vendas():
    st.header("📥 Importar e Processar Vendas")
    uploaded_file = st.file_uploader("Escolha seu arquivo de vendas da Shopee (.xlsx)", type="xlsx")

    if uploaded_file is not None:
        try:
            df_shopee = pd.read_excel(uploaded_file, dtype=str)
            st.success("Arquivo carregado! Pré-visualização:")
            st.dataframe(df_shopee.head())

            if st.button("🚀 Processar Vendas"):
                with st.spinner("Processando..."), SessionLocal() as db:
                    ids_existentes = {str(id[0]) for id in db.query(LancamentosVendas.pedidoId).all()}
                    
                    df_shopee.columns = df_shopee.columns.str.strip()
                    # Mapeamento robusto para colunas de cupom
                    mapa_colunas = {
                        "ID do pedido": "pedidoId", "Data de criação do pedido": "dataPedido",
                        "Número de referência SKU": "skuVenda", "Quantidade": "quantidade",
                        "Preço acordado": "receitaBrutaProduto", "Taxa de comissão": "taxaComissao",
                        "Taxa de serviço": "taxaServico", "Taxa de transação": "taxaTransacao",
                        "Cupom do vendedor": "cupomVendedor", "Cupom Shopee": "cupomShopee",
                        "Reembolso Shopee": "reembolsoShopee"
                    }
                    df_vendas = df_shopee.rename(columns=mapa_colunas)
                    
                    colunas_numericas = ['quantidade', 'receitaBrutaProduto', 'taxaComissao', 'taxaServico', 'taxaTransacao', 'cupomVendedor', 'cupomShopee', 'reembolsoShopee']
                    for col in colunas_numericas:
                        if col not in df_vendas.columns:
                            df_vendas[col] = 0 # Adiciona a coluna com 0 se não existir
                        # Converte para número, tratando erros e valores não numéricos como 0
                        df_vendas[col] = pd.to_numeric(df_vendas[col], errors='coerce').fillna(0)

                    df_vendas["taxasMarketplace"] = df_vendas["taxaComissao"] + df_vendas["taxaServico"] + df_vendas["taxaTransacao"]
                    df_vendas["totalCupons"] = df_vendas["cupomVendedor"] + df_vendas["cupomShopee"] + df_vendas["reembolsoShopee"]

                    novos_lancamentos, skus_nao_encontrados, vendas_duplicadas = [], [], 0
                    
                    for _, venda in df_vendas.iterrows():
                        pedido_id, sku = str(venda.get('pedidoId')), venda.get('skuVenda')

                        if pedido_id in ids_existentes:
                            vendas_duplicadas += 1
                            continue

                        custo_do_kit = calcular_custo_pelo_produto_pai(db, sku)

                        if custo_do_kit is not None:
                            receita_bruta_total = venda['receitaBrutaProduto'] * venda['quantidade']
                            custo_total_produtos = custo_do_kit * venda['quantidade']
                            
                            valor_venda_liquido = receita_bruta_total - venda['totalCupons'] - venda['taxasMarketplace']
                            lucro_liquido = valor_venda_liquido - custo_total_produtos

                            novos_lancamentos.append(LancamentosVendas(
                                pedidoId=pedido_id,
                                dataPedido=pd.to_datetime(venda['dataPedido']),
                                skuVenda=sku,
                                quantidade=int(venda['quantidade']),
                                receitaBrutaProduto=venda['receitaBrutaProduto'],
                                totalCupons=venda['totalCupons'],
                                taxasMarketplace=venda['taxasMarketplace'],
                                valorVendaLiquido=valor_venda_liquido,
                                custoTotalCalculado=custo_do_kit,
                                lucroLiquidoReal=lucro_liquido
                            ))
                        elif sku and sku not in skus_nao_encontrados:
                            skus_nao_encontrados.append(sku)

                    if novos_lancamentos:
                        db.add_all(novos_lancamentos)
                        db.commit()
                        st.success(f"{len(novos_lancamentos)} novas vendas processadas e salvas!")
                    
                    if vendas_duplicadas > 0: st.info(f"{vendas_duplicadas} vendas já existiam e foram ignoradas.")
                    if skus_nao_encontrados: st.warning("ALERTA: Os seguintes SKUs da sua planilha não foram encontrados ou não estão associados a um Produto Pai com custo definido. Verifique a tela de Cadastros Gerais."); st.json(skus_nao_encontrados)

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =============================================================================
# PÁGINA: DASHBOARD DE ANÁLISE
# =============================================================================
def page_dashboard():
    st.header("📊 Dashboard de Análise de Vendas")
    db_gen = get_db()
    db = next(db_gen)

    try:
        vendas = pd.read_sql(db.query(LancamentosVendas).statement, db.bind)
        variacoes = pd.read_sql(db.query(Variacao).statement, db.bind)
    except Exception:
        st.info("Ainda não há dados de vendas. Importe um arquivo na página 'Importar Vendas'.")
        return

    if vendas.empty:
        st.info("Nenhuma venda processada ainda. Importe um arquivo na página 'Importar Vendas'.")
        return

    vendas['dataPedido'] = pd.to_datetime(vendas['dataPedido'])
    
    st.sidebar.header("Filtros do Dashboard")
    min_date = vendas['dataPedido'].min().date()
    max_date = vendas['dataPedido'].max().date()
    date_range = st.sidebar.date_input("Selecione o Período", (min_date, max_date), min_value=min_date, max_value=max_date)

    vendas_filtradas = vendas.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        vendas_filtradas = vendas[(vendas['dataPedido'].dt.date >= start_date) & (vendas['dataPedido'].dt.date <= end_date)]

    receita_total_bruta = (vendas_filtradas['receitaBrutaProduto'] * vendas_filtradas['quantidade']).sum()
    custo_produto_total = (vendas_filtradas['custoTotalCalculado'] * vendas_filtradas['quantidade']).sum()
    taxas_total = vendas_filtradas['taxasMarketplace'].sum()
    cupons_total = vendas_filtradas['totalCupons'].sum()
    gasto_total = custo_produto_total + taxas_total + cupons_total
    lucro_total = vendas_filtradas['lucroLiquidoReal'].sum()
    pedidos_total = vendas_filtradas['pedidoId'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Bruta", f"R$ {receita_total_bruta:,.2f}")
    col2.metric("Gasto Total", f"R$ {gasto_total:,.2f}", help="Custo dos Produtos + Taxas + Cupons")
    col3.metric("Lucro Líquido", f"R$ {lucro_total:,.2f}")
    col4.metric("Total de Pedidos", f"{pedidos_total}")

    st.markdown("---")
    
    st.subheader("📄 Detalhamento de Lançamentos")
    df_detalhado = pd.merge(vendas_filtradas, variacoes[['skuVariacao', 'nomeVariacao']], left_on='skuVenda', right_on='skuVariacao', how='left')
    df_detalhado['Receita Bruta Total'] = df_detalhado['receitaBrutaProduto'] * df_detalhado['quantidade']
    df_detalhado['Custo Total Produto'] = df_detalhado['custoTotalCalculado'] * df_detalhado['quantidade']
    df_final_para_exibir = df_detalhado.rename(columns={'dataPedido': 'Data', 'nomeVariacao': 'Variação', 'totalCupons': 'Cupons', 'taxasMarketplace': 'Taxas', 'valorVendaLiquido': 'Venda Líquida', 'lucroLiquidoReal': 'Lucro Líquido'})

    st.dataframe(
        df_final_para_exibir[['Data', 'Variação', 'Receita Bruta Total', 'Cupons', 'Taxas', 'Venda Líquida', 'Custo Total Produto', 'Lucro Líquido']].style.format({
            'Receita Bruta Total': 'R$ {:,.2f}', 'Cupons': 'R$ {:,.2f}', 'Taxas': 'R$ {:,.2f}',
            'Venda Líquida': 'R$ {:,.2f}', 'Custo Total Produto': 'R$ {:,.2f}', 'Lucro Líquido': 'R$ {:,.2f}',
            'Data': '{:%d/%m/%Y %H:%M}'
        }),
        use_container_width=True
    )

# =============================================================================
# NAVEGAÇÃO PRINCIPAL
# =============================================================================
st.sidebar.title("Navegação")
paginas = {
    "Dashboard": page_dashboard,
    "Cadastros Gerais (CRUD)": page_cadastros_gerais,
    "Importar Vendas": page_importar_vendas,
}
pagina_selecionada = st.sidebar.radio("Selecione uma página:", paginas.keys())
paginas[pagina_selecionada]()