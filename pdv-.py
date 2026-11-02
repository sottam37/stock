import datetime
import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QSpinBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

# ===============================================================
# Conexão com o banco
# ===============================================================
def criar_conexao():
    try:
        conn = pymysql.connect(
            host="sistemasintegrados.myddns.me",
            user="root",
            password="K@rraP1x0",  # ⚠️ altere conforme seu ambiente
            database="stock",
            port=27317,
            cursorclass=DictCursor,
            autocommit=True
        )
        print("✅ Banco de dados conectado com sucesso!")
        return conn
    except pymysql.MySQLError as e:
        QMessageBox.critical(None, "Erro de Conexão", f"Erro ao conectar ao banco:\n{e}")
        return None


    except pymysql.MySQLError as e:
        QMessageBox.critical(
            None,  # ou use self se transformar em método da classe
            "Erro de conexão",
            f"Não foi possível conectar ao banco:\n{e}"
        )
        return None


# ===============================================================
# Tela de vendas simplificada
# ===============================================================
class TelaVendas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 Vendas de Itens (Simples)")
        self.setMinimumSize(1000, 650)

        self.carrinho = []  # lista de produtos adicionados

        # Layout principal
        main_layout = QHBoxLayout(self)

        # =====================================
        # Lado esquerdo: produtos e busca
        # =====================================
        left_layout = QVBoxLayout()

        # 🔍 Barra de busca
        busca_layout = QHBoxLayout()
        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Buscar por nome ou código do produto...")
        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.clicked.connect(self.buscar_produtos)
        btn_todos = QPushButton("📋 Mostrar Todos")
        btn_todos.clicked.connect(self.carregar_produtos)

        busca_layout.addWidget(self.txt_busca)
        busca_layout.addWidget(btn_buscar)
        busca_layout.addWidget(btn_todos)
        left_layout.addLayout(busca_layout)

        # 🧾 Tabela de produtos
        self.tabela_produtos = QTableWidget(0, 5)
        self.tabela_produtos.setHorizontalHeaderLabels(["ID", "Produto", "Preço", "Estoque", "Qtd"])
        self.tabela_produtos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.tabela_produtos)

        # Botão adicionar ao carrinho
        self.btn_adicionar = QPushButton("➕ Adicionar ao Carrinho")
        self.btn_adicionar.setStyleSheet("background-color: #0078d7; color: white; font-weight: bold;")
        self.btn_adicionar.clicked.connect(self.adicionar_selecionado)
        left_layout.addWidget(self.btn_adicionar)

        # =====================================
        # Lado direito: carrinho
        # =====================================
        right_layout = QVBoxLayout()
        lbl_carrinho = QLabel("🛍️ Carrinho de Compras")
        lbl_carrinho.setFont(QFont("Arial", 16, QFont.Bold))
        lbl_carrinho.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tabela_carrinho = QTableWidget(0, 4)
        self.tabela_carrinho.setHorizontalHeaderLabels(["Produto", "Qtd", "Preço", "Subtotal"])
        self.tabela_carrinho.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.lbl_total = QLabel("Total: R$ 0,00")
        self.lbl_total.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Botões: finalizar e limpar
        botoes_layout = QHBoxLayout()

        btn_finalizar = QPushButton("💰 Finalizar Venda")
        btn_finalizar.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        btn_finalizar.clicked.connect(self.finalizar_venda)

        btn_limpar = QPushButton("🧹 Cancelar Venda")
        btn_limpar.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
        btn_limpar.clicked.connect(self.limpar_carrinho)

        botoes_layout.addWidget(btn_finalizar)
        botoes_layout.addWidget(btn_limpar)

        right_layout.addWidget(lbl_carrinho)
        right_layout.addWidget(self.tabela_carrinho)
        right_layout.addWidget(self.lbl_total)
        right_layout.addLayout(botoes_layout)

        main_layout.addLayout(left_layout, 60)
        main_layout.addLayout(right_layout, 40)
        self.setLayout(main_layout)

        # Carrega todos os produtos ao iniciar
        self.carregar_produtos()

    # ===============================================================
    # Carregar produtos do banco
    # ===============================================================
    def carregar_produtos(self, filtro=None):
        conn = criar_conexao()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                if filtro:
                    cur.execute("""
                        SELECT id_produto, nome_produto, preco_venda
                        FROM produtos
                        WHERE nome_produto LIKE %s OR id_produto = %s
                    """, (f"%{filtro}%", filtro if filtro.isdigit() else 0))
                else:
                    cur.execute("SELECT id_produto, nome_produto, preco_venda FROM produtos WHERE ativo = 1")

                produtos = cur.fetchall()

            self.tabela_produtos.setRowCount(0)

            for p in produtos:
                row = self.tabela_produtos.rowCount()
                self.tabela_produtos.insertRow(row)
                self.tabela_produtos.setItem(row, 0, QTableWidgetItem(str(p["id_produto"])))
                self.tabela_produtos.setItem(row, 1, QTableWidgetItem(p["nome_produto"]))
                self.tabela_produtos.setItem(row, 2, QTableWidgetItem(f"R$ {p['preco_venda']:.2f}"))
                

                spin = QSpinBox()
                spin.setRange(1, p["estoque_atual"])
                spin.setValue(1)
                self.tabela_produtos.setCellWidget(row, 3, spin)

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos:\n{e}")
        finally:
            conn.close()

    # ===============================================================
    # Buscar produto pelo nome ou código
    # ===============================================================
    def buscar_produtos(self):
        termo = self.txt_busca.text().strip()
        if termo == "":
            QMessageBox.information(self, "Busca", "Digite o nome ou código para buscar.")
            return
        self.carregar_produtos(termo)

    # ===============================================================
    # Adicionar produto selecionado ao carrinho
    # ===============================================================
    def adicionar_selecionado(self):
        linha = self.tabela_produtos.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Seleção", "Selecione um produto para adicionar.")
            return

        id_produto = int(self.tabela_produtos.item(linha, 0).text())
        nome = self.tabela_produtos.item(linha, 1).text()
        preco_str = self.tabela_produtos.item(linha, 2).text().replace("R$ ", "")
        preco = float(preco_str)
        qtd_widget = self.tabela_produtos.cellWidget(linha, 3)
        quantidade = qtd_widget.value()

        # Se já existe no carrinho, soma a quantidade
        for item in self.carrinho:
            if item["id"] == id_produto:
                item["quantidade"] += quantidade
                break
        else:
            self.carrinho.append({
                "id": id_produto,
                "nome": nome,
                "quantidade": quantidade,
                "preco": preco
            })

        self.atualizar_carrinho()

    # ===============================================================
    # Atualiza tabela do carrinho
    # ===============================================================
    def atualizar_carrinho(self):
        self.tabela_carrinho.setRowCount(len(self.carrinho))
        total = 0

        for i, item in enumerate(self.carrinho):
            subtotal = item["quantidade"] * item["preco"]
            total += subtotal

            self.tabela_carrinho.setItem(i, 0, QTableWidgetItem(item["nome"]))
            self.tabela_carrinho.setItem(i, 1, QTableWidgetItem(str(item["quantidade"])))
            self.tabela_carrinho.setItem(i, 2, QTableWidgetItem(f"R$ {item['preco']:.2f}"))
            self.tabela_carrinho.setItem(i, 3, QTableWidgetItem(f"R$ {subtotal:.2f}"))

        self.lbl_total.setText(f"Total: R$ {total:.2f}")

    # ===============================================================
    # Cancelar venda (limpa carrinho)
    # ===============================================================
    def limpar_carrinho(self):
        if not self.carrinho:
            QMessageBox.information(self, "Carrinho", "Não há itens para remover.")
            return

        confirm = QMessageBox.question(
            self, "Cancelar Venda",
            "Tem certeza que deseja cancelar esta venda e limpar o carrinho?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.carrinho.clear()
            self.tabela_carrinho.setRowCount(0)
            self.lbl_total.setText("Total: R$ 0,00")
            QMessageBox.information(self, "Venda Cancelada", "Carrinho limpo com sucesso.")

    # ===============================================================
    # Finalizar venda e registrar saída de estoque
    # ===============================================================
    def finalizar_venda(self):
        if not self.carrinho:
            QMessageBox.warning(self, "Carrinho vazio", "Adicione itens ao carrinho antes de finalizar.")
            return

        conn = criar_conexao()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                for item in self.carrinho:
                    cur.execute("""
                        INSERT INTO saidas_estoque (id_produto, id_empresa, quantidade,data_saida, motivo, observacao, id_usuario, valor_unitario , valor_total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
                    """, (item["id"], 1 , item["quantidade"], datetime.datetime.now(), "Venda", "Venda simples via sistema", 1, item["preco"], item["quantidade"] * item["preco"]))
            QMessageBox.information(self, "Sucesso", "Venda registrada com sucesso!")
            self.carrinho.clear()
            self.tabela_carrinho.setRowCount(0)
            self.lbl_total.setText("Total: R$ 0,00")
            
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao registrar venda:\n{e}")
        finally:
            conn.close()


# ===============================================================
# Execução principal
# ===============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = TelaVendas()
    janela.show()
    sys.exit(app.exec_())
