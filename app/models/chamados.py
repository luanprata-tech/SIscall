from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from app.models.base import Base

class Chamado(Base):
    __tablename__ = 'chamados'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'))
    suporte_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)
    
    data_abertura = Column(String)
    data_inicio_atendimento = Column(String, nullable=True)
    data_fechamento = Column(String, nullable=True)
    
    descricao = Column(String)
    maquina = Column(String)
    setor_origem = Column(String, nullable=True)
    imagem_data = Column(LargeBinary, nullable=True) # Armazena os bytes da imagem
    imagem_filename = Column(String, nullable=True) # Armazena o nome original do arquivo
    
    status = Column(String, default="Aberto")
    diagnostico = Column(String, nullable=True)
    observacao_confirmacao = Column(String, nullable=True)
    
    # Quando é solicitação de conta, este campo armazena a resposta do atendimento
    solucao = Column(String, nullable=True)

    usuario = relationship("Usuario", foreign_keys=[usuario_id], back_populates="chamados_abertos")
    suporte = relationship("Usuario", foreign_keys=[suporte_id], back_populates="chamados_atendidos")
    
    @property
    def nome_usuario(self):
        return self.usuario.nome if self.usuario else "Desconhecido"
    
    @property
    def setor_usuario(self):
        if self.setor_origem:
            return self.setor_origem
        return self.usuario.setor if self.usuario and self.usuario.setor else "N/A"
        
    @property
    def nome_suporte(self):
        return self.suporte.nome if self.suporte else None