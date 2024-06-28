import network
import espnow
import ubinascii
import uasyncio as asyncio
from packet import Packet, PacketType
from message import Message
import _thread


class AetherMeshNode:
  def __init__(self):
    self.esp = network.WLAN(network.STA_IF)
    self.esp.active(True)
    self.mac = ubinascii.hexlify(self.esp.config('mac')).decode()
    self.e = espnow.ESPNow()
    self.e.active(True)
    try:
      self.e.get_peer(b'\xff' * 6)
    except OSError:
      self.e.add_peer(b'\xff' * 6)
    self.seen_packets = set()
    self.routing_table = {
      self.mac: (self.mac, 0)
    }  # dest: (next_hop, dist)

  def send_packet(self, dest_mac, packet):
    if dest_mac == "ffffffffffff":
      self.e.send(b'\xff' * 6, packet.to_bytes())
    else:
      self.e.add_peer(bytes.fromhex(dest_mac))
      self.e.send(bytes.fromhex(dest_mac), packet.to_bytes())
      self.e.del_peer(bytes.fromhex(dest_mac))

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

    if packet.dest_mac_str == self.mac or packet.dest_mac_str == 'ffffffffffff':
      self.handle_packet(packet)
    else:
      self.forward_packet(packet)

  def handle_packet(self, packet):
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
      self.send_packet("ffffffffffff", packet)

  def update_routing_table(self, dest_mac, next_hop, dist):
    # Update routing table with new information
    if dest_mac not in self.routing_table:
      self.routing_table[dest_mac] = (next_hop, dist)
    else:
      current_next_hop, current_dist = self.routing_table[dest_mac]
      if dist < current_dist:
        self.routing_table[dest_mac] = (next_hop, dist)

  def handle_routing_packet(self, packet):
    # Extract routing information from packet
    dest_mac = packet.payload[:6]
    dist = packet.payload[6]

    # Decode MAC addresses
    dest_mac_decoded = ubinascii.hexlify(dest_mac).decode()

    # Update routing table with correct information
    self.update_routing_table(dest_mac_decoded, packet.src_mac_str, dist + 1)
    self.update_routing_table(packet.src_mac_str, packet.src_mac_str, 1)

  def handle_tcp_packet(self, packet):
    pass

  def handle_udp_packet(self, packet):
    pass

  async def receive_loop(self):
    while True:
      packet = self.receive_packet()
      if packet:
        self.process_packet(packet)
      await asyncio.sleep_ms(10)

  async def broadcast_routing_table(self):
    while True:
      for dest_mac, (next_hop, dist) in self.routing_table.items():
        dest_mac_bytes = bytes.fromhex(dest_mac)
        routing_packet = Packet(packet_type=PacketType.ROUTING,
                                src_mac=bytes.fromhex(self.mac),
                                dest_mac=bytes.fromhex("ffffffffffff"),
                                payload=dest_mac_bytes + dist.to_bytes(1, 'big'))
        self.send_packet("ffffffffffff", routing_packet)
      await asyncio.sleep(10)

  def run(self):
    print("Node started")
    print(f"MAC address: {self.mac}")
    loop = asyncio.get_event_loop()
    loop.create_task(self.receive_loop())
    loop.create_task(self.broadcast_routing_table())
    loop.create_task(cli_loop(self))
    loop.run_forever()


async def cli_loop(node):
  while True:
    cmd = await unblock(input, "AetherMesh> ")
    if cmd == "show routing":
      for dest, (next_hop, dist) in node.routing_table.items():
        print(f"(cmd: show routing) {dest} via {next_hop} distance {dist}")
    else:
      print("Unknown command")


async def unblock(func, *args, **kwargs):
  def wrap(func, message, args, kwargs):
    message.set(func(*args, **kwargs))
  msg = Message()
  _thread.start_new_thread(wrap, (func, msg, args, kwargs))
  return await msg

node = AetherMeshNode()
node.run()
