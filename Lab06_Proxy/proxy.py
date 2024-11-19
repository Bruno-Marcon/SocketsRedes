import socket
import urllib.parse
import time

# Dicionário como cache
cache_memoria = {}
ttl = 60  # 1 minuto de validade para o cache

# Função para verificar e usar o cache em memória
def verificar_cache(url):
    if url in cache_memoria:
        dados, timestamp = cache_memoria[url]
        if time.time() - timestamp < ttl:  # Verifica se o cache ainda é válido
            print(f"[INFO] Usando cache da memória para: {url}")
            return dados
        else:
            print(f"[INFO] Cache expirado para: {url}")
            del cache_memoria[url]
    return None

# Função para armazenar o cache em memória
def armazenar_cache(url, dados):
    cache_memoria[url] = (dados, time.time())  # Armazenar junto com timestamp

# Função para criar a requisição HTTP
def criar_requisicao(metodo, caminho, host, cabecalhos=None, corpo=None):
    requisicao = f"{metodo} {caminho} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n"
    if cabecalhos:
        requisicao += cabecalhos
    if corpo:
        requisicao += f"Content-Length: {len(corpo)}\r\n\r\n{corpo.decode(errors='ignore')}"
    else:
        requisicao += "\r\n"
    return requisicao.encode()

# Função para processar a requisição do cliente
def processar_requisicao(cliente_socket):
    try:
        # Recebe e processa a solicitação
        requisicao = cliente_socket.recv(4096)
        primeira_linha = requisicao.split(b'\n')[0]
        metodo, url, _ = primeira_linha.split()

        if metodo not in [b'GET', b'POST']:
            cliente_socket.sendall(b"HTTP/1.1 405 Metodo Nao Permitido\r\n\r\n")
            return

        # Decodifica a URL e ajusta o formato
        url_decodificada = url.decode()
        url_processada = urllib.parse.urlparse(
            url_decodificada if url.startswith(b'http') else 'http://' + url_decodificada.lstrip('/')
        )
        host = url_processada.hostname
        caminho = url_processada.path or '/'

        if not host:
            cliente_socket.sendall(b"HTTP/1.1 400 Requisicao Invalida\r\n\r\n")
            return

        # Verifica se a resposta está no cache
        resposta_cache = verificar_cache(url_decodificada)
        if resposta_cache:
            cliente_socket.sendall(resposta_cache)
            return

        # Conecta ao servidor de destino
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket_servidor:
                socket_servidor.connect((host, 80))
                print(f"[INFO] Conectado ao servidor {host}")

                if metodo == b'GET':
                    requisicao_completa = criar_requisicao("GET", caminho, host)
                else:
                    cabecalhos = requisicao.split(b'\n')[1:]
                    comprimento_conteudo = 0
                    corpo = b""

                    for cabecalho in cabecalhos:
                        if b'Content-Length' in cabecalho:
                            comprimento_conteudo = int(cabecalho.split(b':')[1].strip())
                    
                    if comprimento_conteudo > 0:
                        corpo = requisicao.split(b'\r\n\r\n')[1]
                        while len(corpo) < comprimento_conteudo:
                            corpo += cliente_socket.recv(4096)

                    cabecalhos_str = b'\r\n'.join(cabecalhos).decode(errors='ignore')
                    requisicao_completa = criar_requisicao("POST", caminho, host, cabecalhos_str, corpo)

                socket_servidor.sendall(requisicao_completa)

                # Recebe a resposta
                resposta = b""
                while (dados := socket_servidor.recv(4096)):
                    resposta += dados

                # Tratamento de erros com a resposta
                if b"404 Not Found" in resposta:
                    print(f"[INFO] Erro 404 - Página não encontrada para a URL: {url_decodificada}")
                elif b"403 Forbidden" in resposta:
                    print(f"[INFO] Erro 403 - Acesso proibido para a URL: {url_decodificada}")
                elif b"500 Internal Server Error" in resposta:
                    print(f"[INFO] Erro 500 - Erro no servidor para a URL: {url_decodificada}")
                else:
                    # Caso contrário, armazena a resposta no cache
                    if resposta:
                        armazenar_cache(url_decodificada, resposta)
                        print(f"[INFO] Cache salvo para: {url_decodificada}")

                # Envia a resposta ao cliente
                cliente_socket.sendall(resposta)

        except socket.error as erro_socket:
            print(f"[INFO] Erro ao conectar ao servidor: {erro_socket}")
            cliente_socket.sendall(b"HTTP/1.1 500 Erro Interno do Servidor\r\n\r\n")
    except Exception as erro:
        print(f"[INFO] Erro ao processar a requisição: {erro}")
        cliente_socket.sendall(b"HTTP/1.1 400 Requisicao Invalida\r\n\r\n")

    cliente_socket.close()

def iniciar_proxy(ENDERECOSERVIDOR):
    servidor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor_socket.bind(ENDERECOSERVIDOR)
    servidor_socket.listen(5)
    print(f"[INFO] Servidor proxy ativo em {ENDERECOSERVIDOR}")

    while True:
        cliente_socket, endereco_cliente = servidor_socket.accept()
        print(f"[INFO] Conexão recebida de {endereco_cliente}")
        processar_requisicao(cliente_socket)

def main():
    HOST2 = '0.0.0.0'
    PORT = 8888
    ENDERECOSERVIDOR = (HOST2, PORT)
    
    iniciar_proxy(ENDERECOSERVIDOR)

if __name__ == "__main__":
    main()
