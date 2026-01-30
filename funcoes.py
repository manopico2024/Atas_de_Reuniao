from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox
import pandas as pd


class TelaArrastavelBase(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mouse_press_pos = None
        self._mouse_move_pos = None

    # Detecta clique do mouse
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._mouse_press_pos = event.globalPos()
            self._mouse_move_pos = self.pos()
        super().mousePressEvent(event)

    # Move a janela enquanto arrasta
    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self._mouse_press_pos:
            diff = event.globalPos() - self._mouse_press_pos
            self.move(self._mouse_move_pos + diff)
        super().mouseMoveEvent(event)

    # Reseta ao soltar o mouse
    def mouseReleaseEvent(self, event):
        self._mouse_press_pos = None
        super().mouseReleaseEvent(event)


class Tabelas(QtWidgets.QMainWindow):
    def carregar_tabela(self):
        # Abrir diálogo para selecionar o arquivo
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,  # Corrigido: Use self em vez de None
            "Abrir Arquivo de Tabela",
            "",
            "Arquivos Excel (*.xlsx *.xls);;Arquivos CSV (*.csv);;Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )

        if caminho_arquivo:
            try:
                # Detectar tipo do arquivo e ler com pandas
                if caminho_arquivo.endswith('.csv'):
                    df = pd.read_csv(caminho_arquivo)
                elif caminho_arquivo.endswith('.txt'):
                    # Tenta detectar o separador automaticamente
                    try:
                        df = pd.read_csv(caminho_arquivo, sep=None, engine='python')
                    except Exception:
                        # Caso falhe, usa separador padrão de tabulação
                        df = pd.read_csv(caminho_arquivo, sep='\t')
                else:
                    # Para arquivos Excel
                    df = pd.read_excel(caminho_arquivo)

                # Verificar se existe um QTableWidget chamado 'tableWidget' na classe
                if hasattr(self, 'tableWidget'):
                    # Limpar tabela antes de preencher
                    self.tableWidget.clear()
                    self.tableWidget.setRowCount(df.shape[0])
                    self.tableWidget.setColumnCount(df.shape[1])
                    self.tableWidget.setHorizontalHeaderLabels(df.columns.astype(str))  # Converter para string

                    # Inserir os dados na tabela
                    for linha in range(df.shape[0]):
                        for coluna in range(df.shape[1]):
                            valor = df.iat[linha, coluna]
                            # Converter para string se não for None
                            item_texto = str(valor) if valor is not None else ""
                            item = QTableWidgetItem(item_texto)
                            self.tableWidget.setItem(linha, coluna, item)

                    # Exibir a tabela se existir um groupBox_tabela
                    if hasattr(self, 'groupBox_tabela'):
                        self.groupBox_tabela.show()
                    
                    QMessageBox.information(self, "Sucesso", 
                                          f"Tabela carregada com sucesso!\n"
                                          f"Linhas: {df.shape[0]}, Colunas: {df.shape[1]}")
                else:
                    QMessageBox.warning(self, "Aviso", 
                                      "O objeto 'tableWidget' não foi encontrado na classe.")

            except FileNotFoundError:
                QMessageBox.critical(self, "Erro", "Arquivo não encontrado.")
            except pd.errors.EmptyDataError:
                QMessageBox.critical(self, "Erro", "O arquivo está vazio.")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao carregar tabela:\n{str(e)}")