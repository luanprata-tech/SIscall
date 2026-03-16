from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, case, desc
from sqlalchemy.exc import IntegrityError
from app.models import Usuario, Chamado
from datetime import datetime

class UsuarioRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def buscar_por_login(self, login: str) -> Optional[Usuario]:
        session = self.session_factory()
        try:
            # Apenas usuários ativos podem se logar
            return session.query(Usuario).filter(Usuario.login == login, Usuario.ativo == True).first()
        finally:
            session.close()
            
    def buscar_por_id(self, user_id: int) -> Optional[Usuario]:
        session = self.session_factory()
        try:
            return session.get(Usuario, user_id)
        finally:
            session.close()

    def criar(self, nome: str, login: str, senha_hash: str, tipo: int, setor: str, trocar_senha: bool = False):
        session = self.session_factory()
        try:
            novo_usuario = Usuario(nome=nome, login=login, senha=senha_hash, tipo=tipo, setor=setor)
            # Flag para forçar troca de senha no primeiro login
            if trocar_senha:
                novo_usuario.trocar_senha = True
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
            # Exibe apenas usuários ativos na gestão
            return session.query(Usuario).filter(Usuario.ativo == True).order_by(Usuario.nome).all()
        finally:
            session.close()

    def buscar_filtrado(self, termo: str, filtro_setor: str = None) -> List[Usuario]:
        session = self.session_factory()
        try:
            # Exibe apenas usuários ativos na gestão
            query = session.query(Usuario).filter(Usuario.ativo == True)
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
            u = session.get(Usuario, user_id)
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
            u = session.get(Usuario, user_id)
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
            u = session.get(Usuario, user_id)
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
            u = session.get(Usuario, user_id)
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
            u = session.get(Usuario, user_id)
            if u:
                # Soft delete: marca como inativo para não quebrar relações FK existentes
                u.ativo = False
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()