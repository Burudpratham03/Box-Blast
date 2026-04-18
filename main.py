import math
import random
import sys

import cv2
import mediapipe as mp
import numpy as np
import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

UI_PANEL_WIDTH = 240
PLAYFIELD_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH

PLAYFIELD_RECT = pygame.Rect(0, 0, PLAYFIELD_WIDTH, SCREEN_HEIGHT)
HUD_RECT = pygame.Rect(PLAYFIELD_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
CAMERA_RECT = pygame.Rect(PLAYFIELD_WIDTH + 22, 262, UI_PANEL_WIDTH - 44, 148)

PADDLE_WIDTH = 140
PADDLE_HEIGHT = 16
PADDLE_Y = SCREEN_HEIGHT - 60

BALL_RADIUS = 10
BALL_SPEED = 7.0

BOX_GAP = 6
BOX_TOP_OFFSET = 88
MAX_HEALTH_CAP = 21

BG_TOP = (8, 10, 20)
BG_BOTTOM = (14, 18, 34)
HUD_BG_TOP = (16, 20, 34)
HUD_BG_BOTTOM = (10, 13, 26)
AETHER_CYAN = (67, 232, 255)
AETHER_MINT = (86, 255, 190)
AETHER_AMBER = (255, 178, 96)
WHITE = (238, 245, 255)
RED = (255, 93, 112)

STAR_COUNT = 42


class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.rect.centerx = PLAYFIELD_WIDTH // 2
        self.rect.y = PADDLE_Y

    def update_from_normalized_x(self, x_norm: float) -> None:
        target_x = int(max(0.0, min(1.0, x_norm)) * PLAYFIELD_WIDTH)
        self.rect.centerx = target_x
        self.rect.clamp_ip(PLAYFIELD_RECT)

    def update_from_keyboard(self, keys) -> None:
        speed = 9
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += speed
        self.rect.clamp_ip(PLAYFIELD_RECT)

    def draw(self, surface: pygame.Surface, frame_tick: int) -> None:
        pulse = 0.5 + 0.5 * math.sin(frame_tick * 0.11)
        glow_rect = self.rect.inflate(26, 14)
        glow_color = (26, int(120 + 80 * pulse), int(165 + 70 * pulse))
        pygame.draw.rect(surface, glow_color, glow_rect, border_radius=12)

        body_color = (18, 48, 86)
        pygame.draw.rect(surface, body_color, self.rect, border_radius=8)

        segment_count = 6
        segment_gap = 3
        seg_width = (self.rect.width - segment_gap *
                     (segment_count + 1)) // segment_count
        for i in range(segment_count):
            seg_x = self.rect.x + segment_gap + i * (seg_width + segment_gap)
            seg_rect = pygame.Rect(
                seg_x, self.rect.y + 3, seg_width, self.rect.height - 6)
            shade = int(120 + i * 14 + 35 * pulse)
            pygame.draw.rect(surface, (30, shade, 210),
                             seg_rect, border_radius=4)

        pygame.draw.line(
            surface,
            (180, 245, 255),
            (self.rect.left + 6, self.rect.top + 3),
            (self.rect.right - 6, self.rect.top + 3),
            2,
        )


class Ball:
    def __init__(self):
        self.radius = BALL_RADIUS
        self.vx = BALL_SPEED * random.choice([-1, 1])
        self.vy = -BALL_SPEED
        self.stuck = True
        self.x = PLAYFIELD_WIDTH / 2
        self.y = PADDLE_Y - BALL_RADIUS - 2
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        self._sync_rect()

    def _sync_rect(self) -> None:
        self.rect.center = (int(self.x), int(self.y))

    def reset_on_paddle(self, paddle: Paddle) -> None:
        self.stuck = True
        self.vx = BALL_SPEED * random.choice([-1, 1])
        self.vy = -BALL_SPEED
        self.x = float(paddle.rect.centerx)
        self.y = float(paddle.rect.top - self.radius - 2)
        self._sync_rect()

    def throw(self) -> None:
        if self.stuck:
            self.stuck = False
            self.vx = BALL_SPEED * random.choice([-1, 1])
            self.vy = -BALL_SPEED

    def update(self, paddle: Paddle) -> bool:
        if self.stuck:
            self.x = float(paddle.rect.centerx)
            self.y = float(paddle.rect.top - self.radius - 2)
            self._sync_rect()
            return False

        self.x += self.vx
        self.y += self.vy

        if self.x - self.radius <= 0:
            self.x = float(self.radius)
            self.vx *= -1
        elif self.x + self.radius >= PLAYFIELD_WIDTH:
            self.x = float(PLAYFIELD_WIDTH - self.radius)
            self.vx *= -1

        if self.y - self.radius <= 0:
            self.y = float(self.radius)
            self.vy *= -1

        self._sync_rect()

        if self.rect.colliderect(paddle.rect) and self.vy > 0:
            hit_ratio = (self.x - paddle.rect.centerx) / \
                (paddle.rect.width / 2)
            hit_ratio = max(-1.0, min(1.0, hit_ratio))
            angle = hit_ratio * math.radians(60)
            speed = max(BALL_SPEED, math.hypot(self.vx, self.vy))
            self.vx = speed * math.sin(angle)
            self.vy = -abs(speed * math.cos(angle))
            self.y = float(paddle.rect.top - self.radius - 1)
            self._sync_rect()

        if self.rect.top > SCREEN_HEIGHT:
            return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        speed = max(1.0, math.hypot(self.vx, self.vy))
        tail_dx = -self.vx / speed
        tail_dy = -self.vy / speed

        for i in range(1, 5):
            center = (
                int(self.x + tail_dx * i * 6),
                int(self.y + tail_dy * i * 6),
            )
            tail_radius = max(2, self.radius - i * 2)
            tail_color = (40, 120 + i * 20, 180 + i * 10)
            pygame.draw.circle(surface, tail_color, center, tail_radius)

        pygame.draw.circle(surface, (130, 255, 245),
                           self.rect.center, self.radius + 4)
        pygame.draw.circle(surface, WHITE, self.rect.center, self.radius)


class Box:
    def __init__(self, x: int, y: int, box_width: int, box_height: int, health: int):
        self.rect = pygame.Rect(x, y, box_width, box_height)
        self.health = health

    def color(self) -> tuple[int, int, int]:
        t = min(1.0, max(0.0, (self.health - 1) / (MAX_HEALTH_CAP - 1)))
        r = int(90 + 165 * t)
        g = int(235 - 120 * t)
        b = int(255 - 185 * t)
        return r, g, b

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, frame_tick: int) -> None:
        c = self.color()
        pulse = 0.5 + 0.5 * math.sin(frame_tick * 0.08 + self.rect.x * 0.03)

        glow = self.rect.inflate(8, 8)
        glow_color = (
            min(255, c[0] + int(20 * pulse)),
            min(255, c[1] + int(24 * pulse)),
            min(255, c[2] + int(24 * pulse)),
        )
        pygame.draw.rect(surface, glow_color, glow, border_radius=8)

        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        highlight = pygame.Rect(
            self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 6)
        pygame.draw.rect(surface, (220, 246, 255), highlight, border_radius=3)
        pygame.draw.rect(surface, (255, 255, 255),
                         self.rect, width=1, border_radius=6)

        hp_text = font.render(str(self.health), True, (6, 10, 26))
        hp_rect = hp_text.get_rect(center=self.rect.center)
        surface.blit(hp_text, hp_rect)


class HandTracker:
    def __init__(self):
        self.init_error = None
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.available = self.capture.isOpened()

        self.mp_hands = None
        self.mp_draw = None
        self.hands = None

        try:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            self.hands = self.mp_hands.Hands(
                max_num_hands=1,
                min_detection_confidence=0.6,
                min_tracking_confidence=0.5,
            )
        except Exception as exc:
            self.available = False
            self.init_error = str(exc)

    def read(self) -> tuple[float | None, bool, np.ndarray | None]:
        if not self.available:
            return None, False, None

        ok, frame = self.capture.read()
        if not ok:
            return None, False, None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        palm_x = None
        pinch = False

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            self.mp_draw.draw_landmarks(
                frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

            points = hand_landmarks.landmark
            palm_x = points[0].x

            thumb = points[4]
            index_tip = points[8]
            pinch_distance = math.hypot(
                thumb.x - index_tip.x, thumb.y - index_tip.y)
            pinch = pinch_distance < 0.05

        return palm_x, pinch, frame

    def release(self) -> None:
        if self.available:
            self.capture.release()
        if self.hands is not None:
            self.hands.close()


def generate_level(level_number: int) -> list[Box]:
    boxes = []
    max_health = min(MAX_HEALTH_CAP, 4 + level_number * 2)

    # L1 starts lighter (12 boxes) and ramps with level.
    rows = min(6, 2 + level_number // 2)
    cols = min(9, 6 + (level_number - 1) // 2)

    horizontal_padding = 24
    total_gap = BOX_GAP * (cols - 1)
    available_width = PLAYFIELD_WIDTH - horizontal_padding * 2
    box_width = (available_width - total_gap) // cols
    box_height = 28
    x_start = horizontal_padding

    for row in range(rows):
        for col in range(cols):
            x = x_start + col * (box_width + BOX_GAP)
            y = BOX_TOP_OFFSET + row * (box_height + BOX_GAP)
            health = random.randint(1, max_health)
            boxes.append(Box(x, y, box_width, box_height, health))

    return boxes


def resolve_collision(ball: Ball, box: Box) -> None:
    overlap_left = ball.rect.right - box.rect.left
    overlap_right = box.rect.right - ball.rect.left
    overlap_top = ball.rect.bottom - box.rect.top
    overlap_bottom = box.rect.bottom - ball.rect.top

    min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

    if min_overlap in (overlap_left, overlap_right):
        ball.vx *= -1
    else:
        ball.vy *= -1


def create_background() -> pygame.Surface:
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    for y in range(SCREEN_HEIGHT):
        t = y / max(1, SCREEN_HEIGHT - 1)
        r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
        g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
        b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (PLAYFIELD_WIDTH, y))

    for y in range(SCREEN_HEIGHT):
        t = y / max(1, SCREEN_HEIGHT - 1)
        r = int(HUD_BG_TOP[0] * (1 - t) + HUD_BG_BOTTOM[0] * t)
        g = int(HUD_BG_TOP[1] * (1 - t) + HUD_BG_BOTTOM[1] * t)
        b = int(HUD_BG_TOP[2] * (1 - t) + HUD_BG_BOTTOM[2] * t)
        pygame.draw.line(bg, (r, g, b), (PLAYFIELD_WIDTH, y),
                         (SCREEN_WIDTH, y))

    haze = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(haze, (38, 92, 160, 48), (120, 130), 160)
    pygame.draw.circle(haze, (24, 140, 170, 42),
                       (PLAYFIELD_WIDTH - 90, 210), 130)
    pygame.draw.circle(haze, (90, 78, 170, 35), (220, SCREEN_HEIGHT - 70), 180)
    bg.blit(haze, (0, 0))

    return bg


def create_starfield() -> list[tuple[float, float, int, float, float]]:
    stars = []
    for _ in range(STAR_COUNT):
        x = random.uniform(20, PLAYFIELD_WIDTH - 20)
        y = random.uniform(20, SCREEN_HEIGHT - 30)
        size = random.randint(1, 2)
        speed = random.uniform(0.08, 0.45)
        phase = random.uniform(0, math.tau)
        stars.append((x, y, size, speed, phase))
    return stars


def draw_playfield_fx(surface: pygame.Surface, stars: list[tuple[float, float, int, float, float]], frame_tick: int) -> None:
    fx = pygame.Surface((PLAYFIELD_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    for x, y, size, speed, phase in stars:
        y_anim = (y + frame_tick * speed) % SCREEN_HEIGHT
        twinkle = 0.5 + 0.5 * math.sin(frame_tick * 0.08 + phase)
        brightness = int(120 + 110 * twinkle)
        star_color = (brightness, min(255, brightness + 30), 255, 170)
        pygame.draw.circle(fx, star_color, (int(x), int(y_anim)), size)

    sweep_offset = (frame_tick * 2) % 120
    for i in range(-220, PLAYFIELD_WIDTH + 220, 120):
        pygame.draw.line(
            fx,
            (80, 180, 255, 25),
            (i + sweep_offset, 0),
            (i - 120 + sweep_offset, SCREEN_HEIGHT),
            1,
        )

    for x in range(0, PLAYFIELD_WIDTH, 56):
        pygame.draw.line(fx, (100, 160, 255, 18),
                         (x, 0), (x, SCREEN_HEIGHT), 1)

    surface.blit(fx, (0, 0))


def draw_heart(surface: pygame.Surface, center_x: int, center_y: int, color: tuple[int, int, int]) -> None:
    pygame.draw.circle(surface, color, (center_x - 5, center_y - 3), 5)
    pygame.draw.circle(surface, color, (center_x + 5, center_y - 3), 5)
    pygame.draw.polygon(
        surface,
        color,
        [
            (center_x - 10, center_y),
            (center_x + 10, center_y),
            (center_x, center_y + 12),
        ],
    )


def draw_lives(surface: pygame.Surface, lives: int, font: pygame.font.Font, x: int, y: int) -> None:
    label = font.render("Lives", True, (200, 220, 255))
    surface.blit(label, (x, y))

    for i in range(3):
        cx = x + 64 + i * 28
        cy = y + 13
        if i < lives:
            draw_heart(surface, cx, cy, RED)
        else:
            draw_heart(surface, cx, cy, (76, 84, 108))


def camera_to_surface(frame_bgr: np.ndarray, camera_width: int, camera_height: int) -> pygame.Surface:
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.resize(
        frame_rgb, (camera_width, camera_height), interpolation=cv2.INTER_AREA)
    frame_rgb = np.rot90(frame_rgb)
    return pygame.surfarray.make_surface(frame_rgb)


def draw_card(surface: pygame.Surface, rect: pygame.Rect, title: str, title_font: pygame.font.Font) -> None:
    shadow = rect.move(0, 2)
    pygame.draw.rect(surface, (6, 8, 16), shadow, border_radius=12)
    pygame.draw.rect(surface, (20, 28, 48), rect, border_radius=12)
    pygame.draw.rect(surface, (80, 140, 220), rect, 1, border_radius=12)

    title_text = title_font.render(title, True, (180, 230, 255))
    surface.blit(title_text, (rect.x + 10, rect.y + 8))


def draw_hud(
    surface: pygame.Surface,
    level: int,
    lives: int,
    boxes_remaining: int,
    total_boxes: int,
    pinch: bool,
    hand_x: float | None,
    combo_count: int,
    cam_frame: np.ndarray | None,
    tracker: HandTracker,
    title_font: pygame.font.Font,
    info_font: pygame.font.Font,
    frame_tick: int,
) -> None:
    pulse = 0.5 + 0.5 * math.sin(frame_tick * 0.09)

    pygame.draw.line(
        surface,
        (80, int(180 + 60 * pulse), 255),
        (PLAYFIELD_WIDTH, 0),
        (PLAYFIELD_WIDTH, SCREEN_HEIGHT),
        2,
    )

    stats_rect = pygame.Rect(HUD_RECT.x + 12, 12, HUD_RECT.width - 24, 132)
    gesture_rect = pygame.Rect(HUD_RECT.x + 12, 154, HUD_RECT.width - 24, 98)
    camera_card = CAMERA_RECT.inflate(18, 44)

    draw_card(surface, stats_rect, "AETHER CORE", title_font)
    draw_card(surface, gesture_rect, "GESTURE LINK", title_font)
    draw_card(surface, camera_card, "VISION FEED", title_font)

    level_text = info_font.render(f"Level {level}", True, WHITE)
    surface.blit(level_text, (stats_rect.x + 12, stats_rect.y + 36))
    draw_lives(surface, lives, info_font, stats_rect.x + 12, stats_rect.y + 58)

    progress_bg = pygame.Rect(
        stats_rect.x + 12, stats_rect.y + 96, stats_rect.width - 24, 12)
    pygame.draw.rect(surface, (40, 50, 76), progress_bg, border_radius=6)
    progress = 1.0 - (boxes_remaining / max(1, total_boxes))
    fill_w = max(0, int(progress_bg.width * progress))
    progress_fill = pygame.Rect(
        progress_bg.x, progress_bg.y, fill_w, progress_bg.height)
    pygame.draw.rect(surface, (74, 224, 255), progress_fill, border_radius=6)

    pinch_color = AETHER_MINT if pinch else (92, 108, 130)
    pinch_radius = 7 + int(2 * pulse) if pinch else 7
    pygame.draw.circle(surface, pinch_color, (gesture_rect.x +
                       20, gesture_rect.y + 45), pinch_radius)
    pinch_text = info_font.render(
        "Pinch armed" if pinch else "Pinch idle", True, WHITE)
    surface.blit(pinch_text, (gesture_rect.x + 34, gesture_rect.y + 36))

    meter_rect = pygame.Rect(
        gesture_rect.x + 12, gesture_rect.y + 66, gesture_rect.width - 24, 10)
    pygame.draw.rect(surface, (38, 44, 68), meter_rect, border_radius=5)
    hand_fill = int(meter_rect.width *
                    (0.0 if hand_x is None else max(0.0, min(1.0, hand_x))))
    pygame.draw.rect(
        surface,
        (AETHER_AMBER[0], AETHER_AMBER[1], min(255, AETHER_AMBER[2] + 30)),
        pygame.Rect(meter_rect.x, meter_rect.y, hand_fill, meter_rect.height),
        border_radius=5,
    )

    combo_text = info_font.render(
        f"Combo x{max(1, combo_count)}", True, AETHER_AMBER)
    surface.blit(combo_text, (gesture_rect.x + 12, gesture_rect.y + 12))

    pygame.draw.rect(surface, (16, 20, 34), CAMERA_RECT)
    pygame.draw.rect(surface, (90, int(180 + 60 * pulse), 255),
                     CAMERA_RECT, 2, border_radius=8)

    if cam_frame is not None:
        cam_surface = camera_to_surface(
            cam_frame, CAMERA_RECT.width, CAMERA_RECT.height)
        surface.blit(cam_surface, CAMERA_RECT.topleft)

        scan = pygame.Surface(
            (CAMERA_RECT.width, CAMERA_RECT.height), pygame.SRCALPHA)
        for y in range(0, CAMERA_RECT.height, 4):
            pygame.draw.line(scan, (8, 12, 22, 45), (0, y),
                             (CAMERA_RECT.width, y), 1)
        surface.blit(scan, CAMERA_RECT.topleft)
    else:
        cam_off = info_font.render("Camera offline", True, (180, 190, 205))
        surface.blit(
            cam_off,
            (CAMERA_RECT.x + (CAMERA_RECT.width - cam_off.get_width()) //
             2, CAMERA_RECT.y + CAMERA_RECT.height // 2 - 8),
        )

    if not tracker.available:
        warning_text = "MediaPipe unavailable" if tracker.init_error else "Camera unavailable"
        warning = info_font.render(warning_text, True, (255, 188, 110))
        surface.blit(warning, (camera_card.x + 12, camera_card.bottom - 24))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Box Blast - Aether Grid")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("bahnschrift", 19, bold=True)
    hp_font = pygame.font.SysFont("consolas", 18, bold=True)
    info_font = pygame.font.SysFont("consolas", 18)

    background = create_background()
    stars = create_starfield()
    trail_surface = pygame.Surface(
        (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

    paddle = Paddle()
    ball = Ball()

    level = 1
    lives = 3
    boxes = generate_level(level)
    level_box_total = len(boxes)

    tracker = HandTracker()
    prev_pinch = False

    combo_count = 0
    combo_timer = 0
    frame_tick = 0

    running = True
    while running:
        clock.tick(FPS)
        frame_tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()

        hand_x, pinch, cam_frame = tracker.read()
        if hand_x is not None:
            paddle.update_from_normalized_x(hand_x)
        else:
            paddle.update_from_keyboard(keys)

        if (pinch and not prev_pinch) or keys[pygame.K_SPACE]:
            ball.throw()
        prev_pinch = pinch

        lost_life = ball.update(paddle)
        if lost_life:
            lives -= 1
            combo_count = 0
            combo_timer = 0
            if lives <= 0:
                lives = 3
                level = 1
                boxes = generate_level(level)
                level_box_total = len(boxes)
            ball.reset_on_paddle(paddle)

        hit_box = False
        for box in boxes[:]:
            if ball.rect.colliderect(box.rect):
                resolve_collision(ball, box)
                box.health -= 1
                hit_box = True
                if box.health <= 0:
                    boxes.remove(box)
                break

        if hit_box:
            combo_count += 1
            combo_timer = FPS * 2

        if combo_timer > 0:
            combo_timer -= 1
        else:
            combo_count = 0

        if not boxes:
            level += 1
            boxes = generate_level(level)
            level_box_total = len(boxes)
            combo_count = 0
            combo_timer = 0
            ball.reset_on_paddle(paddle)

        trail_surface.fill((245, 245, 245, 232),
                           special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.circle(trail_surface, (106, 255, 240, 78),
                           ball.rect.center, ball.radius + 5)

        screen.blit(background, (0, 0))
        draw_playfield_fx(screen, stars, frame_tick)
        screen.blit(trail_surface, (0, 0))

        for box in boxes:
            box.draw(screen, hp_font, frame_tick)

        pygame.draw.rect(screen, (80, 190, 255), PLAYFIELD_RECT, 2)

        paddle.draw(screen, frame_tick)
        ball.draw(screen)

        if ball.stuck:
            hint = info_font.render(
                "Pinch thumb + index to launch", True, AETHER_CYAN)
            hint_rect = hint.get_rect(
                center=(PLAYFIELD_WIDTH // 2, SCREEN_HEIGHT - 22))
            screen.blit(hint, hint_rect)

        draw_hud(
            screen,
            level,
            lives,
            len(boxes),
            level_box_total,
            pinch,
            hand_x,
            combo_count,
            cam_frame,
            tracker,
            title_font,
            info_font,
            frame_tick,
        )

        pygame.display.flip()

    tracker.release()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
