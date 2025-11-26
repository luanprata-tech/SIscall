from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, scoped_session
import hashlib

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)
    tipo = Column(Integer, nullable=False)  # 0 = Comum, 1 = Admin
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
    status = Column(String, default="Aberto")
    diagnostico = Column(String, nullable=True)
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
    def __init__(self, connection_string="sqlite:///sistema_chamados.db"):
        self.engine = create_engine(connection_string, echo=False)
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