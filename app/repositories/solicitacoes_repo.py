from typing import List, Optional
from sqlalchemy.orm import joinedload
from app.models import Usuario, SolicitacaoConta
from datetime import datetime

class SolicitacaoContaRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def criar(self, usuario_id: int, descricao: str, sistemas: str):
        session = self.session_factory()
        try:
            nova_solicitacao = SolicitacaoConta(
                usuario_id=usuario_id,
                descricao=descricao,
                sistemas_solicitados=sistemas,
                data_abertura=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="Aberto"
            )
            session.add(nova_solicitacao)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def listar_pendentes(self) -> List[SolicitacaoConta]:
        session = self.session_factory()
        try:
            return session.query(SolicitacaoConta)\
                .options(joinedload(SolicitacaoConta.usuario), joinedload(SolicitacaoConta.suporte))\
                .filter(SolicitacaoConta.status != 'Finalizado')\
                .order_by(SolicitacaoConta.data_abertura.desc()).all()
        finally:
            session.close()
    
    def buscar_por_id(self, solicitacao_id: int) -> Optional[SolicitacaoConta]:
        session = self.session_factory()
        try:
            return session.query(SolicitacaoConta)\
                .options(joinedload(SolicitacaoConta.usuario), joinedload(SolicitacaoConta.suporte))\
                .filter(SolicitacaoConta.id == solicitacao_id).first()
        finally:
            session.close()

    def assumir_atendimento(self, solicitacao_id: int, suporte_id: int):
        session = self.session_factory()
        try:
            solicitacao = session.query(SolicitacaoConta).get(solicitacao_id)
            if solicitacao:
                solicitacao.status = "Em andamento"
                solicitacao.suporte_id = suporte_id
                solicitacao.data_inicio_atendimento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def finalizar_atendimento(self, solicitacao_id: int, credenciais: str):
        session = self.session_factory()
        try:
            solicitacao = session.query(SolicitacaoConta).get(solicitacao_id)
            if solicitacao:
                solicitacao.status = "Finalizado"
                solicitacao.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                solicitacao.credenciais_criadas = credenciais
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
