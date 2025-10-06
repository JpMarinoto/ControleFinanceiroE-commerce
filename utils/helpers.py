# utils/helpers.py
from sqlalchemy.orm import Session
from database import Variacao, ProdutoPai

def calcular_custo_pelo_produto_pai(db: Session, sku_variacao: str):
    """
    Calcula o custo de um SKU buscando os dados financeiros do seu Produto Pai.
    """
    variacao = db.query(Variacao).filter(Variacao.skuVariacao == sku_variacao).first()
    if not variacao or not variacao.idProdutoPai:
        return None

    produto_pai = db.query(ProdutoPai).filter(ProdutoPai.idProdutoPai == variacao.idProdutoPai).first()
    if not produto_pai:
        return None

    custo_total = (produto_pai.custoUnidade * produto_pai.quantidadeKit) + produto_pai.custoInsumos
    return custo_total