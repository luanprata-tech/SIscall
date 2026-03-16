from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, scoped_session
import hashlib
import os
import sys
from dotenv import load_dotenv
from app.models import Base, Usuario

# Carregar variáveis de ambiente do arquivo .env
# Quando empacotado com PyInstaller, o .env pode ser incluído dentro da pasta gerada
# (ex: dist\main\.config\.env) — detectamos o ambiente "frozen" e buscamos no
# diretório interno (`sys._MEIPASS`) primeiro. Caso não exista, tentamos o .env
# na raiz do projeto (modo dev) e, se nada for encontrado, deixamos o dotenv
# tentar carregar variáveis de ambiente do ambiente atual.
env_loaded = False
try:
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
        candidate = os.path.join(base, '.config', '.env')
        if os.path.exists(candidate):
            load_dotenv(candidate)
            env_loaded = True
        else:
            # Também verificar se foi incluído diretamente em base
            candidate2 = os.path.join(base, '.env')
            if os.path.exists(candidate2):
                load_dotenv(candidate2)
                env_loaded = True
    if not env_loaded:
        # Ambiente de desenvolvimento: .env na raiz do projeto
        project_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
        if os.path.exists(project_env):
            load_dotenv(project_env)
            env_loaded = True
except Exception:
    pass

# Fallback: tenta carregar qualquer .env no ambiente (sem path) se nada foi carregado
if not env_loaded:
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
        self._ensure_usuario_ativo_column()
        self._criar_dados_iniciais()

    def _ensure_usuario_ativo_column(self):
        """Garante que a coluna `ativo` exista na tabela de usuários.

        Isso permite que atualizações em produção adicionem o campo sem exigir
        migrações externas (útil para instalações com SQLite ou PostgreSQL).
        """
        inspector = inspect(self.engine)
        if 'usuarios' not in inspector.get_table_names():
            return
        cols = [c['name'] for c in inspector.get_columns('usuarios')]
        if 'ativo' in cols:
            return

        # Adiciona a coluna com valor padrão para não quebrar dados existentes.
        with self.engine.begin() as conn:
            if self.engine.dialect.name == 'sqlite':
                conn.execute(text('ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT 1 NOT NULL'))
            elif self.engine.dialect.name == 'postgresql':
                conn.execute(text('ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT TRUE NOT NULL'))
            else:
                conn.execute(text('ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT TRUE'))

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