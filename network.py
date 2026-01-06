# network.py
import socket, json, time

UDP_PORT = 37020  # 방 검색용(고정)
BROADCAST_ADDR = "255.255.255.255"

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def broadcast_room(room_id, room_name, tcp_port, interval=0.5, stop_flag=None):
    """Host: LAN에 방 정보를 주기적으로 광고(UDP broadcast)"""
    ip = get_local_ip()
    payload = {
        "type": "room_announce",
        "room_id": room_id,
        "room_name": room_name,
        "ip": ip,
        "port": tcp_port,
        "ts": time.time(),
    }
    msg = (json.dumps(payload) + "\n").encode("utf-8")

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        while True:
            if stop_flag is not None and stop_flag.is_set():
                break
            s.sendto(msg, (BROADCAST_ADDR, UDP_PORT))
            time.sleep(interval)
    finally:
        s.close()

def discover_rooms(listen_seconds=1.2):
    """Client: UDP로 방 광고를 잠깐 수신해서 목록 수집"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", UDP_PORT))
    s.settimeout(0.2)

    rooms = {}
    deadline = time.time() + listen_seconds
    try:
        while time.time() < deadline:
            try:
                data, _ = s.recvfrom(2048)
            except socket.timeout:
                continue
            except Exception:
                continue

            try:
                line = data.decode("utf-8").strip()
                obj = json.loads(line)
            except Exception:
                continue

            if obj.get("type") != "room_announce":
                continue
            rid = obj.get("room_id")
            if not rid:
                continue
            rooms[rid] = obj
    finally:
        s.close()

    return rooms

# ---------------- TCP JSON line ----------------
class JsonLineSocket:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""

    def send(self, obj):
        self.sock.sendall((json.dumps(obj) + "\n").encode("utf-8"))

    def recv(self):
        while b"\n" not in self.buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except Exception:
            return None

    def close(self):
        try:
            self.sock.close()
        except Exception:
            pass

def tcp_host_listen(port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("", port))
    srv.listen(1)
    return srv

def tcp_client_connect(host_ip, port, timeout=4.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host_ip, port))
    s.settimeout(None)
    return s
