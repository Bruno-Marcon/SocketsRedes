from socket import *
import sys
import os
import threading

HOST = '127.0.0.1'
PORT = 6787
ENDERECOSERVIDOR = (HOST, PORT)

# Função para tratar cada conexão
def handle_client(connectionSocket, addr):
    print(f"Conexão estabelecida com IP: {addr[0]} Porta: {addr[1]}")

    try:
        while True:
            # Recebe a mensagem do cliente
            message = connectionSocket.recv(4096).decode('utf-8')
            if not message:  # sai do looping se não houver mensagem
                break

            # Pega o nome do arquivo solicitado
            filename = message.split()[1]
            # Localiza o arquivo na pasta
            file_path = os.path.join('arquivos', filename[1:])

            # Tenta abrir o arquivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Cria a resposta com o conteúdo
                response = f"HTTP/1.1 200 OK\nContent-Type: text/html\n\n{content}"

            except IOError:
                # Envia resposta de erro se não achar o arquivo
                response = "HTTP/1.1 404 NOT FOUND\nContent-Type: text/html\n\nArquivo não encontrado"

            # Envia a resposta para o cliente
            connectionSocket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Erro durante a comunicação: {e}")
    
    finally:
        # Fecha o socket do cliente
        connectionSocket.close()

# Cria o socket do servidor
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(ENDERECOSERVIDOR)
serverSocket.listen(5)

print("Servidor iniciado")
print("Pronto para servir...")

while True:
    connectionSocket, addr = serverSocket.accept()

    # Cria uma nova thread
    threading.Thread(target=handle_client, args=(connectionSocket, addr)).start()

# Fecha o socket do servidor
serverSocket.close()
sys.exit()
