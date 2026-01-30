# IMPORTANDO AS LIBS DE INTERFACE GRÁFICA
from PyQt5.QtWidgets import (QDialog, QMessageBox, QMainWindow, QApplication, 
                             QTreeWidgetItem, QVBoxLayout, QTextEdit, QPushButton, 
                             QShortcut, QHBoxLayout, QComboBox, QLabel, QInputDialog, 
                             QTableWidget, QTableWidgetItem, QFrame, QFileDialog, 
                             QProgressDialog, QWidget, QTreeWidget, QLineEdit)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap
from PyQt5.QtCore import Qt, QCoreApplication, QPoint, QTimer
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QKeySequence, QPixmap
import pandas as pd
import shutil
from datetime import datetime
from PyQt5 import QtCore
import traceback
# IMPORTANDO AS LIBS DE BANCO DE DADOS
import sqlite3
# IMPORTANDO AS LIBS DE SISTEMA
import sys
import os
from pathlib import Path
import json
import logging

# IMPORTANDO AS TELAS (ajuste os caminhos conforme necessário)
# from telaLogin import Ui_telaLogin
# from telaOrdemservicos import Ui_telaOrdeservicos
# from telaConsultacliente import Ui_telaConsultacliente
# from telaPrincipal import Ui_telaPrincipal
# from telaCliente import Ui_telaPedidos
# from telaRegistrofuncs import Ui_telaFunrcionario

# Classe DatabaseManager (mantida igual)
class DatabaseManager:
    def __init__(self, base_path="database"):
        self.base_path = base_path
        self.setup_estrutura_pastas()
        self.setup_logging()
        self.connections = {}
        self.cursors = {}
    
    def add_pedidos_from_txt(self, arquivo_txt, db_name="pedidos", loja=None):
        try:
            with open(arquivo_txt, 'r', encoding='utf-8') as file:
                linhas = file.readlines()
            
            pedidos_adicionados = 0
            for numero_linha, linha in enumerate(linhas, 1):
                linha = linha.strip()
                if not linha or linha.startswith('#'):  # Ignora linhas vazias e comentários
                    continue
                    
                try:
                    dados = linha.split(',')
                    if len(dados) == 3:
                        tipo = dados[0].strip()
                        valor = float(dados[1].strip())
                        total = float(dados[2].strip())
                        
                        # Adiciona ao banco
                        if self.add_pedido_simples(db_name, tipo, valor, total, loja):
                            pedidos_adicionados += 1
                        else:
                            self.log_error(f"Erro ao adicionar pedido da linha {numero_linha}")
                            
                    else:
                        self.log_error(f"Formato inválido na linha {numero_linha}: {linha}")
                        
                except ValueError as e:
                    self.log_error(f"Erro de conversão na linha {numero_linha}: {e}")
                except Exception as e:
                    self.log_error(f"Erro na linha {numero_linha}: {e}")
            
            self.log_success(f"Processamento concluído! {pedidos_adicionados} pedidos adicionados.")
            return pedidos_adicionados
            
        except FileNotFoundError:
            self.log_error(f"Arquivo não encontrado: {arquivo_txt}")
            return 0
        except Exception as e:
            self.log_error(f"Erro ao processar arquivo: {e}")
            return 0

    def add_pedido_simples(self, db_name, tipo, valores, totais, loja=None):
        """Adiciona um pedido simples ao banco"""
        try:
            if db_name not in self.connections:
                self.conectar_db(db_name, loja)
            
            query = "INSERT INTO pedidos (tipo, valores, totais) VALUES (?, ?, ?)"
            params = (tipo, valores, totais)
            result = self.executar_query(db_name, query, params)
            
            if result is not None:
                self.log_success(f"Pedido '{tipo}' adicionado com sucesso!")
                return True
            return False
        except Exception as e:
            self.log_error(f"Erro ao adicionar pedido: {e}")
            return False

    def exportar_pedidos_para_txt(self, db_name, arquivo_saida, loja=None):
        try:
            if db_name not in self.connections:
                self.conectar_db(db_name, loja)
            
            query = "SELECT tipo, valores, totais FROM pedidos ORDER BY id"
            pedidos = self.executar_query(db_name, query)
            
            with open(arquivo_saida, 'w', encoding='utf-8') as file:
                file.write("# Arquivo de pedidos exportado\n")
                file.write("# Formato: tipo,valor,total\n\n")
                
                for pedido in pedidos:
                    linha = f"{pedido[0]},{pedido[1]:.2f},{pedido[2]:.2f}\n"
                    file.write(linha)
            
            self.log_success(f"Pedidos exportados para: {arquivo_saida}")
            return True
        except Exception as e:
            self.log_error(f"Erro ao exportar pedidos: {e}")
            return False
    
    def setup_estrutura_pastas(self):
        pastas = [
            'database/lojas', 'database/backups',
            'logs', 'arquivo', 'relatorios',
            'imagens', 'imagens/clientes',
            'imagens/funcionarios', 'imagens/equipamentos']
        for pasta in pastas:
            os.makedirs(pasta, exist_ok=True)
            print(f"✅ Pasta '{pasta}' criada/verificada")
    
    def setup_logging(self):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"database_{datetime.now().strftime('%Y%m%d')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()]  )
        self.logger = logging.getLogger(__name__)
    
    def conectar_db(self, db_name, loja=None):
        if loja:
            db_path = os.path.join(self.base_path, "lojas", f"{loja}_{db_name}.db")
        else:
            db_path = os.path.join(self.base_path, f"{db_name}.db")
        try:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.connections[db_name] = sqlite3.connect(db_path)
            self.cursors[db_name] = self.connections[db_name].cursor()
            self.log_success(f"Conectado ao banco: {db_name}" + (f" (Loja: {loja})" if loja else ""))
            return True
        except sqlite3.Error as e:
            self.log_error(f"Erro ao conectar {db_name}", e)
            return False

    def get_queries_da_loja(self, loja=None):
        queries = {}
        queries = self.carregar_estrutura_lojas()
        if loja and loja != "Principal":
            queries_loja = self.carregar_estrutura_loja_especifica(loja)
            if queries_loja:
                queries.update(queries_loja)
        return queries

    def carregar_estrutura_lojas(self):
        queries = {}
        lojas_path = Path(self.base_path) / "lojas"
        if not lojas_path.exists():
            return queries
        for arquivo in lojas_path.glob("*.json"):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    estruturas = json.load(f)
                    for tabela, estrutura in estruturas.items():
                        if isinstance(estrutura, str):
                            queries[tabela] = estrutura
                        else:
                            queries[tabela] = self.criar_query_from_estrutura(tabela, estrutura)
                self.log_success(f"Estrutura carregada de {arquivo.name}")
            except Exception as e:
                self.log_error(f"Erro ao carregar estrutura de {arquivo.name}", e)
        return queries

    def carregar_estrutura_loja_especifica(self, loja):
        queries = {}
        loja_path = Path(self.base_path) / "lojas" / f"{loja}_estrutura.json"
        if loja_path.exists():
            try:
                with open(loja_path, 'r', encoding='utf-8') as f:
                    estruturas = json.load(f)
                    for tabela, estrutura in estruturas.items():
                        if isinstance(estrutura, str):
                            queries[tabela] = estrutura
                        else:
                            queries[tabela] = self.criar_query_from_estrutura(tabela, estrutura)
                self.log_success(f"Estrutura específica carregada para loja {loja}")
            except Exception as e:
                self.log_error(f"Erro ao carregar estrutura da loja {loja}", e)
        return queries

    def criar_query_from_estrutura(self, nome_tabela, estrutura):
        colunas = []
        for coluna in estrutura.get('colunas', []):
            coluna_sql = f"{coluna['nome']} {coluna['tipo']}"
            if coluna.get('primary_key'):
                coluna_sql += " PRIMARY KEY"
            if coluna.get('autoincrement'):
                coluna_sql += " AUTOINCREMENT"
            if coluna.get('not_null'):
                coluna_sql += " NOT NULL"
            if coluna.get('default') is not None:
                default_val = coluna['default']
                if isinstance(default_val, str) and not default_val.isdigit():
                    default_val = f"'{default_val}'"
                coluna_sql += f" DEFAULT {default_val}"
            colunas.append(coluna_sql)
        colunas_sql = ", ".join(colunas)
        return f'CREATE TABLE IF NOT EXISTS "{nome_tabela}" ({colunas_sql})'

    def criar_todas_tabelas(self, db_name, loja=None):
        if db_name not in self.connections:
            self.conectar_db(db_name, loja)
        try:
            queries = self.get_queries_da_loja(loja)
            if not queries:
                self.log_error(f"Nenhuma estrutura encontrada na pasta lojas para {db_name}")
                return False 
            cursor = self.cursors[db_name]
            for tabela, query in queries.items():
                cursor.execute(query)
            self.connections[db_name].commit()
            self.log_success(f"Tabelas criadas/verificadas em {db_name} usando estrutura da loja!")
            return True
        except sqlite3.Error as e:
            self.log_error(f"Erro ao criar tabelas em {db_name}", e)
            return False
    
    def executar_query(self, db_name, query, params=()):
        if db_name not in self.connections:
            self.conectar_db(db_name)
        try:
            cursor = self.cursors[db_name]
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connections[db_name].commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            self.log_error(f"Erro ao executar query em {db_name}", e)
            return None
    
    def listar_bancos(self):
        path = Path(self.base_path)
        dbs = []
        dbs.extend([f.stem for f in path.glob("*.db")])
        lojas_path = path / "lojas"
        if lojas_path.exists():
            dbs.extend([f.stem for f in lojas_path.glob("*.db")])
        return dbs
    
    def listar_lojas(self):
        lojas_path = Path(self.base_path) / "lojas"
        if lojas_path.exists():
            arquivos = list(lojas_path.glob("*.db"))
            lojas = set()
            for arquivo in arquivos:
                partes = arquivo.stem.split('_')
                if len(partes) >= 2:
                    lojas.add(partes[0])
            return list(lojas)
        return ["Principal"]
    
    def backup_database(self, db_name, loja=None):
        if loja:
            backup_name = f"{loja}_{db_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            original_path = os.path.join(self.base_path, "lojas", f"{loja}_{db_name}.db")
        else:
            backup_name = f"{db_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            original_path = os.path.join(self.base_path, f"{db_name}.db")    
        backup_path = os.path.join(self.base_path, "backups", backup_name)
        try:
            if db_name in self.connections:
                self.connections[db_name].close()
            if os.path.exists(original_path):
                shutil.copy2(original_path, backup_path)
                self.log_success(f"Backup criado: {backup_path}")
                return True
            else:
                self.log_error(f"Arquivo original não encontrado para {db_name}")
                return False
        except Exception as e:
            self.log_error(f"Erro ao criar backup de {db_name}", e)
            return False
    
    def fechar_todas_conexoes(self):
        for name, conn in self.connections.items():
            try:
                conn.close()
            except:
                pass
        self.connections.clear()
        self.cursors.clear()
        self.log_success("Todas as conexões fechadas")
    
    # LOG DE INFORMAÇÕES, ERROS, AVISOS E SUCESSOS
    def log_info(self, mensagem):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"✅ [{timestamp}] INFO: {mensagem}")
        self.logger.info(mensagem)

    def log_error(self, mensagem, erro=None):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if erro:
            print(f"❌ [{timestamp}] ERRO: {mensagem} - Detalhes: {str(erro)}")
            self.logger.error(f"{mensagem} - Detalhes: {str(erro)}")
        else:
            print(f"❌ [{timestamp}] ERRO: {mensagem}")
            self.logger.error(mensagem)

    def log_warning(self, mensagem):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"⚠️ [{timestamp}] AVISO: {mensagem}")
        self.logger.warning(mensagem)

    def log_success(self, mensagem):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"🎉 [{timestamp}] SUCESSO: {mensagem}")
        self.logger.info(f"SUCESSO: {mensagem}")

class sqlite_db:
    def __init__(self, db_name="funcionarios.db", loja=None):
        self.db_manager = DatabaseManager()
        self.db_name = db_name
        self.loja = loja
        self.db_manager.conectar_db(db_name, loja)
        self.db_manager.criar_todas_tabelas(db_name, loja)
    
    @property
    def cursor(self):
        return self.db_manager.cursors.get(self.db_name)
    
    @property
    def conn(self):
        return self.db_manager.connections.get(self.db_name)
    
    def open(self, db_name=None, loja=None):
        if db_name:
            self.db_name = db_name
        if loja:
            self.loja = loja
        return self.db_manager.conectar_db(self.db_name, self.loja)
    
    # FUNÇÕES DE FUNCIONÁRIOS - CORRIGIDAS
    def add_funcs(self, nome, endereco, documento, complemento, admin=1):
        try:
            query = "INSERT INTO funcs (nome, endereco, documento, complemento, admin) VALUES (?, ?, ?, ?, ?)"
            params = (nome, endereco, documento, complemento, admin)
            result = self.db_manager.executar_query(self.db_name, query, params)
            if result is not None:
                self.db_manager.log_success("Funcionário adicionado com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao salvar funcionário", e)
            return False 

    def buscar_funcs(self, filtro=""):
        try:
            if filtro:
                query = '''SELECT * FROM funcs WHERE nome LIKE ? OR endereco LIKE ? OR documento LIKE ? OR id LIKE ? OR complemento LIKE ?'''
                parametro = f'%{filtro}%'
                return self.db_manager.executar_query(self.db_name, query, (parametro, parametro, parametro, parametro, parametro))
            else:
                query = 'SELECT * FROM funcs ORDER BY nome'
                return self.db_manager.executar_query(self.db_name, query)
        except Exception as e:
            self.db_manager.log_error("Erro na busca de funcionários", e)
            return []
        
    def excluir_func(self, id_func):
        try:
            query = "DELETE FROM funcs WHERE id = ?"
            result = self.db_manager.executar_query(self.db_name, query, (id_func,))
            if result is not None:
                self.db_manager.log_success("Funcionário excluído com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao excluir funcionário", e)
            return False

    # FUNÇÕES DE CLIENTES
    def add_Cliente(self, nome, endereco, documento, complemento, admin=1):
        try:
            query = "INSERT INTO clientes (nome, endereco, documento, complemento, admin) VALUES (?, ?, ?, ?, ?)"
            params = (nome, endereco, documento, complemento, admin)
            result = self.db_manager.executar_query(self.db_name, query, params)
            if result is not None:
                self.db_manager.log_success("Cliente adicionado com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao salvar cliente", e)
            return False

    def buscar_clientes(self, filtro=""):
        try:
            if filtro:
                query = '''SELECT * FROM clientes WHERE nome LIKE ? OR endereco LIKE ? OR documento LIKE ? OR id LIKE ? OR complemento LIKE ?'''
                parametro = f'%{filtro}%'
                return self.db_manager.executar_query(self.db_name, query, (parametro, parametro, parametro, parametro, parametro))
            else:
                query = 'SELECT * FROM clientes ORDER BY nome'
                return self.db_manager.executar_query(self.db_name, query)
        except Exception as e:
            self.db_manager.log_error("Erro na busca de clientes", e)
            return []

    def excluir_cliente(self, id_cliente):
        try:
            query = "DELETE FROM clientes WHERE id = ?"
            result = self.db_manager.executar_query(self.db_name, query, (id_cliente,))
            if result is not None:
                self.db_manager.log_success("Cliente excluído com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao excluir cliente", e)
            return False

    # FUNÇÕES DE ORDEM DE SERVIÇO
    def add_ordem_servico(self, tipo_equipamento, modelo_equipamento, numero_serie, 
                        numero_placa, revisao_placa, etiqueta_servico, valor_reparo,
                        limpeza, troca_tela, troca_bateria, troca_cpu, formatacao,
                        troca_gpu, troca_psu, backup_windows, troca_teclado,
                        troca_trackpad, regravacao_bios, troca_memoria, regravacao_sio,
                        com_backup, sem_backup, observacoes=None, loja="Principal"):
        try:
            query = """INSERT INTO equipamentos
                (tipo_equipamento, modelo_equipamento, numero_serie, numero_placa, 
                revisao_placa, etiqueta_servico, valor_reparo,
                limpeza, troca_tela, troca_bateria, troca_cpu, formatacao,
                troca_gpu, troca_psu, backup_windows, troca_teclado,
                troca_trackpad, regravacao_bios, troca_memoria, regravacao_sio,
                com_backup, sem_backup, observacoes, loja) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            params = (tipo_equipamento, modelo_equipamento, numero_serie, numero_placa,
                     revisao_placa, etiqueta_servico, valor_reparo,
                     limpeza, troca_tela, troca_bateria, troca_cpu, formatacao,
                     troca_gpu, troca_psu, backup_windows, troca_teclado,
                     troca_trackpad, regravacao_bios, troca_memoria, regravacao_sio,
                     com_backup, sem_backup, observacoes, loja)
            result = self.db_manager.executar_query(self.db_name, query, params)
            if result is not None:
                self.db_manager.log_success("Ordem de serviço adicionada com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao salvar ordem de serviço", e)
            return False

    def buscar_equipamentos(self, filtro="", loja=None):
        try:
            if filtro:
                if loja:
                    query = '''SELECT * FROM equipamentos WHERE (tipo_equipamento LIKE ? OR modelo_equipamento LIKE ? OR numero_serie LIKE ? OR id LIKE ?) AND loja = ?'''
                    parametro = f'%{filtro}%'
                    return self.db_manager.executar_query(self.db_name, query, (parametro, parametro, parametro, parametro, loja))
                else:
                    query = '''SELECT * FROM equipamentos WHERE tipo_equipamento LIKE ? OR modelo_equipamento LIKE ? OR numero_serie LIKE ? OR id LIKE ?'''
                    parametro = f'%{filtro}%'
                    return self.db_manager.executar_query(self.db_name, query, (parametro, parametro, parametro, parametro))
            else:
                if loja:
                    query = 'SELECT * FROM equipamentos WHERE loja = ? ORDER BY data_criacao DESC'
                    return self.db_manager.executar_query(self.db_name, query, (loja,))
                else:
                    query = 'SELECT * FROM equipamentos ORDER BY data_criacao DESC'
                    return self.db_manager.executar_query(self.db_name, query)
        except Exception as e:
            self.db_manager.log_error("Erro na busca de ordens de serviço", e)
            return []

    def excluir_ordem_servico(self, id_ordem):
        try:
            query = "DELETE FROM equipamentos WHERE id = ?"
            result = self.db_manager.executar_query(self.db_name, query, (id_ordem,))
            if result is not None:
                self.db_manager.log_success("Ordem de serviço excluída com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao excluir ordem de serviço", e)
            return False

    # FUNÇÕES DE PEDIDOS
    def buscar_pedidos(self, filtro=""):
        try:
            if filtro:
                query = '''SELECT * FROM pedidos WHERE tipo LIKE ? OR valores LIKE ? OR totais LIKE ? OR id LIKE ?'''
                parametro = f'%{filtro}%'
                return self.db_manager.executar_query(self.db_name, query, (parametro, parametro, parametro, parametro))
            else:
                query = 'SELECT * FROM pedidos ORDER BY tipo'
                return self.db_manager.executar_query(self.db_name, query)
        except Exception as e:
            self.db_manager.log_error("Erro na busca de pedidos", e)
            return []

    def add_pedido(self, tipo, valores, totais, loja=None):
        try:
            query = "INSERT INTO pedidos (tipo, valores, totais, loja) VALUES (?, ?, ?, ?)"
            params = (tipo, valores, totais, loja or self.loja)
            result = self.db_manager.executar_query(self.db_name, query, params)
            if result is not None:
                self.db_manager.log_success("Pedido adicionado com sucesso!")
                return True
            return False
        except Exception as e:
            self.db_manager.log_error("Erro ao salvar pedido", e)
            return False

    # FECHAR CONEXÃO
    def fechar_conexao(self):
        self.db_manager.fechar_todas_conexoes()

    # NOVAS FUNÇÕES PARA MULTIPLOS BANCOS
    def listar_lojas(self):
        return self.db_manager.listar_lojas()
    
    def trocar_loja(self, nova_loja):
        self.loja = nova_loja
        return self.open(self.db_name, nova_loja)

    def fazer_backup(self):
        return self.db_manager.backup_database(self.db_name, self.loja)

# CORREÇÃO DA CLASSE PedidosCliente
class PedidosCliente(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.ui = Ui_telaPedidos()  # Descomente quando tiver a UI
        # self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon(":/icons/icons/logoSpike.png"))
        self.setGeometry(300, 150, 800, 600)

        # Inicializa os bancos
        self.db_clientes = sqlite_db("clientes")
        self.db_pedidos = sqlite_db("pedidos")

        # Criar interface básica se a UI não estiver disponível
        self.setup_interface_basica()
        self.configurar_tree_widget_pedidos()
        self.carregar_pedidos_salvos()

    def setup_interface_basica(self):
        """Cria interface básica se a UI não estiver disponível"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Botões
        button_layout = QHBoxLayout()
        self.btn_fechar = QPushButton("Fechar")
        self.btn_cliente = QPushButton("Clientes")
        self.btn_produtos = QPushButton("Carregar Pedidos")
        self.btn_salvar = QPushButton("Salvar Pedidos")
        
        button_layout.addWidget(self.btn_cliente)
        button_layout.addWidget(self.btn_produtos)
        button_layout.addWidget(self.btn_salvar)
        button_layout.addWidget(self.btn_fechar)
        
        # Tabela
        self.tree_widget = QTreeWidget()
        
        layout.addLayout(button_layout)
        layout.addWidget(self.tree_widget)
        
        # Conectar botões
        self.btn_fechar.clicked.connect(self.fechar_tela_Pedidos)
        self.btn_cliente.clicked.connect(self.pesquisar_clientes)
        self.btn_produtos.clicked.connect(self.carregar_pedidos)
        self.btn_salvar.clicked.connect(self.salvar_pedidos)

    def configurar_tree_widget_pedidos(self):
        colunas = ["ID", "Tipo", "Valor", "Total"]
        self.tree_widget.setColumnCount(len(colunas))
        self.tree_widget.setHeaderLabels(colunas)
        for i in range(len(colunas)):
            self.tree_widget.setColumnWidth(i, [50, 200, 150, 150][i])
        self.tree_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def carregar_pedidos(self):
        """Função corrigida para carregar pedidos de arquivos"""
        try:
            caminho_arquivo, _ = QFileDialog.getOpenFileName(
                self,
                "Abrir Arquivo de Tabela",
                "",
                "Arquivos Excel (*.xlsx *.xls);;Arquivos CSV (*.csv);;Arquivos de Texto (*.txt);;Bancos SQLite (*.db);;Todos os Arquivos (*)"
            )

            if not caminho_arquivo or not os.path.exists(caminho_arquivo):
                return

            # Limpar tabela atual
            self.tree_widget.clear()

            try:
                # Detectar tipo do arquivo e ler com pandas
                if caminho_arquivo.endswith('.csv'):
                    df = pd.read_csv(caminho_arquivo, encoding='utf-8')
                elif caminho_arquivo.endswith('.txt'):
                    try:
                        df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8')
                    except Exception:
                        df = pd.read_csv(caminho_arquivo, sep='\t', encoding='utf-8')
                elif caminho_arquivo.endswith('.db'):
                    conn = sqlite3.connect(caminho_arquivo)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tabelas = [t[0] for t in cursor.fetchall()]

                    if not tabelas:
                        QMessageBox.warning(self, "Banco vazio", "Nenhuma tabela encontrada no banco de dados.")
                        conn.close()
                        return

                    tabela_nome, ok = QInputDialog.getItem(
                        self, 
                        "Selecionar Tabela", 
                        "Escolha uma tabela para carregar:", 
                        tabelas, 
                        0, 
                        False
                    )
                    
                    if not ok or not tabela_nome:
                        conn.close()
                        return

                    df = pd.read_sql_query(f"SELECT * FROM {tabela_nome}", conn)
                    conn.close()
                else:
                    df = pd.read_excel(caminho_arquivo)

                # Configurar colunas
                colunas = [str(c) for c in df.columns]
                self.tree_widget.setColumnCount(len(colunas))
                self.tree_widget.setHeaderLabels(colunas)

                # Adicionar dados
                for index, row in df.iterrows():
                    item = QTreeWidgetItem()
                    for col_idx, value in enumerate(row):
                        item.setText(col_idx, str(value) if pd.notna(value) else "")
                    self.tree_widget.addTopLevelItem(item)

                QMessageBox.information(self, "Sucesso", f"Dados carregados: {len(df)} registros")

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar arquivo: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro geral: {str(e)}")

    def salvar_pedidos(self):
        """Função corrigida para salvar pedidos"""
        try:
            if self.tree_widget.topLevelItemCount() == 0:
                QMessageBox.warning(self, "Aviso", "Não há dados para salvar!")
                return

            file_name, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Salvar Pedidos",
                f"pedidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "Arquivos CSV (*.csv);;Arquivos de Texto (*.txt);;Todos os Arquivos (*)")

            if not file_name:
                return

            # Determinar extensão do arquivo
            if selected_filter == "Arquivos CSV (*.csv)" and not file_name.lower().endswith('.csv'):
                file_name += '.csv'
            elif selected_filter == "Arquivos de Texto (*.txt)" and not file_name.lower().endswith('.txt'):
                file_name += '.txt'

            with open(file_name, 'w', encoding='utf-8') as file:
                # Escrever cabeçalho
                header = []
                for col in range(self.tree_widget.columnCount()):
                    header.append(self.tree_widget.headerItem().text(col))
                file.write(",".join(header) + "\n")

                # Escrever dados
                for row in range(self.tree_widget.topLevelItemCount()):
                    item = self.tree_widget.topLevelItem(row)
                    row_data = []
                    for col in range(self.tree_widget.columnCount()):
                        row_data.append(item.text(col))
                    file.write(",".join(row_data) + "\n")

            QMessageBox.information(self, "Sucesso", f"Arquivo salvo em: {file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo: {str(e)}")

    def pesquisar_clientes(self):
        try:
            # Implementar pesquisa de clientes
            clientes = self.db_clientes.buscar_clientes()
            self.carregar_pedidos_salvos()
        except Exception as e:
            print(f"Erro na pesquisa: {e}")

    def carregar_pedidos_salvos(self, pedidos=None):
        try:
            self.tree_widget.clear()
            if pedidos is None:
                pedidos = self.db_pedidos.buscar_pedidos()

            colunas = ["ID", "Tipo", "Valor", "Total"]
            self.tree_widget.setColumnCount(len(colunas))
            self.tree_widget.setHeaderLabels(colunas)
            
            if pedidos:
                for pedido in pedidos:
                    item = QTreeWidgetItem([str(pedido[0]), pedido[1], str(pedido[2]), str(pedido[3])])
                    self.tree_widget.addTopLevelItem(item)
        except Exception as e:
            print(f"Erro ao preencher tabela de pedidos: {e}")

    def fechar_tela_Pedidos(self):
        self.close()

# CORREÇÃO DA CLASSE CadastrarFunionarios (removendo duplicação)
class CadastrarFunionarios(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.ui = Ui_telaFunrcionario()  # Descomente quando tiver a UI
        # self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon(":/icons/icons/logoSpike.png"))
        self.setGeometry(300, 150, 800, 600)
        
        # Criar interface básica
        self.setup_interface_basica()
        self.configurar_tree_widget_funcs()
        self.carregar_funcs()
        self.db_manager = DatabaseManager()
        self.db_funcs = sqlite_db("funcionarios")

    def setup_interface_basica(self):
        """Cria interface básica para funcionários"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Área de formulário
        form_layout = QVBoxLayout()
        
        # Campos de entrada
        self.txt_nome = QLineEdit()
        self.txt_endereco = QLineEdit()
        self.txt_documento = QLineEdit()
        self.txt_complemento = QLineEdit()
        
        form_layout.addWidget(QLabel("Nome:"))
        form_layout.addWidget(self.txt_nome)
        form_layout.addWidget(QLabel("Endereço:"))
        form_layout.addWidget(self.txt_endereco)
        form_layout.addWidget(QLabel("Documento:"))
        form_layout.addWidget(self.txt_documento)
        form_layout.addWidget(QLabel("Complemento:"))
        form_layout.addWidget(self.txt_complemento)
        
        # Botões
        button_layout = QHBoxLayout()
        self.btn_salvar = QPushButton("Salvar")
        self.btn_limpar = QPushButton("Limpar")
        self.btn_fechar = QPushButton("Fechar")
        
        button_layout.addWidget(self.btn_salvar)
        button_layout.addWidget(self.btn_limpar)
        button_layout.addWidget(self.btn_fechar)
        
        # Tabela
        self.tree_widget = QTreeWidget()
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        layout.addWidget(self.tree_widget)
        
        # Conectar botões
        self.btn_salvar.clicked.connect(self.salvar_funcionario)
        self.btn_limpar.clicked.connect(self.limpar_campos_funcs)
        self.btn_fechar.clicked.connect(self.close)

    def configurar_tree_widget_funcs(self):
        colunas = ["ID", "Nome", "Endereço", "Documento", "Complemento", "Administrador"]
        self.tree_widget.setColumnCount(6)
        self.tree_widget.setHeaderLabels(colunas)
        for i in range(6):
            self.tree_widget.setColumnWidth(i, [50, 200, 250, 120, 200, 100][i])
        self.tree_widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def salvar_funcionario(self):
        nome = self.txt_nome.text().strip()
        endereco = self.txt_endereco.text().strip()
        documento = self.txt_documento.text().strip()
        complemento = self.txt_complemento.text().strip()
        
        if not all([nome, endereco, documento, complemento]):
            QMessageBox.warning(self, "Campos Obrigatórios", "Preencha todos os campos!")
            return
            
        if self.db_funcs.add_funcs(nome, endereco, documento, complemento, 1):
            QMessageBox.information(self, "Sucesso", "Funcionário salvo!")
            self.limpar_campos_funcs()
            self.carregar_funcs()
            self.criar_arquivo_funcionarios()
        else:
            QMessageBox.critical(self, "Erro", "Erro ao salvar funcionário!")

    def criar_arquivo_funcionarios(self):
        """Função única - removida a duplicação"""
        try:
            dados = f"""
            NOME: {self.txt_nome.text()}
            ENDERECO: {self.txt_endereco.text()}
            DOCUMENTO: {self.txt_documento.text()}
            COMPLEMENTO: {self.txt_complemento.text()}
            DATA: {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
            
            os.makedirs("arquivo", exist_ok=True)
            with open('arquivo/funcionarios.txt', 'w', encoding='utf-8') as f:
                f.write(dados)
        except Exception as e:
            print(f"Erro ao criar arquivo: {e}")

    def carregar_funcs(self, filtro=""):
        try:
            self.tree_widget.clear()
            resultado = self.db_funcs.buscar_funcs(filtro)
            if resultado:
                for func in resultado:
                    item = QTreeWidgetItem([str(func[i]) for i in range(5)] + ["Sim" if func[5] == 1 else "Não"])
                    for i in range(6):
                        item.setForeground(i, QtGui.QBrush(QtGui.QColor("black")))
                    self.tree_widget.addTopLevelItem(item)
        except Exception as e:
            print(f"Erro ao carregar funcionários: {e}")

    def limpar_campos_funcs(self):
        self.txt_nome.clear()
        self.txt_endereco.clear()
        self.txt_documento.clear()
        self.txt_complemento.clear()

# Classe principal (exemplo simplificado)
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Principal")
        self.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Teste das classes corrigidas
    # main_window = MainApp()
    # main_window.show()
    
    # Teste da tela de pedidos
    pedidos_window = PedidosCliente()
    pedidos_window.show()
    
    # Teste da tela de funcionários
    # func_window = CadastrarFunionarios()
    # func_window.show()
    
    sys.exit(app.exec_())