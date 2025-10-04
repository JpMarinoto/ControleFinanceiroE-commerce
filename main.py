import pandas as pd

def calcular_cmv(sku_variacao, df_composicao, df_itens):
    """Calcula o CMV para um SKU de variação específico."""
    receita_kit = df_composicao[df_composicao['SKU_Variacao'] == sku_variacao]
    if receita_kit.empty:
        return 0
    receita_com_custo = pd.merge(receita_kit, df_itens, on='SKU_Item', how='left')
    receita_com_custo['Custo_Total_Item'] = receita_com_custo['Quantidade_Item'] * receita_com_custo['Custo_Unitario_Aquisicao']
    cmv_final = receita_com_custo['Custo_Total_Item'].sum()
    return cmv_final

# --- Carregamento dos Dados ---
caminho_dados = "dados/"
try:
    df_itens = pd.read_csv(f"{caminho_dados}itens.csv")
    df_produtos_pai = pd.read_csv(f"{caminho_dados}produtos_pai.csv")
    df_variacoes = pd.read_csv(f"{caminho_dados}variacoes.csv")
    df_composicao = pd.read_csv(f"{caminho_dados}composicao_kits.csv")
    df_lojas = pd.read_csv(f"{caminho_dados}lojas.csv")
    
    # NOVO: Carregar o arquivo de vendas a ser processado
    df_vendas = pd.read_csv(f"{caminho_dados}vendas_a_importar.csv")

    print("✅ Arquivos carregados com sucesso!\n")
except FileNotFoundError as e:
    print(f"❌ Erro: Arquivo não encontrado '{e.filename}'. Verifique se o nome e o caminho estão corretos.")
    exit()

# --- Processamento das Vendas ---

print("Iniciando o processamento da planilha de vendas...")

# 1. Calcular o CMV para cada venda na planilha
#    A função .apply() do Pandas é como um "para cada linha, faça isso:"
df_vendas['CMV_Calculado'] = df_vendas['SKU_VENDA'].apply(
    lambda sku: calcular_cmv(sku, df_composicao, df_itens)
)

# 2. Calcular o CMV Total do Pedido (CMV unitário * Quantidade)
df_vendas['CMV_TOTAL_PEDIDO'] = df_vendas['CMV_Calculado'] * df_vendas['QUANTIDADE']

# 3. Calcular a Receita Total do Pedido
df_vendas['RECEITA_TOTAL_PEDIDO'] = df_vendas['PRECO_VENDA_UNITARIO'] * df_vendas['QUANTIDADE']

# 4. Calcular o Lucro Líquido Real por Pedido
df_vendas['LUCRO_LIQUIDO_REAL'] = (
    df_vendas['RECEITA_TOTAL_PEDIDO'] - 
    df_vendas['CMV_TOTAL_PEDIDO'] - 
    df_vendas['CUSTO_FRETE'] - 
    df_vendas['TAXAS_MARKETPLACE']
)

print("✅ Processamento concluído!\n")

# --- Exibição do Resultado Final ---
print("--- Tabela de Lançamentos de Vendas Processada ---")
# Selecionando as colunas mais importantes para exibir no final
colunas_para_exibir = [
    'ID_LOJA', 
    'SKU_VENDA', 
    'QUANTIDADE', 
    'RECEITA_TOTAL_PEDIDO', 
    'CMV_TOTAL_PEDIDO', 
    'CUSTO_FRETE', 
    'TAXAS_MARKETPLACE',
    'LUCRO_LIQUIDO_REAL'
]
print(df_vendas[colunas_para_exibir].round(2))