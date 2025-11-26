from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, case, desc
from sqlalchemy.exc import IntegrityError
from app.database import Usuario, Chamado
from datetime import datetime

class UsuarioRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        session = self.session_factory()
        try:
            return session.query(Usuario).filter_by(login=login).first()
        finally:
            session.close()
            
    def buscar_por_id(self, user_id: int) -> Optional[Usuario]:
        session = self.session_factory()
        try:
            return session.query(Usuario).get(user_id)
        finally:
            session.close()

    def criar(self, nome: str, login: str, senha_hash: str, tipo: int, setor: str):
        session = self.session_factory()
        try:
            novo_usuario = Usuario(nome=nome, login=login, senha=senha_hash, tipo=tipo, setor=setor)
            session.add(novo_usuario)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    # --- GESTÃO DE USUÁRIOS ---
    def listar_todos(self) -> List[Usuario]:
        session = self.session_factory()
        try:
            return session.query(Usuario).order_by(Usuario.nome).all()
        finally:
            session.close()

    def buscar_filtrado(self, termo: str, filtro_setor: str = None) -> List[Usuario]:
        session = self.session_factory()
        try:
            query = session.query(Usuario)
            if termo:
                t = f"%{termo}%"
                query = query.filter(or_(Usuario.nome.like(t), Usuario.login.like(t)))
            if filtro_setor and filtro_setor != "Todos":
                query = query.filter(Usuario.setor == filtro_setor)
            return query.order_by(Usuario.nome).all()
        finally:
            session.close()

    def atualizar_setor(self, user_id: int, novo_setor: str):
        session = self.session_factory()
        try:
            u = session.query(Usuario).get(user_id)
            if u:
                u.setor = novo_setor
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def atualizar_tipo(self, user_id: int, novo_tipo: int):
        session = self.session_factory()
        try:
            u = session.query(Usuario).get(user_id)
            if u:
                u.tipo = novo_tipo
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def resetar_senha(self, user_id: int, senha_hash: str):
        session = self.session_factory()
        try:
            u = session.query(Usuario).get(user_id)
            if u:
                u.senha = senha_hash
                u.trocar_senha = True 
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def confirmar_nova_senha(self, user_id: int, senha_hash: str):
        session = self.session_factory()
        try:
            u = session.query(Usuario).get(user_id)
            if u:
                u.senha = senha_hash
                u.trocar_senha = False 
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def excluir(self, user_id: int):
        session = self.session_factory()
        try:
            u = session.query(Usuario).get(user_id)
            if u:
                session.delete(u)
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

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