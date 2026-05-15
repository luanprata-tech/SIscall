from ipaddress import ip_address


class IPController:
    IP_INICIO = ip_address("172.23.6.1")
    IP_FIM = ip_address("172.23.6.255")
    STATUS_VALIDOS = ["Livre", "Alocado", "Reservado", "Bloqueado"]

    def __init__(self, repo):
        self.repo = repo

    def _validar_ip(self, ip_texto: str):
        try:
            ip = ip_address(ip_texto)
        except ValueError:
            raise ValueError("IP inválido.")

        if ip.version != 4:
            raise ValueError("Apenas IPs IPv4 são suportados.")
        if ip < self.IP_INICIO or ip > self.IP_FIM:
            raise ValueError("O IP deve estar entre 172.23.6.1 e 172.23.6.255.")

    def listar_ips(self, termo="", status="Todos"):
        return self.repo.buscar_filtrado(termo, status)

    def buscar_por_ip(self, ip_texto):
        return self.repo.buscar_por_ip(ip_texto)

    def salvar_ip(self, ip_texto, maquina, nome_maquina, nome_usuario, setor, status):
        self._validar_ip(ip_texto)
        if status not in self.STATUS_VALIDOS:
            raise ValueError("Status inválido.")
        return self.repo.salvar(ip_texto, maquina, nome_maquina, nome_usuario, setor, status)

    def liberar_ip(self, ip_texto):
        self._validar_ip(ip_texto)
        return self.repo.liberar(ip_texto)