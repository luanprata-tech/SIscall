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
            solicitacao = session.get(SolicitacaoConta, solicitacao_id)
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
            solicitacao = session.get(SolicitacaoConta, solicitacao_id)
            if solicitacao:
                solicitacao.status = "Resolvido"
                solicitacao.credenciais_criadas = credenciais
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def marcar_em_espera(self, solicitacao_id: int):
        session = self.session_factory()
        try:
            solicitacao = session.get(SolicitacaoConta, solicitacao_id)
            if solicitacao:
                solicitacao.status = "Em espera"
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def continuar_de_espera(self, solicitacao_id: int):
        session = self.session_factory()
        try:
            solicitacao = session.get(SolicitacaoConta, solicitacao_id)
            if solicitacao:
                solicitacao.status = "Em andamento"
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def tem_solicitacao_ativa_por_usuario(self, usuario_id: int) -> bool:
        """
        Verifica se um usuário já possui uma solicitação de criação de conta
        com status 'Aberto' ou 'Em andamento'.
        """
        session = self.session_factory()
        try:
            solicitacao_ativa = session.query(SolicitacaoConta).filter(
                SolicitacaoConta.usuario_id == usuario_id,
                SolicitacaoConta.status.in_(['Aberto', 'Em andamento'])
            ).first()
            return solicitacao_ativa is not None
        finally:
            session.close()

    def tem_resolvido_pendente_por_usuario(self, usuario_id: int) -> bool:
        """Retorna True se o usuário possuir ao menos uma solicitação com status 'Resolvido' (aguardando confirmação)."""
        session = self.session_factory()
        try:
            count = session.query(SolicitacaoConta).filter(
                SolicitacaoConta.usuario_id == usuario_id,
                SolicitacaoConta.status == 'Resolvido'
            ).count()
            return count > 0
        finally:
            session.close()

    def listar_por_usuario(self, usuario_id: int) -> List[SolicitacaoConta]:
        """Lista todas as solicitações de um usuário, ordenadas pela mais recente."""
        session = self.session_factory()
        try:
            return session.query(SolicitacaoConta).filter(
                SolicitacaoConta.usuario_id == usuario_id
            ).order_by(SolicitacaoConta.data_abertura.desc()).all()
        finally:
            session.close()

    def excluir(self, solicitacao_id: int):
        """Exclui uma solicitação pelo seu ID."""
        session = self.session_factory()
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
        """Muda o status de uma solicitação para 'Finalizado', a pedido do usuário."""
        session = self.session_factory()
        try:
            solicitacao = session.query(SolicitacaoConta).filter_by(id=solicitacao_id).first()
            if solicitacao:
                solicitacao.status = "Finalizado"
                solicitacao.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def listar_todas(self) -> List[SolicitacaoConta]:
        """Lista todas as solicitações, incluindo as finalizadas."""
        session = self.session_factory()
        try:
            return session.query(SolicitacaoConta)\
                .options(joinedload(SolicitacaoConta.usuario), joinedload(SolicitacaoConta.suporte))\
                .order_by(SolicitacaoConta.data_abertura.desc()).all()
        finally:
            session.close()

    def contar_em_aberto(self) -> int:
        """Conta o número de solicitações com status 'Aberto'."""
        session = self.session_factory()
        try:
            return session.query(SolicitacaoConta).filter(
                SolicitacaoConta.status == 'Aberto'
            ).count()
        finally:
            session.close()
