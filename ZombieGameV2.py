# ============================================================
#  Zombie Rival – 2D Side-Scrolling Edition
#  เกม Side-scrolling Zombie Rival ด้วย Python + Pygame
#  OOP + State Machine + Camera + Platformer Physics
# ============================================================

import pygame
import math
import random
import sys
import os
import webbrowser

# ─────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1920, 1080
WINDOW_W, WINDOW_H = 1280, 720

def get_scaled_mouse_pos():
    mx, my = pygame.mouse.get_pos()
    return int(mx * (SCREEN_W / WINDOW_W)), int(my * (SCREEN_H / WINDOW_H))

FPS = 60
TITLE = "Zombie Rival"
GRAVITY = 0.65
JUMP_FORCE = -13.5
GROUND_Y = 860  # default ground level in world coords
WORLD_W = 5000  # total world width

# ── Colors ──
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
RED         = (220, 50, 50)
DARK_RED    = (140, 20, 20)
GREEN       = (50, 200, 80)
DARK_GREEN  = (20, 80, 30)
FOREST_BG   = (12, 30, 18)
LIGHT_GREEN = (100, 220, 130)
BLUE        = (60, 120, 220)
LIGHT_BLUE  = (100, 180, 255)
YELLOW      = (255, 220, 50)
ORANGE      = (255, 140, 30)
PURPLE      = (160, 60, 220)
GRAY        = (120, 120, 120)
DARK_GRAY   = (50, 50, 50)
BROWN       = (120, 80, 40)
DARK_BROWN  = (70, 45, 20)
GOLD        = (255, 200, 0)
CYAN        = (0, 220, 220)
SKY_TOP     = (10, 15, 40)
SKY_BOT     = (25, 45, 60)

# ── Zombie Theme Colors ──
ZOMBIE_RED   = (140, 0, 0)
ZOMBIE_RED_A = (140, 0, 0, 150)
DRY_BLOOD    = (80, 20, 20)
NEON_GREEN   = (57, 255, 20)
GRIM_GRAY    = (40, 40, 45)
RUST_ORANGE  = (183, 65, 14)
VIGNETTE_COL = (10, 5, 5, 120)

DIFFICULTY_SETTINGS = {
    "Easy":   {"hp": 0.6, "dmg": 0.6, "spd": 0.7, "spawn_mult": 0.6, "spawn_delay": 2.0, "label": "ง่าย"},
    "Medium": {"hp": 1.0, "dmg": 1.0, "spd": 1.0, "spawn_mult": 1.0, "spawn_delay": 1.2, "label": "ปกติ"},
    "Hard":   {"hp": 1.8, "dmg": 1.6, "spd": 1.35, "spawn_mult": 1.6, "spawn_delay": 0.7, "label": "ยาก"},
}

# ─────────────────────────────────────────────
#  Utility Functions & Global Volume
# ─────────────────────────────────────────────
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

GLOBAL_BGM_VOL = 0.2
GLOBAL_SFX_VOL = 0.5

def update_bgm_volume():
    try: pygame.mixer.music.set_volume(GLOBAL_BGM_VOL)
    except: pass
    
def update_sfx_volume():
    for s in SOUNDS.values():
        if s: s.set_volume(GLOBAL_SFX_VOL)

def load_image(name, size=None):
    """Try to load image from assets folder; return None on failure."""
    path = os.path.join(ASSET_DIR, name)
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception:
        return None

SOUNDS = {}
def init_sounds():
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        sound_files = {
            "shoot_pistol": "sfx_pistol.wav",
            "shoot_shotgun": "sfx_shotgun.wav",
            "shoot_smg": "sfx_smg.wav",
            "shoot_sniper": "sfx_sniper.wav",
            "zombie_hurt": "sfx_zombie_hurt.wav",
            "zombie_die": "sfx_zombie_die.wav",
            "player_hurt": "sfx_player_hurt.wav",
            "pickup_money": "sfx_money.wav",
            "pickup_exp": "sfx_exp.wav",
            "pickup_weapon": "sfx_weapon.wav",
            "rescue": "sfx_rescue.wav",
            "click": "sfx_click.wav"
        }
        for key, fname in sound_files.items():
            path = os.path.join(ASSET_DIR, fname)
            if os.path.exists(path):
                s = pygame.mixer.Sound(path)
                s.set_volume(GLOBAL_SFX_VOL)
                SOUNDS[key] = s
            else:
                SOUNDS[key] = None
    except Exception:
        pass

    # Background Music
    try:
        bgm_path = os.path.join(ASSET_DIR, "bgm.wav")
        if os.path.exists(bgm_path):
            pygame.mixer.music.load(bgm_path)
            update_bgm_volume()
            pygame.mixer.music.play(-1) # Loop indefinitely
    except Exception:
        pass

def play_sound(name):
    if name in SOUNDS and SOUNDS[name]:
        try:
            SOUNDS[name].play()
        except:
            pass

def dist(ax, ay, bx, by):
    return math.hypot(bx - ax, by - ay)

def normalize(dx, dy):
    length = math.hypot(dx, dy)
    if length == 0:
        return 0.0, 0.0
    return dx / length, dy / length

def draw_bar(surf, x, y, w, h, val, max_val, fg_col, bg_col=DARK_GRAY, border=1):
    pygame.draw.rect(surf, bg_col, (x, y, w, h))
    fill_w = int(w * max(0, val) / max(1, max_val))
    if fill_w > 0:
        pygame.draw.rect(surf, fg_col, (x, y, fill_w, h))
    if border:
        pygame.draw.rect(surf, WHITE, (x, y, w, h), border)

def draw_button(surf, rect, text, font, hovered=False, base_col=(30, 30, 35), hover_col=(60, 60, 70)):
    col = hover_col if hovered else base_col
    # Grungy button
    pygame.draw.rect(surf, col, rect, border_radius=4)
    border_col = RUST_ORANGE if hovered else GRAY
    pygame.draw.rect(surf, border_col, rect, 2, border_radius=4)
    
    # Simple rivet look
    for rx, ry in [(rect.x+5, rect.y+5), (rect.right-7, rect.y+5), (rect.x+5, rect.bottom-7), (rect.right-7, rect.bottom-7)]:
        pygame.draw.circle(surf, DARK_GRAY, (rx, ry), 2)

    draw_text_fit(surf, text, font, WHITE, rect.center, rect.w - 20, center=True)

def draw_text_centered(surf, text, font, color, cy, shadow=True):
    if shadow:
        sh = font.render(text, True, BLACK)
        surf.blit(sh, sh.get_rect(center=(SCREEN_W // 2 + 2, cy + 2)))
    lbl = font.render(text, True, color)
    surf.blit(lbl, lbl.get_rect(center=(SCREEN_W // 2, cy)))

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def draw_text_fit(surf, text, font, color, pos, max_w, center=False, shadow=False):
    """Render text, scaling it down if it exceeds max_w."""
    lbl = font.render(text, True, color)
    tw, th = lbl.get_size()
    if tw > max_w:
        scale = max_w / tw
        lbl = pygame.transform.smoothscale(lbl, (max_w, int(th * scale)))
        tw, th = lbl.get_size()
    
    rect = lbl.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
        
    if shadow:
        sh = font.render(text, True, BLACK)
        if sh.get_width() > max_w:
            sh = pygame.transform.smoothscale(sh, (max_w, int(th)))
        surf.blit(sh, (rect.x + 2, rect.y + 2))
    
    surf.blit(lbl, rect)

# ─────────────────────────────────────────────
#  Camera
# ─────────────────────────────────────────────
class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x, target_y):
        # Smooth follow horizontally, limited vertically
        target_cx = target_x - SCREEN_W // 2
        # Offset Y so the ground (horizon) is lower, showing more sky
        target_cy = target_y - int(SCREEN_H * 0.75)
        self.x += (target_cx - self.x) * 0.08
        self.y += (target_cy - self.y) * 0.04
        self.x = clamp(self.x, 0, max(0, WORLD_W - SCREEN_W))
        self.y = clamp(self.y, -600, 600)

    def apply(self, wx, wy):
        return int(wx - self.x), int(wy - self.y)

    def apply_rect(self, rect):
        return pygame.Rect(rect.x - int(self.x), rect.y - int(self.y), rect.w, rect.h)

# ─────────────────────────────────────────────
#  Platform
# ─────────────────────────────────────────────
class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surf, camera):
        sr = camera.apply_rect(self.rect)
        if sr.right < -50 or sr.left > SCREEN_W + 50:
            return
        # Wooden platform look
        pygame.draw.rect(surf, BROWN, sr)
        pygame.draw.rect(surf, DARK_BROWN, sr, 2)
        # Plank lines
        for i in range(1, self.rect.w // 40):
            lx = sr.x + i * 40
            pygame.draw.line(surf, DARK_BROWN, (lx, sr.y), (lx, sr.y + sr.h), 1)

# ─────────────────────────────────────────────
#  FloatingText
# ─────────────────────────────────────────────
class FloatingText:
    def __init__(self, x, y, text, color=GOLD, duration=1.5, screen_space=False):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.timer = duration
        self.duration = duration
        self.screen_space = screen_space
        self.alive = True

    def update(self, dt):
        self.y -= 40 * dt
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False

    def draw(self, surf, font, camera):
        if not self.alive:
            return
        alpha = int(255 * (self.timer / self.duration))
        if self.screen_space:
            sx, sy = self.x, self.y
        else:
            sx, sy = camera.apply(self.x, self.y)
        
        lbl = font.render(self.text, True, self.color)
        tmp = pygame.Surface(lbl.get_size(), pygame.SRCALPHA)
        tmp.blit(lbl, (0, 0))
        tmp.set_alpha(alpha)
        surf.blit(tmp, (sx - lbl.get_width() // 2, sy))

# ─────────────────────────────────────────────
#  Bullet
# ─────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, dx, dy, damage, speed=14, color=YELLOW, radius=4, lifespan=5.0):
        self.x, self.y = float(x), float(y)
        self.dx, self.dy = dx, dy
        self.damage = damage
        self.speed = speed
        self.color = color
        self.radius = radius
        self.lifespan = lifespan
        self.alive = True

    def update(self, dt):
        if dt <= 0: return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        self.lifespan -= dt
        if self.lifespan <= 0 or self.x < -100 or self.x > WORLD_W + 100 or self.y < -200 or self.y > SCREEN_H + 400:
            self.alive = False

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        if -20 < sx < SCREEN_W + 20 and -20 < sy < SCREEN_H + 20:
            pygame.draw.circle(surf, self.color, (sx, sy), self.radius)
            pygame.draw.circle(surf, WHITE, (sx, sy), self.radius, 1)

# ─────────────────────────────────────────────
#  Grenade & Explosion
# ─────────────────────────────────────────────
class Explosion:
    def __init__(self, x, y, radius, damage):
        self.x, self.y = float(x), float(y)
        self.max_radius = radius
        self.radius = 0.0
        self.damage = damage
        self.timer = 0.2
        self.duration = 0.2
        self.alive = True
        self.hits = [] # Track zombies already hit

    def update(self, dt):
        self.timer -= dt
        progress = 1.0 - max(0, self.timer / self.duration)
        self.radius = self.max_radius * math.sqrt(progress)
        if self.timer <= 0:
            self.alive = False

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        if -100 < sx < SCREEN_W + 100 and -100 < sy < SCREEN_H + 100:
            alpha = int(255 * max(0, self.timer / self.duration))
            s = pygame.Surface((int(self.radius*2), int(self.radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 50, 0, alpha), (int(self.radius), int(self.radius)), int(self.radius))
            pygame.draw.circle(s, (255, 200, 0, alpha), (int(self.radius), int(self.radius)), int(self.radius * 0.7))
            pygame.draw.circle(s, (255, 255, 255, alpha), (int(self.radius), int(self.radius)), int(self.radius * 0.3)) # Inner white flash
            surf.blit(s, (int(sx - self.radius), int(sy - self.radius)))

# ─────────────────────────────────────────────
#  Particle System
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifespan, gravity=0.15):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.lifespan = lifespan
        self.max_life = lifespan
        self.gravity = gravity
        self.alive = True

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += self.gravity
        self.lifespan -= dt
        if self.lifespan <= 0:
            self.alive = False

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        if -50 < sx < SCREEN_W + 50 and -50 < sy < SCREEN_H + 50:
            alpha = int(255 * (self.lifespan / self.max_life))
            # Optimization: only draw if alpha is significant
            if alpha > 10:
                p_surf = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
                surf.blit(p_surf, (sx - self.size, sy - self.size))

class MuzzleFlash:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.timer = 0.04
        self.alive = True
    
    def update(self, dt):
        self.timer -= dt
        if self.timer <= 0:
            self.alive = False
            
    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        # Small orange/yellow flash
        length = random.randint(15, 30)
        width = random.randint(10, 20)
        tip_x = sx + math.cos(self.angle) * length
        tip_y = sy + math.sin(self.angle) * length
        offset = width / 2
        p1 = (sx + math.cos(self.angle + 0.6) * offset, sy + math.sin(self.angle + 0.6) * offset)
        p2 = (sx + math.cos(self.angle - 0.6) * offset, sy + math.sin(self.angle - 0.6) * offset)
        pygame.draw.polygon(surf, (255, 230, 100), [ (sx, sy), p1, (tip_x, tip_y), p2 ])
        pygame.draw.circle(surf, WHITE, (int(sx), int(sy)), 5)

class Grenade:
    def __init__(self, x, y, dx, dy, damage, explosion_radius=100):
        self.x, self.y = float(x), float(y)
        throw_power = 600
        self.vx = dx * throw_power
        self.vy = dy * throw_power - 150 # Arc upwards slightly
        self.timer = 1.5
        self.damage = damage
        self.explosion_radius = explosion_radius
        self.alive = True
        self.radius = 6
        self.bounced = False

    def update(self, dt, platforms):
        if dt <= 0: return
        self.timer -= dt
        self.vy += 800 * dt # Gravity
        
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Ground collision
        if self.y >= GROUND_Y - self.radius:
            self.y = GROUND_Y - self.radius
            self.vy = -self.vy * 0.5 # Bounce
            self.vx *= 0.7 # Friction
            if abs(self.vy) > 50 and not self.bounced:
                self.bounced = True
                play_sound("click") # Simple bounce thud
                
        if self.timer <= 0:
            self.alive = False

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        if -20 < sx < SCREEN_W + 20 and -20 < sy < SCREEN_H + 20:
            pygame.draw.circle(surf, DARK_GRAY, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surf, GREEN, (int(sx), int(sy)), 2)
            # Blink red when close to blowing up
            if int(self.timer * 10) % 2 == 0:
                pygame.draw.circle(surf, RED, (int(sx), int(sy)), 2)

# ─────────────────────────────────────────────
#  Player
# ─────────────────────────────────────────────
class Player:
    WEAPONS = {
        "knife":   {"dmg": 25, "rate": 0.40, "spd": 0,  "spread": 0,  "pellets": 1,
                    "col": GRAY,       "name": "Knife",   "cost": 0,   "type": "melee",    "ammo_type": None, "lifespan": 0.15},
        "pistol":  {"dmg": 25, "rate": 0.35, "spd": 16, "spread": 2,  "pellets": 1,
                    "col": YELLOW,     "name": "Pistol",  "cost": 0,   "type": "gun",      "ammo_type": "pistol", "lifespan": 0.8},
        "shotgun": {"dmg": 15, "rate": 0.80, "spd": 18, "spread": 15, "pellets": 5,
                    "col": ORANGE,     "name": "Shotgun", "cost": 100, "type": "gun",      "ammo_type": "shotgun", "lifespan": 0.35},
        "smg":     {"dmg": 12, "rate": 0.10, "spd": 20, "spread": 5,  "pellets": 1,
                    "col": LIGHT_GREEN,"name": "SMG",     "cost": 150, "type": "gun",      "ammo_type": "smg", "lifespan": 0.6},
        "sniper":  {"dmg": 80, "rate": 1.20, "spd": 25, "spread": 0,  "pellets": 1,
                    "col": WHITE,      "name": "Sniper",  "cost": 250, "type": "gun",      "ammo_type": "sniper", "lifespan": 2.0},
        "grenade": {"dmg": 150,"rate": 1.5,  "spd": 0,  "spread": 0,  "pellets": 1,
                    "col": DARK_GREEN, "name": "Grenade", "cost": 200, "type": "throwable", "ammo_type": "grenade", "lifespan": 1.5},
    }

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 61, 88
        self.vx, self.vy = 0.0, 0.0
        self.speed = 4.2
        self.sprint_spd = 7.0
        self.on_ground = False
        self.facing = 1  # 1=right, -1=left

        self.max_hp = 100
        self.hp = 100.0
        self.max_stamina = 100
        self.stamina = 100.0
        self.sta_regen = 10.0
        self.sta_cost = 20.0

        self.money = 25
        self.exp = 0
        self.alive = True
        self.unlocked_weapons = ["knife", "pistol"]
        self.weapon = "pistol"
        self.weapon_index = 0
        self.fire_cd = 0.0
        self.angle = 0.0
        self.hurt_t = 0.0
        self.is_flying = False
        self.is_admin = False

        self.rescued_npcs = 0
        self.kills = 0
        self.medkits = 0

        # Level / EXP system
        self.level = 1
        self.exp_to_next = 100   # EXP required for next level-up
        self.level_up_pending = False  # flag for GameManager to show banner
        self.skill_points_pending = 0  # Number of skill selections to show

        # Skills
        self.has_double_jump = False
        self.jumps_made = 0
        self.has_shield = False
        self.shield_active = False
        self.shield_timer = 0.0
        self.shield_cd = 0.0

        # Per-weapon ammo inventory
        self.ammo = {"pistol": 30, "shotgun": 8, "smg": 60, "sniper": 10, "grenade": 3}

        self.image = load_image("player.png", (self.w, self.h))

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h), self.w, self.h)

    def check_level_up(self):
        """Check if exp is enough to level up. May level up multiple times."""
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            # Scale exp requirement: each level needs ~30% more EXP
            self.exp_to_next = int(self.exp_to_next * 1.3)
            # Stat bonus per level-up
            self.max_hp += 15
            self.hp = min(self.hp + 20, self.max_hp)  # small heal
            self.max_stamina += 10
            self.stamina = min(self.stamina + 15, self.max_stamina)
            self.level_up_pending = True
            
            # Every 5 levels, give a skill point
            if self.level % 5 == 0:
                self.skill_points_pending += 1
                
    def jump(self):
        """Trigger a jump or double jump if allowed."""
        if self.on_ground:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self.jumps_made = 1
        elif self.has_double_jump and self.jumps_made == 1:
            self.vy = JUMP_FORCE * 0.9  # slightly weaker 2nd jump
            self.jumps_made = 2
            # Feedback?
            
    def use_shield(self):
        """Activate energy shield if unlocked and off cooldown."""
        if self.has_shield and self.shield_cd <= 0 and not self.shield_active:
            self.shield_active = True
            self.shield_timer = 8.0 # 8 seconds as requested
            self.shield_cd = 30.0   # 30 second cooldown
            play_sound("pickup_exp")

    def take_damage(self, amount):
        if self.shield_active:
            # Shield absorbs 100% damage
            return
        self.hp -= amount
        self.hurt_t = 0.2
        play_sound("player_hurt")
        if self.hp <= 0:
            self.alive = False
            self.hp = 0

    def update(self, dt, bullets, platforms, camera, grenades, particles):
        if dt <= 0: return
        keys = pygame.key.get_pressed()
        # Horizontal movement
        move = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move += 1
        if move != 0:
            self.facing = move

        sprinting = keys[pygame.K_LSHIFT] and self.stamina > 0 and move != 0
        spd = self.sprint_spd if sprinting else self.speed
        if sprinting:
            self.stamina = max(0, self.stamina - self.sta_cost * dt)
        else:
            self.stamina = min(self.max_stamina, self.stamina + self.sta_regen * dt)

        self.vx = move * spd
        if self.is_flying:
            # Flight mode
            y_move = 0
            if keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]:
                y_move -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                y_move += 1
            self.vy = y_move * spd
            
            self.x += self.vx
            self.x = clamp(self.x, self.w // 2, WORLD_W - self.w // 2)
            self.y += self.vy
            self.on_ground = False
        else:
            # Gravity
            self.vy += GRAVITY
            self.vy = min(self.vy, 18)

            # Move X
            self.x += self.vx
            self.x = clamp(self.x, self.w // 2, WORLD_W - self.w // 2)

            # Move Y and collide platforms
            self.y += self.vy
            self.on_ground = False
            pr = self.rect
            for plat in platforms:
                if pr.colliderect(plat.rect):
                    if self.vy > 0 and pr.bottom >= plat.rect.top and (pr.bottom - self.vy) <= plat.rect.top + 10:
                        self.y = float(plat.rect.top)
                        self.vy = 0
                        self.on_ground = True
                        self.jumps_made = 0

            # Ground collision
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0
                self.on_ground = True
                self.jumps_made = 0

        # Shield Logics
        if self.shield_active:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield_active = False
        if self.shield_cd > 0:
            self.shield_cd -= dt

        # Aiming
        mx, my = get_scaled_mouse_pos()
        sx, sy = camera.apply(self.x, self.y - self.h // 2)
        self.angle = math.atan2(my - sy, mx - sx)
        if math.cos(self.angle) < 0:
            self.facing = -1
        else:
            self.facing = 1

        # Weapon swapping
        if keys[pygame.K_1] and "pistol" in self.unlocked_weapons: self.weapon = "pistol"
        if keys[pygame.K_2] and "shotgun" in self.unlocked_weapons: self.weapon = "shotgun"
        if keys[pygame.K_3] and "smg" in self.unlocked_weapons: self.weapon = "smg"
        if keys[pygame.K_4] and "sniper" in self.unlocked_weapons: self.weapon = "sniper"

        self.fire_cd -= dt
        if self.hurt_t > 0:
            self.hurt_t -= dt

        if pygame.mouse.get_pressed()[0]:
            self._shoot(bullets, grenades, particles)

    def _shoot(self, bullets, grenades, particles):
        if self.fire_cd > 0:
            return
        w = self.WEAPONS[self.weapon]
        ammo_type = w.get("ammo_type")

        if ammo_type and self.ammo.get(ammo_type, 0) <= 0:
            return

        self.fire_cd = w["rate"]
        wtype = w.get("type", "gun")

        if wtype == "gun":
            self.ammo[self.weapon] = max(0, self.ammo.get(self.weapon, 0) - 1)
            play_sound(f"shoot_{self.weapon}")
            
            # Position for effects
            flash_x = self.x + math.cos(self.angle) * 35
            flash_y = self.y - self.h // 2 + math.sin(self.angle) * 35
            
            for _ in range(w["pellets"]):
                spread_rad = math.radians(random.uniform(-w["spread"], w["spread"]))
                a = self.angle + spread_rad
                ox = self.x + math.cos(a) * 35
                oy = self.y - self.h // 2 + math.sin(a) * 35
                rad = 6 if self.weapon == "sniper" else 4
                bullets.append(Bullet(ox, oy, math.cos(a), math.sin(a),
                                      w["dmg"], w["spd"], w["col"], radius=rad, lifespan=w.get("lifespan", 5.0)))
            
            # Muzzle Flash
            particles.append(MuzzleFlash(flash_x, flash_y, self.angle))
            
            # Smoke & Sparks
            for _ in range(random.randint(4, 8)):
                p_angle = self.angle + random.uniform(-0.5, 0.5)
                p_spd = random.uniform(1, 4)
                particles.append(Particle(flash_x, flash_y, math.cos(p_angle)*p_spd, math.sin(p_angle)*p_spd, (255, 220, 100), random.randint(1, 3), random.uniform(0.1, 0.25)))
            
            # Smoke (gray)
            for _ in range(3):
                p_angle = self.angle + random.uniform(-0.4, 0.4)
                p_spd = random.uniform(0.5, 2)
                particles.append(Particle(flash_x, flash_y, math.cos(p_angle)*p_spd, math.sin(p_angle)*p_spd, (150, 150, 150), random.randint(3, 6), random.uniform(0.3, 0.6), gravity=-0.04))
        elif wtype == "melee":
            play_sound("shoot_smg")
            ox = self.x + math.cos(self.angle) * 35
            oy = self.y - self.h // 2 + math.sin(self.angle) * 35
            b = Bullet(ox, oy, math.cos(self.angle), math.sin(self.angle), w["dmg"], 0, w["col"], radius=35)
            b.lifespan = 0.15
            bullets.append(b)
        elif wtype == "throwable":
            self.ammo["grenade"] = max(0, self.ammo.get("grenade", 0) - 1)
            play_sound("shoot_pistol")
            ox = self.x
            oy = self.y - self.h // 2
            grenades.append(Grenade(ox, oy, math.cos(self.angle), math.sin(self.angle), w["dmg"]))

    def _draw_weapon(self, surf, sx, sy):
        # Gun drawing logic based on type
        w_id = self.weapon
        w_data = self.WEAPONS[w_id]
        angle = self.angle
        
        # Center of player (where hands are)
        hx = sx
        hy = sy - self.h // 2
        
        # Gun length/shape
        g_len = 0
        g_thick = 4
        g_col = w_data["col"]
        
        # Tip of the barrel (for muzzle flash etc if needed)
        gx = hx + int(math.cos(angle) * 35)
        gy = hy + int(math.sin(angle) * 35)

        # Custom shapes per gun
        if w_id == "pistol":
            # Small body
            self._draw_rect_rot(surf, hx, hy, 18, 10, angle, DARK_GRAY)
            # Barrel
            self._draw_rect_rot(surf, hx + math.cos(angle)*10, hy + math.sin(angle)*10, 20, 6, angle, GRAY)
        elif w_id == "shotgun":
            # Stock
            self._draw_rect_rot(surf, hx - math.cos(angle)*8, hy - math.sin(angle)*8, 25, 12, angle, BROWN)
            # Long thick barrel
            self._draw_rect_rot(surf, hx + math.cos(angle)*15, hy + math.sin(angle)*15, 45, 10, angle, DARK_GRAY)
        elif w_id == "smg":
            # Magazine
            mag_angle = angle + math.pi/2
            self._draw_rect_rot(surf, hx + math.cos(angle)*10, hy + math.sin(angle)*10, 15, 6, mag_angle, GRAY)
            # Body
            self._draw_rect_rot(surf, hx + math.cos(angle)*12, hy + math.sin(angle)*12, 35, 12, angle, DARK_GRAY)
        elif w_id == "sniper":
            # Long thin barrel
            self._draw_rect_rot(surf, hx + math.cos(angle)*25, hy + math.sin(angle)*25, 65, 6, angle, BLACK)
            # Body/Scope
            self._draw_rect_rot(surf, hx + math.cos(angle)*5, hy + math.sin(angle)*5, 30, 14, angle, DARK_GRAY)
            # Scope lens
            self._draw_rect_rot(surf, hx + math.cos(angle)*5, hy + math.sin(angle)*5 - 8, 12, 6, angle, CYAN)
        elif w_id == "knife":
            # Handle
            self._draw_rect_rot(surf, hx, hy, 12, 6, angle, BROWN)
            # Blade
            self._draw_rect_rot(surf, hx + math.cos(angle)*12, hy + math.sin(angle)*12, 18, 4, angle, WHITE)
        elif w_id == "grenade":
            # Small green ball
            pygame.draw.circle(surf, DARK_GREEN, (int(hx + math.cos(angle)*15), int(hy + math.sin(angle)*15)), 6)
            pygame.draw.circle(surf, WHITE, (int(hx + math.cos(angle)*15), int(hy + math.sin(angle)*15)), 6, 1)

        # Muzzle hint
        if w_data["type"] == "gun":
            pygame.draw.circle(surf, YELLOW, (gx, gy), 2)

    def _draw_rect_rot(self, surf, x, y, w, h, angle, color):
        """Helper to draw a rotated rectangle."""
        # Create a surface for the rect
        rect_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rect_surf.fill(color)
        # Rotate it
        rotated = pygame.transform.rotate(rect_surf, -math.degrees(angle))
        # Draw it centered
        r = rotated.get_rect(center=(int(x), int(y)))
        surf.blit(rotated, r)

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        # Draw character
        body_rect = pygame.Rect(sx - self.w // 2, sy - self.h, self.w, self.h)

        if self.shield_active:
            # Pulsing blue shield outline
            s_pulse = int(120 + 80 * math.sin(pygame.time.get_ticks() * 0.01))
            pygame.draw.circle(surf, (0, 150, 255), (sx, sy - self.h // 2), self.h // 2 + 15, 3)
            # Inner glow
            overlay = pygame.Surface((self.h*2, self.h*2), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (0, 100, 255, 60), (self.h, self.h), self.h // 2 + 10)
            surf.blit(overlay, (sx - self.h, sy - self.h - self.h // 2))

        if self.image:
            img = self.image
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            if self.hurt_t > 0:
                tinted = img.copy()
                tinted.fill((255, 80, 80), special_flags=pygame.BLEND_MULT)
                surf.blit(tinted, body_rect.topleft)
            else:
                surf.blit(img, body_rect.topleft)
        else:
            self._draw_fallback(surf, sx, sy)

        # Draw current weapon
        self._draw_weapon(surf, sx, sy)


    def _draw_fallback(self, surf, sx, sy):
        col = (255, 100, 100) if self.hurt_t > 0 else (80, 140, 80)
        # Body
        body = pygame.Rect(sx - 14, sy - 44, 28, 32)
        pygame.draw.rect(surf, col, body, border_radius=4)
        pygame.draw.rect(surf, DARK_GREEN, body, 2, border_radius=4)
        # Head
        pygame.draw.circle(surf, (200, 170, 130), (sx, sy - 48), 10)
        pygame.draw.circle(surf, DARK_BROWN, (sx, sy - 48), 10, 2)
        # Hair
        pygame.draw.arc(surf, DARK_BROWN, (sx - 10, sy - 62, 20, 16), 0, math.pi, 3)
        # Legs
        pygame.draw.rect(surf, DARK_BROWN, (sx - 10, sy - 12, 8, 12))
        pygame.draw.rect(surf, DARK_BROWN, (sx + 2, sy - 12, 8, 12))
        # Eyes
        ex = sx + 3 * self.facing
        pygame.draw.circle(surf, WHITE, (ex, sy - 50), 3)
        pygame.draw.circle(surf, BLACK, (ex + self.facing, sy - 50), 1)

# ─────────────────────────────────────────────
#  Zombie
# ─────────────────────────────────────────────
class Zombie:
    NORMAL = "normal"
    FAST = "fast"
    TANK = "tank"
    JUMP = "jump"
    FLY = "fly"
    BOSS = "boss"

    _STATS = {
        "normal": {"hp": 80, "spd": 1.8, "dmg": 12, "w": 42, "h": 62,
                   "col": (80, 160, 80), "money": 3, "exp": 8},
        "fast":   {"hp": 40, "spd": 3.5, "dmg": 8, "w": 36, "h": 57,
                   "col": (200, 120, 50), "money": 2, "exp": 10},
        "tank":   {"hp": 300, "spd": 1.0, "dmg": 25, "w": 57, "h": 73,
                   "col": (120, 80, 180), "money": 8, "exp": 20},
        "jump":   {"hp": 60, "spd": 2.2, "dmg": 12, "w": 42, "h": 60,
                   "col": (180, 200, 50), "money": 4, "exp": 12},
        "fly":    {"hp": 50, "spd": 2.5, "dmg": 10, "w": 39, "h": 39,
                   "col": (90, 200, 220), "money": 5, "exp": 15},
        "boss":   {"hp": 1500, "spd": 1.2, "dmg": 40, "w": 156, "h": 208,
                   "col": (255, 50, 50), "money": 100, "exp": 500},
    }

    def __init__(self, ztype, x, y, diff_hp=1.0, diff_dmg=1.0, diff_spd=1.0):
        s = self._STATS[ztype]
        self.ztype = ztype
        self.x, self.y = float(x), float(y)
        self.w, self.h = s["w"], s["h"]
        self.max_hp = s["hp"] * diff_hp
        self.hp = self.max_hp
        self.speed = s["spd"] * diff_spd
        self.damage = s["dmg"] * diff_dmg
        self.color = s["col"]
        self.money_drop = s["money"]
        self.exp_drop = s["exp"]
        self.alive = True
        self.atk_cd = 0.0
        self.hurt_t = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.jump_timer = random.uniform(2.0, 4.0) # Used for boss skill cooldown
        self.fly_wave = random.uniform(0.0, 6.28)  # Sine wave offset
        self.boss_skill_ready = False # Flag for GM to handle bullet spawning

        # Try to load custom image based on type, fallback otherwise
        if ztype == self.BOSS:
            # Boss image from image/Din.png
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "Din.png")
            try:
                img = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(img, (self.w, self.h))
            except Exception:
                self.image = load_image("zombie_boss.png", (self.w, self.h))
        else:
            img_name = f"zombie_{ztype}.png" if ztype != "normal" else "zombie.png"
            self.image = load_image(img_name, (self.w, self.h))

        if not self.image:
            self.image = load_image("zombie.png", (self.w, self.h))

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h), self.w, self.h)

    def update(self, dt, player, platforms):
        if dt <= 0: return
        dx = player.x - self.x
        self.facing = 1 if dx > 0 else -1
        self.x += self.facing * self.speed

        if self.ztype == self.FLY:
            # Flying zombie logic: Ignore gravity, fly towards player's Y with sine wave flutter
            target_y = player.y - 20
            dy = target_y - self.y
            self.y += (1 if dy > 0 else -1) * (self.speed * 0.8)
            self.fly_wave += dt * 4.0
            self.y += math.sin(self.fly_wave) * 1.5
        else:
            # Gravity
            self.vy += GRAVITY
            self.vy = min(self.vy, 18)
            self.y += self.vy
            self.on_ground = False

            pr = self.rect
            for plat in platforms:
                if pr.colliderect(plat.rect):
                    if self.vy > 0 and pr.bottom >= plat.rect.top:
                        self.y = float(plat.rect.top)
                        self.vy = 0
                        self.on_ground = True

            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0
                self.on_ground = True

            if self.ztype == self.JUMP:
                self.jump_timer -= dt
                # Jump if timer is up and on ground, or occasionally if blocked
                if self.on_ground and self.jump_timer <= 0:
                    self.vy = -12.0
                    self.on_ground = False
                    self.jump_timer = random.uniform(1.5, 4.0)
            
            if self.ztype == self.BOSS:
                # Boss Skill cooldown
                self.jump_timer -= dt
                if self.jump_timer <= 0:
                    self.jump_timer = random.uniform(3.0, 5.0)
                    self.boss_skill_ready = True # GM will read this and spawn bullet

        self.atk_cd -= dt
        if self.hurt_t > 0:
            self.hurt_t -= dt

        # Attack if close
        if abs(player.x - self.x) < 30 and abs(player.y - self.y) < 50:
            if self.atk_cd <= 0:
                player.take_damage(self.damage)
                self.atk_cd = 1.0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        self.hurt_t = 0.15
        if self.hp <= 0:
            self.alive = False
            play_sound("zombie_die")
        else:
            play_sound("zombie_hurt")

    def try_drop(self):
        drops = []
        if random.random() < 0.30:
            drops.append(Drop(self.x, self.y, "exp"))
        if random.random() < 0.25:
            drops.append(Drop(self.x + random.randint(-20, 20), self.y, "money"))
        if random.random() < 0.06:
            drops.append(Drop(self.x + random.randint(-15, 15), self.y, "weapon"))
        if random.random() < 0.20:
            drops.append(Drop(self.x + random.randint(-10, 10), self.y, "ammo_bullet"))
        if random.random() < 0.05:
            drops.append(Drop(self.x + random.randint(-10, 10), self.y, "ammo_grenade"))
        return drops

    def draw(self, surf, camera):
        sx, sy = camera.apply(self.x, self.y)
        if sx < -60 or sx > SCREEN_W + 60:
            return
        body = pygame.Rect(sx - self.w // 2, sy - self.h, self.w, self.h)
        col = (230, 230, 100) if self.hurt_t > 0 else self.color

        if self.image:
            img = self.image
            if self.facing < 0:
                img = pygame.transform.flip(img, True, False)
            if self.hurt_t > 0:
                # Tint red when hurt
                tinted = img.copy()
                tinted.fill((255, 100, 100), special_flags=pygame.BLEND_MULT)
                surf.blit(tinted, body.topleft)
            else:
                surf.blit(img, body.topleft)
        else:
            # Fallback zombie drawing
            if self.ztype == self.FLY:
                # Give flying zombie some wings/thrusters
                pygame.draw.circle(surf, WHITE, (sx - 10, sy - 15), 8)
                pygame.draw.circle(surf, WHITE, (sx + 10, sy - 15), 8)

            pygame.draw.rect(surf, col, body, border_radius=3)
            pygame.draw.rect(surf, BLACK, body, 2, border_radius=3)
            # Head
            hx, hy = sx, sy - self.h - 6
            pygame.draw.circle(surf, col, (hx, hy), self.w // 3)
            pygame.draw.circle(surf, BLACK, (hx, hy), self.w // 3, 2)
            # Red eyes
            pygame.draw.circle(surf, RED, (hx - 4, hy - 2), 3)
            pygame.draw.circle(surf, RED, (hx + 4, hy - 2), 3)

            # Extra details for Jump
            if self.ztype == self.JUMP:
                pygame.draw.rect(surf, RED, (sx - self.w // 2 + 4, sy - 10, 8, 10))
                pygame.draw.rect(surf, RED, (sx + self.w // 2 - 12, sy - 10, 8, 10))
            # Arms
            if self.ztype == self.TANK:
                pygame.draw.line(surf, col, (sx - self.w // 2, sy - self.h + 10),
                                 (sx - self.w // 2 - 12, sy - self.h + 25), 4)
                pygame.draw.line(surf, col, (sx + self.w // 2, sy - self.h + 10),
                                 (sx + self.w // 2 + 12, sy - self.h + 25), 4)

            # Special Scarier Boss Decorations
            if self.ztype == self.BOSS:
                # 1. Dark pulsing aura
                aura_time = pygame.time.get_ticks() / 1000.0
                aura_size = int(math.sin(aura_time * 5) * 10 + 20)
                aura_surf = pygame.Surface((self.w + aura_size*2, self.h + aura_size*2), pygame.SRCALPHA)
                pygame.draw.ellipse(aura_surf, (0, 0, 0, 100), (0, 0, self.w + aura_size*2, self.h + aura_size*2))
                surf.blit(aura_surf, (sx - self.w // 2 - aura_size, sy - self.h - aura_size), special_flags=pygame.BLEND_RGBA_SUB)

                # 2. Glowing Red Eyes (Re-draw bigger)
                eye_pulse = int(150 + 105 * math.sin(aura_time * 10))
                pygame.draw.circle(surf, (eye_pulse, 0, 0), (hx - 8, hy - 4), 6)
                pygame.draw.circle(surf, (eye_pulse, 0, 0), (hx + 8, hy - 4), 6)
                pygame.draw.circle(surf, WHITE, (hx - 8, hy - 4), 2)
                pygame.draw.circle(surf, WHITE, (hx + 8, hy - 4), 2)

                # 3. Horns/Spikes
                # Left horn
                pygame.draw.polygon(surf, DARK_GRAY, [(hx - 15, hy - 25), (hx - 25, hy - 45), (hx - 5, hy - 20)])
                # Right horn
                pygame.draw.polygon(surf, DARK_GRAY, [(hx + 15, hy - 25), (hx + 25, hy - 45), (hx + 5, hy - 20)])
                
                # 4. Spikes on shoulders
                pygame.draw.polygon(surf, BLACK, [(sx - self.w // 2, sy - self.h + 10), (sx - self.w // 2 - 20, sy - self.h - 10), (sx - self.w // 2 + 10, sy - self.h + 15)])
                pygame.draw.polygon(surf, BLACK, [(sx + self.w // 2, sy - self.h + 10), (sx + self.w // 2 + 20, sy - self.h - 10), (sx + self.w // 2 - 10, sy - self.h + 15)])

                # 5. Some "shadow flicker"
                if int(aura_time * 20) % 2 == 0:
                     flicker_rect = body.copy()
                     flicker_rect.x += random.randint(-5, 5)
                     flicker_rect.y += random.randint(-5, 5)
                     pygame.draw.rect(surf, (20, 0, 0, 100), flicker_rect, 3, border_radius=3)

        # HP bar above head
        bw = self.w + 4
        if self.ztype == self.BOSS:
            bw = 400 # Even wider bar for boss
        bx = sx - bw // 2
        by = sy - self.h - 16
        if self.ztype == self.BOSS:
            by -= 25 # Move higher to fit name
            # Draw Boss Name
            name_lbl = pygame.font.SysFont("arial", 28, bold=True).render("BOSS: P_Din", True, YELLOW)
            surf.blit(name_lbl, (sx - name_lbl.get_width() // 2, by - 35))
            
        # Draw Bar: Boss gets Red/Gray (Lost HP is Gray), regular get Green/Red
        if self.ztype == self.BOSS:
            draw_bar(surf, bx, by, bw, 12, self.hp, self.max_hp, RED, GRAY, 3)
        else:
            draw_bar(surf, bx, by, bw, 5, self.hp, self.max_hp, GREEN, DARK_RED, 1)

# ─────────────────────────────────────────────
#  NPC (Rescuable)
# ─────────────────────────────────────────────
class NPC:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.w, self.h = 36, 57
        self.rescued = False
        self.bob_t = random.uniform(0, math.pi * 2)
        self.image = load_image("npc.png", (self.w, self.h))

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w // 2), int(self.y - self.h), self.w, self.h)

    def draw(self, surf, camera, font):
        if self.rescued:
            return
        sx, sy = camera.apply(self.x, self.y)
        if sx < -60 or sx > SCREEN_W + 60:
            return
        self.bob_t += 0.03
        by = int(sy + math.sin(self.bob_t) * 2)

        if self.image:
            surf.blit(self.image, (sx - self.w // 2, by - self.h))
        else:
            # Cowering person
            body = pygame.Rect(sx - 12, by - 38, 24, 28)
            pygame.draw.rect(surf, (200, 170, 130), body, border_radius=4)
            pygame.draw.rect(surf, BROWN, body, 2, border_radius=4)
            pygame.draw.circle(surf, (200, 170, 130), (sx, by - 42), 8)
            pygame.draw.circle(surf, BROWN, (sx, by - 42), 8, 2)
            # Legs
            pygame.draw.rect(surf, BLUE, (sx - 8, by - 10, 6, 10))
            pygame.draw.rect(surf, BLUE, (sx + 2, by - 10, 6, 10))

        # Press E prompt
        lbl = font.render("[E] ช่วยเหลือ", True, GOLD)
        surf.blit(lbl, (sx - lbl.get_width() // 2, by - self.h - 22))

# ─────────────────────────────────────────────
#  Drop Item
# ─────────────────────────────────────────────
class Drop:
    COLORS = {"exp": CYAN, "money": GOLD, "weapon": ORANGE,
              "ammo_bullet": YELLOW, "ammo_grenade": DARK_GREEN}
    LABELS = {"exp": "EXP", "money": "$", "weapon": "GUN",
              "ammo_bullet": "AMO", "ammo_grenade": "GRN"}

    def __init__(self, x, y, dtype):
        self.x, self.y = float(x), float(y)
        self.dtype = dtype
        self.radius = 10
        self.alive = True
        self.bob_t = random.uniform(0, math.pi * 2)
        self.vy = -4.0  # initial upward pop

    def update(self, dt, platforms):
        if dt <= 0: return
        self.bob_t += dt * 3.0
        self.vy += GRAVITY * 0.5
        self.y += self.vy
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
        for plat in platforms:
            r = pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                            self.radius * 2, self.radius * 2)
            if r.colliderect(plat.rect) and self.vy > 0:
                self.y = float(plat.rect.top)
                self.vy = 0

    def draw(self, surf, camera, font):
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        if sx < -30 or sx > SCREEN_W + 30:
            return
        by = int(sy + math.sin(self.bob_t) * 3)
        col = self.COLORS.get(self.dtype, WHITE)
        
        # Draw a fancy glow/base for the item
        pygame.draw.circle(surf, DARK_GRAY, (sx, by + 2), self.radius + 4)
        pygame.draw.circle(surf, col, (sx, by), self.radius + 2)
        pygame.draw.circle(surf, WHITE, (sx, by), self.radius + 2, 2)

        # For weapons, draw a mini-version of the gun instead of just text
        if self.dtype == "weapon":
            # Simple icon representation
            pygame.draw.rect(surf, BLACK, (sx-10, by-4, 20, 8), border_radius=2)
            pygame.draw.rect(surf, GRAY, (sx+2, by-2, 12, 4), border_radius=1)
        else:
            lbl = font.render(self.LABELS.get(self.dtype, "?"), True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=(sx, by)))


# ─────────────────────────────────────────────
#  GameManager – State Machine
# ─────────────────────────────────────────────
class GameManager:
    MAIN_MENU  = "main_menu"
    DIFFICULTY = "difficulty"
    STORY      = "story"
    PLAYING    = "playing"
    GAME_OVER  = "game_over"
    VICTORY    = "victory"
    SHOP       = "shop"
    SETTINGS   = "settings"
    PAUSED     = "paused"
    SKILL_SELECT = "skill_select"
    CONTROLS   = "controls"
    ADMIN_MENU = "admin_menu"

    # ── 10 Stages with per-stage config ──
    STAGES = [
        {"name": "ป่าเริ่มต้น",             "name_en": "Starting Woods",
         "zombies": 8, "npc_target": 1, "kill_target": 8,
         "npc_positions": [800], "bg_type": "woods",
         "sky_top": (10, 20, 40), "sky_bot": (30, 50, 70)},
        {"name": "ทางหลวงสายมรณะ",         "name_en": "Highway of Death",
         "zombies": 12, "npc_target": 1, "kill_target": 12,
         "npc_positions": [1200], "bg_type": "urban",
         "sky_top": (15, 15, 35), "sky_bot": (40, 40, 60)},
        {"name": "ชานเมืองไร้ผู้คน",        "name_en": "Desolate Suburbs",
         "zombies": 18, "npc_target": 1, "kill_target": 18,
         "npc_positions": [1800], "bg_type": "urban",
         "sky_top": (20, 10, 30), "sky_bot": (50, 30, 50)},         
        {"name": "หมู่บ้านร้าง",             "name_en": "Abandoned Village",
         "zombies": 25, "npc_target": 1, "kill_target": 25,
         "npc_positions": [1500], "bg_type": "woods",
         "sky_top": (25, 10, 25), "sky_bot": (60, 25, 45)},
        {"name": "ปั๊มน้ำมันต้องสาป",       "name_en": "Cursed Gas Station",
         "zombies": 30, "npc_target": 0, "kill_target": 30,
         "npc_positions": [], "bg_type": "urban",
         "sky_top": (30, 8, 20), "sky_bot": (70, 20, 35)},
        {"name": "ท่อระบายน้ำมืดมิด",       "name_en": "Dark Sewers",
         "zombies": 35, "npc_target": 0, "kill_target": 35,
         "npc_positions": [], "bg_type": "sewer",
         "sky_top": (10, 10, 10), "sky_bot": (20, 20, 20)},
        {"name": "สวนสาธารณะนองเลือด",      "name_en": "Bloody Park",
         "zombies": 40, "npc_target": 1, "kill_target": 40,
         "npc_positions": [2000], "bg_type": "woods",
         "sky_top": (40, 10, 15), "sky_bot": (80, 15, 20)},
        {"name": "สะพานแห่งความตาย",        "name_en": "Bridge of Death",
         "zombies": 45, "npc_target": 1, "kill_target": 45,
         "npc_positions": [2200], "bg_type": "urban",
         "sky_top": (50, 15, 20), "sky_bot": (100, 30, 30)},
        {"name": "โรงงานที่ถูกทิ้งร้าง",     "name_en": "Forsaken Factory",
         "zombies": 50, "npc_target": 0, "kill_target": 50,
         "npc_positions": [], "bg_type": "industrial",
         "sky_top": (60, 20, 20), "sky_bot": (120, 40, 40)},
        {"name": "ยานแม่ของ Zombie",        "name_en": "Zombie Mothership",
         "zombies": 60, "npc_target": 0, "kill_target": 60,
         "npc_positions": [], "bg_type": "alien",
         "sky_top": (0, 0, 50), "sky_bot": (20, 0, 100)},
    ]
    MAX_STAGES = 10

    STORY_TEXT = (
        "เมื่อทั้งโลกเกิด ภัยวิกฤต โดยกลุ่ม Zombie จากนอกโลก "
        "พวกเราเหล่าผู้กล้าทั้ง 5 คน ได้ตัดสินใจออกไปกอบกู้โลก "
        "เพื่อต่อต้านกลุ่ม Zombie ที่จะโจมตีโลกของเรา "
        "เมื่อผู้กล้าทั้ง 4 ถึงยานของ Zombie แล้ว แล้วทำการต่อสู้ "
        "แต่พวก Zombie เยอะเกินกว่าที่คิด "
        "พวกจึงได้ทำการระเบิดยาน Zombie ทิ้ง "
        "จึงทำให้เหล่าผู้กล้าทั้ง 4 คน หล่นลงไปบนโลก คนละทิศคนละทาง "
        "แล้วก็มี Zombie หล่นแถมไปด้วย "
        "และต่อจากนี้ก็จะเป็นการผจญภัย ของเหล่าผู้กล้าทั้ง 4 คน....."
    )

    STORY_LINES = [
        "เมื่อทั้งโลกเกิด ภัยวิกฤต",
        "โดยกลุ่ม Zombie จากนอกโลก...",
        "ผู้กล้าทั้ง 5 ได้ตัดสินใจออกไปกอบกู้โลก",
        "เพื่อต่อต้านกลุ่ม Zombie ที่จะโจมตีโลก",
        "เมื่อผู้กล้าถึงยานของ Zombie แล้วทำการต่อสู้",
        "แต่พวก Zombie เยอะเกินกว่าที่คิด...",
        "พวกจึงระเบิดยาน Zombie ทิ้ง",
        "ผู้กล้าทั้ง 4 หล่นลงบนโลก คนละทิศคนละทาง",
        "แล้วก็มี Zombie หล่นแถมไปด้วย...",
        "และต่อจากนี้จะเป็นการผจญภัยของเหล่าผู้กล้า.....",
        "",
        "[ คลิกเพื่อเริ่มเกม ]",
    ]

    def __init__(self):
        pygame.init()
        init_sounds()
        self.display_screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.screen = pygame.Surface((SCREEN_W, SCREEN_H))
        self.is_fullscreen = False
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self._init_fonts()

        self._init_fonts()

        self.state = self.MAIN_MENU
        self.difficulty = "Medium"
        self.console_active = False
        self.console_text = ""

        # Gameplay objects (initialized on start)
        self.player = None
        self.camera = Camera()
        self.zombies = []
        self.bullets = []
        self.grenades = []
        self.explosions = []
        self.drops = []
        self.npcs = []
        self.platforms = []
        self.float_texts = []
        self.spawn_timer = 0.0
        self.total_zombie_target = 50
        self.show_weapon_wheel = False
        self.total_spawned = 0

        # Wave / Stage tracking
        self.current_stage = 0       # 0-indexed into STAGES
        self.wave_kills = 0          # kills this wave
        self.total_kills_all = 0     # cumulative kills
        self.total_rescued_all = 0   # cumulative rescued NPCs
        self.friend_found = False

        # Wave complete banner
        self.wave_banner_timer = 0.0

        # Menu decorations
        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H),
                       random.uniform(0.5, 2.5)) for _ in range(100)]
        self.star_t = 0.0

        # Story state
        self.story_timer = 0.0
        self.story_lines_shown = 0

        # Background decorations (initialized per stage)
        self.bg_deco_far = []
        self.bg_deco_near = []
        
        # Menu zombies
        self.menu_zombies = []
        for _ in range(4):
            ztype = random.choice(["normal", "fast", "tank"])
            z = Zombie(ztype, random.randint(0, SCREEN_W), SCREEN_H - 100)
            z.facing = random.choice([-1, 1])
            self.menu_zombies.append(z)

    def _init_fonts(self):
        thai_fonts = ["tahoma", "arial", "leelawadee", "cordiaupc",
                      "angsana new", "thsarabun", "freesans"]
        found = None
        for fn in thai_fonts:
            try:
                test = pygame.font.SysFont(fn, 20)
                if test:
                    found = fn
                    break
            except Exception:
                continue

        def make(size):
            return pygame.font.SysFont(found, size) if found else pygame.font.Font(None, size)

        self.font_lg = make(52)
        self.font_md = make(32)
        self.font_sm = make(22)
        self.font_xs = make(16)

    # ── Background Drawing ──
    def _draw_starfield(self, dt):
        self.screen.fill((5, 8, 20))
        self.star_t += dt
        for i, (sx, sy, spd) in enumerate(self.stars):
            ny = (sy + spd) % SCREEN_H
            self.stars[i] = (sx, ny, spd)
            # Ash/Particle look
            bright = int(100 + 50 * math.sin(self.star_t * spd))
            r = 1 if spd < 1.5 else 2
            pygame.draw.circle(self.screen, (bright, bright-10, bright-20), (int(sx), int(ny)), r)

    def _draw_menu_zombies(self, dt):
        """Draw some creepy zombies walking in the menu background."""
        for z in self.menu_zombies:
            # Update position (infinite loop)
            z.x += (z.speed * 0.4) * z.facing
            if z.facing > 0 and z.x > SCREEN_W + 100: z.x = -100
            elif z.facing < 0 and z.x < -100: z.x = SCREEN_W + 100
            
            # Draw as silhouettes
            sx, sy = int(z.x), int(z.y)
            rect = pygame.Rect(sx - z.w // 2, sy - z.h, z.w, z.h)
            
            # Shadow beneath
            pygame.draw.ellipse(self.screen, (10, 10, 10, 150), (sx - 30, sy - 15, 60, 20))
            
            if z.image:
                img = z.image
                if z.facing < 0: img = pygame.transform.flip(img, True, False)
                # Dark silhouette-ish tint
                z_surf = img.copy()
                z_surf.fill((20, 10, 10), special_flags=pygame.BLEND_MULT)
                z_surf.set_alpha(180)
                self.screen.blit(z_surf, rect.topleft)
            else:
                # Fallback circle if no image
                pygame.draw.rect(self.screen, (30, 40, 30), rect, border_radius=4)

    def _draw_sky(self):
        """Draw a nighttime gradient sky."""
        stage = self.STAGES[self.current_stage]
        sky_top = stage.get("sky_top", (10, 20, 40))
        sky_bot = stage.get("sky_bot", (30, 50, 70))

        for y in range(SCREEN_H):
            ratio = y / SCREEN_H
            r = int(sky_top[0] + (sky_bot[0] - sky_top[0]) * ratio)
            g = int(sky_top[1] + (sky_bot[1] - sky_top[1]) * ratio)
            b = int(sky_top[2] + (sky_bot[2] - sky_top[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))
        # Stars
        for sx, sy, spd in self.stars[:40]:
            bright = int(120 + 80 * math.sin(self.star_t * spd * 0.3))
            pygame.draw.circle(self.screen, (bright, bright, bright),
                               (int(sx), int(min(sy, GROUND_Y - 100))), 1)

    def _draw_background(self):
        """Draw dynamic background based on stage theme."""
        self._draw_sky()
        bg_type = self.STAGES[self.current_stage].get("bg_type", "woods")

        if bg_type == "alien":
            # Drawing scifi grid
            grid_col = (0, 100, 200)
            for x in range(0, WORLD_W, 100):
                ox = int(x - self.camera.x * 0.8) % (WORLD_W + 200) - 100
                pygame.draw.line(self.screen, grid_col, (ox, 0), (ox, GROUND_Y), 1)
            for y in range(0, GROUND_Y, 80):
                pygame.draw.line(self.screen, grid_col, (0, y), (SCREEN_W, y), 1)

        # Far Decorations (Parallax 0.3x)
        for dx, dy, dw, col in self.bg_deco_far:
            ox = int(dx - self.camera.x * 0.3) % (WORLD_W + 200) - 100
            if bg_type == "woods":
                pygame.draw.rect(self.screen, DARK_BROWN, (ox - 4, dy, 8, GROUND_Y - dy + 80))
                pygame.draw.circle(self.screen, col, (ox, dy), dw)
            elif bg_type == "urban":
                # Building silhouettes
                pygame.draw.rect(self.screen, col, (ox - dw, dy, dw * 2, GROUND_Y - dy + 80))
            elif bg_type == "sewer":
                # Brick pillar
                pygame.draw.rect(self.screen, (30, 25, 20), (ox - 20, 0, 40, GROUND_Y))
                pygame.draw.rect(self.screen, (20, 15, 10), (ox - 20, 0, 40, GROUND_Y), 2)
            elif bg_type == "industrial":
                # Smoke stacks
                pygame.draw.rect(self.screen, col, (ox - 15, dy, 30, GROUND_Y - dy))
                pygame.draw.rect(self.screen, BLACK, (ox - 18, dy, 36, 10))
            elif bg_type == "alien":
                # Glowing towers
                pygame.draw.rect(self.screen, (20, 0, 40), (ox - 10, dy, 20, GROUND_Y - dy))
                pygame.draw.rect(self.screen, CYAN, (ox - 2, dy, 4, GROUND_Y - dy), 0)

        # Near Decorations (Parallax 0.6x)
        for dx, dy, dw, col in self.bg_deco_near:
            ox = int(dx - self.camera.x * 0.6) % (WORLD_W + 200) - 100
            if bg_type == "woods":
                pygame.draw.rect(self.screen, (60, 40, 20), (ox - 5, dy, 10, GROUND_Y - dy + 80))
                pygame.draw.circle(self.screen, col, (ox, dy), dw)
            elif bg_type == "urban":
                # Closer building details or poles
                pygame.draw.rect(self.screen, col, (ox - dw//2, dy, dw, GROUND_Y - dy + 80))
                for window_y in range(int(dy) + 10, GROUND_Y, 20):
                    pygame.draw.rect(self.screen, (255, 255, 150), (ox - 5, window_y, 4, 4))
            elif bg_type == "sewer":
                # Pipes
                pygame.draw.rect(self.screen, (50, 50, 50), (0, dy, SCREEN_W, 15))
            elif bg_type == "industrial":
                # Metal beams
                pygame.draw.rect(self.screen, DARK_GRAY, (ox - 5, 0, 10, GROUND_Y))
            elif bg_type == "alien":
                # Tech panels
                pygame.draw.rect(self.screen, (40, 0, 80), (ox - 30, dy, 60, 40), border_radius=5)
                pygame.draw.rect(self.screen, (0, 255, 255), (ox - 30, dy, 60, 40), 1, border_radius=5)

        # Ground
        gy = GROUND_Y - int(self.camera.y)
        ground_col = DARK_GREEN if bg_type == "woods" else (40, 40, 40)
        line_col = GREEN if bg_type == "woods" else GRAY
        if bg_type == "sewer": ground_col, line_col = (20, 15, 10), (60, 40, 20)
        if bg_type == "alien": ground_col, line_col = (10, 0, 20), CYAN

        pygame.draw.rect(self.screen, ground_col, (0, gy, SCREEN_W, SCREEN_H - gy + 50))
        pygame.draw.line(self.screen, line_col, (0, gy), (SCREEN_W, gy), 3)

        if bg_type == "woods":
            # Grass blades
            for gx in range(0, SCREEN_W, 15):
                gh = random.randint(4, 12)
                pygame.draw.line(self.screen, (30, 100, 30), (gx, gy), (gx + random.randint(-3, 3), gy - gh), 1)
        elif bg_type == "sewer":
            # Water ripples?
            pygame.draw.rect(self.screen, (0, 50, 40), (0, gy + 10, SCREEN_W, 20))

    # ── Main Loop ──
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_F10:
                        self.console_active = not self.console_active
                        if self.console_active:
                            self.console_text = ""
                    elif e.key == pygame.K_F1:
                        if self.state in (self.PLAYING, self.PAUSED, self.ADMIN_MENU):
                            if self.state != self.ADMIN_MENU:
                                self.prev_state = self.state
                                self.state = self.ADMIN_MENU
                                play_sound("click")
                            else:
                                self.state = self.prev_state
                                play_sound("click")
                    elif self.console_active:
                        if e.key == pygame.K_BACKSPACE:
                            self.console_text = self.console_text[:-1]
                        elif e.key == pygame.K_RETURN:
                            # Execute command
                            cmd = self.console_text.strip()
                            if cmd == "endwave":
                                if self.state == self.PLAYING:
                                    self.total_spawned = self.total_zombie_target
                                    self.zombies = []
                            elif cmd == "P_Din is SuperGay":
                                if self.player:
                                    self.player.max_hp = 999999
                                    self.player.hp = 999999
                                    self.player.max_stamina = 999999
                                    self.player.stamina = 999999
                                    self.player.money += 999999
                                    self.player.exp += 5000
                                    # Unlock all weapons
                                    for w_id in self.player.WEAPONS.keys():
                                        if w_id not in self.player.unlocked_weapons:
                                            self.player.unlocked_weapons.append(w_id)
                            elif cmd == "Dmg_Max":
                                if self.player:
                                    for w_id in self.player.WEAPONS:
                                        self.player.WEAPONS[w_id]["dmg"] = 99999999
                                    self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "You Are Dead (OP Damage)", RED))
                            elif cmd == "Dmg_Normal":
                                if self.player:
                                    defaults = {"knife": 25, "pistol": 25, "shotgun": 15, "smg": 12, "sniper": 80, "grenade": 150}
                                    for w_id, val in defaults.items():
                                        if w_id in self.player.WEAPONS:
                                            self.player.WEAPONS[w_id]["dmg"] = val
                                    self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "Damage Restored to Normal", GREEN))
                            elif cmd == "fly":
                                if self.player:
                                    self.player.is_flying = True
                                    self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "Flight Mode ON", CYAN))
                            elif cmd == "unfly":
                                if self.player:
                                    self.player.is_flying = False
                                    self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "Flight Mode OFF", RED))
                            elif cmd == "betae":
                                if self.player:
                                    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "tae.png")
                                    try:
                                        img = pygame.image.load(path).convert_alpha()
                                        self.player.image = pygame.transform.scale(img, (self.player.w, self.player.h))
                                        self.float_texts.append(FloatingText(self.player.x, self.player.y - 80, "Skin: TAE Activated!", GOLD))
                                    except:
                                        self.float_texts.append(FloatingText(self.player.x, self.player.y - 80, "Error: tae.png not found!", RED))
                            elif cmd == "ฉันเป็นเก":
                                if self.player:
                                    self.prev_state = self.state
                                    self.state = self.ADMIN_MENU
                                    play_sound("click")
                                    self.console_active = False
                                    self.float_texts.append(FloatingText(self.player.x, self.player.y - 100, "Opening Admin Menu...", GOLD))
                            elif cmd == "endgame":
                                self.state = self.VICTORY
                            elif cmd == "spawnboss":
                                if self.state == self.PLAYING:
                                    dh, dd, ds = self._get_diff()
                                    stage_mult = 1.0 + self.current_stage * 0.15
                                    dh *= stage_mult
                                    dd *= stage_mult
                                    boss_sx = WORLD_W - 500 if self.player.x < WORLD_W / 2 else 500
                                    self.zombies.append(Zombie(Zombie.BOSS, boss_sx, GROUND_Y - 50, dh * 2.5, dd * 1.5, ds * 0.8))
                                    self.float_texts.append(FloatingText(SCREEN_W//2, SCREEN_H//2, "!!! COMMAND: BOSS P_Din APPEARED !!!", RED, duration=4.0, screen_space=True))
                                    self.total_spawned += 1
                            elif cmd == "bedin":
                                if self.player:
                                    # Base path is the project folder
                                    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "image", "Din.png")
                                    try:
                                        img = pygame.image.load(full_path).convert_alpha()
                                        self.player.image = pygame.transform.scale(img, (self.player.w, self.player.h))
                                        self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "Transformation: Din!", GOLD))
                                    except Exception:
                                        self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "Image Error: Din.png not found", RED))
                            self.console_active = False
                            self.console_text = ""
                        else:
                            self.console_text += e.unicode
                    elif e.key == pygame.K_F11:
                        self.is_fullscreen = not self.is_fullscreen
                        global WINDOW_W, WINDOW_H
                        if self.is_fullscreen:
                            WINDOW_W, WINDOW_H = SCREEN_W, SCREEN_H
                            self.display_screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.FULLSCREEN)
                        else:
                            WINDOW_W, WINDOW_H = 1280, 720
                            self.display_screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))

            # Block other game updates if typing in console
            if self.console_active:
                dt = 0

            if   self.state == self.MAIN_MENU:  self._state_main_menu(events, dt)
            elif self.state == self.SETTINGS:   self._state_settings(events, dt)
            elif self.state == self.DIFFICULTY:  self._state_difficulty(events, dt)
            elif self.state == self.CONTROLS:    self._state_controls(events, dt)
            elif self.state == self.ADMIN_MENU:  self._state_admin_menu(events, dt)
            elif self.state == self.STORY:       self._state_story(events, dt)
            elif self.state == self.PLAYING:     self._state_playing(events, dt)
            elif self.state == self.SKILL_SELECT: self._state_skill_select(events, dt)
            elif self.state == self.PAUSED:      self._state_paused(events, dt)
            elif self.state == self.SHOP:        self._state_shop(events, dt)
            elif self.state == self.GAME_OVER:   self._state_game_over(events, dt)
            elif self.state == self.VICTORY:     self._state_victory(events, dt)

            # Render Console Overlay
            if self.console_active:
                console_surf = pygame.Surface((SCREEN_W, 60), pygame.SRCALPHA)
                console_surf.fill((0, 0, 0, 200))
                self.screen.blit(console_surf, (0, 0))
                
                txt = self.font_sm.render(f"> {self.console_text}_", True, (0, 255, 0))
                self.screen.blit(txt, (20, 15))

            scaled_surf = pygame.transform.scale(self.screen, (WINDOW_W, WINDOW_H))
            self.display_screen.blit(scaled_surf, (0, 0))
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    # ═════════════════════════════════════
    #  MAIN MENU
    # ═════════════════════════════════════
    def _state_main_menu(self, events, dt):
        self._draw_starfield(dt)
        self._draw_menu_zombies(dt)
        
        # --- Atmospheric Vignette & Blood Splatters ---
        # Draw a dark "blood stain" overlay
        for i in range(4):
            # Slow moving blood stains
            bt = self.star_t * 0.5 + i * 2.1
            bx = SCREEN_W // 2 + int(math.cos(bt) * 450)
            by = SCREEN_H // 2 + int(math.sin(bt * 0.7) * 250)
            size = int(150 + 40 * math.sin(bt * 1.5))
            blood_surf = pygame.Surface((size*2, size), pygame.SRCALPHA)
            pygame.draw.ellipse(blood_surf, (120, 0, 0, 40), (0, 0, size*2, size))
            self.screen.blit(blood_surf, (bx - size, by - size//2))

        # Flickering title effect
        flicker = random.random() > 0.96
        title_col = ZOMBIE_RED if not flicker else (255, 50, 50)
        shadow_col = DRY_BLOOD if not flicker else (100, 0, 0)
        
        draw_text_centered(self.screen, "ZOMBIE SURVIVAL", self.font_lg, shadow_col, 174)
        draw_text_centered(self.screen, "ZOMBIE SURVIVAL", self.font_lg, title_col, 170, shadow=False)
        
        draw_text_centered(self.screen, "WARFARE", self.font_lg, shadow_col, 234)
        draw_text_centered(self.screen, "WARFARE", self.font_lg, title_col, 230, shadow=False)
        
        draw_text_centered(self.screen, "การผจญภัยในโลกที่ล่มสลาย",
                           self.font_sm, LIGHT_GREEN, 290)

        mx, my = get_scaled_mouse_pos()
        btn_start = pygame.Rect(SCREEN_W // 2 - 160, 380, 320, 65)
        btn_setting = pygame.Rect(SCREEN_W // 2 - 160, 465, 320, 65)
        btn_credits = pygame.Rect(SCREEN_W // 2 - 160, 550, 320, 65)
        btn_quit = pygame.Rect(SCREEN_W // 2 - 160, 635, 320, 65)

        # Draw themed buttons
        draw_button(self.screen, btn_start, "Start Game", self.font_md, btn_start.collidepoint(mx, my),
                    base_col=(40, 20, 20), hover_col=ZOMBIE_RED)
        draw_button(self.screen, btn_setting, "Setting Game", self.font_md, btn_setting.collidepoint(mx, my),
                    base_col=(30, 30, 35), hover_col=GRAY)
        draw_button(self.screen, btn_credits, "OwO ทักมาได้ถ้าคิดถึง", self.font_md, btn_credits.collidepoint(mx, my),
                    base_col=(20, 40, 60), hover_col=BLUE)
        draw_button(self.screen, btn_quit, "Exit Game", self.font_md, btn_quit.collidepoint(mx, my),
                    base_col=(30, 20, 20), hover_col=(100, 20, 20))

        ver = self.font_xs.render("v2.1  |  Apocalyptic Edition  |  By NongChamp", True, DARK_RED)
        self.screen.blit(ver, (10, SCREEN_H - 24))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_start.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.DIFFICULTY
                elif btn_setting.collidepoint(mx, my):
                    play_sound("click")
                    self.prev_state = self.state
                    self.state = self.SETTINGS
                elif btn_credits.collidepoint(mx, my):
                    play_sound("click")
                    webbrowser.open("https://www.instagram.com/tanak1t._/") 
                elif btn_quit.collidepoint(mx, my):
                    play_sound("click")
                    pygame.quit(); sys.exit()

    # ═════════════════════════════════════
    #  SETTINGS
    # ═════════════════════════════════════
    def _state_settings(self, events, dt):
        global GLOBAL_BGM_VOL, GLOBAL_SFX_VOL
        self._draw_starfield(dt)
        draw_text_centered(self.screen, "ตั้งค่า (Settings)", self.font_lg, WHITE, 80)

        mx, my = get_scaled_mouse_pos()
        
        # --- BGM Volume ---
        draw_text_centered(self.screen, "เสียงเพลง (Music)", self.font_md, GRAY, 170)
        btn_bgm_m = pygame.Rect(SCREEN_W // 2 - 150, 210, 40, 40)
        btn_bgm_p = pygame.Rect(SCREEN_W // 2 + 110, 210, 40, 40)
        draw_button(self.screen, btn_bgm_m, "-", self.font_md, btn_bgm_m.collidepoint(mx, my))
        draw_button(self.screen, btn_bgm_p, "+", self.font_md, btn_bgm_p.collidepoint(mx, my))
        # Draw Bar
        pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_W // 2 - 90, 215, 180, 30))
        pygame.draw.rect(self.screen, LIGHT_GREEN, (SCREEN_W // 2 - 90, 215, int(180 * GLOBAL_BGM_VOL), 30))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_W // 2 - 90, 215, 180, 30), 2)
        v_bgm = self.font_sm.render(f"{int(GLOBAL_BGM_VOL*100)}%", True, WHITE)
        self.screen.blit(v_bgm, v_bgm.get_rect(center=(SCREEN_W // 2, 230)))

        # --- SFX Volume ---
        draw_text_centered(self.screen, "เสียงเอฟเฟกต์ (SFX)", self.font_md, GRAY, 300)
        btn_sfx_m = pygame.Rect(SCREEN_W // 2 - 150, 340, 40, 40)
        btn_sfx_p = pygame.Rect(SCREEN_W // 2 + 110, 340, 40, 40)
        draw_button(self.screen, btn_sfx_m, "-", self.font_md, btn_sfx_m.collidepoint(mx, my))
        draw_button(self.screen, btn_sfx_p, "+", self.font_md, btn_sfx_p.collidepoint(mx, my))
        # Draw Bar
        pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_W // 2 - 90, 345, 180, 30))
        pygame.draw.rect(self.screen, CYAN, (SCREEN_W // 2 - 90, 345, int(180 * GLOBAL_SFX_VOL), 30))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_W // 2 - 90, 345, 180, 30), 2)
        v_sfx = self.font_sm.render(f"{int(GLOBAL_SFX_VOL*100)}%", True, WHITE)
        self.screen.blit(v_sfx, v_sfx.get_rect(center=(SCREEN_W // 2, 360)))

        # --- Controls Reference ---
        pygame.draw.line(self.screen, DARK_GRAY, (SCREEN_W // 2 - 300, 430), (SCREEN_W // 2 + 300, 430), 1)
        k_y = 450
        draw_text_centered(self.screen, "W A S D - เคลื่อนที่  |  Space - กระโดด  |  Click - ยิง", self.font_sm, GRAY, k_y)
        draw_text_centered(self.screen, "TAB - วงล้ออาวุธ  |  1,2,3,4 - เปลี่ยนอาวุธ  |  E - ช่วยคน", self.font_sm, GRAY, k_y + 30)

        # --- Back Button ---
        btn_back = pygame.Rect(SCREEN_W // 2 - 100, 560, 200, 50)
        draw_button(self.screen, btn_back, "กลับ", self.font_md, btn_back.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # BGM
                if btn_bgm_m.collidepoint(mx, my):
                    GLOBAL_BGM_VOL = max(0.0, round(GLOBAL_BGM_VOL - 0.1, 1))
                    update_bgm_volume()
                    play_sound("click")
                elif btn_bgm_p.collidepoint(mx, my):
                    GLOBAL_BGM_VOL = min(1.0, round(GLOBAL_BGM_VOL + 0.1, 1))
                    update_bgm_volume()
                    play_sound("click")
                # SFX
                elif btn_sfx_m.collidepoint(mx, my):
                    GLOBAL_SFX_VOL = max(0.0, round(GLOBAL_SFX_VOL - 0.1, 1))
                    update_sfx_volume()
                    play_sound("click")
                elif btn_sfx_p.collidepoint(mx, my):
                    GLOBAL_SFX_VOL = min(1.0, round(GLOBAL_SFX_VOL + 0.1, 1))
                    update_sfx_volume()
                    play_sound("click")
                # Back
                elif btn_back.collidepoint(mx, my):
                    play_sound("click")
                    self.state = getattr(self, "prev_state", self.MAIN_MENU)

    # ═════════════════════════════════════
    #  DIFFICULTY
    # ═════════════════════════════════════
    def _state_difficulty(self, events, dt):
        self._draw_starfield(dt)
        draw_text_centered(self.screen, "เลือกระดับความยาก", self.font_lg, YELLOW, 140)
        draw_text_centered(self.screen, "Difficulty Setting", self.font_sm, GRAY, 195)

        mx, my = get_scaled_mouse_pos()
        diff_list = [
            ("Easy", LIGHT_GREEN, "ง่าย – ซอมบี้อ่อนแอ"),
            ("Medium", YELLOW, "ปกติ – สมดุล"),
            ("Hard", RED, "ยาก – ซอมบี้แข็งแกร่ง"),
        ]
        btns = {}
        for i, (key, col, desc) in enumerate(diff_list):
            rect = pygame.Rect(SCREEN_W // 2 - 170, 260 + i * 110, 340, 70)
            hov = rect.collidepoint(mx, my)
            fill_col = (*col, 180) if hov else (30, 30, 50)
            s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            s.fill(fill_col)
            self.screen.blit(s, rect.topleft)
            pygame.draw.rect(self.screen, col, rect, 3, border_radius=10)
            draw_text_fit(self.screen, key, self.font_md, WHITE, (rect.centerx, rect.centery - 12), rect.w - 40, center=True)
            draw_text_fit(self.screen, desc, self.font_xs, col, (rect.centerx, rect.centery + 18), rect.w - 40, center=True)
            btns[key] = rect

        btn_back = pygame.Rect(20, SCREEN_H - 65, 120, 45)
        draw_button(self.screen, btn_back, "กลับ", self.font_sm, btn_back.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for key, rect in btns.items():
                    if rect.collidepoint(mx, my):
                        play_sound("click")
                        self.difficulty = key
                        self.state = self.CONTROLS
                if btn_back.collidepoint(mx, my):
                    self.state = self.MAIN_MENU

    # ═════════════════════════════════════
    #  CONTROLS GUIDE
    # ═════════════════════════════════════
    def _state_controls(self, events, dt):
        self._draw_starfield(dt)
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((10, 15, 20, 220))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "🎮 คู่มือการควบคุม (How to Play)", self.font_lg, GOLD, 120)
        
        # Guide Box
        panel = pygame.Rect(SCREEN_W // 2 - 450, 190, 900, 500)
        pygame.draw.rect(self.screen, (30, 40, 50), panel, border_radius=15)
        pygame.draw.rect(self.screen, RUST_ORANGE if random.random() > 0.1 else WHITE, panel, 3, border_radius=15)

        controls = [
            ("W A S D", "เคลื่อนที่ (Move) / ปีน (Climb)"),
            ("SPACE", "กระโดด (Jump) / กระโดด 2 ชั้น (ถ้ามี)"),
            ("เมาส์ซ้าย (L-Click)", "ยิงปืน (Shoot) / โจมตีประชิด"),
            ("TAB (ค้าง)", "วงล้อเลือกอาวุธ (Weapon Wheel)"),
            ("เลข 1 - 4", "สลับอาวุธโดยตรง (Quick Switch)"),
            ("H", "ใช้ยาพยาบาล (Use Medkit)"),
            ("Y", "เปิดโล่ป้องกัน (Shield Skill)"),
            ("E", "ช่วยตัวประกัน / คุยกับ NPC"),
            ("ESC", "หยุดเกมชั่วคราว (Pause)"),
        ]

        for i, (key, action) in enumerate(controls):
            ky = 230 + i * 42
            # Key highlight
            k_surf = self.font_sm.render(key, True, YELLOW)
            self.screen.blit(k_surf, (panel.x + 50, ky))
            # Action text
            a_surf = self.font_sm.render(f"➜  {action}", True, WHITE)
            self.screen.blit(a_surf, (panel.x + 280, ky))

        mx, my = get_scaled_mouse_pos()
        btn_next = pygame.Rect(SCREEN_W // 2 - 130, 750, 260, 60)
        draw_button(self.screen, btn_next, "เข้าใจแล้ว (Next) ❯", self.font_md, btn_next.collidepoint(mx, my),
                    base_col=(20, 100, 40), hover_col=(40, 160, 60))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_next.collidepoint(mx, my):
                    play_sound("click")
                    self.story_timer = 0.0
                    self.story_lines_shown = 0
                    self.state = self.STORY
            if e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN:
                self.story_timer = 0.0
                self.story_lines_shown = 0
                self.state = self.STORY

    # ═════════════════════════════════════
    #  ADMIN MENU
    # ═════════════════════════════════════
    def _state_admin_menu(self, events, dt):
        self._draw_starfield(dt)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200)) # Darker background
        self.screen.blit(overlay, (0, 0))

        draw_text_centered(self.screen, "🛠️ ADMIN CHEAT PANEL 🛠️", self.font_lg, GOLD, 100)
        
        mx, my = get_scaled_mouse_pos()
        p = self.player

        cheat_options = [
            ("God Mode (HP/Stamina)", "is_admin", GOLD),
            ("Flight Mode (Noclip)", "is_flying", CYAN),
            ("Weapon: Unlock All", "unlock_all", ORANGE),
            ("Weapon: One Hit Kill", "one_hit", RED),
            ("Economy: +10,000 $", "add_money", LIGHT_GREEN),
            ("Action: Kill All Zombies", "nuke", ZOMBIE_RED),
            ("Game: End Wave", "skip", PURPLE),
        ]

        # Draw panel
        panel_rect = pygame.Rect(SCREEN_W // 2 - 300, 180, 600, 520)
        pygame.draw.rect(self.screen, (20, 25, 30), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, GOLD, panel_rect, 2, border_radius=10)

        btns = []
        for i, (label, action_id, col) in enumerate(cheat_options):
            bx = panel_rect.x + 50
            by = panel_rect.y + 40 + i * 65
            btn_rect = pygame.Rect(bx, by, 500, 50)
            
            # Check current status for toggle labels
            status = ""
            if action_id == "is_admin": status = " [ON]" if p.is_admin else " [OFF]"
            elif action_id == "is_flying": status = " [ON]" if p.is_flying else " [OFF]"
            elif action_id == "one_hit": 
                is_ohk = p.WEAPONS["pistol"]["dmg"] > 1000
                status = " [ON]" if is_ohk else " [OFF]"
            
            hov = btn_rect.collidepoint(mx, my)
            draw_button(self.screen, btn_rect, label + status, self.font_md, hov,
                        base_col=(40, 45, 50), hover_col=col)
            btns.append((btn_rect, action_id))

        # Close button
        btn_close = pygame.Rect(SCREEN_W // 2 - 100, 720, 200, 50)
        draw_button(self.screen, btn_close, "กลับ (Exit)", self.font_md, btn_close.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_close.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.prev_state
                    
                for rect, aid in btns:
                    if rect.collidepoint(mx, my):
                        play_sound("click")
                        if aid == "is_admin":
                            p.is_admin = not p.is_admin
                            if p.is_admin:
                                p.max_hp = 999999; p.hp = 999999
                                p.max_stamina = 999999; p.stamina = 999999
                            else:
                                p.max_hp = 100; p.hp = 100
                                p.max_stamina = 100; p.stamina = 100
                        elif aid == "is_flying":
                            p.is_flying = not p.is_flying
                        elif aid == "unlock_all":
                            for w_id in p.WEAPONS:
                                if w_id not in p.unlocked_weapons:
                                    p.unlocked_weapons.append(w_id)
                        elif aid == "one_hit":
                            is_ohk = p.WEAPONS["pistol"]["dmg"] > 1000
                            new_dmg = 99999 if not is_ohk else 25 # simple revert
                            for w_id in p.WEAPONS: p.WEAPONS[w_id]["dmg"] = new_dmg
                        elif aid == "add_money":
                            p.money += 10000
                        elif aid == "nuke":
                            self.zombies = []
                        elif aid == "skip":
                            self.total_spawned = self.total_zombie_target
                            self.zombies = []
            
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = self.prev_state

    # ═════════════════════════════════════
    #  STORY CUTSCENE
    # ═════════════════════════════════════
    def _state_story(self, events, dt):
        self.screen.fill((5, 10, 5))
        pygame.draw.rect(self.screen, DARK_GREEN,
                         (40, 40, SCREEN_W - 80, SCREEN_H - 80), 2, border_radius=16)

        draw_text_centered(self.screen, "เรื่องราว / Story", self.font_md, GOLD, 80)

        # Animate lines appearing one by one
        self.story_timer += dt
        lines_to_show = min(len(self.STORY_LINES), int(self.story_timer / 0.6) + 1)

        for i in range(lines_to_show):
            line = self.STORY_LINES[i]
            # Fade effect for latest line
            if i == lines_to_show - 1:
                progress = (self.story_timer / 0.6) - i
                alpha = int(clamp(progress * 255, 0, 255))
            else:
                alpha = 255

            col = CYAN if "คลิก" in line else WHITE
            lbl = self.font_sm.render(line, True, col)
            tmp = pygame.Surface(lbl.get_size(), pygame.SRCALPHA)
            tmp.blit(lbl, (0, 0))
            tmp.set_alpha(alpha)
            self.screen.blit(tmp, (SCREEN_W // 2 - lbl.get_width() // 2, 130 + i * 45))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if lines_to_show >= len(self.STORY_LINES):
                    self._start_game()
                else:
                    self.story_timer = len(self.STORY_LINES) * 0.6  # skip to end

    # ─────────────────────────────────────
    #  Start / Setup Game
    # ─────────────────────────────────────
    def _start_game(self):
        """Start a brand new game from stage 1."""
        self.current_stage = 0
        self.total_kills_all = 0
        self.total_rescued_all = 0
        self.friend_found = False
        self.player = Player(200, GROUND_Y)
        self.camera = Camera()
        self._setup_stage()
        self.state = self.PLAYING

    def _setup_stage(self):
        """Set up the current stage (wave): world, NPCs, zombie count."""
        stage = self.STAGES[self.current_stage]
        # ดึงค่าตัวคูณจำนวนซอมบี้จากระดับความยาก
        diff_cfg = DIFFICULTY_SETTINGS[self.difficulty]
        spawn_mult = diff_cfg.get("spawn_mult", 1.0)
        self.total_zombie_target = int(stage["zombies"] * spawn_mult)
        self.total_spawned = 0
        self.wave_kills = 0
        self.wave_banner_timer = 0.0

        self.zombies = []
        self.bullets = []
        self.drops = []
        self.float_texts = []
        self.particles = []
        self.spawn_timer = 0.0

        # Build world for this stage
        self._build_world()
        self._init_bg_deco()

        # Reset player position
        self.player.x = 200
        self.player.y = GROUND_Y
        self.player.vx = 0
        self.player.vy = 0
        self.player.hp = min(self.player.hp + 30, self.player.max_hp)  # heal a bit between stages

    def _init_bg_deco(self):
        """Initialize background decorations based on stage theme."""
        bg_type = self.STAGES[self.current_stage].get("bg_type", "woods")
        random.seed(self.current_stage * 99)
        
        self.bg_deco_far = []
        self.bg_deco_near = []
        
        if bg_type == "woods":
            # Trees
            for _ in range(50):
                self.bg_deco_far.append((random.randint(0, WORLD_W), random.randint(600, 800), random.randint(40, 80), 
                    (15+random.randint(0,10), 40+random.randint(0,20), 10)))
            for _ in range(40):
                self.bg_deco_near.append((random.randint(0, WORLD_W), random.randint(700, 850), random.randint(35, 60), 
                    (10+random.randint(0,10), 60+random.randint(0,25), 8)))
        elif bg_type == "urban":
            # Buildings
            for _ in range(30):
                self.bg_deco_far.append((random.randint(0, WORLD_W), random.randint(400, 700), random.randint(40, 100), 
                    (30, 30, 40)))
            for _ in range(20):
                self.bg_deco_near.append((random.randint(0, WORLD_W), random.randint(500, 750), random.randint(60, 120), 
                    (50, 50, 60)))
        elif bg_type == "industrial":
            # Factory stuff
            for _ in range(25):
                self.bg_deco_far.append((random.randint(0, WORLD_W), random.randint(600, 800), random.randint(20, 50), 
                    (60, 65, 70)))
            for _ in range(15):
                self.bg_deco_near.append((random.randint(0, WORLD_W), random.randint(650, 800), random.randint(40, 80), 
                    (80, 85, 90)))
        elif bg_type == "sewer":
            # Pipes and grates
            for _ in range(20):
                self.bg_deco_far.append((random.randint(0, WORLD_W), random.randint(0, 800), 0, (0,0,0)))
            for _ in range(15):
                self.bg_deco_near.append((0, random.randint(200, 800), 0, (0,0,0)))
        elif bg_type == "alien":
            # Scifi things
            for _ in range(30):
                self.bg_deco_far.append((random.randint(0, WORLD_W), random.randint(300, 800), 0, (0,0,0)))
            for _ in range(20):
                self.bg_deco_near.append((random.randint(0, WORLD_W), random.randint(400, 850), 0, (0,0,0)))
        
        random.seed()

    def _build_world(self):
        """Generate platforms and NPCs for the current stage."""
        self.platforms = []
        # Generate semi-random platforms based on stage
        random.seed(self.current_stage * 42)  # deterministic per stage
        num_platforms = 8 + self.current_stage * 2
        for i in range(num_platforms):
            px = 250 + i * (WORLD_W // (num_platforms + 1))
            py = random.randint(580, 800)
            pw = random.randint(180, 300)
            self.platforms.append(Platform(px, py, pw, 16))
        random.seed()  # re-randomize

        # NPCs for this stage
        stage = self.STAGES[self.current_stage]
        self.npcs = []
        for npc_x in stage["npc_positions"]:
            self.npcs.append(NPC(npc_x, GROUND_Y))

    def _get_diff(self):
        d = DIFFICULTY_SETTINGS[self.difficulty]
        return d["hp"], d["dmg"], d["spd"]

    def _spawn_zombie(self):
        dh, dd, ds = self._get_diff()
        # Scale up stats slightly per stage
        stage_mult = 1.0 + self.current_stage * 0.15
        dh *= stage_mult
        dd *= stage_mult

        # Spawn ahead or behind player
        side = random.choice([-1, 1])
        sx = self.player.x + side * random.randint(SCREEN_W // 2 + 50, SCREEN_W // 2 + 300)
        sx = clamp(sx, 50, WORLD_W - 50)
        sy = GROUND_Y - 10

        # Later stages introduce new types and increase odds
        tank_chance = 0.05 + self.current_stage * 0.04
        fast_chance = 0.10 + self.current_stage * 0.04
        jump_chance = 0.0  + self.current_stage * 0.05
        fly_chance  = 0.0  + max(0, self.current_stage - 1) * 0.06 # start appearing stage 2+
        
        r = random.random()
        if r < fly_chance:
            ztype = Zombie.FLY
            sy -= random.randint(100, 250) # spawn in air
        elif r < fly_chance + jump_chance:
            ztype = Zombie.JUMP
        elif r < fly_chance + jump_chance + tank_chance:
            ztype = Zombie.TANK
        elif r < fly_chance + jump_chance + tank_chance + fast_chance:
            ztype = Zombie.FAST
        else:
            ztype = Zombie.NORMAL
            
        self.zombies.append(Zombie(ztype, sx, sy, dh, dd, ds))
        self.total_spawned += 1

        # Every 5 waves, spawn boss if almost all zombies are spawned
        wave_num = self.current_stage + 1
        if wave_num % 5 == 0 and self.total_spawned == self.total_zombie_target:
            # Spawn the Boss "P_Din"
            boss_sx = WORLD_W - 500 if self.player.x < WORLD_W / 2 else 500
            # Higher HP multiplier for boss
            self.zombies.append(Zombie(Zombie.BOSS, boss_sx, GROUND_Y - 50, dh * 2.5, dd * 1.5, ds * 0.8))
            self.float_texts.append(FloatingText(SCREEN_W//2, SCREEN_H//2, "!!! BOSS P_Din APPEARED !!!", RED, duration=4.0, screen_space=True))

    def _on_wave_complete(self):
        """Called when all zombies in current wave are dead."""
        self.current_stage += 1

        # Final stage beaten → victory!
        if self.current_stage >= self.MAX_STAGES:
            self.state = self.VICTORY
            return

        # Shop after waves 3, 6, and 9 (0-indexed stages 3, 6, 9 -> after completing waves 3,6,9)
        if self.current_stage in (3, 6, 9):
            self.state = self.SHOP
        else:
            # Go directly to next stage
            self._setup_stage()
            self.wave_banner_timer = 3.0  # show "Wave X" banner

    # ═════════════════════════════════════
    #  GAMEPLAY STATE
    # ═════════════════════════════════════
    def _state_playing(self, events, dt):
        self.star_t += dt  # for background twinkle

        # ── Spawn zombies ──
        self.spawn_timer -= dt
        if self.total_spawned < self.total_zombie_target and self.spawn_timer <= 0:
            self._spawn_zombie()
            # ปรับความเร็วในการเกิดตามระดับความยาก
            delay_mult = DIFFICULTY_SETTINGS[self.difficulty].get("spawn_delay", 1.0)
            self.spawn_timer = random.uniform(0.8, 2.0) * delay_mult

        # ── Handle events ──
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_TAB:
                    play_sound("click")
                    self.show_weapon_wheel = True
                elif e.key == pygame.K_ESCAPE:
                    self.state = self.PAUSED
                    return
                elif e.key == pygame.K_e:
                    # Try rescue NPC
                    for npc in self.npcs:
                        if not npc.rescued and abs(self.player.x - npc.x) < 50 and abs(self.player.y - npc.y) < 60:
                            npc.rescued = True
                            play_sound("rescue")
                            self.player.rescued_npcs += 1
                            self.total_rescued_all += 1
                            self.float_texts.append(FloatingText(npc.x, npc.y - 40, "+ช่วยผู้คน!", CYAN))
                elif e.key == pygame.K_h:
                    # Use Medkit
                    if self.player.medkits > 0 and self.player.hp < self.player.max_hp:
                        self.player.medkits -= 1
                        heal_amt = 50
                        self.player.hp = min(self.player.hp + heal_amt, self.player.max_hp)
                        play_sound("pickup_exp") # Use a pleasant sound
                        self.float_texts.append(FloatingText(self.player.x, self.player.y - 60, f"+{heal_amt} HP (ใช้ยา)", GREEN))
                elif e.key == pygame.K_y:
                    # Use Shield
                    self.player.use_shield()
                elif e.key == pygame.K_w or e.key == pygame.K_SPACE:
                    # Jump
                    self.player.jump()
            elif e.type == pygame.KEYUP:
                if e.key == pygame.K_TAB:
                    self.show_weapon_wheel = False
                    play_sound("click")

        # ── Update ──
        if self.show_weapon_wheel:
            dt = 0 # Freeze game
            
        self.player.update(dt, self.bullets, self.platforms, self.camera, self.grenades, self.particles)
        self.camera.update(self.player.x, self.player.y)

        # ── Level-up check ──
        self.player.check_level_up()
        if self.player.level_up_pending:
            self.player.level_up_pending = False
            lv = self.player.level
            self.float_texts.append(FloatingText(
                self.player.x, self.player.y - 80,
                f"★ LEVEL UP!  Lv.{lv} ★", GOLD, duration=2.5, screen_space=True))
            self.float_texts.append(FloatingText(
                self.player.x, self.player.y - 50,
                f"+15 HP  |  +10 Stamina", LIGHT_GREEN, duration=2.0, screen_space=True))
            
            # Transition to skill select if earned a point (every 5 levels)
            if self.player.skill_points_pending > 0:
                self.state = self.SKILL_SELECT

        # Bullets
        for b in self.bullets:
            b.update(dt)
            
        # Grenades & Explosions
        for g in self.grenades:
            g.update(dt, self.platforms)
            if not g.alive:
                play_sound("shoot_shotgun") # Big boom sound
                self.explosions.append(Explosion(g.x, g.y, g.explosion_radius, g.damage))
        self.grenades = [g for g in self.grenades if g.alive]
        
        for e_obj in self.explosions:
            e_obj.update(dt)
        self.explosions = [e_obj for e_obj in self.explosions if e_obj.alive]

        # Zombies
        for z in self.zombies:
            z.update(dt, self.player, self.platforms)
            
            # Spawn Boss Projectile if ready
            if hasattr(z, "boss_skill_ready") and z.boss_skill_ready:
                z.boss_skill_ready = False
                p_dir_x, p_dir_y = normalize(self.player.x - z.x, (self.player.y - self.player.h//2) - (z.y - z.h//2))
                boss_proj = Bullet(z.x, z.y - z.h//2, p_dir_x, p_dir_y, z.damage * 0.8, speed=10, color=RED, radius=15)
                boss_proj.is_boss_atk = True
                self.bullets.append(boss_proj)
                play_sound("shoot_sniper")
            
            # Bullet collision
            for b in self.bullets:
                if b.alive:
                    if hasattr(b, "is_boss_atk") and b.is_boss_atk:
                        # Boss attack hitting player
                        if abs(b.x - self.player.x) < self.player.w // 2 + b.radius and abs(b.y - (self.player.y - self.player.h // 2)) < self.player.h // 2 + b.radius:
                            self.player.take_damage(b.damage)
                            b.alive = False
                    elif z.alive:
                        # Player attack hitting zombie
                        if abs(b.x - z.x) < z.w // 2 + b.radius and abs(b.y - (z.y - z.h // 2)) < z.h // 2 + b.radius:
                            z.take_damage(b.damage)
                            b.alive = False
                        
            # Explosion collision
            for e_obj in self.explosions:
                if z.alive and z not in e_obj.hits:
                    if dist(z.x, z.y - z.h // 2, e_obj.x, e_obj.y) < e_obj.radius + z.w // 2:
                        z.take_damage(e_obj.damage)
                        e_obj.hits.append(z)
            # Zombie died
            if not z.alive and z.hp <= 0:
                self.player.kills += 1
                self.wave_kills += 1
                self.total_kills_all += 1
                self.player.money += z.money_drop
                self.player.exp += z.exp_drop
                new_drops = z.try_drop()
                self.drops.extend(new_drops)
                self.float_texts.append(FloatingText(z.x, z.y - z.h, f"+{z.exp_drop} Exp", CYAN))
                if z.money_drop > 0:
                    self.float_texts.append(FloatingText(z.x + 15, z.y - z.h + 10, f"+{z.money_drop} เงิน", GOLD))

        # Drops
        for d in self.drops:
            d.update(dt, self.platforms)
            if d.alive:
                if abs(d.x - self.player.x) < 30 and abs(d.y - self.player.y) < 40:
                    d.alive = False
                    if d.dtype == "exp":
                        play_sound("pickup_exp")
                        self.player.exp += 15
                        self.float_texts.append(FloatingText(d.x, d.y - 20, "+Exp", CYAN))
                    elif d.dtype == "money":
                        play_sound("pickup_money")
                        self.player.money += 5
                        self.float_texts.append(FloatingText(d.x, d.y - 20, "+เงิน", GOLD))
                    elif d.dtype == "weapon":
                        play_sound("pickup_weapon")
                        available = [w_id for w_id in self.player.WEAPONS.keys() if w_id not in self.player.unlocked_weapons]
                        if available:
                            new_wpn = random.choice(available)
                            self.player.unlocked_weapons.append(new_wpn)
                            self.float_texts.append(FloatingText(d.x, d.y - 20, f"+ปืนใหม่ ({self.player.WEAPONS[new_wpn]['name']})", ORANGE))
                        else:
                            self.player.money += 30
                            self.float_texts.append(FloatingText(d.x, d.y - 20, "+$30 (มีปืนครบแล้ว)", GOLD))
                    elif d.dtype == "ammo_bullet":
                        play_sound("pickup_money")
                        # Give ammo to the currently equipped gun, or pistol if using knife/grenade
                        gun_target = self.player.weapon if self.player.WEAPONS[self.player.weapon]["type"] == "gun" else "pistol"
                        self.player.ammo[gun_target] = self.player.ammo.get(gun_target, 0) + 10
                        self.float_texts.append(FloatingText(d.x, d.y - 20, f"+10 {self.player.WEAPONS[gun_target]['name']}", YELLOW))
                    elif d.dtype == "ammo_grenade":
                        play_sound("pickup_weapon")
                        self.player.ammo["grenade"] = self.player.ammo.get("grenade", 0) + 1
                        self.float_texts.append(FloatingText(d.x, d.y - 20, "+1 ระเบิด", DARK_GREEN))

        # Floating texts
        for ft in self.float_texts:
            ft.update(dt)
            
        # Particles
        for p_obj in self.particles:
            p_obj.update(dt)

        # Cleanup
        self.bullets = [b for b in self.bullets if b.alive]
        self.zombies = [z for z in self.zombies if z.alive]
        self.drops = [d for d in self.drops if d.alive]
        self.float_texts = [ft for ft in self.float_texts if ft.alive]
        self.particles = [p_obj for p_obj in self.particles if p_obj.alive]

        # Death check
        if not self.player.alive:
            self.state = self.GAME_OVER
            return

        # Wave complete check – all zombies spawned and killed
        if self.total_spawned >= self.total_zombie_target and len(self.zombies) == 0:
            self._on_wave_complete()
            return

        # Wave banner countdown
        if self.wave_banner_timer > 0:
            self.wave_banner_timer -= dt

        # ── Draw ──
        # Draw sky colors based on logic or base colors
        stage_cfg = self.STAGES[self.current_stage]
        c1 = stage_cfg["sky_top"]
        c2 = stage_cfg["sky_bot"]
        # Basic gradient over background (just 2 big rects for performance)
        pygame.draw.rect(self.screen, c1, (0, 0, SCREEN_W, SCREEN_H // 2))
        pygame.draw.rect(self.screen, c2, (0, SCREEN_H // 2, SCREEN_W, SCREEN_H // 2))

        self._draw_background()

        # Platforms
        for plat in self.platforms:
            plat.draw(self.screen, self.camera)

        # Drops
        for d in self.drops:
            d.draw(self.screen, self.camera, self.font_xs)
            
        # Particles
        for p_obj in self.particles:
            p_obj.draw(self.screen, self.camera)

        # NPCs
        for npc in self.npcs:
            npc.draw(self.screen, self.camera, self.font_xs)

        # Zombies
        for z in self.zombies:
            z.draw(self.screen, self.camera)

        # Bullets
        for b in self.bullets:
            b.draw(self.screen, self.camera)

        # Grenades
        for g in self.grenades:
            g.draw(self.screen, self.camera)

        # Explosions
        for e_obj in self.explosions:
            e_obj.draw(self.screen, self.camera)

        # Player
        self.player.draw(self.screen, self.camera)

        # Floating texts
        for ft in self.float_texts:
            ft.draw(self.screen, self.font_sm, self.camera)

        # HUD on top
        self._draw_hud()

        if self.show_weapon_wheel:
            self._draw_weapon_wheel()

        # ── Wave Banner (Draw on Top Layer) ──
        if self.wave_banner_timer > 0:
            alpha = int(min(255, self.wave_banner_timer * 255))
            if alpha > 0:
                # Banner bg
                bh = 170
                bs = pygame.Surface((SCREEN_W, bh), pygame.SRCALPHA)
                bs.fill((0, 0, 0, min(200, alpha)))
                self.screen.blit(bs, (0, SCREEN_H // 2 - bh // 2))
                
                # Glowing edges
                pygame.draw.line(self.screen, ZOMBIE_RED, (0, SCREEN_H // 2 - bh // 2), (SCREEN_W, SCREEN_H // 2 - bh // 2), 3)
                pygame.draw.line(self.screen, ZOMBIE_RED, (0, SCREEN_H // 2 + bh // 2), (SCREEN_W, SCREEN_H // 2 + bh // 2), 3)

                # Texts
                stg = self.STAGES[self.current_stage]
                w_txt = f"WAVE {self.current_stage + 1}"
                draw_text_centered(self.screen, w_txt, self.font_lg, ZOMBIE_RED, SCREEN_H // 2 - 55)
                draw_text_centered(self.screen, stg["name"], self.font_md, LIGHT_GREEN, SCREEN_H // 2 + 30)
                
                # Subtext
                sub = f"Mission: {stg['kill_target']} Kills Required"
                draw_text_centered(self.screen, sub, self.font_xs, WHITE, SCREEN_H // 2 + 75)

    # ─────────────────────────────────────
    #  HUD & Weapon Wheel
    # ─────────────────────────────────────
    def _draw_weapon_wheel(self):
        # Darken screen
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 180))
        self.screen.blit(ov, (0, 0))

        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        
        # Center text
        draw_text_centered(self.screen, "WEAPONS", self.font_md, WHITE, cy - 10)
        draw_text_centered(self.screen, "Release TAB to Equip", self.font_xs, GRAY, cy + 20)
        
        mx, my = get_scaled_mouse_pos()
        angle_mouse = math.atan2(my - cy, mx - cx)
        if angle_mouse < 0:
            angle_mouse += 2 * math.pi
            
        weapons = self.player.unlocked_weapons
        num_w = len(weapons)
        slice_angle = (2 * math.pi) / max(1, num_w)
        
        # Find which slice the mouse is in
        selected_idx = int((angle_mouse + slice_angle / 2) % (2 * math.pi) / slice_angle)
        if selected_idx >= num_w:
            selected_idx = 0
            
        radius = 180
        for i, w_id in enumerate(weapons):
            w_data = self.player.WEAPONS[w_id]
            angle = i * slice_angle
            
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            
            is_selected = (i == selected_idx)
            if is_selected:
                self.player.weapon = w_id # Auto equip
                pygame.draw.circle(self.screen, (50, 150, 50), (int(x), int(y)), 55)
                pygame.draw.circle(self.screen, WHITE, (int(x), int(y)), 55, 3)
            else:
                pygame.draw.circle(self.screen, (40, 40, 40), (int(x), int(y)), 45)
                pygame.draw.circle(self.screen, w_data["col"], (int(x), int(y)), 45, 2)
            
            draw_text_fit(self.screen, w_data["name"], self.font_sm, WHITE if is_selected else GRAY, (int(x), int(y)), 80, center=True)

    def _draw_hud(self):
        p = self.player

        # ── Top-Left: Avatar + HP + Stamina + Skills ──
        # Panel background (taller to fit EXP bar)
        hud_panel = pygame.Surface((310, 170), pygame.SRCALPHA)
        hud_panel.fill((0, 0, 0, 160))
        self.screen.blit(hud_panel, (8, 8))
        pygame.draw.rect(self.screen, GRAY, (8, 8, 310, 170), 1, border_radius=6)

        # Level badge (top-left of avatar)
        lv_badge_lbl = self.font_xs.render(f"LV.{p.level}", True, GOLD)
        self.screen.blit(lv_badge_lbl, (12, 12))

        # Avatar circle
        pygame.draw.circle(self.screen, DARK_GRAY, (50, 50), 28)
        if p.image:
            # Draw the player's current image in the HUD portrait
            avatar_img = pygame.transform.scale(p.image, (42, 42))
            self.screen.blit(avatar_img, (50 - 21, 50 - 21))
        else:
            pygame.draw.circle(self.screen, (200, 170, 130), (50, 50), 24)  # face
            pygame.draw.circle(self.screen, DARK_BROWN, (50, 40), 15, 3)  # hair
            pygame.draw.circle(self.screen, BLACK, (44, 48), 2)  # eye
            pygame.draw.circle(self.screen, BLACK, (56, 48), 2)  # eye
        pygame.draw.circle(self.screen, WHITE, (50, 50), 28, 2)

        # HP label + bar
        lbl_hp = self.font_xs.render("VITALITY / HP", True, ZOMBIE_RED)
        self.screen.blit(lbl_hp, (86, 18))
        draw_bar(self.screen, 86, 36, 210, 14, p.hp, p.max_hp, ZOMBIE_RED)
        hp_txt = self.font_xs.render(f"{int(p.hp)}/{p.max_hp}", True, WHITE)
        self.screen.blit(hp_txt, (300 - hp_txt.get_width(), 35))

        # Stamina label + bar
        lbl_st = self.font_xs.render("ADRENALINE / STAMINA", True, LIGHT_BLUE)
        self.screen.blit(lbl_st, (86, 56))
        draw_bar(self.screen, 86, 74, 210, 14, p.stamina, p.max_stamina, BLUE)
        st_txt = self.font_xs.render(f"{int(p.stamina)}/{p.max_stamina}", True, WHITE)
        self.screen.blit(st_txt, (300 - st_txt.get_width(), 73))

        # ── EXP Bar (below stamina) ──
        exp_ratio = p.exp / max(1, p.exp_to_next)
        lbl_exp = self.font_xs.render(
            f"EXP  {p.exp}/{p.exp_to_next}  (Lv.{p.level})", True, CYAN)
        self.screen.blit(lbl_exp, (86, 95))
        # Bar background
        pygame.draw.rect(self.screen, DARK_GRAY, (86, 112, 210, 11), border_radius=4)
        # Filled portion – glow cyan
        fill_w = int(210 * exp_ratio)
        if fill_w > 0:
            pygame.draw.rect(self.screen, CYAN, (86, 112, fill_w, 11), border_radius=4)
        pygame.draw.rect(self.screen, WHITE, (86, 112, 210, 11), 1, border_radius=4)

        # ── Skill icons label ──
        lbl_skill = self.font_xs.render("ทักษะ", True, WHITE)
        self.screen.blit(lbl_skill, (16, 130))

        # 3 Skill icon placeholders
        skill_names = ["Sprint Boot", "Axe Swing", "Rifle Scope"]
        skill_colors = [GREEN, ORANGE, BLUE]
        for i, (sn, sc) in enumerate(zip(skill_names, skill_colors)):
            sx = 86 + i * 70
            sy = 138
            pygame.draw.rect(self.screen, DARK_GRAY, (sx, sy, 56, 30), border_radius=4)
            pygame.draw.rect(self.screen, sc, (sx, sy, 56, 30), 2, border_radius=4)
            # Skill icon symbol
            pygame.draw.circle(self.screen, sc, (sx + 28, sy + 11), 7)
            draw_text_fit(self.screen, sn.split()[0], self.font_xs, WHITE, (sx + 28, sy + 24), 50, center=True)

        # Medkit count in HUD
        med_lbl = self.font_xs.render(f"[H] ยา: {p.medkits}", True, LIGHT_GREEN)
        self.screen.blit(med_lbl, (16, 175))

        # ── Top-Right: Ammo Panel (above minimap) ──
        ammo_panel_w = 180
        ammo_panel_x = SCREEN_W - ammo_panel_w - 12
        ammo_panel_y = 12
        gun_weapons = [(w_id, p.WEAPONS[w_id]) for w_id in p.unlocked_weapons if p.WEAPONS[w_id]["type"] in ("gun", "throwable")]
        ammo_panel_h = 14 + len(gun_weapons) * 22 + 6
        ap = pygame.Surface((ammo_panel_w, ammo_panel_h), pygame.SRCALPHA)
        ap.fill((0, 0, 0, 160))
        self.screen.blit(ap, (ammo_panel_x, ammo_panel_y))
        pygame.draw.rect(self.screen, GRAY, (ammo_panel_x, ammo_panel_y, ammo_panel_w, ammo_panel_h), 1, border_radius=3)
        hdr = self.font_xs.render("กระสุน / AMMO", True, GOLD)
        self.screen.blit(hdr, (ammo_panel_x + 8, ammo_panel_y + 4))
        for i, (w_id, wdata) in enumerate(gun_weapons):
            ay = ammo_panel_y + 18 + i * 22
            is_current = (p.weapon == w_id)
            count = p.ammo.get(w_id, 0)
            name_col = wdata["col"] if is_current else GRAY
            count_col = (LIGHT_GREEN if count > 0 else RED) if is_current else GRAY
            marker = "▶ " if is_current else "   "
            draw_text_fit(self.screen, f"{marker}{wdata['name']}", self.font_xs, name_col, (ammo_panel_x + 6, ay), ammo_panel_w - 50)
            a_lbl = self.font_xs.render(str(count), True, count_col)
            self.screen.blit(a_lbl, (ammo_panel_x + ammo_panel_w - a_lbl.get_width() - 8, ay))

        ammo_panel_bottom = ammo_panel_y + ammo_panel_h + 8

        # ── Top-Right: Minimap ──
        mm_w, mm_h = 180, 100
        mm_x, mm_y = SCREEN_W - mm_w - 12, ammo_panel_bottom
        mm_panel = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm_panel.fill((0, 0, 0, 140))
        self.screen.blit(mm_panel, (mm_x, mm_y))
        pygame.draw.rect(self.screen, GRAY, (mm_x, mm_y, mm_w, mm_h), 1)

        # Player dot (green)
        pmx = int(mm_x + (p.x / WORLD_W) * mm_w)
        pmy = int(mm_y + mm_h * 0.7)
        pygame.draw.circle(self.screen, GREEN, (pmx, pmy), 4)

        # Zombie dots (red)
        for z in self.zombies:
            zmx = int(mm_x + (z.x / WORLD_W) * mm_w)
            zmy = int(mm_y + mm_h * 0.65 + random.randint(-3, 3))
            pygame.draw.circle(self.screen, RED, (zmx, zmy), 2)

        # NPC dots (yellow)
        for npc in self.npcs:
            if not npc.rescued:
                nmx = int(mm_x + (npc.x / WORLD_W) * mm_w)
                nmy = int(mm_y + mm_h * 0.7)
                pygame.draw.circle(self.screen, YELLOW, (nmx, nmy), 3)

        # ── Mission Panel (below minimap) ──
        stage_cfg = self.STAGES[self.current_stage]
        mp_x, mp_y = SCREEN_W - 250, mm_y + mm_h + 10
        mp_panel = pygame.Surface((238, 165), pygame.SRCALPHA)
        mp_panel.fill((0, 0, 0, 150))
        self.screen.blit(mp_panel, (mp_x, mp_y))
        pygame.draw.rect(self.screen, GOLD, (mp_x, mp_y, 238, 165), 1, border_radius=4)

        mission_title = self.font_xs.render("ภารกิจปัจจุบัน:", True, ORANGE)
        self.screen.blit(mission_title, (mp_x + 8, mp_y + 6))

        # Per-stage missions
        stage_npc_target = stage_cfg["npc_target"]
        stage_npcs_rescued = sum(1 for n in self.npcs if n.rescued)
        stage_kill_target = stage_cfg["kill_target"]
        friend_val = 1 if self.total_rescued_all >= 3 else 0
        missions = [
            f"• ช่วยผู้คน ({stage_npcs_rescued}/{stage_npc_target} คน)",
            f"• กำจัดซอมบี้ ({self.wave_kills}/{stage_kill_target})",
            f"• เจอเพื่อน ({friend_val}/1)",
        ]
        for i, m_text in enumerate(missions):
            draw_text_fit(self.screen, m_text, self.font_xs, WHITE, (mp_x + 12, mp_y + 28 + i * 22), 210)

        # Stage progress
        prog_title = self.font_xs.render("ความคืบหน้าเรื่องหลัก:", True, GREEN)
        self.screen.blit(prog_title, (mp_x + 8, mp_y + 98))
        draw_text_fit(self.screen, stage_cfg["name"], self.font_xs, GOLD, (mp_x + 12, mp_y + 118), 210)
        draw_text_fit(self.screen, f"Wave {self.current_stage + 1}/{self.MAX_STAGES}", self.font_xs, LIGHT_GREEN, (mp_x + 12, mp_y + 140), 210)

        # ── Bottom-Left: Inventory ──
        inv_y = SCREEN_H - 80
        inv_panel = pygame.Surface((320, 68), pygame.SRCALPHA)
        inv_panel.fill((0, 0, 0, 160))
        self.screen.blit(inv_panel, (8, inv_y))
        pygame.draw.rect(self.screen, GRAY, (8, inv_y, 320, 68), 1, border_radius=4)

        # Backpack icon
        pygame.draw.rect(self.screen, BROWN, (16, inv_y + 32, 28, 22), border_radius=3)
        pygame.draw.rect(self.screen, DARK_BROWN, (16, inv_y + 32, 28, 22), 2, border_radius=3)
        bp_lbl = self.font_xs.render("กระเป๋า", True, BROWN)
        self.screen.blit(bp_lbl, (16, inv_y + 10))

        # Weapon
        wp_lbl = self.font_xs.render(f"อาวุธ:", True, YELLOW)
        self.screen.blit(wp_lbl, (85, inv_y + 10))
        current_w = p.WEAPONS[p.weapon]
        draw_text_fit(self.screen, current_w['name'], self.font_xs, current_w['col'], (85, inv_y + 32), 80)

        # EXP Info
        exp_lbl = self.font_xs.render(f"Level {p.level}", True, GOLD)
        self.screen.blit(exp_lbl, (175, inv_y + 10))
        
        # EXP Circle
        pygame.draw.circle(self.screen, CYAN, (185, inv_y + 44), 10)
        pygame.draw.circle(self.screen, WHITE, (185, inv_y + 44), 10, 1)
        e_lbl = self.font_xs.render("E", True, WHITE) # Shorter label inside
        self.screen.blit(e_lbl, e_lbl.get_rect(center=(185, inv_y + 44)))
        
        exp_val = self.font_xs.render(f"{p.exp}/{p.exp_to_next}", True, CYAN)
        self.screen.blit(exp_val, (200, inv_y + 36))

        # Money
        money_lbl = self.font_xs.render("เงินหลัก", True, GOLD)
        self.screen.blit(money_lbl, (260, inv_y + 10))
        pygame.draw.circle(self.screen, GOLD, (272, inv_y + 44), 10)
        pygame.draw.circle(self.screen, DARK_BROWN, (272, inv_y + 44), 10, 1)
        m_txt = self.font_xs.render("$", True, DARK_BROWN)
        self.screen.blit(m_txt, m_txt.get_rect(center=(272, inv_y + 44)))
        money_val = self.font_xs.render(f"{p.money}", True, WHITE)
        self.screen.blit(money_val, (288, inv_y + 36))

        # ── Shield Status (if unlocked) ──
        if p.has_shield:
            sh_x, sh_y = 8, inv_y - 45
            sh_panel = pygame.Surface((320, 40), pygame.SRCALPHA)
            sh_panel.fill((0, 0, 0, 160))
            self.screen.blit(sh_panel, (sh_x, sh_y))
            pygame.draw.rect(self.screen, BLUE, (sh_x, sh_y, 320, 40), 1, border_radius=4)
            
            if p.shield_active:
                status_text = f"🛡️ โล่ทำงาน: {int(p.shield_timer)} วินาที"
                status_col = CYAN
            elif p.shield_cd > 0:
                status_text = f"🔄 Cooldown: {int(p.shield_cd)} วินาที"
                status_col = RED
            else:
                status_text = "✅ กด [Y] เพื่อใช้โล่ป้องกัน"
                status_col = LIGHT_GREEN
            
            sh_lbl = self.font_sm.render(status_text, True, status_col)
            self.screen.blit(sh_lbl, (sh_x + 12, sh_y + 8))

        # ── Difficulty indicator ──
        diff_col = {"Easy": LIGHT_GREEN, "Medium": YELLOW, "Hard": RED}.get(self.difficulty, WHITE)
        diff_txt = self.font_xs.render(f"[{DIFFICULTY_SETTINGS[self.difficulty]['label']}]", True, diff_col)
        self.screen.blit(diff_txt, (SCREEN_W - diff_txt.get_width() - 16, SCREEN_H - 28))

        # Admin Mode Watermark
        if p.is_admin:
            admin_lbl = self.font_md.render("ADMIN MODE: ACTIVATED", True, GOLD)
            self.screen.blit(admin_lbl, (SCREEN_W - admin_lbl.get_width() - 20, 150))
            # Flickering glow
            if random.random() > 0.8:
                pygame.draw.rect(self.screen, GOLD, (SCREEN_W - admin_lbl.get_width() - 25, 145, admin_lbl.get_width() + 10, 40), 2)

    # ═════════════════════════════════════
    #  SKILL SELECTION (EVERY 5 LEVELS)
    # ═════════════════════════════════════
    def _state_skill_select(self, events, dt):
        self._draw_starfield(dt)
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((10, 20, 30, 200))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "★ ปลดล็อกทักษะพิเศษ ★", self.font_lg, GOLD, 200)
        draw_text_centered(self.screen, f"ระดับ {self.player.level}: เลือกทักษะเพื่อเสริมความแข็งแกร่ง", self.font_md, WHITE, 280)

        mx, my = get_scaled_mouse_pos()
        
        # Skill List
        choices = [
            {"id": "double_jump", "name": "กระโดด 2 ครั้ง (Double Jump)", "desc": "กด Space หรือ W กลางอากาศเพื่อกระโดดอีกครั้ง", "icon_col": LIGHT_BLUE},
            {"id": "shield", "name": "โล่พลังงาน (Energy Shield)", "desc": "กด [Y] เพื่อเป็นอมตะชั่วคราว 8 วินาที (คูลดาวน์ 30 วิ)", "icon_col": BLUE},
        ]
        
        btn_rects = []
        for i, skill in enumerate(choices):
            rect = pygame.Rect(SCREEN_W // 2 - 400, 380 + i * 180, 800, 140)
            btn_rects.append((rect, skill))
            
            hov = rect.collidepoint(mx, my)
            base_color = (40, 50, 80) if not hov else (60, 70, 110)
            pygame.draw.rect(self.screen, base_color, rect, border_radius=15)
            pygame.draw.rect(self.screen, skill["icon_col"], rect, 3, border_radius=15)
            
            # Icon placeholder
            pygame.draw.circle(self.screen, skill["icon_col"], (rect.x + 70, rect.centery), 45)
            pygame.draw.circle(self.screen, WHITE, (rect.x + 70, rect.centery), 45, 2)
            
            # Text
            draw_text_fit(self.screen, skill["name"], self.font_md, WHITE, (rect.x + 140, rect.y + 35), rect.w - 160)
            draw_text_fit(self.screen, skill["desc"], self.font_sm, LIGHT_GREEN, (rect.x + 140, rect.y + 80), rect.w - 160)

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for rect, skill in btn_rects:
                    if rect.collidepoint(mx, my):
                        play_sound("pickup_weapon")
                        if skill["id"] == "double_jump":
                            self.player.has_double_jump = True
                            self.float_texts.append(FloatingText(self.player.x, self.player.y - 120, "ปลดล็อก: กระโดด 2 ชั้น!", LIGHT_BLUE, duration=3.0))
                        elif skill["id"] == "shield":
                            self.player.has_shield = True
                            self.float_texts.append(FloatingText(self.player.x, self.player.y - 120, "ปลดล็อก: โล่พลังงาน!", BLUE, duration=3.0))
                        
                        self.player.skill_points_pending -= 1
                        if self.player.skill_points_pending <= 0:
                            self.state = self.PLAYING
                        return
            elif e.type == pygame.KEYUP and e.key == pygame.K_ESCAPE:
                self.state = self.PLAYING

    # ═════════════════════════════════════
    #  SHOP (BETWEEN WAVES)
    # ═════════════════════════════════════
    def _state_shop(self, events, dt):
        self._draw_starfield(dt)
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((20, 30, 40, 180))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "★ ร้านค้าอัพเกรด ★", self.font_lg, GOLD, 120)
        draw_text_centered(self.screen, "เตรียมพร้อมสำหรับด่านถัดไป", self.font_sm, LIGHT_GREEN, 180)

        # Show current money
        money_txt = self.font_md.render(f"เงินของคุณ: ${self.player.money}", True, YELLOW)
        self.screen.blit(money_txt, (SCREEN_W // 2 - money_txt.get_width() // 2, 220))

        mx, my = get_scaled_mouse_pos()

        # Shop items (Medkit, plus locked weapons)
        items = [
            {"type": "stat", "title": "ยาพยาบาล (Medkit)", "desc": "เก็บไว้ใช้กด [H] ฟื้นฟู HP 50", "cost": 30, "id": "medkit"},
            {"type": "ammo", "title": "กระสุนปืนปัจจุบัน (Ammo Refill)", "desc": "+30 กระสุนสำหรับปืนที่ถือ สำหรับปืนทุกกระบอก $5 ต่อกระบอก", "cost": 20, "id": "current_gun"},
            {"type": "ammo", "title": "ลูกระเบิด (Grenades) x2", "desc": "เพิ่มลูกระเบิด +2 ลูก", "cost": 100, "id": "grenade"},
        ]
        
        # Add locked weapons to shop
        if "shotgun" not in self.player.unlocked_weapons:
            w = self.player.WEAPONS["shotgun"]
            items.append({"type": "gun", "title": "ปืนลูกซอง (Shotgun)", "desc": f"Dmg: {w['dmg']}x{w['pellets']} / กดปุ่ม 2", "cost": w["cost"], "id": "shotgun"})
        if "smg" not in self.player.unlocked_weapons:
            w = self.player.WEAPONS["smg"]
            items.append({"type": "gun", "title": "ปืนกลมือ (SMG)", "desc": f"รัวเร็ว Dmg: {w['dmg']} / กดปุ่ม 3", "cost": w["cost"], "id": "smg"})
        if "sniper" not in self.player.unlocked_weapons:
            w = self.player.WEAPONS["sniper"]
            items.append({"type": "gun", "title": "ปืนซุ่มยิง (Sniper)", "desc": f"รุนแรง Dmg: {w['dmg']} / กดปุ่ม 4", "cost": w["cost"], "id": "sniper"})

        # Draw item buttons (up to 6 items max)
        btn_rects = []
        for i, item in enumerate(items[:6]):
            bx = SCREEN_W // 2 - 250
            by = 260 + i * 75
            rect = pygame.Rect(bx, by, 500, 65)
            btn_rects.append((rect, item))
            
            # Hover effect
            col = (50, 60, 70) if not rect.collidepoint(mx, my) else (70, 80, 90)
            pygame.draw.rect(self.screen, col, rect, border_radius=8)
            pygame.draw.rect(self.screen, GOLD if self.player.money >= item['cost'] else GRAY, rect, 2, border_radius=8)
            
            draw_text_fit(self.screen, item["title"], self.font_sm, WHITE, (bx + 20, by + 10), 360)
            draw_text_fit(self.screen, item["desc"], self.font_xs, LIGHT_GREEN, (bx + 20, by + 35), 360)
            tc = self.font_sm.render(f"${item['cost']}", True, YELLOW if self.player.money >= item['cost'] else RED)
            self.screen.blit(tc, (bx + 400, by + 15))

        # Continue button
        btn_next = pygame.Rect(SCREEN_W // 2 - 130, 850, 260, 60)
        draw_button(self.screen, btn_next, "ไปด่านต่อไป ❯", self.font_md, btn_next.collidepoint(mx, my),
                    base_col=(20, 80, 150), hover_col=(40, 100, 180))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # Buy items
                for rect, item in btn_rects:
                    if rect.collidepoint(mx, my) and self.player.money >= item["cost"]:
                        play_sound("click")
                        self.player.money -= item["cost"]
                        if item["type"] == "stat":
                            if item["id"] == "medkit":
                                self.player.medkits += 1
                                self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "+1 Medkit", GREEN))
                        elif item["type"] == "gun":
                            self.player.unlocked_weapons.append(item["id"])
                            self.player.weapon = item["id"]
                            self.float_texts.append(FloatingText(self.player.x, self.player.y - 50, "+ปืนใหม่!", ORANGE))
                        elif item["type"] == "ammo":
                            if item["id"] == "current_gun":
                                # Buy +30 ammo for ALL gun weapons
                                for w_id, wdata in self.player.WEAPONS.items():
                                    if wdata["type"] == "gun" and w_id in self.player.unlocked_weapons:
                                        self.player.ammo[w_id] = self.player.ammo.get(w_id, 0) + 30
                            elif item["id"] == "grenade":
                                self.player.ammo["grenade"] = self.player.ammo.get("grenade", 0) + 2

                if btn_next.collidepoint(mx, my):
                    play_sound("click")
                    self._setup_stage()
                    self.state = self.PLAYING
                    self.wave_banner_timer = 3.0

    # ═════════════════════════════════════
    #  PAUSED
    # ═════════════════════════════════════
    def _state_paused(self, events, dt):
        # We can draw the background and player to show the game is still there
        # just don't update them with dt. For simplicity, we just freeze frame
        # by drawing a dark overlay over the old frame
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "PAUSED", self.font_lg, WHITE, SCREEN_H // 2 - 100)
        draw_text_centered(self.screen, "เกมหยุดชั่วคราว", self.font_sm, GRAY, SCREEN_H // 2 - 40)

        mx, my = get_scaled_mouse_pos()
        btn_resume = pygame.Rect(SCREEN_W // 2 - 130, SCREEN_H // 2, 260, 55)
        btn_setting = pygame.Rect(SCREEN_W // 2 - 130, SCREEN_H // 2 + 75, 260, 55)
        btn_menu = pygame.Rect(SCREEN_W // 2 - 130, SCREEN_H // 2 + 150, 260, 55)

        draw_button(self.screen, btn_resume, "เล่นต่อ (Resume)", self.font_md, btn_resume.collidepoint(mx, my))
        draw_button(self.screen, btn_setting, "ตั้งค่า (Settings)", self.font_md, btn_setting.collidepoint(mx, my))
        draw_button(self.screen, btn_menu, "กลับเมนูหลัก (Main Menu)", self.font_md, btn_menu.collidepoint(mx, my),
                    base_col=(180, 40, 40), hover_col=(220, 60, 60))

        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.state = self.PLAYING
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_resume.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.PLAYING
                elif btn_setting.collidepoint(mx, my):
                    play_sound("click")
                    self.prev_state = self.state
                    self.state = self.SETTINGS
                elif btn_menu.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.MAIN_MENU

    # ═════════════════════════════════════
    #  GAME OVER
    # ═════════════════════════════════════
    def _state_game_over(self, events, dt):
        self._draw_starfield(dt)
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((120, 0, 0, 100))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "GAME  OVER", self.font_lg, RED, 220)
        draw_text_centered(self.screen, "คุณถูกซอมบี้กิน!", self.font_md, ORANGE, 300)

        if self.player:
            p = self.player
            info = f"Kills: {p.kills}   EXP: {p.exp}   Money: ${p.money}"
            draw_text_centered(self.screen, info, self.font_sm, GRAY, 360)
            rescue_info = f"ช่วยผู้คน: {p.rescued_npcs}/{len(self.npcs)} คน"
            draw_text_centered(self.screen, rescue_info, self.font_sm, CYAN, 400)

        mx, my = get_scaled_mouse_pos()
        btn_menu = pygame.Rect(SCREEN_W // 2 - 130, 460, 260, 60)
        draw_button(self.screen, btn_menu, "กลับเมนูหลัก", self.font_md, btn_menu.collidepoint(mx, my))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_menu.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.MAIN_MENU

    # ═════════════════════════════════════
    #  VICTORY
    # ═════════════════════════════════════
    def _state_victory(self, events, dt):
        self._draw_starfield(dt)
        # Golden overlay
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((40, 40, 0, 80))
        self.screen.blit(ov, (0, 0))

        draw_text_centered(self.screen, "★  VICTORY  ★", self.font_lg, GOLD, 160)
        draw_text_centered(self.screen, "คุณกำจัดซอมบี้ทั้งหมดแล้ว!", self.font_md, YELLOW, 230)
        draw_text_centered(self.screen, "ผู้กล้าได้ปกป้องโลกสำเร็จ!", self.font_md, LIGHT_GREEN, 280)

        if self.player:
            p = self.player
            stats = [
                f"Kills: {p.kills}   EXP: {p.exp}   Money: ${p.money}",
                f"ช่วยผู้คน: {p.rescued_npcs}/{len(self.npcs)} คน",
                f"ระดับความยาก: {DIFFICULTY_SETTINGS[self.difficulty]['label']}",
            ]
            for i, s in enumerate(stats):
                draw_text_centered(self.screen, s, self.font_sm, WHITE, 340 + i * 36)

        mx, my = get_scaled_mouse_pos()
        btn_menu = pygame.Rect(SCREEN_W // 2 - 130, 480, 260, 60)
        draw_button(self.screen, btn_menu, "กลับเมนูหลัก", self.font_md, btn_menu.collidepoint(mx, my))

        btn_retry = pygame.Rect(SCREEN_W // 2 - 130, 560, 260, 55)
        draw_button(self.screen, btn_retry, "เล่นอีกครั้ง", self.font_md, btn_retry.collidepoint(mx, my),
                    base_col=(30, 100, 50), hover_col=(50, 160, 80))

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if btn_menu.collidepoint(mx, my):
                    play_sound("click")
                    self.state = self.MAIN_MENU
                elif btn_retry.collidepoint(mx, my):
                    play_sound("click")
                    self._start_game()


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    game = GameManager()
    game.run()