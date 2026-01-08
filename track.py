# track.py
import random
import math
import pygame


class Track:
    """
    통합 Track:
    - Track(map_id=0) + load_map(map_id)
    - spawn_points 제공 (car spawn)
    - get_random_safe_point 제공 (아이템 스폰)
    - draw()는 "fill을 하지 않음" (Game이 배경 fill 담당)
    """

    def __init__(self, map_id: int = 0):
        self.walls: list[pygame.Rect] = []
        self.checkpoints: list[pygame.Rect] = []

        self.spawn_points = [(300, 540), (350, 540)]
        self.spawn_angle = 0.0 # 추가 - 라디안 단위


        # pygame.init() 이후에 font 사용 가능
        try:
            self.font = pygame.font.SysFont("Arial", 30, bold=True)
        except Exception:
            self.font = None

        # 기존 track.py의 맵(=Map 1로 사용)
        T = 16
        map0_walls = [
            pygame.Rect(0, 0, 900, T),
            pygame.Rect(0, 600 - T, 900, T),
            pygame.Rect(0, 0, T, 600),
            pygame.Rect(900 - T, 0, T, 600),

            pygame.Rect(220, 170, 460, 200),
            pygame.Rect(140, 60, 140, 120),
            pygame.Rect(330, 60, 240, 70),
            pygame.Rect(620, 60, 140, 120),
            pygame.Rect(740, 250, 110, 150),
            pygame.Rect(90, 270, 130, 140),
            pygame.Rect(260, 450, 380, 40),
            pygame.Rect(460, 260, 100, 60),
        ]
        map0_cps = [
            pygame.Rect(420, 520, 60, 40),
            pygame.Rect(780, 120, 60, 60),
            pygame.Rect(120, 120, 60, 60),
        ]
        map0_spawn = [(200, 530), (200, 560)] 

        # 기존 track.py 맵을 Map 1로 + track2의 맵들을 Map 2~5로 (총 5개)
        self.MAP_DATA = [
            {"walls": map0_walls, "checkpoints": map0_cps, "spawn_points": map0_spawn},

            # Map 2: 기본 오벌 트랙(원본 track2의 Map 1)
            {
                "walls": [
                    pygame.Rect(0, 0, 900, 20),
                    pygame.Rect(0, 580, 900, 20),
                    pygame.Rect(0, 0, 20, 600),
                    pygame.Rect(880, 0, 20, 600),
                    pygame.Rect(200, 150, 500, 300),
                ],
                "checkpoints": [
                    pygame.Rect(750, 60, 80, 80),
                    pygame.Rect(750, 460, 80, 80),
                    pygame.Rect(70, 260, 80, 80),
                ],
                "spawn_points": [(100, 300), (130, 300)],
                "spawn_angle": -math.pi/2 # 추가

            },

            # Map 3: U자
            {
                "walls": [
                    pygame.Rect(0, 0, 900, 20),
                    pygame.Rect(0, 580, 900, 20),
                    pygame.Rect(0, 0, 20, 600),
                    pygame.Rect(880, 0, 20, 600),
                    pygame.Rect(200, 150, 500, 250),
                    pygame.Rect(200, 400, 150, 100),
                    pygame.Rect(550, 400, 150, 100),
                ],
                "checkpoints": [
                    pygame.Rect(50, 50, 80, 80),
                    pygame.Rect(770, 50, 80, 80),
                    pygame.Rect(420, 500, 80, 80),
                ],
                "spawn_points": [(100, 500), (130, 500)],
                "spawn_angle": -math.pi/2 # 추가
            },

            # Map 4: 8자
            {
                "walls": [
                    pygame.Rect(0, 0, 900, 20),
                    pygame.Rect(0, 580, 900, 20),
                    pygame.Rect(0, 0, 20, 600),
                    pygame.Rect(880, 0, 20, 600),
                    pygame.Rect(150, 100, 250, 150),
                    pygame.Rect(500, 100, 250, 150),
                    pygame.Rect(150, 350, 250, 150),
                    pygame.Rect(500, 350, 250, 150),
                ],
                "checkpoints": [
                    pygame.Rect(420, 30, 60, 60),
                    pygame.Rect(420, 510, 60, 60),
                    pygame.Rect(400, 270, 100, 60),
                ],
                "spawn_points": [(420, 280), (450, 280)],
                "spawn_angle": -math.pi/2 # 추가
            },

            # Map 5: 미로형
            {
                "walls": [
                    pygame.Rect(0, 0, 900, 20),
                    pygame.Rect(0, 580, 900, 20),
                    pygame.Rect(0, 0, 20, 600),
                    pygame.Rect(880, 0, 20, 600),
                    pygame.Rect(200, 0, 20, 450),
                    pygame.Rect(450, 150, 20, 450),
                    pygame.Rect(700, 0, 20, 450),
                ],
                "checkpoints": [
                    pygame.Rect(100, 500, 60, 60),
                    pygame.Rect(550, 50, 60, 60),
                    pygame.Rect(800, 500, 60, 60),
                ],
                "spawn_points": [(100, 100), (130, 100)],
                "spawn_angle": math.pi/2 # 추가
            },
        ]

        self.load_map(map_id)

    def load_map(self, map_id: int):
        if map_id < 0 or map_id >= len(self.MAP_DATA):
            map_id = 0

        data = self.MAP_DATA[map_id]
        self.walls = data["walls"]
        self.checkpoints = data["checkpoints"]
        self.spawn_points = data.get("spawn_points", [(300, 540), (350, 540)])
        self.spawn_angle = data.get("spawn_angle", 0.0) # 추가


    def collides_with_walls(self, rect: pygame.Rect) -> bool:
        for w in self.walls:
            if rect.colliderect(w):
                return True
        return False

    def draw(self, screen: pygame.Surface):
        # NOTE: 배경 fill은 Game이 담당 (통합 규칙)
        for w in self.walls:
            pygame.draw.rect(screen, (100, 100, 100), w)
            pygame.draw.rect(screen, (150, 150, 150), w, 2)

        for i, cp in enumerate(self.checkpoints):
            pygame.draw.rect(screen, (0, 255, 0), cp, 4)
            if self.font:
                text = self.font.render(str(i + 1), True, (255, 255, 255))
                screen.blit(text, text.get_rect(center=cp.center))

    def get_random_safe_point(self, width: int, height: int, obj_w: int, obj_h: int):
        for _ in range(50):
            x = random.randint(50, width - 50)
            y = random.randint(50, height - 50)
            rect = pygame.Rect(x, y, obj_w, obj_h)
            if not self.collides_with_walls(rect):
                return (x, y)
        return None
