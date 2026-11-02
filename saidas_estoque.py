import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox,
    QSpinBox, QPushButton, QVBoxLayout, QFormLayout, QMessageBox
)


class SaidasEstoqueApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Saídas de Estoque")
        self.setFixedSize(500, 500)

        # --- Campos ---
        self.combo_produto = QComboBox()
        self.input_quantidade = QSpinBox()
        self.input_quantidade.setMaximum(100000)
        self.input_quantidade.setMinimum(1)

        self.input_motivo = QLineEdit()
        self.input_motivo.setPlaceholderText("Motivo da saída (ex: Venda, Devolução...)")

        self.input_observacao = QTextEdit()
        self.input_observacao.setPlaceholderText("Observações (opcional)")

        # --- Botões ---
        self.btn_salvar = QPushButton("Registrar Saída")
        self.btn_salvar.clicked.connect(self.registrar_saida)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)

        # --- Layout ---
        form_layout = QFormLayout()
        form_layout.addRow("Produto:", self.combo_produto)
        form_layout.addRow("Quantidade:", self.input_quantidade)
        form_layout.addRow("Motivo:", self.input_motivo)
        form_layout.addRow("Observação:", self.input_observacao)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addWidget(self.btn_salvar)
        layout_principal.addWidget(self.btn_limpar)

        self.setLayout(layout_principal)

        # Carregar produtos
        self.carregar_produtos()

    # -------------------------------------------------------------
    # Conexão com banco de dados
    # -------------------------------------------------------------
    def criar_conexao(self):
        """Cria e retorna uma conexão com o banco MySQL."""
        try:
            conexao = pymysql.connect(
                host="sistemasintegrados.myddns.me",
                user="suporte",
                password="K@rraP1x0",  # ⚠️ altere conforme seu ambiente
                database="stock",
                port=27317,
                cursorclass=DictCursor,
                autocommit=True
            )
            
            return conexao
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível conectar ao banco de dados:\n{e}")
            return None
    # -------------------------------------------------------------
    # Carregar produtos
    # -------------------------------------------------------------
    def carregar_produtos(self):
        """Carrega a lista de produtos no combo box."""
        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT id_produto, nome_produto, estoque_atual FROM produtos ORDER BY nome_produto;")
                produtos = cursor.fetchall()
                self.combo_produto.clear()
                for p in produtos:
                    nome = f"{p['nome_produto']} (Estoque: {p['estoque_atual']})"
                    self.combo_produto.addItem(nome, p["id_produto"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Registrar saída
    # -------------------------------------------------------------
    def registrar_saida(self):
        """Registra uma saída de estoque no banco."""
        id_produto = self.combo_produto.currentData()
        quantidade = int(self.input_quantidade.value())
        motivo = self.input_motivo.text().strip()
        observacao = self.input_observacao.toPlainText().strip()

        if not id_produto:
            QMessageBox.warning(self, "Campo obrigatório", "Selecione um produto!")
            return
        if not motivo:
            QMessageBox.warning(self, "Campo obrigatório", "Informe o motivo da saída!")
            return

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                # Verifica o estoque atual
                cursor.execute("SELECT estoque_atual FROM produtos WHERE id_produto = %s", (id_produto,))
                produto = cursor.fetchone()
                if not produto:
                    QMessageBox.critical(self, "Erro", "Produto não encontrado no banco!")
                    return
                if produto["estoque_atual"] < quantidade:
                    QMessageBox.warning(self, "Estoque insuficiente",
                                        f"Estoque atual: {produto['estoque_atual']} unidades.\n"
                                        f"Não é possível registrar {quantidade}.")
                    return

                # Registra saída
                sql = """
                    INSERT INTO saidas_estoque (id_produto, quantidade, motivo, observacao)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (id_produto, quantidade, motivo, observacao))

                # Atualiza o estoque do produto
                sql_update = """
                    UPDATE produtos
                    SET estoque_atual = estoque_atual - %s
                    WHERE id_produto = %s
                """
                cursor.execute(sql_update, (quantidade, id_produto))

                QMessageBox.information(self, "Sucesso", "Saída registrada com sucesso!")
                self.limpar_campos()
                self.carregar_produtos()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar saída:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Limpar campos
    # -------------------------------------------------------------
    def limpar_campos(self):
        """Limpa os campos do formulário."""
        self.combo_produto.setCurrentIndex(0)
        self.input_quantidade.setValue(1)
        self.input_motivo.clear()
        self.input_observacao.clear()


# -------------------------------------------------------------
# Execução direta
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = SaidasEstoqueApp()
    janela.show()
    sys.exit(app.exec_())
