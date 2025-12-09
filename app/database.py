from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
import hashlib
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
# Este arquivo deve estar na raiz do projeto com credenciais do PostgreSQL
def configurar_ambiente():
    # Verifica se está rodando como executável (Nuitka/PyInstaller)
    if getattr(sys, 'frozen', False):
        # Se for .exe, o .env está na mesma pasta do executável
        # sys.executable retorna o caminho completo do .exe
        pasta_raiz = os.path.dirname(sys.executable)
    else:
        # Se for desenvolvimento (script .py)
        # Estamos em: Projeto/app/database.py
        # __file__ = .../app/database.py
        pasta_atual = os.path.dirname(os.path.abspath(__file__)) # .../app
        pasta_raiz = os.path.dirname(pasta_atual) # .../Projeto (sobe um nível)

    caminho_env = os.path.join(pasta_raiz, '.env')
    
    # Carrega explicitamente desse caminho
    load_dotenv(caminho_env)

# Chama a função antes de tentar conectar
configurar_ambiente()

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    tipo = Column(Integer, nullable=False)  # 0 = Comum, 1 = Admin, 2 = Responsável Setor
    setor = Column(String, nullable=True)
    
    # Flag para forçar troca de senha no próximo login
    trocar_senha = Column(Boolean, default=False) 

    chamados_abertos = relationship("Chamado", foreign_keys="[Chamado.usuario_id]", back_populates="usuario")
    chamados_atendidos = relationship("Chamado", foreign_keys="[Chamado.suporte_id]", back_populates="suporte")

class Chamado(Base):
    __tablename__ = 'chamados'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    suporte_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    data_abertura = Column(String)
    data_inicio_atendimento = Column(String, nullable=True)
    data_fechamento = Column(String, nullable=True)
    
    descricao = Column(String)
    maquina = Column(String, nullable=True)
    
    # Campo para armazenar contas selecionadas (JSON string: "email,sharepoint,confluence,...")
    # Usado quando maquina == "Solicitação de Criação de Conta"
    contas_solicitadas = Column(String, nullable=True)
    
    status = Column(String, default="Aberto")
    diagnostico = Column(String, nullable=True)
    
    # Quando é solicitação de conta, este campo armazena login e senha
    # Exemplo: "admin.user | senha123456"
    solucao = Column(String, nullable=True)

    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="chamados_abertos")
    suporte = relationship("Usuario", foreign_keys=[suporte_id], back_populates="chamados_atendidos")
    
    @property
    def nome_usuario(self):
        return self.usuario.nome if self.usuario else "Desconhecido"
    
    @property
    def setor_usuario(self):
        return self.usuario.setor if self.usuario and self.usuario.setor else "N/A"
        
    @property
    def nome_suporte(self):
        return self.suporte.nome if self.suporte else None

class DatabaseManager:
    def __init__(self, connection_string=None):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            connection_string (str): String de conexão do banco. Se None, usa variáveis de ambiente.
                                     Exemplo: "postgresql://usuario:senha@localhost:5432/siscall"
        
        Se connection_string for None, tenta carregar de variáveis de ambiente:
        - DB_ENGINE: "postgresql" ou "sqlite"
        - DB_USER: Usuário do banco
        - DB_PASSWORD: Senha do banco
        - DB_HOST: Endereço do servidor
        - DB_PORT: Porta do servidor
        - DB_NAME: Nome do banco de dados
        """
        
        # Se nenhuma string for passada, constrói a partir de variáveis de ambiente
        if connection_string is None:
            db_engine = os.getenv("DB_ENGINE")  # Default: PostgreSQL
            
            if db_engine == "postgresql+pg8000":
                # Constrói URL PostgreSQL: postgresql://usuario:senha@host:porta/banco
                db_user = os.getenv("DB_USER")
                db_password = os.getenv("DB_PASSWORD")
                db_host = os.getenv("DB_HOST")
                db_port = os.getenv("DB_PORT")
                db_name = os.getenv("DB_NAME")
                
                connection_string = f"{db_engine}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                print(f"✓ Conectando ao PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")
            
            elif db_engine == "sqlite":
                # Para SQLite local (desenvolvimento)
                db_path = os.getenv("DB_PATH", "sistema_chamados.db")
                connection_string = f"sqlite:///{db_path}"
                print(f"✓ Usando SQLite: {db_path}")
            
            else:
                raise ValueError(f"DB_ENGINE '{db_engine}' não é suportado. Use 'postgresql' ou 'sqlite'.")
        
        # Cria a engine SQLAlchemy
        # echo=False: Não mostra queries SQL no console
        # Para debug, mude para echo=True
        self.engine = create_engine(connection_string, echo=False)
        
        # scoped_session garante que cada thread tenha sua própria sessão
        # Muito importante para aplicações com threads (como interface gráfica)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def setup(self):
        Base.metadata.create_all(self.engine)
        self._criar_dados_iniciais()

    def _criar_dados_iniciais(self):
        session = self.Session()
        if session.query(Usuario).first():
            session.close()
            return

        senha_admin = hashlib.sha256("admin123".encode()).hexdigest()
        senha_user = hashlib.sha256("user123".encode()).hexdigest()
        senha_resp = hashlib.sha256("resp123".encode()).hexdigest()

        admin = Usuario(nome="Administrador", login="admin", senha=senha_admin, tipo=1, setor="GEINFORM")
        user = Usuario(nome="Usuário Teste", login="user", senha=senha_user, tipo=0, setor="GEINFORM")
        resp = Usuario(nome="Responsável Setor", login="resp_setor", senha=senha_resp, tipo=2, setor="GEINFORM")

        session.add(admin)
        session.add(user)
        session.add(resp)
        try:
            session.commit()
            print("Dados iniciais criados.")
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_session(self):
        return self.Session()