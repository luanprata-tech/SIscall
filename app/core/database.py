from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import hashlib
import os
from dotenv import load_dotenv
from app.models import Base, Usuario

# Carregar variáveis de ambiente do arquivo .env
# Este arquivo deve estar na raiz do projeto com credenciais do PostgreSQL
load_dotenv()

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
            db_engine = os.getenv("DB_ENGINE", "postgresql")  # Default: PostgreSQL
            
            if db_engine == "postgresql":
                # Constrói URL PostgreSQL: postgresql://usuario:senha@host:porta/banco
                db_user = os.getenv("DB_USER", "postgres")
                db_password = os.getenv("DB_PASSWORD", "postgres")
                db_host = os.getenv("DB_HOST", "localhost")
                db_port = os.getenv("DB_PORT", "5432")
                db_name = os.getenv("DB_NAME", "siscall")
                
                connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                print(f"✓ Conectando ao PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")
            
            elif db_engine == "mysql":
                db_user = os.getenv("DB_USER")
                db_password = os.getenv("DB_PASSWORD")
                db_host = os.getenv("DB_HOST")
                db_port = os.getenv("DB_PORT", "3306")
                db_name = os.getenv("DB_NAME")
                # String de conexão para MySQL usando pymysql
                connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

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

        admin = Usuario(nome="Administrador", login="admin", senha=senha_admin, tipo=1, setor="TI - Infraestrutura")
        user = Usuario(nome="Usuário Teste", login="user", senha=senha_user, tipo=0, setor="Comercial")

        session.add(admin)
        session.add(user)
        try:
            session.commit()
            print("Dados iniciais criados.")
        except Exception:
            session.rollback()
        finally:
            session.close()

    def get_session(self):
        return self.Session()