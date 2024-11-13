from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8  # Tipo ICMP Echo Request

def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = ord(string[count+1]) * 256 + ord(string[count])
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2
    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1])
        csum = csum & 0xffffffff
    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout
    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return "Request timed out."
        
        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Preenche o cabeçalho ICMP
        icmpHeader = recPacket[20:28]  # Cabeçalho ICMP
        type, code, checksum, pID, sequence = struct.unpack("bbHHh", icmpHeader)
        
        if pID == ID:
            bytesInDouble = struct.unpack("d", recPacket[28:36])[0]
            delay = (timeReceived - bytesInDouble) * 1000  # Atraso em milissegundos
            return delay
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    # Cabeçalho do ICMP: tipo (8), código (8), checksum (16), id (16), sequência (16)
    myChecksum = 0

    # Cria um cabeçalho com checksum zerado
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())  # Dados para calcular o tempo de resposta

    # Calcula o checksum nos dados e no cabeçalho
    myChecksum = checksum(str(header + data))

    # Coloca o checksum no cabeçalho
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    # Envia o pacote ICMP
    mySocket.sendto(packet, (destAddr, 1))  # AF_INET endereço precisa ser uma tupla (host, porta)

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")
    mySocket = socket(AF_INET, SOCK_RAW, icmp)
    myID = os.getpid() & 0xFFFF  # Obtém o PID do processo atual
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay

def ping(host, timeout=1):
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")

    # Envia solicitações de ping para o servidor, separadas por aproximadamente um segundo
    while 1:
        delay = doOnePing(dest, timeout)
        print(f"Delay: {delay} ms")
        time.sleep(1)

if __name__ == "__main__":
    ping("google.com", timeout=1)  # Substitua por qualquer endereço que queira testar
