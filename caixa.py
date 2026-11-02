import sys
import datetime
import pymysql
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QDateEdit, QHeaderView, QFrame, QAbstractItemView
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QDate, Qt
from pymysql.cursors import DictCursor


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
QLabel#titulo { font-size: 22px; font-weight: 700; color: #111827; }
QLabel#subtitulo { color: #6b7280; }
QLabel#rotulo { color: #6b7280; font-weight: 600; }

QDateEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 8px 10px;
    min-width: 110px;
}
QDateEdit:focus { border: 1px solid #2563eb; }

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

QFrame#kpiReceita, QFrame#kpiDespesa, QFrame#kpiLucro {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
}
QFrame#kpiReceita { border-left: 5px solid #16a34a; }
QFrame#kpiDespesa { border-left: 5px solid #dc2626; }
QFrame#kpiLucro   { border-left: 5px solid #2563eb; }
QLabel#kpiTitulo { color: #6b7280; font-size: 12px; font-weight: 700; }
QLabel#kpiReceitaValor { font-size: 24px; font-weight: 800; color: #15803d; }
QLabel#kpiDespesaValor { font-size: 24px; font-weight: 800; color: #b91c1c; }
QLabel#kpiLucroValor   { font-size: 24px; font-weight: 800; color: #1d4ed8; }

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
"""


def moeda(valor):
    """1234.5 -> 'R$ 1.234,50'"""
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


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
        print("✅ Banco de dados conectado com sucesso!")
        return conn
    except pymysql.MySQLError as e:
        QMessageBox.critical(None, "Erro de Conexão", f"Erro ao conectar ao banco:\n{e}")
        return None


# ===============================================================
# Classe principal
# ===============================================================
class FluxoCaixaApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📊 Fluxo de Caixa")
        self.resize(1100, 700)
        self.setMinimumSize(900, 600)
        self.setObjectName("tela")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(ESTILO)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # ------------------------------
        # Cabeçalho
        # ------------------------------
        titulo = QLabel("Fluxo de Caixa")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Compras (entradas de estoque) e vendas (saídas) do período selecionado.")
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        # ------------------------------
        # Filtros de data
        # ------------------------------
        card_filtro = QFrame()
        card_filtro.setObjectName("card")
        filtro_layout = QHBoxLayout(card_filtro)
        filtro_layout.setContentsMargins(16, 12, 16, 12)
        filtro_layout.setSpacing(10)

        lbl_de = QLabel("De")
        lbl_de.setObjectName("rotulo")
        filtro_layout.addWidget(lbl_de)
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDisplayFormat("dd/MM/yyyy")
        filtro_layout.addWidget(self.data_inicio)

        lbl_ate = QLabel("Até")
        lbl_ate.setObjectName("rotulo")
        filtro_layout.addWidget(lbl_ate)
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDisplayFormat("dd/MM/yyyy")
        filtro_layout.addWidget(self.data_fim)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("primario")
        self.btn_filtrar.setCursor(Qt.PointingHandCursor)
        self.btn_filtrar.clicked.connect(lambda _checked=False: self.carregar_fluxo())
        filtro_layout.addWidget(self.btn_filtrar)

        self.btn_limpar = QPushButton("Limpar filtros")
        self.btn_limpar.setCursor(Qt.PointingHandCursor)
        filtro_layout.addWidget(self.btn_limpar)
        filtro_layout.addStretch()

        layout.addWidget(card_filtro)

        # ------------------------------
        # Resumo Financeiro (3 cartões)
        # ------------------------------
        resumo_layout = QHBoxLayout()
        resumo_layout.setSpacing(14)
        self.lbl_entradas = self._criar_kpi(resumo_layout, "RECEITAS (VENDAS)", "kpiReceita")
        self.lbl_saidas = self._criar_kpi(resumo_layout, "DESPESAS (COMPRAS)", "kpiDespesa")
        self.lbl_saldo = self._criar_kpi(resumo_layout, "LUCRO LÍQUIDO", "kpiLucro")
        layout.addLayout(resumo_layout)

        # ------------------------------
        # Tabela de movimentações
        # ------------------------------
        card_tabela = QFrame()
        card_tabela.setObjectName("card")
        tabela_layout = QVBoxLayout(card_tabela)
        tabela_layout.setContentsMargins(16, 14, 16, 14)
        tabela_layout.setSpacing(8)

        topo_tabela = QHBoxLayout()
        lbl_mov = QLabel("Movimentações")
        lbl_mov.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.lbl_contagem = QLabel("0 registros")
        self.lbl_contagem.setObjectName("subtitulo")
        topo_tabela.addWidget(lbl_mov)
        topo_tabela.addStretch()
        topo_tabela.addWidget(self.lbl_contagem)
        tabela_layout.addLayout(topo_tabela)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Data", "Tipo", "Produto", "Quantidade", "Valor Unitário", "Total"
        ])
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabela.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setShowGrid(False)
        self.tabela.setFrameShape(QFrame.NoFrame)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.verticalHeader().setDefaultSectionSize(38)
        cab = self.tabela.horizontalHeader()
        cab.setHighlightSections(False)
        cab.setSectionResizeMode(2, QHeaderView.Stretch)
        for coluna, largura in ((0, 140), (1, 90), (3, 110), (4, 130), (5, 130)):
            cab.setSectionResizeMode(coluna, QHeaderView.Fixed)
            self.tabela.setColumnWidth(coluna, largura)
        tabela_layout.addWidget(self.tabela, 1)

        layout.addWidget(card_tabela, 1)

        # ------------------------------
        # Botões extras
        # ------------------------------
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(10)
        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.setCursor(Qt.PointingHandCursor)
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.setObjectName("perigo")
        self.btn_fechar.setCursor(Qt.PointingHandCursor)

        botoes_layout.addStretch()
        botoes_layout.addWidget(self.btn_atualizar)
        botoes_layout.addWidget(self.btn_fechar)
        layout.addLayout(botoes_layout)

        # Conexões
        self.btn_atualizar.clicked.connect(lambda _checked=False: self.carregar_fluxo())
        self.btn_limpar.clicked.connect(lambda _checked=False: self.limpar_filtros())
        self.btn_fechar.clicked.connect(self.close)

        # Carrega os dados iniciais
        self.carregar_fluxo()

    # ===============================================================
    # Cartão de resumo (retorna o label do valor)
    # ===============================================================
    @staticmethod
    def _criar_kpi(layout_pai, titulo, nome_objeto):
        cartao = QFrame()
        cartao.setObjectName(nome_objeto)
        interno = QVBoxLayout(cartao)
        interno.setContentsMargins(18, 14, 18, 14)
        interno.setSpacing(2)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("kpiTitulo")
        lbl_valor = QLabel("R$ 0,00")
        lbl_valor.setObjectName(nome_objeto + "Valor")

        interno.addWidget(lbl_titulo)
        interno.addWidget(lbl_valor)
        layout_pai.addWidget(cartao, 1)
        return lbl_valor

    @staticmethod
    def _item(texto, alinhamento=Qt.AlignLeft):
        item = QTableWidgetItem(texto)
        item.setTextAlignment(alinhamento | Qt.AlignVCenter)
        return item

    # ===============================================================
    # Função: carregar movimentações (entradas e saídas)
    # ===============================================================
    def carregar_fluxo(self):
        conn = criar_conexao()
        if not conn:
            return

        data_inicio = self.data_inicio.date().toString("yyyy-MM-dd")
        data_fim = self.data_fim.date().toString("yyyy-MM-dd")

        try:
            with conn.cursor() as cur:
                # Entradas (compras)
                cur.execute("""
                    SELECT 
                        e.data_entrada AS data,
                        'Compra' AS tipo,
                        p.nome_produto,
                        e.quantidade,
                        e.custo_unitario AS valor_unitario,
                        (e.quantidade * e.custo_unitario) AS total
                    FROM entradas_estoque e
                    JOIN produtos p ON p.id_produto = e.id_produto
                    WHERE DATE(e.data_entrada) BETWEEN %s AND %s
                """, (data_inicio, data_fim))
                entradas = list(cur.fetchall())

                # Saídas (vendas)
                cur.execute("""
                    SELECT 
                        s.data_saida AS data,
                        'Venda' AS tipo,
                        p.nome_produto,
                        s.quantidade,
                        p.preco_venda AS valor_unitario,
                        (s.quantidade * p.preco_venda) AS total
                    FROM saidas_estoque s
                    JOIN produtos p ON p.id_produto = s.id_produto
                    WHERE DATE(s.data_saida) BETWEEN %s AND %s
                """, (data_inicio, data_fim))
                saidas = list(cur.fetchall())

            # Junta tudo
            todos = entradas + saidas
            todos.sort(key=lambda x: x["data"])

            self.tabela.setRowCount(len(todos))
            total_entradas = total_saidas = 0

            for i, row in enumerate(todos):
                data = row["data"]
                if isinstance(data, (datetime.datetime, datetime.date)):
                    data = data.strftime("%d/%m/%Y %H:%M") if isinstance(data, datetime.datetime) \
                        else data.strftime("%d/%m/%Y")

                tipo = self._item(str(row["tipo"]), Qt.AlignCenter)
                if row["tipo"] == "Venda":
                    tipo.setForeground(QColor("#15803d"))   # receita
                else:
                    tipo.setForeground(QColor("#b91c1c"))   # despesa
                fonte = tipo.font()
                fonte.setBold(True)
                tipo.setFont(fonte)

                self.tabela.setItem(i, 0, self._item(str(data)))
                self.tabela.setItem(i, 1, tipo)
                self.tabela.setItem(i, 2, self._item(str(row["nome_produto"])))
                self.tabela.setItem(i, 3, self._item(str(row["quantidade"]), Qt.AlignCenter))
                vu = row["valor_unitario"]
                self.tabela.setItem(i, 4, self._item(moeda(vu) if vu is not None else "-", Qt.AlignRight))
                tt = row["total"]
                self.tabela.setItem(i, 5, self._item(moeda(tt) if tt is not None else "-", Qt.AlignRight))

                # Soma total
                if row["tipo"] == "Venda":
                    total_entradas += row["total"]
                else:
                    total_saidas += row["total"]

            lucro = total_entradas - total_saidas

            self.lbl_entradas.setText(moeda(total_entradas))
            self.lbl_saidas.setText(moeda(total_saidas))
            self.lbl_saldo.setText(moeda(lucro))
            # lucro negativo (prejuízo) fica vermelho
            if lucro < 0:
                self.lbl_saldo.setStyleSheet("color: #b91c1c;")
            else:
                self.lbl_saldo.setStyleSheet("")
            n = len(todos)
            self.lbl_contagem.setText(f"{n} registro" if n == 1 else f"{n} registros")

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar fluxo de caixa:\n{e}")
        finally:
            conn.close()

    # ===============================================================
    # Função: limpar filtros
    # ===============================================================
    def limpar_filtros(self):
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        self.data_fim.setDate(QDate.currentDate())
        self.carregar_fluxo()


# ===============================================================
# Execução
# ===============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    janela = FluxoCaixaApp()
    janela.show()
    sys.exit(app.exec_())