from sqlalchemy.orm import Session
from app.core.database import SolicitacaoConta  # Importe seu modelo aqui

class SolicitacaoContaRepository:
    def __init__(self, session_factory):
        self.Session = session_factory

    def tem_solicitacao_ativa_por_usuario(self, usuario_id: int) -> bool:
        """
        Verifica se um usuário já possui uma solicitação de criação de conta
        com status 'Aberto' ou 'Em andamento'.
        """
        session = self.Session()
        try:
            solicitacao_ativa = session.query(SolicitacaoConta).filter(
                SolicitacaoConta.usuario_id == usuario_id,
                SolicitacaoConta.status.in_(['Aberto', 'Em andamento'])
            ).first()
            return solicitacao_ativa is not None
        finally:
            session.close()

    def listar_por_usuario(self, usuario_id: int):
        """Lista todas as solicitações de um usuário, ordenadas pela mais recente."""
        session = self.Session()
        try:
            return session.query(SolicitacaoConta).filter(
                SolicitacaoConta.usuario_id == usuario_id
            ).order_by(SolicitacaoConta.data_abertura.desc()).all()
        finally:
            session.close()

    def excluir(self, solicitacao_id: int):
        """Exclui uma solicitação pelo seu ID."""
        session = self.Session()
        try:
            solicitacao = session.query(SolicitacaoConta).filter_by(id=solicitacao_id).first()
            if solicitacao:
                session.delete(solicitacao)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def fechar_solicitacao(self, solicitacao_id: int):
        """Muda o status de uma solicitação para 'Finalizado'."""
        session = self.Session()
        try:
            solicitacao = session.query(SolicitacaoConta).filter_by(id=solicitacao_id).first()
            if solicitacao:
                solicitacao.status = "Finalizado"
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
