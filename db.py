import os
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv é opcional se as variáveis já estiverem no ambiente
    pass


class ConfiguracaoError(RuntimeError):
    """Variável de ambiente obrigatória ausente."""


def _env(nome, padrao=None):
    valor = os.environ.get(nome, padrao)
    if valor in (None, ""):
        raise ConfiguracaoError(
            f"Configuração ausente: defina a variável {nome} no arquivo .env."
        )
    return valor


@contextmanager
def conexao():
    """Abre uma conexão; faz commit se tudo der certo e rollback se houver erro.

    Uso:
        with conexao() as conn, conn.cursor() as cur:
            cur.execute("SELECT ...", (param,))
    """
    conn = pymysql.connect(
        host=_env("DB_HOST"),
        user=_env("DB_USER"),
        password=_env("DB_PASSWORD"),
        database=_env("DB_NAME"),
        port=int(_env("DB_PORT", "3306")),
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=5,
        read_timeout=15,
        write_timeout=15,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()