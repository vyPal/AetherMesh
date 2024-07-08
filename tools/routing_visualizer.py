import networkx as nx
import matplotlib.pyplot as plt
import serial
import threading
import time

class AetherMeshVisualizer:
  def __init__(self, serial_port='/dev/ttyACM0', baud_rate=115200):
    self.serial = serial.Serial(
        port='/dev/ttyACM0',
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1)
    self.G = nx.Graph()
    self.node_data = {}
    self.mac = None
    self.sent_mac_request = False
    self.sent_neighbors_request = False

  def update_graph(self, data):
    node_mac = data['mac']
    self.node_data[node_mac] = data
    self.G.add_node(node_mac)
    for neighbor in data['neighbors']:
      if neighbor == '':
        continue
      self.G.add_edge(node_mac, neighbor)

  def visualize(self):
    plt.clf()
    pos = nx.spring_layout(self.G)
    nx.draw(self.G, pos, with_labels=True, node_color='lightblue',
            node_size=500, font_size=8, font_weight='bold')

    # Add node information
    """ node_info = {node: f"{node}\n{self.node_data[node]['packet_count']} pkts"
                 for node in self.G.nodes() if node in self.node_data}
    nx.draw_networkx_labels(self.G, pos, node_info, font_size=6) """

    plt.title("AetherMesh Network Visualization")
    plt.axis('off')
    plt.tight_layout()
    plt.pause(0.1)

  def request_neighbors(self):
    while True:
      self.serial.flush()
      self.serial.write(b"show mac\r\n")
      self.serial.flush()
      self.serial.flush()
      self.serial.write(b"show neighbors\r\n")
      self.serial.flush()
      time.sleep(5)
      self.serial.flush()
      self.serial.write(b"show topology\r\n")
      self.serial.flush()
      time.sleep(5)

  def run(self):
    plt.ion()

    threading.Thread(target=self.request_neighbors, daemon=True).start()

    while True:
      data = self.serial.readline().decode('utf-8').strip()
      if data == "":
        continue
      print(f"Received data: {data}")
      if data.startswith("(cmd: show mac)"):
        self.mac = data.split()[-1]
      elif data.startswith("(cmd: show neighbors)"):
        if self.mac is None:
          continue
        data = {"mac": self.mac, "neighbors": [i.strip(" '") for i in " ".join(data.split()[3:])[1:-1].split(",")]}
        self.G.clear()
        self.update_graph(data)
        self.visualize()
      elif data.startswith("(cmd: show topology)"):
        if self.mac is None:
          continue
        data = {"mac": data.split()[3], "neighbors": [i.strip(" '") for i in " ".join(data.split()[4:])[1:-1].split(",")]}
        self.G.clear()
        self.update_graph(data)
        self.visualize()


if __name__ == "__main__":
  visualizer = AetherMeshVisualizer()
  visualizer.run()
