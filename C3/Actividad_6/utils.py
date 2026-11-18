class IPPacket:
  def __init__(
      self,
      IP: str,
      port: int,
      TTL: int,
      id: int,
      size: int,
      data: bytes, 
      offset: int = 0,
      FLAG: int = 0
  ):
    self.IP = IP
    self.port = port
    self.TTL = TTL
    self.id = id
    self.offset = offset
    self.size = size
    self.FLAG = FLAG
    self.data = data

def parse_packet(IP_packet):
  IP = IP_packet[0:4]
  IP = ".".join(str(b) for b in IP)
  port = int.from_bytes(IP_packet[4:6], byteorder="big")
  TTL = IP_packet[6]
  id = int.from_bytes(IP_packet[7:9], byteorder="big")
  offset = int.from_bytes(IP_packet[9:13], byteorder="big")
  size = int.from_bytes(IP_packet[13:17], byteorder="big")
  FLAG = IP_packet[17]
  data = IP_packet[18:]

  packet = IPPacket(
        IP=IP, 
        port=port,
        TTL=TTL,
        id=id,
        offset=offset,
        size=size,
        FLAG=FLAG,
        data=data
        )
  
  return packet

def create_packet(parsed_IP_packet):
  IP = parsed_IP_packet.IP
  IP = bytes(int(n) for n in IP.split("."))
  port = parsed_IP_packet.port.to_bytes(2, byteorder="big")
  TTL = parsed_IP_packet.TTL.to_bytes(1, byteorder="big")
  id = parsed_IP_packet.id.to_bytes(2, byteorder="big")
  offset = parsed_IP_packet.offset.to_bytes(4, byteorder="big")
  size = parsed_IP_packet.size.to_bytes(4, byteorder="big")
  FLAG = parsed_IP_packet.FLAG.to_bytes(1, byteorder="big")
  data = parsed_IP_packet.data
  return IP + port + TTL + id + offset + size + FLAG + data


def check_routes(routes_file_name, destination_address, counter):
  destination_ip, destination_port = destination_address

  routes = []
  area = None

  with open(routes_file_name, "r") as file:
    for line in file:
      red, p_inicial, p_final, next_hop_IP, next_hop_puerto, next_hop_mtu = line.split()
      IP, mask = red.split("/")
      if IP == destination_ip and int(p_inicial) <= int(destination_port) <= int(p_final):
        if area is None:
          area = f"{red} {p_inicial} {p_final}"
        routes.append(((next_hop_IP, int(next_hop_puerto)), next_hop_mtu))

  if not routes:
    return None

  ind = counter.get(area, 0)
  counter[area] = (ind + 1) % len(routes)
  return routes[ind]

def fragment_IP_packet(IP_packet, MTU):
  total_size = len(IP_packet)
  if total_size <= MTU:
    return [IP_packet]
  
  frags = []
  parsed_IP_packet = parse_packet(IP_packet)
  data_size = parsed_IP_packet.size
  packet_offset = 0
  frag_offset = 0
  if parsed_IP_packet.offset != 0:
    packet_offset = parsed_IP_packet.offset
  headers_size = 18
  size = MTU - headers_size
  FLAG = 1


  while frag_offset < data_size:
    # Último fragmento
    if (data_size - frag_offset < size):
      data = parsed_IP_packet.data[frag_offset:]
      size = len(data)
      if parsed_IP_packet.FLAG == 0:
        FLAG = 0
    else:
      data = parsed_IP_packet.data[frag_offset:frag_offset + size]

    fragment = IPPacket(
      IP=parsed_IP_packet.IP, 
      port=parsed_IP_packet.port,
      TTL=parsed_IP_packet.TTL,
      id=parsed_IP_packet.id,
      offset=packet_offset,  
      size=size,
      FLAG=FLAG,
      data=data
    )

    fragment = create_packet(fragment)
    frags.append(fragment)
    frag_offset += size
    packet_offset += size

  return frags

def reassemble_IP_packet(fragment_list):
  if len(fragment_list) == 1:
    packet = fragment_list[0]
    if packet.offset == 0 and packet.FLAG == 0:
      return packet
    return None
  
  sorted_fragments = sorted(fragment_list, key=lambda f: f.offset)
  last_fragment = sorted_fragments[-1]
  if last_fragment.FLAG == 1:
    return None

  data = b""

  for frag in sorted_fragments:
    if frag.offset != len(data):
      return None
    data += frag.data

  packet = IPPacket(
    IP=last_fragment.IP, 
    port=last_fragment.port,
    TTL=last_fragment.TTL,
    id=last_fragment.id,
    offset=0,  
    size=len(data),
    FLAG=0,
    data=data
  )

  return packet
