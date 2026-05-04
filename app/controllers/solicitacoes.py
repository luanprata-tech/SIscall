class SolicitacaoContaController:
    def __init__(self, repo):
        self.solicitacao_repo = repo

    def criar_solicitacao(self, usuario_id, descricao, sistemas):
        # Nova regra: permite múltiplas solicitações, mas bloqueia se houver
        # alguma solicitação com status 'Resolvido' aguardando confirmação pelo usuário.
        if hasattr(self.solicitacao_repo, 'tem_resolvido_pendente_por_usuario') and self.solicitacao_repo.tem_resolvido_pendente_por_usuario(usuario_id):
            raise ValueError("Você possui solicitações resolvidas aguardando confirmação. Confirme o fechamento antes de abrir novas solicitações.")
        
        if not sistemas:
            raise ValueError("Selecione pelo menos um sistema.")
        
        sistemas_str = ", ".join(sistemas)
        self.solicitacao_repo.criar(usuario_id, descricao, sistemas_str)

    def listar_minhas_solicitacoes(self, usuario_id):
        return self.solicitacao_repo.listar_por_usuario(usuario_id)

    def listar_pendentes(self):
        return self.solicitacao_repo.listar_pendentes()

    def listar_todas_solicitacoes(self):
        return self.solicitacao_repo.listar_todas()

    def buscar_por_id(self, solicitacao_id):
        return self.solicitacao_repo.buscar_por_id(solicitacao_id)

    def assumir_solicitacao(self, solicitacao_id, suporte_id):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if solicitacao.status != "Aberto":
            raise ValueError("Esta solicitação não está mais aberta para atendimento.")
        self.solicitacao_repo.assumir_atendimento(solicitacao_id, suporte_id)

    def finalizar_solicitacao(self, solicitacao_id, suporte_id, credenciais):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if solicitacao.suporte_id != suporte_id:
             raise ValueError("Apenas o suporte responsável pode finalizar.")
        
        self.solicitacao_repo.finalizar_atendimento(solicitacao_id, credenciais)

    def marcar_em_espera(self, solicitacao_id, suporte_id):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada.")
        if solicitacao.status != "Em andamento":
            raise ValueError("Apenas solicitações 'Em andamento' podem ser marcadas como em espera.")
        if solicitacao.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode marcar como em espera.")
        self.solicitacao_repo.marcar_em_espera(solicitacao_id)

    def continuar_de_espera(self, solicitacao_id, suporte_id):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada.")
        if solicitacao.status != "Em espera":
            raise ValueError("Apenas solicitações 'Em espera' podem ser continuadas.")
        if solicitacao.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode continuar a solicitação.")
        self.solicitacao_repo.continuar_de_espera(solicitacao_id)

    def resolver_de_espera(self, solicitacao_id, suporte_id, credenciais):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada.")
        if solicitacao.status != "Em espera":
            raise ValueError("Apenas solicitações 'Em espera' podem ser resolvidas.")
        if solicitacao.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode resolver a solicitação.")
        self.solicitacao_repo.finalizar_atendimento(solicitacao_id, credenciais)

    def excluir_solicitacao(self, solicitacao_id, usuario_id):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada.")
        if solicitacao.usuario_id != usuario_id:
            raise ValueError("Você não tem permissão para excluir esta solicitação.")
        if solicitacao.status != "Aberto":
            raise ValueError("Apenas solicitações com status 'Aberto' podem ser excluídas.")
        self.solicitacao_repo.excluir(solicitacao_id)

    def fechar_solicitacao_pelo_usuario(self, solicitacao_id: int, usuario_id: int):
        solicitacao = self.solicitacao_repo.buscar_por_id(solicitacao_id)
        if not solicitacao:
            raise ValueError("Solicitação não encontrada.")
        if solicitacao.usuario_id != usuario_id:
            raise ValueError("Apenas o autor da solicitação pode fechá-la.")
        if solicitacao.status != 'Resolvido':
            raise ValueError("Esta solicitação não pode ser fechada pois não foi resolvida pelo suporte.")
        
        self.solicitacao_repo.fechar_solicitacao(solicitacao_id)

    def contar_em_aberto(self) -> int:
        """Retorna o número de solicitações de acesso em aberto."""
        return self.solicitacao_repo.contar_em_aberto()