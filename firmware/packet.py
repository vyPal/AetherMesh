import struct
import ubinascii

class Packet:
  HEADER_FORMAT = "!HBB6s6sHHIIBBH"
  HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
  MAX_PAYLOAD_SIZE = 250 - HEADER_SIZE

  def __init__(self, packet_type=0, ttl=64, flags=0, src_mac=None, dest_mac=None, 
                src_port=0, dest_port=0, seq_num=0, ack_num=0, payload=b''):
    self.packet_type = packet_type
    self.ttl = ttl
    self.flags = flags
    self.src_mac = src_mac or b'\x00' * 6
    self.dest_mac = dest_mac or b'\x00' * 6
    self.src_port = src_port
    self.dest_port = dest_port
    self.seq_num = seq_num
    self.ack_num = ack_num
    self.payload = payload
    self.checksum = 0  # Will be calculated when packing

  @classmethod
  def from_bytes(cls, data):
    header = struct.unpack(cls.HEADER_FORMAT, data[:cls.HEADER_SIZE])
    packet = cls(
      packet_type=header[0],
      ttl=header[1],
      flags=header[2],
      src_mac=header[3],
      dest_mac=header[4],
      src_port=header[5],
      dest_port=header[6],
      seq_num=header[7],
      ack_num=header[8],
      payload=data[cls.HEADER_SIZE:]
    )
    packet.checksum = header[11]
    return packet

  def to_bytes(self):
    self.checksum = self._calculate_checksum()
    header = struct.pack(
      self.HEADER_FORMAT,
      self.packet_type,
      self.ttl,
      self.flags,
      self.src_mac,
      self.dest_mac,
      self.src_port,
      self.dest_port,
      self.seq_num,
      self.ack_num,
      self.flags,
      self.ttl,
      self.checksum
    )
    return header + self.payload
  
  def to_bytes_without_checksum(self):
    header = struct.pack(
      self.HEADER_FORMAT,
      self.packet_type,
      self.ttl,
      self.flags,
      self.src_mac,
      self.dest_mac,
      self.src_port,
      self.dest_port,
      self.seq_num,
      self.ack_num,
      self.flags,
      self.ttl,
      0
    )
    return header + self.payload

  def _calculate_checksum(self):
    # Simple checksum calculation (you might want to use a more robust algorithm)
    return sum(self.to_bytes_without_checksum()) & 0xFFFF

  @property
  def src_mac_str(self):
    return ubinascii.hexlify(self.src_mac).decode()

  @property
  def dest_mac_str(self):
    return ubinascii.hexlify(self.dest_mac).decode()

  def __str__(self):
    return ("Packet(type={packet_type}, src={src_mac_str}:{src_port}, dest={dest_mac_str}:{dest_port}, seq={seq_num}, ack={ack_num}, flags={flags}, ttl={ttl}, payload_length={payload_length})").format(
      packet_type=self.packet_type,
      src_mac_str=self.src_mac_str,
      src_port=self.src_port,
      dest_mac_str=self.dest_mac_str,
      dest_port=self.dest_port,
      seq_num=self.seq_num,
      ack_num=self.ack_num,
      flags=self.flags,
      ttl=self.ttl,
      payload_length=len(self.payload)
    )

# Packet type constants
class PacketType:
  TCP = 1
  UDP = 2
  ICMP = 3
  ROUTING = 4

# Flag constants
class Flags:
  SYN = 0x01
  ACK = 0x02
  FIN = 0x04
  RST = 0x08

# Usage example:
# packet = Packet(PacketType.TCP, src_mac=b'\x01\x02\x03\x04\x05\x06', dest_mac=b'\x0A\x0B\x0C\x0D\x0E\x0F',
#                 src_port=12345, dest_port=80, seq_num=1, ack_num=0, flags=Flags.SYN, payload=b'Hello, AetherMesh!')
# packet_bytes = packet.to_bytes()
# received_packet = Packet.from_bytes(packet_bytes)
# print(received_packet)