# game.py
import os
import random
import threading
import time
from dataclasses import dataclass

import pygame

import network
from car import Car
from track import Track
from resource import resource_path


# -----------------------------
# Item (cyan pickup)
# -----------------------------
class Item:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(int(x), int(y), 16, 16)
        self.color = (0, 255, 255)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=4)


class Game:
    """
    game.py (통합판)
    - game2.py 기능: 맵 선택(1~5), 이모트(1~5), 아이템/부스트, 리매치 투표, LAN host/client 동기화
    - game.py 기능: host time 기반 카운트다운(start_at/go_until/race_started) 동기화(클라 offset 스무딩)
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        mode: str = "local",
        host_ip: str | None = None,
        port: int = 5000,
        room_name: str = "Room",
        room_id: str = "RACE01",
    ):
        self.screen = screen
        self.clock = clock
        self.running = True

        # 모드 및 네트워크 설정
        self.mode = mode
        self.host_ip = host_ip
        self.port = port
        self.room_name = room_name
        self.room_id = room_id

        self.width = screen.get_width()
        self.height = screen.get_height()

        # -----------------------------
        # Track / Map
        # -----------------------------
        self.current_map_id = 0
        self.track = Track(self.current_map_id)

        # -----------------------------
        # Cars
        # -----------------------------
        self.car1 = Car(300, 540)
        self.car2 = Car(350, 540)
        # Car 쪽에 속성이 없을 수도 있으니 setattr로 안전하게
        setattr(self.car1, "body_color", (230, 230, 230))
        setattr(self.car1, "nose_color", (255, 80, 80))
        setattr(self.car2, "body_color", (120, 160, 255))
        setattr(self.car2, "nose_color", (255, 255, 80))

        # -----------------------------
        # Game state
        # -----------------------------
        self.cp_index1 = 0
        self.cp_index2 = 0
        self.winner: str | None = None

        # 결과 화면 타이머 및 투표 상태
        self.finish_time: float | None = None
        self.rematch_p1: bool | None = None
        self.rematch_p2: bool | None = None
        self.match_running = False

        # -----------------------------
        # Countdown sync (from old game.py)
        # -----------------------------
        self.countdown_total = 3.0
        self.show_go_time = 0.6
        self.start_at: float | None = None
        self.go_until: float | None = None
        self.race_started = False
        self.time_offset = 0.0  # client: (server_time - local_time)

        # -----------------------------
        # Items / boost
        # -----------------------------
        self.items: list[Item] = []
        self.item_spawn_timer = 0.0
        self.ITEM_SPAWN_INTERVAL = 5.0

        # -----------------------------
        # Key maps (boost key added)
        # -----------------------------
        self.p1_keymap = {
            "throttle": pygame.K_w,
            "brake": pygame.K_s,
            "left": pygame.K_a,
            "right": pygame.K_d,
            "boost": pygame.K_RSHIFT,
        }
        self.p2_keymap = {
            "throttle": pygame.K_UP,
            "brake": pygame.K_DOWN,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "boost": pygame.K_LSHIFT,
        }

        # -----------------------------
        # UI
        # -----------------------------
        self.show_hud = True
        self.font = pygame.font.SysFont(None, 22)
        self.big_font = pygame.font.SysFont("Arial", 40, bold=True)
        self.rank_font = pygame.font.SysFont("Arial", 60, bold=True)

        # -----------------------------
        # Emote images
        # -----------------------------
        self.emote_imgs: dict[int, pygame.Surface] = {}
        self._load_emote_images()
        self.client_pending_emote = 0

        # -----------------------------
        # Network
        # -----------------------------
        self.net = None  # JsonLineSocket
        self._net_thread = None
        self._broadcast_thread = None
        self._broadcast_stop = threading.Event()

        self.remote_input = {
            "throttle": False,
            "brake": False,
            "left": False,
            "right": False,
            "boost": False,
            "emote_req": 0,
        }
        self.latest_state = None

        # 게임 시작 시 초기 아이템 생성 (호스트/로컬만)
        if self.mode != "client":
            self._spawn_initial_items()

        if self.mode == "host":
            self._srv = network.tcp_host_listen(self.port)
            self._broadcast_thread = threading.Thread(
                target=network.broadcast_room,
                args=(self.room_id, self.room_name, self.port, 0.5, self._broadcast_stop),
                daemon=True,
            )
            self._broadcast_thread.start()

        elif self.mode == "client":
            s = network.tcp_client_connect(self.host_ip, self.port)
            self.net = network.JsonLineSocket(s)
            self._net_thread = threading.Thread(target=self._client_recv_loop, daemon=True)
            self._net_thread.start()

    # -----------------------------
    # Init helpers
    # -----------------------------
    def _load_emote_images(self):
        try:
            for i in range(1, 6):
                file_path = resource_path(f"assets/{i}.png")
                raw_img = pygame.image.load(file_path).convert_alpha()
                self.emote_imgs[i] = pygame.transform.scale(raw_img, (32, 32))
            print("이모티콘 로드 성공! (resource_path 사용)")
        except Exception as e:
            print(f"이모티콘 로드 실패: {e}")


    def _spawn_initial_items(self):
        self.items = []
        for _ in range(5):
            pos = self.track.get_random_safe_point(self.width, self.height, 16, 16)
            if pos:
                self.items.append(Item(pos[0], pos[1]))

    # -----------------------------
    # Reset helpers
    # -----------------------------
    def _reset_car_positions(self):
        sp = self.track.spawn_points
        self.car1.x, self.car1.y = sp[0]
        self.car1.speed = 0
        self.car1.angle = 0
        self.car2.x, self.car2.y = sp[1]
        self.car2.speed = 0
        self.car2.angle = 0

        # 아이템/부스트 상태 초기화
        self.car1.has_item = False
        self.car1.boost_timer = 0.0
        self.car2.has_item = False
        self.car2.boost_timer = 0.0

        # emote 초기화(선택)
        self.car1.emote_id = 0
        self.car2.emote_id = 0

    def _reset_match_state(self):
        self.cp_index1 = 0
        self.cp_index2 = 0
        self.winner = None
        self.finish_time = None
        self.rematch_p1 = None
        self.rematch_p2 = None

        # countdown
        self.start_at = None
        self.go_until = None
        self.race_started = False
        if self.mode == "client":
            # 클라는 time_offset 누적값을 유지해도 되지만, 맵 전환/재시작 때 흔들림 줄이려면 reset
            self.time_offset = 0.0

        self._reset_car_positions()

        # 맵 리셋 시 아이템도 초기화
        if self.mode != "client":
            self._spawn_initial_items()

    # -----------------------------
    # Main loop
    # -----------------------------
    def run(self):
        if self.mode == "host":
            self._wait_for_client_and_bind()

        while self.running:
            self._select_map_screen()
            if not self.running:
                break

            self._reset_match_state()
            self.match_running = True

            while self.match_running and self.running:
                dt = self.clock.tick(60) / 1000.0
                self.handle_events()
                self.update(dt)
                self.draw()

        self._cleanup_network()

    def _wait_for_client_and_bind(self):
        self._srv.settimeout(0.2)
        while self.running and self.net is None:
            self.handle_events()
            self.screen.fill((18, 18, 18))
            msg = self.font.render("Waiting for client... (ESC to cancel)", True, (240, 240, 240))
            self.screen.blit(msg, msg.get_rect(center=(self.width // 2, self.height // 2)))
            pygame.display.flip()
            try:
                sock, _addr = self._srv.accept()
                self.net = network.JsonLineSocket(sock)
                self._net_thread = threading.Thread(target=self._host_recv_loop, daemon=True)
                self._net_thread.start()
            except Exception:
                continue

    # -----------------------------
    # Map select
    # -----------------------------
    def _select_map_screen(self):
        """
        Host: 1~5 선택 후 start=true 전송
        Client: map_select 수신 대기
        Local: host처럼 1~5로 선택
        """
        selected = False
        while self.running and not selected:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                # local/host는 키로 선택
                if self.mode in ("local", "host") and event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_5:
                        self.current_map_id = event.key - pygame.K_1
                        self.track.load_map(self.current_map_id)
                        self._reset_car_positions()
                        selected = True

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                    return

            # host는 선택 과정도 실시간 broadcast(미리보기 동기화)
            if self.mode == "host" and self.net:
                msg = {"type": "map_select", "map": self.current_map_id}
                if selected:
                    msg["start"] = True
                self.net.send(msg)

            # client는 map_select 수신으로만 진행
            if self.mode == "client" and self.latest_state:
                st = self.latest_state
                if st.get("type") == "map_select":
                    server_map = int(st.get("map", 0))
                    if self.current_map_id != server_map:
                        self.current_map_id = server_map
                        self.track.load_map(server_map)
                        self._reset_car_positions()
                    if st.get("start", False):
                        selected = True

            # draw
            self.screen.fill((30, 30, 30))
            if self.mode in ("local", "host"):
                title = self.big_font.render("SELECT MAP (Press 1-5)", True, (255, 255, 0))
                self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 40)))
                sub = self.font.render(f"Current Preview: Map {self.current_map_id + 1}", True, (200, 200, 200))
                self.screen.blit(sub, sub.get_rect(center=(self.width // 2, self.height // 2 + 20)))
            else:
                title = self.big_font.render("Host is selecting map...", True, (200, 200, 200))
                self.screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2)))
                sub = self.font.render(f"Map {self.current_map_id + 1}", True, (100, 255, 100))
                self.screen.blit(sub, sub.get_rect(center=(self.width // 2, self.height // 2 + 50)))

            pygame.display.flip()
            self.clock.tick(30)

    # -----------------------------
    # Network recv loops
    # -----------------------------
    def _host_recv_loop(self):
        while self.running and self.net is not None:
            obj = self.net.recv()
            if obj is None:
                break
            if obj.get("type") == "input":
                self.remote_input = {
                    "throttle": bool(obj.get("throttle")),
                    "brake": bool(obj.get("brake")),
                    "left": bool(obj.get("left")),
                    "right": bool(obj.get("right")),
                    "boost": bool(obj.get("boost")),
                    "emote_req": int(obj.get("emote_req", 0)),
                }
            elif obj.get("type") == "rematch_vote":
                self.rematch_p2 = obj.get("vote")

    def _client_recv_loop(self):
        while self.running and self.net is not None:
            obj = self.net.recv()
            if obj is None:
                break
            if obj.get("type") in ["state", "map_select"]:
                self.latest_state = obj
            elif obj.get("type") == "match_result":
                action = obj.get("action")
                if action == "restart":
                    self.match_running = False
                elif action == "quit":
                    self.running = False

    # -----------------------------
    # Events
    # -----------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self.show_hud = not self.show_hud
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # winner 화면에서 5초 이후 Y/N 투표
                if self.winner is not None:
                    if self.finish_time and (time.time() - self.finish_time >= 5.0):
                        vote_val = None
                        if event.key == pygame.K_y:
                            vote_val = True
                        elif event.key == pygame.K_n:
                            vote_val = False

                        if vote_val is not None:
                            if self.mode in ("local", "host"):
                                self.rematch_p1 = vote_val
                            elif self.mode == "client":
                                self.rematch_p2 = vote_val
                                if self.net:
                                    self.net.send({"type": "rematch_vote", "vote": vote_val})

                # 레이스 중 감정표현 1~5
                else:
                    emote_val = 0
                    if event.key == pygame.K_1:
                        emote_val = 1
                    elif event.key == pygame.K_2:
                        emote_val = 2
                    elif event.key == pygame.K_3:
                        emote_val = 3
                    elif event.key == pygame.K_4:
                        emote_val = 4
                    elif event.key == pygame.K_5:
                        emote_val = 5

                    if emote_val > 0:
                        if self.mode in ("local", "host"):
                            self.car1.set_emote(emote_val)
                        elif self.mode == "client":
                            self.client_pending_emote = emote_val

    # -----------------------------
    # Update
    # -----------------------------
    def update(self, dt: float):
        keys = pygame.key.get_pressed()

        # 승리 시 투표 로직 (Host)
        if self.winner is not None:
            if self.finish_time is None:
                self.finish_time = time.time()

            if self.mode == "host":
                if self.rematch_p1 is not None and self.rematch_p2 is not None:
                    if self.rematch_p1 and self.rematch_p2:
                        if self.net:
                            self.net.send({"type": "match_result", "action": "restart"})
                        self.match_running = False
                    else:
                        if self.net:
                            self.net.send({"type": "match_result", "action": "quit"})
                        self.running = False
            elif self.mode == "local":
                # 로컬은 P2투표가 없으니, P1만으로 결정(편의)
                if self.rematch_p1 is False:
                    self.running = False
                elif self.rematch_p1 is True:
                    self.match_running = False
            return

        # 아이템 주기적 생성 (Host/Local)
        if self.mode in ("local", "host"):
            self.item_spawn_timer += dt
            if self.item_spawn_timer >= self.ITEM_SPAWN_INTERVAL:
                self.item_spawn_timer = 0.0
                if len(self.items) < 5:
                    pos = self.track.get_random_safe_point(self.width, self.height, 16, 16)
                    if pos:
                        self.items.append(Item(pos[0], pos[1]))

        # -----------------------------
        # Countdown gate (host/local authoritative)
        # -----------------------------
        if self.mode in ("local", "host"):
            now = time.monotonic()
            if self.start_at is None:
                self.start_at = now + self.countdown_total

            if not self.race_started:
                if now >= self.start_at:
                    self.race_started = True
                    self.go_until = now + self.show_go_time
                else:
                    # 출발 전에는 움직임 적용하지 않음
                    if self.mode == "host" and self.net is not None:
                        self._send_state_to_client(server_time=time.monotonic())
                    return

        # -----------------------------
        # Local
        # -----------------------------
        if self.mode == "local":
            self._move_with_sliding(self.car1, dt, keys, self.p1_keymap)
            self._check_item_collision_host(self.car1)
            if keys[self.p1_keymap["boost"]]:
                self.car1.activate_boost()
            self.cp_index1 = self._check_checkpoint(self.car1, self.cp_index1)

            self._move_with_sliding(self.car2, dt, keys, self.p2_keymap)
            self._check_item_collision_host(self.car2)
            if keys[self.p2_keymap["boost"]]:
                self.car2.activate_boost()
            self.cp_index2 = self._check_checkpoint(self.car2, self.cp_index2)

            if self.cp_index1 >= len(self.track.checkpoints):
                self.winner = "P1"
            elif self.cp_index2 >= len(self.track.checkpoints):
                self.winner = "P2"
            return

        # -----------------------------
        # Host
        # -----------------------------
        if self.mode == "host":
            # P2 emote req
            p2_emote_req = int(self.remote_input.get("emote_req", 0))
            if p2_emote_req > 0:
                self.car2.set_emote(p2_emote_req)
                self.remote_input["emote_req"] = 0

            p1 = {
                "throttle": keys[self.p1_keymap["throttle"]],
                "brake": keys[self.p1_keymap["brake"]],
                "left": keys[self.p1_keymap["left"]],
                "right": keys[self.p1_keymap["right"]],
                "boost": keys[self.p1_keymap["boost"]],
            }
            p2 = self.remote_input

            # P1
            self._move_with_sliding_control(self.car1, dt, p1)
            self._check_item_collision_host(self.car1)
            if p1.get("boost"):
                self.car1.activate_boost()
            self.cp_index1 = self._check_checkpoint(self.car1, self.cp_index1)

            # P2
            self._move_with_sliding_control(self.car2, dt, p2)
            self._check_item_collision_host(self.car2)
            if p2.get("boost"):
                self.car2.activate_boost()
            self.cp_index2 = self._check_checkpoint(self.car2, self.cp_index2)

            if self.cp_index1 >= len(self.track.checkpoints):
                self.winner = "P1"
            elif self.cp_index2 >= len(self.track.checkpoints):
                self.winner = "P2"

            if self.net is not None:
                self._send_state_to_client(server_time=time.monotonic())
            return

        # -----------------------------
        # Client
        # -----------------------------
        if self.mode == "client":
            # 1) input send
            if self.net is not None:
                self.net.send(
                    {
                        "type": "input",
                        "throttle": keys[self.p2_keymap["throttle"]],
                        "brake": keys[self.p2_keymap["brake"]],
                        "left": keys[self.p2_keymap["left"]],
                        "right": keys[self.p2_keymap["right"]],
                        "boost": keys[self.p2_keymap["boost"]],
                        "emote_req": self.client_pending_emote,
                    }
                )
                self.client_pending_emote = 0

            # 2) state apply
            st = self.latest_state
            if st and st.get("type") == "state":
                self._apply_server_state(st)
            return

    def _send_state_to_client(self, server_time: float):
        item_data = [{"x": i.rect.x, "y": i.rect.y} for i in self.items]
        self.net.send(
            {
                "type": "state",
                "server_time": server_time,
                "start_at": self.start_at,
                "go_until": self.go_until,
                "race_started": self.race_started,
                "map": self.current_map_id,
                "items": item_data,
                # car state (+ emote, has_item)
                "car1": {
                    "x": self.car1.x,
                    "y": self.car1.y,
                    "a": self.car1.angle,
                    "s": self.car1.speed,
                    "e": self.car1.emote_id,
                    "hi": self.car1.has_item,
                    "bt": float(getattr(self.car1, "boost_timer", 0.0)),
                },
                "car2": {
                    "x": self.car2.x,
                    "y": self.car2.y,
                    "a": self.car2.angle,
                    "s": self.car2.speed,
                    "e": self.car2.emote_id,
                    "hi": self.car2.has_item,
                    "bt": float(getattr(self.car2, "boost_timer", 0.0)),
                },
                "cp1": self.cp_index1,
                "cp2": self.cp_index2,
                "winner": self.winner,
            }
        )

    def _apply_server_state(self, st: dict):
        # time offset smoothing
        try:
            srv_now = float(st.get("server_time", time.monotonic()))
        except Exception:
            srv_now = time.monotonic()
        local_now = time.monotonic()
        new_offset = srv_now - local_now
        self.time_offset = self.time_offset * 0.8 + new_offset * 0.2

        # countdown sync
        if "start_at" in st:
            self.start_at = st.get("start_at")
        if "go_until" in st:
            self.go_until = st.get("go_until")
        if "race_started" in st:
            self.race_started = bool(st.get("race_started"))

        # map sync
        server_map = int(st.get("map", 0))
        if self.current_map_id != server_map:
            self.current_map_id = server_map
            self.track.load_map(server_map)
            self._reset_car_positions()

        # checkpoints / winner
        self.cp_index1 = int(st.get("cp1", self.cp_index1))
        self.cp_index2 = int(st.get("cp2", self.cp_index2))

        new_winner = st.get("winner", None)
        if new_winner and not self.winner:
            self.finish_time = time.time()
        self.winner = new_winner

        # items sync
        server_items = st.get("items", [])
        self.items = [Item(d["x"], d["y"]) for d in server_items]

        # cars
        c1 = st.get("car1", {})
        c2 = st.get("car2", {})

        self.car1.x = float(c1.get("x", self.car1.x))
        self.car1.y = float(c1.get("y", self.car1.y))
        self.car1.angle = float(c1.get("a", self.car1.angle))
        self.car1.speed = float(c1.get("s", self.car1.speed))
        self.car1.has_item = bool(c1.get("hi", self.car1.has_item))
        self.car1.boost_timer = float(c1.get("bt", getattr(self.car1, "boost_timer", 0.0)))
        self.car1.emote_id = int(c1.get("e", 0))
        if self.car1.emote_id > 0:
            self.car1.emote_end_time = time.time() + 1.0

        self.car2.x = float(c2.get("x", self.car2.x))
        self.car2.y = float(c2.get("y", self.car2.y))
        self.car2.angle = float(c2.get("a", self.car2.angle))
        self.car2.speed = float(c2.get("s", self.car2.speed))
        self.car2.has_item = bool(c2.get("hi", self.car2.has_item))
        self.car2.boost_timer = float(c2.get("bt", getattr(self.car2, "boost_timer", 0.0)))
        self.car2.emote_id = int(c2.get("e", 0))
        if self.car2.emote_id > 0:
            self.car2.emote_end_time = time.time() + 1.0

    # -----------------------------
    # Collision / movement helpers
    # -----------------------------
    def _check_item_collision_host(self, car: Car):
        if not car.has_item:
            car_rect = car.get_aabb_rect()
            for item in self.items[:]:
                if car_rect.colliderect(item.rect):
                    self.items.remove(item)
                    car.has_item = True
                    break

    def _move_with_sliding_control(self, car: Car, dt: float, control: dict):
        old_x, old_y = car.x, car.y
        car.update_control(
            dt,
            control.get("throttle", False),
            control.get("brake", False),
            control.get("left", False),
            control.get("right", False),
        )
        self._sliding_collision(car, old_x, old_y)

    def _move_with_sliding(self, car: Car, dt: float, keys, keymap: dict):
        old_x, old_y = car.x, car.y
        car.update(dt, keys, keymap)
        self._sliding_collision(car, old_x, old_y)

    def _sliding_collision(self, car: Car, old_x: float, old_y: float):
        dx, dy = car.x - old_x, car.y - old_y
        car.x, car.y = old_x, old_y

        car.x = old_x + dx
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.x = old_x

        car.y = old_y + dy
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.y = old_y

    def _check_checkpoint(self, car: Car, cp_index: int) -> int:
        if cp_index >= len(self.track.checkpoints):
            return cp_index
        target = self.track.checkpoints[cp_index]
        if car.get_aabb_rect().colliderect(target):
            return cp_index + 1
        return cp_index

    # -----------------------------
    # Draw
    # -----------------------------
    def draw(self):
        # 배경(트랙 draw에서 fill하지 않도록 통합했기 때문에 game이 fill 담당)
        self.screen.fill((40, 90, 40))
        pygame.draw.rect(self.screen, (30, 30, 30), self.screen.get_rect(), 6)

        self.track.draw(self.screen)

        # items
        for item in self.items:
            item.draw(self.screen)

        # cars + emotes
        self.car1.draw(self.screen, self.emote_imgs)
        self.car2.draw(self.screen, self.emote_imgs)

        if self.show_hud:
            self._draw_hud()

        # countdown overlay (winner 없을 때만)
        if self.winner is None:
            self._draw_countdown_overlay()

        # winner / rematch UI
        if self.winner and self.finish_time:
            self._draw_result_overlay()

        pygame.display.flip()

    def _draw_hud(self):
        p1_state = "BOOST!" if getattr(self.car1, "boost_timer", 0) > 0 else ("ITEM" if self.car1.has_item else "")
        p2_state = "BOOST!" if getattr(self.car2, "boost_timer", 0) > 0 else ("ITEM" if self.car2.has_item else "")

        lines = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"P1 CP: {self.cp_index1}/{len(self.track.checkpoints)} | {p1_state}",
            f"P2 CP: {self.cp_index2}/{len(self.track.checkpoints)} | {p2_state}",
        ]
        y = 8
        for line in lines:
            surf = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (10, y))
            y += 20

    def _draw_result_overlay(self):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        if self.winner == "P1":
            first, second = "P1", "P2"
            color1, color2 = (255, 255, 0), (200, 200, 200)
        else:
            first, second = "P2", "P1"
            color1, color2 = (255, 255, 0), (200, 200, 200)

        txt_1st = self.rank_font.render(f"1st Player: {first}", True, color1)
        txt_2nd = self.big_font.render(f"2nd Player: {second}", True, color2)

        self.screen.blit(txt_1st, txt_1st.get_rect(center=(self.width // 2, self.height // 2 - 80)))
        self.screen.blit(txt_2nd, txt_2nd.get_rect(center=(self.width // 2, self.height // 2)))

        elapsed = time.time() - self.finish_time
        if elapsed < 5.0:
            remain = int(6 - elapsed)
            count_msg = self.font.render(f"Next screen in {remain}...", True, (150, 150, 150))
            self.screen.blit(count_msg, count_msg.get_rect(center=(self.width // 2, self.height // 2 + 100)))
        else:
            q_msg = self.big_font.render("Do you want to do it again? (Y / N)", True, (255, 255, 255))
            self.screen.blit(q_msg, q_msg.get_rect(center=(self.width // 2, self.height // 2 + 100)))

            def get_vote_str(val):
                return "READY" if val is True else ("NO" if val is False else "Waiting...")

            p1_state = get_vote_str(self.rematch_p1)
            p2_state = get_vote_str(self.rematch_p2)

            status_msg = self.font.render(f"P1: {p1_state}   |   P2: {p2_state}", True, (200, 200, 200))
            self.screen.blit(status_msg, status_msg.get_rect(center=(self.width // 2, self.height // 2 + 150)))

    def _draw_countdown_overlay(self):
        # GO 표시 (race_started 이후, go_until까지)
        if self.race_started:
            if self.go_until is not None and self._host_time_now() < float(self.go_until):
                msg = self.font.render("GO!", True, (0, 255, 0))
                self.screen.blit(msg, msg.get_rect(center=(self.width // 2, 140)))
            return

        left = self._countdown_left()
        if left is None:
            return

        if left <= 0:
            sec = 1
        else:
            sec = int(left) + 1
            sec = max(1, min(3, sec))

        big = pygame.font.SysFont(None, 90)
        num = big.render(str(sec), True, (255, 255, 255))
        self.screen.blit(num, num.get_rect(center=(self.width // 2, 140)))

        # 신호등
        cx, cy = self.width // 2, 240
        radius = 22
        gap = 60

        red_on = (sec >= 3) or (sec == 2)
        yellow_on = (sec <= 2)
        green_on = False

        red = (255, 60, 60) if red_on else (80, 20, 20)
        yellow = (255, 220, 0) if yellow_on else (80, 60, 0)
        green = (0, 220, 0) if green_on else (0, 60, 0)

        box = pygame.Rect(cx - 70, cy - 45, 140, 90)
        pygame.draw.rect(self.screen, (20, 20, 20), box, border_radius=12)
        pygame.draw.rect(self.screen, (200, 200, 200), box, 2, border_radius=12)
        pygame.draw.circle(self.screen, red, (cx - gap, cy), radius)
        pygame.draw.circle(self.screen, yellow, (cx, cy), radius)
        pygame.draw.circle(self.screen, green, (cx + gap, cy), radius)

        small = pygame.font.SysFont(None, 26)
        tip = small.render("Get ready...", True, (220, 220, 220))
        self.screen.blit(tip, tip.get_rect(center=(self.width // 2, 300)))

    def _host_time_now(self):
        # client는 local monotonic + offset => host time으로 환산
        return time.monotonic() + float(self.time_offset)

    def _countdown_left(self):
        if self.start_at is None:
            return None
        return float(self.start_at) - self._host_time_now()

    # -----------------------------
    # Cleanup
    # -----------------------------
    def _cleanup_network(self):
        try:
            self._broadcast_stop.set()
        except Exception:
            pass
        try:
            if getattr(self, "net", None):
                self.net.close()
        except Exception:
            pass
        try:
            if getattr(self, "_srv", None):
                self._srv.close()
        except Exception:
            pass
