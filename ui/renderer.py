import pygame
import math
import time
from typing import Tuple, List, Dict
from engine.game import GameEngine

# ─────────────────────────────────────────────────────────────────────────────
# Premium Minesweeper Renderer
# ─────────────────────────────────────────────────────────────────────────────

class Renderer:
    # ── Palette ──────────────────────────────────────────────────────────────
    # Background & panels
    BG_TOP          = (8,  10,  20)
    BG_BOT          = (14, 18,  36)
    HUD_COLOR       = (12, 14,  26)
    HUD_BORDER      = (40, 50,  90)
    PANEL_COLOR     = (18, 22,  40)

    # Cells
    CELL_TOP        = (52, 62,  94)   # unrevealed highlight
    CELL_MID        = (38, 46,  74)   # unrevealed base
    CELL_BOT        = (24, 30,  52)   # unrevealed shadow
    REVEALED_COL    = (20, 24,  40)   # revealed bg
    REVEALED_BORDER = (30, 38,  60)

    # Accent
    MINE_COL        = (255, 60,  60)
    FLAG_COL        = (255, 165,  50)
    ACCENT_BLUE     = (80, 160, 255)
    ACCENT_GREEN    = (60, 220, 140)
    ACCENT_RED      = (255, 80,  80)

    # Number palette (1-8)
    NUMBER_COLORS = {
        1: (80,  180, 255),
        2: (60,  220, 120),
        3: (255, 90,  80),
        4: (160, 80,  255),
        5: (255, 180, 60),
        6: (60,  220, 220),
        7: (255, 80,  200),
        8: (200, 200, 200),
    }

    def __init__(self, cell_size: int = 32):
        pygame.init()
        self.cell_size = cell_size
        self.ui_height = 80

        # Fonts — fallback to SysFont if no system font
        def sf(name, size, bold=False):
            return pygame.font.SysFont(name, size, bold=bold)

        self.font_big   = sf('Segoe UI', 22, bold=True)
        self.font_med   = sf('Segoe UI', 15, bold=True)
        self.font_small = sf('Segoe UI', 11)
        self.font_num   = sf('Segoe UI', int(cell_size * 0.55), bold=True)
        self.font_prob  = sf('Segoe UI', max(8, int(cell_size * 0.28)))
        self.font_huge  = sf('Segoe UI', 40, bold=True)
        self.font_sub   = sf('Segoe UI', 18)

        self._start_time: float = time.time()
        self._elapsed_frozen: float | None = None
        self._hover_cell: Tuple[int, int] | None = None

        # Pre-build gradient background surface (will be rebuilt on resize)
        self._bg_surf: pygame.Surface | None = None
        self._bg_size: Tuple[int, int] = (0, 0)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def reset_timer(self):
        self._start_time = time.time()
        self._elapsed_frozen = None

    def freeze_timer(self):
        if self._elapsed_frozen is None:
            self._elapsed_frozen = time.time() - self._start_time

    def elapsed_seconds(self) -> int:
        if self._elapsed_frozen is not None:
            return int(self._elapsed_frozen)
        return int(time.time() - self._start_time)

    def _lerp_color(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def _make_gradient(self, w: int, h: int) -> pygame.Surface:
        surf = pygame.Surface((w, h))
        for y in range(h):
            t = y / max(h - 1, 1)
            col = self._lerp_color(self.BG_TOP, self.BG_BOT, t)
            pygame.draw.line(surf, col, (0, y), (w, y))
        return surf

    def _draw_rounded_rect(self, surface, color, rect, radius=6, border_color=None, border_width=1):
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        if border_color:
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

    def _blit_centered(self, surface, text_surf, rect):
        surface.blit(text_surf, text_surf.get_rect(center=rect.center))

    def _glow_text(self, surface, text, font, color, pos, glow_radius=2):
        """Draw text with a subtle soft glow."""
        gr, gg, gb = max(0, color[0] - 80), max(0, color[1] - 80), max(0, color[2] - 80)
        glow_col = (gr, gg, gb)
        glow = font.render(text, True, glow_col)
        for dx in range(-glow_radius, glow_radius + 1):
            for dy in range(-glow_radius, glow_radius + 1):
                if dx == 0 and dy == 0:
                    continue
                surface.blit(glow, (pos[0] + dx, pos[1] + dy))
        txt = font.render(text, True, color)
        surface.blit(txt, pos)

    # ── Window sizing ─────────────────────────────────────────────────────────

    def get_window_size(self, game: GameEngine) -> Tuple[int, int]:
        if game.shape == 'square':
            w = max(620, game.cols * self.cell_size)
            h = game.rows * self.cell_size + self.ui_height
        else:  # hexagon
            w = int(game.cols * self.cell_size * 1.5 + self.cell_size * 0.5)
            h = int(game.rows * self.cell_size * math.sqrt(3) + self.cell_size * math.sqrt(3))
            w, h = max(620, w), h + self.ui_height
        return (w, h)

    # ── Cell geometry ─────────────────────────────────────────────────────────

    def _cell_rect(self, r: int, c: int) -> pygame.Rect:
        return pygame.Rect(c * self.cell_size, r * self.cell_size + self.ui_height,
                           self.cell_size, self.cell_size)

    def get_hex_center(self, r: int, c: int) -> Tuple[float, float]:
        s = self.cell_size
        x = s * 1.5 * c + s
        y = s * math.sqrt(3) * (r + 0.5 * (c % 2)) + s * math.sqrt(3) / 2 + self.ui_height
        return (x, y)

    def _hex_points(self, cx: float, cy: float, size: float = None) -> List[Tuple[float, float]]:
        s = size if size is not None else self.cell_size
        return [(cx + s * math.cos(math.radians(60 * i)),
                 cy + s * math.sin(math.radians(60 * i))) for i in range(6)]

    # ── Beveled cell drawing ──────────────────────────────────────────────────

    def _draw_unrevealed_square(self, surface, rect: pygame.Rect, hovered: bool = False):
        cs = self.cell_size
        pad = 2

        # Base fill with subtle gradient simulation (lighter top, darker bottom)
        top_col = self.CELL_TOP if not hovered else (70, 82, 120)
        bot_col = self.CELL_BOT if not hovered else (30, 38, 70)
        inner = pygame.Rect(rect.x + pad, rect.y + pad, rect.w - pad*2, rect.h - pad*2)
        for y_off in range(inner.height):
            t = y_off / max(inner.height - 1, 1)
            col = self._lerp_color(top_col, bot_col, t)
            pygame.draw.line(surface, col, (inner.x, inner.y + y_off), (inner.right, inner.y + y_off))

        # Top/left highlight edge
        hl = (90, 105, 150) if not hovered else (110, 130, 180)
        pygame.draw.line(surface, hl, rect.topleft, (rect.right - 1, rect.top))
        pygame.draw.line(surface, hl, rect.topleft, (rect.left, rect.bottom - 1))
        # Bottom/right shadow edge
        sh = (15, 18, 32)
        pygame.draw.line(surface, sh, (rect.left, rect.bottom - 1), (rect.right - 1, rect.bottom - 1))
        pygame.draw.line(surface, sh, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1))

    def _draw_revealed_square(self, surface, rect: pygame.Rect):
        pygame.draw.rect(surface, self.REVEALED_COL, rect)
        pygame.draw.rect(surface, self.REVEALED_BORDER, rect, 1)

    def _draw_mine_square(self, surface, rect: pygame.Rect):
        pygame.draw.rect(surface, (60, 12, 12), rect)
        # Red pulsing disc
        cx, cy = rect.center
        r = int(self.cell_size * 0.28)
        pygame.draw.circle(surface, self.MINE_COL, (cx, cy), r)
        # Spikes
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x1 = cx + r * math.cos(rad)
            y1 = cy + r * math.sin(rad)
            x2 = cx + (r + 4) * math.cos(rad)
            y2 = cy + (r + 4) * math.sin(rad)
            pygame.draw.line(surface, self.MINE_COL, (int(x1), int(y1)), (int(x2), int(y2)), 2)
        # Inner shine dot
        pygame.draw.circle(surface, (255, 200, 200), (cx - r // 3, cy - r // 3), max(2, r // 3))
        pygame.draw.rect(surface, (120, 20, 20), rect, 1)

    def _draw_flag_icon(self, surface, cx: int, cy: int):
        cs = self.cell_size
        # Pole
        pole_x = cx - cs // 10
        pygame.draw.line(surface, (210, 210, 210),
                         (pole_x, cy + cs // 4),
                         (pole_x, cy - cs // 3), 2)
        # Flag triangle
        tip     = (pole_x, cy - cs // 3)
        bottom  = (pole_x, cy - cs // 12)
        right   = (pole_x + cs // 3, (tip[1] + bottom[1]) // 2)
        pygame.draw.polygon(surface, self.FLAG_COL, [tip, bottom, right])
        # Base
        base_w = cs // 3
        pygame.draw.line(surface, (210, 210, 210),
                         (cx - base_w // 2, cy + cs // 4),
                         (cx + base_w // 2, cy + cs // 4), 2)

    # ── Probability overlay ───────────────────────────────────────────────────

    def _draw_prob_overlay_square(self, surface, rect, prob):
        # Gradient heat: transparent blue (safe) → red (danger)
        r = int(220 * prob)
        g = int(180 * (1 - prob) * 0.4)
        b = int(220 * (1 - prob))
        alpha = 160
        overlay = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        overlay.fill((r, g, b, alpha))
        surface.blit(overlay, rect.topleft)

        # Label
        pct = f"{prob * 100:.0f}%"
        txt = self.font_prob.render(pct, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))

    def _draw_prob_overlay_hex(self, surface, cx, cy, prob):
        r = int(220 * prob)
        g = int(180 * (1 - prob) * 0.4)
        b = int(220 * (1 - prob))
        alpha = 150
        s = self.cell_size
        overlay = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pts = self._hex_points(s, s)
        pygame.draw.polygon(overlay, (r, g, b, alpha), pts)
        surface.blit(overlay, (cx - s, cy - s))
        pct = f"{prob * 100:.0f}%"
        txt = self.font_prob.render(pct, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=(cx, cy)))

    # ── Square grid ───────────────────────────────────────────────────────────

    def draw_square_grid(self, surface, game: GameEngine,
                         probabilities: Dict, show_probs: bool):
        hover = self._hover_cell
        for r in range(game.rows):
            for c in range(game.cols):
                cell = game.cells[(r, c)]
                rect = self._cell_rect(r, c)
                hovered = (hover == (r, c))

                if cell.is_revealed:
                    if cell.is_mine:
                        self._draw_mine_square(surface, rect)
                    else:
                        self._draw_revealed_square(surface, rect)
                        if cell.neighbor_mines > 0:
                            col = self.NUMBER_COLORS.get(cell.neighbor_mines, (255, 255, 255))
                            txt = self.font_num.render(str(cell.neighbor_mines), True, col)
                            self._blit_centered(surface, txt, rect)
                else:
                    self._draw_unrevealed_square(surface, rect, hovered)
                    if cell.is_flagged:
                        self._draw_flag_icon(surface, rect.centerx, rect.centery)
                    elif show_probs and (r, c) in probabilities:
                        self._draw_prob_overlay_square(surface, rect, probabilities[(r, c)])

    # ── Hex grid ──────────────────────────────────────────────────────────────

    def draw_hex_grid(self, surface, game: GameEngine,
                      probabilities: Dict, show_probs: bool):
        s = self.cell_size
        hover = self._hover_cell

        for r in range(game.rows):
            for c in range(game.cols):
                cell = game.cells[(r, c)]
                cx, cy = self.get_hex_center(r, c)
                pts = self._hex_points(cx, cy)
                inner_pts = self._hex_points(cx, cy, s - 2)

                is_hover = (hover == (r, c))

                if cell.is_revealed:
                    if cell.is_mine:
                        pygame.draw.polygon(surface, (50, 10, 10), pts)
                        pygame.draw.polygon(surface, (100, 20, 20), pts, 2)
                        # Mine disc
                        pygame.draw.circle(surface, self.MINE_COL, (int(cx), int(cy)), int(s * 0.28))
                        pygame.draw.circle(surface, (255, 200, 200),
                                           (int(cx - s * 0.08), int(cy - s * 0.1)),
                                           max(2, int(s * 0.08)))
                    else:
                        pygame.draw.polygon(surface, self.REVEALED_COL, pts)
                        pygame.draw.polygon(surface, self.REVEALED_BORDER, pts, 1)
                        if cell.neighbor_mines > 0:
                            col = self.NUMBER_COLORS.get(cell.neighbor_mines, (255, 255, 255))
                            txt = self.font_num.render(str(cell.neighbor_mines), True, col)
                            surface.blit(txt, txt.get_rect(center=(cx, cy)))
                else:
                    # Gradient fill
                    top_c = (70, 82, 120) if is_hover else (52, 62, 94)
                    bot_c = (28, 34, 58) if is_hover else (24, 30, 52)
                    # Fill with mid color then draw inner polygon for pseudo-gradient
                    mid_c = self._lerp_color(top_c, bot_c, 0.5)
                    pygame.draw.polygon(surface, mid_c, pts)
                    pygame.draw.polygon(surface, top_c, inner_pts)
                    # Border
                    hl_col = (90, 110, 160) if is_hover else (60, 75, 115)
                    pygame.draw.polygon(surface, hl_col, pts, 2)

                    if cell.is_flagged:
                        self._draw_flag_icon(surface, int(cx), int(cy))
                    elif show_probs and (r, c) in probabilities:
                        self._draw_prob_overlay_hex(surface, cx, cy, probabilities[(r, c)])

    # ── HUD ───────────────────────────────────────────────────────────────────

    def draw_ui(self, surface, game: GameEngine, auto_play: bool, show_probs: bool):
        W = surface.get_width()

        # HUD background
        hud_rect = pygame.Rect(0, 0, W, self.ui_height)
        pygame.draw.rect(surface, self.HUD_COLOR, hud_rect)
        pygame.draw.line(surface, self.HUD_BORDER, (0, self.ui_height - 1), (W, self.ui_height - 1), 2)

        # ── Left: Level + shape badge ─────────────────────────────────────────
        badge_text = f"  {game.level.upper()}  ·  {game.shape.upper()}  "
        badge_surf = self.font_med.render(badge_text, True, self.ACCENT_BLUE)
        badge_rect = badge_surf.get_rect(topleft=(16, 12))
        bg_rect = badge_rect.inflate(10, 6)
        bg_rect.topleft = (badge_rect.x - 5, badge_rect.y - 3)
        pygame.draw.rect(surface, (20, 35, 65), bg_rect, border_radius=5)
        pygame.draw.rect(surface, self.ACCENT_BLUE, bg_rect, 1, border_radius=5)
        surface.blit(badge_surf, badge_rect)

        # ── Left: mine counter ────────────────────────────────────────────────
        flags_placed = sum(1 for cell in game.cells.values() if cell.is_flagged)
        remaining = game.total_mines - flags_placed
        mine_str = f"💣  {remaining:03d}"
        # Draw a pill
        mine_surf = self.font_big.render(mine_str, True, (255, 120, 80))
        mine_rect = mine_surf.get_rect(topleft=(16, 42))
        surface.blit(mine_surf, mine_rect)

        # ── Center: status ────────────────────────────────────────────────────
        if game.game_over:
            status_text  = "GAME  OVER"
            status_color = self.ACCENT_RED
        elif game.victory:
            status_text  = "✔  YOU  WIN"
            status_color = self.ACCENT_GREEN
        else:
            status_text  = "MINESWEEPER  AI"
            status_color = (200, 210, 240)

        s_surf = self.font_big.render(status_text, True, status_color)
        s_rect = s_surf.get_rect(center=(W // 2, self.ui_height // 2))
        surface.blit(s_surf, s_rect)

        # ── Right: timer ──────────────────────────────────────────────────────
        secs = self.elapsed_seconds()
        timer_str = f"⏱  {secs:04d}"
        t_surf = self.font_big.render(timer_str, True, (140, 200, 255))
        t_rect = t_surf.get_rect(midright=(W - 130, self.ui_height // 2))
        surface.blit(t_surf, t_rect)

        # ── Restart button ────────────────────────────────────────────────────
        btn_w, btn_h = 90, 32
        self.restart_rect = pygame.Rect(W - btn_w - 12, (self.ui_height - btn_h) // 2, btn_w, btn_h)
        pygame.draw.rect(surface, (30, 50, 90), self.restart_rect, border_radius=8)
        pygame.draw.rect(surface, self.ACCENT_BLUE, self.restart_rect, 1, border_radius=8)
        r_surf = self.font_med.render("↺  Restart", True, (180, 215, 255))
        surface.blit(r_surf, r_surf.get_rect(center=self.restart_rect.center))

        # ── Bottom bar: controls hint (fixed single line) ─────────────────────
        ctrl_y = self.ui_height - 1   # just above grid border, actually below HUD
        # We'll draw a tiny strip BELOW the hud but still above grid
        # controls row inside HUD bottom
        auto_str  = "ON" if auto_play   else "OFF"
        prob_str  = "ON" if show_probs  else "OFF"
        hints = (f"[S] Step  [A] Auto:{auto_str}  [P] Probs:{prob_str}  "
                 f"[R] Reset  [1-4] Diff  [H] Hex  [Q] Square")
        h_surf = self.font_small.render(hints, True, (90, 100, 140))
        # Draw inside hud, clipped to single line at bottom
        surface.blit(h_surf, (16, self.ui_height - 16))

    # ── Overlay screens ───────────────────────────────────────────────────────

    def _draw_overlay_screen(self, surface, title: str, color: Tuple, subtitle: str = ""):
        W, H = surface.get_size()
        # Semi-transparent dark veil
        veil = pygame.Surface((W, H - self.ui_height), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 145))
        surface.blit(veil, (0, self.ui_height))

        # Card
        cw, ch = min(460, W - 40), 190
        cx, cy = W // 2 - cw // 2, self.ui_height + (H - self.ui_height) // 2 - ch // 2
        card_rect = pygame.Rect(cx, cy, cw, ch)
        pygame.draw.rect(surface, (14, 18, 36), card_rect, border_radius=14)
        pygame.draw.rect(surface, color, card_rect, 2, border_radius=14)

        # Title
        t_surf = self.font_huge.render(title, True, color)
        surface.blit(t_surf, t_surf.get_rect(center=(W // 2, cy + 60)))

        # Subtitle
        if subtitle:
            s_surf = self.font_sub.render(subtitle, True, (170, 180, 210))
            surface.blit(s_surf, s_surf.get_rect(center=(W // 2, cy + 110)))

        # Restart hint
        hint = self.font_small.render("Press  R  or click  ↺ Restart  to play again", True, (100, 120, 160))
        surface.blit(hint, hint.get_rect(center=(W // 2, cy + 155)))

    # ── Master draw ───────────────────────────────────────────────────────────

    def draw(self, surface, game: GameEngine, probabilities: Dict,
             auto_play: bool, show_probs: bool):
        W, H = surface.get_size()

        # Gradient background
        if (W, H) != self._bg_size:
            self._bg_surf = self._make_gradient(W, H)
            self._bg_size = (W, H)
        surface.blit(self._bg_surf, (0, 0))

        if game.shape == 'square':
            self.draw_square_grid(surface, game, probabilities, show_probs)
        elif game.shape == 'hexagon':
            self.draw_hex_grid(surface, game, probabilities, show_probs)

        self.draw_ui(surface, game, auto_play, show_probs)

        # Game-over / Victory overlay
        if game.game_over:
            self.freeze_timer()
            self._draw_overlay_screen(surface, "GAME  OVER", self.ACCENT_RED,
                                      "The AI hit a mine  💣")
        elif game.victory:
            self.freeze_timer()
            t = self.elapsed_seconds()
            self._draw_overlay_screen(surface, "YOU  WIN", self.ACCENT_GREEN,
                                      f"Cleared in  {t}s  🎉")

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def set_hover(self, pos: Tuple[int, int], game: GameEngine):
        """Call every frame with current mouse position to enable hover effect."""
        self._hover_cell = self.get_cell_from_mouse(pos, game)

    def get_cell_from_mouse(self, pos, game: GameEngine):
        x, y = pos
        y -= self.ui_height
        if y < 0:
            return None

        if game.shape == 'square':
            c = x // self.cell_size
            r = y // self.cell_size
            if 0 <= r < game.rows and 0 <= c < game.cols:
                return (r, c)

        elif game.shape == 'hexagon':
            best_dist = float('inf')
            best_cell = None
            for r in range(game.rows):
                for c in range(game.cols):
                    cx, cy_hex = self.get_hex_center(r, c)
                    dist = math.hypot(x - cx, y - (cy_hex - self.ui_height))
                    if dist < best_dist:
                        best_dist = dist
                        best_cell = (r, c)
            if best_dist < self.cell_size:
                return best_cell

        return None
