import hashlib
from datetime import datetime
from app.models import Usuario

class ChamadoController:
    def __init__(self, repo):
        self.repo = repo

    def criar_chamado(self, usuario_id, descricao, maquina):
        if self.repo.possui_chamado_ativo(usuario_id):
            raise ValueError("Você já possui um chamado em aberto ou em andamento. Aguarde a finalização para abrir um novo.")

        if not descricao.strip():
            raise ValueError("Descrição não pode estar vazia.")
        if not maquina or maquina == "Selecione a Máquina":
             raise ValueError("Selecione qual máquina está com problema.")
        self.repo.criar(usuario_id, descricao, maquina)
    
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

    def resolver_chamado(self, chamado_id, suporte_id, diagnostico, solucao):
        chamado = self.repo.buscar_por_id(chamado_id)
        
        if not diagnostico.strip() or not solucao.strip():
            raise ValueError("É obrigatório descrever o Diagnóstico e a Solução.")
        
        if chamado.suporte_id != suporte_id:
             raise ValueError("Apenas o suporte responsável pode resolver o chamado.")
        self.repo.finalizar_atendimento(chamado_id, diagnostico, solucao)
    
    def fechar_chamado_pelo_usuario(self, chamado_id: int, usuario_id: int):
        """Usuário confirma a resolução e fecha o chamado."""
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado:
            raise ValueError("Chamado não encontrado.")
        if chamado.usuario_id != usuario_id:
            raise ValueError("Apenas o autor do chamado pode fechá-lo.")
        if chamado.status != 'Resolvido':
            raise ValueError("Este chamado não pode ser fechado pois não foi resolvido pelo suporte.")
        
        self.repo.fechar_chamado(chamado_id)

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