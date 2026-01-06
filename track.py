# track.py
import pygame

class Track:
    def __init__(self):
        # # 벽(장애물) 목록: pygame.Rect(x, y, w, h)
        # self.walls = [
        #     # 바깥 테두리(두께 20) 느낌의 벽 4개
        #     pygame.Rect(0, 0, 900, 20),
        #     pygame.Rect(0, 580, 900, 20),
        #     pygame.Rect(0, 0, 20, 600),
        #     pygame.Rect(880, 0, 20, 600),

        #     # 내부 장애물(코스 모양 만들기)
        #     pygame.Rect(120, 100, 660, 20),
        #     pygame.Rect(120, 100, 20, 380),
        #     pygame.Rect(120, 460, 520, 20),
        #     pygame.Rect(620, 220, 20, 260),
        #     pygame.Rect(260, 220, 380, 20),
        # ]

        # # (선택) 시각용 체크포인트: 아직 판정 안 함(그리기만)
        # self.checkpoints = [
        #     pygame.Rect(200, 60, 80, 20),
        #     pygame.Rect(760, 260, 20, 80),
        #     pygame.Rect(300, 520, 80, 20),
        # ]


        T = 16  # ✅ 벽 두께 줄임 (통로 넓어짐)

        self.walls = [
            # 바깥 테두리(외벽)
            pygame.Rect(0, 0, 900, T),
            pygame.Rect(0, 600 - T, 900, T),
            pygame.Rect(0, 0, T, 600),
            pygame.Rect(900 - T, 0, T, 600),
        ]

        # ✅ 내부 섬들(통로 넓게 조정)
        self.walls += [
            # (A) 중앙 큰 섬: 크기 줄여서 사방 통로 넓힘
            pygame.Rect(220, 170, 460, 200),   # 기존(170,140,560,260)보다 훨씬 작게

            # (B) 위쪽 굴곡: 덩어리들을 작게/위로 올려 통로 확보
            pygame.Rect(140, 60, 140, 120),
            pygame.Rect(330, 60, 240, 70),
            pygame.Rect(620, 60, 140, 120),

            # (C) 오른쪽 헤어핀: 폭/높이 줄여 막힘 감소
            pygame.Rect(740, 250, 110, 150),

            # (D) 왼쪽 중간: 폭 줄여 좌측 통로 넓힘
            pygame.Rect(90, 270, 130, 140),

            # (E) 하단 직선 위 섬: 높이 줄여 하단 통로 넓힘
            pygame.Rect(260, 450, 380, 40),

            # (F) 중앙 돌출부(시케인 느낌): 과하게 막히면 주석처리 가능
            pygame.Rect(460, 260, 100, 60),
        ]

        # 체크포인트도 통로 넓어진 배치에 맞춰 약간 조정
        self.checkpoints = [
            pygame.Rect(420, 520, 60, 40),  # 하단 직선
            pygame.Rect(780, 120, 60, 60),  # 우상단
            pygame.Rect(120, 120, 60, 60),  # 좌상단
        ]

    def draw(self, screen):
                # 배경(잔디 느낌)
        screen.fill((40, 90, 40))

        # 도로 느낌(그냥 어두운 영역을 깔아도 되지만, 여기선 벽만 표시)
        # 외곽 테두리 강조
        pygame.draw.rect(screen, (30, 30, 30), screen.get_rect(), 6)

        # 벽(섬) 그리기
        for w in self.walls:
            pygame.draw.rect(screen, (90, 90, 90), w)

        # 체크포인트(초록 테두리)
        for cp in self.checkpoints:
            pygame.draw.rect(screen, (60, 200, 60), cp, 3)

        # # 배경(트랙 영역) 느낌
        # pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(50, 50, 200, 120))

        # screen_rect = screen.get_rect()
        # pygame.draw.rect(screen, (40, 40, 40), screen_rect)          # 바탕
        # pygame.draw.rect(screen, (70, 70, 70), screen_rect, 8)       # 테두리 강조

        # # 벽 그리기
        # for w in self.walls:
        #     pygame.draw.rect(screen, (0, 255, 255), w)  # 시안색


        # # 체크포인트(선택: 눈에만 보이게)
        # for cp in self.checkpoints:
        #     pygame.draw.rect(screen, (60, 140, 60), cp, 2)

    def collides_with_walls(self, rect):
        for w in self.walls:
            if rect.colliderect(w):
                return True
        return False
