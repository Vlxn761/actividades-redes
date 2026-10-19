import socket
import random

DEBUG = True

def d_print(*args, **kwargs):
  if DEBUG: 
    print(*args, **kwargs)

class Segment:
  def __init__(
      self,
      source: int = 5000,
      destination: int = 5000,
      seq: int = 0,
      ack_num: int = 0,
      message_length: int = 0,
      ACK: bool = False,
      SYN: bool = False,
      FIN: bool = False,
      LEN: bool = False,
      data: bytes = b"",
  ):
    self.source = source
    self.destination = destination
    self.seq = seq
    self.ack_num = ack_num
    self.message_length = message_length
    self.ACK = ACK
    self.SYN = SYN
    self.FIN = FIN
    self.LEN = LEN
    self.data = data

class SocketTCP:
  def __init__(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.address = None
    self.connection_addr = None
    self.segment = None
    self.seq = None
    self.message_left = 0

  @staticmethod
  def parse_segment(segment):
    source = int.from_bytes(segment[0:2], "big")
    destination = int.from_bytes(segment[2:4], "big")
    seq = int.from_bytes(segment[4:8], "big")
    ack_num = int.from_bytes(segment[8:12], "big")
    message_length = int.from_bytes(segment[12:14], "big")

    ACK = bool(segment[14])
    SYN = bool(segment[15]) 
    FIN = bool(segment[16])
    LEN = bool(segment[17])

    data = segment[18:]

    new_segment = Segment(
          source=source,
          destination=destination,
          seq=seq,
          ack_num=ack_num,
          message_length=message_length,
          ACK=ACK,
          SYN=SYN,
          FIN=FIN,
          LEN=LEN,
          data=data
          )
  
    return new_segment

  @staticmethod
  def create_segment(segment):
    segment_bytes = b"".join([
      segment.source.to_bytes(2, "big"),
      segment.destination.to_bytes(2, "big"),
      segment.seq.to_bytes(4, "big"),
      segment.ack_num.to_bytes(4, "big"),
      segment.message_length.to_bytes(2, "big"),
      bytes([
        segment.ACK,
        segment.SYN,
        segment.FIN,
        segment.LEN
      ]),
      segment.data
    ])
  
    return segment_bytes
  
  def bind(self, address):
    self.address = address
    self.socket.bind(address)

  def connect(self, address):
    d_print(f"Conectando con {address[0]}:{address[1]}")
    self.socket.settimeout(5)
    self.seq = random.randint(0, 100)
    seg = Segment(
      seq=self.seq,
      SYN=True
    )
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, address)

    while True:
      try:
        r_msg, address = self.socket.recvfrom(35)  
        seg = self.parse_segment(r_msg)
        if seg.SYN and seg.ACK and seg.seq == self.seq + 1:
          d_print("SYN + ACK recibido")
          break
      except socket.timeout:
        d_print("No se ha recibido mensaje SYN + ACK, reintentando...")
        self.socket.sendto(s_msg, address)

    self.seq = self.seq + 2
    new_addr = (address[0], seg.source)
    seg = Segment(
      seq=self.seq,
      ACK=True
    )
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, address)
    self.connection_addr = new_addr
    self.socket.settimeout(None)
    d_print("Conexión establecida")

  def accept(self):
    while True:
      r_msg, addr = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if seg.SYN:
        d_print(f"Recibido SYN desde {addr[0]}:{addr[1]}")
        break
  
    self.seq = seg.seq+1
    new_socket = SocketTCP()
    new_socket.connection_addr = addr
    new_addr = (self.address[0], 0)
    
    new_socket.bind(new_addr)
    new_port = new_socket.socket.getsockname()[1]

    seg = Segment(
      source=new_port,
      seq=self.seq,
      SYN=True,
      ACK=True
    )
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, addr)

    while True:
      r_msg, addr = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if (seg.ACK or seg.LEN) and seg.seq == self.seq+1:
        break
      d_print("Mensaje incorrecto recibido, reintentando...")
      self.socket.sendto(s_msg, addr)

    d_print("Conexión establecida")
    return new_socket, addr

  def send(self, message):
    n = len(message)
    self.socket.settimeout(5)  

    #Primer segmento
    seg = Segment(
      seq=self.seq,
      message_length=4,
      LEN=True,
      data=n.to_bytes(4, "big")
    )
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, self.connection_addr)
    while True:
      try:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.ACK and seg.seq == self.seq+4:
          break
      except socket.timeout:
        d_print("Timeout o mensaje/secuencia incorrecta, reintentando...")
        self.socket.sendto(s_msg, self.connection_addr)

        
    #Enviar el mensaje
    self.seq = seg.seq
    for i in range(n//16):
      data = message[i*16: (i+1)*16]
      seg = Segment(
        seq=self.seq,
        message_length=16,
        data=data
      )
      s_msg = self.create_segment(seg)
      self.socket.sendto(s_msg, self.connection_addr)

      while True:
        try:
          r_msg, _ =self.socket.recvfrom(35)
          seg = self.parse_segment(r_msg)
          if seg.ACK and seg.seq == self.seq+16:
            break
        except socket.timeout:
          d_print("Timeout o mensaje/secuencia incorrecta, reintentando...")
          self.socket.sendto(s_msg, self.connection_addr)
      
      self.seq = seg.seq
    if n%16 != 0:
      data = message[((n//16))*16:]
      seg = Segment(
        seq=self.seq,
        message_length=len(data),
        data=data
      )
      s_msg = self.create_segment(seg)
      self.socket.sendto(s_msg, self.connection_addr)

      while True:
        try:  
          r_msg, _ = self.socket.recvfrom(35)
          seg = self.parse_segment(r_msg)
          if seg.ACK and seg.seq == self.seq+len(data):
            break
        except socket.timeout:
          d_print("Timeout o mensaje/secuencia incorrecta, reintentando...")
          self.socket.sendto(s_msg, self.connection_addr)

      self.seq = seg.seq
    d_print("Mensaje completo enviado")
    self.socket.settimeout(None)

  def recv(self, buff_size):
    d_print("Esperando mensaje...")
    data = b''

    if self.message_left == 0:
      while True:  
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.LEN:
          break
        d_print("Mensaje incorrecto recibido")
        
      length = int.from_bytes(seg.data, byteorder="big")
      self.message_left = length
      self.seq = seg.seq + seg.message_length

      seg = Segment(
        seq=self.seq,
        ACK=True
        )
      s_msg = self.create_segment(seg)
      self.socket.sendto(s_msg, self.connection_addr)

    while buff_size > 0:
      while True:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.seq == self.seq:
          break
        d_print("Secuencia incorrecta recibida, reenviando ACK...")
        self.socket.sendto(s_msg, self.connection_addr)

      self.seq = seg.seq + seg.message_length
      buff_size -= 16
      self.message_left -= seg.message_length
      data += seg.data

      seg = Segment(
        seq=self.seq,
        ACK=True
        )
      s_msg = self.create_segment(seg)
      self.socket.sendto(s_msg, self.connection_addr)

    d_print("Mensaje completo recibido")
    return data

  def close(self):
    d_print("Cerrando conexión")
    self.socket.settimeout(5)
    seg = Segment(
      seq=self.seq,
      FIN=True
      )
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, self.connection_addr)

    intentos = 0
    while True:
      try:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.ACK and seg.FIN and seg.seq == self.seq+1:
          break
      except socket.timeout:
        intentos += 1
        if intentos == 3:
          self.socket.close()
          d_print(f"Intento {intentos} fallido, conexión cerrada")
          return
        d_print(f"Intento {intentos} fallido, reintentando...")
        self.socket.sendto(s_msg, self.connection_addr)

    self.seq += 2
    seg = Segment(
            seq=self.seq,
            ACK=True
            )
    s_msg = self.create_segment(seg)
    for i in range(3):
      d_print(f"Enviando ACK final {i}")
      self.socket.sendto(s_msg, self.connection_addr)
      try:
        self.socket.recvfrom(35)
      except socket.timeout:
        pass

    d_print("Conexión cerrada")
    self.socket.close()

  def recv_close(self):
    d_print("Esperanco cierre de conexión")
    while True:
      r_msg, _ = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if seg.FIN:
        break
      d_print("Mensaje incorrecto recibido")

    self.socket.settimeout(5)
    self.seq = seg.seq + 1
    seg = Segment(
                  seq=self.seq,
                  FIN=True,
                  ACK=True
                  )
                  
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, self.connection_addr)

    d_print("Esperando ACK final...")
    intentos = 0
    while intentos < 3:
      try:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.ACK and seg.seq == self.seq+1:
          break
      except socket.timeout:
        intentos += 1
        d_print(f"Timeout {intentos} terminado, reintentando...")

    d_print("Conexión cerrada")
    self.socket.close()


