class IPPacket:
  def __init__(
      self,
      IP: str,
      port: int,
      TTL: int,
      data: bytes 
  ):
    self.IP = IP
    self.port = port
    self.TTL = TTL
    self.data = data

def parse_packet(IP_packet):
  IP = IP_packet[0:4]
  IP = ".".join(str(b) for b in IP)
  port = int.from_bytes(IP_packet[4:6], byteorder="big")
  TTL = IP_packet[6]
  data = IP_packet[7:]

  IPPacket = IPPacket(
        IP=IP, 
        port=port,
        TTL=TTL,
        data=data
        )
  
  return IPPacket

def create_packet(parsed_IP_packet):
  IP = parsed_IP_packet.IP
  IP = bytes(int(n) for n in IP.split("."))
  port = parsed_IP_packet.port.to_bytes(2, byteorder="big")
  TTL = parsed_IP_packet.TTL.to_bytes(1, byteorder="big")
  data = parsed_IP_packet.data
  return IP + port + TTL + data


def check_routes(routes_file_name, destination_address, counter):
  destination_ip, destination_port = destination_address

  routes = []
  area = None

  with open(routes_file_name, "r") as file:
    for line in file:
      red, p_inicial, p_final, next_hop_IP, next_hop_puerto = line.split()
      IP, mask = red.split("/")
      if IP == destination_ip and int(p_inicial) <= int(destination_port) <= int(p_final):
        if area is None:
          area = f"{red} {p_inicial} {p_final}"
        routes.append((next_hop_IP, int(next_hop_puerto)))

  if not routes:
    return None

  ind = counter.get(area, 0)
  counter[area] = (ind + 1) % len(routes)
  return routes[ind]

