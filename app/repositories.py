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
            novo_usuario = Usuario(nome=nome, login=login, senha=senha_hash, tipo=tipo, setor=setor,trocar_senha=True)
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
            if filtro_setor and filtro_setor != "TODOS":
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

    def possui_chamado_ativo(self, user_id: int) -> bool:
        """Verifica se o usuário tem chamados que não estão Finalizados"""
        session = self.session_factory()
        try:
            # Busca um chamado que seja do usuário E que o status NÃO seja 'Finalizado'
            chamado = session.query(Chamado).filter(
                Chamado.usuario_id == user_id,
                Chamado.status != 'Finalizado'
            ).first()

            
            # Se encontrou algum (chamado is not None), retorna True
            return chamado is not None
        finally:
            session.close()

    def criar_com_contas(self, usuario_id: int, descricao: str, maquina: str, contas_selecionadas: str):

        session = self.session_factory()
        try:
            novo_chamado = Chamado(
                usuario_id=usuario_id,
                descricao=descricao,
                maquina=maquina,
                contas_solicitadas=contas_selecionadas,
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
                chamado.status = "Resolvido"
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
                .filter(Chamado.status.notin_(["Finalizado", "Resolvido"]))\
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
            filtro_data = Chamado.data_abertura.between(data_inicio, data_fim)
            
            # --- NOVO: Contagem por Status para o Dashboard ---
            # Retorna algo como: [('Aberto', 10), ('Finalizado', 5)]
            stats_raw = session.query(Chamado.status, func.count(Chamado.id))\
                .filter(filtro_data)\
                .group_by(Chamado.status).all()
            
            # Converte para dicionário para facilitar: {'Aberto': 10, 'Finalizado': 5}
            stats_dict = {s[0]: s[1] for s in stats_raw}


            # 2. Top 5 Usuários que mais abrem chamados
            lista_usuarios = session.query(Usuario.nome, func.count(Chamado.id).label('total'))\
                .join(Chamado, Chamado.usuario_id == Usuario.id)\
                .filter(filtro_data)\
                .group_by(Usuario.nome)\
                .order_by(desc('total'))\
                .limit(5).all()

            # 3. Top 5 Setores
            lista_setores = session.query(Usuario.setor, func.count(Chamado.id).label('total'))\
                .join(Chamado, Chamado.usuario_id == Usuario.id)\
                .filter(filtro_data)\
                .group_by(Usuario.setor)\
                .order_by(desc('total'))\
                .limit(5).all()

            return {
                "stats_dict": stats_dict, # <--- ADICIONADO AQUI
                "lista_usuarios": lista_usuarios,
                "lista_setores": lista_setores
            }
        finally:
            session.close()