import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QVBoxLayout, QFormLayout, QMessageBox
)


class CategoriasApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Categorias")
        self.setFixedSize(500, 350)

        # --- Campos de entrada ---
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome da categoria")

        self.input_descricao = QTextEdit()
        self.input_descricao.setPlaceholderText("Descrição da categoria")

        # --- Botões ---
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self.salvar_categoria)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)

        # --- Layout do formulário ---
        form_layout = QFormLayout()
        form_layout.addRow("Nome da Categoria:", self.input_nome)
        form_layout.addRow("Descrição:", self.input_descricao)

        # --- Layout principal ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addWidget(self.btn_salvar)
        layout_principal.addWidget(self.btn_limpar)

        self.setLayout(layout_principal)

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
                database="stock_teste",
                port=27317,
                cursorclass=DictCursor,
                autocommit=True
            )
            
            return conexao
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro de conexão", f"Não foi possível conectar ao banco:\n{e}")
            return None

    # -------------------------------------------------------------
    # Lógica do botão "Salvar"
    # -------------------------------------------------------------
    def salvar_categoria(self):
        """Insere uma nova categoria no banco de dados."""
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.toPlainText().strip()

        if not nome:
            QMessageBox.warning(self, "Campo obrigatório", "O nome da categoria é obrigatório!")
            return

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                sql = """
                    INSERT INTO categorias (nome_categoria, descricao)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (nome, descricao))
                QMessageBox.information(self, "Sucesso", "Categoria cadastrada com sucesso!")
                print("✅ Categoria cadastrada com sucesso!")
                self.limpar_campos()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar categoria:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Lógica do botão "Limpar"
    # -------------------------------------------------------------
    def limpar_campos(self):
        """Limpa os campos do formulário."""
        self.input_nome.clear()
        self.input_descricao.clear()


# -------------------------------------------------------------
# Execução direta do aplicativo
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = CategoriasApp()
    janela.show()
    sys.exit(app.exec_())
