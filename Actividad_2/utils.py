#Integrante: Alejandro Molina

import socket
from dnslib import QTYPE, DNSRecord, RR, A
from collections import deque, Counter

root_ip = "198.41.0.4"
buff_size = 4096

last_queries = deque(maxlen=20)
domain_cache = {}
domain_freq = Counter()

def add_domain(name):
  if len(last_queries) == 20:
    domain_freq[last_queries[0]] -= 1 

  last_queries.append(name)
  domain_freq[name] += 1

def common_domains():
  domains = []
  for domain, freq in domain_freq.most_common(3):
    domains.append(domain)
  return domains

def parse_DNS_message(dns_message):
  return DNSRecord.parse(dns_message)

def resolver(mensaje_consulta, ip_addr=root_ip, name_server=".", debug=False):
  parsed_query = parse_DNS_message(mensaje_consulta)
  domain = parsed_query.q.qname

  if domain in common_domains():
    print(f"(debug) '{domain}' encontrado en caché, consultando...")
    domain_address = domain_cache[domain]
    parsed_query.add_answer(RR(domain, QTYPE.A, rdata=A(domain_address)))

    add_domain(domain)
    return bytes(parsed_query.pack())
  
  else:  
    dns_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  
    print(f"(debug) Consultando '{domain}' a '{name_server}' con dirección IP '{ip_addr}'")
    
    dns_socket.sendto(mensaje_consulta, (ip_addr, 53))

    answer, _ = dns_socket.recvfrom(buff_size)
  
    dns_reply = parse_DNS_message(answer)

    for rr in dns_reply.rr:
      if QTYPE.get(rr.rtype) == "A":
        add_domain(domain)
        domain_cache[domain] = str(rr.rdata)
        return answer

    name_servers = []
    for rr in dns_reply.auth:
      if QTYPE.get(rr.rtype) == "NS":
        name_servers.append(rr.rdata)

    if name_servers:
      for rr in dns_reply.ar:
        if QTYPE.get(rr.rtype) == "A":
          answer_address = str(rr.rdata)
          answer_name = str(rr.rname)
          
          return resolver(mensaje_consulta, answer_address, answer_name, debug=debug)

      ns_name = str(name_servers[0])
      ns_q = DNSRecord.question(ns_name)

      ns_answer = resolver(bytes(ns_q.pack()))
      ns_reply = parse_DNS_message(ns_answer)
      ns_address = ""
      for rr in ns_reply.rr:
        if QTYPE.get(rr.rtype) == "A":
          ns_address = str(rr.rdata)
          ns_name = str(rr.rname)
          break

      return resolver(mensaje_consulta, ns_address, ns_name, debug=debug)