import os
import socket
import struct
import select
import time
import errno

class Traceroute:
    ICMP_ECHO_REQUEST = 8
    MAX_HOPS = 30
    TIMEOUT = 2.0
    TRIES = 2

    def __init__(self, timeout=2, max_hops=30, tries=2):
        self.timeout = timeout
        self.max_hops = max_hops
        self.tries = tries
        self.default_timer = time.time

    def checksum(self, source_string):
        # Calcula o checksum para verificar a integridade do pacote ICMP
        csum = 0
        count_to = (len(source_string) // 2) * 2
        count = 0

        while count < count_to:
            this_val = (source_string[count + 1] << 8) + source_string[count]
            csum = csum + this_val
            csum = csum & 0xffffffff
            count = count + 2

        if count_to < len(source_string):
            csum = csum + source_string[len(source_string) - 1]
            csum = csum & 0xffffffff

        csum = (csum >> 16) + (csum & 0xffff)
        csum = csum + (csum >> 16)
        answer = ~csum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def build_packet(self):
        # Cria o pacote ICMP com o checksum
        pid = os.getpid() & 0xFFFF
        my_checksum = 0
        header = struct.pack("bbHHh", self.ICMP_ECHO_REQUEST, 0, my_checksum, pid, 1)
        data = struct.pack("d", self.default_timer())
        my_checksum = self.checksum(header + data)
        header = struct.pack("bbHHh", self.ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), pid, 1)
        return header + data

    def get_route(self, destination):
        # Realiza o traceroute para o destino especificado
        print(f"\nTraceroute para {destination} ({socket.gethostbyname(destination)}), {self.MAX_HOPS} saltos máximos:")

        try:
            dest_addr = socket.gethostbyname(destination)
        except socket.gaierror as e:
            print(f"Erro: {e.strerror}. Não foi possível resolver o host.")
            return

        for ttl in range(1, self.MAX_HOPS + 1):
            for attempt in range(self.TRIES):
                try:
                    # Criação do socket RAW
                    icmp = socket.getprotobyname("icmp")
                    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
                    my_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('I', ttl))
                    my_socket.settimeout(self.TIMEOUT)

                    # Construção e envio do pacote ICMP
                    packet = self.build_packet()
                    my_socket.sendto(packet, (dest_addr, 0))
                    start_time = self.default_timer()

                    # Espera pela resposta
                    started_select = self.default_timer()
                    ready = select.select([my_socket], [], [], self.TIMEOUT)
                    time_in_select = (self.default_timer() - started_select)

                    if ready[0] == []:  # Timeout
                        print(f"{ttl:2}  *        *        *    Request timed out.")
                        continue

                    recv_packet, addr = my_socket.recvfrom(1024)
                    time_received = self.default_timer()
                    icmp_header = recv_packet[20:28]
                    types, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)

                    if types == 11:  # Time Exceeded
                        bytes_recvd = struct.calcsize("d")
                        time_sent = struct.unpack("d", recv_packet[28:28 + bytes_recvd])[0]
                        print(f"{ttl:2}  rtt={int((time_received - time_sent) * 1000):3} ms  {addr[0]}")
                    elif types == 3:  # Destination Unreachable
                        print(f"{ttl:2}  Destination Unreachable")
                    elif types == 0:  # Echo Reply (chegou ao destino)
                        bytes_recvd = struct.calcsize("d")
                        time_sent = struct.unpack("d", recv_packet[28:28 + bytes_recvd])[0]
                        print(f"{ttl:2}  rtt={int((time_received - time_sent) * 1000):3} ms  {addr[0]}")
                        return
                    else:
                        print(f"{ttl:2}  Erro desconhecido")
                        break

                except socket.error as e:
                    print(f"Erro ao criar o socket: {e}")
                    return
                except Exception as e:
                    print(f"Erro: {e}")
                finally:
                    my_socket.close()

if __name__ == '__main__':
    traceroute = Traceroute(timeout=2, max_hops=30, tries=2)
    traceroute.get_route("google.com")
    traceroute.get_route("facebook.com")
    traceroute.get_route("1.1.1.1")
    traceroute.get_route("8.8.8.8")
