import pandas as pd

# Garante que todas as colunas da tabela sejam exibidas no terminal
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def calcularCmv(skuVariacao, dfComposicao, dfItens):
    """Calcula o CMV (Custo da Matéria Prima) para um SKU."""
    skuVariacao = str(skuVariacao)
    receitaKit = dfComposicao[dfComposicao['skuVariacao'] == skuVariacao]
    if receitaKit.empty: return None
    receitaComCusto = pd.merge(receitaKit, dfItens, on='skuItem', how='left')
    if receitaComCusto['custoUnitarioAquisicao'].isnull().any(): return None
    receitaComCusto['custoTotalItem'] = receitaComCusto['quantidadeItem'] * receitaComCusto['custoUnitarioAquisicao']
    cmvFinal = receitaComCusto['custoTotalItem'].sum()
    return cmvFinal

# --- 1. Carregamento dos Dados Base ---
caminhoDados = "dados/"
try:
    dfItens = pd.read_csv(f"{caminhoDados}itens.csv", dtype=str)
    dfComposicao = pd.read_csv(f"{caminhoDados}composicao_kits.csv", dtype=str)
    dfCustosAdicionais = pd.read_csv(f"{caminhoDados}custos_adicionais.csv", dtype=str)
    
    dfItens['custoUnitarioAquisicao'] = pd.to_numeric(dfItens['custoUnitarioAquisicao'])
    dfComposicao['quantidadeItem'] = pd.to_numeric(dfComposicao['quantidadeItem'])
    print("✅ Arquivos de base carregados!")
except FileNotFoundError as e:
    print(f"❌ Erro Crítico: Arquivo base '{e.filename}' não encontrado.")
    exit()

# --- 2. Carregamento e Limpeza do Arquivo de Vendas ---
arquivoVendasShopee = "Order.toship.20250905_20251005.xlsx" 
try:
    dfShopee = pd.read_excel(f"{caminhoDados}{arquivoVendasShopee}", dtype=str)
    print(f"✅ Arquivo '{arquivoVendasShopee}' carregado com sucesso!")
except FileNotFoundError:
    print(f"❌ Erro Crítico: Arquivo de vendas '{arquivoVendasShopee}' não encontrado.")
    exit()

dfShopee.columns = dfShopee.columns.str.strip()
mapaColunas = {
    "Data de criação do pedido": "dataPedido", "Número de referência SKU": "skuVenda",
    "Quantidade": "quantidade", "Preço acordado": "receitaBrutaProduto",
    "Valor estimado do frete": "custoFrete", "Taxa de comissão": "taxaComissao",
    "Taxa de serviço": "taxaServico", "Taxa de transação": "taxaTransacao",
    "Cupom do vendedor": "cupomVendedor", "Cupom Shopee": "cupomShopee",
    "Reembolso Shopee": "reembolsoShopee"
}
dfVendas = dfShopee.rename(columns=mapaColunas)

colunasNumericasEsperadas = ['quantidade', 'receitaBrutaProduto', 'custoFrete', 'taxaComissao', 'taxaServico', 'taxaTransacao', 'cupomVendedor', 'cupomShopee', 'reembolsoShopee']
for col in colunasNumericasEsperadas:
    if col not in dfVendas.columns: dfVendas[col] = 0
    dfVendas[col] = pd.to_numeric(dfVendas[col], errors='coerce').fillna(0)

dfVendas["taxasMarketplace"] = dfVendas["taxaComissao"] + dfVendas["taxaServico"] + dfVendas["taxaTransacao"]
dfVendas["totalCupons"] = dfVendas["cupomVendedor"] + dfVendas["cupomShopee"] + dfVendas["reembolsoShopee"]
print("✅ Limpeza e mapeamento do arquivo de vendas concluídos.")

# --- 3. Processamento e Cálculo do Lucro ---
print("⚙️  Iniciando processamento e cálculo de lucro...")
dfVendas['cmvCalculado'] = dfVendas['skuVenda'].apply(lambda sku: calcularCmv(sku, dfComposicao, dfItens))
dfVendasSemCmv = dfVendas[dfVendas['cmvCalculado'].isnull()]
dfVendas = dfVendas.dropna(subset=['cmvCalculado'])

colunasCustosAdicionais = ['embalagem', 'etiqueta', 'fita', 'maoDeObra', 'impostoNfe', 'outrosCustos']
for col in colunasCustosAdicionais:
    if col in dfCustosAdicionais.columns:
        dfCustosAdicionais[col] = pd.to_numeric(dfCustosAdicionais[col], errors='coerce').fillna(0)
dfVendas = pd.merge(dfVendas, dfCustosAdicionais, left_on='skuVenda', right_on='skuVariacao', how='left')
dfVendas[colunasCustosAdicionais] = dfVendas[colunasCustosAdicionais].fillna(0)

# Totalizando valores e custos por pedido
dfVendas['receitaTotalProduto'] = dfVendas['receitaBrutaProduto'] * dfVendas['quantidade']
dfVendas['cmvTotalPedido'] = dfVendas['cmvCalculado'] * dfVendas['quantidade']
dfVendas['custosAdicionaisTotal'] = (
    dfVendas['embalagem'] + dfVendas['etiqueta'] + dfVendas['fita'] + 
    dfVendas['maoDeObra'] + dfVendas['impostoNfe'] + dfVendas['outrosCustos']
) * dfVendas['quantidade']
dfVendas['gastoTotal'] = dfVendas['cmvTotalPedido'] + dfVendas['custosAdicionaisTotal']
dfVendas['rendaEstimada'] = (
    dfVendas['receitaTotalProduto'] - 
    dfVendas['totalCupons'] - 
    dfVendas['taxasMarketplace']
)

### MUDANÇA PRINCIPAL AQUI ###
# FÓRMULA FINAL DE LUCRO LÍQUIDO, conforme seu pedido
dfVendas['lucroLiquidoReal'] = (
    dfVendas['rendaEstimada'] -
    dfVendas['gastoTotal']
)
print("✅ Processamento finalizado.")

# --- 4. Exibição dos Resultados ---
print("\n--- 📈 RELATÓRIO DE LUCRO LÍQUIDO (v5.5 - Fórmula Simplificada) ---")
colunasParaExibir = [
    'dataPedido', 
    'skuVenda', 
    'receitaTotalProduto', 
    'totalCupons',
    'taxasMarketplace',
    'rendaEstimada',
    'gastoTotal',
    'lucroLiquidoReal'
]
print(dfVendas[colunasParaExibir].round(2))

if not dfVendasSemCmv.empty:
    print("\n--- ⚠️ AVISO: SKUs NÃO ENCONTRADOS NO CADASTRO DE COMPOSIÇÃO ---")
    print("Os seguintes SKUs da sua planilha de vendas não foram encontrados:")
    print(dfVendasSemCmv['skuVenda'].unique())