import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QPushButton, QVBoxLayout, QFormLayout, QMessageBox
)


class EntradasEstoqueApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Entradas de Estoque")
        self.setFixedSize(500, 500)

        # --- Campos do formulário ---
        self.combo_produto = QComboBox()
        self.input_quantidade = QSpinBox()
        self.input_quantidade.setMaximum(100000)
        self.input_quantidade.setMinimum(1)

        self.input_custo_unitario = QDoubleSpinBox()
        self.input_custo_unitario.setPrefix("R$ ")
        self.input_custo_unitario.setDecimals(2)
        self.input_custo_unitario.setMaximum(999999.99)

        self.input_observacao = QTextEdit()
        self.input_observacao.setPlaceholderText("Observações (opcional)")

        # --- Botões ---
        self.btn_salvar = QPushButton("Registrar Entrada")
        self.btn_salvar.clicked.connect(self.registrar_entrada)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)

        # --- Layout do formulário ---
        form_layout = QFormLayout()
        form_layout.addRow("Produto:", self.combo_produto)
        form_layout.addRow("Quantidade:", self.input_quantidade)
        form_layout.addRow("Custo Unitário:", self.input_custo_unitario)
        form_layout.addRow("Observação:", self.input_observacao)

        # --- Layout principal ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addWidget(self.btn_salvar)
        layout_principal.addWidget(self.btn_limpar)

        self.setLayout(layout_principal)

        # Carregar produtos do banco
        self.carregar_produtos()

    # -------------------------------------------------------------
    # Conexão com o banco
    # -------------------------------------------------------------
    def criar_conexao(self):
        """Cria e retorna uma conexão com o banco MySQL."""
        try:
            conexao = pymysql.connect(
                host="sistemasintegrados.myddns.me",
                user="root",
                password="K@rraP1x0",  # ⚠️ altere conforme seu ambiente
                database="stock",
                port=27317,
                cursorclass=DictCursor,
                autocommit=True
            )
            
            return conexao
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro de conexão", f"Não foi possível conectar ao banco:\n{e}")
            return None


    # -------------------------------------------------------------
    # Carregar produtos
    # -------------------------------------------------------------
    def carregar_produtos(self):
        """Carrega os produtos cadastrados no combo box."""
        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT id_produto, nome_produto FROM produtos ORDER BY nome_produto;")
                produtos = cursor.fetchall()
                self.combo_produto.clear()
                for p in produtos:
                    self.combo_produto.addItem(p["nome_produto"], p["id_produto"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Registrar entrada
    # -------------------------------------------------------------
    def registrar_entrada(self):
        """Registra uma nova entrada de estoque no banco."""
        id_produto = self.combo_produto.currentData()
        quantidade = int(self.input_quantidade.value())
        custo_unitario = float(self.input_custo_unitario.value())
        observacao = self.input_observacao.toPlainText().strip()

        if not id_produto:
            QMessageBox.warning(self, "Campo obrigatório", "Selecione um produto!")
            return

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                # Inserir entrada
                sql = """
                    INSERT INTO entradas_estoque (id_produto, quantidade, custo_unitario, observacao)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (id_produto, quantidade, custo_unitario, observacao))

                # Atualizar estoque atual do produto
                sql_update = """
                    UPDATE produtos
                    SET estoque_atual = estoque_atual + %s
                    WHERE id_produto = %s
                """
                cursor.execute(sql_update, (quantidade, id_produto))

                QMessageBox.information(self, "Sucesso", "Entrada registrada com sucesso!")
                self.limpar_campos()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar entrada:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Limpar campos
    # -------------------------------------------------------------
    def limpar_campos(self):
        """Limpa todos os campos do formulário."""
        self.combo_produto.setCurrentIndex(0)
        self.input_quantidade.setValue(1)
        self.input_custo_unitario.setValue(0.00)
        self.input_observacao.clear()


# -------------------------------------------------------------
# Execução direta
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = EntradasEstoqueApp()
    janela.show()
    sys.exit(app.exec_())
