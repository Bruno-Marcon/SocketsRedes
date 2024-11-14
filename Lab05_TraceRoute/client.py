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
        print(f"\nTraceroute para {destination} ({socket.gethostbyname(destination)}), {self.MAX_HOPS} saltos máximos:\n")

        try:
            dest_addr = socket.gethostbyname(destination)
        except socket.gaierror as e:
            print(f"Erro: {e.strerror}. Não foi possível resolver o host {destination}.")
            return

        rtts = []  # Lista para armazenar os RTTs
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
                    try:
                        my_socket.sendto(packet, (dest_addr, 0))
                    except Exception as e:
                        print(f"Falha ao enviar o pacote ICMP no salto {ttl}. Erro: {e}")
                        continue  # Tente o próximo envio

                    start_time = self.default_timer()

                    # Espera resposta
                    started_select = self.default_timer()
                    ready = select.select([my_socket], [], [], self.TIMEOUT)
                    time_in_select = (self.default_timer() - started_select)

                    if ready[0] == []:
                        print(f"{ttl:2}  *        *        *    Request timed out.")
                        continue

                    try:
                        recv_packet, addr = my_socket.recvfrom(1024)
                    except socket.timeout:
                        print(f"Timeout ao receber resposta do salto {ttl}.")
                        continue
                    except Exception as e:
                        print(f"Falha ao receber o pacote ICMP no salto {ttl}. Erro: {e}")
                        continue

                    time_received = self.default_timer()
                    icmp_header = recv_packet[20:28]
                    
                    try:
                        types, code, checksum, packet_id, sequence = struct.unpack("bbHHh", icmp_header)
                    except struct.error as e:
                        print(f"Falha ao desempacotar o cabeçalho ICMP no salto {ttl}. Erro: {e}")
                        continue

                    # Resolver o nome do host
                    try:
                        host_name = socket.gethostbyaddr(addr[0])[0]
                    except socket.herror:
                        print(f"Falha ao resolver o nome do host para o IP {addr[0]}")
                        host_name = addr[0]  # Se falhar, usa o endereço IP

                    if types == 11:
                        bytes_recvd = struct.calcsize("d")
                        time_sent = struct.unpack("d", recv_packet[28:28 + bytes_recvd])[0]
                        rtt = int((time_received - time_sent) * 1000)
                        rtts.append(rtt)
                        print(f"{ttl:2}  rtt={rtt:3} ms  {addr[0]} ({host_name})")
                    elif types == 3:
                        print(f"{ttl:2}  Destino inacessivel")
                    elif types == 0:
                        bytes_recvd = struct.calcsize("d")
                        time_sent = struct.unpack("d", recv_packet[28:28 + bytes_recvd])[0]
                        rtt = int((time_received - time_sent) * 1000)
                        rtts.append(rtt)
                        print(f"{ttl:2}  rtt={rtt:3} ms  {addr[0]} ({host_name})")
                        print(f"\nDestino ({host_name}) alcançado!")
                        break  # Interrompe o loop de tentativas e saltos quando o destino for alcançado
                except socket.error as e:
                    print(f"Falha ao criar o socket no salto {ttl}. Erro: {e}")
                    return
                except Exception as e:
                    print(f"Erro inesperado no salto {ttl}. Erro: {e}")
                finally:
                    my_socket.close()

            # Se o destino foi alcançado, sai do loop de saltos
            if rtts:
                print("\nResumo do Traceroute:")
                print(f"RTT Total: {sum(rtts)} ms")
                print(f"RTT Máximo: {max(rtts)} ms")
                print(f"RTT Mínimo: {min(rtts)} ms")
                break
        else:
            print("Destino não alcançado no número máximo de saltos.")

if __name__ == '__main__':
    traceroute = Traceroute(timeout=2, max_hops=30, tries=2)
    #traceroute.get_route("google.com")
    traceroute.get_route("192.168.1.1")
    
