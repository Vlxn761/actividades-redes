import sys
import socket
from utils import check_routes, parse_packet, create_packet


if __name__ == "__main__":
    router_address = (sys.argv[1], int(sys.argv[2]))
    path = sys.argv[3]

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind(router_address)

    counter = {}

    while True:
      msg, paquete_ip = router_socket.recvfrom(1024)
      msg = parse_packet(msg)
      if msg.TTL <= 0:
         print(f"Se recibió paquete {paquete_ip} con TTL 0")
         break
      msg.TTL -= 1
      destination_address = (msg.IP, msg.port)
      if destination_address == router_address:
         print(msg.data.decode())
      else:
        next_hop = check_routes(path, destination_address, counter)
        if next_hop == None:
          print(f"No hay rutas hacia {destination_address} para {paquete_ip}")
        else:
          print(f"redirigiendo paquete {paquete_ip} con destino final {destination_address} desde {router_address} hacia {next_hop}")          
          msg = create_packet(msg)
          router_socket.sendto(msg, next_hop)
