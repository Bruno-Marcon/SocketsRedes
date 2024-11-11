import random
from socket import *

HOST = '127.0.0.1'
PORT = 12000
ENDERECOSERVIDOR = (HOST, PORT)

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind((ENDERECOSERVIDOR))
print('Server Iniciado')
while True:
 rand = random.randint(0, 10)

 message, address = serverSocket.recvfrom(1024)

 message = message.upper()

 if rand < 4:
    continue
 serverSocket.sendto(message, address)