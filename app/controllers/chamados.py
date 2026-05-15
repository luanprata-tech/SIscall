import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from app.models import Usuario

class ChamadoController:
    def __init__(self, repo):
        self.repo = repo

    def criar_chamado(self, usuario_id, descricao, maquina, imagem_path=None, setor_origem=None):
        # Nova regra: permite múltiplos chamados, mas bloqueia enquanto houver
        # algum chamado do usuário com status 'Resolvido' (aguardando confirmação).
        if hasattr(self.repo, 'tem_resolvido_pendente_por_usuario') and self.repo.tem_resolvido_pendente_por_usuario(usuario_id):
            raise ValueError("Você possui chamados resolvidos aguardando confirmação. Confirme o fechamento antes de abrir novos chamados.")

        if not descricao.strip():
            raise ValueError("Descrição não pode estar vazia.")
        if not maquina or maquina == "Selecione a Máquina":
             raise ValueError("Selecione qual máquina está com problema.")
        self.repo.criar(usuario_id, descricao, maquina, imagem_path=imagem_path, setor_origem=setor_origem)
    
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

    def marcar_em_espera(self, chamado_id, suporte_id, motivo_espera=""):
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado:
            raise ValueError("Chamado não encontrado.")
        if chamado.status != "Em andamento":
            raise ValueError("Apenas chamados 'Em andamento' podem ser marcados como em espera.")
        if chamado.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode marcar como em espera.")
        self.repo.marcar_em_espera(chamado_id, motivo_espera=motivo_espera)

    def continuar_de_espera(self, chamado_id, suporte_id):
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado:
            raise ValueError("Chamado não encontrado.")
        if chamado.status != "Em espera":
            raise ValueError("Apenas chamados 'Em espera' podem ser continuados.")
        if chamado.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode continuar o chamado.")
        self.repo.continuar_de_espera(chamado_id)

    def resolver_de_espera(self, chamado_id, suporte_id, diagnostico, solucao):
        chamado = self.repo.buscar_por_id(chamado_id)
        if not chamado:
            raise ValueError("Chamado não encontrado.")
        if chamado.status != "Em espera":
            raise ValueError("Apenas chamados 'Em espera' podem ser resolvidos.")
        if not diagnostico.strip() or not solucao.strip():
            raise ValueError("É obrigatório descrever o Diagnóstico e a Solução.")
        if chamado.suporte_id != suporte_id:
            raise ValueError("Apenas o suporte responsável pode resolver o chamado.")
        self.repo.finalizar_atendimento(chamado_id, diagnostico, solucao)

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

        def _parse_datetime(valor):
            if not valor:
                return None
            if isinstance(valor, datetime):
                return valor
            for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
                try:
                    return datetime.strptime(str(valor), formato)
                except Exception:
                    continue
            return None
        
        # Calcular tempo médio
        total_segundos = 0
        qtd_atendidos = 0
        qtd_mais_1_dia = 0
        
        status_counts = Counter()
        department_counts = Counter()
        weekday_counts = Counter({"Seg": 0, "Ter": 0, "Qua": 0, "Qui": 0, "Sex": 0, "Sab": 0, "Dom": 0})
        created_by_day = defaultdict(int)
        resolved_by_day = defaultdict(int)
        heatmap_weekday_hour = [[0 for _ in range(24)] for _ in range(7)]

        for item in dados.get("chamados_periodo", []):
            abertura = item[0] if len(item) > 0 else None
            inicio_atendimento = item[1] if len(item) > 1 else None
            fechamento = item[2] if len(item) > 2 else None
            status = item[3] if len(item) > 3 else "Sem status"
            setor = item[4] if len(item) > 4 else None
            descricao = item[5] if len(item) > 5 else ""

            t_abertura = _parse_datetime(abertura)
            t_inicio = _parse_datetime(inicio_atendimento)
            t_fechamento = _parse_datetime(fechamento)

            status_key = status or "Sem status"
            status_counts[status_key] += 1

            department_counts[(setor or "N/A")] += 1

            if t_abertura:
                weekday_idx = t_abertura.weekday()
                weekday_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
                weekday_counts[weekday_names[weekday_idx]] += 1
                day_key = t_abertura.strftime("%Y-%m-%d")
                created_by_day[day_key] += 1
                heatmap_weekday_hour[t_abertura.weekday()][t_abertura.hour] += 1

            if t_abertura and t_inicio:
                diferenca_atendimento = (t_inicio - t_abertura).total_seconds()
                if diferenca_atendimento >= 0:
                    total_segundos += diferenca_atendimento
                    qtd_atendidos += 1

            if t_abertura and t_fechamento:
                diferenca_fechamento = (t_fechamento - t_abertura).total_seconds()
                if diferenca_fechamento > 86400:
                    qtd_mais_1_dia += 1
                resolved_by_day[t_fechamento.strftime("%Y-%m-%d")] += 1

        # Série mensal fixa (1..12), independente do filtro superior
        monthly_year = datetime.now().year
        monthly_labels = [str(m) for m in range(1, 13)]
        monthly_created = [0] * 12
        try:
            for chamado in self.repo.listar_todos():
                t_abertura = _parse_datetime(getattr(chamado, "data_abertura", None))
                if t_abertura and t_abertura.year == monthly_year:
                    monthly_created[t_abertura.month - 1] += 1
        except Exception:
            pass
        
        tempo_medio_str = "N/A"
        if qtd_atendidos > 0:
            media = total_segundos / qtd_atendidos
            # Converte segundos para H:M
            horas = int(media // 3600)
            minutos = int((media % 3600) // 60)
            tempo_medio_str = f"{horas}h {minutos}m"

        return {
            "top_setor": dados["setores"][0] if dados["setores"] else ("Nenhum", 0),
            "top_maquina": dados["maquinas"][0] if dados["maquinas"] else ("Nenhuma", 0),
            "top_suporte": dados["suportes"][0] if dados["suportes"] else ("Nenhum", 0),
            "tempo_medio": tempo_medio_str,
            "total_periodo": dados.get("total_periodo", 0),
            "abertos": dados.get("abertos", 0),
            "fechados": dados.get("fechados", 0),
            "tempo_medio_atendimento": tempo_medio_str,
            "mais_1_dia": qtd_mais_1_dia,
            "status_counts": dict(status_counts),
            "department_counts": dict(department_counts),
            "weekday_counts": dict(weekday_counts),
            "top_3_suportes": dados["suportes"][:3] if dados["suportes"] else [],
            "timeline_labels": [],
            "timeline_created": [],
            "timeline_resolved": [],
            "monthly_year": monthly_year,
            "monthly_labels": monthly_labels,
            "monthly_created": monthly_created,
            "heatmap_weekday_hour": heatmap_weekday_hour,
        }