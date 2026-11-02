import os
import sys
import tempfile
import datetime
from decimal import Decimal
import pymysql
from pymysql.cursors import DictCursor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QSpinBox, QDoubleSpinBox,
    QHeaderView, QAbstractItemView
)
from PyQt5.QtGui import QColor, QPainter, QPixmap, QPolygon
from PyQt5.QtCore import Qt, QPoint


# ===============================================================
# Visual (folha de estilo)
# ===============================================================
ESTILO = """
QWidget#tela { background: #f3f4f6; }
QWidget { font-size: 13px; color: #1f2937; }
QLabel { background: transparent; }

QTabWidget::pane {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #6b7280;
    padding: 11px 24px;
    margin-right: 4px;
    border: none;
    border-bottom: 3px solid transparent;
}
QTabBar::tab:hover:!selected { color: #111827; }
QTabBar::tab:selected { color: #2563eb; border-bottom: 3px solid #2563eb; }

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 10px;
    min-height: 20px;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #2563eb;
}
QComboBox { padding-right: 28px; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox::down-arrow { image: url(@BAIXO@); width: 10px; height: 10px; margin-right: 8px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d1d5db;
    selection-background-color: #dbeafe;
    selection-color: #111827;
    outline: 0;
}
QSpinBox, QDoubleSpinBox { padding-right: 24px; }
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right;
    width: 20px; border: none; background: transparent;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 20px; border: none; background: transparent;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: url(@CIMA@); width: 10px; height: 10px; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: url(@BAIXO@); width: 10px; height: 10px; }

QPushButton {
    background: #e5e7eb;
    color: #1f2937;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
}
QPushButton:hover { background: #d1d5db; }
QPushButton:pressed { background: #9ca3af; }
QPushButton#primario { background: #2563eb; color: #ffffff; }
QPushButton#primario:hover { background: #1d4ed8; }
QPushButton#perigo { background: #fee2e2; color: #b91c1c; }
QPushButton#perigo:hover { background: #fecaca; }

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
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
"""


def montar_estilo():
    """Gera as setas (png) numa pasta temporária e devolve a folha de estilo pronta."""
    pasta = os.path.join(tempfile.gettempdir(), "estoque_setas")
    os.makedirs(pasta, exist_ok=True)
    caminhos = {}
    formas = {"BAIXO": [(1, 3), (9, 3), (5, 8)], "CIMA": [(1, 7), (9, 7), (5, 2)]}
    for nome, pontos in formas.items():
        pix = QPixmap(10, 10)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#6b7280"))
        p.drawPolygon(QPolygon([QPoint(x, y) for x, y in pontos]))
        p.end()
        caminho = os.path.join(pasta, nome.lower() + ".png")
        pix.save(caminho)
        caminhos[nome] = caminho.replace("\\", "/")
    return ESTILO.replace("@BAIXO@", caminhos["BAIXO"]).replace("@CIMA@", caminhos["CIMA"])


def fmt(valor):
    """Formata valores para a tabela: dinheiro, datas e vazios."""
    if valor is None:
        return "-"
    if isinstance(valor, (Decimal, float)):
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return "R$ " + texto
    if isinstance(valor, datetime.datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    if isinstance(valor, datetime.date):
        return valor.strftime("%d/%m/%Y")
    return str(valor)


def configurar_tabela(tabela):
    tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
    tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
    tabela.setSelectionMode(QAbstractItemView.SingleSelection)
    tabela.setAlternatingRowColors(True)
    tabela.setShowGrid(False)
    tabela.verticalHeader().setVisible(False)
    tabela.verticalHeader().setDefaultSectionSize(38)
    cab = tabela.horizontalHeader()
    cab.setHighlightSections(False)
    cab.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    cab.setSectionResizeMode(QHeaderView.Stretch)


# ===============================================================
# Função de conexão com o banco
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
# Classe base com botões e funções padrão
# ===============================================================
class AbaBase(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.form_layout = QHBoxLayout()
        self.botoes_layout = QHBoxLayout()
        self.tabela = QTableWidget()
        self.setLayout(self.layout)

        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(12)
        self.form_layout.setSpacing(8)
        self.botoes_layout.setSpacing(8)
        configurar_tabela(self.tabela)

        # Botões
        self.btn_novo = QPushButton("Novo")
        self.btn_salvar = QPushButton("Cadastrar")
        self.btn_deletar = QPushButton("Deletar")
        self.btn_limpar = QPushButton("Limpar")
        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_fechar = QPushButton("Fechar")

        self.btn_salvar.setObjectName("primario")
        self.btn_deletar.setObjectName("perigo")

        for b in [self.btn_novo, self.btn_salvar, self.btn_deletar, self.btn_limpar, self.btn_atualizar, self.btn_fechar]:
            b.setCursor(Qt.PointingHandCursor)
            self.botoes_layout.addWidget(b)

        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.botoes_layout)
        self.layout.addWidget(self.tabela)

        self.btn_fechar.clicked.connect(self.fechar)
        self.btn_limpar.clicked.connect(self.limpar_campos)

    def fechar(self):
        self.window().close()

    def limpar_campos(self):
        for w in self.findChildren(QLineEdit):
            w.clear()
        for w in self.findChildren(QSpinBox):
            w.setValue(0)
        for w in self.findChildren(QDoubleSpinBox):
            w.setValue(0.00)


# ===============================================================
# Aba Fornecedores
# ===============================================================
class FornecedoresTab(AbaBase):
    def __init__(self):
        super().__init__()
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Nome")
        self.cnpj = QLineEdit(); self.cnpj.setPlaceholderText("CNPJ")
        self.telefone = QLineEdit(); self.telefone.setPlaceholderText("Telefone")
        self.email = QLineEdit(); self.email.setPlaceholderText("Email")
        self.endereco = QLineEdit(); self.endereco.setPlaceholderText("Endereço")

        for w in [self.nome, self.cnpj, self.telefone, self.email, self.endereco]:
            self.form_layout.addWidget(w)

        self.btn_salvar.clicked.connect(self.cadastrar)
        self.btn_deletar.clicked.connect(self.deletar)
        self.btn_atualizar.clicked.connect(self.carregar)
        self.btn_novo.clicked.connect(self.limpar_campos)

        self.carregar()

    def cadastrar(self):
        conn = criar_conexao()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO fornecedores (nome, cnpj, telefone, email, endereco) VALUES (%s,%s,%s,%s,%s)",
                    (self.nome.text(), self.cnpj.text(), self.telefone.text(), self.email.text(), self.endereco.text())
                )
            QMessageBox.information(self, "Sucesso", "Fornecedor cadastrado!")
            self.carregar()
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
        finally:
            conn.close()

    def deletar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um fornecedor para deletar.")
            return
        cnpj = self.tabela.item(row, 1).text()
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("DELETE FROM fornecedores WHERE cnpj=%s", (cnpj,))
        QMessageBox.information(self, "Sucesso", "Fornecedor removido!")
        self.carregar()
        conn.close()

    def carregar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("SELECT nome, cnpj, telefone, email, endereco FROM fornecedores")
            dados = cur.fetchall()
            self.tabela.setColumnCount(5)
            self.tabela.setHorizontalHeaderLabels(["Nome", "CNPJ", "Telefone", "Email", "Endereço"])
            self.tabela.setRowCount(len(dados))
            for i, row in enumerate(dados):
                for j, val in enumerate(row.values()):
                    self.tabela.setItem(i, j, QTableWidgetItem(fmt(val)))
        conn.close()


# ===============================================================
# Aba Categorias
# ===============================================================
class CategoriasTab(AbaBase):
    def __init__(self):
        super().__init__()
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Nome da categoria")
        self.descricao = QLineEdit(); self.descricao.setPlaceholderText("Descrição")
        for w in [self.nome, self.descricao]:
            self.form_layout.addWidget(w)

        self.btn_salvar.clicked.connect(self.cadastrar)
        self.btn_deletar.clicked.connect(self.deletar)
        self.btn_atualizar.clicked.connect(self.carregar)
        self.btn_novo.clicked.connect(self.limpar_campos)

        self.carregar()

    def cadastrar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("INSERT INTO categorias (nome_categoria, descricao) VALUES (%s,%s)",
                        (self.nome.text(), self.descricao.text()))
        QMessageBox.information(self, "Sucesso", "Categoria cadastrada!")
        self.carregar()
        conn.close()

    def deletar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma categoria.")
            return
        nome = self.tabela.item(row, 0).text()
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("DELETE FROM categorias WHERE nome_categoria=%s", (nome,))
        QMessageBox.information(self, "Sucesso", "Categoria removida!")
        self.carregar()
        conn.close()

    def carregar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("SELECT nome_categoria, descricao FROM categorias")
            dados = cur.fetchall()
            self.tabela.setColumnCount(2)
            self.tabela.setHorizontalHeaderLabels(["Nome", "Descrição"])
            self.tabela.setRowCount(len(dados))
            for i, row in enumerate(dados):
                for j, val in enumerate(row.values()):
                    self.tabela.setItem(i, j, QTableWidgetItem(fmt(val)))
        conn.close()


# ===============================================================
# Aba Produtos
# ===============================================================
class ProdutosTab(AbaBase):
    def __init__(self):
        super().__init__()
        self.nome = QLineEdit(); self.nome.setPlaceholderText("Nome do produto")
        self.descricao = QLineEdit(); self.descricao.setPlaceholderText("Descrição")
        self.categoria = QComboBox()
        self.fornecedor = QComboBox()
        self.preco_custo = QDoubleSpinBox(); self.preco_custo.setPrefix("R$ "); self.preco_custo.setMaximum(999999)
        self.preco_venda = QDoubleSpinBox(); self.preco_venda.setPrefix("R$ "); self.preco_venda.setMaximum(999999)
        self.estoque = QSpinBox(); self.estoque.setMaximum(999999)

        for w in [self.nome, self.descricao, self.categoria, self.fornecedor, self.preco_custo, self.preco_venda, self.estoque]:
            self.form_layout.addWidget(w)

        self.btn_salvar.clicked.connect(self.cadastrar)
        self.btn_deletar.clicked.connect(self.deletar)
        self.btn_atualizar.clicked.connect(self.carregar)
        self.btn_novo.clicked.connect(self.limpar_campos)

        self.carregar_combos()
        self.carregar()

    def carregar_combos(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("SELECT id_categoria, nome_categoria FROM categorias")
            cats = cur.fetchall()
            self.categoria.clear()
            for c in cats:
                self.categoria.addItem(c["nome_categoria"], c["id_categoria"])
            cur.execute("SELECT id_fornecedor, nome FROM fornecedores")
            fors = cur.fetchall()
            self.fornecedor.clear()
            for f in fors:
                self.fornecedor.addItem(f["nome"], f["id_fornecedor"])
        conn.close()

    def cadastrar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO produtos (nome_produto, descricao, id_categoria, id_fornecedor, preco_custo, preco_venda, estoque_atual)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                self.nome.text(), self.descricao.text(),
                self.categoria.currentData(), self.fornecedor.currentData(),
                self.preco_custo.value(), self.preco_venda.value(), self.estoque.value()
            ))
        QMessageBox.information(self, "Sucesso", "Produto cadastrado!")
        self.carregar()
        conn.close()

    def deletar(self):
        row = self.tabela.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione um produto.")
            return
        nome = self.tabela.item(row, 0).text()
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("DELETE FROM produtos WHERE nome_produto=%s", (nome,))
        QMessageBox.information(self, "Sucesso", "Produto removido!")
        self.carregar()
        conn.close()

    def carregar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.nome_produto, p.descricao, c.nome_categoria, f.nome, p.preco_custo, p.preco_venda, p.estoque_atual
                FROM produtos p
                JOIN categorias c ON c.id_categoria=p.id_categoria
                JOIN fornecedores f ON f.id_fornecedor=p.id_fornecedor
            """)
            dados = cur.fetchall()
            self.tabela.setColumnCount(7)
            self.tabela.setHorizontalHeaderLabels(["Produto", "Descrição", "Categoria", "Fornecedor", "Custo", "Venda", "Estoque"])
            self.tabela.setRowCount(len(dados))
            for i, row in enumerate(dados):
                for j, val in enumerate(row.values()):
                    self.tabela.setItem(i, j, QTableWidgetItem(fmt(val)))
        conn.close()


# ===============================================================
# Entradas, Saídas e Movimentações
# ===============================================================
class EntradasTab(AbaBase):
    def __init__(self):
        super().__init__()
        self.produto = QComboBox()
        self.quantidade = QSpinBox(); self.quantidade.setMaximum(99999)
        self.custo = QDoubleSpinBox(); self.custo.setPrefix("R$ "); self.custo.setMaximum(999999)
        self.obs = QLineEdit(); self.obs.setPlaceholderText("Observação")
        self.data_entrada = QLabel("Data: " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.data_entrada.setStyleSheet("color: #6b7280;")

        for w in [self.produto, self.quantidade, self.custo, self.obs, self.data_entrada]:
            self.form_layout.addWidget(w)

        self.btn_salvar.clicked.connect(self.cadastrar)
        self.btn_deletar.clicked.connect(self.deletar)
        self.btn_atualizar.clicked.connect(self.carregar)
        self.btn_novo.clicked.connect(self.limpar_campos)

        self.carregar_combos()
        self.carregar()

    def carregar_combos(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("SELECT id_produto, nome_produto FROM produtos")
            self.produto.clear()
            for p in cur.fetchall():
                self.produto.addItem(p["nome_produto"], p["id_produto"])
        conn.close()

    def cadastrar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO entradas_estoque (id_produto, quantidade, custo_unitario, custo_total, observacao, data_entrada, id_usuario)
                VALUES (%s,%s,%s,%s,%s,%s,1)
            """, (self.produto.currentData(), self.quantidade.value(), self.custo.value(), self.custo.value() * self.quantidade.value(), self.obs.text(), datetime.datetime.now()))
        self.carregar()
        conn.close()

    def deletar(self):
        row = self.tabela.currentRow()
        if row < 0: return
        id_entrada = self.tabela.item(row, 0).text()
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("DELETE FROM entradas_estoque WHERE id_entrada=%s", (id_entrada,))
        QMessageBox.information(self, "Sucesso", "Entrada removida!")
        self.carregar()
        conn.close()

    def carregar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.id_entrada, p.nome_produto, e.quantidade, e.data_entrada, e.custo_unitario, e.observacao
                FROM entradas_estoque e JOIN produtos p ON p.id_produto=e.id_produto
                ORDER BY e.data_entrada DESC
            """)
            dados = cur.fetchall()
            self.tabela.setColumnCount(6)
            self.tabela.setHorizontalHeaderLabels(["ID", "Produto", "Qtd", "Data", "Custo", "Obs"])
            self.tabela.setRowCount(len(dados))
            for i, row in enumerate(dados):
                for j, val in enumerate(row.values()):
                    self.tabela.setItem(i, j, QTableWidgetItem(fmt(val)))
        conn.close()


class SaidasTab(EntradasTab):
    def cadastrar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO saidas_estoque (id_produto, quantidade, motivo, observacao,id_usuario, valor_unitario, valor_total)
                VALUES (%s,%s,%s,%s,1,%s,%s)
            """, (self.produto.currentData(), self.quantidade.value(), "Saída", self.obs.text(), self.custo.value(), self.custo.value() * self.quantidade.value()))
        QMessageBox.information(self, "Sucesso", "Saída registrada!")
        self.carregar()
        conn.close()

    def carregar(self):
        conn = criar_conexao()
        if not conn: return
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.id_saida, p.nome_produto, s.quantidade, s.data_saida, s.motivo, s.observacao
                FROM saidas_estoque s JOIN produtos p ON p.id_produto=s.id_produto
                ORDER BY s.data_saida DESC
            """)
            dados = cur.fetchall()
            self.tabela.setColumnCount(6)
            self.tabela.setHorizontalHeaderLabels(["ID", "Produto", "Qtd", "Data", "Motivo", "Obs"])
            self.tabela.setRowCount(len(dados))
            for i, row in enumerate(dados):
                for j, val in enumerate(row.values()):
                    self.tabela.setItem(i, j, QTableWidgetItem(fmt(val)))
        conn.close()


class MovimentacoesTab(AbaBase):
    def __init__(self):
        super().__init__()
        # Aba só de consulta: esconde os botões que não se aplicam
        for b in (self.btn_novo, self.btn_salvar, self.btn_deletar, self.btn_limpar):
            b.hide()
        self.btn_atualizar.clicked.connect(self.carregar)
        self.carregar()

    def carregar(self):
        conn = criar_conexao()
        if not conn:
            return

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        tipo_movimentacao,
                        id_movimento,
                        nome_produto,
                        quantidade,
                        data_movimentacao,
                        valor_unitario
                    FROM movimentacoes_estoque
                    ORDER BY data_movimentacao DESC
                """)
                dados = cur.fetchall()

                self.tabela.setColumnCount(6)
                self.tabela.setHorizontalHeaderLabels([
                    "Tipo", "ID Movimento", "Produto", "Quantidade", "Data", "Valor Unit."
                ])

                self.tabela.setRowCount(len(dados))
                for i, row in enumerate(dados):
                    valores = [
                        row["tipo_movimentacao"],
                        row["id_movimento"],
                        row["nome_produto"],
                        row["quantidade"],
                        row["data_movimentacao"],
                        row["valor_unitario"]
                    ]
                    for j, v in enumerate(valores):
                        self.tabela.setItem(i, j, QTableWidgetItem(fmt(v)))

                if not dados:
                    QMessageBox.information(self, "Aviso", "Nenhuma movimentação encontrada.")

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar movimentações:\n{e}")
        finally:
            conn.close()


# ===============================================================
# Janela Principal
# ===============================================================
class EstoqueApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📦 Sistema de Controle de Estoque - PyQt5")
        self.setMinimumSize(1200, 700)
        self.setObjectName("tela")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(montar_estilo())

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        tabs = QTabWidget()
        tabs.addTab(FornecedoresTab(), "Fornecedores")
        tabs.addTab(CategoriasTab(), "Categorias")
        tabs.addTab(ProdutosTab(), "Produtos")
        tabs.addTab(EntradasTab(), "Entradas de Estoque")
        tabs.addTab(SaidasTab(), "Saídas de Estoque")
        tabs.addTab(MovimentacoesTab(), "Movimentações")
        layout.addWidget(tabs)
        self.setLayout(layout)


# ===============================================================
# Execução
# ===============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    janela = EstoqueApp()
    janela.show()
    sys.exit(app.exec_())