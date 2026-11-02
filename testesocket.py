import socket

HOST = "192.168.100.33"
PORT = 22
TIMEOUT = 30 # segundos


def enviar(mensagem: bytes, host=HOST, port=PORT, timeout=TIMEOUT) -> bytes:
    """Abre a conexão, envia os bytes, lê a resposta e fecha."""
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(mensagem)   # sendall garante que tudo foi enviado
        return s.recv(1024)   # recebe a resposta


if __name__ == "__main__":
    try:
        resposta = enviar("Ola, Mundo".encode("utf-8"))   # texto -> bytes
        print("Bytes recebidos:", resposta)
        print("Como texto:", resposta.decode("utf-8", errors="replace"))
    except socket.timeout:
        print("Tempo esgotado: o servidor não respondeu.")
    except ConnectionRefusedError:
        print("Conexão recusada: confira o IP, a porta e se o servidor está ligado.")
    except OSError as e:
        print(f"Erro de rede: {e}")