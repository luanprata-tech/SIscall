import hashlib
from datetime import datetime
from app.models import Usuario

class AuthController:
    def __init__(self, repo):
        self.repo = repo
        self.sessao_usuario = None

    def login(self, user_login, password_plain):
        usuario = self.repo.buscar_por_login(user_login)
        if usuario:
            pass_hash = hashlib.sha256(password_plain.encode()).hexdigest()
            if pass_hash == usuario.senha:
                self.sessao_usuario = usuario
                return usuario
        return None
    
    def cadastrar_usuario(self, nome, sobrenome, login, senha, setor, tipo=0):
        if not nome or not login or not senha:
            raise ValueError("Preencha todos os campos obrigatórios.")
        if not setor or setor == "Selecione seu Setor":
            raise ValueError("Por favor, selecione um setor válido.")
        
        nome_completo = f"{nome} {sobrenome}".strip()
        if self.repo.buscar_por_login(login):
            raise ValueError("Este login já está em uso.")
            
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        # Ao cadastrar via painel administrativo, marcar como senha provisória
        sucesso = self.repo.criar(nome_completo, login, senha_hash, tipo=tipo, setor=setor, trocar_senha=True)
        if not sucesso:
            raise ValueError("Erro ao criar usuário.")

    # --- MÉTODOS ADMIN ---
    def listar_usuarios(self, termo="", setor="Todos"):
        return self.repo.buscar_filtrado(termo, setor)

    def atualizar_setor(self, user_id, novo_setor):
        self.repo.atualizar_setor(user_id, novo_setor)

    def alterar_cargo_usuario(self, user_id, novo_tipo):
        # 0 = User, 1 = Admin
        # Prevenção: Não remover o próprio admin se for o último (opcional, mas boa prática)
        if self.sessao_usuario and self.sessao_usuario.id == user_id and novo_tipo == 0:
             # Em um sistema real verificariamos se há outros admins. 
             # Aqui deixamos livre mas avisamos.
             pass
        self.repo.atualizar_tipo(user_id, novo_tipo)

    def definir_senha_provisoria(self, user_id, senha_texto):
        if not senha_texto or len(senha_texto) < 3:
            raise ValueError("A senha provisória deve ter pelo menos 3 caracteres.")
        senha_hash = hashlib.sha256(senha_texto.encode()).hexdigest()
        self.repo.resetar_senha(user_id, senha_hash)

    def excluir_usuario(self, user_id):
        if self.sessao_usuario and self.sessao_usuario.id == user_id:
            raise ValueError("Você não pode excluir seu próprio usuário logado.")
        self.repo.excluir(user_id)

    def alterar_senha_definitiva(self, user_id, nova_senha):
        if len(nova_senha) < 4:
            raise ValueError("A nova senha deve ter no mínimo 4 caracteres.")
        senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
        self.repo.confirmar_nova_senha(user_id, senha_hash)

    def logout(self):
        self.sessao_usuario = None
