from socket import *
import sys
import os

HOST = '127.0.0.1'
PORT = 6787
ENDERECOSERVIDOR = (HOST, PORT)

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind((ENDERECOSERVIDOR))
serverSocket.listen(5)
print("Servidor iniciado")
print("Pronto para servir...")

while True:
    # Estabelece a conexão
    connectionSocket, addr = serverSocket.accept()
    print(f"Conexão estabelecida com IP: {addr[0]} Porta: {addr[1]}")

    try:
        while True:
            # Recebe a mensagem do cliente
            message = connectionSocket.recv(4096).decode('utf-8')
            if not message:  # sai do looping se tiver sem mensagem
                break

            # Pega o nome do arquivo solicitado
            filename = message.split()[1]
            # Localiza o arquivo na pasta
            file_path = os.path.join('arquivos', filename[1:])

            # Tenta abrir o arquivo
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Cria a resposta com o conteudo
                response = f"HTTP/1.1 200 OK\n\n{content}"
            except IOError:
                # Envia resposta de erro se não achar o arquivo
                response = "HTTP/1.1 404 NOT FOUND\nContent-Type: text/plain\n\nArquivo não encontrado"
            
            # Envia a resposta para o cliente
            connectionSocket.send(response.encode('utf-8'))

    except Exception as e:
        print(f"Erro durante a comunicação: {e}")
    
    finally:
        # Fecha o socket do client
        connectionSocket.close()

# Fecha o socket do servidor
serverSocket.close()
sys.exit()
