import sys
import pymysql

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox
)


# ============================================================
# CONFIGURAÇÃO DO BANCO
# ============================================================

HOST = "sistemasintegrados.myddns.me"
USUARIO_BANCO = "root"
SENHA_BANCO = "K@rraP1x0"
BANCO = "stock"
PORT = 27317


# ============================================================
# VISUAL (folha de estilo)
# ============================================================

ESTILO = """
QDialog { background: #f3f4f6; }
QWidget { font-size: 13px; color: #1f2937; }
QLabel { background: transparent; }

QFrame#card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}

QLabel#logo {
    background: #2563eb;
    color: #ffffff;
    font-size: 28px;
    font-weight: 800;
    border-radius: 16px;
}
QLabel#titulo { font-size: 22px; font-weight: 700; color: #111827; }
QLabel#subtitulo { color: #6b7280; }
QLabel#rotulo { font-weight: 600; color: #374151; }

QLineEdit {
    background: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 10px 12px;
    min-height: 20px;
}
QLineEdit:focus { border: 1px solid #2563eb; }

QPushButton {
    background: #e5e7eb;
    color: #1f2937;
    border: none;
    border-radius: 8px;
    padding: 11px 16px;
    font-weight: 600;
}
QPushButton:hover { background: #d1d5db; }
QPushButton:pressed { background: #9ca3af; }
QPushButton:disabled { background: #bfdbfe; color: #ffffff; }
QPushButton#primario { background: #2563eb; color: #ffffff; font-size: 14px; }
QPushButton#primario:hover { background: #1d4ed8; }
QPushButton#primario:disabled { background: #93c5fd; }
"""


# ============================================================
# TELA DE LOGIN
# ============================================================

class Login(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login")
        self.setFixedSize(400, 500)
        self.setStyleSheet(ESTILO)

        self.criar_tela()

    # ========================================================
    # CRIAR TELA
    # ========================================================

    def criar_tela(self):

        externo = QVBoxLayout()
        externo.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(6)

        # ----------------------------------------------------
        # LOGO + TÍTULO
        # ----------------------------------------------------

        logo = QLabel("E")
        logo.setObjectName("logo")
        logo.setFixedSize(60, 60)
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo, 0, Qt.AlignHCenter)
        layout.addSpacing(8)

        titulo = QLabel("Sistema de Estoque")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel("Entre com seu usuário e senha")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitulo)
        layout.addSpacing(16)

        # ----------------------------------------------------
        # USUÁRIO
        # ----------------------------------------------------

        label_usuario = QLabel("Usuário")
        label_usuario.setObjectName("rotulo")

        self.usuario = QLineEdit()

        self.usuario.setPlaceholderText(
            "Digite o usuário"
        )

        layout.addWidget(label_usuario)
        layout.addWidget(self.usuario)
        layout.addSpacing(6)

        # ----------------------------------------------------
        # SENHA
        # ----------------------------------------------------

        label_senha = QLabel("Senha")
        label_senha.setObjectName("rotulo")

        self.senha = QLineEdit()

        self.senha.setPlaceholderText(
            "Digite a senha"
        )

        self.senha.setEchoMode(
            QLineEdit.Password
        )

        layout.addWidget(label_senha)
        layout.addWidget(self.senha)
        layout.addSpacing(14)

        # ----------------------------------------------------
        # BOTÃO ENTRAR
        # ----------------------------------------------------

        self.botao_entrar = QPushButton(
            "Entrar"
        )
        self.botao_entrar.setObjectName("primario")
        self.botao_entrar.setMinimumHeight(44)
        self.botao_entrar.setCursor(Qt.PointingHandCursor)
        self.botao_entrar.setDefault(True)

        self.botao_entrar.clicked.connect(
            lambda _checked=False: self.fazer_login()
        )

        layout.addWidget(
            self.botao_entrar
        )

        # ----------------------------------------------------
        # BOTÃO SAIR
        # ----------------------------------------------------

        botao_sair = QPushButton(
            "Sair"
        )
        botao_sair.setMinimumHeight(40)
        botao_sair.setCursor(Qt.PointingHandCursor)

        botao_sair.clicked.connect(
            self.close
        )

        layout.addWidget(
            botao_sair
        )

        externo.addWidget(card)
        self.setLayout(
            externo
        )

        # ENTER NO USUÁRIO PULA PARA A SENHA
        self.usuario.returnPressed.connect(
            self.senha.setFocus
        )

        # ENTER NA SENHA
        self.senha.returnPressed.connect(
            self.fazer_login
        )

        self.usuario.setFocus()

    # ========================================================
    # FAZER LOGIN
    # ========================================================

    def fazer_login(self):

        usuario = self.usuario.text().strip()
        senha = self.senha.text()

        # ----------------------------------------------------
        # VERIFICAR CAMPOS
        # ----------------------------------------------------

        if not usuario:

            QMessageBox.warning(
                self,
                "Atenção",
                "Digite o usuário."
            )

            self.usuario.setFocus()

            return

        if not senha:

            QMessageBox.warning(
                self,
                "Atenção",
                "Digite a senha."
            )

            self.senha.setFocus()

            return

        # ----------------------------------------------------
        # CONECTAR AO MYSQL
        # ----------------------------------------------------

        # feedback visual enquanto conecta
        self.botao_entrar.setEnabled(False)
        self.botao_entrar.setText("Entrando...")
        QApplication.processEvents()

        try:

            conexao = pymysql.connect(
                host=HOST,
                user=USUARIO_BANCO,
                password=SENHA_BANCO,
                database=BANCO,
                port = PORT
            )

            cursor = conexao.cursor()

            # ------------------------------------------------
            # CONSULTAR USUÁRIO
            # ------------------------------------------------

            sql = """
                SELECT id
                FROM usuarios
                WHERE usuario = %s
                AND senha = %s
                AND ativo = 1
            """

            cursor.execute(
                sql,
                (usuario, senha)
            )

            resultado = cursor.fetchone()

            cursor.close()
            conexao.close()

            # ------------------------------------------------
            # LOGIN CORRETO
            # ------------------------------------------------

            if resultado:

                QMessageBox.information(
                    self,
                    "Login",
                    "Login efetuado com sucesso!"
                )

                self.accept()

            # ------------------------------------------------
            # LOGIN INCORRETO
            # ------------------------------------------------

            else:

                QMessageBox.warning(
                    self,
                    "Login",
                    "Usuário ou senha inválidos."
                )

                self.senha.clear()
                self.senha.setFocus()

        except pymysql.MySQLError as erro:

            QMessageBox.critical(
                self,
                "Erro",
                f"Erro ao conectar ao banco:\n\n{erro}"
            )

        finally:

            self.botao_entrar.setEnabled(True)
            self.botao_entrar.setText("Entrar")


# ============================================================
# PROGRAMA
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    janela = Login()

    janela.exec_()


    sys.exit()