import hashlib
from datetime import datetime
from app.database import Usuario

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
    
    def cadastrar_usuario(self, nome, sobrenome, login, senha, setor):
        if not nome or not login or not senha:
            raise ValueError("Preencha todos os campos obrigatórios.")
        if not setor or setor == "Selecione seu Setor":
            raise ValueError("Por favor, selecione um setor válido.")
        
        nome_completo = f"{nome} {sobrenome}".strip()
        if self.repo.buscar_por_login(login):
            raise ValueError("Este login já está em uso.")
            
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        sucesso = self.repo.criar(nome_completo, login, senha_hash, tipo=0, setor=setor)
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

class ChamadoController:
    def __init__(self, repo):
        self.repo = repo

    def criar_chamado(self, usuario_id, descricao, maquina):
        if not descricao.strip():
            raise ValueError("Descrição não pode estar vazia.")
        if not maquina or maquina == "Selecione a Máquina":
             raise ValueError("Selecione qual máquina está com problema.")
        self.repo.criar(usuario_id, descricao, maquina)
    
    def criar_chamado_com_contas(self, usuario_id, descricao, maquina, contas_selecionadas):
        """Criar chamado para solicitação de contas com sistemas selecionados"""
        if not descricao.strip():
            raise ValueError("Descrição não pode estar vazia.")
        if maquina != "CRIAÇÃO DE CONTA":
            raise ValueError("Este método é apenas para solicitações de contas.")
        if not contas_selecionadas:
            raise ValueError("Selecione pelo menos um sistema.")
        # Passar contas_selecionadas para o repositório
        self.repo.criar_com_contas(usuario_id, descricao, maquina, contas_selecionadas)
    
    def excluir_chamado(self, chamado_id):
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado: raise ValueError("Chamado não encontrado.")
        if chamado.status != "Aberto":
            raise ValueError("Apenas chamados 'Aberto' podem ser excluídos.")
        self.repo.excluir(chamado_id)

    def assumir_chamado(self, chamado_id, suporte_id):
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado: raise ValueError("Chamado não encontrado.")
        if chamado.status == "Em andamento" and chamado.suporte_id and chamado.suporte_id != suporte_id:
            raise ValueError(f"Este chamado já está sendo atendido por {chamado.nome_suporte}.")
        self.repo.assumir_atendimento(chamado_id, suporte_id)

    def finalizar_chamado(self, chamado_id, suporte_id, diagnostico, solucao):
        # Buscar o chamado para verificar o tipo
        chamado = self.repo.buscar_por_id(chamado_id)
        
        # Validação diferente para solicitação de contas
        if chamado.maquina == "CRIAÇÃO DE CONTA":
            # Para contas, apenas solução (login/senha) é obrigatória
            if not solucao.strip():
                raise ValueError("É obrigatório informar as credenciais criadas.")
        else:
            # Para chamados normais, tanto diagnóstico quanto solução são obrigatórios
            if not diagnostico.strip() or not solucao.strip():
                raise ValueError("É obrigatório descrever o Diagnóstico e a Solução.")
        
        if chamado.suporte_id != suporte_id:
             raise ValueError("Apenas o suporte responsável pode finalizar.")
        self.repo.finalizar_atendimento(chamado_id, diagnostico, solucao)
    
    def buscar_por_id(self, chamado_id):
        return self.repo.buscar_por_id(chamado_id)

    def listar_meus_chamados(self, usuario_id):
        return self.repo.listar_por_usuario(usuario_id)

    def listar_todos(self):
        return self.repo.listar_todos()

    def listar_pendentes(self):
        return self.repo.listar_pendentes()

    def atualizar_status(self, chamado_id, novo_status):
        self.repo.atualizar_status(chamado_id, novo_status)
    
    def buscar(self, termo):
        return self.repo.buscar_filtrado(termo)

    # --- RELATÓRIOS ---
    def gerar_relatorio(self, data_inicio, data_fim):
        # Formata datas para string SQL (YYYY-MM-DD HH:MM:SS)
        # Assumindo que data_inicio e data_fim vêm como QDate ou string YYYY-MM-DD
        inicio_str = f"{data_inicio} 00:00:00"
        fim_str = f"{data_fim} 23:59:59"
        
        dados = self.repo.obter_dados_relatorio(inicio_str, fim_str)
        
        # Calcular tempo médio
        total_segundos = 0
        qtd_fechados = len(dados["tempos"])
        
        for inicio, fim in dados["tempos"]:
            try:
                t1 = datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
                t2 = datetime.strptime(fim, "%Y-%m-%d %H:%M:%S")
                total_segundos += (t2 - t1).total_seconds()
            except:
                pass # Ignora datas mal formadas
        
        tempo_medio_str = "N/A"
        if qtd_fechados > 0:
            media = total_segundos / qtd_fechados
            # Converte segundos para H:M
            horas = int(media // 3600)
            minutos = int((media % 3600) // 60)
            tempo_medio_str = f"{horas}h {minutos}m"

        return {
            "top_setor": dados["setores"][0] if dados["setores"] else ("Nenhum", 0),
            "top_maquina": dados["maquinas"][0] if dados["maquinas"] else ("Nenhuma", 0),
            "top_suporte": dados["suportes"][0] if dados["suportes"] else ("Nenhum", 0),
            "tempo_medio": tempo_medio_str,
            "total_periodo": qtd_fechados # ou total geral se quisesse
        }