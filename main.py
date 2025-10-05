import pandas as pd

def calcularCmv(skuVariacao, dfComposicao, dfItens):
    """Calcula o CMV para um SKU de variação específico."""
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
    print("✅ Arquivos de base (itens, composição, custos adic.) carregados!")
except FileNotFoundError as e:
    print(f"❌ Erro Crítico: Arquivo base '{e.filename}' não encontrado.")
    exit()

# --- 2. Carregamento e Limpeza do Arquivo de Vendas ---
arquivoVendasShopee = "shopee_vendas.csv.xlsx - orders.csv" 
try:
    dfShopee = pd.read_csv(f"{caminhoDados}{arquivoVendasShopee}", dtype=str)
    print(f"✅ Arquivo '{arquivoVendasShopee}' carregado com sucesso!")
except FileNotFoundError:
    print(f"❌ Erro Crítico: Arquivo de vendas '{arquivoVendasShopee}' não encontrado.")
    exit()

# Mapeamento expandido para a nova lógica
mapaColunas = {
    "Data de criação do pedido": "dataPedido",
    "Número de referência SKU": "skuVenda",
    "Quantidade": "quantidade",
    "Valor da transação do pedido": "totalPagoComprador", # NOVO PONTO DE PARTIDA
    "Custo de Envio Real": "custoFrete",             # NOVO CUSTO ESSENCIAL
    "Taxa de comissão": "taxaComissao",
    "Taxa de serviço": "taxaServico",
    "Taxa de transação": "taxaTransacao",
    "Total do Vendedor do Desconto do Produto": "descontoVendedor",
    "Reembolso da Shopee": "reembolsoShopee"
}
dfVendas = dfShopee.rename(columns=mapaColunas)

# Lógica robusta para garantir que colunas numéricas existam
colunasNumericasEsperadas = [
    'quantidade', 'totalPagoComprador', 'custoFrete', 'taxaComissao', 'taxaServico', 
    'taxaTransacao', 'descontoVendedor', 'reembolsoShopee'
]
for col in colunasNumericasEsperadas:
    if col not in dfVendas.columns:
        dfVendas[col] = 0
    dfVendas[col] = pd.to_numeric(dfVendas[col], errors='coerce').fillna(0)

# Consolidação de custos e informações
dfVendas["taxasMarketplace"] = dfVendas["taxaComissao"] + dfVendas["taxaServico"] + dfVendas["taxaTransacao"]
dfVendas["totalCupons"] = dfVendas["descontoVendedor"] + dfVendas["reembolsoShopee"]
print("✅ Limpeza e mapeamento do arquivo de vendas concluídos.")


# --- 3. Processamento e Cálculo do Lucro (Lógica Aprimorada) ---
print("⚙️  Iniciando processamento e cálculo de lucro...")
dfVendas['cmvCalculado'] = dfVendas['skuVenda'].apply(lambda sku: calcularCmv(sku, dfComposicao, dfItens))
dfVendasSemCmv = dfVendas[dfVendas['cmvCalculado'].isnull()]
dfVendas = dfVendas.dropna(subset=['cmvCalculado'])

# Juntando os custos adicionais (custo fixo, marketing, etc.)
for col in ['custoFixo', 'custoMarketing', 'custoImposto', 'custoEmbalagem']:
    if col in dfCustosAdicionais.columns:
        dfCustosAdicionais[col] = pd.to_numeric(dfCustosAdicionais[col], errors='coerce').fillna(0)
dfVendas = pd.merge(dfVendas, dfCustosAdicionais, left_on='skuVenda', right_on='skuVariacao', how='left')
for col in ['custoFixo', 'custoMarketing', 'custoImposto', 'custoEmbalagem']:
    if col not in dfVendas.columns:
        dfVendas[col] = 0
    dfVendas[col].fillna(0, inplace=True)


# Totalizando custos por pedido
dfVendas['cmvTotalPedido'] = dfVendas['cmvCalculado'] * dfVendas['quantidade']
dfVendas['custosAdicionaisTotal'] = (dfVendas['custoFixo'] + dfVendas['custoMarketing'] + dfVendas['custoImposto'] + dfVendas['custoEmbalagem']) * dfVendas['quantidade']

# FÓRMULA DE LUCRO LÍQUIDO FINAL (Top-Down)
dfVendas['lucroLiquidoReal'] = (
    dfVendas['totalPagoComprador'] -
    dfVendas['custoFrete'] -
    dfVendas['taxasMarketplace'] -
    dfVendas['cmvTotalPedido'] -
    dfVendas['custosAdicionaisTotal']
)
print("✅ Processamento finalizado.")


# --- 4. Exibição dos Resultados ---
print("\n--- 📈 RELATÓRIO DE LUCRO LÍQUIDO FINAL (v4.0) ---")
colunasParaExibir = [
    'dataPedido', 'skuVenda', 'totalPagoComprador', 'totalCupons', 'custoFrete',
    'taxasMarketplace', 'cmvTotalPedido', 'custosAdicionaisTotal', 'lucroLiquidoReal'
]
print(dfVendas[colunasParaExibir].round(2))

if not dfVendasSemCmv.empty:
    print("\n--- ⚠️ AVISO: SKUs NÃO ENCONTRADOS NO CADASTRO DE COMPOSIÇÃO ---")
    print(dfVendasSemCmv['skuVenda'].unique())