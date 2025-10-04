import pandas as pd

# Define o caminho para a pasta de dados
caminho_dados = "dados/"

# Carregar cada arquivo CSV em um DataFrame do Pandas
try:
    df_itens = pd.read_csv(f"{caminho_dados}itens.csv")
    df_produtos_pai = pd.read_csv(f"{caminho_dados}produtos_pai.csv")
    df_variacoes = pd.read_csv(f"{caminho_dados}variacoes.csv")
    df_composicao = pd.read_csv(f"{caminho_dados}composicao_kits.csv")
    df_lojas = pd.read_csv(f"{caminho_dados}lojas.csv")

    print("✅ Arquivos carregados com sucesso!")
    
    print("\n--- Amostra de Itens (Matéria-Prima) ---")
    print(df_itens.head())
    
    print("\n--- Amostra de Variações (SKUs de Venda) ---")
    print(df_variacoes.head())

    print("\n--- Amostra da Composição do Kit 'KV001-AZ' ---")
    print(df_composicao[df_composicao['SKU_Variacao'] == 'KV001-AZ'])

except FileNotFoundError as e:
    print(f"❌ Erro: Arquivo não encontrado. Verifique se o nome e o caminho estão corretos.")
    print(e)