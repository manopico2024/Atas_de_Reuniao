###############################################################
#                 CRIADO POR MVDevTECHteam!                   #                                                              
#                                                             #
#          Créditos: Developer Marcus Vinicius Nunes          #
#                                                             #        
#                          @2025                              #
#                        Game-PASS                            #                            
#                           \o/                               #
#                      Tem mais Atualizações                  #                              
###############################################################

# IMPORTANDO AS LIBS DE INTERFACE GRÁFICA
from PyQt5.QtWidgets import (QDialog, QMessageBox, QMainWindow, QApplication, 
                             QTreeWidgetItem, QVBoxLayout, QTextEdit, QPushButton, 
                             QShortcut, QHBoxLayout, QComboBox, QLabel, QInputDialog, 
                             QTableWidget, QTableWidgetItem, QFrame, QFileDialog, 
                             QProgressDialog, QWidget, QTreeWidget, QLineEdit)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap
from PyQt5.QtCore import Qt, QCoreApplication, QPoint
from PyQt5.QtGui import QCursor
import requests
import pandas as pd
import sqlite3
from pathlib import Path
import shutil
import sys
import os
import traceback
import logging
import random

# IMPORTANDO AS TELAS
from models.telaLogin import Ui_telaLogin
from models.telaGraficodePresenca import Ui_telaGraficodePresenca
from models.telaPrincipal import Ui_telaPrincipal
from models.telaCatalogoBiblico import Ui_telaCatalogoBiblico
from biblia_api import BibliaDigitalAPI

class TelaArrastavelBase(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = None
        
        # Configurar janela sem bordas
        self.setWindowFlags(Qt.FramelessWindowHint)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Diferença entre o mouse e o canto da janela
            self._offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._offset:
            # Move a janela livremente
            self.move(event.globalPos() - self._offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._offset = None
        event.accept()
        
class Login(TelaArrastavelBase):
    def __init__(self, parent=None):
        super().__init__(parent)  # Chama o construtor da classe base
        self.ui = Ui_telaLogin()
        self.ui.setupUi(self)

        self.setWindowIcon(QIcon("icons/icons/logoSpike.png"))

        # Configurar campos de senha
        self.ui.TXT_SENHA.setEchoMode(QLineEdit.Password)
        self.ui.TXT_CONFIRMAR_SENHA.setEchoMode(QLineEdit.Password)

        self.ui.TXT_NOME.setFocus()  # Foco inicial no campo de nome
        self.login_sucesso = False   # Flag para controle de login

        self.configurar_shortcuts_login()

        # CONEXÕES DOS BOTÕES
        self.ui.BTN_LOGIN.clicked.connect(self.novo_login)
        self.ui.TXT_NOME.returnPressed.connect(self.focar_senha)
        self.ui.TXT_SENHA.returnPressed.connect(self.focar_confirmacao)
        self.ui.TXT_CONFIRMAR_SENHA.returnPressed.connect(self.novo_login)

        print("✅ Tela Login criada com arrasta e solta!")

    # ================= SHORTCUTS =================
    def configurar_shortcuts_login(self):
        self.shortcutEnter = QShortcut(QKeySequence(Qt.Key_Return), self)
        self.shortcutEnter.activated.connect(self.novo_login)
        self.shortcutEnter.setContext(Qt.WidgetShortcut)

    # ================= FOCO =================
    def focar_senha(self):
        self.ui.TXT_SENHA.setFocus()

    def focar_confirmacao(self):
        self.ui.TXT_CONFIRMAR_SENHA.setFocus()

    # ================= LOGIN =================
    def novo_login(self):
        admin = "mano"
        senha_admin = "admin"

        user = self.ui.TXT_NOME.text().strip()
        password = self.ui.TXT_SENHA.text().strip()
        pass_confirm = self.ui.TXT_CONFIRMAR_SENHA.text().strip()

        if not user or not password or not pass_confirm:
            self.mostrar_mensagem("Atenção", "📝 Preencha todos os campos!")
            return

        if user == admin and password == senha_admin and pass_confirm == senha_admin:
            self.mostrar_mensagem("Sucesso", "✅ Login realizado com sucesso!\nBem-vindo!")
            self.login_sucesso = True
            self.close()
        else:
            self.mostrar_mensagem("Erro", "❌ Usuário ou senha inválidos!")
            self.ui.TXT_SENHA.clear()
            self.ui.TXT_CONFIRMAR_SENHA.clear()
            self.ui.TXT_NOME.setFocus()

    # ================= MENSAGENS =================
    def mostrar_mensagem(self, titulo, mensagem):
        dialog = QDialog(self)
        dialog.setWindowTitle(titulo)
        dialog.setModal(True)
        dialog.setFixedSize(320, 160)

        layout = QVBoxLayout(dialog)

        label = QLabel(mensagem)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; font-weight: bold;")

        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(dialog.accept)

        layout.addWidget(label)
        layout.addWidget(btn_ok)

        dialog.exec_()

    # ================= CONTROLE =================
    def login_foi_bem_sucedido(self):
        return self.login_sucesso

    def closeEvent(self, event):
        if not self.login_sucesso:
            QCoreApplication.quit()
        event.accept()

class TelaGraficodePresenca(TelaArrastavelBase):
    def __init__(self, parent=None):
        super().__init__(parent)  # Chama o construtor da classe base
        self.ui = Ui_telaGraficodePresenca()
        self.ui.setupUi(self)
        
        # Criar diretório para arquivos
        os.makedirs("arquivo", exist_ok=True)       
        # Configurações da janela
        self.setWindowIcon(QIcon("icons/icons/logoSpike.png"))
        self.setGeometry(150, 200, 500, 350)
        
        print("✅ Tela Gráfico de Presença criada com arrasta e solta!")

class CatalogoBiblico(TelaArrastavelBase):
    def __init__(self, parent=None):
        super().__init__(parent)  # Chama o construtor da classe base
        self.ui = Ui_telaCatalogoBiblico()
        self.ui.setupUi(self)
        
        self.setWindowIcon(QIcon("icons/icons/logoSpike.png"))
        self.setGeometry(150, 200, 973, 437)
        
        # Criar diretório para arquivos
        os.makedirs("arquivo", exist_ok=True)

        self.api = BibliaDigitalAPI()

        # Conectar botões
        self.ui.btnCarregarLivros.clicked.connect(self.carregar_livros)
        self.ui.btnBuscarCapitulo.clicked.connect(self.carregar_capitulo)

        # Carregar livros automaticamente
        self.carregar_livros()
        
    def carregar_livros(self):
        try:
            livros = self.api.get_books()

            self.ui.comboLivros.clear()
            for livro in livros:
                self.ui.comboLivros.addItem(
                    livro["name"],
                    livro["abbrev"]["pt"]
                )

            print("📚 Livros carregados com sucesso")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar livros:\n{str(e)}"
            )
    
    def carregar_capitulo(self):
        try:
            abbrev = self.ui.comboLivros.currentData()
            capitulo = self.ui.spinCapitulo.value()
            versao = self.ui.comboVersao.currentText()

            dados = self.api.get_chapter(versao, abbrev, capitulo)

            self.ui.listaVersiculos.clear()

            for verso in dados["verses"]:
                texto = f'{verso["number"]} - {verso["text"]}'
                self.ui.listaVersiculos.addItem(texto)

            print("📖 Capítulo carregado")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao carregar capítulo:\n{str(e)}"
            )
    
    def versiculo_aleatorio(self):
        try:
            versao = self.ui.comboVersao.currentText()
            verso = self.api.get_random_verse(versao)

            texto = (
                f'{verso["book"]["name"]} '
                f'{verso["chapter"]}:{verso["number"]}\n\n'
                f'{verso["text"]}'
            )

            self.ui.txtResultado.setPlainText(texto)

        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

class AtasdeReuniao(TelaArrastavelBase):
    def __init__(self):
        super().__init__()  # Não passa parent aqui
        
        self.ui = Ui_telaPrincipal()
        self.ui.setupUi(self)
        
        # Configurações da janela
        self.setWindowIcon(QIcon("icons/icons/logoSpike.png"))
        self.setGeometry(150, 200, 973, 437)
        
        # Criar diretório para arquivos
        os.makedirs("arquivo", exist_ok=True)
        
        # CONECTAR TODOS OS BOTÕES
        self.conectar_botoes()
        
        # CONFIGURAR SHORTCUTS
        self.configurar_shortcuts_principal()
        
        # Inicializar variáveis para armazenar referências às janelas
        self.tela_grafico_de_presenca = None
        self.tela_login = None
        self.tela_catalogo_biblico = None
        
        print("✅ Tela Principal criada com arrasta e solta!")

    # FUNÇÕES DAS CONEXÕES DOS BOTÕES
    def conectar_botoes(self):
        try:
            # BOTÕES PRINCIPAIS
            self.ui.BTN_BUSCAR_MEMBRO.clicked.connect(self.abrir_tela_catalogo_biblico)
            self.ui.BTN_GERAR_RELATORIO.clicked.connect(self.abrir_tela_login)
            self.ui.BTN_GRAFICO_DE_PRESENCA.clicked.connect(self.abrir_tela_grafico_de_presenca)
            
            # CONECTAR ACTIONS DO MENU
            self.ui.actionLOGIN.triggered.connect(self.abrir_tela_login)
            
            print("✅ Botões da tela principal conectados!")
        except Exception as e:
            print(f"❌ Erro ao conectar botões: {e}")

    def configurar_shortcuts_principal(self):
        try:
            # F3 - Abrir tela do catálogo bíblico
            self.shortcut_equipamentos = QShortcut(QKeySequence(Qt.Key_F3), self)
            self.shortcut_equipamentos.activated.connect(self.abrir_tela_catalogo_biblico)
            
            # F4 - Abrir tela de gráficos
            self.shortcut_graficos = QShortcut(QKeySequence(Qt.Key_F4), self)
            self.shortcut_graficos.activated.connect(self.abrir_tela_grafico_de_presenca)
            
            # ESC - Fechar aplicação
            self.shortcut_esc = QShortcut(QKeySequence(Qt.Key_Escape), self)
            self.shortcut_esc.activated.connect(self.fechar_aplicacao)
            
            # F1 - Mostrar ajuda com atalhos
            self.shortcut_ajuda = QShortcut(QKeySequence(Qt.Key_F1), self)
            self.shortcut_ajuda.activated.connect(self.mostrar_atalhos_disponiveis)
            
            print("✅ Shortcuts configurados!")
        except Exception as e:
            print(f"❌ Erro ao configurar shortcuts: {e}")
    
    def fechar_aplicacao(self):
        reply = QMessageBox.question(self, "Confirmação", 
                                     "Deseja realmente sair do sistema?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            QCoreApplication.quit()
    
    def mostrar_atalhos_disponiveis(self):
        atalhos = """
    📋 ATALHOS DE TECLADO DISPONÍVEIS:
    F1 - Mostrar esta ajuda
    F3 - Catálogo Bíblico
    F4 - Tela de gráficos de presença
    ESC - Sair do sistema
    
    💡 Dica: Para arrastar as telas, clique e arraste em qualquer área vazia!
    Cada tela pode ser arrastada independentemente!
    """
        QMessageBox.information(self, "Atalhos do Sistema", atalhos)
    
    def abrir_tela_catalogo_biblico(self):
        try:
            # Fechar janela anterior se existir
            if self.tela_catalogo_biblico:
                self.tela_catalogo_biblico.close()
            self.tela_catalogo_biblico = CatalogoBiblico(self)
            self.tela_catalogo_biblico.show()
            print("✅ Tela Catálogo Bíblico aberta!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", 
                               f"Erro ao abrir catálogo bíblico: {str(e)}")

    def abrir_tela_grafico_de_presenca(self):
        try:
            # Fechar janela anterior se existir
            if self.tela_grafico_de_presenca:
                self.tela_grafico_de_presenca.close()
            
            self.tela_grafico_de_presenca = TelaGraficodePresenca(self)
            self.tela_grafico_de_presenca.show()
            print("✅ Tela de gráfico aberta!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", 
                               f"Erro ao abrir tela gráfico de presença: {str(e)}")
    
    def abrir_tela_login(self):
        try:
            # Fechar janela anterior se existir
            if self.tela_login:
                self.tela_login.close()
            self.tela_login = Login(self)
            self.tela_login.show()
            print("✅ Tela de login aberta!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", 
                               f"Erro ao abrir tela de login: {str(e)}")
    
    def closeEvent(self, event):
        # Fechar todas as janelas filhas
        if self.tela_grafico_de_presenca:
            self.tela_grafico_de_presenca.close()
        if self.tela_login:
            self.tela_login.close()
        if self.tela_catalogo_biblico:
            self.tela_catalogo_biblico.close()
        event.accept()


# EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        # Criar e mostrar tela de login
        login = Login()
        login.show()
        print("🔧 Tela Login criada - Teste arrastar ela agora!")
        
        # Executar a aplicação
        app.exec_()
        
        # Verificar se o login foi bem-sucedido
        if login.login_foi_bem_sucedido():
            print("✅ Login bem-sucedido! Abrindo tela principal...")
            
            # Criar e mostrar tela principal
            main_window = AtasdeReuniao()
            main_window.show()
            print("🔧 Tela Principal criada - Teste arrastar ela também!")
            print("💡 Dica: Abra outras telas (F3 Catálogo Bíblico), (F4 para gráfico), e arraste cada uma separadamente!")
            
            # Executar novamente para a tela principal
            sys.exit(app.exec_())
        else:
            print("❌ Login cancelado ou falhou.")
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        traceback.print_exc()
        sys.exit(1)