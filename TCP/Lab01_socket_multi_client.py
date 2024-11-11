import socket

HOST = '127.0.0.1'
PORT = 6787
ENDERECOSERVIDOR = (HOST, PORT)

def Main():
    #Criação do socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #realiza conexão com o server
        clientSocket.connect((ENDERECOSERVIDOR))
    except socket.error as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return

    while True:
        filename = input("Digite o nome do arquivo que deseja (ou não digite nada para sair): ")
        
        # Envia a solicitação GET para o servidor
        clientSocket.send(f"GET /{filename} HTTP/1.1".encode('utf-8'))
        
        try:
            #Recebe resposta do server
            response = clientSocket.recv(4096).decode('utf-8')
            print(f'Resposta do servidor:\n{response}')
        except ConnectionAbortedError:
            print("A conexão foi encerrada pelo servidor.")
            break
            #encerra o socket
    clientSocket.close()

if __name__ == '__main__':
    Main()
