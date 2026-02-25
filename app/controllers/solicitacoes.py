class SolicitacaoContaController:
    def __init__(self, repo):
        self.repo = repo

    def criar_solicitacao(self, usuario_id, descricao, sistemas):
        if not sistemas:
            raise ValueError("Selecione pelo menos um sistema.")
        sistemas_str = ", ".join(sistemas)
        self.repo.criar(usuario_id, descricao, sistemas_str)

    def listar_pendentes(self):
        return self.repo.listar_pendentes()
    
    def buscar_por_id(self, solicitacao_id):
        return self.repo.buscar_por_id(solicitacao_id)

    def assumir_solicitacao(self, solicitacao_id, suporte_id):
        solicitacao = self.repo.buscar_por_id(solicitacao_id)
        if not solicitacao: raise ValueError("Solicitação não encontrada.")
        if solicitacao.status == "Em andamento" and solicitacao.suporte_id and solicitacao.suporte_id != suporte_id:
            raise ValueError(f"Esta solicitação já está sendo atendida por {solicitacao.nome_suporte}.")
        self.repo.assumir_atendimento(solicitacao_id, suporte_id)

    def finalizar_solicitacao(self, solicitacao_id, suporte_id, credenciais):
        if not credenciais.strip():
            raise ValueError("É obrigatório informar as credenciais criadas.")
        
        solicitacao = self.repo.buscar_por_id(solicitacao_id)
        if solicitacao.suporte_id != suporte_id:
             raise ValueError("Apenas o suporte responsável pode finalizar.")
        
        self.repo.finalizar_atendimento(solicitacao_id, credenciais)
