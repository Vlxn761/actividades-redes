import sys
import socket
from utils import check_routes, parse_packet, create_packet, fragment_IP_packet, reassemble_IP_packet


if __name__ == "__main__":
    router_address = (sys.argv[1], int(sys.argv[2]))
    path = sys.argv[3]

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind(router_address)

    counter = {}
    packets = {}

    while True:
      msg, paquete_ip = router_socket.recvfrom(1024)
      msg = parse_packet(msg)

      if msg.TTL <= 0:
         print(f"Se recibió paquete {paquete_ip} con TTL 0")
         continue
      
      msg.TTL -= 1
      destination_address = (msg.IP, msg.port)

      if destination_address == router_address:
        if msg.id not in packets:
          packets[msg.id] = []
        packets[msg.id].append(msg) 
        packet = reassemble_IP_packet(packets[msg.id])
        if packet is not None:
          print(packet.data.decode())
      else:
        next_hop, MTU = check_routes(path, destination_address, counter)
        if next_hop == None:
          print(f"No hay rutas hacia {destination_address} para {paquete_ip}")
        else:
          print(f"redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {router_address} hacia {next_hop}")          
          msg = create_packet(msg)
          fragments = fragment_IP_packet(msg, int(MTU))
          for fragment in fragments:
            router_socket.sendto(fragment, next_hop)

