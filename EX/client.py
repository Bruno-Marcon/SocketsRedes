from socket import *
import time

HOST = '127.0.0.1'
PORT = 12000
PINGS = 10

def start_client():
    client = socket(AF_INET, SOCK_DGRAM)
    client.settimeout(1)
    return client

def ping(client):
    send = ''
    avgRTT = 0
    packetLoss = 0.0
    minRTT = 0.0
    maxRTT = 0.0

    for num in range(PINGS):
        timeS = time.time() 
        send = 'Ping ' + str(num + 1) + ' '+ str(timeS)
        client.sendto(send.encode(), (HOST,PORT))
        
        try:
            recv, orgin = client.recvfrom(1024)
            timeR = time.time()
            RTT = timeR - timeS
            avgRTT += RTT

            if minRTT == 0.0:
                minRTT = RTT
            else:
                if minRTT > RTT:
                    minRTT = RTT
            
            if maxRTT < RTT:
                maxRTT = RTT

            print(recv.decode())
            print('RTT: ' + str(RTT) + '\n')
        except timeout:
            print('Request timed out\n')
            packetLoss += 1

    print('MIN RRT: ' + str(minRTT))
    print('MAX RRT: ' + str(maxRTT))
    print('AVG RRT: ' + str(avgRTT/(10-packetLoss)))
    print('PACKET LOSS: ' + str((packetLoss/10.0)*100) + '%' )

def main():
    client = start_client()
    ping(client)
    client.close()

if __name__ == "__main__":
    main()