import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
    QVBoxLayout, QFormLayout, QMessageBox
)


class FornecedoresApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Fornecedores")
        self.setFixedSize(500, 450)

        # --- Campos de entrada ---
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do fornecedor")

        self.input_cnpj = QLineEdit()
        self.input_cnpj.setPlaceholderText("00.000.000/0000-00")

        self.input_telefone = QLineEdit()
        self.input_telefone.setPlaceholderText("(00) 00000-0000")

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("email@empresa.com")

        self.input_endereco = QTextEdit()
        self.input_endereco.setPlaceholderText("Endereço completo")

        # --- Botões ---
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self.salvar_fornecedor)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)

        # --- Layout do formulário ---
        form_layout = QFormLayout()
        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("CNPJ:", self.input_cnpj)
        form_layout.addRow("Telefone:", self.input_telefone)
        form_layout.addRow("E-mail:", self.input_email)
        form_layout.addRow("Endereço:", self.input_endereco)

        # --- Layout principal ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addWidget(self.btn_salvar)
        layout_principal.addWidget(self.btn_limpar)

        self.setLayout(layout_principal)

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


    def salvar_fornecedor(self):
        """Insere um novo fornecedor no banco de dados."""
        nome = self.input_nome.text().strip()
        cnpj = self.input_cnpj.text().strip()
        telefone = self.input_telefone.text().strip()
        email = self.input_email.text().strip()
        endereco = self.input_endereco.toPlainText().strip()

        if not nome or not cnpj:
            QMessageBox.warning(self, "Campos obrigatórios", "Nome e CNPJ são obrigatórios!")
            return

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                sql = """
                    INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nome, cnpj, telefone, email, endereco))
                QMessageBox.information(self, "Sucesso", "Fornecedor cadastrado com sucesso!")
                self.limpar_campos()
        except pymysql.IntegrityError:
            QMessageBox.warning(self, "Erro", "CNPJ já cadastrado!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar fornecedor:\n{e}")
        finally:
            conexao.close()

    def limpar_campos(self):
        """Limpa todos os campos do formulário."""
        self.input_nome.clear()
        self.input_cnpj.clear()
        self.input_telefone.clear()
        self.input_email.clear()
        self.input_endereco.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = FornecedoresApp()
    janela.show()
    sys.exit(app.exec_())
