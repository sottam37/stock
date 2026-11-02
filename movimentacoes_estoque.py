import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt


class MovimentacoesEstoqueApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Movimentações de Estoque")
        self.setFixedSize(900, 600)

        # --- Filtros ---
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Todos", "Entrada", "Saída"])

        self.input_busca = QLineEdit()
        self.input_busca.setPlaceholderText("Buscar por nome do produto...")

        self.btn_buscar = QPushButton("Filtrar")
        self.btn_buscar.clicked.connect(self.carregar_movimentacoes)

        # --- Layout dos filtros ---
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Tipo:"))
        filtro_layout.addWidget(self.combo_tipo)
        filtro_layout.addWidget(QLabel("Produto:"))
        filtro_layout.addWidget(self.input_busca)
        filtro_layout.addWidget(self.btn_buscar)

        # --- Tabela ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Tipo", "ID Movimento", "Produto", "Quantidade", "Data", "Valor Unitário"
        ])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setStyleSheet("alternate-background-color: #f5f5f5;")

        # --- Layout principal ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(filtro_layout)
        layout_principal.addWidget(self.tabela)

        self.setLayout(layout_principal)

        # Carrega os dados iniciais
        self.carregar_movimentacoes()

    # -------------------------------------------------------------
    # Conexão com o banco
    # -------------------------------------------------------------
    def criar_conexao(self):
        """Cria e retorna uma conexão com o banco."""
        try:
            conexao = pymysql.connect(
                host="192.168.100.33",
                user="root",
                password="12345678",  # ⚠️ altere conforme seu ambiente
                database="stock",
                port=3306,
                cursorclass=DictCursor,
                autocommit=True
            )
            return conexao
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro de conexão", f"Não foi possível conectar ao banco:\n{e}")
            return None

    # -------------------------------------------------------------
    # Carregar movimentações
    # -------------------------------------------------------------
    def carregar_movimentacoes(self):
        """Carrega as movimentações da view com base nos filtros."""
        tipo = self.combo_tipo.currentText()
        filtro_nome = self.input_busca.text().strip()

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                query = "SELECT * FROM movimentacoes_estoque WHERE 1=1"
                params = []

                if tipo != "Todos":
                    query += " AND tipo_movimentacao = %s"
                    params.append(tipo)

                if filtro_nome:
                    query += " AND nome_produto LIKE %s"
                    params.append(f"%{filtro_nome}%")

                query += " ORDER BY data_movimentacao DESC"

                cursor.execute(query, params)
                registros = cursor.fetchall()

                self.tabela.setRowCount(len(registros))
                for i, row in enumerate(registros):
                    self.tabela.setItem(i, 0, QTableWidgetItem(row["tipo_movimentacao"]))
                    self.tabela.setItem(i, 1, QTableWidgetItem(str(row["id_movimento"])))
                    self.tabela.setItem(i, 2, QTableWidgetItem(row["nome_produto"]))
                    self.tabela.setItem(i, 3, QTableWidgetItem(str(row["quantidade"])))
                    self.tabela.setItem(i, 4, QTableWidgetItem(str(row["data_movimentacao"])))
                    valor = row["valor_unitario"] if row["valor_unitario"] is not None else "-"
                    self.tabela.setItem(i, 5, QTableWidgetItem(str(valor)))

                self.tabela.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar movimentações:\n{e}")
        finally:
            conexao.close()


# -------------------------------------------------------------
# Execução direta
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = MovimentacoesEstoqueApp()
    janela.show()
    sys.exit(app.exec_())
