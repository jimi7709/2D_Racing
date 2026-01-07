# car.py
import math
import time

import pygame


class Car:
    """
    통합된 자동차 클래스:
    - 기본 주행 물리 (가속, 마찰, 회전)
    - 감정표현 (이모트) 기능 포함
    - 아이템 (부스트) 기능 포함

    통합 규칙:
    - 생성자: Car(x, y) 형태 유지 (색은 setattr로 바꿀 수 있음)
    - draw(screen, emote_imgs=None) 형태 유지 (emote_imgs는 선택)
    """

    def __init__(self, x, y, body_color=(230, 230, 230), nose_color=(255, 80, 80)):
        # 상태
        self.x = float(x)
        self.y = float(y)
        self.angle = 0.0
        self.speed = 0.0

        # 튜닝 파라미터
        # (기본 속도는 낮추고, 부스트로 체감되게 구성)
        self.ACCEL = 200.0
        self.BRAKE = 450.0
        self.FRICTION = 240.0
        self.TURN_SPEED = 2.6
        self.MAX_SPEED = 300.0

        # 차량 크기
        self.W = 20
        self.H = 11

        # 색상
        self.body_color = body_color
        self.nose_color = nose_color

        # 감정표현
        self.emote_id = 0
        self.emote_end_time = 0.0

        # 아이템/부스트
        self.has_item = False
        self.boost_timer = 0.0
        self.boost_duration = 2.0
        self.boost_factor = 1.8

    # --- 감정표현 ---
    def set_emote(self, emote_id: int):
        self.emote_id = int(emote_id)
        self.emote_end_time = time.time() + 2.5

    # --- 아이템/부스트 ---
    def activate_boost(self):
        if self.has_item:
            self.has_item = False
            self.boost_timer = self.boost_duration

    # --- 업데이트 ---
    def update(self, dt, keys, keymap):
        throttle = keys[keymap["throttle"]]
        brake = keys[keymap["brake"]]
        left = keys[keymap["left"]]
        right = keys[keymap["right"]]
        self.update_control(dt, throttle, brake, left, right)

    def update_control(self, dt, throttle: bool, brake: bool, left: bool, right: bool):
        # 부스트 상태에 따라 최대 속도/가속도 증가
        current_max_speed = self.MAX_SPEED
        current_accel = self.ACCEL

        if self.boost_timer > 0.0:
            self.boost_timer = max(0.0, self.boost_timer - dt)
            current_max_speed *= self.boost_factor
            current_accel *= self.boost_factor

        # 가속/브레이크
        if throttle:
            self.speed += current_accel * dt
        elif brake:
            self.speed -= self.BRAKE * dt
        else:
            # 마찰
            if self.speed > 0:
                self.speed = max(0.0, self.speed - self.FRICTION * dt)
            elif self.speed < 0:
                self.speed = min(0.0, self.speed + self.FRICTION * dt)

        # 속도 제한(후진은 약 40%)
        self.speed = max(-current_max_speed * 0.4, min(current_max_speed, self.speed))

        # 회전 (속도가 어느 정도 있을 때만)
        if abs(self.speed) > 5:
            if left:
                self.angle -= self.TURN_SPEED * dt
            if right:
                self.angle += self.TURN_SPEED * dt

        # 위치 업데이트
        vx = math.cos(self.angle) * self.speed
        vy = math.sin(self.angle) * self.speed
        self.x += vx * dt
        self.y += vy * dt

    # --- 렌더링 ---
    def draw(self, screen: pygame.Surface, emote_imgs=None):
        # 차체
        car_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        pygame.draw.rect(car_surf, self.body_color, pygame.Rect(0, 0, self.W, self.H), border_radius=6)

        # 앞부분 표시
        pygame.draw.circle(car_surf, self.nose_color, (self.W - 6, self.H // 2), 4)

        # 아이템 보유 표시
        if self.has_item:
            pygame.draw.circle(car_surf, (0, 200, 255), (self.W // 2, self.H // 2), 3)

        rotated = pygame.transform.rotate(car_surf, -math.degrees(self.angle))
        rect = rotated.get_rect(center=(self.x, self.y))
        screen.blit(rotated, rect.topleft)

        # 감정표현(이모트)
        now = time.time()
        if self.emote_id > 0:
            if now < self.emote_end_time:
                if emote_imgs and self.emote_id in emote_imgs:
                    img = emote_imgs[self.emote_id]
                    cx, cy = self.x, self.y - 40
                    screen.blit(img, img.get_rect(center=(cx, cy)))
            else:
                self.emote_id = 0

    def get_aabb_rect(self):
        return pygame.Rect(int(self.x - self.W / 2), int(self.y - self.H / 2), self.W, self.H)
