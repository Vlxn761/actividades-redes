import socket
import random
from socketUDP import SocketUDP
from slidingWindowCC import SlidingWindowCC
from CongestionControl import CongestionControl

class Segment:
  def __init__(
      self,
      source: int = 5000,
      destination: int = 5000,
      seq: int = 0,
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
    self.congestion_control_on = False 
    self.congestion_controller = None

  def set_congestion_control(self, status: bool):
    self.congestion_control_on = status

  @staticmethod
  def parse_segment(segment):
    print("source =", segment[0:2])
    source = int.from_bytes(segment[0:2], "big")
    destination = int.from_bytes(segment[2:4], "big")
    seq = int.from_bytes(segment[4:8], "big")
    message_length = int.from_bytes(segment[8:10], "big")

    ACK = bool(segment[10])
    SYN = bool(segment[11]) 
    FIN = bool(segment[12])
    LEN = bool(segment[13])

    data = segment[14:]

    print("RECIBIDO")
    print("source =", source)
    print("destination =", destination)
    print("seq =", seq)
    print("message_length =", message_length)
    print("ACK =", ACK)
    print("SYN =", SYN)
    print("FIN =", FIN)
    print("LEN =", LEN)
    print("data =", data)
    print("")
    print("")

    new_segment = Segment(
          source=source,
          destination=destination,
          seq=seq,
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
      segment.message_length.to_bytes(2, "big"),
      bytes([
        segment.ACK,
        segment.SYN,
        segment.FIN,
        segment.LEN
      ]),
      segment.data
    ])

    print("Enviado")
    print(segment_bytes)
    
    return segment_bytes
  
  def bind(self, address):
    self.address = address
    self.socket.bind(address)

  def connect(self, address):
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
          break
      except socket.timeout:
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

  def accept(self):
    while True:
      r_msg, addr = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if seg.SYN:
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
      self.socket.sendto(s_msg, addr)
    
    return new_socket, addr

  def send_using_stop_and_wait(self, message):
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
    print("enviando mensaje a ", self.connection_addr)
    self.socket.sendto(s_msg, self.connection_addr)
    print(self.socket.getsockname())
    while True:
      try:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.ACK and seg.seq == self.seq+4:
          break
      except socket.timeout:
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
          self.socket.sendto(s_msg, self.connection_addr)

      self.seq = seg.seq
    self.socket.settimeout(None)

  def recv_using_stop_and_wait(self, buff_size):
    data = b''
    print(self.socket.getsockname())
    print("LARGO RESTANTE", self.message_left)

    if self.message_left == 0:
      print("NO  while")
      while True:  
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.LEN:
          break
        
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
      print("en el while")
      while True:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.seq == self.seq:
          break
        #Reenvía el último mensaje
        self.socket.sendto(s_msg, self.connection_addr)

      self.seq = seg.seq + seg.message_length
      buff_size -= 16
      self.message_left -= seg.message_length
      print("LARGO RESTANTE", self.message_left)
      data += seg.data

      seg = Segment(
        seq=self.seq,
        ACK=True
        )
      s_msg = self.create_segment(seg)
      self.socket.sendto(s_msg, self.connection_addr)

    print("retornar")
    return data

  def close(self):
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
          return
        self.socket.sendto(s_msg, self.connection_addr)

    self.seq += 2
    seg = Segment(
            seq=self.seq,
            ACK=True
            )
    s_msg = self.create_segment(seg)
    for i in range(3):
      self.socket.sendto(s_msg, self.connection_addr)
      try:
        self.socket.recvfrom(35)
      except (socket.timeout, ConnectionResetError, OSError):
        pass
      
    self.socket.close()

  def recv_close(self):
    while True:
      r_msg, _ = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if seg.FIN:
        break
      else:
        seg_ack = Segment(seq=self.seq, ACK=True) 
        s_msg = self.create_segment(seg_ack)
        self.socket.sendto(s_msg, self.connection_addr)

    self.socket.settimeout(5)
    self.seq = seg.seq + 1
    seg = Segment(
                  seq=self.seq,
                  FIN=True,
                  ACK=True
                  )
                  
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, self.connection_addr)

    intentos = 0
    while intentos < 3:
      try:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.ACK and seg.seq == self.seq+1:
          print("terminó")
          break
      except socket.timeout:
        intentos += 1

    self.socket.close()

  def send(self, message, mode="stop_and_wait"):
    if mode == "stop_and_wait": 
      self.send_using_stop_and_wait(message) 
    elif mode == "go_back_n":
      self.send_using_go_back_n(message) 

  def recv(self, buff_size, mode="stop_and_wait"):
    if mode == "stop_and_wait":
      return self.recv_using_stop_and_wait(buff_size) 
    elif mode == "go_back_n": 
      return self.recv_using_go_back_n(buff_size)

  def send_using_go_back_n(self, message):
    n = len(message)
    self.socket.settimeout(0.5)
    if self.congestion_control_on:
      MSS = 8
      if self.congestion_controller is None:
        self.congestion_controller = CongestionControl(MSS=MSS)
      window_size = self.congestion_controller.get_MSS_in_cwnd()
    else:
      MSS = 16
      window_size = 8
    data_list = [message[i:i+MSS] for i in range(0, n, MSS)]
    seg = Segment(seq=self.seq, message_length=4, LEN=True, data=n.to_bytes(4, "big"))
    s_msg = self.create_segment(seg)
    self.socket.sendto(s_msg, self.connection_addr)
    while True:
      try: 
        r_msg, _ = self.socket.recvfrom(35)
        seg_ack = self.parse_segment(r_msg) 
        if seg_ack.ACK and seg_ack.seq == self.seq + 4:
          self.seq = seg_ack.seq 
          break 
      except socket.timeout: 
        self.socket.sendto(s_msg, self.connection_addr)
    data_window = SlidingWindowCC(window_size, data_list, self.seq)
    base = 0
    total_packets = len(data_list)
    sent_until = 0
    while base < total_packets:
      curr_window_size = data_window.window_size 
      while sent_until < curr_window_size and (base + sent_until) < total_packets:
        p_data = data_window.get_data(sent_until)
        p_seq = data_window.get_sequence_number(sent_until) 
        if p_data is not None and p_seq is not None:
          seg = Segment(seq=p_seq, message_length=len(p_data), data=p_data)
          s_msg = self.create_segment(seg)
          self.socket.sendto(s_msg, self.connection_addr)
        sent_until += 1
      try: 
        r_msg, _ = self.socket.recvfrom(35)
        seg_ack = self.parse_segment(r_msg) 
        if seg_ack.ACK:
          base_seq = data_window.get_sequence_number(0) 
          if base_seq is not None and seg_ack.seq > base_seq:
            bytes_advanced = seg_ack.seq - base_seq
            adv_packets = 0
            accum = 0
            for idx in range(curr_window_size):
              d = data_window.get_data(idx)
              if d is not None:
                accum += len(d)
                adv_packets += 1
                if accum >= bytes_advanced:
                  break
            if adv_packets > 0:
              if self.congestion_control_on: 
                self.congestion_controller.event_ack_received()
              data_window.move_window(adv_packets)
              base += adv_packets
              sent_until = max(0, sent_until - adv_packets)
              if self.congestion_control_on: 
                new_size = self.congestion_controller.get_MSS_in_cwnd()
                data_window.update_window_size(new_size)
                print(f"[DEBUG ACK] cwnd: {self.congestion_controller.cwnd} bytes ({new_size} MSS) | Estado: {self.congestion_controller.current_state}")
      except socket.timeout:
        if self.congestion_control_on: 
          self.congestion_controller.event_timeout()
          new_size = self.congestion_controller.get_MSS_in_cwnd()
          data_window.update_window_size(new_size)
          print(f"[DEBUG TIMEOUT] ssthresh: {self.congestion_controller.ssthresh} bytes | cwnd: {self.congestion_controller.cwnd} bytes | Estado: {self.congestion_controller.current_state}")
        sent_until = 0
    self.seq = seg_ack.seq if 'seg_ack' in locals() else self.seq
    self.socket.settimeout(None)

  def recv_using_go_back_n(self, buff_size):
    data = b''
    if self.message_left == 0:
      while True:
        r_msg, _ = self.socket.recvfrom(35)
        seg = self.parse_segment(r_msg)
        if seg.LEN:
          break
        else:
          seg_ack = Segment(seq=self.seq, ACK=True)
          s_msg = self.create_segment(seg_ack)
          self.socket.sendto(s_msg, self.connection_addr)
      length = int.from_bytes(seg.data, byteorder="big")
      self.message_left = length
      self.seq = seg.seq + seg.message_length
      seg_ack = Segment(seq=self.seq, ACK=True)
      s_msg = self.create_segment(seg_ack)
      self.socket.sendto(s_msg, self.connection_addr)
    last_ack_sent = self.seq 
    while self.message_left > 0 and len(data) < buff_size:
      r_msg, _ = self.socket.recvfrom(35)
      seg = self.parse_segment(r_msg)
      if seg.seq == self.seq:
        self.seq = seg.seq + seg.message_length
        self.message_left -= seg.message_length
        data += seg.data 
        last_ack_sent = self.seq
        seg_ack = Segment(seq=self.seq, ACK=True)
        s_msg = self.create_segment(seg_ack)
        self.socket.sendto(s_msg, self.connection_addr)
      else:
        seg_ack = Segment(seq=last_ack_sent, ACK=True)
        s_msg = self.create_segment(seg_ack)
        self.socket.sendto(s_msg, self.connection_addr)
    return data

  def set_peso(self, peso):
    self.peso = peso

  def set_mala_mascota(self):
    print("No, no hay mascotas malas, me niego")

  def is_buena_mascota(self):
    return self.buena_mascota

  def is_chonky(self):
    if self.especie == "gato":
      if self.tamanno == "smol":
        if self.peso > 5:
          return "está chonky"
        else:
          return "no está chonky"
      else:
        if self.peso > 7:
          return "está chonky"
        else:
          return "no está chonky"
    else:
      return "la verdad es que ni idea, esto es un ejemplo chiquito"
