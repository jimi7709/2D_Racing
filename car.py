# car.py
import math
import pygame


class Car:
    """
    자동차 1대의 책임:
    - 상태: x, y, angle(radians), speed
    - 입력 기반 업데이트(가속/브레이크/회전/마찰)
    - 화면 렌더링(회전 포함)

    game.py에서 요구하는 것:
    - self.x, self.y, self.speed, self.angle 존재
    - update(dt, keys), draw(screen) 제공
    """

    def __init__(self, x: float, y: float):
        # 상태
        self.x = float(x)
        self.y = float(y)
        self.angle = 0.0     # radians
        self.speed = 0.0     # pixels/sec

        # 튜닝 파라미터(완료주의 기본값)
        self.ACCEL = 300.0       # 가속 (px/s^2)
        self.BRAKE = 450.0       # 감속/브레이크 (px/s^2)
        self.FRICTION = 240.0    # 마찰 (px/s^2)
        self.TURN_SPEED = 2.6    # 회전 속도 (rad/s)
        self.MAX_SPEED = 500.0   # 최대 속도 (px/s)

        # 차량 크기(충돌 박스도 이걸로 만들 예정)
        self.W = 20
        self.H = 11

        # 렌더링용 색/표시
        self.body_color = (230, 230, 230)
        self.nose_color = (255, 80, 80)  # 앞부분 표시(방향 확인)

    def update(self, dt: float, keys):
        """
        keys: pygame.key.get_pressed() 결과
        dt: seconds
        """
        # 1) 가속/브레이크
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.speed += self.ACCEL * dt
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.speed -= self.BRAKE * dt
        else:
            # 2) 마찰: 속도를 0으로 끌어오기
            if self.speed > 0:
                self.speed = max(0.0, self.speed - self.FRICTION * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + self.FRICTION * dt)

        # 3) 속도 제한(후진은 절반 정도만 허용)
        self.speed = max(-self.MAX_SPEED * 0.4, min(self.MAX_SPEED, self.speed))

        # 4) 회전(속도가 거의 0이면 회전 금지 → 레이싱 느낌)
        if abs(self.speed) > 5:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                self.angle -= self.TURN_SPEED * dt
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                self.angle += self.TURN_SPEED * dt

        # 5) 이동(각도 방향 벡터로 전진)
        vx = math.cos(self.angle) * self.speed
        vy = math.sin(self.angle) * self.speed
        self.x += vx * dt
        self.y += vy * dt

    def draw(self, screen: pygame.Surface):
        """
        회전 포함 렌더링:
        - 차체 사각형
        - 앞부분 점(방향 표시)
        """
        car_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(
            car_surf,
            self.body_color,
            pygame.Rect(0, 0, self.W, self.H),
            border_radius=6,
        )

        # 방향 표시(앞쪽)
        pygame.draw.circle(
            car_surf,
            self.nose_color,
            (self.W - 6, self.H // 2),
            4,
        )

        rotated = pygame.transform.rotate(car_surf, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect.topleft)

    def get_aabb_rect(self):
        return pygame.Rect(
        int(self.x - self.W / 2),
        int(self.y - self.H / 2),
        self.W,
        self.H
        )
