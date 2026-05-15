from sqlalchemy import Column, Integer, String
from app.models.base import Base


class EnderecoIP(Base):
    __tablename__ = 'enderecos_ip'

    id = Column(Integer, primary_key=True)
    ip_address = Column(String, unique=True, nullable=False, index=True)
    maquina = Column(String, nullable=True)
    nome_maquina = Column(String, nullable=True)
    nome_usuario = Column(String, nullable=True)
    setor = Column(String, nullable=True)
    status = Column(String, nullable=False, default="Livre")
    data_modificacao = Column(String, nullable=True)