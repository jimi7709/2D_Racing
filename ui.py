# ui.py
import pygame

class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.enabled = True

    def draw(self, screen):
        bg = (70, 70, 70) if self.enabled else (40, 40, 40)
        pygame.draw.rect(screen, bg, self.rect, border_radius=10)
        pygame.draw.rect(screen, (120, 120, 120), self.rect, 2, border_radius=10)
        surf = self.font.render(self.text, True, (230, 230, 230))
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class TextInput:
    def __init__(self, rect, font, text="", placeholder=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = text
        self.placeholder = placeholder
        self.active = False

    def draw(self, screen):
        pygame.draw.rect(screen, (30, 30, 30), self.rect, border_radius=8)
        pygame.draw.rect(screen, (120, 120, 120), self.rect, 2, border_radius=8)
        show = self.text if self.text else self.placeholder
        color = (230, 230, 230) if self.text else (140, 140, 140)
        surf = self.font.render(show, True, color)
        screen.blit(surf, (self.rect.x + 10, self.rect.y + 10))
        if self.active:
            cx = self.rect.x + 10 + surf.get_width() + 2
            cy = self.rect.y + 10
            pygame.draw.line(screen, (230, 230, 230), (cx, cy), (cx, cy + surf.get_height()), 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 18 and event.unicode.isprintable():
                    self.text += event.unicode

def draw_title(screen, font, title):
    surf = font.render(title, True, (240, 240, 240))
    screen.blit(surf, (30, 25))

def draw_label(screen, font, text, x, y):
    surf = font.render(text, True, (220, 220, 220))
    screen.blit(surf, (x, y))
