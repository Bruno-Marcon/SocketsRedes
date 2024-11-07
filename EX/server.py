import random
from socket import *

HOST = '127.0.0.1'
PORT = 12000

def start_server():
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind((HOST, PORT))
    print('Server Iniciado')
    return serverSocket

def main():
    serverSocket = start_server()
    packet_number = 0

    while True:
        rand = random.randint(0, 10)
        message, address = serverSocket.recvfrom(1024)
        packet_number += 1
        print(f'Pacote #{packet_number} recebido , tamanho: {len(message)}')

        message = message.upper()
        
        if rand < 4:
            print(f'Pacote #{packet_number} perdido, tamanho: {len(message)}')
            continue
        
        serverSocket.sendto(message, address)
        print(f'Enviando pacote #{packet_number}, tamanho: {len(message)}')

        

if __name__ == "__main__":
    main()
