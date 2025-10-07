# pages/cadastrosGerais.py
import streamlit as st
import pandas as pd
from database import SessionLocal, Categoria, ProdutoPai, Variacao
from sqlalchemy import delete

def page_cadastros_gerais():
    st.header("⚙️ Cadastros Gerais (Categorias, Produtos e SKUs)")
    # Usar 'with' garante que a sessão do banco de dados seja fechada corretamente
    with SessionLocal() as db:

        tab_cat, tab_prod, tab_var = st.tabs(["🏷️ Categorias", "🧩 Produtos Pai", "🎨 Variações (SKUs)"])

        # --- ABA 1: CATEGORIAS ---
        with tab_cat:
            st.subheader("Gerenciar Categorias de Produtos")
            add_cat_tab, edit_cat_tab, del_cat_tab = st.tabs(["Adicionar", "Editar", "Deletar"])
            with add_cat_tab:
                with st.form("nova_categoria_form", clear_on_submit=True):
                    nome_categoria = st.text_input("Nome da Nova Categoria*")
                    if st.form_submit_button("Salvar Categoria"):
                        # VERIFICAÇÃO ADICIONADA
                        if not nome_categoria or not nome_categoria.strip():
                            st.warning("O nome da categoria é obrigatório.")
                        else:
                            if db.query(Categoria).filter_by(nome=nome_categoria.strip()).first():
                                st.error("Esta categoria já existe.")
                            else:
                                db.add(Categoria(nome=nome_categoria.strip()))
                                db.commit()
                                st.success("Categoria adicionada!")
                                st.rerun()
            with edit_cat_tab:
                categorias_lista = db.query(Categoria).all()
                if not categorias_lista:
                    st.info("Nenhuma categoria para editar.")
                else:
                    categoria_para_editar = st.selectbox("Selecione a Categoria para Editar", options=categorias_lista, format_func=lambda c: c.nome, key="sel_edit_cat")
                    with st.form("edit_categoria_form"):
                        novo_nome_cat = st.text_input("Novo Nome*", value=categoria_para_editar.nome)
                        if st.form_submit_button("Atualizar Categoria"):
                            # VERIFICAÇÃO ADICIONADA
                            if not novo_nome_cat or not novo_nome_cat.strip():
                                st.warning("O nome da categoria é obrigatório.")
                            else:
                                cat_atualizar = db.query(Categoria).filter_by(id=categoria_para_editar.id).first()
                                cat_atualizar.nome = novo_nome_cat.strip()
                                db.commit()
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
                                db.execute(delete(Categoria).where(Categoria.id == categoria_para_deletar.id))
                                db.commit()
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
                        col1, col2 = st.columns(2)
                        with col1:
                            id_produto = st.text_input("ID do Produto Pai*", placeholder="Ex: CABE-RIPA-7UNI")
                            categoria_id_selecionada = st.selectbox("Categoria*", options=list(categorias_dict.keys()), format_func=lambda x: categorias_dict[x])
                            quantidade_kit = st.number_input("Quantidade no Kit", min_value=1, step=1, value=1)
                        with col2:
                            nome = st.text_input("Nome do Produto Pai*", placeholder="Ex: Cabeceira Ripa 7 uni")
                            custo_unidade = st.number_input("Custo por Unidade (R$)", min_value=0.0, format="%.2f")
                            custo_insumos = st.number_input("Custo dos Insumos (R$)", min_value=0.0, format="%.2f")
                        
                        if st.form_submit_button("Salvar Novo Produto"):
                            # VERIFICAÇÃO ADICIONADA
                            if not id_produto.strip() or not nome.strip():
                                st.warning("Os campos com * são obrigatórios.")
                            else:
                                if db.query(ProdutoPai).filter_by(idProdutoPai=id_produto.strip()).first():
                                    st.error(f"ID '{id_produto}' já existe!")
                                else:
                                    novo_produto = ProdutoPai(
                                        idProdutoPai=id_produto.strip(), nomeProdutoPai=nome.strip(),
                                        categoria_id=categoria_id_selecionada,
                                        custoUnidade=custo_unidade, quantidadeKit=quantidade_kit,
                                        custoInsumos=custo_insumos
                                    )
                                    db.add(novo_produto)
                                    db.commit()
                                    st.success("Produto Pai adicionado!")
                                    st.rerun()
            with edit_prod_tab:
                produtos_pai_lista = db.query(ProdutoPai).all()
                categorias_dict_edit = {c.id: c.nome for c in db.query(Categoria).all()}
                if not produtos_pai_lista:
                    st.info("Nenhum produto para editar.")
                elif not categorias_dict_edit:
                    st.warning("Cadastre ao menos uma categoria primeiro.")
                else:
                    produto_para_editar = st.selectbox("Selecione o Produto para Editar", options=produtos_pai_lista, format_func=lambda p: f"{p.idProdutoPai} - {p.nomeProdutoPai}", key="sel_edit_prod")
                    with st.form("edit_produto_form"):
                        st.write(f"**Editando:** `{produto_para_editar.idProdutoPai}`")
                        col1, col2 = st.columns(2)
                        with col1:
                            novo_nome = st.text_input("Nome do Produto Pai*", value=produto_para_editar.nomeProdutoPai)
                            cat_ids = list(categorias_dict_edit.keys())
                            current_cat_index = cat_ids.index(produto_para_editar.categoria_id) if produto_para_editar.categoria_id in cat_ids else 0
                            nova_cat_id = st.selectbox("Categoria*", options=cat_ids, index=current_cat_index, format_func=lambda x: categorias_dict_edit[x])
                            nova_qtd_kit = st.number_input("Quantidade no Kit", value=produto_para_editar.quantidadeKit, min_value=1, step=1)
                        with col2:
                            novo_custo_unidade = st.number_input("Custo por Unidade (R$)", value=produto_para_editar.custoUnidade, format="%.2f")
                            novo_custo_insumos = st.number_input("Custo dos Insumos (R$)", value=produto_para_editar.custoInsumos, format="%.2f")

                        if st.form_submit_button("Atualizar Produto"):
                            # VERIFICAÇÃO ADICIONADA
                            if not novo_nome.strip():
                                st.warning("O nome do produto é obrigatório.")
                            else:
                                produto_atualizar = db.query(ProdutoPai).filter_by(idProdutoPai=produto_para_editar.idProdutoPai).first()
                                produto_atualizar.nomeProdutoPai = novo_nome.strip()
                                produto_atualizar.categoria_id = nova_cat_id
                                produto_atualizar.custoUnidade = novo_custo_unidade
                                produto_atualizar.quantidadeKit = nova_qtd_kit
                                produto_atualizar.custoInsumos = novo_custo_insumos
                                db.commit()
                                st.success("Produto Pai atualizado!")
                                st.rerun()
            with del_prod_tab:
                produtos_pai_del = db.query(ProdutoPai).all()
                if not produtos_pai_del:
                    st.info("Nenhum produto para deletar.")
                else:
                    with st.form("delete_produto_form"):
                        produto_para_deletar = st.selectbox("Selecione o Produto para Deletar", options=produtos_pai_del, format_func=lambda p: f"{p.idProdutoPai} - {p.nomeProdutoPai}", key="del_prod")
                        confirmacao = st.checkbox(f"Sim, eu confirmo que desejo deletar o produto '{produto_para_deletar.nomeProdutoPai}' e todos os seus SKUs associados.")
                        if st.form_submit_button("Deletar Produto e SKUs"):
                            if confirmacao:
                                db.execute(delete(Variacao).where(Variacao.idProdutoPai == produto_para_deletar.idProdutoPai))
                                db.execute(delete(ProdutoPai).where(ProdutoPai.idProdutoPai == produto_para_deletar.idProdutoPai))
                                db.commit()
                                st.success("Produto Pai e suas variações deletados!")
                                st.rerun()
                            else:
                                st.warning("Você precisa confirmar a exclusão marcando a caixa.")

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
                    sku_variacao = st.text_input("SKU da Variação*", placeholder="Ex: RIPADO-FREIJO-100UNI")
                    nome_variacao = st.text_input("Nome da Variação*", placeholder="Ex: Ripado Freijó 100 unidades")
                    id_pai_selecionado = st.selectbox("Associar ao Produto Pai*", options=list(produtos_pai_lista.keys()), format_func=lambda x: f"{x} - {produtos_pai_lista[x]}")
                    if st.form_submit_button("Salvar Nova Variação"):
                        # VERIFICAÇÃO ADICIONADA
                        if not sku_variacao.strip() or not nome_variacao.strip():
                            st.warning("Os campos com * são obrigatórios.")
                        else:
                            if db.query(Variacao).filter_by(skuVariacao=sku_variacao.strip()).first():
                                st.error(f"SKU '{sku_variacao}' já existe!")
                            else:
                                db.add(Variacao(skuVariacao=sku_variacao.strip(), nomeVariacao=nome_variacao.strip(), idProdutoPai=id_pai_selecionado))
                                db.commit()
                                st.success("Variação adicionada!")
                                st.rerun()
        with edit_var_tab:
            variacoes_lista = db.query(Variacao).all()
            if not variacoes_lista:
                st.info("Nenhuma variação para editar.")
            else:
                variacao_para_editar = st.selectbox("Selecione a Variação para Editar", options=variacoes_lista, format_func=lambda v: f"{v.skuVariacao} - {v.nomeVariacao}", key="sel_edit_var")
                with st.form("edit_variacao_form"):
                    novo_nome_var = st.text_input("Novo Nome da Variação*", value=variacao_para_editar.nomeVariacao)
                    if st.form_submit_button("Atualizar Variação"):
                        # VERIFICAÇÃO ADICIONADA
                        if not novo_nome_var.strip():
                            st.warning("O nome da variação é obrigatório.")
                        else:
                            var_atualizar = db.query(Variacao).filter_by(skuVariacao=variacao_para_editar.skuVariacao).first()
                            var_atualizar.nomeVariacao = novo_nome_var.strip()
                            db.commit()
                            st.success("Variação atualizada!")
                            st.rerun()
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
                            db.execute(delete(Variacao).where(Variacao.skuVariacao == variacao_para_deletar.skuVariacao))
                            db.commit()
                            st.success("Variação deletada!")
                            st.rerun()
                        else:
                            st.warning("Você precisa confirmar a exclusão marcando a caixa.")

        st.markdown("---")
        variacoes_df = pd.read_sql(db.query(Variacao).statement, db.bind).rename(columns={'skuVariacao': 'SKU', 'nomeVariacao': 'Nome da Variação', 'idProdutoPai': 'ID Produto Pai'})
        st.dataframe(variacoes_df, use_container_width=True)
    
    db.close()