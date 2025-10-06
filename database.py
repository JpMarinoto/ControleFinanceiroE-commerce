from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# --- 1. Configuração do Banco de Dados ---
DATABASE_URL = "sqlite:///controle_financeiro.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. Definição dos Modelos (Nossas Tabelas) ---

class Categoria(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False, unique=True)
    produtos_pai = relationship("ProdutoPai", back_populates="categoria")

class ProdutoPai(Base):
    __tablename__ = "produtos_pai"
    idProdutoPai = Column(String, primary_key=True, index=True)
    nomeProdutoPai = Column(String, nullable=False)
    custoUnidade = Column(Float, nullable=False, default=0.0)
    quantidadeKit = Column(Integer, nullable=False, default=1)
    custoInsumos = Column(Float, nullable=False, default=0.0)
    
    # --- NOVO RELACIONAMENTO ---
    categoria_id = Column(Integer, ForeignKey("categorias.id"))
    categoria = relationship("Categoria", back_populates="produtos_pai")
    
    variacoes = relationship("Variacao", back_populates="produto_pai")

class Variacao(Base):
    __tablename__ = "variacoes"
    skuVariacao = Column(String, primary_key=True, index=True)
    nomeVariacao = Column(String, nullable=False)
    idProdutoPai = Column(String, ForeignKey("produtos_pai.idProdutoPai"))
    produto_pai = relationship("ProdutoPai", back_populates="variacoes")

class LancamentosVendas(Base):
    __tablename__ = "lancamentos_vendas"
    
    id = Column(Integer, primary_key=True, index=True)
    pedidoId = Column(String, unique=True, nullable=False, index=True)
    dataPedido = Column(DateTime, nullable=False)
    skuVenda = Column(String, nullable=False, index=True)
    quantidade = Column(Integer, nullable=False)
    receitaBrutaProduto = Column(Float, nullable=False)
    totalCupons = Column(Float, nullable=False)
    taxasMarketplace = Column(Float, nullable=False)
    valorVendaLiquido = Column(Float, nullable=False)
    custoTotalCalculado = Column(Float, nullable=False)
    lucroLiquidoReal = Column(Float, nullable=False)

# --- 3. Função para Criar o Banco de Dados ---
def criar_banco():
    print("Criando/Verificando tabelas no banco de dados...")
    Base.metadata.create_all(bind=engine)
    print("Tabelas prontas.")

if __name__ == "__main__":
    criar_banco()