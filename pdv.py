import datetime
import sys
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox,
    QSpinBox, QFrame, QAbstractItemView
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt


# ===============================================================
# Visual (folha de estilo)
# ===============================================================
ESTILO = """
QWidget#tela { background: #f3f4f6; }
QWidget { font-size: 13px; color: #1f2937; }

QFrame#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}
QLabel { background: transparent; }
QLabel#titulo { font-size: 20px; font-weight: 700; color: #111827; }
QLabel#subtitulo { color: #6b7280; }

QLineEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 9px 12px;
}
QLineEdit:focus { border: 1px solid #2563eb; }

QPushButton {
    background: #e5e7eb;
    color: #1f2937;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
}
QPushButton:hover { background: #d1d5db; }
QPushButton:pressed { background: #9ca3af; }

QPushButton#primario { background: #2563eb; color: #ffffff; }
QPushButton#primario:hover { background: #1d4ed8; }
QPushButton#sucesso { background: #16a34a; color: #ffffff; font-size: 14px; }
QPushButton#sucesso:hover { background: #15803d; }
QPushButton#perigo { background: #fee2e2; color: #b91c1c; }
QPushButton#perigo:hover { background: #fecaca; }

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f9fafb;
    border: none;
    selection-background-color: #dbeafe;
    selection-color: #111827;
    outline: 0;
}
QTableWidget::item { padding: 4px 8px; border: none; }
QHeaderView::section {
    background: #f3f4f6;
    color: #6b7280;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 9px 8px;
    font-weight: 700;
}

QFrame#caixaTotal {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
}
QLabel#rotuloTotal { font-size: 14px; font-weight: 600; color: #166534; }
QLabel#total { font-size: 26px; font-weight: 800; color: #15803d; }
"""


def moeda(valor):
    """1234.5 -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


# ===============================================================
# Conexão com o banco
# ===============================================================
def criar_conexao():
    try:
        conn = pymysql.connect(
            host="sistemasintegrados.myddns.me",
            user="root",
            password="K@rraP1x0",  # ⚠️ altere conforme seu ambiente
            database="stock_teste",
            port=27317,
            cursorclass=DictCursor,
            autocommit=True
        )

        return conn
    except pymysql.MySQLError as e:
        QMessageBox.critical(None, "Erro de Conexão", f"Erro ao conectar ao banco:\n{e}")
        return None


# ===============================================================
# Tela de vendas simplificada
# ===============================================================
class TelaVendas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 Vendas de Itens (Simples)")
        self.setMinimumSize(1000, 650)
        self.setObjectName("tela")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(ESTILO)

        self.carrinho = []  # lista de produtos adicionados

        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # =====================================
        # Lado esquerdo: produtos e busca
        # =====================================
        card_esq = QFrame()
        card_esq.setObjectName("card")
        left_layout = QVBoxLayout(card_esq)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        titulo = QLabel("Produtos")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Busque, escolha a quantidade e adicione ao carrinho "
                           "(duplo clique também adiciona).")
        subtitulo.setObjectName("subtitulo")
        left_layout.addWidget(titulo)
        left_layout.addWidget(subtitulo)

        # Barra de busca
        busca_layout = QHBoxLayout()
        busca_layout.setSpacing(8)
        self.txt_busca = QLineEdit()
        self.txt_busca.setPlaceholderText("Buscar por nome ou código do produto...")
        self.txt_busca.returnPressed.connect(self.buscar_produtos)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setCursor(Qt.PointingHandCursor)
        btn_buscar.clicked.connect(lambda _checked=False: self.buscar_produtos())
        btn_todos = QPushButton("Mostrar todos")
        btn_todos.setCursor(Qt.PointingHandCursor)
        btn_todos.clicked.connect(lambda _checked=False: self.mostrar_todos())

        busca_layout.addWidget(self.txt_busca, 1)
        busca_layout.addWidget(btn_buscar)
        busca_layout.addWidget(btn_todos)
        left_layout.addLayout(busca_layout)

        # Tabela de produtos
        self.tabela_produtos = QTableWidget(0, 5)
        self.tabela_produtos.setHorizontalHeaderLabels(["Código", "Produto", "Preço", "Estoque", "Qtd"])
        self._ajustar_tabela(self.tabela_produtos)
        cab = self.tabela_produtos.horizontalHeader()
        cab.setSectionResizeMode(1, QHeaderView.Stretch)
        for coluna, largura in ((0, 80), (2, 110), (3, 90), (4, 110)):
            cab.setSectionResizeMode(coluna, QHeaderView.Fixed)
            self.tabela_produtos.setColumnWidth(coluna, largura)
        self.tabela_produtos.itemDoubleClicked.connect(lambda _item: self.adicionar_selecionado())
        left_layout.addWidget(self.tabela_produtos, 1)

        # Botão adicionar ao carrinho
        self.btn_adicionar = QPushButton("Adicionar ao carrinho")
        self.btn_adicionar.setObjectName("primario")
        self.btn_adicionar.setCursor(Qt.PointingHandCursor)
        self.btn_adicionar.setMinimumHeight(42)
        self.btn_adicionar.clicked.connect(lambda _checked=False: self.adicionar_selecionado())
        left_layout.addWidget(self.btn_adicionar)

        # =====================================
        # Lado direito: carrinho
        # =====================================
        card_dir = QFrame()
        card_dir.setObjectName("card")
        right_layout = QVBoxLayout(card_dir)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        topo_carrinho = QHBoxLayout()
        lbl_carrinho = QLabel("Carrinho")
        lbl_carrinho.setObjectName("titulo")
        self.lbl_itens = QLabel("0 itens")
        self.lbl_itens.setObjectName("subtitulo")
        self.lbl_itens.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        topo_carrinho.addWidget(lbl_carrinho)
        topo_carrinho.addStretch()
        topo_carrinho.addWidget(self.lbl_itens)
        right_layout.addLayout(topo_carrinho)

        self.tabela_carrinho = QTableWidget(0, 4)
        self.tabela_carrinho.setHorizontalHeaderLabels(["Produto", "Qtd", "Preço", "Subtotal"])
        self._ajustar_tabela(self.tabela_carrinho)
        cab = self.tabela_carrinho.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.Stretch)
        for coluna, largura in ((1, 55), (2, 95), (3, 105)):
            cab.setSectionResizeMode(coluna, QHeaderView.Fixed)
            self.tabela_carrinho.setColumnWidth(coluna, largura)
        right_layout.addWidget(self.tabela_carrinho, 1)

        # Total
        caixa_total = QFrame()
        caixa_total.setObjectName("caixaTotal")
        layout_total = QHBoxLayout(caixa_total)
        layout_total.setContentsMargins(16, 10, 16, 10)
        rotulo_total = QLabel("TOTAL")
        rotulo_total.setObjectName("rotuloTotal")
        self.lbl_total = QLabel("R$ 0,00")
        self.lbl_total.setObjectName("total")
        self.lbl_total.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout_total.addWidget(rotulo_total)
        layout_total.addStretch()
        layout_total.addWidget(self.lbl_total)
        right_layout.addWidget(caixa_total)

        # Botões: finalizar e limpar
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)

        btn_finalizar = QPushButton("Finalizar venda")
        btn_finalizar.setObjectName("sucesso")
        btn_finalizar.setCursor(Qt.PointingHandCursor)
        btn_finalizar.setMinimumHeight(46)
        btn_finalizar.clicked.connect(lambda _checked=False: self.finalizar_venda())

        btn_limpar = QPushButton("Cancelar venda")
        btn_limpar.setObjectName("perigo")
        btn_limpar.setCursor(Qt.PointingHandCursor)
        btn_limpar.setMinimumHeight(46)
        btn_limpar.clicked.connect(lambda _checked=False: self.limpar_carrinho())

        botoes_layout.addWidget(btn_finalizar, 3)
        botoes_layout.addWidget(btn_limpar, 2)
        right_layout.addLayout(botoes_layout)

        main_layout.addWidget(card_esq, 60)
        main_layout.addWidget(card_dir, 40)

        # Carrega todos os produtos ao iniciar
        self.carregar_produtos()

    # ===============================================================
    # Utilitários visuais
    # ===============================================================
    @staticmethod
    def _ajustar_tabela(tabela):
        tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        tabela.setAlternatingRowColors(True)
        tabela.setShowGrid(False)
        tabela.setFrameShape(QFrame.NoFrame)
        tabela.verticalHeader().setVisible(False)
        tabela.verticalHeader().setDefaultSectionSize(38)
        tabela.horizontalHeader().setHighlightSections(False)

    @staticmethod
    def _item(texto, alinhamento=Qt.AlignLeft):
        item = QTableWidgetItem(texto)
        item.setTextAlignment(alinhamento | Qt.AlignVCenter)
        return item

    # ===============================================================
    # Carregar produtos do banco
    # ===============================================================
    def mostrar_todos(self):
        self.txt_busca.clear()
        self.carregar_produtos()

    def carregar_produtos(self, filtro=None):
        conn = criar_conexao()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                if filtro:
                    cur.execute("""
                        SELECT id_produto, nome_produto, preco_venda, estoque_atual
                        FROM produtos
                        WHERE nome_produto LIKE %s OR id_produto = %s
                        ORDER BY nome_produto
                    """, (f"%{filtro}%", filtro if filtro.isdigit() else 0))
                else:
                    cur.execute("SELECT id_produto, nome_produto, preco_venda, estoque_atual "
                                "FROM produtos WHERE ativo = 1 ORDER BY nome_produto")

                produtos = cur.fetchall()

            self.tabela_produtos.setRowCount(0)

            for p in produtos:
                row = self.tabela_produtos.rowCount()
                self.tabela_produtos.insertRow(row)

                preco = self._item(moeda(p["preco_venda"]), Qt.AlignRight)
                preco.setData(Qt.UserRole, float(p["preco_venda"]))  # valor real, sem depender do texto

                estoque = p["estoque_atual"]
                item_estoque = self._item(str(estoque), Qt.AlignCenter)
                if estoque <= 0:
                    item_estoque.setForeground(QColor("#dc2626"))   # sem estoque / negativo
                elif estoque <= 10:
                    item_estoque.setForeground(QColor("#d97706"))   # estoque baixo

                self.tabela_produtos.setItem(row, 0, self._item(str(p["id_produto"]), Qt.AlignCenter))
                self.tabela_produtos.setItem(row, 1, self._item(p["nome_produto"]))
                self.tabela_produtos.setItem(row, 2, preco)
                self.tabela_produtos.setItem(row, 3, item_estoque)

                spin = QSpinBox()
                spin.setRange(1, max(1, estoque))
                spin.setValue(1)
                spin.setAlignment(Qt.AlignCenter)
                self.tabela_produtos.setCellWidget(row, 4, spin)

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
        preco = self.tabela_produtos.item(linha, 2).data(Qt.UserRole)
        qtd_widget = self.tabela_produtos.cellWidget(linha, 4)
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

        qtd_widget.setValue(1)
        self.atualizar_carrinho()

    # ===============================================================
    # Atualiza tabela do carrinho
    # ===============================================================
    def atualizar_carrinho(self):
        self.tabela_carrinho.setRowCount(len(self.carrinho))
        total = 0
        itens = 0

        for i, item in enumerate(self.carrinho):
            subtotal = item["quantidade"] * item["preco"]
            total += subtotal
            itens += item["quantidade"]

            self.tabela_carrinho.setItem(i, 0, self._item(item["nome"]))
            self.tabela_carrinho.setItem(i, 1, self._item(str(item["quantidade"]), Qt.AlignCenter))
            self.tabela_carrinho.setItem(i, 2, self._item(moeda(item["preco"]), Qt.AlignRight))
            self.tabela_carrinho.setItem(i, 3, self._item(moeda(subtotal), Qt.AlignRight))

        self.lbl_total.setText(moeda(total))
        self.lbl_itens.setText(f"{itens} item" if itens == 1 else f"{itens} itens")

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
            self.atualizar_carrinho()
            QMessageBox.information(self, "Venda Cancelada", "Carrinho limpo com sucesso.")

    # ===============================================================
    # Finalizar venda, registrar saída e dar baixa no estoque
    # ===============================================================
    def finalizar_venda(self):
        if not self.carrinho:
            QMessageBox.warning(self, "Carrinho vazio", "Adicione itens ao carrinho antes de finalizar.")
            return

        conn = criar_conexao()
        if not conn:
            return

        try:
            conn.begin()  # tudo ou nada: se algo falhar, nada é gravado
            with conn.cursor() as cur:
                for item in self.carrinho:
                    cur.execute("""
                        INSERT INTO saidas_estoque (id_produto, quantidade,data_saida, motivo, observacao, id_usuario, valor_unitario , valor_total)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (item["id"], item["quantidade"], datetime.datetime.now(), "Venda", "Venda simples via sistema", 1, item["preco"], item["quantidade"] * item["preco"]))

                # Baixa automática no estoque pela procedure do banco
                cur.execute("CALL recalcular_estoque()")

                # Se a procedure recebe parâmetros, troque a linha acima por:
                # for item in self.carrinho:
                #     cur.execute("CALL ajustar_estoque(%s, %s)", (item["id"], item["quantidade"]))
            conn.commit()

            QMessageBox.information(self, "Sucesso", "Venda registrada com sucesso!")
            self.carrinho.clear()
            self.atualizar_carrinho()
            self.carregar_produtos()  # mostra o estoque já atualizado

        except pymysql.MySQLError as e:
            conn.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao registrar venda:\n{e}")
        finally:
            conn.close()


# ===============================================================
# Execução principal
# ===============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    janela = TelaVendas()
    janela.show()
    sys.exit(app.exec_())