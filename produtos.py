import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QPushButton, QVBoxLayout, QFormLayout, QMessageBox
)


class ProdutosApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Produtos")
        self.setFixedSize(550, 550)

        # --- Campos de entrada ---
        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Nome do produto")

        self.input_descricao = QTextEdit()
        self.input_descricao.setPlaceholderText("Descrição do produto")

        self.combo_categoria = QComboBox()
        self.combo_fornecedor = QComboBox()

        self.input_preco_custo = QDoubleSpinBox()
        self.input_preco_custo.setPrefix("R$ ")
        self.input_preco_custo.setDecimals(2)
        self.input_preco_custo.setMaximum(999999.99)

        self.input_preco_venda = QDoubleSpinBox()
        self.input_preco_venda.setPrefix("R$ ")
        self.input_preco_venda.setDecimals(2)
        self.input_preco_venda.setMaximum(999999.99)

        self.input_estoque = QSpinBox()
        self.input_estoque.setMaximum(100000)

        # --- Botões ---
        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.clicked.connect(self.salvar_produto)

        self.btn_limpar = QPushButton("Limpar")
        self.btn_limpar.clicked.connect(self.limpar_campos)

        # --- Layout do formulário ---
        form_layout = QFormLayout()
        form_layout.addRow("Nome do Produto:", self.input_nome)
        form_layout.addRow("Descrição:", self.input_descricao)
        form_layout.addRow("Categoria:", self.combo_categoria)
        form_layout.addRow("Fornecedor:", self.combo_fornecedor)
        form_layout.addRow("Preço de Custo:", self.input_preco_custo)
        form_layout.addRow("Preço de Venda:", self.input_preco_venda)
        form_layout.addRow("Estoque Inicial:", self.input_estoque)

        # --- Layout principal ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addWidget(self.btn_salvar)
        layout_principal.addWidget(self.btn_limpar)

        self.setLayout(layout_principal)

        # Carregar opções de categorias e fornecedores
        self.carregar_categorias()
        self.carregar_fornecedores()

    # -------------------------------------------------------------
    # Conexão com o banco
    # -------------------------------------------------------------
    def criar_conexao(self):
        """Cria e retorna uma conexão com o banco MySQL."""
        try:
            conexao = pymysql.connect(
                host="192.168.100.33",
                user="root",
                password="12345678",  # ⚠️ altere conforme seu ambiente
                database="stock",
                cursorclass=DictCursor,
                autocommit=True
            )
            print("✅ Banco de dados conectado com sucesso!")
            return conexao
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro de conexão", f"Não foi possível conectar ao banco:\n{e}")
            return None

    # -------------------------------------------------------------
    # Carregar combos
    # -------------------------------------------------------------
    def carregar_categorias(self):
        """Preenche o combo de categorias a partir do banco."""
        conexao = self.criar_conexao()
        if not conexao:
            return
        try:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT id_categoria, nome_categoria FROM categorias ORDER BY nome_categoria;")
                categorias = cursor.fetchall()
                self.combo_categoria.clear()
                for cat in categorias:
                    self.combo_categoria.addItem(cat["nome_categoria"], cat["id_categoria"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar categorias:\n{e}")
        finally:
            conexao.close()

    def carregar_fornecedores(self):
        """Preenche o combo de fornecedores a partir do banco."""
        conexao = self.criar_conexao()
        if not conexao:
            return
        try:
            with conexao.cursor() as cursor:
                cursor.execute("SELECT id_fornecedor, nome FROM fornecedores ORDER BY nome;")
                fornecedores = cursor.fetchall()
                self.combo_fornecedor.clear()
                for forn in fornecedores:
                    self.combo_fornecedor.addItem(forn["nome"], forn["id_fornecedor"])
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar fornecedores:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Salvar produto
    # -------------------------------------------------------------
    def salvar_produto(self):
        """Insere um novo produto no banco de dados."""
        nome = self.input_nome.text().strip()
        descricao = self.input_descricao.toPlainText().strip()
        id_categoria = self.combo_categoria.currentData()
        id_fornecedor = self.combo_fornecedor.currentData()
        preco_custo = float(self.input_preco_custo.value())
        preco_venda = float(self.input_preco_venda.value())
        estoque = int(self.input_estoque.value())

        if not nome or not id_categoria or not id_fornecedor:
            QMessageBox.warning(self, "Campos obrigatórios", "Preencha nome, categoria e fornecedor!")
            return

        conexao = self.criar_conexao()
        if not conexao:
            return

        try:
            with conexao.cursor() as cursor:
                sql = """
                    INSERT INTO produtos (nome_produto, descricao, id_categoria, id_fornecedor, preco_custo, preco_venda, estoque_atual)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (nome, descricao, id_categoria, id_fornecedor, preco_custo, preco_venda, estoque))
                QMessageBox.information(self, "Sucesso", "Produto cadastrado com sucesso!")
                self.limpar_campos()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar produto:\n{e}")
        finally:
            conexao.close()

    # -------------------------------------------------------------
    # Limpar campos
    # -------------------------------------------------------------
    def limpar_campos(self):
        """Limpa todos os campos do formulário."""
        self.input_nome.clear()
        self.input_descricao.clear()
        self.input_preco_custo.setValue(0.00)
        self.input_preco_venda.setValue(0.00)
        self.input_estoque.setValue(0)
        self.combo_categoria.setCurrentIndex(0)
        self.combo_fornecedor.setCurrentIndex(0)


# -------------------------------------------------------------
# Execução direta
# -------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = ProdutosApp()
    janela.show()
    sys.exit(app.exec_())
