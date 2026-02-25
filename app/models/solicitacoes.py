from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class SolicitacaoConta(Base):
    __tablename__ = 'solicitacoes_conta'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    suporte_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    data_abertura = Column(String, nullable=False)
    data_inicio_atendimento = Column(String, nullable=True)
    data_fechamento = Column(String, nullable=True)
    
    descricao = Column(String, nullable=True)
    
    sistemas_solicitados = Column(String, nullable=False)
    
    status = Column(String, default="Aberto", nullable=False)
    
    credenciais_criadas = Column(String, nullable=True)

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    suporte = relationship("Usuario", foreign_keys=[suporte_id])

    @property
    def nome_usuario(self):
        return self.usuario.nome if self.usuario else "Desconhecido"
    
    @property
    def setor_usuario(self):
        return self.usuario.setor if self.usuario and self.usuario.setor else "N/A"
        
    @property
    def nome_suporte(self):
        return self.suporte.nome if self.suporte else None