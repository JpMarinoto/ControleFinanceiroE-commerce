# pages/importar_vendas.py
import streamlit as st
import pandas as pd
from database import SessionLocal, Variacao, LancamentosVendas
from utils.helpers import calcular_custo_pelo_produto_pai

def page_importar_vendas():
    st.header("📥 Importar e Processar Vendas")

    def detectar_plataforma(colunas):
        colunas_set = set(colunas)
        if {'ID do pedido', 'Taxa de comissão', 'Taxa de serviço'}.issubset(colunas_set):
            return "Shopee"
        return None

    if 'uploaded_file' not in st.session_state: st.session_state.uploaded_file = None
    uploaded_file = st.file_uploader("Escolha seu arquivo de vendas (.xlsx)", type="xlsx")

    if uploaded_file: st.session_state.uploaded_file = uploaded_file

    if st.session_state.uploaded_file is not None:
        try:
            db_gen = SessionLocal(); db = db_gen
            df_shopee = pd.read_excel(st.session_state.uploaded_file, dtype=str)
            df_shopee.columns = df_shopee.columns.str.strip()
            
            plataforma_detectada = detectar_plataforma(df_shopee.columns)
            
            col1, col2 = st.columns(2)
            with col1:
                if plataforma_detectada: st.success(f"Plataforma detectada: **{plataforma_detectada}**")
                else: st.warning("Não foi possível detectar a plataforma automaticamente.")
            with col2:
                plataformas_disponiveis = ["Shopee", "Mercado Livre", "Shein", "Outra"]
                indice_plataforma = plataformas_disponiveis.index(plataforma_detectada) if plataforma_detectada in plataformas_disponiveis else 3
                plataforma_selecionada = st.selectbox("Confirme ou selecione a plataforma", options=plataformas_disponiveis, index=indice_plataforma)

            mapa_colunas = {
                "ID do pedido": "pedidoId", "Data de criação do pedido": "dataPedido",
                "Número de referência SKU": "skuVenda", "Quantidade": "quantidade",
                "Preço acordado": "receitaBrutaProduto", "Taxa de comissão": "taxaComissao",
                "Taxa de serviço": "taxaServico", "Taxa de transação": "taxaTransacao",
                "Cupom do vendedor": "cupomVendedor", "Cupom Shopee": "cupomShopee",
                "Reembolso Shopee": "reembolsoShopee"
            }
            
            colunas_relevantes = [col for col in mapa_colunas.keys() if col in df_shopee.columns]
            df_preview = df_shopee[colunas_relevantes]
            st.write("Pré-visualização simplificada:")
            st.dataframe(df_preview.head())

            if st.button("🚀 Processar Vendas"):
                with st.spinner("Processando..."):
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
                        if pedido_id in ids_existentes: vendas_duplicadas += 1; continue
                        custo_do_kit = calcular_custo_pelo_produto_pai(db, sku)
                        if custo_do_kit is not None: novos_lancamentos.append(venda)
                        elif sku and sku not in skus_nao_encontrados: skus_nao_encontrados.append(sku)
                    
                    lancamentos_para_salvar = []
                    pedidos_unicos = set()
                    for venda in novos_lancamentos:
                        custo_do_kit = calcular_custo_pelo_produto_pai(db, venda['skuVenda'])
                        receita_bruta_total = venda['receitaBrutaProduto'] * venda['quantidade']
                        custo_total_produtos = custo_do_kit * venda['quantidade']
                        valor_venda_liquido = receita_bruta_total - venda['totalCupons'] - venda['taxasMarketplace']
                        lucro_liquido = valor_venda_liquido - custo_total_produtos
                        pedidos_unicos.add(venda['pedidoId'])
                        lancamentos_para_salvar.append(LancamentosVendas(pedidoId=venda['pedidoId'], dataPedido=pd.to_datetime(venda['dataPedido']), plataforma=plataforma_selecionada, skuVenda=venda['skuVenda'], quantidade=int(venda['quantidade']), receitaBrutaProduto=venda['receitaBrutaProduto'], totalCupons=venda['totalCupons'], taxasMarketplace=venda['taxasMarketplace'], valorVendaLiquido=valor_venda_liquido, custoTotalCalculado=custo_do_kit, lucroLiquidoReal=lucro_liquido))
                    
                    if lancamentos_para_salvar:
                        db.add_all(lancamentos_para_salvar); db.commit()
                        st.success(f"✅ {len(pedidos_unicos)} novos pedidos ({len(lancamentos_para_salvar)} itens) da plataforma '{plataforma_selecionada}' foram processados e salvos!")
                    if vendas_duplicadas > 0: st.info(f"ℹ️ {vendas_duplicadas} itens de pedidos já existentes foram ignorados.")
                    st.session_state.skus_nao_encontrados = skus_nao_encontrados
                    st.rerun()
        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
        finally:
            db.close()

    # Seção para adicionar SKUs faltantes (sem alterações)
    if 'skus_nao_encontrados' in st.session_state and st.session_state.skus_nao_encontrados:
        # ...
        pass