# game.py
import pygame

from car import Car
from track import Track


class Game:
    """
    Game = 전체 흐름 제어(컨트롤 타워)
    - 이벤트 처리(종료)
    - 입력 수집
    - 업데이트(dt 기반)
    - 그리기(트랙 -> 자동차 -> HUD)
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        self.screen = screen
        self.clock = clock
        self.running = True

        # 화면 크기(Track/Car에서 사용할 수도 있으니 보관)
        self.width = screen.get_width()
        self.height = screen.get_height()

        # 월드 구성 요소
        self.track = Track()  # 1-3: 벽/코스 그리기
        #self.car = Car(self.width // 2, self.height // 2)  # 1-2: 차량 1대
        #self.car1 = Car(300, 540)   # P1
        #self.car2 = Car(350, 540)   # P2 (조금 옆에)
        
         # 2P 차량
        self.car1 = Car(300, 540, body_color=(230, 230, 230), nose_color=(255, 80, 80))
        self.car2 = Car(350, 540, body_color=(120, 160, 255), nose_color=(255, 255, 80))


        self.cp_index1 = 0
        self.cp_index2 = 0
        self.winner = None  # "P1" or "P2"

         # 키맵(입력 분리용): 여기서 "정의만" 해둠  
        self.p1_keymap = {"throttle": pygame.K_w, "brake": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d}
        self.p2_keymap = {"throttle": pygame.K_UP, "brake": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT}

        # UI
        self.show_hud = True
        self.font = pygame.font.SysFont(None, 22)

        # keys = pygame.key.get_pressed()

        # p1 = {
        #     "throttle": keys[pygame.K_w],
        #     "brake": keys[pygame.K_s],
        #     "left": keys[pygame.K_a],
        #     "right": keys[pygame.K_d],
        # }

        # p2 = {
        #     "throttle": keys[pygame.K_UP],
        #     "brake": keys[pygame.K_DOWN],
        #     "left": keys[pygame.K_LEFT],
        #     "right": keys[pygame.K_RIGHT],
        # }

        
        # self.car.angle = 0.0
        # self.car.speed = 0.0

        # 디버그/옵션
        self.show_hud = True
        self.font = pygame.font.SysFont(None, 22)

        #체크 포인트
        self.cp_index = 0       # 다음에 통과해야 할 체크포인트 인덱스 (0~2)
        self.finished = False   # 3개 다 통과하면 True

    def update_one_car(self, car, control, cp_index): # 비권장
        old_x, old_y = car.x, car.y

        # car.update가 이동까지 수행
        car.update(
            self.dt,
            control["throttle"],
            control["brake"],
            control["left"],
            control["right"]
        )

        # 변화량 추출 → 축별 적용(슬라이딩)
        dx, dy = car.x - old_x, car.y - old_y
        car.x, car.y = old_x, old_y

        # X
        car.x = old_x + dx
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.x = old_x

        # Y
        car.y = old_y + dy
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.y = old_y

        # 체크포인트(순서 강제)
        if cp_index < len(self.track.checkpoints):
            target = self.track.checkpoints[cp_index]
            if car.get_aabb_rect().colliderect(target):
                cp_index += 1

        return cp_index


    def run(self):
        print("Game.run() entered")   # ✅ 여기 찍히는지

        """메인 루프"""
        while self.running:
            print("tick")             # ✅ 계속 찍히는지(너무 많이 찍히면 1초만 테스트하고 지우기)
            dt = self.clock.tick(60) / 1000.0  # seconds

            self.handle_events()
            self.update(dt)
            self.draw()

    def handle_events(self):
        """QUIT 및 토글 키 같은 '이벤트성' 입력 처리"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # (선택) HUD 토글: H 키
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    self.show_hud = not self.show_hud

                # (선택) ESC로 종료
                if event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self, dt):
        keys = pygame.key.get_pressed()

        # 승자 나오면 차량 업데이트 중지(원하면 계속 움직이게 해도 됨)
        if self.winner is None:
            # P1 업데이트
            self._move_with_sliding(self.car1, dt, keys, self.p1_keymap)
            self.cp_index1 = self._check_checkpoint(self.car1, self.cp_index1)

            # P2 업데이트
            self._move_with_sliding(self.car2, dt, keys, self.p2_keymap)
            self.cp_index2 = self._check_checkpoint(self.car2, self.cp_index2)

            # 승리 판정
            if self.cp_index1 >= len(self.track.checkpoints):
                self.winner = "P1"
            elif self.cp_index2 >= len(self.track.checkpoints):
                self.winner = "P2"


    # def update(self, dt):
    #     keys = pygame.key.get_pressed()

    #     # 1) 이동 전 상태 저장
    #     old_x, old_y = self.car.x, self.car.y

    #     # 2) car.update로 (임시) 새 위치까지 계산하게 둠
    #     #    -> car.update가 self.x/self.y를 바꿔버리므로, 변화량을 뽑아낸다.
    #     self.car.update(dt, keys)

    #     new_x, new_y = self.car.x, self.car.y
    #     dx = new_x - old_x
    #     dy = new_y - old_y

    #     # 3) 일단 원래 위치로 되돌려 놓고, 축별로 적용
    #     self.car.x, self.car.y = old_x, old_y

    #     # --- X축 먼저 적용 ---
    #     self.car.x = old_x + dx
    #     if self.track.collides_with_walls(self.car.get_aabb_rect()):
    #         # X축은 벽에 막힘 -> 되돌림
    #         self.car.x = old_x
    #         # (선택) X축 충돌이면 속도 약간 깎기(너무 딱딱하면 주석)
    #         # self.car.speed *= 0.8

    #     # --- Y축 적용 ---
    #     self.car.y = old_y + dy
    #     if self.track.collides_with_walls(self.car.get_aabb_rect()):
    #         # Y축은 벽에 막힘 -> 되돌림
    #         self.car.y = old_y
    #         # (선택) Y축 충돌이면 속도 약간 깎기
    #         # self.car.speed *= 0.8

    #     # --- 체크포인트 판정(순서 강제) ---
    #     if not self.finished:
    #         car_rect = self.car.get_aabb_rect()
    #         target_cp = self.track.checkpoints[self.cp_index]

    #     if car_rect.colliderect(target_cp):
    #         self.cp_index += 1

    #     if self.cp_index >= len(self.track.checkpoints):
    #         self.finished = True
    #         # 완료주의: 일단 속도 0으로 정지
    #         self.car.speed = 0.0

    #     if self.winner is None:
    #         if self.cp_index1 >= len(self.track.checkpoints):
    #             self.winner = "P1"
    #         elif self.cp_index2 >= len(self.track.checkpoints):
    #             self.winner = "P2"


    # def update(self, dt: float):
    #     """상태 업데이트(입력 -> 차량 업데이트). 1-3 단계에서는 충돌/체크포인트 없음."""
    #     keys = pygame.key.get_pressed()

    #         # ✅ 이동 전 좌표 저장
    #     old_x, old_y = self.car.x, self.car.y
    #     old_speed = self.car.speed  # (선택) 충돌 시 속도 처리용

    #     # 차량 이동(입력 반영)
    #     self.car.update(dt, keys)

    #     # ✅ 이동 후 충돌 검사
    #     car_rect = self.car.get_aabb_rect()
    #     if self.track.collides_with_walls(car_rect):
    #     # ✅ 벽과 겹치면 원래 위치로 되돌림
    #         self.car.x, self.car.y = old_x, old_y
    #     # (선택) 벽에 박으면 속도 조금 깎기 (튕김 대신)
    #         self.car.speed = 0.0

    #     # 차량 업데이트(가속/회전/마찰 등은 car.py에서 처리)
    #     #self.car.update(dt, keys)
    #     # (선택) 화면 밖으로 나가지 않게 임시 클램프
    #     # ※ 나중에 벽 충돌 구현하면 이 부분은 제거/완화해도 됨
    #     #self.car.x = max(0, min(self.width, self.car.x))
    #     #self.car.y = max(0, min(self.height, self.car.y))

    def draw(self):
        """그리기 순서 중요: fill -> track -> car -> hud -> flip"""
        # 배경
        self.screen.fill((20, 20, 20))

        # 트랙(벽/코스) 먼저
        self.track.draw(self.screen)

        
        # ✅ 자동차 2대 그리기
        self.car1.draw(self.screen)
        self.car2.draw(self.screen)

        # HUD
        if self.show_hud:
            self._draw_hud()

        # ✅ 승자 메시지(있으면) - flip 전에
        if self.winner:
            msg = self.font.render(f"{self.winner} WINS! (ESC to quit)", True, (255, 255, 0))
            self.screen.blit(msg, msg.get_rect(center=(self.width // 2, self.height // 2)))
            # if self.finished:
            #     msg = self.font.render("FINISH! (Press ESC to quit)", True, (255, 255, 0))
            #     rect = msg.get_rect(center=(self.width // 2, self.height // 2))
            #     self.screen.blit(msg, rect)
        
        pygame.display.flip()
    
    def _draw_hud(self):
        lines = [
            f"FPS: {self.clock.get_fps():.1f}",
            f"P1 CP: {self.cp_index1}/{len(self.track.checkpoints)}",
            f"P2 CP: {self.cp_index2}/{len(self.track.checkpoints)}",
        ]
        y = 8
        for line in lines:
            surf = self.font.render(line, True, (220, 220, 220))
            self.screen.blit(surf, (10, y))
            y += 20

    # def _draw_hud(self):
    #     """상단 왼쪽 디버그 정보 표시"""
    #     # car.py에 angle/speed가 있어야 함(없으면 car.py에 추가 필요)
    #     speed = getattr(self.car, "speed", 0.0)
    #     angle = getattr(self.car, "angle", 0.0)

    #     lines = [
    #         f"FPS: {self.clock.get_fps():.1f}",
    #         f"checkpoint: {self.cp_index}/{len(self.track.checkpoints)}",

    #         f"pos: ({self.car.x:.1f}, {self.car.y:.1f})",
    #         f"speed: {speed:.1f}",
    #         f"angle(rad): {angle:.2f}",
    #         "H: toggle HUD | ESC: quit",
    #     ]

    #     y = 8
    #     for line in lines:
    #         surf = self.font.render(line, True, (220, 220, 220))
    #         self.screen.blit(surf, (10, y))
    #         y += 20


    def _move_with_sliding(self, car, dt, keys, keymap):
        old_x, old_y = car.x, car.y

        # car.update가 (x,y)를 바꿔버리므로 변화량 추출 방식 사용
        car.update(dt, keys, keymap)
        dx, dy = car.x - old_x, car.y - old_y

        car.x, car.y = old_x, old_y

        # X
        car.x = old_x + dx
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.x = old_x

        # Y
        car.y = old_y + dy
        if self.track.collides_with_walls(car.get_aabb_rect()):
            car.y = old_y


    def _check_checkpoint(self, car, cp_index):
        if cp_index >= len(self.track.checkpoints):
            return cp_index
        target = self.track.checkpoints[cp_index]
        if car.get_aabb_rect().colliderect(target):
            return cp_index + 1
        return cp_index
