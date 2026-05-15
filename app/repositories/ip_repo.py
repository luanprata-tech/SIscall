from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_

from app.models import EnderecoIP


class IPRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def buscar_por_ip(self, ip_address: str) -> Optional[EnderecoIP]:
        session = self.session_factory()
        try:
            return session.query(EnderecoIP).filter(EnderecoIP.ip_address == ip_address).first()
        finally:
            session.close()

    def listar_todos(self) -> List[EnderecoIP]:
        session = self.session_factory()
        try:
            return session.query(EnderecoIP).order_by(EnderecoIP.id).all()
        finally:
            session.close()

    def buscar_filtrado(self, termo: str = "", status: str = "Todos") -> List[EnderecoIP]:
        session = self.session_factory()
        try:
            query = session.query(EnderecoIP)
            if termo:
                filtro = f"%{termo}%"
                query = query.filter(or_(
                    EnderecoIP.ip_address.like(filtro),
                    EnderecoIP.maquina.like(filtro),
                    EnderecoIP.nome_maquina.like(filtro),
                    EnderecoIP.nome_usuario.like(filtro),
                    EnderecoIP.setor.like(filtro),
                    EnderecoIP.status.like(filtro),
                ))
            if status and status != "Todos":
                query = query.filter(EnderecoIP.status == status)
            return query.order_by(EnderecoIP.id).all()
        finally:
            session.close()

    def salvar(self, ip_address: str, maquina: str, nome_maquina: str, nome_usuario: str, setor: str, status: str):
        session = self.session_factory()
        try:
            registro = session.query(EnderecoIP).filter(EnderecoIP.ip_address == ip_address).first()
            if not registro:
                registro = EnderecoIP(ip_address=ip_address)
                session.add(registro)

            registro.maquina = maquina or None
            registro.nome_maquina = nome_maquina or None
            registro.nome_usuario = nome_usuario or None
            registro.setor = setor or None
            registro.status = status
            registro.data_modificacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            session.commit()
            return registro
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def liberar(self, ip_address: str):
        session = self.session_factory()
        try:
            registro = session.query(EnderecoIP).filter(EnderecoIP.ip_address == ip_address).first()
            if not registro:
                return None

            registro.maquina = None
            registro.nome_maquina = None
            registro.nome_usuario = None
            registro.setor = None
            registro.status = "Livre"
            registro.data_modificacao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            session.commit()
            return registro
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()