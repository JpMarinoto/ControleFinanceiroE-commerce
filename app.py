import streamlit as st
import pandas as pd
from database import SessionLocal, Item, ProdutoPai, Variacao, LancamentosVendas
from sqlalchemy import func
import datetime

# --- Configuração da Página ---
st.set_page_config(page_title="Gestor E-commerce", page_icon="📈", layout="wide")

# --- Funções de Banco de Dados (Sessão) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ... (As funções das páginas de cadastro - Itens, Produtos Pai, Variações - não precisam de alteração) ...
# =============================================================================
# PÁGINA 1: GERENCIAR ITENS
# =============================================================================
def page_gerenciar_itens():
    st.header("📦 Gerenciamento de Itens (Matéria-Prima)")

    def carregar_itens():
        db_gen = get_db()
        db = next(db_gen)
        itens = db.query(Item).order_by(Item.skuItem).all()
        return pd.DataFrame([item.__dict__ for item in itens]).drop('_sa_instance_state', axis=1) if itens else pd.DataFrame()

    df_itens = carregar_itens()
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander("📝 Adicionar Novo Item", expanded=True):
            with st.form("novo_item_form", clear_on_submit=True):
                sku = st.text_input("SKU do Item", placeholder="Ex: IT001")
                nome = st.text_input("Nome do Item", placeholder="Ex: Caixa de Papelão P")
                custo = st.number_input("Custo de Aquisição (R$)", min_value=0.0, format="%.2f")
                if st.form_submit_button("Adicionar Item"):
                    if not sku or not nome or custo <= 0:
                        st.warning("Preencha todos os campos.")
                    else:
                        db_gen = get_db()
                        db = next(db_gen)
                        if db.query(Item).filter(Item.skuItem == sku).first():
                            st.error(f"SKU '{sku}' já existe!")
                        else:
                            db.add(Item(skuItem=sku, nomeItem=nome, custoUnitarioAquisicao=custo))
                            db.commit()
                            st.success(f"Item '{nome}' adicionado!")
                            st.rerun()
    with col2:
        st.subheader("📋 Itens Cadastrados")
        st.dataframe(df_itens, use_container_width=True, height=600)

# =============================================================================
# PÁGINA 2: GERENCIAR PRODUTOS PAI
# =============================================================================
def page_gerenciar_produtos_pai():
    st.header("🧩 Gerenciamento de Produtos Pai")

    def carregar_produtos():
        db_gen = get_db()
        db = next(db_gen)
        produtos = db.query(ProdutoPai).order_by(ProdutoPai.idProdutoPai).all()
        if not produtos: return pd.DataFrame()
        df = pd.DataFrame([p.__dict__ for p in produtos]).drop('_sa_instance_state', axis=1)
        df['custoTotalKit'] = (df['custoUnidade'] * df['quantidadeKit']) + df['custoInsumos']
        return df

    df_produtos = carregar_produtos()
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander("📝 Adicionar Novo Produto Pai", expanded=True):
            with st.form("novo_produto_form", clear_on_submit=True):
                id_produto = st.text_input("ID do Produto Pai", placeholder="Ex: RIPADO-75")
                nome = st.text_input("Nome do Produto Pai", placeholder="Ex: Kit Ripado 75 Unidades")
                custo_unidade = st.number_input("Custo por Unidade (R$)", min_value=0.0, format="%.2f", help="Custo de uma única peça do produto principal.")
                quantidade_kit = st.number_input("Quantidade no Kit", min_value=1, step=1, help="Quantas unidades compõem o kit.")
                custo_insumos = st.number_input("Custo dos Insumos (R$)", min_value=0.0, format="%.2f", help="Soma dos custos de embalagem, etc.")
                if st.form_submit_button("Adicionar Produto"):
                    if not id_produto or not nome or custo_unidade <= 0 or quantidade_kit <= 0:
                        st.warning("Preencha todos os campos obrigatórios.")
                    else:
                        db_gen = get_db()
                        db = next(db_gen)
                        if db.query(ProdutoPai).filter(ProdutoPai.idProdutoPai == id_produto).first():
                            st.error(f"ID '{id_produto}' já existe!")
                        else:
                            db.add(ProdutoPai(idProdutoPai=id_produto, nomeProdutoPai=nome, custoUnidade=custo_unidade, quantidadeKit=quantidade_kit, custoInsumos=custo_insumos))
                            db.commit()
                            st.success(f"Produto '{nome}' adicionado!")
                            st.rerun()
    with col2:
        st.subheader("📋 Produtos Pai Cadastrados")
        st.dataframe(df_produtos, use_container_width=True, height=600)

# =============================================================================
# PÁGINA 3: GERENCIAR VARIAÇÕES
# =============================================================================
def page_gerenciar_variacoes():
    st.header("🎨 Gerenciamento de Variações (SKUs de Venda)")

    def carregar_variacoes():
        db_gen = get_db()
        db = next(db_gen)
        variacoes = db.query(Variacao, ProdutoPai.nomeProdutoPai).join(ProdutoPai).order_by(Variacao.skuVariacao).all()
        if not variacoes: return pd.DataFrame()
        lista_variacoes = [{'skuVariacao': v.skuVariacao, 'nomeVariacao': v.nomeVariacao, 'idProdutoPai': v.idProdutoPai, 'nomeProdutoPai': nome_pai} for v, nome_pai in variacoes]
        return pd.DataFrame(lista_variacoes)

    def carregar_produtos_pai_lista():
        db_gen = get_db()
        db = next(db_gen)
        return [p.idProdutoPai for p in db.query(ProdutoPai).order_by(ProdutoPai.idProdutoPai).all()]

    df_variacoes = carregar_variacoes()
    lista_produtos_pai = carregar_produtos_pai_lista()
    col1, col2 = st.columns([1, 2])
    with col1:
        with st.expander("📝 Adicionar Nova Variação", expanded=True):
            if not lista_produtos_pai:
                st.warning("Cadastre um Produto Pai primeiro.")
            else:
                with st.form("nova_variacao_form", clear_on_submit=True):
                    sku_variacao = st.text_input("SKU da Variação (SKU de Venda)", placeholder="Ex: Ripado-Verde-75uni")
                    nome_variacao = st.text_input("Nome da Variação", placeholder="Ex: Ripado Verde 75 Unidades")
                    id_pai_selecionado = st.selectbox("Selecione o Produto Pai", options=lista_produtos_pai)
                    if st.form_submit_button("Adicionar Variação"):
                        if not sku_variacao or not nome_variacao:
                            st.warning("Preencha SKU e Nome.")
                        else:
                            db_gen = get_db()
                            db = next(db_gen)
                            if db.query(Variacao).filter(Variacao.skuVariacao == sku_variacao).first():
                                st.error(f"SKU '{sku_variacao}' já existe!")
                            else:
                                nova_variacao = Variacao(skuVariacao=sku_variacao, nomeVariacao=nome_variacao, idProdutoPai=id_pai_selecionado)
                                db.add(nova_variacao)
                                db.commit()
                                st.success(f"Variação '{nome_variacao}' adicionada!")
                                st.rerun()
    with col2:
        st.subheader("📋 Variações Cadastradas")
        st.dataframe(df_variacoes, use_container_width=True, height=600)

# =============================================================================
# PÁGINA 4: IMPORTAR VENDAS
# =============================================================================
def page_importar_vendas():
    st.header("📥 Importar e Processar Vendas")

    uploaded_file = st.file_uploader("Escolha seu arquivo de vendas da Shopee (.xlsx)", type="xlsx")

    if uploaded_file is not None:
        try:
            df_shopee = pd.read_excel(uploaded_file, dtype=str)
            st.success("Arquivo carregado com sucesso! Pré-visualização:")
            st.dataframe(df_shopee.head())

            if st.button("🚀 Processar Vendas"):
                with st.spinner("Processando..."):
                    db_gen = get_db()
                    db = next(db_gen)
                    
                    ids_existentes = {str(id[0]) for id in db.query(LancamentosVendas.pedidoId).all()}
                    
                    df_shopee.columns = df_shopee.columns.str.strip()
                    mapa_colunas = {
                        "ID do pedido": "pedidoId", "Data de criação do pedido": "dataPedido",
                        "Número de referência SKU": "skuVenda", "Quantidade": "quantidade",
                        "Preço acordado": "receitaBrutaProduto", "Taxa de comissão": "taxaComissao",
                        "Taxa de serviço": "taxaServico", "Taxa de transação": "taxaTransacao",
                        "Valor estimado do frete": "custoFrete",
                        "Cupom do vendedor": "cupomVendedor", "Cupom Shopee": "cupomShopee",
                        "Reembolso Shopee": "reembolsoShopee"
                    }
                    df_vendas = df_shopee.rename(columns=mapa_colunas)
                    
                    ### CORREÇÃO PRINCIPAL AQUI ###
                    # Converte todas as colunas para número ANTES do loop, como no main.py
                    colunas_numericas = ['quantidade', 'receitaBrutaProduto', 'custoFrete', 'taxaComissao', 'taxaServico', 'taxaTransacao', 'cupomVendedor', 'cupomShopee', 'reembolsoShopee']
                    for col in colunas_numericas:
                        if col not in df_vendas.columns:
                            df_vendas[col] = 0 # Adiciona a coluna com 0 se não existir
                        df_vendas[col] = pd.to_numeric(df_vendas[col], errors='coerce').fillna(0)

                    # Calcula os campos agregados
                    df_vendas["taxasMarketplace"] = df_vendas["taxaComissao"] + df_vendas["taxaServico"] + df_vendas["taxaTransacao"]
                    df_vendas["totalCupons"] = df_vendas["cupomVendedor"] + df_vendas["cupomShopee"] + df_vendas["reembolsoShopee"]

                    mapa_custos = {var.skuVariacao: (prod.custoUnidade * prod.quantidadeKit) + prod.custoInsumos
                                   for var in db.query(Variacao).all()
                                   for prod in db.query(ProdutoPai).filter(ProdutoPai.idProdutoPai == var.idProdutoPai).all()}
                    
                    novos_lancamentos, skus_nao_encontrados, vendas_duplicadas = [], [], 0
                    
                    for _, venda in df_vendas.iterrows():
                        pedido_id, sku = str(venda.get('pedidoId')), venda.get('skuVenda')

                        if pedido_id in ids_existentes:
                            vendas_duplicadas += 1
                            continue

                        if sku in mapa_custos:
                            custo_total_kit = mapa_custos[sku]
                            
                            renda_estimada = (venda['receitaBrutaProduto'] * venda['quantidade']) - venda['totalCupons'] - venda['taxasMarketplace']
                            lucro_liquido = renda_estimada - (custo_total_kit * venda['quantidade']) - venda['custoFrete']

                            novos_lancamentos.append(LancamentosVendas(
                                pedidoId=pedido_id,
                                dataPedido=pd.to_datetime(venda['dataPedido']),
                                skuVenda=sku,
                                quantidade=int(venda['quantidade']),
                                receitaBrutaProduto=venda['receitaBrutaProduto'],
                                totalCupons=venda['totalCupons'],
                                custoFrete=venda['custoFrete'],
                                taxasMarketplace=venda['taxasMarketplace'],
                                custoTotalCalculado=custo_total_kit,
                                lucroLiquidoReal=lucro_liquido
                            ))
                        elif sku and sku not in skus_nao_encontrados:
                            skus_nao_encontrados.append(sku)

                    if novos_lancamentos:
                        db.add_all(novos_lancamentos)
                        db.commit()
                        st.success(f"{len(novos_lancamentos)} novas vendas processadas e salvas!")
                    
                    if vendas_duplicadas > 0: st.info(f"{vendas_duplicadas} vendas já existiam e foram ignoradas.")
                    if skus_nao_encontrados: st.warning("SKUs não encontrados:"); st.json(skus_nao_encontrados)
                    if not novos_lancamentos and not skus_nao_encontrados and vendas_duplicadas > 0: st.info("Nenhuma nova venda para processar.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =============================================================================
# PÁGINA 5: DASHBOARD DE ANÁLISE
# =============================================================================
def page_dashboard():
    st.header("📊 Dashboard de Análise de Vendas")

    db_gen = get_db()
    db = next(db_gen)

    vendas = pd.read_sql(db.query(LancamentosVendas).statement, db.bind)
    variacoes = pd.read_sql(db.query(Variacao).statement, db.bind)

    if vendas.empty:
        st.info("Nenhuma venda processada ainda. Importe um arquivo na página 'Importar Vendas'.")
        return

    # Garante que as colunas sejam numéricas para os cálculos
    cols_numericas = ['quantidade', 'receitaBrutaProduto', 'totalCupons', 'custoFrete', 'taxasMarketplace', 'custoTotalCalculado', 'lucroLiquidoReal']
    for col in cols_numericas:
        vendas[col] = pd.to_numeric(vendas[col], errors='coerce').fillna(0)
    
    # --- Filtros ---
    st.sidebar.header("Filtros do Dashboard")
    min_date = vendas['dataPedido'].min().date()
    max_date = vendas['dataPedido'].max().date()
    date_range = st.sidebar.date_input("Selecione o Período", (min_date, max_date), min_value=min_date, max_value=max_date)

    if len(date_range) == 2:
        start_date, end_date = date_range
        vendas_filtradas = vendas[(vendas['dataPedido'].dt.date >= start_date) & (vendas['dataPedido'].dt.date <= end_date)]
    else:
        vendas_filtradas = vendas.copy()

    # --- KPIs Corrigidos ---
    receita_total_bruta = (vendas_filtradas['receitaBrutaProduto'] * vendas_filtradas['quantidade']).sum()
    gasto_total = ((vendas_filtradas['custoTotalCalculado'] * vendas_filtradas['quantidade']) + vendas_filtradas['custoFrete'] + vendas_filtradas['taxasMarketplace'] + vendas_filtradas['totalCupons']).sum()
    lucro_total = vendas_filtradas['lucroLiquidoReal'].sum()
    pedidos_total = vendas_filtradas['pedidoId'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita Bruta", f"R$ {receita_total_bruta:,.2f}")
    col2.metric("Gasto Total", f"R$ {gasto_total:,.2f}", help="Custo dos Produtos + Frete + Taxas + Cupons")
    col3.metric("Lucro Líquido", f"R$ {lucro_total:,.2f}")
    col4.metric("Total de Pedidos", f"{pedidos_total}")

    st.markdown("---")

    # --- NOVA SEÇÃO: DETALHAMENTO DE VENDAS ---
    st.subheader("📄 Detalhamento de Lançamentos (Estilo Main.py)")
    
    df_detalhado = pd.merge(vendas_filtradas, variacoes[['skuVariacao', 'nomeVariacao']], left_on='skuVenda', right_on='skuVariacao', how='left')
    
    df_detalhado['Receita Total Produto'] = df_detalhado['receitaBrutaProduto'] * df_detalhado['quantidade']
    df_detalhado['Gasto Total'] = (df_detalhado['custoTotalCalculado'] * df_detalhado['quantidade']) + df_detalhado['custoFrete']
    df_detalhado['Renda Estimada'] = df_detalhado['Receita Total Produto'] - df_detalhado['totalCupons'] - df_detalhado['taxasMarketplace']
    
    df_final_para_exibir = df_detalhado.rename(columns={
        'dataPedido': 'Data', 'nomeVariacao': 'Variação',
        'totalCupons': 'Total Cupons', 'taxasMarketplace': 'Taxas Marketplace',
        'lucroLiquidoReal': 'Lucro Líquido'
    })

    st.dataframe(
        df_final_para_exibir[[
            'Data', 'Variação', 'Receita Total Produto', 'Total Cupons', 'Taxas Marketplace',
            'Renda Estimada', 'Gasto Total', 'Lucro Líquido'
        ]].style.format({
            'Receita Total Produto': 'R$ {:,.2f}', 'Total Cupons': 'R$ {:,.2f}',
            'Taxas Marketplace': 'R$ {:,.2f}', 'Renda Estimada': 'R$ {:,.2f}',
            'Gasto Total': 'R$ {:,.2f}', 'Lucro Líquido': 'R$ {:,.2f}',
            'Data': '{:%d/%m/%Y %H:%M}'
        }),
        use_container_width=True
    )

# =============================================================================
# NAVEGAÇÃO PRINCIPAL
# =============================================================================
st.sidebar.title("Navegação")
pagina_selecionada = st.sidebar.radio(
    "Selecione uma página:",
    ["Dashboard", "Importar Vendas", "Gerenciar Variações", "Gerenciar Produtos Pai", "Gerenciar Itens"]
)

if pagina_selecionada == "Dashboard":
    page_dashboard()
elif pagina_selecionada == "Importar Vendas":
    page_importar_vendas()
elif pagina_selecionada == "Gerenciar Variações":
    page_gerenciar_variacoes()
elif pagina_selecionada == "Gerenciar Produtos Pai":
    page_gerenciar_produtos_pai()
elif pagina_selecionada == "Gerenciar Itens":
    page_gerenciar_itens()