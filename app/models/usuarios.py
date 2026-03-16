from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base

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

    # Flag para marcar usuário como ativo/inativo (soft delete)
    ativo = Column(Boolean, default=True, nullable=False)

    chamados_abertos = relationship("Chamado", foreign_keys="Chamado.usuario_id", back_populates="usuario")
    chamados_atendidos = relationship("Chamado", foreign_keys="Chamado.suporte_id", back_populates="suporte")
