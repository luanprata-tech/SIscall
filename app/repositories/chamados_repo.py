from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, case, desc
from sqlalchemy.exc import IntegrityError
from app.models import Usuario, Chamado
from datetime import datetime



class ChamadoRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def criar(self, usuario_id: int, descricao: str, maquina: str):
        session = self.session_factory()
        try:
            novo_chamado = Chamado(
                usuario_id=usuario_id,
                descricao=descricao,
                maquina=maquina,
                data_abertura=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                status="Aberto"
            )
            session.add(novo_chamado)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def assumir_atendimento(self, chamado_id: int, suporte_id: int):
        session = self.session_factory()
        try:
            chamado = session.query(Chamado).get(chamado_id)
            if chamado:
                chamado.status = "Em andamento"
                chamado.suporte_id = suporte_id
                chamado.data_inicio_atendimento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def finalizar_atendimento(self, chamado_id: int, diagnostico: str, solucao: str):
        session = self.session_factory()
        try:
            chamado = session.query(Chamado).get(chamado_id)
            if chamado:
                chamado.status = "Finalizado"
                chamado.data_fechamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                chamado.diagnostico = diagnostico
                chamado.solucao = solucao
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def buscar_por_id(self, chamado_id: int) -> Optional[Chamado]:
        session = self.session_factory()
        try:
            return session.query(Chamado)\
                .options(joinedload(Chamado.usuario), joinedload(Chamado.suporte))\
                .filter(Chamado.id == chamado_id).first()
        finally:
            session.close()

    def excluir(self, chamado_id: int):
        session = self.session_factory()
        try:
            chamado = session.query(Chamado).get(chamado_id)
            if chamado:
                session.delete(chamado)
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def listar_todos(self) -> List[Chamado]:
        session = self.session_factory()
        try:
            return session.query(Chamado).options(joinedload(Chamado.usuario), joinedload(Chamado.suporte)).order_by(Chamado.data_abertura.desc()).all()
        finally:
            session.close()

    def listar_pendentes(self) -> List[Chamado]:
        session = self.session_factory()
        try:
            return session.query(Chamado).options(joinedload(Chamado.usuario), joinedload(Chamado.suporte))\
                .filter(Chamado.status != 'Finalizado')\
                .order_by(Chamado.data_abertura.desc()).all()
        finally:
            session.close()

    def listar_por_usuario(self, usuario_id: int) -> List[Chamado]:
        session = self.session_factory()
        try:
            return session.query(Chamado).options(joinedload(Chamado.usuario)).filter_by(usuario_id=usuario_id).order_by(Chamado.data_abertura.desc()).all()
        finally:
            session.close()

    def atualizar_status(self, chamado_id: int, novo_status: str):
        session = self.session_factory()
        try:
            chamado = session.query(Chamado).get(chamado_id)
            if chamado:
                chamado.status = novo_status
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    
    def buscar_filtrado(self, termo: str) -> List[Chamado]:
        session = self.session_factory()
        try:
            termo_like = f"%{termo}%"
            return session.query(Chamado).join(Usuario, Chamado.usuario_id == Usuario.id).options(joinedload(Chamado.usuario), joinedload(Chamado.suporte)).filter(
                or_(
                    Usuario.nome.like(termo_like),
                    Usuario.setor.like(termo_like),
                    Chamado.descricao.like(termo_like),
                    Chamado.maquina.like(termo_like),
                    Chamado.status.like(termo_like)
                )
            ).order_by(Chamado.data_abertura.desc()).all()
        finally:
            session.close()

    # --- RELATÓRIOS ---
    def obter_dados_relatorio(self, data_inicio: str, data_fim: str) -> Dict[str, Any]:
        session = self.session_factory()
        try:
            # Filtro base de data (Abertura dentro do range)
            # Como é SQLite string, a comparação lexicográfica funciona YYYY-MM-DD
            filtro_data = Chamado.data_abertura.between(data_inicio, data_fim)
            
            # 1. Setor com mais chamados
            top_setor = session.query(Usuario.setor, func.count(Chamado.id).label('total'))\
                .join(Chamado, Chamado.usuario_id == Usuario.id)\
                .filter(filtro_data)\
                .group_by(Usuario.setor)\
                .order_by(desc('total')).all()

            # 2. Máquina com mais problemas
            top_maquina = session.query(Chamado.maquina, func.count(Chamado.id).label('total'))\
                .filter(filtro_data)\
                .group_by(Chamado.maquina)\
                .order_by(desc('total')).all()

            # 3. Suporte que mais resolveu (Status Finalizado)
            top_suporte = session.query(Usuario.nome, func.count(Chamado.id).label('total'))\
                .join(Chamado, Chamado.suporte_id == Usuario.id)\
                .filter(filtro_data, Chamado.status == 'Finalizado')\
                .group_by(Usuario.nome)\
                .order_by(desc('total')).all()

            # 4. Chamados para calcular tempo médio (buscamos os dados brutos para calcular no Python)
            chamados_finalizados = session.query(Chamado.data_abertura, Chamado.data_fechamento)\
                .filter(filtro_data, Chamado.status == 'Finalizado').all()

            return {
                "setores": top_setor,
                "maquinas": top_maquina,
                "suportes": top_suporte,
                "tempos": chamados_finalizados
            }
        finally:
            session.close()