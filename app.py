import streamlit as st
import pandas as pd
from database import SessionLocal, Categoria, ProdutoPai, Variacao, LancamentosVendas
from sqlalchemy.orm import Session
from sqlalchemy import delete

# --- Configuração da Página e CSS ---
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
    if not variacao or not variacao.idProdutoPai: return None
    produto_pai = db.query(ProdutoPai).filter(ProdutoPai.idProdutoPai == variacao.idProdutoPai).first()
    if not produto_pai: return None
    custo_total = (produto_pai.custoUnidade * produto_pai.quantidadeKit) + produto_pai.custoInsumos
    return custo_total

# =============================================================================
# PÁGINA DE CADASTROS GERAIS (CRUD COMPLETO)
# =============================================================================
def page_cadastros_gerais():
    st.header("⚙️ Cadastros Gerais (Categorias, Produtos e SKUs)")
    db_gen = get_db()
    db = next(db_gen)

    tab_cat, tab_prod, tab_var = st.tabs(["🏷️ Categorias", "🧩 Produtos Pai", "🎨 Variações (SKUs)"])

    # --- ABA 1: CATEGORIAS ---
    with tab_cat:
        st.subheader("Gerenciar Categorias de Produtos")
        add_cat_tab, edit_cat_tab, del_cat_tab = st.tabs(["Adicionar", "Editar", "Deletar"])
        with add_cat_tab:
            with st.form("nova_categoria_form", clear_on_submit=True):
                nome_categoria = st.text_input("Nome da Nova Categoria*")
                if st.form_submit_button("Salvar Categoria"):
                    if not nome_categoria:
                        st.warning("O nome da categoria é obrigatório.")
                    else:
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        if db_commit.query(Categoria).filter_by(nome=nome_categoria).first():
                            st.error("Esta categoria já existe.")
                        else:
                            db_commit.add(Categoria(nome=nome_categoria))
                            db_commit.commit()
                            st.success("Categoria adicionada!")
                            st.rerun()
        with edit_cat_tab:
            categorias_lista = db.query(Categoria).all()
            if not categorias_lista:
                st.info("Nenhuma categoria para editar.")
            else:
                categoria_para_editar = st.selectbox("Selecione a Categoria para Editar", options=categorias_lista, format_func=lambda c: c.nome, key="sel_edit_cat")
                with st.form("edit_categoria_form"):
                    novo_nome_cat = st.text_input("Novo Nome", value=categoria_para_editar.nome)
                    if st.form_submit_button("Atualizar Categoria"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        cat_atualizar = db_commit.query(Categoria).filter_by(id=categoria_para_editar.id).first()
                        cat_atualizar.nome = novo_nome_cat
                        db_commit.commit()
                        st.success("Categoria atualizada!")
                        st.rerun()
        with del_cat_tab:
            categorias_lista_del = db.query(Categoria).all()
            if not categorias_lista_del:
                st.info("Nenhuma categoria para deletar.")
            else:
                with st.form("delete_categoria_form"):
                    categoria_para_deletar = st.selectbox("Selecione a Categoria para Deletar", options=categorias_lista_del, format_func=lambda c: c.nome, key="del_cat")
                    confirmacao = st.checkbox(f"Sim, eu confirmo que desejo deletar a categoria '{categoria_para_deletar.nome}'. Esta ação é irreversível.")
                    if st.form_submit_button("Deletar Categoria Selecionada"):
                        if confirmacao:
                            db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                            db_commit.execute(delete(Categoria).where(Categoria.id == categoria_para_deletar.id))
                            db_commit.commit()
                            st.success("Categoria deletada!")
                            st.rerun()
                        else:
                            st.warning("Você precisa confirmar a exclusão marcando a caixa.")

        st.markdown("---")
        categorias_df = pd.read_sql(db.query(Categoria).statement, db.bind).rename(columns={'id': 'ID', 'nome': 'Nome da Categoria'})
        st.dataframe(categorias_df, use_container_width=True)

    # --- ABA 2: PRODUTOS PAI ---
    with tab_prod:
        st.subheader("Gerenciar Produtos Pai")
        add_prod_tab, edit_prod_tab, del_prod_tab = st.tabs(["Adicionar", "Editar", "Deletar"])
        
        with add_prod_tab:
            categorias_dict = {c.id: c.nome for c in db.query(Categoria).all()}
            if not categorias_dict:
                st.warning("Cadastre uma Categoria na primeira aba antes de adicionar um produto.")
            else:
                with st.form("novo_produto_form", clear_on_submit=True):
                    id_produto = st.text_input("ID do Produto Pai*", placeholder="Ex: P001")
                    nome = st.text_input("Nome do Produto Pai*", placeholder="Ex: Kit Pele de Verão")
                    categoria_id_selecionada = st.selectbox("Categoria*", options=list(categorias_dict.keys()), format_func=lambda x: categorias_dict[x])
                    custo_unidade = st.number_input("Custo por Unidade (R$)", min_value=0.0, format="%.2f")
                    quantidade_kit = st.number_input("Quantidade no Kit", min_value=1, step=1)
                    custo_insumos = st.number_input("Custo dos Insumos (R$)", min_value=0.0, format="%.2f")
                    if st.form_submit_button("Salvar Novo Produto"):
                        if not id_produto or not nome: st.warning("Os campos com * são obrigatórios.")
                        else:
                            db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                            if db_commit.query(ProdutoPai).filter_by(idProdutoPai=id_produto).first(): st.error(f"ID '{id_produto}' já existe!")
                            else:
                                novo_produto = ProdutoPai(idProdutoPai=id_produto, nomeProdutoPai=nome, categoria_id=categoria_id_selecionada, custoUnidade=custo_unidade, quantidadeKit=quantidade_kit, custoInsumos=custo_insumos)
                                db_commit.add(novo_produto); db_commit.commit()
                                st.success("Produto Pai adicionado!"); st.rerun()
        with edit_prod_tab:
            produtos_pai_lista = db.query(ProdutoPai).all()
            categorias_dict_edit = {c.id: c.nome for c in db.query(Categoria).all()}
            if not produtos_pai_lista: st.info("Nenhum produto para editar.")
            elif not categorias_dict_edit: st.warning("Cadastre ao menos uma categoria primeiro.")
            else:
                produto_para_editar = st.selectbox("Selecione o Produto para Editar", options=produtos_pai_lista, format_func=lambda p: f"{p.idProdutoPai} - {p.nomeProdutoPai}", key="sel_edit_prod")
                with st.form("edit_produto_form"):
                    novo_nome = st.text_input("Nome do Produto Pai*", value=produto_para_editar.nomeProdutoPai)
                    cat_ids = list(categorias_dict_edit.keys())
                    current_cat_index = cat_ids.index(produto_para_editar.categoria_id) if produto_para_editar.categoria_id in cat_ids else 0
                    nova_cat_id = st.selectbox("Categoria*", options=cat_ids, index=current_cat_index, format_func=lambda x: categorias_dict_edit[x])
                    novo_custo_unidade = st.number_input("Custo por Unidade (R$)", value=produto_para_editar.custoUnidade, format="%.2f")
                    nova_qtd_kit = st.number_input("Quantidade no Kit", value=produto_para_editar.quantidadeKit, min_value=1, step=1)
                    novo_custo_insumos = st.number_input("Custo dos Insumos (R$)", value=produto_para_editar.custoInsumos, format="%.2f")
                    if st.form_submit_button("Atualizar Produto"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        produto_atualizar = db_commit.query(ProdutoPai).filter_by(idProdutoPai=produto_para_editar.idProdutoPai).first()
                        produto_atualizar.nomeProdutoPai = novo_nome; produto_atualizar.categoria_id = nova_cat_id
                        produto_atualizar.custoUnidade = novo_custo_unidade; produto_atualizar.quantidadeKit = nova_qtd_kit
                        produto_atualizar.custoInsumos = novo_custo_insumos
                        db_commit.commit(); st.success("Produto Pai atualizado!"); st.rerun()
        with del_prod_tab:
            produtos_pai_del = db.query(ProdutoPai).all()
            if not produtos_pai_del: st.info("Nenhum produto para deletar.")
            else:
                with st.form("delete_produto_form"):
                    produto_para_deletar = st.selectbox("Selecione o Produto para Deletar", options=produtos_pai_del, format_func=lambda p: f"{p.idProdutoPai} - {p.nomeProdutoPai}", key="del_prod")
                    confirmacao = st.checkbox(f"Sim, eu confirmo que desejo deletar o produto '{produto_para_deletar.nomeProdutoPai}' e todos os seus SKUs associados.")
                    if st.form_submit_button("Deletar Produto e SKUs"):
                        if confirmacao:
                            db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                            db_commit.execute(delete(Variacao).where(Variacao.idProdutoPai == produto_para_deletar.idProdutoPai))
                            db_commit.execute(delete(ProdutoPai).where(ProdutoPai.idProdutoPai == produto_para_deletar.idProdutoPai))
                            db_commit.commit(); st.success("Produto Pai e suas variações deletados!"); st.rerun()
                        else: st.warning("Você precisa confirmar a exclusão marcando a caixa.")

        st.markdown("---")
        produtos_pai_df = pd.read_sql(db.query(ProdutoPai).statement, db.bind).rename(columns={'idProdutoPai': 'ID Produto', 'nomeProdutoPai': 'Nome do Produto', 'custoUnidade': 'Custo Unid. (R$)', 'quantidadeKit': 'Qtd. Kit', 'custoInsumos': 'Insumos (R$)', 'categoria_id': 'ID Categoria'})
        st.dataframe(produtos_pai_df, use_container_width=True)

    # --- ABA 3: VARIAÇÕES (SKUs) ---
    with tab_var:
        st.subheader("Gerenciar Variações (SKUs)")
        add_var_tab, edit_var_tab, del_var_tab = st.tabs(["Adicionar", "Editar", "Deletar"])
        with add_var_tab:
            produtos_pai_lista = {p.idProdutoPai: p.nomeProdutoPai for p in db.query(ProdutoPai).all()}
            if not produtos_pai_lista:
                st.warning("Cadastre um Produto Pai primeiro.")
            else:
                with st.form("nova_variacao_form", clear_on_submit=True):
                    sku_variacao = st.text_input("SKU da Variação*", placeholder="Ex: KV001-AZ")
                    nome_variacao = st.text_input("Nome da Variação*", placeholder="Ex: Kit Pele de Verão - Azul")
                    id_pai_selecionado = st.selectbox("Associar ao Produto Pai*", options=list(produtos_pai_lista.keys()), format_func=lambda x: f"{x} - {produtos_pai_lista[x]}")
                    if st.form_submit_button("Salvar Nova Variação"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        if db_commit.query(Variacao).filter_by(skuVariacao=sku_variacao).first(): st.error(f"SKU '{sku_variacao}' já existe!")
                        else:
                            db_commit.add(Variacao(skuVariacao=sku_variacao, nomeVariacao=nome_variacao, idProdutoPai=id_pai_selecionado))
                            db_commit.commit(); st.success("Variação adicionada!"); st.rerun()
        with edit_var_tab:
            variacoes_lista = db.query(Variacao).all()
            if not variacoes_lista:
                st.info("Nenhuma variação para editar.")
            else:
                variacao_para_editar = st.selectbox("Selecione a Variação para Editar", options=variacoes_lista, format_func=lambda v: f"{v.skuVariacao} - {v.nomeVariacao}", key="sel_edit_var")
                with st.form("edit_variacao_form"):
                    novo_nome_var = st.text_input("Novo Nome da Variação*", value=variacao_para_editar.nomeVariacao)
                    if st.form_submit_button("Atualizar Variação"):
                        db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                        var_atualizar = db_commit.query(Variacao).filter_by(skuVariacao=variacao_para_editar.skuVariacao).first()
                        var_atualizar.nomeVariacao = novo_nome_var
                        db_commit.commit(); st.success("Variação atualizada!"); st.rerun()
        with del_var_tab:
            variacoes_lista_del = db.query(Variacao).all()
            if not variacoes_lista_del:
                st.info("Nenhuma variação para deletar.")
            else:
                with st.form("delete_variacao_form"):
                    variacao_para_deletar = st.selectbox("Selecione a Variação para Deletar", options=variacoes_lista_del, format_func=lambda v: f"{v.skuVariacao} - {v.nomeVariacao}", key="del_var")
                    confirmacao = st.checkbox(f"Sim, eu confirmo que desejo deletar o SKU '{variacao_para_deletar.skuVariacao}'.")
                    if st.form_submit_button("Deletar Variação"):
                        if confirmacao:
                            db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                            db_commit.execute(delete(Variacao).where(Variacao.skuVariacao == variacao_para_deletar.skuVariacao))
                            db_commit.commit(); st.success("Variação deletada!"); st.rerun()
                        else: st.warning("Você precisa confirmar a exclusão marcando a caixa.")

        st.markdown("---")
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind).rename(columns={'skuVariacao': 'SKU', 'nomeVariacao': 'Nome da Variação', 'idProdutoPai': 'ID Produto Pai'})
        st.dataframe(variacoes_df, use_container_width=True)

# =============================================================================
# PÁGINA: IMPORTAR VENDAS (NOVA VERSÃO APRIMORADA)
# =============================================================================
def page_importar_vendas():
    st.header("📥 Importar e Processar Vendas")
    
    # Coloca o uploader de arquivo numa sessão para não desaparecer após o rerun
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_file = st.file_uploader("Escolha seu arquivo de vendas da Shopee (.xlsx)", type="xlsx")

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None:
        try:
            db_gen = get_db(); db = next(db_gen)
            df_shopee = pd.read_excel(st.session_state.uploaded_file, dtype=str)
            df_shopee.columns = df_shopee.columns.str.strip()

            mapa_colunas = {
                "ID do pedido": "pedidoId", "Data de criação do pedido": "dataPedido",
                "Número de referência SKU": "skuVenda", "Quantidade": "quantidade",
                "Preço acordado": "receitaBrutaProduto", "Taxa de comissão": "taxaComissao",
                "Taxa de serviço": "taxaServico", "Taxa de transação": "taxaTransacao",
                "Cupom do vendedor": "cupomVendedor", "Cupom Shopee": "cupomShopee",
                "Reembolso Shopee": "reembolsoShopee"
            }
            
            # Filtra o DataFrame para mostrar apenas as colunas relevantes na pré-visualização
            colunas_relevantes = [col for col in mapa_colunas.keys() if col in df_shopee.columns]
            df_preview = df_shopee[colunas_relevantes]

            st.success("Arquivo carregado! Pré-visualização simplificada:")
            st.dataframe(df_preview.head())

            if st.button("🚀 Processar Vendas"):
                with st.spinner("Processando..."):
                    # A lógica de processamento começa aqui
                    df_vendas = df_shopee.rename(columns=mapa_colunas)
                    colunas_numericas = ['quantidade', 'receitaBrutaProduto', 'taxaComissao', 'taxaServico', 'taxaTransacao', 'cupomVendedor', 'cupomShopee', 'reembolsoShopee']
                    for col in colunas_numericas:
                        if col not in df_vendas.columns: df_vendas[col] = 0
                        df_vendas[col] = pd.to_numeric(df_vendas[col], errors='coerce').fillna(0)

                    df_vendas["taxasMarketplace"] = df_vendas["taxaComissao"] + df_vendas["taxaServico"] + df_vendas["taxaTransacao"]
                    df_vendas["totalCupons"] = df_vendas["cupomVendedor"] + df_vendas["cupomShopee"] + df_vendas["reembolsoShopee"]

                    novos_lancamentos, skus_nao_encontrados, vendas_duplicadas = [], [], 0
                    ids_existentes = {str(id[0]) for id in db.query(LancamentosVendas.pedidoId).all()}

                    for _, venda in df_vendas.iterrows():
                        pedido_id, sku = str(venda.get('pedidoId')), venda.get('skuVenda')
                        if pedido_id in ids_existentes:
                            vendas_duplicadas += 1; continue
                        custo_do_kit = calcular_custo_pelo_produto_pai(db, sku)
                        if custo_do_kit is not None:
                            novos_lancamentos.append(venda)
                        elif sku and sku not in skus_nao_encontrados:
                            skus_nao_encontrados.append(sku)
                    
                    # Salva no banco de dados
                    lancamentos_para_salvar = []
                    pedidos_unicos = set()
                    for venda in novos_lancamentos:
                        custo_do_kit = calcular_custo_pelo_produto_pai(db, venda['skuVenda'])
                        receita_bruta_total = venda['receitaBrutaProduto'] * venda['quantidade']
                        custo_total_produtos = custo_do_kit * venda['quantidade']
                        valor_venda_liquido = receita_bruta_total - venda['totalCupons'] - venda['taxasMarketplace']
                        lucro_liquido = valor_venda_liquido - custo_total_produtos
                        pedidos_unicos.add(venda['pedidoId'])
                        lancamentos_para_salvar.append(LancamentosVendas(pedidoId=venda['pedidoId'], dataPedido=pd.to_datetime(venda['dataPedido']), skuVenda=venda['skuVenda'], quantidade=int(venda['quantidade']), receitaBrutaProduto=venda['receitaBrutaProduto'], totalCupons=venda['totalCupons'], taxasMarketplace=venda['taxasMarketplace'], valorVendaLiquido=valor_venda_liquido, custoTotalCalculado=custo_do_kit, lucroLiquidoReal=lucro_liquido))
                    
                    if lancamentos_para_salvar:
                        db.add_all(lancamentos_para_salvar); db.commit()
                        st.success(f"✅ {len(pedidos_unicos)} novos pedidos ({len(lancamentos_para_salvar)} itens) processados e salvos!")

                    if vendas_duplicadas > 0: st.info(f"ℹ️ {vendas_duplicadas} itens de pedidos já existentes foram ignorados.")
                    
                    # Armazena os SKUs não encontrados no estado da sessão
                    st.session_state.skus_nao_encontrados = skus_nao_encontrados
                    
                    # Força um rerun para mostrar a seção de adicionar SKUs
                    st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

    # --- NOVA SEÇÃO: ADICIONAR SKUS FALTANTES ---
    if 'skus_nao_encontrados' in st.session_state and st.session_state.skus_nao_encontrados:
        skus_faltantes = st.session_state.skus_nao_encontrados
        st.warning(f"ALERTA: {len(skus_faltantes)} SKUs da sua planilha não foram encontrados ou não estão associados a um Produto Pai com custo definido.")
        
        with st.expander("➕ Adicionar SKUs Faltantes Rapidamente"):
            db_gen = get_db(); db = next(db_gen)
            produtos_pai_lista = {p.idProdutoPai: p.nomeProdutoPai for p in db.query(ProdutoPai).all()}

            if not produtos_pai_lista:
                st.error("Nenhum 'Produto Pai' cadastrado. Vá para 'Cadastros Gerais' para criar um antes de adicionar SKUs.")
            else:
                for sku in skus_faltantes:
                    with st.form(f"form_add_{sku}", clear_on_submit=True):
                        st.markdown(f"**Cadastrar SKU:** `{sku}`")
                        nome_variacao = st.text_input("Nome da Variação*", key=f"nome_{sku}")
                        id_pai_selecionado = st.selectbox("Associar ao Produto Pai*", options=list(produtos_pai_lista.keys()), format_func=lambda x: f"{x} - {produtos_pai_lista[x]}", key=f"pai_{sku}")
                        
                        if st.form_submit_button(f"Salvar SKU {sku}"):
                            if not nome_variacao:
                                st.warning("O nome da variação é obrigatório.")
                            else:
                                db_commit_gen = get_db(); db_commit = next(db_commit_gen)
                                if db_commit.query(Variacao).filter_by(skuVariacao=sku).first():
                                    st.error(f"O SKU '{sku}' já existe no banco de dados.")
                                else:
                                    db_commit.add(Variacao(skuVariacao=sku, nomeVariacao=nome_variacao, idProdutoPai=id_pai_selecionado))
                                    db_commit.commit()
                                    st.success(f"SKU '{sku}' salvo com sucesso!")
                                    # Remove o SKU da lista de faltantes e reroda
                                    st.session_state.skus_nao_encontrados.remove(sku)
                                    st.rerun()

# =============================================================================
# PÁGINA: DASHBOARD DE ANÁLISE (Sem alterações)
# =============================================================================
def page_dashboard():
    # ... (O código desta página permanece o mesmo, pois já está otimizado) ...
    st.header("📊 Dashboard de Análise de Vendas")
    db_gen = get_db()
    db = next(db_gen)
    try:
        vendas_df = pd.read_sql(db.query(LancamentosVendas).statement, db.bind)
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind)
        produtos_pai_df = pd.read_sql(db.query(ProdutoPai).statement, db.bind)
        categorias_df = pd.read_sql(db.query(Categoria).statement, db.bind)
    except Exception:
        st.info("Ainda não há dados de vendas. Importe um arquivo na página 'Importar Vendas'.")
        return
    if vendas_df.empty:
        st.info("Nenhuma venda processada ainda. Importe um arquivo na página 'Importar Vendas'.")
        return
    dados_completos = pd.merge(vendas_df, variacoes_df, left_on='skuVenda', right_on='skuVariacao')
    dados_completos = pd.merge(dados_completos, produtos_pai_df, on='idProdutoPai')
    dados_completos = pd.merge(dados_completos, categorias_df, left_on='categoria_id', right_on='id', suffixes=('', '_cat'))
    dados_completos['dataPedido'] = pd.to_datetime(dados_completos['dataPedido'])
    st.sidebar.header("Filtros do Dashboard")
    categorias_dict = {cat.id: cat.nome for _, cat in categorias_df.iterrows()}
    categorias_selecionadas = st.sidebar.multiselect("Filtrar por Categoria", options=list(categorias_dict.keys()), format_func=lambda x: categorias_dict[x])
    min_date = dados_completos['dataPedido'].min().date()
    max_date = dados_completos['dataPedido'].max().date()
    date_range = st.sidebar.date_input("Selecione o Período", (min_date, max_date), min_value=min_date, max_value=max_date)
    vendas_filtradas = dados_completos.copy()
    if categorias_selecionadas: vendas_filtradas = vendas_filtradas[vendas_filtradas['categoria_id'].isin(categorias_selecionadas)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        vendas_filtradas = vendas_filtradas[(vendas_filtradas['dataPedido'].dt.date >= start_date) & (vendas_filtradas['dataPedido'].dt.date <= end_date)]
    if vendas_filtradas.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return
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
    df_detalhado = vendas_filtradas.copy()
    df_detalhado['Receita Bruta Total'] = df_detalhado['receitaBrutaProduto'] * df_detalhado['quantidade']
    df_detalhado['Custo Total Produto'] = df_detalhado['custoTotalCalculado'] * df_detalhado['quantidade']
    df_final_para_exibir = df_detalhado.rename(columns={'dataPedido': 'Data', 'nomeVariacao': 'Variação', 'totalCupons': 'Cupons', 'taxasMarketplace': 'Taxas', 'valorVendaLiquido': 'Venda Líquida', 'lucroLiquidoReal': 'Lucro Líquido'})
    st.dataframe(df_final_para_exibir[['Data', 'Variação', 'Receita Bruta Total', 'Cupons', 'Taxas', 'Venda Líquida', 'Custo Total Produto', 'Lucro Líquido']].style.format({ 'Receita Bruta Total': 'R$ {:,.2f}', 'Cupons': 'R$ {:,.2f}', 'Taxas': 'R$ {:,.2f}', 'Venda Líquida': 'R$ {:,.2f}', 'Custo Total Produto': 'R$ {:,.2f}', 'Lucro Líquido': 'R$ {:,.2f}', 'Data': '{:%d/%m/%Y %H:%M}' }), use_container_width=True)


# =============================================================================
# NAVEGAÇÃO PRINCIPAL
# =============================================================================
st.sidebar.title("Navegação")
# Mapeia os nomes das páginas para as funções
paginas = {
    "Dashboard": page_dashboard,
    "Importar Vendas": page_importar_vendas,
    "Cadastros Gerais": page_cadastros_gerais,
}
pagina_selecionada = st.sidebar.radio("Selecione uma página:", paginas.keys())
paginas[pagina_selecionada]()