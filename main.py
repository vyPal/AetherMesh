import network
import espnow
import ubinascii
import sys
import uasyncio as asyncio
import uselect
from packet import Packet, PacketType


class AetherMeshNode:
  def __init__(self):
    self.esp = network.WLAN(network.STA_IF)
    self.esp.active(True)
    self.mac = ubinascii.hexlify(self.esp.config('mac')).decode()
    self.e = espnow.ESPNow()
    self.e.active(True)
    self.seen_packets = set()
    self.routing_table = {}

  def send_packet(self, dest_mac, data, packet_type=PacketType.UDP):
    packet = Packet(packet_type=packet_type,
                    src_mac=bytes.fromhex(self.mac),
                    dest_mac=bytes.fromhex(dest_mac),
                    payload=data)
    try:
      self.e.get_peer(b'\xff' * 6)
    except OSError:
      self.e.add_peer(b'\xff' * 6)
    self.e.send(b'\xff' * 6, packet.to_bytes())

  def receive_packet(self):
    raw_packet = self.e.recv(0)
    if raw_packet:
      sender, data = raw_packet
      if data is None:
        return None
      packet = Packet.from_bytes(data)
      return packet
    else:
      return None

  def process_packet(self, packet):
    packet_hash = hash(packet.payload)
    if packet_hash in self.seen_packets:
      return

    self.seen_packets.add(packet_hash)
    if len(self.seen_packets) > 100:
      self.seen_packets.pop()

    self.handle_packet(packet)

    """ if packet.dest_mac_str == self.mac:
      self.handle_packet(packet)
    else:
      self.forward_packet(packet) """

  def handle_packet(self, packet):
    print(f"Received packet type {packet.packet_type} from {packet.src_mac_str}: {packet.payload}")
    print(f"Packet details: {packet}")

    if packet.packet_type == PacketType.ROUTING:
      self.handle_routing_packet(packet)
    elif packet.packet_type == PacketType.TCP:
      self.handle_tcp_packet(packet)
    elif packet.packet_type == PacketType.UDP:
      self.handle_udp_packet(packet)

  def forward_packet(self, packet):
    # Decrement TTL
    packet.ttl -= 1
    if packet.ttl <= 0:
      return  # Don't forward packets with expired TTL

    # Use routing table to determine next hop
    next_hop = self.routing_table.get(packet.dest_mac_str, None)
    if next_hop:
      self.send_packet(next_hop, packet)
    else:
      # If no route is known, broadcast the packet
      self.send_packet(b'\xff' * 6, packet)

  def update_routing_table(self, dest_mac, next_hop):
    self.routing_table[dest_mac] = next_hop

  def handle_routing_packet(self, packet):
    # Process routing information
    pass

  def handle_tcp_packet(self, packet):
    # Process TCP-like packet
    pass

  def handle_udp_packet(self, packet):
    # Process UDP-like packet
    pass

  async def receive_loop(self):
    while True:
      packet = self.receive_packet()
      if packet:
        self.process_packet(packet)
      await asyncio.sleep_ms(10)

  async def send_loop(self):
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)
    while True:
      events = poller.poll(0)
      if events:
        message = sys.stdin.readline().strip()
        if message:
          self.send_packet('ffffffffffff', message.encode(), PacketType.UDP)
      await asyncio.sleep_ms(10)

  def run(self):
    print("Node started")
    print(f"MAC address: {self.mac}")
    loop = asyncio.get_event_loop()
    loop.create_task(self.receive_loop())
    loop.create_task(self.send_loop())
    loop.run_forever()


node = AetherMeshNode()
node.run()
