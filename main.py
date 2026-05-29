import sys
import traceback
import os

# --- INÍCIO DA CORREÇÃO PARA PLUGINS DE MÍDIA ---
# Adicionado para resolver problema de plugins (como áudio) no Windows
# Define explicitamente o caminho dos plugins do Qt para o ambiente.
try:
    # O método preferencial e mais robusto
    from PySide6.QtCore import QLibraryInfo
    plugin_path = QLibraryInfo.path(QLibraryInfo.PluginsPath)
    os.environ['QT_PLUGIN_PATH'] = plugin_path
except ImportError:
    # Um método de fallback caso o de cima falhe
    try:
        import PySide6
        plugin_path = os.path.join(os.path.dirname(PySide6.__file__), "plugins")
        if os.path.isdir(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
    except Exception as e:
        print(f"AVISO: Falha ao tentar configurar o QT_PLUGIN_PATH: {e}")
# --- FIM DA CORREÇÃO ---

if sys.platform == "win32":
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif sys.platform == "darwin":  # macOS
    os.environ["QT_QPA_PLATFORM"] = "cocoa"
elif sys.platform == "linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"

print(">>> Importando módulos...", flush=True)
try:
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from app.core.database import DatabaseManager
    from app.repositories import UsuarioRepository, ChamadoRepository, SolicitacaoContaRepository, IPRepository
    from app.controllers import AuthController, ChamadoController, SolicitacaoContaController, IPController
    from app.views import LoginWindow, UserWindow, AdminWindow, STYLESHEET
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    sys.exit(1)

class SistemaChamadosApp:
    def __init__(self):
        print(">>> Inicializando QApplication...", flush=True)
        # A flag self.is_initialized controla se a aplicação pode rodar.
        # Se a conexão com o banco falhar, ela permanecerá False.
        self.is_initialized = False
        self.app = QApplication(sys.argv)
        # Define ícone da aplicação (suporta executável empacotado)
        def resource_path(relative_path: str) -> str:
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.abspath('.'))
            else:
                base_path = os.path.abspath('.')
            return os.path.join(base_path, relative_path)

        icon_path = resource_path('assets/icon.ico')
        try:
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        self.app.setStyleSheet(STYLESHEET)
        
        # 1. Configuração do Banco
        print(">>> Configurando banco de dados...", flush=True)
        try:
            self.db_manager = DatabaseManager()
            self.db_manager.setup()
            print(">>> Banco configurado com sucesso.", flush=True)
        except Exception as e:
            print(f"ERRO NO BANCO: {e}")
            # Se a conexão com o banco de dados falhar, exibe uma janela de erro.
            # A aplicação não continuará a inicialização.
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setWindowTitle("Sistema Indisponível")
            error_dialog.setText("Não foi possível conectar ao Siscall.")
            error_dialog.setInformativeText("Tente novamente mais tarde ou contate o suporte.")
            error_dialog.setStandardButtons(QMessageBox.Ok)
            error_dialog.exec()
            return # Interrompe a inicialização

        # 2. Repositórios e Controladores
        print(">>> Inicializando controladores...", flush=True)
        session_factory = self.db_manager.get_session
        user_repo = UsuarioRepository(session_factory)
        chamado_repo = ChamadoRepository(session_factory)
        solicitacao_repo = SolicitacaoContaRepository(session_factory)
        ip_repo = IPRepository(session_factory)
        
        self.auth_controller = AuthController(user_repo)
        self.chamado_controller = ChamadoController(chamado_repo, ip_repo)
        self.solicitacao_controller = SolicitacaoContaController(solicitacao_repo)
        self.ip_controller = IPController(ip_repo)

        # 3. Janela Atual
        self.current_window = None
        print(">>> Abrindo janela de login...", flush=True)
        self.show_login()

        # Se a inicialização chegou até aqui, está tudo OK.
        self.is_initialized = True

    def show_login(self):
        # Abre nova janela antes de fechar a antiga
        new_window = LoginWindow(self.auth_controller, self.on_login_success)
        new_window.show()
        
        if self.current_window:
            self.current_window.close()
        self.current_window = new_window

    def on_login_success(self, user):
        # O Timer protege a transição, evitando crash no Linux ao apertar Enter
        QTimer.singleShot(0, lambda: self._perform_transition(user))

    def _perform_transition(self, user):
        try:
            print(f">>> Login sucesso: {user.nome} ({user.tipo})")
            if user.tipo == 1:
                # Admin - Passa todos os controllers diretamente no construtor
                new_window = AdminWindow(user, self.chamado_controller, self.auth_controller, self.solicitacao_controller, self.ip_controller, self.logout)
            else:
                # Comum
                new_window = UserWindow(user, self.chamado_controller, self.auth_controller, self.solicitacao_controller, self.logout)
            
            new_window.show()
            
            old_window = self.current_window
            self.current_window = new_window
            
            if old_window:
                old_window.close()
                
        except Exception as e:
            print(f"ERRO AO ABRIR PAINEL: {e}")
            traceback.print_exc()

    def logout(self):
        print(">>> Logout solicitado")
        self.auth_controller.logout()
        QTimer.singleShot(0, self.show_login)

    def run(self):
        # Se a inicialização falhou (ex: erro de banco), não executa o app.
        if not self.is_initialized:
            return 1 # Retorna um código de erro

        print(">>> Entrando no loop de eventos...", flush=True)
        return self.app.exec()

if __name__ == "__main__":
    try:
        sistema = SistemaChamadosApp()
        sys.exit(sistema.run())
    except Exception as e:
        print("\n!!! OCORREU UM ERRO FATAL !!!")
        print(f"Erro: {e}")
        traceback.print_exc()