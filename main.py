# main.py
import pygame
import time

from game import Game
import network
from ui import Button, TextInput, draw_title, draw_label


WIDTH, HEIGHT = 900, 600


def run_host(screen, clock, room_name, room_id, port):
    # Host 모드로 게임 실행 (Game.run()이 끝나면 메뉴로 돌아옴)
    game = Game(
        screen, clock,
        mode="host",
        port=port,
        room_name=room_name,
        room_id=room_id,
    )
    game.run()


def run_client(screen, clock, host_ip, port):
    game = Game(
        screen, clock,
        mode="client",
        host_ip=host_ip,
        port=port,
    )
    game.run()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2D Racing - LAN")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont(None, 40)
    font = pygame.font.SysFont(None, 26)
    font_small = pygame.font.SysFont(None, 22)

    state = "menu"   # menu / create / join / settings
    running = True

    # -------- 메뉴 버튼 --------
    btn_create = Button((340, 210, 220, 55), "Create Room", font)
    btn_join = Button((340, 280, 220, 55), "Join Room", font)
    btn_settings = Button((340, 350, 220, 55), "Settings", font)
    btn_quit = Button((340, 420, 220, 55), "Quit", font)

    # -------- 방 만들기 UI --------
    inp_room_name = TextInput((340, 210, 360, 45), font, text="JimiRoom", placeholder="방 이름")
    inp_room_id = TextInput((340, 270, 360, 45), font, text="RACE01", placeholder="방 ID (중복되면 덮어씀)")
    inp_port = TextInput((340, 330, 360, 45), font, text="5000", placeholder="포트 (예: 5000)")

    btn_make = Button((340, 400, 170, 55), "Make", font)
    btn_back1 = Button((530, 400, 170, 55), "Back", font)

    # -------- 방 참여 UI --------
    btn_refresh = Button((30, 520, 150, 50), "Refresh", font_small)
    btn_back2 = Button((720, 520, 150, 50), "Back", font_small)

    last_discover_time = 0.0
    rooms = []  # list of dict
    room_buttons = []
    
    def refresh_rooms():
        nonlocal rooms, room_buttons
        found = network.discover_rooms(listen_seconds=1.2)
        rooms = list(found.values())
        rooms.sort(key=lambda r: (r.get("room_name", ""), r.get("ip", "")))

        room_buttons = []
        y = 120
        for r in rooms[:10]:
            name = r.get("room_name", "Room")
            ip = r.get("ip", "?")
            port = r.get("port", "?")
            text = f"{name}  ({ip}:{port})"
            room_buttons.append((r, Button((60, y, 780, 42), text, font_small)))
            y += 50
    # def refresh_rooms():
    #     nonlocal rooms, room_buttons, last_discover_time
    #     last_discover_time = time.time()
    #     found = network.discover_rooms(listen_seconds=1.2)  # 1~2초면 충분
    #     rooms = list(found.values())
    #     # 보기 좋게 정렬: 이름, ip
    #     rooms.sort(key=lambda r: (r.get("room_name", ""), r.get("ip", "")))

    #     room_buttons = []
    #     y = 120
    #     for i, r in enumerate(rooms[:10]):  # 화면상 10개만
    #         name = r.get("room_name", "Room")
    #         ip = r.get("ip", "?")
    #         port = r.get("port", "?")
    #         text = f"{i+1}. {name}  ({ip}:{port})"
    #         room_buttons.append((r, Button((60, y, 780, 42), text, font_small)))
    #         y += 50

    # 초기 진입 시 목록 한번
    # (join 화면 들어갈 때 refresh_rooms() 호출)

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ESC로 뒤로/종료
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state == "menu":
                    running = False
                else:
                    state = "menu"

            if state == "menu":
                if btn_create.handle_event(event):
                    state = "create"
                if btn_join.handle_event(event):
                    state = "join"
                    refresh_rooms()
                if btn_settings.handle_event(event):
                    state = "settings"
                if btn_quit.handle_event(event):
                    running = False

            elif state == "create":
                inp_room_name.handle_event(event)
                inp_room_id.handle_event(event)
                inp_port.handle_event(event)

                if btn_back1.handle_event(event):
                    state = "menu"

                if btn_make.handle_event(event):
                    room_name = inp_room_name.text.strip() or "Room"
                    room_id = inp_room_id.text.strip() or "RACE01"
                    try:
                        port = int(inp_port.text.strip())
                    except Exception:
                        port = 5000

                    # 여기서 게임으로 진입 (끝나면 메뉴로 복귀)
                    run_host(screen, clock, room_name, room_id, port)
                    state = "menu"

            elif state == "join":
                if btn_back2.handle_event(event):
                    state = "menu"
                if btn_refresh.handle_event(event):
                    refresh_rooms()

                # 방 버튼 클릭
                for r, b in room_buttons:
                    if b.handle_event(event):
                        host_ip = r.get("ip")
                        port = int(r.get("port"))
                        run_client(screen, clock, host_ip, port)
                        state = "menu"
                        break

            elif state == "settings":
                # 일단 껍데기만: 뒤로는 ESC 또는 상태 변경
                pass

        # -------- 화면 그리기 --------
        screen.fill((18, 18, 18))

        if state == "menu":
            draw_title(screen, font_title, "2D Racing - LAN")
            btn_create.draw(screen)
            btn_join.draw(screen)
            btn_settings.draw(screen)
            btn_quit.draw(screen)

        elif state == "create":
            draw_title(screen, font_title, "Make Room")
            draw_label(screen, font_small, "Room Name", 220, 222)
            draw_label(screen, font_small, "Room ID", 220, 282)
            draw_label(screen, font_small, "Port", 220, 342)

            inp_room_name.draw(screen)
            inp_room_id.draw(screen)
            inp_port.draw(screen)

            btn_make.draw(screen)
            btn_back1.draw(screen)

            # 참고: host IP 보여주기
            ip = network.get_local_ip()
            info = font_small.render(f"내 IP: {ip}  (같은 Wi-Fi에서 방 목록으로 자동 표시됨)", True, (180, 180, 180))
            screen.blit(info, (30, 520))

        elif state == "join":
            draw_title(screen, font_title, "게임 방 참여하기")
            info = font_small.render("LAN에서 방을 찾는 중... (안 보이면 AP isolation/방화벽 가능)", True, (180, 180, 180))
            screen.blit(info, (30, 70))

            if not rooms:
                empty = font.render("발견된 방이 없습니다. [새로고침]을 눌러 다시 탐색하세요.", True, (220, 220, 220))
                screen.blit(empty, (60, 140))

            for r, b in room_buttons:
                b.draw(screen)

            btn_refresh.draw(screen)
            btn_back2.draw(screen)

        elif state == "settings":
            draw_title(screen, font_title, "설정")
            t = font.render("설정은 다음 단계에서 추가합니다. (ESC로 뒤로)", True, (220, 220, 220))
            screen.blit(t, (30, 120))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

# # main.py
# import pygame
# from game import Game

# def main():
#     pygame.init()
#     screen = pygame.display.set_mode((900, 600))
#     pygame.display.set_caption("2D Racing")
#     clock = pygame.time.Clock()

#     game = Game(screen, clock)
#     game.run()

#     pygame.quit()

# if __name__ == "__main__":
#     main()
