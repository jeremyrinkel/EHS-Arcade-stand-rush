"""STEEL BALL RUN: STAND RUSH — ARCADE UPGRADE — Pygame edition.
Python 3.10+ and Pygame 2.5+ required.
No external image/audio assets required.
"""
import random
import math
import time
import sys
import json
import asyncio
import os
IS_BROWSER = sys.platform == "emscripten"
from pathlib import Path

# Chess mode uses python-chess for complete legal move handling.  Try to
# install it automatically so the extra menu game works without a separate
# setup step.  If the computer is offline, the chess screen still opens and
# explains the one-time install command instead of silently doing nothing.
try:
    import chess
except ImportError:
    chess = None
    if not IS_BROWSER:
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "python-chess"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=45)
            import chess
        except Exception:
            chess = None

try:
    import pygame
except ImportError:
    print("Pygame is not installed in this Python environment.")
    print("Install it with: py -m pip install pygame")
    try:
        input("Press Enter to close...")
    except EOFError:
        pass
    raise SystemExit(1)

WIDTH, HEIGHT = 1120, 740
RACE_LENGTH = 20000.0       # slightly longer four-stage route with more room to race
FPS_MS = 30
LANE_Y = [355, 425, 495, 565]

INK = "#1d202b"
PAPER = "#f6ead0"
GOLD = "#efb951"
MUTED = "#b4b6b2"
RED = "#ca5559"
TEAL = "#51b9a8"
PURPLE = "#a17ada"
BLUE = "#6d9ed3"
WHITE = "#ffffff"

# Percentage weights total 100%. These are the relative odds when a Stand is awakened.
STANDS = [
    {"name":"Tusk Act 1", "chance":16, "color":"#65aeea", "speed":1, "stamina":-1.0, "combat":1.20, "defense":0,
     "buff":"Nail shots deal extra damage", "nerf":"Stamina recovers more slowly", "ability":"Nail shot: fire a focused, long-range nail projectile."},
    {"name":"Tusk Act 2", "chance":0, "color":"#65b9ee", "speed":5, "stamina":-0.5, "combat":1.45, "defense":3,
     "buff":"Curving, tunnelling nail projectiles", "nerf":"Higher stamina cost", "ability":"Curving nails: spiral shots chase rivals and drill through obstacles."},
    {"name":"Tusk Act 3", "chance":0, "color":"#4ba4dc", "speed":9, "stamina":-1.0, "combat":1.75, "defense":6,
     "buff":"Spatial nail holes and stronger projectiles", "nerf":"More costly special", "ability":"Spatial nail shot: open a brief hole in space and strike across lanes."},
    {"name":"Tusk Act 4", "chance":0, "color":"#4f9bd9", "speed":14, "stamina":-2.0, "combat":2.20, "defense":10,
     "buff":"Infinite Rotation; breaks D4C Love Train", "nerf":"Very high stamina drain", "ability":"Infinite Rotation: deliver a devastating Golden Spin attack that pierces Love Train."},
    {"name":"Scary Monsters", "chance":12, "color":"#a9b95c", "speed":8, "stamina":-2.5, "combat":1.10, "defense":-8,
     "buff":"Excellent racing speed", "nerf":"Lower maximum health", "ability":"Dinosaur rush: burst forward and knock nearby rivals aside."},
    {"name":"D4C", "chance":9, "color":"#d889b4", "speed":4, "stamina":-1.5, "combat":1.05, "defense":0,
     "buff":"Dimensional dash, temporary intangibility, and a parallel-world strike", "nerf":"Sprint stamina drains faster", "ability":"D4C: cross into a parallel world, dash forward, evade attacks, and strike nearby rivals."},
    {"name":"Ball Breaker", "chance":8, "color":"#d9c28a", "speed":-2, "stamina":-0.5, "combat":1.75, "defense":4,
     "buff":"Outstanding Spin damage", "nerf":"Slightly lower racing speed", "ability":"Golden Spin: unleash a high-impact attack on nearby rivals."},
    {"name":"Cream Starter", "chance":8, "color":"#e79cba", "speed":0, "stamina":5, "combat":0.75, "defense":5,
     "buff":"Recovery and endurance", "nerf":"Lower direct damage", "ability":"Restorative spray: patch yourself up and restore stamina."},
    {"name":"Mandom", "chance":6, "color":"#c0a2e5", "speed":1, "stamina":1.5, "combat":0.90, "defense":2,
     "buff":"Can recover from a bad moment", "nerf":"Lower damage", "ability":"Six-second rewind: return to an earlier race position and recover."},
    {"name":"Catch the Rainbow", "chance":5, "color":"#78c7d2", "speed":6, "stamina":-0.5, "combat":0.95, "defense":8,
     "buff":"Fast and resilient", "nerf":"Less effective attacks", "ability":"Rain veil: glide through the storm with a short guard and speed surge."},
    {"name":"In a Silent Way", "chance":5, "color":"#e0a457", "speed":0, "stamina":0.5, "combat":1.25, "defense":0,
     "buff":"Powerful sound-based counters", "nerf":"No large speed bonus", "ability":"Sound trap: stun and knock back rivals caught in range."},
    {"name":"Hey Ya!", "chance":5, "color":"#f0cb75", "speed":3, "stamina":7, "combat":0.80, "defense":0,
     "buff":"Great endurance and morale", "nerf":"Low combat damage", "ability":"Motivation: restore stamina and focus into a strong sprint."},
    {"name":"Ticket to Ride", "chance":3, "color":"#f0e6dd", "speed":0, "stamina":1.5, "combat":0.85, "defense":18,
     "buff":"Powerful protective blessing", "nerf":"Less offensive power", "ability":"Blessing: raise a temporary shield against incoming attacks."},
    {"name":"Oh! Lonesome Me", "chance":5, "color":"#b88e69", "speed":4, "stamina":1.0, "combat":1.05, "defense":5,
     "buff":"Rope mastery and evasive movement", "nerf":"Shorter range than heavy Stands", "ability":"Rope trap: snag a rival, slow them, and strike through the lariat."},
    {"name":"Soft & Wet", "chance":8, "color":"#7de3df", "speed":2, "stamina":1.5, "combat":1.15, "defense":2,
     "buff":"Plunder bubbles steal an opponent's momentum", "nerf":"Bubbles need a nearby target to plunder", "ability":"Plunder bubbles: steal a rival's speed briefly, then turn it into your own burst."},
    {"name":"Soft & Wet: Go Beyond", "chance":0, "color":"#a9f4ef", "speed":8, "stamina":-2.0, "combat":2.25, "defense":5,
     "buff":"Unseeable spin bubbles pierce defenses", "nerf":"Powerful shot has a longer cooldown", "ability":"Go Beyond: fire an impossible spin bubble that pierces defenses and heavily damages a rival or boss."},
    {"name":"Wonder of U", "chance":0, "color":"#a88be8", "speed":70, "stamina":100, "combat":50, "defense":100,
     "buff":"Calamity crushes anyone who attacks you", "nerf":"None — secret overpowered Stand", "ability":"Calamity: attackers are crushed instantly; K crushes nearby rivals."},
    {"name":"Civil War", "chance":2, "color":"#d9d6e8", "speed":1, "stamina":-1, "combat":1.45, "defense":6,
     "buff":"Guilt weighs down nearby opponents", "nerf":"Moderate sprint drain", "ability":"Civil War: manifest a guilt-bound shroud that slows and damages nearby rivals."},
    {"name":"Chocolate Disco", "chance":2, "color":"#c5a0d9", "speed":0, "stamina":0, "combat":1.3, "defense":4,
     "buff":"Grid-based precision strike", "nerf":"Shorter effective range", "ability":"Chocolate Disco: strike rivals caught in your tactical grid."},
    {"name":"Killer Queen", "chance":2, "color":"#e7a6ad", "speed":1, "stamina":-1, "combat":1.55, "defense":2,
     "buff":"Explosive pressure burst", "nerf":"Small stamina cost", "ability":"Killer Queen: tag nearby rivals with a bomb and detonate it in a burst."},
    {"name":"Paisley Park", "chance":2, "color":"#7fc8c0", "speed":5, "stamina":4, "combat":0.8, "defense":8,
     "buff":"Finds a safe route and restores endurance", "nerf":"Low direct damage", "ability":"Paisley Park: guide yourself through a safe shortcut and restore stamina."},
    {"name":"Born This Way", "chance":2, "color":"#a8c9ed", "speed":3, "stamina":-0.5, "combat":1.35, "defense":7,
     "buff":"Freezing gust slows enemies", "nerf":"Moderate cooldown", "ability":"Born This Way: unleash a freezing wind that slows and stuns rivals."},
    {"name":"Speed King", "chance":2, "color":"#d8b34f", "speed":6, "stamina":-2, "combat":1.1, "defense":1,
     "buff":"Stores heat for a burst of speed", "nerf":"Consumes stamina", "ability":"Speed King: release stored heat as a rapid sprint and damage pulse."},
    {"name":"The World (Alternate Universe)", "chance":0, "color":"#e7c84f", "speed":10, "stamina":-2, "combat":2.0, "defense":8,
     "buff":"Time stop, heavy strikes, and a brief safe reposition", "nerf":"Long cooldown; time stop costs stamina", "ability":"THE WORLD: stop time briefly, strike nearby rivals, or deal heavy damage to a boss."},
]

# Expanded manga catalogue: regular Stands enter the Corpse Part pool; signature endgame
# Stands are deliberately excluded from random rolls and awarded by story challenges.
_EXTRA_STANDS = [
    # Part 7: Steel Ball Run
    ("Wired", "#8a9aaf", "control", False),
    ("Tomb of the Boom", "#c58b63", "offense", False),
    ("Boku no Rhythm wo Kiitekure", "#e58c70", "offense", False),
    ("Sugar Mountain", "#8bc8a5", "support", False),
    ("Tubular Bells", "#d9b6a0", "control", False),
    ("20th Century Boy", "#9ca5b4", "defense", False),
    ("Tattoo You!", "#d5a6b8", "offense", False),
    # Part 8: JoJolion
    ("King Nothing", "#c9a86a", "control", False),
    ("California King Bed", "#9b83c8", "control", False),
    ("Paper Moon King", "#a8d7d2", "control", False),
    ("Nut King Call", "#d1a16d", "support", False),
    ("Walking Heart", "#c97f92", "offense", False),
    ("Doobie Wah!", "#b4d1d7", "control", False),
    ("Schott Key No. 1", "#8e9fba", "offense", False),
    ("Schott Key No. 2", "#a6b8ca", "offense", False),
    ("Vitamin C", "#d8c16a", "control", False),
    ("Milagro Man", "#c2a4d9", "support", False),
    ("Blue Hawaii", "#76b9d1", "control", False),
    ("Brain Storm", "#b2b6c2", "offense", False),
    ("Ozon Baby", "#a6c7c9", "control", False),
    ("Doctor Wu", "#a9a9b6", "evasion", False),
    ("I Am a Rock", "#8a9b87", "control", False),
    ("Fun Fun Fun", "#d5b2a0", "control", False),
    ("Les Feuilles", "#9bbd83", "speed", False),
    ("Love Love Deluxe", "#c98caa", "control", False),
    ("Doggy Style", "#e0b98d", "defense", False),
    ("Space Trucking", "#9bb4cf", "evasion", False),
    ("Killer Queen (JoJolion)", "#d7a3b7", "offense", False),
    # Part 9: The JoJoLands (ongoing manga; this roster can be expanded as new Stands appear)
    ("November Rain", "#6b879d", "control", False),
    ("Smooth Operators", "#d0a7bd", "support", False),
    ("The Hustle", "#b88461", "defense", False),
    ("The Matte Kudasai", "#a8c3d0", "support", False),
    ("Bigmouth Strikes Again", "#9b9fae", "offense", False),
    ("Bags' Groove", "#c5a8d8", "control", False),
    ("Cat Size", "#d6bd7e", "defense", False),
    ("Glory Days", "#a8a0b8", "offense", False),
    ("West End Girl", "#cb9a9e", "control", False),
    ("200 Balloons", "#d5b3cf", "support", False),
    ("Lyin' Eyes", "#9db9a2", "evasion", False),
    # Rare / powerful story unlocks
    ("D4C: Love Train", "#e6b3c9", "legendary", True),
    ("Soft & Wet: Go Beyond", "#9cf0e8", "legendary", True),
]
for _name, _color, _effect, _special in _EXTRA_STANDS:
    if _name not in {st["name"] for st in STANDS}:
        STANDS.append({
            "name": _name, "chance": 0 if _special else 1, "color": _color,
            "speed": 2 if _effect in ("speed", "evasion") else 0,
            "stamina": 2 if _effect == "support" else -0.5,
            "combat": 1.75 if _special else (1.18 if _effect == "offense" else 0.95),
            "defense": 12 if _effect == "defense" else (5 if _effect == "support" else 1),
            "buff": "Rare manga ability with a distinct tactical effect" if _special else f"{_effect.title()}-focused Stand technique",
            "nerf": "Story challenge required" if _special else "Balanced cooldown and stamina cost",
            "ability": f"{_name}: use K to activate its { _effect } technique.",
            "effect_type": _effect,
        })
# The archive and unlock validation are generated from this complete catalogue.
STAND_BY_NAME = {st["name"]: st for st in STANDS}

# Manga-accurate affinities are bonuses only; Corpse Part awakenings are randomized.
# Every character can awaken any eligible Stand from the weighted pool.
STAND_AFFINITIES = {
    "Johnny Joestar": "Tusk Act 1", "Gyro Zeppeli": "Ball Breaker",
    "Diego Brando": "Scary Monsters", "Hot Pants": "Cream Starter",
    "Mountain Tim": "Oh! Lonesome Me", "Funny Valentine": "D4C",
    "Joshu Higashikata": "Soft & Wet",
}
STAGE_BOSSES = [
    {"name": "Ringo Roadagain", "subtitle": "MANDOM — THE HIGH NOON DUEL", "hp": 560, "color": "#c0a2e5", "stand": "Mandom"},
    {"name": "Wekapipo", "subtitle": "LEFT-SIDE ATTACK — THE SPIN WARRIOR", "hp": 680, "color": "#a8b4c9", "stand": "Wrecking Ball"},
    {"name": "Blackmore", "subtitle": "CATCH THE RAINBOW — THE RAIN HUNTER", "hp": 820, "color": "#78c7d2", "stand": "Catch the Rainbow"},
    {"name": "Funny Valentine", "subtitle": "DIRTY DEEDS DONE DIRT CHEAP — D4C: LOVE TRAIN", "hp": 1000, "color": "#d65b83", "stand": "D4C"},
]
STAGE_NAMES = ["THE OPEN RANGE", "RED ROCK PASS", "ROCKY BADLANDS", "THE FINAL FRONTIER"]
ALT_STAGE_BOSSES = [
    {"name":"Pocoloco (AU Trial)", "subtitle":"HEY YA! — FATE FAVORS THE BOLD", "hp":600, "color":"#9c7ad3", "stand":"Hey Ya!"},
    {"name":"Parallel Diego", "subtitle":"SCARY MONSTERS — THE DINO RIDER", "hp":740, "color":"#a9b95c", "stand":"Scary Monsters"},
    {"name":"AU Gyro", "subtitle":"THE SPIN THAT CROSSES WORLDS", "hp":880, "color":"#e0c06e", "stand":"Ball Breaker"},
    {"name":"Diego Brando (AU)", "subtitle":"THE WORLD — TIME STOPS HERE", "hp":1250, "color":"#e7c84f", "stand":"The World (Alternate Universe)"},
]
ALT_STAGE_NAMES = ["MIRRORING BADLANDS", "PARALLEL RED ROCKS", "THE SPLIT FRONTIER", "WORLD OVER HEAVEN'S SHADOW"]
BOSS_MAX_HP = 1000.0
CORPSE_PART_CHANCE = 38   # each regular Corpse Part site has an independent chance
PALM_POSITIONS = [3800, 8400, 13200, 17800]
PART_NAMES = ["Saint's Left Arm", "Saint's Right Arm", "Saint's Left Eye", "Saint's Right Eye", "Saint's Heart", "Saint's Spine"]


# Original, shape-drawn rider costumes use distinct color palettes and accessories
# instead of stretching low-resolution artwork. Colors are manga-inspired interpretations.
CHARACTER_LOOKS = {
    "Johnny Joestar": {"shirt":"#72c3df", "hair":"#d6b879", "headgear":"#78d5e4", "accent":"#f4e5bf", "detail":"#f6e7c6"},
    "Gyro Zeppeli": {"shirt":"#39bba5", "hair":"#d9bd87", "headgear":"#58c9d6", "accent":"#efca4d", "detail":"#e8f0dd"},
    "Diego Brando": {"shirt":"#a8c8a6", "hair":"#e5cb83", "headgear":"#436f67", "accent":"#d6e0c9", "detail":"#e7d18c"},
    "Mountain Tim": {"shirt":"#c69b67", "hair":"#79523d", "headgear":"#51382e", "accent":"#dfbd7b", "detail":"#f1dfc0"},
    "Hot Pants": {"shirt":"#b75a59", "hair":"#b89a7a", "headgear":"#ece2d7", "accent":"#e7c9aa", "detail":"#f4e6da"},
    "Sandman": {"shirt":"#dfbb70", "hair":"#48362c", "headgear":"#a85e48", "accent":"#f3e0b5", "detail":"#8b403b"},
    "Pocoloco": {"shirt":"#b99ad9", "hair":"#392c26", "headgear":"#e9d5f1", "accent":"#7f9b91", "detail":"#f4e6c9"},
    "Nikolai": {"shirt":"#849c70", "hair":"#5d4437", "headgear":"#4c6349", "accent":"#d6c48e", "detail":"#e6d9bd"},
    "Marco": {"shirt":"#b97c6a", "hair":"#483b35", "headgear":"#6e4a43", "accent":"#dfb28c", "detail":"#ead8c7"},
    "Diego Brando (AU)": {"shirt":"#d7bd58", "hair":"#c5c4b9", "headgear":"#e6d58b", "accent":"#f1e7b1", "detail":"#f7f0d0"},
    "Parallel Diego": {"shirt":"#d8c35d", "hair":"#d9d5c9", "headgear":"#e8d991", "accent":"#fff0a4", "detail":"#f7efcf"},
    "AU Gyro": {"shirt":"#d0a85c", "hair":"#d7c8a0", "headgear":"#e7d6b0", "accent":"#f4d66b", "detail":"#f7e8bd"},
    "Pocoloco (AU Trial)": {"shirt":"#8e6fba", "hair":"#2c211f", "headgear":"#e8d8f0", "accent":"#d5b6f0", "detail":"#f6e8d5"},
}
HORSE_COATS = {
    "Johnny Joestar":"#d7d9d3", "Gyro Zeppeli":"#9a5634", "Diego Brando":"#48413d",
    "Mountain Tim":"#b98a4f", "Hot Pants":"#68483d", "Sandman":"#c8a16f",
    "Pocoloco":"#a66e45", "Nikolai":"#6a4939", "Marco":"#bd895e",
    "Diego Brando (AU)":"#514c48", "Parallel Diego":"#55504a",
    "AU Gyro":"#9b5b36", "Pocoloco (AU Trial)":"#a66e45",
}

SAVE_FILE = Path(__file__).with_name("stand_rush_progress.json")

def browser_load_progress():
    if not IS_BROWSER:
        return None
    try:
        from platform import window
        raw = window.localStorage.getItem("stand_rush_progress_v1")
        return json.loads(str(raw)) if raw else None
    except Exception:
        return None

def browser_save_progress(data):
    if not IS_BROWSER:
        return False
    try:
        from platform import window
        window.localStorage.setItem("stand_rush_progress_v1", json.dumps(data))
        return True
    except Exception:
        return False


def load_progress_data():
    defaults = {"unlocked_stands": [], "selected_stand": None, "wins_in_row": 0,
                "total_wins": 0, "has_corpse_part": False, "wonder_unlocked": False,
                "total_spin_tokens": 0, "spin_ability_unlocked": False,
                "last_character": None}
    try:
        if IS_BROWSER or SAVE_FILE.exists():
            loaded = browser_load_progress() if IS_BROWSER else json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                defaults.update(loaded)
    except (OSError, ValueError, TypeError):
        pass
    defaults["unlocked_stands"] = [n for n in defaults.get("unlocked_stands", [])
                                    if n in {st["name"] for st in STANDS}]
    if defaults.get("wonder_unlocked") and "Wonder of U" not in defaults["unlocked_stands"]:
        defaults["unlocked_stands"].append("Wonder of U")
    return defaults


def weighted_stand(exclude_names=None):
    """Choose an unowned random-pool Stand first; duplicates are allowed only
    after every Stand in the normal random pool has been collected.
    Zero-chance evolution/secret Stands remain progression-gated.
    """
    exclude_names = set(exclude_names or ())
    pool = [st for st in STANDS if st["chance"] > 0 and st["name"] not in exclude_names]
    # Do not repeat a normal random Stand while any Stand in the overall
    # collection is still missing. Zero-chance secret/evolution Stands remain
    # governed by their own progression requirements.
    if not pool:
        normal_pool = [st for st in STANDS if st["chance"] > 0]
        if len(exclude_names.intersection(st["name"] for st in normal_pool)) < len(normal_pool):
            return None
        pool = normal_pool
    total = sum(st["chance"] for st in pool)
    roll = random.uniform(0, total)
    upto = 0
    for stand in pool:
        upto += stand["chance"]
        if roll <= upto:
            return stand.copy()
    return pool[-1].copy()


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def hexmix(a, b, t):
    a = tuple(int(a[i:i+2], 16) for i in (1, 3, 5))
    b = tuple(int(b[i:i+2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))



class PygameCanvas:
    """Small Tk-Canvas-compatible drawing adapter backed by Pygame primitives."""
    def __init__(self, surface):
        self.surface = surface
        self._fonts = {}

    @staticmethod
    def _color(value, default=(0, 0, 0)):
        if value is None or value == "" or value == "":
            return default
        if isinstance(value, (tuple, list)):
            return tuple(value[:3])
        if isinstance(value, str) and value.startswith("#") and len(value) == 7:
            try:
                return tuple(int(value[i:i+2], 16) for i in (1, 3, 5))
            except ValueError:
                return default
        try:
            return pygame.Color(value)[:3]
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _int_points(coords):
        return [(int(round(coords[i])), int(round(coords[i+1]))) for i in range(0, len(coords)-1, 2)]

    def delete(self, tag):
        if tag == "all":
            self.surface.fill((217, 166, 109))

    def _rect(self, x1, y1, x2, y2):
        left, right = sorted((int(round(x1)), int(round(x2))))
        top, bottom = sorted((int(round(y1)), int(round(y2))))
        return pygame.Rect(left, top, max(1, right-left), max(1, bottom-top))

    def create_rectangle(self, x1, y1, x2, y2, fill="", outline="", width=1, stipple=None, **kwargs):
        rect = self._rect(x1, y1, x2, y2)
        if fill:
            col = self._color(fill)
            if stipple:
                # Tk stipple is approximated by a soft translucent overlay.
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((*col, 132))
                self.surface.blit(overlay, rect.topleft)
            else:
                pygame.draw.rect(self.surface, col, rect)
        if outline and width > 0:
            pygame.draw.rect(self.surface, self._color(outline), rect, max(1, int(width)))

    def create_oval(self, x1, y1, x2, y2, fill="", outline="", width=1, **kwargs):
        rect = self._rect(x1, y1, x2, y2)
        if fill:
            pygame.draw.ellipse(self.surface, self._color(fill), rect)
        if outline and width > 0:
            pygame.draw.ellipse(self.surface, self._color(outline), rect, max(1, int(width)))

    def create_polygon(self, *coords, fill="", outline="", width=1, **kwargs):
        pts = self._int_points(coords)
        if len(pts) < 3:
            return
        if fill:
            pygame.draw.polygon(self.surface, self._color(fill), pts)
        if outline and width > 0:
            pygame.draw.polygon(self.surface, self._color(outline), pts, max(1, int(width)))

    def create_line(self, *coords, fill="#000000", width=1, smooth=False, dash=None, **kwargs):
        pts = self._int_points(coords)
        if len(pts) < 2:
            return
        col = self._color(fill)
        if dash and len(pts) == 2:
            a, b = pts
            dx, dy = b[0]-a[0], b[1]-a[1]
            length = math.hypot(dx, dy)
            if length <= 0:
                return
            ux, uy = dx/length, dy/length
            pos = 0.0
            pattern = list(dash) if isinstance(dash, (list, tuple)) else [5, 4]
            if not pattern:
                pattern = [5, 4]
            index = 0
            while pos < length:
                end = min(length, pos + max(1, pattern[index % len(pattern)]))
                if index % 2 == 0:
                    pygame.draw.line(self.surface, col,
                        (round(a[0]+ux*pos), round(a[1]+uy*pos)),
                        (round(a[0]+ux*end), round(a[1]+uy*end)), max(1, int(width)))
                pos = end
                index += 1
        else:
            pygame.draw.lines(self.surface, col, False, pts, max(1, int(width)))

    def create_arc(self, x1, y1, x2, y2, start=0, extent=90, style="arc", outline="#000000", width=1, **kwargs):
        rect = self._rect(x1, y1, x2, y2)
        if style == "arc" and outline:
            # Pygame's arc angles are radians; reverse signs to approximate Tk's convention.
            a0 = math.radians(-float(start + extent))
            a1 = math.radians(-float(start))
            pygame.draw.arc(self.surface, self._color(outline), rect, a0, a1, max(1, int(width)))

    def create_text(self, x, y, text="", anchor="center", fill="#000000", font=("Arial", 12), width=None, **kwargs):
        if text is None:
            return
        font_spec = font if isinstance(font, (tuple, list)) else ("Arial", 12)
        family = str(font_spec[0]) if font_spec else "Arial"
        try:
            size = max(8, int(float(font_spec[1])))
        except (IndexError, TypeError, ValueError):
            size = 12
        bold = any(str(item).lower() in ("bold", "heavy") for item in font_spec[2:])
        italic = any(str(item).lower() == "italic" for item in font_spec[2:])
        key = (family, size, bold, italic)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont(family, size, bold=bold, italic=italic)
        fnt = self._fonts[key]
        col = self._color(fill)
        max_width = int(width) if width else None
        lines = []
        for raw_line in str(text).split("\n"):
            if not max_width or fnt.size(raw_line)[0] <= max_width:
                lines.append(raw_line)
                continue
            words = raw_line.split(" ")
            current = ""
            for word in words:
                candidate = word if not current else current + " " + word
                if current and fnt.size(candidate)[0] > max_width:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            lines.append(current)
        rendered = [fnt.render(line, True, col) for line in lines]
        line_height = fnt.get_linesize()
        total_h = max(line_height, line_height * len(rendered))
        max_w = max((img.get_width() for img in rendered), default=0)
        block = pygame.Surface((max(1, max_w), max(1, total_h)), pygame.SRCALPHA)
        for i, img in enumerate(rendered):
            block.blit(img, (0, i*line_height))
        rect = block.get_rect()
        anchor = str(anchor).lower()
        if anchor in ("w", "nw", "sw"):
            rect.left = int(round(x))
        elif anchor in ("e", "ne", "se"):
            rect.right = int(round(x))
        else:
            rect.centerx = int(round(x))
        if anchor in ("n", "nw", "ne"):
            rect.top = int(round(y))
        elif anchor in ("s", "sw", "se"):
            rect.bottom = int(round(y))
        else:
            rect.centery = int(round(y))
        self.surface.blit(block, rect)



class Racer:
    def __init__(self, name, color, lane, progress, speed, player=False):
        self.name, self.color, self.lane, self.progress, self.speed = name, color, lane, float(progress), speed
        self.player = player
        self.stand = None
        self.hp = 100.0
        self.stamina = 100.0
        self.cooldown = random.uniform(1.2, 3.2)
        self.stun = 0.0
        self.knocked = 0.0
        self.out = False
        self.out_timer = 0.0
        self.ally = False
        self.parts = 0
        self.last_palm = -1
        self.dodge = 0.0
        self.plundered = 0.0
        self.ai_lane_timer = random.uniform(1.8, 3.8)

    def max_hp(self):
        if self.stand and self.stand["name"] == "Scary Monsters": return 82
        return 100

    def stat_speed(self):
        return self.stand["speed"] if self.stand else 0

    def stat_damage(self):
        return self.stand["combat"] if self.stand else 1.0


class SteelBallRunGame:
    def __init__(self):
        # Audio is generated locally: no copyrighted anime soundtrack or external files needed.
        try:
            pygame.mixer.pre_init(22050, -16, 1, 512)
        except Exception:
            pass
        pygame.init()
        pygame.display.set_caption("STEEL BALL RUN: STAND RUSH")
        # Start in a predictable windowed mode. Some Windows/SDL display
        # drivers return a black surface for FULLSCREEN | SCALED. Fullscreen
        # is enabled later using SDL's fullscreen toggle, which preserves the
        # existing 1120x740 drawing surface and avoids a broken mode reset.
        self.fullscreen = False
        # Keep drawing on a fixed logical surface. The actual window may use
        # a different desktop resolution in fullscreen; scaling happens only
        # when presenting the finished frame.
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.game_surface = pygame.Surface((WIDTH, HEIGHT)).convert()
        self.game_surface.fill((16, 21, 32))
        self.clock = pygame.time.Clock()
        self.canvas = PygameCanvas(self.game_surface)
        self.audio_enabled = False
        self.music_state = None
        self.music_files = {}
        self.sfx = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512)
            self.audio_enabled = pygame.mixer.get_init() is not None
            if IS_BROWSER:
                self.music_files = {m: str(Path(__file__).with_name('audio') / (m + '.wav'))
                                    for m in ('title', 'race', 'boss', 'chess', 'victory')}
                # Same original effect generator; no large music synthesis at startup.
                for name, spec in {
                    'select': (660, .10, 'sine'), 'move': (420, .07, 'triangle'),
                    'attack': (115, .20, 'saw'), 'stand': (880, .24, 'sine'),
                    'dash': (250, .18, 'noise'), 'hit': (82, .16, 'noise'),
                    'check': (740, .14, 'triangle'), 'win': (990, .35, 'sine'),
                }.items():
                    self.sfx[name] = self._make_effect(*spec)
            else:
                self._prepare_audio()
        except (pygame.error, OSError, ValueError):
            self.audio_enabled = False
        self.keys = set()
        self.stand_sprite_images = {}
        try:
            atlas = pygame.image.load(str(Path(__file__).with_name("stand_sprites.png"))).convert_alpha()
            sprite_names = ["Tusk Act 1", "Tusk Act 2", "Tusk Act 3", "Tusk Act 4", "Scary Monsters", "D4C", "Ball Breaker", "Cream Starter", "Mandom", "Catch the Rainbow", "Soft & Wet", "Wonder of U", "Civil War", "Killer Queen", "PART 7", "PART 8"]
            for i, sprite_name in enumerate(sprite_names):
                self.stand_sprite_images[sprite_name] = atlas.subsurface(pygame.Rect((i % 4) * 96, (i // 4) * 128, 96, 128)).copy()
        except (pygame.error, OSError):
            self.stand_sprite_images = {}
        self.last_tick = time.perf_counter()
        self.last_lane_move = 0
        self.running = True
        self.save_data = load_progress_data()
        self.unlocked_stands = list(self.save_data.get("unlocked_stands", []))
        self.selected_stand_name = self.save_data.get("selected_stand")
        if self.selected_stand_name not in self.unlocked_stands:
            self.selected_stand_name = None
        self.wins_in_row = int(self.save_data.get("wins_in_row", 0))
        self.total_wins = int(self.save_data.get("total_wins", 0))
        self.has_ever_collected_part = bool(self.save_data.get("has_corpse_part", False))
        self.total_spin_tokens = max(0, int(self.save_data.get("total_spin_tokens", 0)))
        self.spin_ability_unlocked = bool(self.save_data.get("spin_ability_unlocked", False)) or self.total_spin_tokens >= 5
        self.stand_menu_index = 0
        self.stand_scroll_offset = 0
        self.selected_character_name = self.save_data.get("selected_character") or self.save_data.get("last_character")
        if self.selected_character_name not in CHARACTER_LOOKS:
            self.selected_character_name = "Johnny Joestar"
        self.character_menu_index = list(CHARACTER_LOOKS).index(self.selected_character_name)
        self.unlock_notice = ""
        self.alternate_universe = False
        self.show_help = False
        self.settings_index = 0
        self.settings = {"difficulty": "Normal", "horse_speed": "Fast", "hazards": "On", "controls": "Arrows"}
        self.reset()
        self.chess_board = chess.Board() if chess else None
        self.chess_message = "Your move — White plays first."
        self.chess_last_move = None
        self.chess_selected = None
        self.chess_thinking = False
        self.state = "title"
        self.last_tick = time.perf_counter()
        self._set_music_for_state(force=True)

    def _prepare_audio(self):
        """Create original western-adventure game music and effects at runtime."""
        if not self.audio_enabled:
            return
        self.music_files = {name: self._write_music_track(name) for name in
                            ("title", "race", "boss", "chess", "victory")}
        for name, spec in {
            "select": (660, 0.10, "sine"), "move": (420, 0.07, "triangle"),
            "attack": (115, 0.20, "saw"), "stand": (880, 0.24, "sine"),
            "dash": (250, 0.18, "noise"), "hit": (82, 0.16, "noise"),
            "check": (740, 0.14, "triangle"), "win": (990, 0.35, "sine"),
        }.items():
            self.sfx[name] = self._make_effect(*spec)

    def _write_music_track(self, mood):
        import wave, struct, tempfile
        """Synthesize a short, loopable, original frontier-western instrumental."""
        import math as _math
        rate, duration = 11025, 12.0
        bpm = 112 if mood in ("race", "boss") else 94
        beat = 60.0 / bpm
        # Original chord progression; each mood changes instrumentation/energy.
        progressions = {
            "title": [(0, 3, 7), (5, 8, 12), (2, 5, 9), (4, 7, 11)],
            "race": [(0, 4, 7), (7, 11, 14), (5, 9, 12), (2, 5, 9)],
            "boss": [(0, 3, 7), (1, 5, 8), (5, 8, 12), (3, 7, 10)],
            "chess": [(0, 3, 7), (2, 5, 9), (5, 8, 12), (4, 7, 11)],
            "victory": [(0, 4, 7), (5, 9, 12), (7, 11, 14), (0, 4, 7)],
        }
        chordset = progressions[mood]
        melody = [12, 16, 19, 16, 14, 12, 7, 9, 12, 14, 16, 19,
                  21, 19, 16, 14, 12, 9, 7, 9, 12, 16, 14, 12]
        samples = bytearray()
        total = int(rate * duration)
        for n in range(total):
            t = n / rate
            beat_i = int(t / beat)
            bar = (beat_i // 4) % 4
            chord = chordset[bar]
            beat_phase = (t % beat) / beat
            # Low warm bass and plucked guitar-like chord tones.
            root = 82.41 * (2 ** (chord[0] / 12))
            bass_env = 0.72 + 0.28 * _math.exp(-5 * beat_phase)
            bass = _math.sin(2 * _math.pi * root * t) * 0.17 * bass_env
            chord_freqs = [110.0 * (2 ** (v / 12)) for v in chord]
            pluck_phase = (t % (beat * 2)) / (beat * 2)
            pluck_env = _math.exp(-5.5 * pluck_phase)
            pluck = sum(_math.sin(2 * _math.pi * f * t) for f in chord_freqs) / 3
            pluck *= 0.12 * pluck_env
            note = melody[(beat_i // 2) % len(melody)]
            lead_freq = 220.0 * (2 ** (note / 12))
            lead_env = _math.exp(-3.2 * ((t % (beat * 2)) / (beat * 2)))
            lead = (_math.sin(2 * _math.pi * lead_freq * t) +
                    0.22 * _math.sin(4 * _math.pi * lead_freq * t)) * 0.095 * lead_env
            # Soft kick/snare pulse; boss track is more forceful.
            pulse = 0.0
            if beat_phase < 0.13:
                pulse += _math.sin(2 * _math.pi * (58 - 28 * beat_phase) * t) * (0.16 if mood in ("race", "boss") else 0.09) * (1 - beat_phase / 0.13)
            if beat_i % 4 in (1, 3) and beat_phase < 0.07:
                pulse += (1 if (n % 7 < 3) else -1) * 0.035 * (1 - beat_phase / 0.07)
            energy = 1.15 if mood == "boss" else (1.05 if mood == "race" else 0.88)
            value = max(-0.92, min(0.92, (bass + pluck + lead + pulse) * energy))
            # Gentle fade at loop boundary to avoid clicks.
            edge = min(1.0, t / 0.08, (duration - t) / 0.08)
            value *= max(0.0, edge)
            samples.extend(struct.pack('<h', int(value * 32767)))
        path = Path(tempfile.gettempdir()) / f"sbr_original_{mood}_theme.wav"
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate); wf.writeframes(samples)
        return str(path)

    def _make_effect(self, frequency, duration, shape="sine"):
        import struct
        import math as _math
        import random as _random
        rate = 22050
        frames = int(rate * duration)
        raw = bytearray()
        phase = 0.0
        for i in range(frames):
            t = i / rate
            env = (1 - i / frames) ** 1.7
            if shape == "noise":
                value = _random.uniform(-1, 1)
            else:
                f = frequency * (1 - 0.35 * t / duration) if shape == "saw" else frequency
                phase += 2 * _math.pi * f / rate
                if shape == "triangle":
                    value = 2 / _math.pi * _math.asin(_math.sin(phase))
                elif shape == "saw":
                    value = 2 * ((phase / (2 * _math.pi)) % 1) - 1
                else:
                    value = _math.sin(phase)
            raw.extend(struct.pack('<h', int(max(-1, min(1, value * env * 0.48)) * 32767)))
        return pygame.mixer.Sound(buffer=bytes(raw))

    def play_sfx(self, name):
        if self.audio_enabled and name in self.sfx:
            try:
                self.sfx[name].play()
            except pygame.error:
                pass

    def _set_music_for_state(self, force=False):
        if not self.audio_enabled:
            return
        if self.state in ("race", "town"):
            mood = "race"
        elif self.state in ("boss", "bossintro"):
            mood = "boss"
        elif self.state == "chess":
            mood = "chess"
        elif self.state == "victory":
            mood = "victory"
        else:
            mood = "title"
        if force or mood != self.music_state:
            try:
                pygame.mixer.music.fadeout(250)
                pygame.mixer.music.load(self.music_files[mood])
                pygame.mixer.music.set_volume(0.42 if mood != "boss" else 0.52)
                pygame.mixer.music.play(-1, fade_ms=250)
                self.music_state = mood
            except (pygame.error, KeyError):
                pass

    def reset(self):
        self.progress = 0.0
        self.target_lane = 1
        self.lane = 1.0
        self.speed = 0.0
        self.hp = 100.0
        self.stamina = 100.0
        self.score = 0
        self.elapsed = 0.0
        self.stand = None
        self.stand_cooldown = 0.0
        self.shield = 0.0
        self.surge = 0.0
        self.dodge = 0.0
        self.dismounted_timer = 0.0
        self.balance_qte_timer = 0.0
        self.balance_qte_taps = 0
        self.balance_qte_needed = 9
        self.balance_qte_cooldown = 0.0
        self.mount_recovery = 0.0
        # New arcade systems: burst dash, attack combo, and Spin tokens.
        self.dash_cooldown = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.overdrive = 0.0
        self.overdrive_active = 0.0
        self.bounty_name = None
        self.bounty_reward = 500
        # Dynamic race events make each run feel different without requiring assets.
        self.race_event = None
        self.race_event_timer = 0.0
        self.race_event_countdown = random.uniform(15.0, 23.0)
        self.race_event_number = 0
        self.event_score_clock = 0.0
        # Rotating side contracts add optional short-term goals to every race.
        self.contract_kind = random.choice(["SPRINT", "PICKUPS", "COMBAT", "DISTANCE"])
        self.contract_progress = 0.0
        self.contract_target = {"SPRINT": 4.0, "PICKUPS": 2.0, "COMBAT": 3.0, "DISTANCE": 950.0}[self.contract_kind]
        self.contract_timer = 22.0
        self.contract_cooldown = 8.0
        self.contract_completed = 0
        self.checkpoint_index = 0
        self.checkpoint_progress = 0.0
        self.town_x = 0.0; self.town_z = 0.0
        self.town_enemies = []; self.town_attacks = []
        self.town_combat_cooldown = 0.0; self.town_player_hp = 100.0
        self.town_enemy_count = 0; self.town_reward = 0
        self.town_message = "Welcome to checkpoint town!"; self.town_message_timer = 4.0
        self.camera_shake = 0.0
        self.ambient_dust = [{"x":random.uniform(0, WIDTH), "y":random.uniform(120, HEIGHT-70),
                              "speed":random.uniform(25, 110), "size":random.uniform(1, 3)} for _ in range(34)]
        self.spin_tokens_collected = 0
        self.spin_ability_cooldown = 0.0
        self.allies = 0
        # Allies act independently during boss duels instead of being just a score counter.
        self.ally_attack_timer = 1.0
        self.ally_support_timer = 4.5
        self.ally_boss_damage_total = 0
        self.corpse_parts = []
        self.part_bonus = 0
        self.message = "Collect Corpse Parts to awaken a Stand."
        self.message_timer = 4.0
        self.effects = []
        self.visual_bubbles = []
        self.steel_ball_projectiles = []
        self.visual_crushes = []
        self.result_recorded = False
        self.unlock_notice = ""
        self.rewind_history = []
        self.history_stamp = 0.0
        self.boss_slow = 0.0
        self.time_stop_timer = 0.0  # Enemies freeze; the player keeps moving.
        self.racers = [
            Racer("Gyro Zeppeli", "#58b9a7", 0, 430, 158),
            Racer("Diego Brando", "#d6ad5e", 3, 690, 166),
            Racer("Mountain Tim", "#80a6d1", 2, 920, 150),
            Racer("Hot Pants", "#cb7f9e", 0, 1280, 162),
            Racer("Sandman", "#d68b51", 3, 1640, 170),
            Racer("Pocoloco", "#ac94d0", 1, 2120, 172),
            Racer("Nikolai", "#90aa74", 2, 2490, 154),
            Racer("Marco", "#b77a63", 1, 2880, 160),
            # Additional Part 7 manga rivals with their signature abilities.
            Racer("Ringo Roadagain", "#b9a06b", 2, 3240, 165),
            Racer("Blackmore", "#a5c8d4", 0, 3590, 161),
            Racer("Pork Pie Hat Kid", "#9a8d78", 3, 3940, 157),
            Racer("Axl RO", "#c3b4d7", 1, 4280, 155),
            Racer("Magenta Magenta", "#b47f95", 2, 4620, 152),
            Racer("Oyecomova", "#d3a27b", 0, 4960, 159),
            Racer("Dr. Ferdinand", "#a4b17b", 3, 5300, 162),
            Racer("Wekapipo", "#b9bec9", 1, 5640, 164),
        ]
        # Give manga Stand users their canon signature Stand. Wekapipo uses Spin, not a Stand.
        canon_stands = {
            "Gyro Zeppeli":"Ball Breaker", "Diego Brando":"Scary Monsters",
            "Mountain Tim":"Oh! Lonesome Me", "Hot Pants":"Cream Starter",
            "Sandman":"In a Silent Way", "Pocoloco":"Hey Ya!",
            "Ringo Roadagain":"Mandom", "Blackmore":"Catch the Rainbow",
            "Pork Pie Hat Kid":"Wired", "Axl RO":"Civil War",
            "Magenta Magenta":"20th Century Boy", "Oyecomova":"Boku no Rhythm wo Kiitekure",
            "Dr. Ferdinand":"Scary Monsters"
        }
        stand_lookup = {st["name"]: st for st in STANDS}
        for npc in self.racers:
            signature = canon_stands.get(npc.name)
            if signature and signature in stand_lookup:
                self.assign_stand(npc, stand_lookup[signature].copy())
        # Use the rider chosen in the character-select screen; retain a safe fallback.
        available_characters = list(CHARACTER_LOOKS)
        self.character_name = (self.selected_character_name
                               if getattr(self, "selected_character_name", None) in available_characters
                               else random.choice(available_characters))
        # The selected player character must not also appear as an NPC rival.
        self.racers = [r for r in self.racers if r.name != self.character_name]
        bounty_candidates = [r for r in self.racers if not r.ally]
        self.bounty_name = random.choice(bounty_candidates).name if bounty_candidates else None
        rider_coat = HORSE_COATS.get(self.character_name, "#9a5634")
        self.player = Racer(self.character_name, rider_coat, 1, 0, 100, player=True)
        self.stand = None
        if self.selected_stand_name:
            chosen = next((st.copy() for st in STANDS if st["name"] == self.selected_stand_name), None)
            if chosen and chosen["name"] in self.unlocked_stands:
                self.assign_stand(self.player, chosen)
        self.save_data["last_character"] = self.character_name
        self.save_progress()
        self.pickups = []
        # Corpse Part sites have independent odds; no relic/shrine terminology.
        for idx, p in enumerate(PALM_POSITIONS):
            part = random.random() < CORPSE_PART_CHANCE / 100.0
            self.pickups.append({"kind":"corpse_site", "p":float(p), "lane":(idx * 3 + 1) % 4, "taken":False,
                                 "part":part, "part_claimed":False,
                                 "part_name":random.choice(PART_NAMES) if part else None, "site_index":idx})
        # A different section of the route becomes Skull Sun Territory every run.
        valid_skull_positions = [v for v in range(1000, max(1001, int(RACE_LENGTH)-800), 350)
                                 if all(abs(v - shrine) > 1900 for shrine in PALM_POSITIONS)]
        # Keep a safe fallback for unusually short custom race lengths.
        if not valid_skull_positions:
            valid_skull_positions = [max(500, int(RACE_LENGTH * 0.55))]
        safe_skull_positions = valid_skull_positions or [max(500, int(RACE_LENGTH * 0.55))]
        self.skull_sun = {"p":float(random.choice(safe_skull_positions)), "width":2200,
                          "lane":random.randrange(4)}
        skull_part = random.choice(PART_NAMES)
        self.pickups.append({"kind":"skull_sun", "p":self.skull_sun["p"],
                             "lane":self.skull_sun["lane"], "taken":False, "part":True,
                             "part_claimed":False, "part_name":skull_part})
        for p in range(700, int(RACE_LENGTH)-250, 600):
            if random.random() < .72:
                self.pickups.append({"kind":"carrot", "p":float(p), "lane":random.randrange(4), "taken":False})
        # Golden Spin tokens create an optional risk/reward route through the lanes.
        for p in range(1150, int(RACE_LENGTH)-350, 1050):
            if random.random() < .88:
                self.pickups.append({"kind":"spin_token", "p":float(p), "lane":random.randrange(4), "taken":False})
        # New race pickups: horseshoes protect the rider; stars trigger a score/speed burst.
        for p in range(900, int(RACE_LENGTH)-300, 1450):
            if random.random() < .78:
                self.pickups.append({"kind":"horseshoe", "p":float(p), "lane":random.randrange(4), "taken":False})
        for p in range(1550, int(RACE_LENGTH)-300, 1750):
            if random.random() < .72:
                self.pickups.append({"kind":"race_star", "p":float(p), "lane":random.randrange(4), "taken":False})
        # Jesus appears once along the main route. Johnny can meet him to awaken Act 3.
        self.pickups.append({"kind":"jesus_encounter", "p":float(RACE_LENGTH * 0.56),
                             "lane":1, "taken":False})
        self.hazards = []
        for p in range(1100, int(RACE_LENGTH)-250, 850):
            self.hazards.append({"p":float(p), "lane":random.randrange(4), "kind":random.choice(["rock","cactus","fallen_log"]), "hit":False, "near_miss":False})
        self.current_stage = 0
        self.boss_hp = float(self.stage_bosses()[self.current_stage]["hp"]) * {"Easy": 0.72, "Normal": 1.0, "Hard": 1.35}.get(self.settings["difficulty"], 1.0)
        self.boss_love_train_unlocked = False
        self.boss_love_train_clock = 0.0
        self.boss_love_train_active = False
        self.boss_phase_announced = False
        self.boss_cooldown = 2.0
        self.boss_attack_anim = 0.0
        self.winner = False
        self.state = getattr(self, "state", "race")

    def advance_contract(self, kind, amount=1.0):
        """Advance the current optional race contract and award a clear reward."""
        if self.state != "race" or self.contract_timer <= 0 or self.contract_kind != kind:
            return
        self.contract_progress += amount
        if self.contract_progress >= self.contract_target:
            self.contract_completed += 1
            self.score += 350 + 100 * min(3, self.contract_completed - 1)
            self.overdrive = min(100.0, self.overdrive + 18.0)
            self.stamina = min(100.0, self.stamina + 25.0)
            self.contract_timer = 0.0
            self.contract_cooldown = 7.0
            self.camera_shake = max(self.camera_shake, 0.18)
            self.notify(f"CONTRACT COMPLETE! +{350 + 100 * min(3, self.contract_completed - 1)} points • +18% Overdrive • stamina restored!", 3.0)

    def notify(self, message, duration=2.4):
        self.message, self.message_timer = message, duration

    def assign_stand(self, racer, stand):
        """Equip a Stand; canon-user bonuses apply only when the matching Stand is equipped."""
        equipped = stand.copy()
        equipped_name = equipped.get("name", "")
        legitimate = (STAND_AFFINITIES.get(racer.name) == equipped_name or
                      (racer.name == "Johnny Joestar" and equipped_name.startswith("Tusk Act")))
        if legitimate and not equipped.get("affinity_bonus"):
            equipped["speed"] = equipped.get("speed", 0) + 18
            equipped["stamina"] = equipped.get("stamina", 0) + 5
            equipped["combat"] = equipped.get("combat", 1.0) * 1.30
            equipped["defense"] = equipped.get("defense", 0) + 8
            equipped["affinity_bonus"] = True
            equipped["affinity_text"] = "LEGITIMATE USER: +18 speed, +30% combat, +5 stamina, +8 defense"
            # Infinite Rotation (Act 4), rather than early Tusk forms, counters Love Train.
            if racer.name == "Johnny Joestar" and equipped["name"] == "Tusk Act 4":
                equipped["love_train_pierce"] = True
            if racer.name == "Gyro Zeppeli" and equipped["name"] == "Ball Breaker":
                equipped["love_train_pierce"] = True
        racer.stand = equipped
        if getattr(racer, "player", False):
            self.stand = equipped.copy()
            self.player.stand = equipped.copy()
        return equipped

    def damage_boss(self, amount, source_stand=None):
        """Damage Funny Valentine, with Love Train periodically redirecting misfortune."""
        amount = max(0.0, float(amount))
        if getattr(self, "boss_love_train_active", False):
            source_name = source_stand.get("name", "") if source_stand else ""
            if source_name == "Tusk Act 4":
                amount *= 1.0  # Infinite Rotation passes through the dimensional wall.
            elif source_name == "Ball Breaker":
                amount *= 0.82  # Golden Spin can pierce the barrier, but is less decisive.
            elif source_stand and source_stand.get("love_train_pierce"):
                amount *= 0.62
            else:
                amount *= 0.38
            piercing = source_name in ("Tusk Act 4", "Ball Breaker") or bool(
                source_stand and source_stand.get("love_train_pierce"))
            self.effects.append({"kind":"pulse", "until":self.elapsed+0.45,
                                 "color":"#ffe9a0" if piercing else "#e8cd73"})
        self.boss_hp = max(0.0, self.boss_hp - amount)
        if (self.current_stage == 3 and not self.boss_love_train_unlocked and
                self.boss_hp <= float(self.current_boss()["hp"]) * 0.72 and self.boss_hp > 0):
            self.boss_love_train_unlocked = True
            self.boss_love_train_clock = 0.0
            self.boss_phase_announced = True
            self.notify("D4C — LOVE TRAIN! A wall of light begins redirecting your attacks. Wait for the barrier to flicker!", 4.5)

    def open_chess_duel(self):
        """Open Chess Duel directly from the title screen."""
        self.play_sfx("select")
        self.chess_last_move = None
        self.chess_selected = None
        self.chess_thinking = False
        if chess:
            self.chess_board = chess.Board()
            self.chess_message = "800 ELO CHESS BOT — you are White. Your move."
        else:
            self.chess_board = None
            self.chess_message = "Chess rules library is missing. Install python-chess, then restart."
        self.state = "chess"
        self.last_tick = time.perf_counter()

    def key_down(self, event):
        key = event.keysym.lower()
        already = key in self.keys
        self.keys.add(key)
        if already: return
        if self.state == "chess":
            if key == "escape":
                self.state = "title"
            elif key == "r":
                if chess:
                    self.chess_board = chess.Board()
                    self.chess_last_move = None
                    self.chess_selected = None
                    self.chess_message = "New game — you are White. Make the first move."
            return
        if self.state == "town":
            if key == "space": self.play_sfx("attack")
            elif key == "k": self.play_sfx("stand")
            if key in ("escape", "t", "q"):
                self.progress = max(self.progress, self.checkpoint_progress)
                self.state = "race"; self.last_tick = time.perf_counter()
                self.notify("Returned to the race. Checkpoint saved!", 2.5)
            elif key == "space": self.town_attack()
            elif key == "k": self.town_stand_attack()
            elif key == "e": self.town_interact()
            return
        if self.state == "settings":
            setting_keys = ["difficulty", "horse_speed", "hazards", "controls", "back"]
            if key == "escape":
                self.state = "title"
            elif key in ("up", "w"):
                self.settings_index = (self.settings_index - 1) % len(setting_keys)
            elif key in ("down", "s"):
                self.settings_index = (self.settings_index + 1) % len(setting_keys)
            elif key in ("left", "a", "right", "d", "return", "space"):
                name = setting_keys[self.settings_index]
                if name == "back":
                    self.state = "title"
                elif name == "difficulty":
                    choices = ["Easy", "Normal", "Hard"]
                    idx = choices.index(self.settings[name])
                    self.settings[name] = choices[(idx + (1 if key in ("right", "d", "return", "space") else -1)) % len(choices)]
                elif name == "horse_speed":
                    choices = ["Fast", "Faster", "Extreme"]
                    idx = choices.index(self.settings[name])
                    self.settings[name] = choices[(idx + (1 if key in ("right", "d", "return", "space") else -1)) % len(choices)]
                elif name == "hazards":
                    self.settings[name] = "Off" if self.settings[name] == "On" else "On"
                elif name == "controls":
                    self.settings[name] = "WASD" if self.settings[name] == "Arrows" else "Arrows"
            return
        if self.state == "stand_select":
            options = self.stand_menu_options()
            if key == "escape":
                self.state = "title"
            elif key in ("up", "w"):
                self.stand_menu_index = max(0, self.stand_menu_index - 1)
                self.keep_stand_selection_visible()
            elif key in ("down", "s"):
                self.stand_menu_index = min(max(0, len(options) - 1), self.stand_menu_index + 1)
                self.keep_stand_selection_visible()
            elif key in ("return", "space"):
                option = options[self.stand_menu_index] if options else "RANDOM / AWAKEN IN RACE"
                if option == "RANDOM / AWAKEN IN RACE":
                    self.selected_stand_name = None
                    self.stand = None
                    self.player.stand = None
                else:
                    # Resolve the exact Stand record and equip it on both the player
                    # racer and the game's combat/stat system immediately.
                    selected = next((st for st in STANDS if st["name"] == option), None)
                    if selected is None or option not in self.unlocked_stands:
                        self.notify("That Stand is not unlocked yet. Collect a Corpse Part first.", 2.5)
                        return
                    self.selected_stand_name = option
                    self.assign_stand(self.player, selected)
                self.save_progress()
                self.state = "title"
                self.notify("Equipped: " + (self.selected_stand_name or "Random Stand from a Corpse Part"), 2.5)
            return
        if self.state == "character_select":
            characters = list(CHARACTER_LOOKS)
            if key == "escape":
                self.state = "title"
            elif key in ("left", "a", "up", "w"):
                self.character_menu_index = (self.character_menu_index - 1) % len(characters)
                self.selected_character_name = characters[self.character_menu_index]
                self.save_progress()
            elif key in ("right", "d", "down", "s"):
                self.character_menu_index = (self.character_menu_index + 1) % len(characters)
                self.selected_character_name = characters[self.character_menu_index]
                self.save_progress()
            elif key in ("return", "space"):
                self.selected_character_name = characters[self.character_menu_index]
                self.reset()
                self.state = "race"
                self.last_tick = time.perf_counter()
                self.notify(f"RIDER SELECTED: {self.character_name}. BOUNTY: {self.bounty_name} (+{self.bounty_reward}) — defeat them for a bonus!", 4.0)
            return
        if self.state == "title" and key == "t":
            self.alternate_universe = not self.alternate_universe
            world = "ALTERNATE UNIVERSE" if self.alternate_universe else "ORIGINAL STEEL BALL RUN"
            self.notify(f"WORLD SELECTED: {world}. Press ENTER to choose your rider.", 3.0)
            return
        if self.state == "title" and key == "v":
            characters = list(CHARACTER_LOOKS)
            self.character_menu_index = characters.index(self.selected_character_name) if self.selected_character_name in characters else 0
            self.state = "character_select"
            return
        if self.state == "title" and key in ("i", "f1", "h"):
            self.state = "howto"
            return
        if self.state == "title" and key == "r":
            self.state = "records"
            return
        if self.state == "title" and key == "b":
            self.open_chess_duel()
            return
        if self.state in ("howto", "records") and key in ("escape", "backspace", "return", "space"):
            self.state = "title"
            return
        if key in ("h", "f1"):
            self.show_help = not self.show_help
            if self.show_help:
                self.notify("HELP: switch lanes to dodge, sprint with SHIFT, Q to dash, X at full meter for OVERDRIVE, SPACE to attack, K for your Stand, E to recruit.", 4.0)
            return
        if key == "escape":
            self.quit(); return
        if self.state == "title" and key == "s":
            self.settings_index = 0
            self.state = "settings"
            return
        if self.state == "title" and key == "c":
            options = self.stand_menu_options()
            preferred = self.selected_stand_name or "RANDOM / AWAKEN IN RACE"
            self.stand_menu_index = options.index(preferred) if preferred in options else 0
            self.stand_scroll_offset = 0
            self.keep_stand_selection_visible()
            self.state = "stand_select"
            return
        if self.state == "title" and key in ("return", "space"):
            self.play_sfx("select")
            characters = list(CHARACTER_LOOKS)
            self.character_menu_index = characters.index(self.selected_character_name) if self.selected_character_name in characters else 0
            self.state = "character_select"
            return
        if self.state in ("victory", "failed") and key == "m":
            self.reset()
            self.state = "title"
            self.last_tick = time.perf_counter()
            return
        if self.state in ("victory", "failed") and key == "return":
            self.reset(); self.state = "race"; self.last_tick = time.perf_counter(); return
        if self.state == "race":
            if key == "space": self.play_sfx("attack")
            elif key == "k": self.play_sfx("stand")
            elif key == "q": self.play_sfx("dash")
            elif key in ("shift_l", "shift_r"): self.play_sfx("dash")
            if self.balance_qte_timer > 0 and key in ("space", "e", "k", "g", "q", "return"):
                self.balance_qte_taps += 1
                if self.balance_qte_taps >= self.balance_qte_needed:
                    self.balance_qte_timer = 0.0
                    self.balance_qte_cooldown = 2.2
                    self.shield = max(self.shield, 1.0)
                    self.notify("SADDLE SAVE! You mashed fast enough and stayed on your horse!", 2.2)
                return
            if self.dismounted_timer > 0 and key in ("space", "e", "return"):
                self.mount_recovery += 1
                if self.mount_recovery >= 5:
                    self.dismounted_timer = 0.0
                    self.mount_recovery = 0
                    self.shield = max(self.shield, 0.8)
                    self.notify("BACK IN THE SADDLE! Keep moving!", 1.8)
                return
            if key == "t":
                self.enter_town()
                return
            if key in (("left",) if self.settings["controls"] == "Arrows" else ("a",)): self.target_lane = max(0, self.target_lane - 1)
            elif key in (("right",) if self.settings["controls"] == "Arrows" else ("d",)): self.target_lane = min(3, self.target_lane + 1)
            elif key == "space": self.attack()
            elif key == "q": self.burst_dash()
            elif key == "x": self.activate_overdrive()
            elif key == "k": self.use_stand()
            elif key == "g": self.use_spin_ability()
            elif key == "e": self.recruit()
        elif self.state == "bossintro" and key in ("return", "space"):
            boss = self.stage_bosses()[self.current_stage]
            self.state = "boss"
            self.notify(f"Face {boss['name']}! SPACE attacks, K uses your Stand, SHIFT guards. Your {self.allies} allies will fight too!", 3.5)
        elif self.state == "boss":
            if key == "space": self.boss_attack()
            elif key == "k": self.use_stand(boss=True)
            elif key == "g": self.use_spin_ability(boss=True)

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def quit(self):
        self.running = False

    def stage_bosses(self):
        return ALT_STAGE_BOSSES if getattr(self, "alternate_universe", False) else STAGE_BOSSES

    def stage_names(self):
        return ALT_STAGE_NAMES if getattr(self, "alternate_universe", False) else STAGE_NAMES

    def stage_index(self):
        return min(3, getattr(self, "current_stage", int(self.progress / RACE_LENGTH * 4)))

    def current_boss(self):
        return self.stage_bosses()[min(3, max(0, self.current_stage))]

    def defeat_stage_boss(self):
        """Advance to the next race stage only after its end-of-stage duel is won."""
        if self.current_stage >= len(self.stage_bosses()) - 1:
            self.state = "victory"
            if (not self.alternate_universe and self.character_name == "Johnny Joestar"
                    and self.stand and self.stand.get("name") == "Tusk Act 3"):
                act4 = next((st.copy() for st in STANDS if st["name"] == "Tusk Act 4"), None)
                if act4:
                    self.assign_stand(self.player, act4)
                    self.unlock_stand("Tusk Act 4")
                    self.notify("TUSK ACT 4 UNLOCKED! You completed the Steel Ball Run with Act 3. Infinite Rotation is yours!", 6.0)
                    self.save_progress()
            if self.alternate_universe:
                self.unlock_stand("The World (Alternate Universe)")
                self.notify("ALTERNATE UNIVERSE CLEARED! THE WORLD (AU) is now unlocked in your Stand Archive!", 5.0)
            else:
                self.notify("Steel Ball Run champion! You defeated Funny Valentine.", 4)
            return
        defeated = self.current_boss()["name"]
        self.current_stage += 1
        self.boss_hp = float(self.current_boss()["hp"]) * {"Easy": 0.72, "Normal": 1.0, "Hard": 1.35}.get(self.settings["difficulty"], 1.0)
        self.boss_love_train_unlocked = False
        self.boss_love_train_clock = 0.0
        self.boss_love_train_active = False
        self.boss_phase_announced = False
        self.boss_cooldown = 2.0
        self.boss_attack_anim = 0.0
        self.progress = self.current_stage * (RACE_LENGTH / 4.0)
        self.state = "race"
        self.notify(f"{defeated} defeated! Stage {self.current_stage + 1}: {self.stage_names()[self.current_stage]}. Ride to the next duel!", 4)

    def world_x(self, progress):
        # A wide visible window gives the race a sense of scale.
        return 255 + (progress - self.progress) * 0.39

    def save_progress(self):
        data = {
            "unlocked_stands": list(dict.fromkeys(self.unlocked_stands)),
            "selected_stand": self.selected_stand_name,
            "wins_in_row": int(self.wins_in_row),
            "total_wins": int(self.total_wins),
            "has_corpse_part": bool(self.has_ever_collected_part),
            "wonder_unlocked": "Wonder of U" in self.unlocked_stands,
            "total_spin_tokens": int(getattr(self, "total_spin_tokens", 0)),
            "spin_ability_unlocked": bool(getattr(self, "spin_ability_unlocked", False)),
            "last_character": getattr(self, "character_name", self.save_data.get("last_character")),
            "selected_character": getattr(self, "selected_character_name", self.save_data.get("selected_character")),
        }
        self.save_data = data
        try:
            if not browser_save_progress(data) and not IS_BROWSER:
                SAVE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            # The game remains playable if the folder is read-only.
            pass

    def unlock_stand(self, name):
        if name and name not in self.unlocked_stands:
            self.unlocked_stands.append(name)
            self.notify(f"STAND ARCHIVE UNLOCKED: {name}!", 3.0)
            self.save_progress()

    def stand_menu_options(self):
        # Filter stale save-file entries so every selectable name maps to a real Stand.
        valid_names = {st["name"] for st in STANDS}
        unlocked = [name for name in self.unlocked_stands if name in valid_names]
        return ["RANDOM / AWAKEN IN RACE"] + unlocked

    def record_run_result(self):
        if self.result_recorded:
            return
        self.result_recorded = True
        if self.state == "victory":
            if getattr(self, "alternate_universe", False):
                self.unlock_stand("The World (Alternate Universe)")
            equipped_name = self.stand.get("name", "") if self.stand else ""
            if equipped_name == "Soft & Wet" and len(self.corpse_parts) >= 3:
                self.unlock_stand("Soft & Wet: Go Beyond")
                self.notify("SECRET UNLOCK: GO BEYOND! Win with Soft & Wet after collecting 3 Corpse Parts.", 5.0)
            if equipped_name == "D4C" and len(self.corpse_parts) >= 4:
                self.unlock_stand("D4C: Love Train")
                self.notify("SECRET UNLOCK: D4C — LOVE TRAIN! Win the final battle with D4C after collecting 4 Corpse Parts.", 5.0)
            self.total_wins += 1
            self.wins_in_row += 1
            if self.wins_in_row >= 5 and self.has_ever_collected_part:
                if "Wonder of U" not in self.unlocked_stands:
                    self.unlocked_stands.append("Wonder of U")
                    self.unlock_notice = "WONDER OF U UNLOCKED — 5 consecutive wins + a Corpse Part!"
                self.save_progress()
            else:
                self.save_progress()
        elif self.state == "failed":
            self.wins_in_row = 0
            self.save_progress()

    def collect_corpse_part(self, racer, pickup):
        if not pickup.get("part") or pickup.get("part_claimed", False):
            return False
        pickup["part_claimed"] = True
        racer.parts += 1
        # A Corpse Part awakens a weighted-random Stand for every character.
        # Manga canon no longer forces a character to receive their usual Stand.
        awakened = None
        if racer.player:
            # Johnny's signature progression starts with Tusk Act 1, then evolves
            # as the player gathers more Corpse Parts. Other riders use the unique pool.
            if racer.name == "Johnny Joestar":
                owned_tusk = [n for n in self.unlocked_stands if n.startswith("Tusk Act")]
                current_tusk = racer.stand.get("name", "") if racer.stand else ""
                if current_tusk.startswith("Tusk Act"):
                    awakened = next(st.copy() for st in STANDS if st["name"] == current_tusk)
                elif owned_tusk:
                    best_tusk = max(owned_tusk, key=lambda n: int(n[-1]))
                    awakened = next(st.copy() for st in STANDS if st["name"] == best_tusk)
                else:
                    awakened = next(st.copy() for st in STANDS if st["name"] == "Tusk Act 1")
            else:
                owned = set(self.unlocked_stands)
                if racer.stand:
                    owned.add(racer.stand.get("name", ""))
                awakened = weighted_stand(owned)
            if awakened:
                self.assign_stand(racer, awakened)
                self.unlock_stand(racer.stand["name"])
                self.notify(f"NEW STAND AWAKENED: {racer.stand['name']}! Duplicate random Stands are blocked until your collection is complete.", 3.8)
                self.score += 300
            else:
                self.notify("NO DUPLICATE STAND! Your regular awakenings are complete. Unlock evolution and secret Stands through their special requirements.", 3.8)
        elif racer.stand is None:
            awakened = weighted_stand()
            self.assign_stand(racer, awakened)
            if abs(racer.progress-self.progress) < 1600:
                self.notify(f"{racer.name} awakened {racer.stand['name']} from a Corpse Part!", 2.2)
        # Johnny unlocks Act 2 by collecting two Corpse Parts. Acts 3 and 4
        # have their own story encounters rather than being granted automatically.
        if racer.name == "Johnny Joestar" and racer.stand and racer.stand.get("name", "").startswith("Tusk Act"):
            current_act = int(racer.stand["name"][-1])
            if racer.player and current_act == 1 and racer.parts >= 2 and "Tusk Act 2" not in self.unlocked_stands:
                evolved = next((st.copy() for st in STANDS if st["name"] == "Tusk Act 2"), None)
                if evolved:
                    self.assign_stand(racer, evolved)
                    awakened = evolved
                    self.unlock_stand("Tusk Act 2")
                    self.notify("TUSK ACT 2 AWAKENED! Collect 2 Corpse Parts as Johnny Joestar.", 4.0)
        if racer.player:
            part_name = pickup.get("part_name") or random.choice(PART_NAMES)
            self.corpse_parts.append(part_name)
            self.score += 650
            self.part_bonus += 1
            self.has_ever_collected_part = True
            if not awakened:
                self.notify(f"CORPSE PART CLAIMED: {part_name}! Your Stand is ready behind you.", 3.0)
            self.save_progress()
        else:
            racer.hp = min(racer.max_hp(), racer.hp + 20)
            racer.speed += 3.0
        return True

    def palm_event(self, racer, index):
        palm = self.pickups[index]
        if racer.last_palm == index:
            return
        racer.last_palm = index
        got_part = self.collect_corpse_part(racer, palm)
        if racer.player and not got_part:
            self.notify("This site has no available Corpse Part. Seek the next glowing site or Skull Sun Territory.", 1.8)

    def skull_sun_event(self, racer, pickup):
        got_part = self.collect_corpse_part(racer, pickup)
        if racer.player:
            pickup["taken"] = True
            if got_part:
                self.notify("SKULL SUN CLAIMED! The Corpse Part awakened or strengthened your Stand.", 3.2)
            else:
                self.notify("A rival claimed the Skull Sun's Corpse Part first!", 2.5)
        return got_part


    def burst_dash(self):
        """A quick lane-racing burst that rewards timing and costs stamina."""
        if self.dash_cooldown > 0:
            self.notify(f"Burst recharging: {self.dash_cooldown:.1f}s", 1.0)
            return
        if self.stamina < 18:
            self.notify("Not enough stamina for a burst! Collect rations or ease off sprint.", 1.4)
            return
        self.stamina -= 18
        self.surge = max(self.surge, 2.6)
        self.dodge = max(self.dodge, 0.85)
        self.speed += 95
        self.dash_cooldown = 4.5
        self.score += 20 * max(1, self.combo)
        self.effects.append({"kind":"pulse", "until":self.elapsed+0.65, "color":"#f3d36c"})
        self.notify("BURST DASH! Brief invulnerability and a big speed boost.", 1.2)

    def activate_overdrive(self):
        """Spend a full momentum meter for a dramatic temporary power-up."""
        if self.overdrive < 100:
            self.notify(f"OVERDRIVE charging: {int(self.overdrive)}% — land hits and near-misses!", 1.4)
            return
        self.overdrive = 0
        self.overdrive_active = 5.0
        self.surge = max(self.surge, 5.0)
        self.shield = max(self.shield, 2.0)
        self.stamina = min(100, self.stamina + 35)
        self.effects.append({"kind":"pulse", "until":self.elapsed+1.0, "color":"#ff9e48"})
        self.notify("⚡ OVERDRIVE! 5 seconds of boosted speed and attacks, plus a brief shield!", 2.5)

    def attack(self):
        if self.character_name == "Gyro Zeppeli":
            candidates = [r for r in self.racers if not r.out and not r.ally and r.knocked <= 0
                          and abs(r.progress-self.progress) < 1450
                          and abs(r.lane-round(self.lane)) <= 1]
            if not candidates:
                self.notify("GYRO: No rival in steel-ball range. Line up a lane and throw again.", 1.5)
                return
            target = min(candidates, key=lambda r: abs(r.progress-self.progress)
                         + abs(r.lane-round(self.lane))*140)
            self.combo = min(9, self.combo + 1) if self.combo_timer > 0 else 1
            self.combo_timer = 4.5
            self.overdrive = min(100, self.overdrive + 14)
            damage = 48 * (self.stand["combat"] if self.stand else 1.0) * (1 + 0.08 * (self.combo - 1)) * (1.75 if self.overdrive_active > 0 else 1.0) * (1.35 if self.race_event == "SPIN SURGE" else 1.0)
            target.hp -= damage
            target.knocked = 0.65
            target.progress -= 125
            ball_start = self.progress + (30 if target.progress >= self.progress else -30)
            ball_target = target.progress
            self.steel_ball_projectiles.append({"p":ball_start, "target_p":ball_target,
                                                "direction":1 if ball_target >= ball_start else -1,
                                                "lane":target.lane, "until":self.elapsed+0.75,
                                                "spin":random.random()*6.28})
            self.effects.append({"kind":"hit", "p":target.progress, "until":self.elapsed+0.45})
            self.score += 35 + 12 * self.combo
            self.notify(f"GYRO'S STEEL BALL strikes {target.name}! COMBO x{self.combo} • {max(0,int(target.hp))} HP remains.", 1.3)
        else:
            candidates = [r for r in self.racers if not r.out and not r.ally and r.knocked <= 0
                          and abs(r.progress-self.progress) < 300
                          and abs(r.lane-round(self.lane)) <= 1]
            if not candidates:
                self.notify("Horse ram: get close to a rival and line up your lane.", 1.5)
                return
            target = min(candidates, key=lambda r: abs(r.progress-self.progress)
                         + abs(r.lane-round(self.lane))*100)
            self.combo = min(9, self.combo + 1) if self.combo_timer > 0 else 1
            self.combo_timer = 4.5
            self.overdrive = min(100, self.overdrive + 14)
            damage = 38 * (self.stand["combat"] if self.stand else 1.0) * (1 + 0.08 * (self.combo - 1)) * (1.75 if self.overdrive_active > 0 else 1.0) * (1.35 if self.race_event == "SPIN SURGE" else 1.0)
            target.hp -= damage
            target.knocked = 0.85
            target.progress -= 95
            self.score += 25 + 12 * self.combo
            self.effects.append({"kind":"hit", "p":target.progress, "until":self.elapsed+0.35})
            self.notify(f"Your horse rams {target.name}! COMBO x{self.combo} • {max(0,int(target.hp))} HP remains.", 1.3)
        self.advance_contract("COMBAT", 1.0)
        if target.hp <= 0:
            target.out = True
            target.out_timer = 2.6
            self.score += 250 + 50 * max(0, self.combo - 1)
            if target.name == self.bounty_name:
                self.score += self.bounty_reward
                self.bounty_name = None
                self.stamina = min(100, self.stamina + 30)
                self.overdrive = min(100, self.overdrive + 35)
                self.notify(f"BOUNTY COMPLETE! +{self.bounty_reward} points, stamina restored, +35% Overdrive!", 3.0)
            self.combo = min(9, max(1, self.combo + 1))
            self.combo_timer = 5.0
            self.notify(f"{target.name} knocked out! BOUNTY +250 • COMBO x{self.combo} ★", 2.5)

    def use_spin_ability(self, boss=False):
        """Use the permanent Golden Spin technique unlocked after collecting five Spin tokens."""
        if not self.spin_ability_unlocked:
            remaining = max(0, 5 - self.total_spin_tokens)
            self.notify(f"GOLDEN SPIN LOCKED — collect {remaining} more Spin token(s) to unlock it.", 2.5)
            return
        if self.spin_ability_cooldown > 0:
            self.notify(f"Spin Technique recharging: {self.spin_ability_cooldown:.1f}s", 1.4)
            return
        self.spin_ability_cooldown = 10.0
        self.stamina = max(0, self.stamina - 12)
        self.surge = max(self.surge, 3.0)
        self.shield = max(self.shield, 1.0)
        self.effects.append({"kind": "pulse", "until": self.elapsed + 1.25, "color": "#f4d16e"})
        if boss:
            self.damage_boss(58, self.stand)
            self.notify("GOLDEN SPIN TECHNIQUE! A concentrated Spin strike hits the boss!", 2.8)
        else:
            self.special_hit(1.8, 105, 650, stun=0.9)
            self.notify("GOLDEN SPIN TECHNIQUE! Rivals are struck by a spinning shockwave — speed boosted!", 2.8)

    def use_stand(self, boss=False):
        if self.stand is None:
            self.notify("No Stand yet — collect a Corpse Part at a glowing site or Skull Sun Territory."); return
        if self.stand_cooldown > 0:
            self.notify(f"Stand recharging: {self.stand_cooldown:.1f}s", 1.2); return
        name = self.stand["name"]
        self.stand_cooldown = 7.5
        col = self.stand["color"]
        self.effects.append({"kind":"pulse", "until":self.elapsed+0.8, "color":col})
        if name.startswith("Tusk Act"):
            act = int(name[-1])
            if boss:
                self.damage_boss({1:28, 2:38, 3:54, 4:108}.get(act, 28), self.stand)
                if act == 4:
                    self.boss_slow = max(self.boss_slow, 2.2)
            else:
                self.nail_shot()
            descriptions = {
                1:"Focused nail shot",
                2:"Curving nails drill through the route",
                3:"Spatial nail holes open across lanes",
                4:"INFINITE ROTATION: Golden Spin pierces Love Train",
            }
            self.notify(f"TUSK ACT {act}: {descriptions[act]}!")
        elif name == "Scary Monsters":
            self.progress += 330 if not boss else 0
            self.surge = 3.2
            if boss: self.damage_boss(18, self.stand)
            else: self.special_hit(1.15, 120, 560)
            self.notify("SCARY MONSTERS: Dinosaur rush!")
        elif name in ("The World (Alternate Universe)", "The World", "THE WORLD"):
            # True time stop: NPC racers and the boss's attack clock freeze, but
            # the player's normal update continues, so their horse keeps moving.
            self.stamina = max(0, self.stamina - 18)
            self.time_stop_timer = max(self.time_stop_timer, 3.0)
            self.surge = max(self.surge, 2.4)
            self.dodge = max(self.dodge, 1.0)
            self.effects.append({"kind":"pulse", "until":self.elapsed+3.0, "color":"#f4d75e"})
            if boss:
                self.damage_boss(62, self.stand)
            else:
                # The player can pass frozen racers while moving at normal speed.
                for target in self.racers:
                    if target.ally or target.out:
                        continue
                    if abs(target.progress-self.progress) < 900 and abs(target.lane-round(self.lane)) <= 1:
                        target.hp -= 30 * (self.stand.get("combat", 1.0) if self.stand else 1.0)
                        target.stun = max(target.stun, 3.0)
                        if target.hp <= 0:
                            target.out = True
                            target.out_timer = 2.5
                            self.score += 150
            self.notify("THE WORLD: TIME STOP! Enemies freeze for 3 seconds — YOUR HORSE KEEPS MOVING!", 3.0)
        elif name == "D4C":
            # Dirty Deeds Done Dirt Cheap: cross dimensions in a sudden dash,
            # become briefly untouchable, and let a parallel-world double strike.
            if not boss:
                self.progress += 370
                self.special_hit(1.0, 80, 520, stun=0.45)
            else:
                self.damage_boss(34, self.stand)
                self.progress += 85
            self.dodge = 3.2
            self.effects.append({"kind":"pulse", "until":self.elapsed+1.1, "color":"#d889b4"})
            self.notify("D4C: PARALLEL-WORLD DASH! You phase ahead while your dimensional double strikes!")
        elif name == "Ball Breaker":
            if boss: self.damage_boss(42, self.stand)
            else: self.special_hit(2.1, 65, 610)
            self.stamina = max(0, self.stamina-8)
            self.notify("BALL BREAKER: Golden spin knocks rivals down!")
        elif name == "Cream Starter":
            self.hp = min(self.max_hp(), self.hp+30)
            self.stamina = min(100, self.stamina+35)
            if boss: self.damage_boss(12, self.stand)
            self.notify("CREAM STARTER: Health and stamina restored.")
        elif name == "Mandom":
            if not boss:
                target_time = self.elapsed - 5.8
                snapshots = [snap for snap in self.rewind_history if snap["time"] <= target_time]
                if snapshots:
                    snap = snapshots[-1]
                    self.progress = max(0.0, snap["progress"])
                    self.hp = min(self.max_hp(), max(self.hp, snap["hp"]))
                    self.stamina = min(100.0, max(self.stamina, snap["stamina"]))
                else:
                    self.progress = max(0.0, self.progress - 260)
                    self.hp = min(self.max_hp(), self.hp + 18)
            else:
                self.damage_boss(30, self.stand)
                self.hp = min(self.max_hp(), self.hp + 28)
            self.notify("MANDOM: The last few seconds rewind; position and endurance restored.")
        elif name == "Catch the Rainbow":
            self.shield = 5.0
            self.surge = 3.2
            if boss: self.damage_boss(20, self.stand)
            self.notify("CATCH THE RAINBOW: Rain veil, shield, and speed!")
        elif name == "In a Silent Way":
            if boss: self.damage_boss(32, self.stand)
            else: self.special_hit(1.4, 20, 700, stun=1.6)
            self.notify("IN A SILENT WAY: Sound constructs trap and stun nearby rivals.")
        elif name == "Oh! Lonesome Me":
            if boss:
                self.damage_boss(25, self.stand)
                self.boss_slow = max(self.boss_slow, 2.5)
            else:
                self.special_hit(1.0, 18, 700, stun=0.9)
            self.notify("OH! LONESOME ME: The lariat snaps tight and leaves the target tangled!")
        elif name == "Hey Ya!":
            self.stamina = 100
            self.surge = 4.0
            if boss: self.damage_boss(15, self.stand)
            self.notify("HEY YA!: Encouragement restores all stamina!")
        elif name == "Ticket to Ride":
            self.shield = 7.0
            if boss: self.damage_boss(27, self.stand)
            self.notify("TICKET TO RIDE: A protective blessing surrounds you.")
        elif name in ("Soft & Wet", "Soft & Wet: Go Beyond"):
            self.surge = 4.2
            if boss:
                self.damage_boss(26, self.stand)
                self.boss_slow = max(self.boss_slow, 3.0)
                for j in range(7):
                    self.visual_bubbles.append({"p": self.progress + j * 20, "lane": 1.0 + (j % 3) * 0.22,
                                                "until": self.elapsed + 1.0, "phase": j * 0.9})
                self.notify("SOFT & WET: Star-marked bubbles plunder the President's momentum!")
            else:
                targets = [r for r in self.racers if not r.out and not r.ally
                           and abs(r.progress-self.progress) < 760
                           and abs(r.lane-round(self.lane)) <= 1]
                for target in targets:
                    target.plundered = max(target.plundered, 3.4)
                    target.hp -= 24 * (self.stand["combat"] if self.stand else 1.0)
                    target.progress -= 32
                    self.visual_bubbles.append({"p": target.progress - 24, "lane": target.lane,
                                                "until": self.elapsed + 0.95, "phase": random.random()*6})
                    if target.hp <= 0:
                        target.out = True
                        target.out_timer = 2.6
                        self.score += 250
                if not targets:
                    self.visual_bubbles.append({"p": self.progress + 140, "lane": self.lane,
                                                "until": self.elapsed + 0.95, "phase": 0.0})
                    self.notify("SOFT & WET: A bubble steals nearby momentum and turns it into a speed burst.")
                else:
                    self.notify(f"SOFT & WET: Plunder bubbles stole momentum from {len(targets)} rival(s)!")
        elif name == "Soft & Wet: Go Beyond":
            # A rare, defense-piercing spin bubble: devastating to bosses, precise against racers.
            self.surge = max(self.surge, 3.0)
            self.visual_bubbles.append({"p": self.progress + 260, "lane": self.lane,
                                        "until": self.elapsed + 1.25, "phase": self.elapsed,
                                        "go_beyond": True})
            if boss:
                self.damage_boss(118, self.stand)
                self.boss_slow = max(self.boss_slow, 1.8)
                self.notify("SOFT & WET: GO BEYOND! The invisible spin pierces the boss's defenses!")
            else:
                targets = [r for r in self.racers if not r.out and not r.ally
                           and abs(r.progress-self.progress) < 1500]
                if targets:
                    target = min(targets, key=lambda r: abs(r.progress-self.progress))
                    target.hp -= 105 * self.stand["combat"]
                    target.progress -= 190
                    target.knocked = max(target.knocked, 1.6)
                    self.visual_bubbles.append({"p": target.progress, "lane": target.lane,
                                                "until": self.elapsed + 1.25, "phase": self.elapsed,
                                                "go_beyond": True})
                    if target.hp <= 0:
                        target.out = True
                        target.out_timer = 2.8
                        self.score += 350
                    self.notify(f"GO BEYOND! An impossible spin bubble strikes {target.name} through their defenses!")
                else:
                    self.progress += 360
                    self.notify("GO BEYOND! The spin bubble races ahead, giving you a burst of speed.")
        elif name == "Civil War":
            if boss:
                self.damage_boss(38, self.stand)
                self.boss_slow = max(self.boss_slow, 2.8)
            else:
                self.special_hit(1.35, 75, 680, stun=1.0)
                for r in self.racers:
                    if not r.out and abs(r.progress-self.progress) < 680:
                        r.speed = max(55, r.speed * 0.72)
            self.shield = max(self.shield, 1.5)
            self.notify("CIVIL WAR: a guilt-bound shroud weighs down nearby enemies!")
        elif name == "Chocolate Disco":
            if boss:
                self.damage_boss(34, self.stand)
            else:
                self.special_hit(1.45, 90, 760, stun=0.75)
            for j in range(5):
                self.effects.append({"kind":"pulse", "until":self.elapsed+0.5+j*0.08, "color":"#c5a0d9"})
            self.notify("CHOCOLATE DISCO: the tactical grid locks onto your rivals!")
        elif name == "Killer Queen":
            if boss:
                self.damage_boss(44, self.stand)
            else:
                targets = [r for r in self.racers if not r.out and not r.ally
                           and abs(r.progress-self.progress) < 820
                           and abs(r.lane-round(self.lane)) <= 1]
                for r in targets:
                    r.hp -= 56 * self.stand["combat"]
                    r.progress -= 115
                    r.knocked = max(r.knocked, 1.1)
                    if r.hp <= 0:
                        r.out = True; r.out_timer = 2.6; self.score += 250
            self.notify("KILLER QUEEN: tagged targets erupt in a controlled explosion!")
        elif name == "Paisley Park":
            self.progress += 520
            self.stamina = min(100, self.stamina + 42)
            self.hp = min(self.max_hp(), self.hp + 12)
            self.shield = max(self.shield, 2.0)
            if boss: self.damage_boss(20, self.stand)
            self.notify("PAISLEY PARK: a safe route appears ahead; stamina restored!")
        elif name == "Born This Way":
            if boss:
                self.damage_boss(36, self.stand)
                self.boss_slow = max(self.boss_slow, 3.5)
            else:
                self.special_hit(1.3, 65, 820, stun=2.0)
            self.shield = max(self.shield, 1.2)
            self.notify("BORN THIS WAY: freezing wind sweeps across the raceway!")
        elif name == "Speed King":
            self.progress += 430
            self.surge = max(self.surge, 5.0)
            self.stamina = max(0, self.stamina - 12)
            if boss: self.damage_boss(32, self.stand)
            else: self.special_hit(0.9, 40, 430)
            self.notify("SPEED KING: stored heat releases into a blazing sprint!")
        elif name == "Wonder of U":
            self.shield = 999.0
            self.surge = 18.0
            if boss:
                self.boss_hp = 0
                self.visual_crushes.append({"p":self.progress, "lane":self.lane, "until":self.elapsed+1.3})
                self.notify("WONDER OF U: CALAMITY crushes the President instantly!")
            else:
                victims = [r for r in self.racers if not r.out and not r.ally
                           and abs(r.progress-self.progress) < 2600]
                for victim in victims:
                    self.crush_racer(victim, "Wonder of U's calamity")
                self.notify(f"WONDER OF U: Calamity crushed {len(victims)} rival(s). You are nearly untouchable!")
        else:
            # Every catalogue Stand gets a tangible K ability. These named moves
            # add specific gameplay effects before the shared role-based fallback.
            effect_type = self.stand.get("effect_type", "offense")
            custom_moves = {
                "Wired": ("control", 24, 1.8, "steel cables snag nearby rivals"),
                "Tomb of the Boom": ("offense", 34, 0.7, "a magnetic blast knocks rivals back"),
                "Boku no Rhythm wo Kiitekure": ("offense", 42, 0.0, "a timed explosive rhythm detonates"),
                "Sugar Mountain": ("support", 0, 0.0, "the tree's blessing restores your stamina"),
                "Tubular Bells": ("control", 28, 1.6, "inflated animal decoys trip rivals"),
                "20th Century Boy": ("defense", 0, 0.0, "you brace and absorb incoming damage"),
                "Tattoo You!": ("evasion", 22, 0.8, "the decoy crowd confuses rivals"),
                "King Nothing": ("control", 30, 1.5, "a scent trail locks onto a rival"),
                "California King Bed": ("control", 26, 1.8, "memory pieces slow the nearest rivals"),
                "Paper Moon King": ("control", 24, 2.0, "paper illusions disorient nearby rivals"),
                "Nut King Call": ("support", 18, 0.0, "bolts and joints restore your endurance"),
                "Walking Heart": ("offense", 38, 0.6, "extended heel spikes strike forward"),
                "Doobie Wah!": ("control", 25, 2.1, "a tracking tornado chases the nearest rival"),
                "Schott Key No. 1": ("offense", 32, 0.7, "the glove launches a surprise strike"),
                "Schott Key No. 2": ("offense", 36, 0.8, "the hidden weapon bursts from the glove"),
                "Vitamin C": ("control", 20, 2.4, "softening touch weakens nearby rivals"),
                "Milagro Man": ("support", 0, 0.0, "a money curse converts into stamina"),
                "Blue Hawaii": ("control", 18, 2.5, "infected pursuers chase and slow rivals"),
                "Brain Storm": ("offense", 35, 1.0, "microscopic attackers deal a damage burst"),
                "Ozon Baby": ("control", 22, 2.2, "heavy pressure slows nearby rivals"),
                "Doctor Wu": ("evasion", 20, 0.0, "your body disperses to evade the next hit"),
                "I Am a Rock": ("control", 28, 1.7, "a magnetic object pulls rivals off pace"),
                "Fun Fun Fun": ("control", 25, 1.8, "remote limb control interrupts rivals"),
                "Les Feuilles": ("speed", 0, 0.0, "leaf paths launch you forward"),
                "Love Love Deluxe": ("control", 24, 1.5, "hair tendrils tangle nearby opponents"),
                "Doggy Style": ("defense", 0, 0.0, "your body unravels to avoid damage"),
                "Space Trucking": ("evasion", 0, 0.0, "you hide inside a playing card and evade"),
                "November Rain": ("control", 42, 2.2, "heavy rain crushes and slows rivals"),
                "Smooth Operators": ("support", 0, 0.0, "tiny sliders repair your gear and heal you"),
                "The Hustle": ("defense", 20, 0.0, "muscle control counters the next attack"),
                "The Matte Kudasai": ("support", 0, 0.0, "an ally's requested object restores stamina"),
                "Bigmouth Strikes Again": ("offense", 30, 1.0, "a hidden attack hits nearby rivals"),
                "Bags' Groove": ("control", 26, 1.7, "tiny parasites disrupt rival movement"),
                "Cat Size": ("defense", 0, 0.0, "elastic wires form a protective web"),
                "Glory Days": ("offense", 38, 0.7, "accelerated bullets hit a rival"),
                "West End Girl": ("control", 25, 1.8, "a thread trap catches nearby rivals"),
                "200 Balloons": ("support", 0, 0.0, "balloons lift you into a quick speed burst"),
                "Lyin' Eyes": ("evasion", 0, 0.0, "a deceptive decoy lets you dodge"),
            }
            move = custom_moves.get(name)
            if move and name != "D4C: Love Train":
                move_type, move_damage, move_slow, move_text = move
                if move_type == "support":
                    self.hp = min(self.max_hp(), self.hp + (18 if move_damage == 0 else 12))
                    self.stamina = min(100, self.stamina + 32)
                    self.shield = max(self.shield, 1.4)
                    if not boss and name in ("Les Feuilles", "200 Balloons"):
                        self.progress += 250
                elif move_type == "defense":
                    self.shield = max(self.shield, 4.0)
                    self.dodge = max(self.dodge, 0.9)
                    if boss: self.damage_boss(30 + move_damage, self.stand)
                    else: self.special_hit(0.8, 40, 500, stun=0.35)
                elif move_type == "speed":
                    self.progress += 420
                    self.surge = max(self.surge, 3.5)
                    self.stamina = min(100, self.stamina + 18)
                    if boss: self.damage_boss(28, self.stand)
                elif move_type == "evasion":
                    self.dodge = max(self.dodge, 2.2)
                    self.surge = max(self.surge, 1.6)
                    if boss: self.damage_boss(24 + move_damage, self.stand)
                    elif move_damage: self.special_hit(0.9, 30, 600, stun=0.6)
                else:
                    if boss:
                        self.damage_boss(30 + move_damage, self.stand)
                        if move_slow: self.boss_slow = max(self.boss_slow, move_slow)
                    else:
                        self.special_hit(1.0 + move_damage / 100.0, 80 + move_damage, 900, stun=move_slow)
                        for rival in self.racers:
                            if not rival.out and not rival.ally and abs(rival.progress-self.progress) < 900:
                                rival.speed = max(65, rival.speed * 0.76)
                                rival.stun = max(rival.stun, move_slow)
                self.effects.append({"kind":"pulse", "until":self.elapsed+1.0, "color":col})
                self.notify(f"{name.upper()}: {move_text.upper()}!", 2.5)
            elif name == "D4C: Love Train":
                self.shield = max(self.shield, 7.0)
                if boss:
                    if self.stand.get("love_train_pierce") or self.character_name == "Johnny Joestar":
                        self.damage_boss(150, self.stand)
                    else:
                        self.damage_boss(48, self.stand)
                        self.notify("LOVE TRAIN redirects incoming damage; Tusk Act 4 / Ball Breaker can pierce it.", 3.0)
                else:
                    self.special_hit(1.8, 155, 1100, stun=1.5)
                self.notify("D4C: LOVE TRAIN! A dimensional light barrier redirects danger.", 2.8)
            elif effect_type in ("speed", "evasion"):
                self.progress += 470 if effect_type == "speed" else 280
                self.surge = max(self.surge, 4.0)
                self.dodge = max(self.dodge, 1.7 if effect_type == "evasion" else 0.6)
                self.stamina = min(100, self.stamina + 24)
                if boss: self.damage_boss(35, self.stand)
                self.notify(f"{name.upper()}: mobility technique activated!", 2.4)
            elif effect_type == "support":
                self.hp = min(self.max_hp(), self.hp + 25)
                self.stamina = min(100, self.stamina + 42)
                self.shield = max(self.shield, 2.8)
                if boss: self.damage_boss(28, self.stand)
                self.notify(f"{name.upper()}: support ability restores your endurance!", 2.4)
            elif effect_type == "defense":
                self.shield = max(self.shield, 5.5)
                self.dodge = max(self.dodge, 0.7)
                if boss: self.damage_boss(38, self.stand)
                else: self.special_hit(0.85, 35, 520, stun=0.4)
                self.notify(f"{name.upper()}: defensive technique blocks the next hits!", 2.4)
            elif effect_type == "control":
                if boss:
                    self.damage_boss(42, self.stand)
                    self.boss_slow = max(self.boss_slow, 3.0)
                else:
                    self.special_hit(1.25, 90, 850, stun=1.25)
                self.notify(f"{name.upper()}: a special trap or field disrupts nearby rivals!", 2.4)
            else:
                if boss: self.damage_boss(50, self.stand)
                else: self.special_hit(1.45, 105, 760, stun=0.8)
                self.notify(f"{name.upper()}: Stand attack lands!", 2.4)
        self.score += 50
        if boss and self.boss_hp <= 0: self.state = "victory"

    def crush_racer(self, racer, source="Wonder of U's calamity"):
        if racer.out:
            return
        racer.hp = 0
        racer.out = True
        racer.out_timer = 3.2
        racer.knocked = 0.0
        self.visual_crushes.append({"p":racer.progress, "lane":racer.lane, "until":self.elapsed+1.1})
        self.score += 400
        self.notify(f"CALAMITY: {racer.name} is instantly crushed by {source}!", 2.0)

    def nail_shot(self):
        """Tusk Act 1 focuses a nail shot on one nearby rival instead of an area burst."""
        candidates = [r for r in self.racers if not r.out and not r.ally and r.knocked <= 0
                      and abs(r.progress-self.progress) < 980
                      and abs(r.lane-round(self.lane)) <= 1]
        if not candidates:
            self.notify("TUSK: No rival in nail-shot range; close the gap first.", 1.4)
            return
        target = min(candidates, key=lambda r: abs(r.progress-self.progress)
                     + abs(r.lane-round(self.lane))*120)
        act = int(self.stand.get("name", "Tusk Act 1")[-1]) if self.stand and self.stand.get("name", "").startswith("Tusk Act") else 1
        damage = (62 + (act-1)*18) * (self.stand["combat"] if self.stand else 1.0)
        target.hp -= damage
        target.progress -= 125
        target.knocked = 0.8
        self.effects.append({"kind":"hit", "p":target.progress, "until":self.elapsed+0.45})
        self.score += 30
        if target.hp <= 0:
            target.out = True
            target.out_timer = 2.6
            self.score += 250
            self.notify(f"TUSK'S NAIL SHOT knocked {target.name} out of the race!", 2.0)

    def special_hit(self, multiplier, push, range_, stun=0.0):
        targets = [r for r in self.racers if not r.out and not r.ally and abs(r.progress-self.progress)<range_
                   and abs(r.lane-round(self.lane)) <= 1]
        for r in targets:
            r.hp -= 42*multiplier
            r.knocked = 1.0
            if stun > 0:
                r.stun = max(r.stun, stun)
            r.progress -= push+95
            if r.hp <= 0:
                r.out = True; r.out_timer = 2.6; self.score += 250
                self.notify(f"{r.name} knocked off their horse and eliminated! ★", 2)

    def recruit(self):
        nearby = [r for r in self.racers if not r.out and not r.ally and abs(r.progress-self.progress)<240
                  and abs(r.lane-round(self.lane))<=1]
        if not nearby:
            self.notify("Ride close to a rival and press E to befriend them."); return
        r = min(nearby,key=lambda q:abs(q.progress-self.progress))
        r.ally = True
        self.allies = sum(1 for ally in self.racers if ally.ally and not ally.out)
        self.score += 125
        if r.stand:
            self.notify(f"{r.name} joined your team with {r.stand['name']}! They'll fight beside you in boss battles.", 3.0)
        else:
            self.notify(f"{r.name} joined your team! They'll fight beside you in boss battles.", 3.0)

    def max_hp(self):
        return max(1, 100 + (self.part_bonus * 4 if hasattr(self, "part_bonus") else 0)
                   + (self.stand["defense"] if self.stand else 0))

    def take_hit(self, amount, source):
        if self.stand and self.stand["name"] == "Wonder of U":
            self.notify("WONDER OF U: Calamity turns the incoming attack into harmless dust.", 1.4)
            return
        if self.dodge > 0:
            self.notify("D4C's dimensional dodge avoided the attack!", 1.0); return
        if self.shield > 0:
            self.notify("Your Stand shield deflected the attack!", 1.0); return
        reduction = self.stand["defense"] if self.stand else 0
        difficulty_damage = {"Easy": 0.62, "Normal": 1.0, "Hard": 1.35}.get(self.settings["difficulty"], 1.0)
        final = max(2, amount * difficulty_damage * (1 - max(0,reduction)/100))
        self.hp -= final
        self.notify(f"{source} hit you! Switch lanes or use your Stand.", 1.4)
        # Hard hits can throw the rider sideways. A short button-mash QTE saves the mount.
        if (final >= 9 and self.balance_qte_cooldown <= 0 and self.dismounted_timer <= 0
                and self.balance_qte_timer <= 0 and random.random() < min(0.78, 0.28 + final / 55)):
            self.balance_qte_timer = 1.45
            self.balance_qte_taps = 0
            self.balance_qte_needed = 9 if self.settings["difficulty"] != "Hard" else 11
            self.notify("ALMOST THROWN OFF! MASH SPACE / E / K / G / Q / ENTER NOW!", 1.45)
        if self.hp <= 0: self.state = "failed"

    def update(self, dt):
        self.elapsed += dt
        self.message_timer = max(0, self.message_timer-dt)
        self.camera_shake = max(0.0, self.camera_shake - dt)
        # Contract rotation: the player gets a fresh optional objective after a short breather.
        if self.contract_timer > 0:
            self.contract_timer = max(0.0, self.contract_timer - dt)
            if self.contract_timer <= 0 and self.contract_progress < self.contract_target:
                self.notify("CONTRACT EXPIRED — a new challenge will appear shortly.", 1.8)
                self.contract_cooldown = 5.0
        else:
            self.contract_cooldown = max(0.0, self.contract_cooldown - dt)
            if self.contract_cooldown <= 0:
                self.contract_kind = random.choice(["SPRINT", "PICKUPS", "COMBAT", "DISTANCE"])
                self.contract_progress = 0.0
                self.contract_target = {"SPRINT": 4.0, "PICKUPS": 2.0, "COMBAT": 3.0, "DISTANCE": 950.0}[self.contract_kind]
                self.contract_timer = 22.0
                self.notify({"SPRINT":"NEW CONTRACT: sprint for 4 seconds!", "PICKUPS":"NEW CONTRACT: collect 2 trail pickups!", "COMBAT":"NEW CONTRACT: land 3 attacks on rivals!", "DISTANCE":"NEW CONTRACT: cover 950 race meters!"}[self.contract_kind], 2.5)
        self.stand_cooldown = max(0, self.stand_cooldown-dt)
        self.time_stop_timer = max(0.0, self.time_stop_timer-dt)
        self.overdrive_active = max(0.0, self.overdrive_active-dt)
        # Random timed events: choose a new challenge every 15–23 seconds.
        if self.race_event_timer > 0:
            self.race_event_timer = max(0.0, self.race_event_timer - dt)
            self.event_score_clock += dt
            if self.race_event == "GOLDEN RUSH" and self.event_score_clock >= 1.0:
                self.event_score_clock = 0.0
                self.score += 18
            if self.race_event_timer <= 0:
                ended = self.race_event
                self.race_event = None
                self.race_event_countdown = random.uniform(15.0, 23.0)
                self.notify(f"{ended} event ended. Prepare for the next race event!", 1.8)
        else:
            self.race_event_countdown -= dt
            if self.race_event_countdown <= 0:
                event = random.choice(["GOLDEN RUSH", "SANDSTORM", "SPIN SURGE", "STAMPede"])
                self.race_event = event
                self.race_event_timer = 8.0
                self.event_score_clock = 0.0
                self.race_event_number += 1
                if event == "GOLDEN RUSH":
                    self.surge = max(self.surge, 8.0)
                    self.stamina = min(100.0, self.stamina + 24.0)
                    self.notify("GOLDEN RUSH! Speed surges and the crowd awards bonus points for 8 seconds!", 3.2)
                elif event == "SANDSTORM":
                    self.shield = max(self.shield, 1.5)
                    self.notify("SANDSTORM! Visibility drops—dodge hazards and rivals lose speed for 8 seconds!", 3.2)
                elif event == "SPIN SURGE":
                    self.overdrive = min(100.0, self.overdrive + 25.0)
                    self.notify("SPIN SURGE! Spin energy floods the track: +25% Overdrive and boosted attacks!", 3.2)
                else:
                    self.surge = max(self.surge, 5.0)
                    self.shield = max(self.shield, 2.0)
                    self.notify("STAMPede! Ride the wild current for bonus speed and temporary protection!", 3.2)
        self.shield = max(0, self.shield-dt)
        self.surge = max(0, self.surge-dt)
        self.dodge = max(0, self.dodge-dt)
        self.balance_qte_cooldown = max(0.0, self.balance_qte_cooldown-dt)
        if self.balance_qte_timer > 0:
            self.balance_qte_timer = max(0.0, self.balance_qte_timer-dt)
            if self.balance_qte_timer <= 0 and self.balance_qte_taps < self.balance_qte_needed:
                self.dismounted_timer = 3.0
                self.mount_recovery = 0
                self.speed *= 0.38
                self.hp = max(1.0, self.hp-5)
                self.notify("THROWN OFF! Mash SPACE / E / ENTER 5 times to remount!", 3.0)
        if self.dismounted_timer > 0:
            self.dismounted_timer = max(0.0, self.dismounted_timer-dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown-dt)
        self.spin_ability_cooldown = max(0.0, self.spin_ability_cooldown-dt)
        if self.combo_timer > 0:
            self.combo_timer = max(0.0, self.combo_timer-dt)
            if self.combo_timer <= 0:
                self.combo = 0
        self.lane += (self.target_lane-self.lane)*min(1,dt*9)
        sprint = ("shift_l" in self.keys or "shift_r" in self.keys) and self.stamina > 0
        if sprint:
            self.advance_contract("SPRINT", dt)
        self.advance_contract("DISTANCE", max(0.0, self.speed) * dt)
        regen = 14.0 + (self.stand["stamina"] if self.stand else 0) * 0.08 + min(8, len(self.corpse_parts)*1.4)
        self.stamina = clamp(self.stamina + (-38 if sprint else regen)*dt, 0, 100)
        stat_speed = self.stand["speed"] if self.stand else 0
        speed_base = {"Fast": 245.0, "Faster": 315.0, "Extreme": 390.0}.get(self.settings["horse_speed"], 315.0)
        sprint_bonus = {"Fast": 105.0, "Faster": 145.0, "Extreme": 190.0}.get(self.settings["horse_speed"], 145.0)
        base_speed = speed_base + stat_speed + (sprint_bonus if sprint else 0) + (75 if self.surge>0 else 0)
        if self.race_event == "GOLDEN RUSH":
            base_speed += 95
        elif self.race_event == "STAMPede":
            base_speed += 115
        elif self.race_event == "SPIN SURGE" and self.overdrive_active > 0:
            base_speed += 45
        if self.dismounted_timer > 0:
            base_speed *= 0.34
        self.speed += (base_speed-self.speed)*min(1,dt*4.5)
        # Save lightweight snapshots for Mandom's six-second rewind.
        if self.elapsed - self.history_stamp >= 0.20:
            self.rewind_history.append({"time":self.elapsed, "progress":self.progress,
                                        "hp":self.hp, "stamina":self.stamina})
            self.rewind_history = [snap for snap in self.rewind_history if self.elapsed-snap["time"] <= 7.5]
            self.history_stamp = self.elapsed
        self.visual_bubbles = [b for b in self.visual_bubbles if b["until"] > self.elapsed]
        self.visual_crushes = [e for e in self.visual_crushes if e["until"] > self.elapsed]
        self.steel_ball_projectiles = [b for b in self.steel_ball_projectiles if b["until"] > self.elapsed
                                       and (abs(b["target_p"]-b["p"]) > 10)]
        for ball in self.steel_ball_projectiles:
            direction = ball.get("direction", 1)
            ball["p"] += 1650 * dt * direction
        self.progress += self.speed*dt
        # Horse-racing AI, stand awakenings, attacks, and recruit opportunities.
        for r in self.racers:
            if r.out:
                r.out_timer = max(0, r.out_timer-dt)
                continue
            # Time stop freezes opponents in place, but never pauses the player.
            if self.time_stop_timer > 0 and not r.ally:
                r.stun = max(r.stun, 0.12)
                continue
            if r.knocked > 0:
                r.knocked = max(0, r.knocked-dt)
                r.progress += max(0, r.speed*0.25)*dt
                continue
            r.cooldown -= dt
            r.stun = max(0,r.stun-dt)
            r.dodge = max(0,r.dodge-dt)
            r.plundered = max(0.0, r.plundered-dt)
            if r.stun <= 0:
                stand_speed = r.stand["speed"] if r.stand else 0
                plunder_slow = 15.0 if r.plundered > 0 else 0.0
                # Rival riders are competitive enough to win Corpse Parts before the player.
                event_slow = 72.0 if self.race_event == "SANDSTORM" else 0.0
                r.progress += max(115.0, r.speed + stand_speed + 53.0 - plunder_slow - event_slow
                                   + 9*math.sin(self.elapsed*.6+r.lane))*dt
            # Riders chase relics when one is ahead. Part carriers then actively hunt the player.
            part_targets = [p for p in self.pickups if p["kind"] in ("corpse_site", "skull_sun") and p.get("part")
                            and not p.get("part_claimed", False)
                            and 0 <= p["p"]-r.progress <= 1050]
            r.ai_lane_timer -= dt
            if r.parts > 0 and abs(r.progress-self.progress) < 850:
                lane_delta = round(self.lane) - r.lane
                r.lane += clamp(lane_delta, -3.7*dt, 3.7*dt)
            elif part_targets:
                target_part = min(part_targets, key=lambda p: p["p"]-r.progress)
                lane_delta = target_part["lane"] - r.lane
                r.lane += clamp(lane_delta, -3.1*dt, 3.1*dt)
            elif r.ai_lane_timer <= 0:
                r.ai_lane_timer = random.uniform(1.1,3.0)
                if random.random()<.55:
                    r.lane = float(random.randrange(4))
            # Corpse parts are shared pickups: the first rider to reach the lane takes them.
            for p in self.pickups:
                if p["kind"] not in ("corpse_site", "skull_sun") or not p.get("part") or p.get("part_claimed", False):
                    continue
                if abs(p["p"]-r.progress) <= 70 and abs(p["lane"]-r.lane) <= 0.62:
                    self.collect_corpse_part(r, p)
                    break
            # Part carriers attack using a horse ram or their awakened Stand.
            near_distance = abs(r.progress-self.progress)
            near_lane = abs(r.lane-round(self.lane)) <= 0.66
            attack_range = 950 if r.name == "Gyro Zeppeli" else 220
            if r.parts > 0 and near_distance < attack_range and near_lane and r.cooldown <= 0:
                r.cooldown = random.uniform(1.0, 1.7)
                if self.stand and self.stand["name"] == "Wonder of U":
                    self.crush_racer(r)
                    continue
                if r.name == "Gyro Zeppeli":
                    self.take_hit(random.uniform(17, 26), "Gyro's steel-ball attack")
                    self.steel_ball_projectiles.append({"p":r.progress, "target_p":self.progress,
                                                        "direction":-1 if self.progress < r.progress else 1,
                                                        "lane":r.lane, "until":self.elapsed+0.75,
                                                        "spin":random.random()*6.28})
                elif r.stand and random.random() < 0.58:
                    damage = random.uniform(18, 27) * max(1.0, r.stand.get("combat", 1.0))
                    attack_name = f"{r.name}'s {r.stand['name']}"
                    self.take_hit(damage, attack_name)
                else:
                    damage = random.uniform(13, 21)
                    self.speed = max(25, self.speed - 28)
                    self.take_hit(damage, f"{r.name}'s horse ram")
                r.progress -= 35
            elif r.parts <= 0 and near_distance < 100 and near_lane and r.cooldown <= 0:
                # Even non-carriers can bump the player's horse, but do little damage.
                r.cooldown = random.uniform(2.0, 3.5)
                if self.stand and self.stand["name"] == "Wonder of U":
                    self.crush_racer(r)
                    continue
                self.take_hit(random.uniform(2, 5), f"{r.name}'s horse")
        for i,p in enumerate(self.pickups):
            if p["taken"]: continue
            if abs(p["p"]-self.progress)<72 and p["lane"]==round(self.lane):
                if p["kind"] == "corpse_site":
                    p["taken"] = True
                    self.palm_event(self.player,i)
                elif p["kind"] == "skull_sun":
                    self.skull_sun_event(self.player, p)
                elif p["kind"] == "jesus_encounter":
                    if self.character_name == "Johnny Joestar" and self.stand and self.stand.get("name") == "Tusk Act 2":
                        p["taken"] = True
                        act3 = next((st.copy() for st in STANDS if st["name"] == "Tusk Act 3"), None)
                        if act3:
                            self.assign_stand(self.player, act3)
                            self.unlock_stand("Tusk Act 3")
                            self.notify("JESUS'S BLESSING! TUSK ACT 3 UNLOCKED. Reach the final stage and win its boss fight with Act 3 to obtain Act 4.", 5.0)
                            self.save_progress()
                    else:
                        self.notify("A mysterious traveler is ahead. You need to be Johnny Joestar with Tusk Act 2 to receive Jesus's blessing.", 3.0)
                elif p["kind"] == "carrot":
                    p["taken"] = True; self.stamina=min(100,self.stamina+28);self.hp=min(self.max_hp(),self.hp+7);self.score+=35
                    self.advance_contract("PICKUPS", 1.0)
                    self.notify("Trail rations collected: stamina restored.",1.2)
                elif p["kind"] == "horseshoe":
                    p["taken"] = True
                    self.shield = max(self.shield, 3.2)
                    self.stamina = min(100, self.stamina + 12)
                    self.score += 60
                    self.advance_contract("PICKUPS", 1.0)
                    self.notify("GOLDEN HORSESHOE! Temporary protection for 3.2 seconds!", 1.8)
                elif p["kind"] == "race_star":
                    p["taken"] = True
                    self.surge = max(self.surge, 3.0)
                    self.score += 100
                    self.combo = min(9, self.combo + 1)
                    self.combo_timer = 5.0
                    self.advance_contract("PICKUPS", 1.0)
                    self.notify(f"RACE STAR! Speed burst and +100 points • {self.combo}x combo", 1.8)
                elif p["kind"] == "spin_token":
                    p["taken"] = True
                    self.spin_tokens_collected += 1
                    self.total_spin_tokens += 1
                    self.overdrive = min(100, self.overdrive + 12)
                    self.score += 125
                    self.stamina = min(100, self.stamina + 16)
                    self.surge = max(self.surge, 1.8)
                    self.combo = min(9, self.combo + 1)
                    self.combo_timer = 4.5
                    self.advance_contract("PICKUPS", 1.0)
                    if not self.spin_ability_unlocked and self.total_spin_tokens >= 5:
                        self.spin_ability_unlocked = True
                        self.notify("GOLDEN SPIN UNLOCKED! You collected 5 Spin tokens. Press G to use the Spin Technique!", 4.0)
                    else:
                        progress_text = "SPIN TECHNIQUE READY — press G!" if self.spin_ability_unlocked else f"Spin tokens: {self.total_spin_tokens}/5 total"
                        self.notify(f"GOLDEN SPIN! +125 points • {self.combo}x combo • {progress_text}", 2.0)
                    self.save_progress()
        for h in self.hazards:
            if self.settings["hazards"] == "Off": continue
            if h["hit"]: continue
            distance_to_hazard = abs(h["p"]-self.progress)
            if (distance_to_hazard < 48 and h["lane"] != round(self.lane)
                    and not h.get("near_miss", False)):
                h["near_miss"] = True
                self.score += 45 * max(1, self.combo)
                self.overdrive = min(100, self.overdrive + 9)
                self.combo = min(9, self.combo + 1)
                self.combo_timer = 3.2
                self.notify(f"CLOSE CALL! +{45 * max(1, self.combo - 1)} points • {self.combo}x combo", 1.0)
            if distance_to_hazard < 43 and h["lane"]==round(self.lane):
                h["hit"] = True; self.stamina=max(0,self.stamina-19);self.speed=max(20,self.speed-12)
                self.take_hit(5,"Road hazard")
                self.notify("Obstacle! Switch lanes to avoid the next one.",1.6)
        stage_finish = (self.current_stage + 1) * (RACE_LENGTH / 4.0)
        while self.checkpoint_index < 4 and self.progress >= (self.checkpoint_index + 1) * (RACE_LENGTH / 4.0):
            self.checkpoint_index += 1
            self.checkpoint_progress = self.checkpoint_index * (RACE_LENGTH / 4.0)
            self.score += 250
            self.hp = min(self.max_hp(), self.hp + 12)
            self.stamina = min(100.0, self.stamina + 25.0)
            self.notify(f"CHECKPOINT {self.checkpoint_index}/4 SAVED! +250 points, health and stamina restored. Press T to visit town.", 4.0)
        if self.progress >= stage_finish:
            self.progress = stage_finish
            self.state = "bossintro"
            boss = self.current_boss()
            self.notify(f"Stage {self.current_stage + 1} finish! {boss['name']} challenges you.", 4)
        if self.hp <= 0: self.state="failed"

    def boss_attack(self):
        damage = 20 + (self.stand["combat"]*5 if self.stand else 0) + self.allies*4
        before = self.boss_hp
        self.damage_boss(damage, self.stand)
        dealt = int(before - self.boss_hp)
        self.notify(f"You struck {self.current_boss()['name']} for {dealt} damage!", 1.2)
        if self.boss_hp <= 0:
            self.defeat_stage_boss()

    def update_boss(self,dt):
        self.elapsed += dt
        self.message_timer=max(0,self.message_timer-dt)
        self.stand_cooldown=max(0,self.stand_cooldown-dt)
        self.spin_ability_cooldown=max(0,self.spin_ability_cooldown-dt)
        self.shield=max(0,self.shield-dt)
        self.dodge=max(0,self.dodge-dt)
        self.boss_slow = max(0.0, self.boss_slow-dt)
        self.time_stop_timer = max(0.0, self.time_stop_timer-dt)
        if self.current_stage == 3 and self.boss_love_train_unlocked:
            self.boss_love_train_clock += dt
            # The dimensional wall cycles: 3.6 seconds protected, then 3 seconds vulnerable.
            self.boss_love_train_active = (self.boss_love_train_clock % 6.6) < 3.6
        if self.time_stop_timer <= 0:
            self.boss_cooldown -= dt * (0.42 if self.boss_slow > 0 else 1.0)
        # Recruited allies actively attack the boss and occasionally protect the player.
        # Damage scales gently with team size so a large crew feels powerful without
        # instantly skipping the whole duel.
        active_allies = [ally for ally in self.racers if ally.ally and not ally.out]
        self.allies = len(active_allies)
        if active_allies and self.boss_hp > 0:
            self.ally_attack_timer -= dt
            if self.ally_attack_timer <= 0:
                self.ally_attack_timer = max(0.72, 1.65 - min(len(active_allies), 4) * 0.12)
                # Each recruited friend attacks independently; Stand users hit harder.
                ally_damage = sum(random.uniform(3.0, 5.2) * (1.45 if ally.stand else 1.0)
                                  for ally in active_allies)
                before_ally = self.boss_hp
                self.damage_boss(ally_damage, None)
                dealt = int(before_ally - self.boss_hp)
                self.ally_boss_damage_total += dealt
                self.effects.append({"kind":"pulse", "until":self.elapsed+0.35, "color":"#80e6c1"})
                if dealt > 0 and (int(self.elapsed * 2) % 5 == 0):
                    self.notify(f"ALLY ASSIST! Your team dealt {dealt} damage!", 1.1)
            self.ally_support_timer -= dt
            if self.ally_support_timer <= 0:
                self.ally_support_timer = max(3.0, 6.2 - min(len(active_allies), 4) * 0.55)
                heal = min(4.0 + self.allies * 1.8, max(0.0, self.max_hp() - self.hp))
                if heal > 0:
                    self.hp += heal
                    self.notify(f"TEAM SUPPORT! Your allies restored {int(heal)} health.", 1.5)
        if "shift_l" in self.keys or "shift_r" in self.keys:
            self.shield=max(self.shield,.10)
        if self.boss_cooldown<=0 and self.time_stop_timer <= 0:
            self.boss_cooldown=random.uniform(1.0,1.8)
            if self.stand and self.stand["name"] == "Wonder of U":
                self.visual_crushes.append({"p":self.progress, "lane":self.lane, "until":self.elapsed+1.2})
                self.boss_hp = 0
                self.notify(f"WONDER OF U: {self.current_boss()['name']} is crushed by calamity!", 2.5)
                self.boss_hp = 0
                self.defeat_stage_boss()
                return
            phase_hit = self.boss_love_train_unlocked and self.boss_love_train_active
            hit_amount = max(4, (13.0 if phase_hit else 10.0) - self.allies*0.8)
            if self.shield > 0 or self.dodge > 0:
                hit_amount *= 0.35
            boss_name = self.current_boss()["name"]
            source = "D4C: Love Train's redirected misfortune" if phase_hit else f"{boss_name}'s attack"
            self.take_hit(hit_amount, source)
        if self.boss_hp<=0:
            self.defeat_stage_boss()

    def draw_background(self):
        stage=min(3,int(self.progress/RACE_LENGTH*4))
        in_skull_zone = hasattr(self, "skull_sun") and abs(self.progress-self.skull_sun["p"]) < self.skull_sun["width"] / 2
        sky=["#edc48a","#cdb1a8","#c4b6a1","#f4d19c"][stage]
        ridge=["#c08a5b","#a87b81","#96867b","#cc8a5e"][stage]
        far=["#a97752","#876b78","#77766f","#965a4d"][stage]
        if getattr(self, "alternate_universe", False):
            sky=["#d9c8ee","#b9c4e7","#e2b5cc","#f1d68c"][stage]
            ridge=["#876aaf","#6c83bd","#b06d98","#bd8a45"][stage]
            far=["#5b4d83","#455b89","#784c72","#6e4c35"][stage]
        if in_skull_zone:
            sky, ridge, far = "#8d718a", "#744b64", "#4d364f"
        self.canvas.create_rectangle(0,0,WIDTH,HEIGHT,fill=sky,outline="")
        self.canvas.create_oval(850,55,935,140,fill="#ffe5a8",outline="")
        # Hazy mesas and far mountain layers drift at different speeds.
        for layer,(col,base,amp,drift) in enumerate([(hexmix(ridge,"#ffffff",.10),185,34,.12),(ridge,238,48,.22),(far,284,39,.34)]):
            pts=[0,HEIGHT]
            for x in range(-15,WIDTH+25,10):
                xx=x+(self.progress*drift)%180
                yy=base+math.sin(xx*.010+layer*1.7)*amp+math.sin(xx*.024+layer)*amp*.26
                pts.extend([x,yy])
            pts.extend([WIDTH,HEIGHT])
            self.canvas.create_polygon(*pts,fill=col,outline="")
        # Randomly positioned Skull Sun landmark: a giant skull-faced sun over its own biome.
        skull_x = self.world_x(self.skull_sun["p"]) if hasattr(self, "skull_sun") else -2000
        if in_skull_zone and -320 < skull_x < WIDTH+320:
            self.canvas.create_oval(skull_x-105,54,skull_x+105,264,fill="#b34b5b",outline="#f5c17a",width=5)
            for ray in range(16):
                angle = ray * math.tau / 16 + self.elapsed*.025
                x1=skull_x+math.cos(angle)*108; y1=158+math.sin(angle)*108
                x2=skull_x+math.cos(angle)*132; y2=158+math.sin(angle)*132
                self.canvas.create_line(x1,y1,x2,y2,fill="#e39b75",width=4)
            self.canvas.create_oval(skull_x-45,112,skull_x+45,205,fill="#f1d2a3",outline="#542e49",width=3)
            self.canvas.create_oval(skull_x-31,138,skull_x-9,160,fill="#33263e",outline="#9c5362",width=2)
            self.canvas.create_oval(skull_x+9,138,skull_x+31,160,fill="#33263e",outline="#9c5362",width=2)
            self.canvas.create_polygon(skull_x-3,163,skull_x+4,163,skull_x,174,fill="#4a2c43",outline="")
            self.canvas.create_rectangle(skull_x-24,180,skull_x+24,196,fill="#d7b58e",outline="#542e49",width=2)
            for tooth_x in range(-15,16,10):
                self.canvas.create_line(skull_x+tooth_x,181,skull_x+tooth_x,194,fill="#71445a",width=2)
            self.canvas.create_text(skull_x,42,text="SKULL SUN TERRITORY",fill="#ffe7c4",font=("Arial",12,"bold"))
        # Each race leg has its own biome and track materials. Skull Sun remains a
        # separate, overriding landmark zone rather than becoming a whole stage.
        ground = ["#c78e59", "#a98c78", "#65766b", "#555966"][stage]
        track = ["#d5a16b", "#bca69a", "#718078", "#737783"][stage]
        lane_light = ["#e9bf8b", "#e1c9ba", "#a5b8a6", "#c5c7d0"][stage]
        lane_dark = ["#a8744c", "#7d625e", "#43594d", "#3d414c"][stage]
        if getattr(self, "alternate_universe", False):
            ground = ["#9984b7", "#777eb1", "#8b688f", "#9d7d55"][stage]
            track = ["#c2a8df", "#a5b4e0", "#c49abf", "#d7bb83"][stage]
            lane_light = ["#e2d5f2", "#d2daf4", "#edd0e7", "#f4e1b3"][stage]
            lane_dark = ["#6c588c", "#4c5888", "#69476c", "#6e5638"][stage]
        if in_skull_zone:
            ground, track, lane_light, lane_dark = "#89566d", "#9c6980", "#d39aaa", "#633a5a"
        self.canvas.create_rectangle(0,292,WIDTH,HEIGHT,fill=ground,outline="")
        # Distinct skyline/landmarks: open range, canyon pass, rain-soaked forest,
        # and the final urban district with layered buildings and streetlights.
        if stage == 0 and not in_skull_zone:
            for i in range(9):
                bx=(i*173-int(self.progress*.17))%(WIDTH+220)-100
                self.canvas.create_line(bx,285,bx,244,fill="#805c48",width=3)
                self.canvas.create_line(bx-18,253,bx+18,253,fill="#805c48",width=2)
                self.canvas.create_oval(bx-5,238,bx+5,248,fill="#d7b16e",outline="")
        elif stage == 1 and not in_skull_zone:
            # Red-rock pass: stacked canyon cliffs and narrow stone spires.
            for i in range(8):
                bx=(i*181-int(self.progress*.23))%(WIDTH+240)-100
                self.canvas.create_polygon(bx-48,295,bx-24,205+(i%3)*12,bx+2,170+(i%4)*10,bx+29,223,bx+52,295,fill=["#9b635e","#b87c70","#855b61"][i%3],outline="#6d4a50")
                self.canvas.create_polygon(bx-13,287,bx+1,220,bx+13,287,fill="#d1a092",outline="")
        elif stage == 2 and not in_skull_zone:
            # Rain country: dark fir trees, mist, and visible slanting rain.
            for i in range(13):
                bx=(i*103-int(self.progress*.28))%(WIDTH+150)-60
                self.canvas.create_rectangle(bx-4,230,bx+4,300,fill="#3d5148",outline="")
                for layer in range(3):
                    yy=210+layer*25
                    self.canvas.create_polygon(bx,yy-28-layer*3,bx-25+layer*5,yy+15,bx+25-layer*5,yy+15,fill=["#405c50","#344a43","#293d39"][layer],outline="")
            for i in range(22):
                rx=(i*67+int(self.elapsed*38))%WIDTH
                ry=300+(i*47)%300
                self.canvas.create_line(rx,ry,rx-9,ry+20,fill="#b6d2d2",width=1)
        elif stage == 3 and not in_skull_zone:
            # Final city: layered masonry buildings, lit windows, rooftop silhouettes.
            for i in range(12):
                bx=(i*108-int(self.progress*.20))%(WIDTH+160)-70
                bw=62+(i%3)*16
                bh=70+(i%5)*19
                top=292-bh
                self.canvas.create_rectangle(bx,top,bx+bw,300,fill=["#484c5b","#5a5660","#3f4654"][i%3],outline="#292d38",width=2)
                self.canvas.create_line(bx+5,top+8,bx+bw-5,top+8,fill="#77727a",width=2)
                for wx in range(int(bx+10),int(bx+bw-6),17):
                    for wy in range(int(top+17),285,23):
                        self.canvas.create_rectangle(wx,wy,wx+7,wy+10,fill="#e8c98c" if (i+wx+wy)%3 else "#8395a7",outline="")
                if i%3==0:
                    self.canvas.create_line(bx+bw/2,top,bx+bw/2,top-22,fill="#343844",width=3)
            # Streetlamps give the last stretch a city-street silhouette.
            for i in range(5):
                lx=(i*260-int(self.progress*.35))%(WIDTH+100)-40
                self.canvas.create_line(lx,290,lx,340,fill="#333744",width=4)
                self.canvas.create_line(lx,291,lx+20,282,fill="#333744",width=3)
                self.canvas.create_oval(lx+13,276,lx+25,288,fill="#f6dba0",outline="#fff0c8",width=1)
        # Race track with surface texture and lane separators.
        self.canvas.create_rectangle(0,315,WIDTH,612,fill=track,outline="")
        for j in range(10):
            y=322+j*31
            self.canvas.create_line(0,y,WIDTH,y,fill=lane_light,width=1)
        if stage == 3 and not in_skull_zone:
            # City paving stones scroll beneath the racers.
            offset=int(self.progress*.8)%90
            for yy in range(324,612,35):
                self.canvas.create_line(0,yy,WIDTH,yy,fill="#555a67",width=1)
                for xx in range(-90+offset,WIDTH+90,90):
                    self.canvas.create_line(xx,yy,xx,yy+35,fill="#626775",width=1)
            self.canvas.create_line(0,316,WIDTH,316,fill="#363a46",width=5)
        for lane in LANE_Y:
            self.canvas.create_line(0,lane+30,WIDTH,lane+30,fill=lane_light,width=2)
            self.canvas.create_line(0,lane+32,WIDTH,lane+32,fill=lane_dark,width=1)
        if in_skull_zone:
            for n in range(12):
                sx = (n*103 + int(self.progress*.7)) % WIDTH
                self.canvas.create_line(sx,305,sx-22,615,fill="#a76c81",width=1)
        # Stage-specific landmarks.
        for i in range(30):
            wp=i*580+210
            x=int((wp-self.progress*.57)%(WIDTH+120))-60
            y=255+(i*71)%355
            if stage==2 and i%4==0:
                self.canvas.create_polygon(x-25,y+28,x-16,y-8,x+4,y-19,x+28,y+20,x+17,y+29,fill="#817d77",outline="#9a948a")
            elif i%3==0:
                self.canvas.create_oval(x-20,y+17,x+27,y+29,fill="#ad7952",outline="")
                self.canvas.create_rectangle(x-3,y-12,x+5,y+26,fill="#3d7455",outline="")
                self.canvas.create_oval(x-10,y-4,x+2,y+8,fill="#48845e",outline="")
                self.canvas.create_oval(x+3,y+6,x+15,y+19,fill="#48845e",outline="")
            else:
                self.canvas.create_polygon(x-18,y+24,x-8,y+2,x+12,y-3,x+27,y+23,fill="#a77a5b",outline="")
        # Stage banners at each quarter of the long world.
        for idx,p in enumerate([4750,9500,14250]):
            x=self.world_x(p)
            if -40<x<WIDTH+40:
                self.canvas.create_line(x,270,x,620,fill="#f5e8cf",width=3)
                self.canvas.create_polygon(x,270,x+54,283,x,298,fill=GOLD,outline="")
                self.canvas.create_text(x+5,310,text=f"STAGE {idx+2}",anchor="w",fill=INK,font=("Arial",10,"bold"))

    def draw_depth_track(self):
        """Add a pseudo-3D, angled track with depth shading while retaining Pygame gameplay."""
        stage = min(3, int(self.progress / RACE_LENGTH * 4))
        in_skull_zone = hasattr(self, "skull_sun") and abs(self.progress-self.skull_sun["p"]) < self.skull_sun["width"] / 2
        track_colors = [("#d6a36d", "#b98653"), ("#bca49a", "#967d76"), ("#73857a", "#4e6258"), ("#777b88", "#555966")]
        near, far = track_colors[stage]
        if in_skull_zone:
            near, far = "#9c6980", "#633a5a"
        # Shaded lane ribbons, with diagonal perspective seams and raised edge rails.
        top_y, bottom_y = 312, 615
        for idx in range(4):
            y0 = top_y + idx * 72
            y1 = top_y + (idx + 1) * 72
            left0 = -20 + idx * 8
            right0 = WIDTH + 20 - idx * 8
            left1 = -35 + idx * 3
            right1 = WIDTH + 35 - idx * 3
            shade = far if idx % 2 == 0 else near
            self.canvas.create_polygon(left0, y0, right0, y0, right1, y1, left1, y1,
                                       fill=shade, outline="")
            # Receding diagonal track marks create a sense of speed and depth.
            for mark in range(9):
                mx = (mark * 155 - int(self.progress * (.55 + idx * .04))) % (WIDTH + 180) - 80
                self.canvas.create_polygon(mx, y0 + 5, mx + 38, y0 + 5,
                                           mx + 17, y1 - 5, mx - 21, y1 - 5,
                                           fill=hexmix(shade, "#ffffff", .10), outline="")
        self.canvas.create_line(0, top_y, WIDTH, top_y + 7, fill="#f4e0c0", width=4)
        self.canvas.create_line(0, bottom_y - 1, WIDTH, bottom_y - 13, fill="#302f38", width=7)
        # A subtle atmospheric veil keeps distant lanes visually behind the foreground.
        self.canvas.create_rectangle(0, top_y, WIDTH, top_y + 22, fill=hexmix(far, "#ffffff", .22), outline="")

    def draw_horse(self,x,y,coat,player=False,small=False,name="",ally=False,phase=0,stand=None,depth_scale=1.0):
        """Draw an animated horse and rider, scaled by lane depth for a pseudo-3D look."""
        s = (.78 if small else 1.0) * depth_scale
        x, y = float(x), float(y)
        character = name or ("Johnny Joestar" if player else "")
        look = CHARACTER_LOOKS.get(character, {
            "shirt":hexmix(coat,"#eee3cf",.25), "hair":"#5b4035",
            "headgear":"#54443b", "accent":"#d9bd80", "detail":"#f1dfbb"})
        coat = HORSE_COATS.get(character, coat)
        # Sandman is a runner, not a mounted racer. Draw an animated sprinting pose.
        if character == "Sandman":
            stride = math.sin(self.elapsed * 15.0 + phase)
            lift = abs(math.cos(self.elapsed * 15.0 + phase)) * 5
            self.canvas.create_oval(x-20*s,y+25*s,x+20*s,y+32*s,fill="#91694c",outline="")
            self.canvas.create_line(x-3*s,y+3*s,x-13*s+stride*9*s,y+17*s-lift,x-20*s-stride*8*s,y+25*s,fill="#7e543b",width=max(3,int(6*s)),smooth=True)
            self.canvas.create_line(x+4*s,y+3*s,x+13*s-stride*9*s,y+15*s-lift,x+21*s+stride*7*s,y+24*s,fill="#7e543b",width=max(3,int(6*s)),smooth=True)
            self.canvas.create_oval(x-10*s,y-43*s,x+10*s,y-23*s,fill="#8b5b3d",outline="#50392e",width=1)
            self.canvas.create_polygon(x-9*s,y-28*s,x+8*s,y-29*s,x+12*s,y-3*s,x-8*s,y+2*s,fill=look["shirt"],outline="#654a36",width=1)
            self.canvas.create_line(x-4*s,y-21*s,x-18*s-stride*7*s,y-10*s,x-25*s-stride*8*s,y-17*s,fill="#8b5b3d",width=max(3,int(5*s)),smooth=True)
            self.canvas.create_line(x+4*s,y-21*s,x+18*s+stride*7*s,y-33*s,x+25*s+stride*8*s,y-28*s,fill="#8b5b3d",width=max(3,int(5*s)),smooth=True)
            self.canvas.create_line(x-6*s,y-2*s,x+7*s,y-1*s,fill="#f0d5a4",width=max(2,int(3*s)))
            self.canvas.create_line(x-6*s,y-38*s,x+4*s,y-38*s,fill="#2b2524",width=max(2,int(3*s)))
            self.canvas.create_oval(x+2*s,y-37*s,x+5*s,y-34*s,fill="#211c1b",outline="")
            self.canvas.create_text(x,y-52*s,text="SANDMAN",fill=PAPER,font=("Arial",max(8,int(10*s)),"bold"),anchor="s")
            return
        coat_light = hexmix(coat, "#f6e8cf", .24)
        coat_dark = hexmix(coat, "#2b2528", .38)
        mane = "#3b302e" if character not in ("Diego Brando", "Johnny Joestar") else ("#d5bc78" if character == "Diego Brando" else "#c5b28b")

        # Ground shadow and drifting dust.
        self.canvas.create_oval(x-46*s,y+29*s,x+47*s,y+40*s,fill="#91694c",outline="")
        dust = abs(math.sin(self.elapsed*6.5+phase))*3*s
        self.canvas.create_oval(x-50*s-dust,y+28*s,x-34*s,y+35*s,fill="#d9b17d",outline="")
        self.canvas.create_oval(x-57*s-dust,y+31*s,x-43*s,y+37*s,fill="#e8c89c",outline="")

        # Tail, rear quarters, and four individually animated legs.
        self.canvas.create_line(x-31*s,y+1*s,x-43*s,y+8*s,x-53*s,y+17*s,
                                fill=mane,width=max(3,int(5*s)),smooth=True)
        self.canvas.create_line(x-51*s,y+15*s,x-57*s,y+23*s,fill=mane,width=max(2,int(3*s)))
        leg_defs = [(-25, .0), (-8, math.pi), (15, math.pi), (29, 0.0)]
        for idx, (dx, offset) in enumerate(leg_defs):
            hip = x + dx*s
            stride = math.sin(self.elapsed*13.5 + phase + offset)*10*s
            lift = max(0.0, math.cos(self.elapsed*13.5 + phase + offset))*4*s
            knee = hip + stride*.46
            hoof = hip + stride
            base_y = y + 8*s
            mid_y = y + 23*s - lift
            foot_y = y + 35*s - lift
            col = coat_dark if idx in (0,2) else "#463832"
            self.canvas.create_line(hip,base_y,knee,mid_y,fill=col,width=max(3,int(6*s)))
            self.canvas.create_line(knee,mid_y,hoof,foot_y,fill=col,width=max(2,int(4*s)))
            self.canvas.create_line(hoof-4*s,foot_y,hoof+4*s,foot_y,fill="#2d2625",width=max(2,int(3*s)))
            if idx in (1,3):
                self.canvas.create_line(hip+1*s,base_y+1*s,knee,mid_y,fill=coat_light,width=max(1,int(2*s)))

        # Main torso, haunch, shoulder muscle and neck.
        self.canvas.create_oval(x-43*s,y-13*s,x-7*s,y+25*s,fill=coat_dark,outline="#503c34",width=1)
        self.canvas.create_oval(x-38*s,y-16*s,x+31*s,y+25*s,fill=coat,outline="#503c34",width=1)
        self.canvas.create_oval(x-30*s,y-13*s,x+15*s,y+8*s,fill=coat_light,outline="")
        self.canvas.create_arc(x-30*s,y-11*s,x+23*s,y+22*s,start=190,extent=155,style="arc",outline=hexmix(coat,"#fff3de",.48),width=max(1,int(2*s)))
        self.canvas.create_polygon(x+12*s,y+5*s,x+22*s,y-18*s,x+36*s,y-27*s,x+43*s,y-15*s,
                                  x+33*s,y+10*s,x+25*s,y+17*s,fill=coat,outline="#503b33",width=1)
        self.canvas.create_polygon(x+20*s,y-4*s,x+27*s,y-19*s,x+37*s,y-24*s,x+33*s,y-7*s,
                                  fill=coat_light,outline="")

        # Mane crest, ears, head and muzzle. The silhouette stays proportional when scaled down.
        self.canvas.create_polygon(x+20*s,y-14*s,x+21*s,y-29*s,x+28*s,y-36*s,
                                  x+29*s,y-25*s,x+36*s,y-34*s,x+37*s,y-21*s,
                                  x+43*s,y-25*s,x+39*s,y-10*s,fill=mane,outline="")
        self.canvas.create_polygon(x+29*s,y-25*s,x+27*s,y-39*s,x+34*s,y-33*s,fill=coat_dark,outline="#503b33")
        self.canvas.create_polygon(x+37*s,y-25*s,x+43*s,y-37*s,x+45*s,y-23*s,fill=coat_dark,outline="#503b33")
        self.canvas.create_oval(x+30*s,y-34*s,x+53*s,y-17*s,fill=coat_light,outline="#563e35",width=1)
        self.canvas.create_oval(x+43*s,y-25*s,x+54*s,y-17*s,fill=coat,outline="#563e35",width=1)
        self.canvas.create_oval(x+46*s,y-22*s,x+49*s,y-20*s,fill="#211d21",outline="")
        self.canvas.create_oval(x+37*s,y-30*s,x+41*s,y-26*s,fill="#fff0ce",outline="")
        self.canvas.create_oval(x+38*s,y-29*s,x+40*s,y-27*s,fill="#292229",outline="")
        self.canvas.create_line(x+37*s,y-21*s,x+45*s,y-19*s,fill=coat_dark,width=max(1,int(2*s)))
        # Extra tack, cheek bridle, neck highlights and flowing mane give the horses more depth.
        self.canvas.create_line(x+30*s,y-31*s,x+33*s,y-13*s,x+44*s,y-9*s,fill="#3c2b2a",width=max(1,int(2*s)))
        self.canvas.create_line(x+29*s,y-15*s,x+18*s,y-7*s,x+8*s,y-5*s,fill="#3c2b2a",width=max(1,int(2*s)))
        self.canvas.create_line(x+23*s,y-27*s,x+13*s,y-19*s,x+7*s,y-13*s,fill=mane,width=max(2,int(4*s)),smooth=True)
        self.canvas.create_line(x+25*s,y-26*s,x+18*s,y-15*s,x+15*s,y-8*s,fill=coat_light,width=max(1,int(2*s)),smooth=True)
        self.canvas.create_line(x-34*s,y-8*s,x-20*s,y-14*s,x-5*s,y-10*s,fill=coat_light,width=max(1,int(2*s)),smooth=True)
        self.canvas.create_line(x-24*s,y+13*s,x-12*s,y+17*s,x+2*s,y+15*s,fill=coat_light,width=max(1,int(2*s)),smooth=True)
        # Face stripe and a few breed-specific dapples on the light-colored Slow Dancer.
        if character == "Johnny Joestar":
            self.canvas.create_polygon(x+34*s,y-31*s,x+38*s,y-31*s,x+42*s,y-21*s,x+39*s,y-20*s,
                                      fill="#f5eee0",outline="")
            for dx,dy in [(-25,-4),(-12,8),(2,-7)]:
                self.canvas.create_oval(x+dx*s,y+dy*s,x+(dx+4)*s,y+(dy+4)*s,fill="#92989a",outline="")

        # Leather tack, stirrups, blue/gold trim and a compact saddle blanket.
        self.canvas.create_line(x-28*s,y+2*s,x+35*s,y+1*s,fill="#5a352e",width=max(2,int(3*s)))
        self.canvas.create_polygon(x-12*s,y-14*s,x+15*s,y-17*s,x+26*s,y+2*s,
                                  x+4*s,y+8*s,x-14*s,y+1*s,fill="#643b33",outline="#33252a",width=1)
        self.canvas.create_polygon(x-13*s,y-12*s,x+11*s,y-15*s,x+19*s,y-1*s,
                                  x+2*s,y+4*s,x-12*s,y-1*s,fill=look["accent"],outline="#48302b",width=1)
        self.canvas.create_line(x-10*s,y-7*s,x+12*s,y-10*s,fill="#f4e2ad",width=max(1,int(2*s)))
        self.canvas.create_oval(x-34*s,y+1*s,x-20*s,y+17*s,fill="#79503a",outline="#d1a45d",width=1)
        self.canvas.create_line(x-30*s,y+4*s,x-24*s,y+12*s,fill="#d7b36a",width=1)
        self.canvas.create_line(x+20*s,y+4*s,x+28*s,y+18*s,fill="#bd9a62",width=max(1,int(2*s)))
        self.canvas.create_polygon(x+20*s,y+14*s,x+32*s,y+13*s,x+34*s,y+20*s,x+22*s,y+21*s,
                                  fill="#4c3934",outline="#d0ad68",width=1)

        # Distinct rider uniform and silhouette.
        shirt = look["shirt"]
        self.canvas.create_polygon(x-8*s,y-20*s,x+3*s,y-39*s,x+22*s,y-33*s,
                                  x+20*s,y-12*s,x+4*s,y-8*s,fill=shirt,outline="#49332f",width=1)
        self.canvas.create_polygon(x-3*s,y-18*s,x-13*s,y-22*s,x-22*s,y-13*s,x-12*s,y-10*s,
                                  fill=look["accent"],outline="#49332f",width=1)
        # Belt and a sleeve seam give the rider more than a flat torso shape.
        self.canvas.create_line(x-6*s,y-17*s,x+17*s,y-19*s,fill=look["detail"],width=max(1,int(2*s)))
        self.canvas.create_line(x+5*s,y-35*s,x+16*s,y-25*s,fill=hexmix(shirt,"#ffffff",.38),width=max(1,int(2*s)))
        if character == "Johnny Joestar":
            # Small cream stars repeat the pattern of Johnny's fitted racing outfit.
            for dx, dy in [(-4,-29),(7,-22),(1,-14)]:
                self.canvas.create_text(x+dx*s,y+dy*s,text="★",fill="#fff0c6",
                                        font=("Arial",max(6,int(7*s)),"bold"))
        elif character == "Gyro Zeppeli":
            # Crossed fastening bars evoke Gyro's armored, studded riding gear.
            self.canvas.create_line(x-3*s,y-34*s,x+14*s,y-19*s,fill="#e6dcb7",width=max(1,int(2*s)))
            self.canvas.create_oval(x-1*s,y-25*s,x+3*s,y-21*s,fill="#f0d16c",outline="#5c4a37",width=1)
        # Neck, face, hair and eye.
        self.canvas.create_rectangle(x+7*s,y-43*s,x+16*s,y-35*s,fill="#e2b18b",outline="")
        self.canvas.create_oval(x+2*s,y-56*s,x+23*s,y-36*s,fill="#edc5a4",outline="#69483b",width=1)
        self.canvas.create_oval(x+16*s,y-48*s,x+18*s,y-46*s,fill="#342b2d",outline="")
        self.canvas.create_line(x+15*s,y-42*s,x+21*s,y-42*s,fill="#a36e5b",width=max(1,int(1*s)))
        hair = look["hair"]
        self.canvas.create_polygon(x+1*s,y-46*s,x+2*s,y-55*s,x+10*s,y-59*s,
                                  x+17*s,y-55*s,x+23*s,y-50*s,x+15*s,y-50*s,
                                  x+10*s,y-45*s,x+8*s,y-51*s,fill=hair,outline="#46322e",width=1)
        if character == "Johnny Joestar":
            # Signature star-patterned cap and blue side flaps.
            self.canvas.create_polygon(x-1*s,y-49*s,x+3*s,y-61*s,x+15*s,y-64*s,
                                      x+25*s,y-55*s,x+24*s,y-48*s,x+12*s,y-51*s,
                                      fill=look["headgear"],outline="#375b75",width=1)
            self.canvas.create_polygon(x+1*s,y-52*s,x-5*s,y-42*s,x+2*s,y-41*s,x+7*s,y-50*s,
                                      fill=look["headgear"],outline="")
            self.canvas.create_text(x+11*s,y-56*s,text="★",fill="#fff0c6",font=("Arial",max(8,int(9*s)),"bold"))
            self.canvas.create_text(x+19*s,y-51*s,text="★",fill="#fff0c6",font=("Arial",max(8,int(7*s)),"bold"))
        elif character == "Gyro Zeppeli":
            self.canvas.create_oval(x-1*s,y-59*s,x+25*s,y-44*s,fill=look["headgear"],outline="#315a62",width=1)
            self.canvas.create_polygon(x-2*s,y-53*s,x+6*s,y-64*s,x+20*s,y-61*s,x+27*s,y-51*s,
                                      x+22*s,y-47*s,x+8*s,y-52*s,fill=look["headgear"],outline="#315a62",width=1)
            self.canvas.create_oval(x+4*s,y-53*s,x+11*s,y-47*s,fill="#d9edcf",outline="#b38b42",width=1)
            self.canvas.create_oval(x+14*s,y-53*s,x+21*s,y-47*s,fill="#d9edcf",outline="#b38b42",width=1)
            self.canvas.create_line(x+11*s,y-50*s,x+14*s,y-50*s,fill="#b38b42",width=2)
        elif character == "Mountain Tim":
            self.canvas.create_oval(x-8*s,y-57*s,x+31*s,y-49*s,fill=look["headgear"],outline="#3c2b2a",width=1)
            self.canvas.create_polygon(x+1*s,y-54*s,x+6*s,y-65*s,x+20*s,y-66*s,x+27*s,y-53*s,
                                      fill=look["headgear"],outline="#3c2b2a",width=1)
            self.canvas.create_line(x+3*s,y-53*s,x+24*s,y-53*s,fill="#d8b56f",width=max(1,int(2*s)))
            self.canvas.create_text(x+15*s,y-59*s,text="★",fill="#e7c779",font=("Arial",max(6,int(7*s)),"bold"))
        elif character == "Diego Brando":
            # Teal DIO helmet with gold lettering and elongated blond side locks.
            self.canvas.create_polygon(x-7*s,y-51*s,x-5*s,y-62*s,x+4*s,y-68*s,
                                      x+18*s,y-67*s,x+26*s,y-57*s,x+25*s,y-49*s,
                                      fill="#4e8c86",outline="#2b5552",width=1)
            self.canvas.create_oval(x-7*s,y-54*s,x+29*s,y-49*s,fill="#3c6d6b",outline="#d0b56d",width=1)
            self.canvas.create_text(x+10*s,y-59*s,text="DIO",fill="#f1d278",
                                    font=("Arial",max(6,int(7*s)),"bold"))
            self.canvas.create_polygon(x+2*s,y-49*s,x+8*s,y-44*s,x+5*s,y-32*s,
                                      x+1*s,y-39*s,fill="#e5cb83",outline="")
            self.canvas.create_polygon(x+21*s,y-49*s,x+25*s,y-43*s,x+23*s,y-31*s,
                                      x+18*s,y-39*s,fill="#e5cb83",outline="")
        elif character == "Pocoloco":
            self.canvas.create_polygon(x-4*s,y-51*s,x+2*s,y-61*s,x+18*s,y-61*s,x+27*s,y-51*s,x+20*s,y-47*s,x+3*s,y-48*s,fill="#e8d7f0",outline="#705f80",width=1)
            self.canvas.create_line(x+16*s,y-59*s,x+28*s,y-69*s,x+31*s,y-57*s,fill="#f0e5c6",width=max(2,int(3*s)))
            self.canvas.create_text(x+10*s,y-55*s,text="★",fill="#806a9e",font=("Arial",max(8,int(8*s)),"bold"))
            self.canvas.create_polygon(x-5*s,y-21*s,x+6*s,y-25*s,x+11*s,y-8*s,x-1*s,y-5*s,fill="#e8d9ed",outline="#7f6b91",width=1)
        elif character in ("Diego Brando (AU)", "Parallel Diego"):
            # Alternate Diego: pale swept-back hair, angular gold headband and a dark racing collar.
            self.canvas.create_polygon(x-8*s,y-57*s,x-15*s,y-69*s,x-2*s,y-65*s,
                                       x+7*s,y-72*s,x+18*s,y-63*s,x+24*s,y-54*s,
                                       x+12*s,y-57*s,x+2*s,y-52*s,
                                       fill=look["hair"],outline="#554b40",width=1)
            self.canvas.create_line(x-10*s,y-55*s,x+22*s,y-55*s,fill=look["headgear"],width=max(2,int(4*s)))
            self.canvas.create_oval(x+5*s,y-57*s,x+13*s,y-49*s,fill="#e7c84f",outline="#6e5928",width=1)
            self.canvas.create_line(x-7*s,y-31*s,x+8*s,y-25*s,x+19*s,y-31*s,fill="#f2df91",width=max(1,int(2*s)))
        elif character == "AU Gyro":
            # AU Gyro gets a distinct brimmed cap, metal cheek guards and a gold Spin emblem.
            self.canvas.create_polygon(x-17*s,y-58*s,x-12*s,y-68*s,x+10*s,y-69*s,
                                       x+19*s,y-59*s,x+25*s,y-55*s,x-20*s,y-54*s,
                                       fill=look["headgear"],outline="#51483b",width=1)
            self.canvas.create_line(x-15*s,y-53*s,x+19*s,y-53*s,fill="#d4b85f",width=max(2,int(3*s)))
            self.canvas.create_oval(x-3*s,y-35*s,x+7*s,y-25*s,fill="#e9c74f",outline="#6f5c32",width=1)
            self.canvas.create_text(x+2*s,y-30*s,text="S",fill="#55452c",font=("Arial",max(6,int(7*s)),"bold"))
        elif character == "Pocoloco (AU Trial)":
            # Pocoloco's AU sprite keeps dark skin/hair and a lilac, star-marked headpiece.
            self.canvas.create_polygon(x-17*s,y-56*s,x-10*s,y-66*s,x+10*s,y-66*s,
                                       x+20*s,y-56*s,x+14*s,y-52*s,x-14*s,y-52*s,
                                       fill="#eadcf1",outline="#5c4b6e",width=1)
            self.canvas.create_text(x+2*s,y-59*s,text="★",fill="#8165a4",font=("Arial",max(7,int(9*s)),"bold"))
            self.canvas.create_line(x-8*s,y-27*s,x+8*s,y-27*s,fill="#f0d8b5",width=max(1,int(2*s)))
        elif character == "Hot Pants":
            # White hood/scarf frames her face instead of using the generic headband.
            self.canvas.create_line(x-1*s,y-55*s,x-5*s,y-49*s,x-4*s,y-39*s,
                                    fill="#eee4d8",width=max(2,int(4*s)),smooth=True)
            self.canvas.create_line(x+23*s,y-53*s,x+27*s,y-45*s,x+24*s,y-35*s,
                                    fill="#eee4d8",width=max(2,int(4*s)),smooth=True)
            self.canvas.create_polygon(x-1*s,y-54*s,x+4*s,y-62*s,x+17*s,y-61*s,
                                      x+24*s,y-54*s,x+18*s,y-52*s,x+8*s,y-56*s,
                                      fill="#eee4d8",outline="#bba99b",width=1)
            self.canvas.create_line(x-1*s,y-21*s,x+20*s,y-21*s,fill="#f2e6d9",width=max(2,int(4*s)))
        elif character in ("Nikolai", "Marco"):
            self.canvas.create_line(x+1*s,y-53*s,x+23*s,y-51*s,fill=look["headgear"],width=max(2,int(5*s)))
            self.canvas.create_polygon(x+3*s,y-53*s,x+7*s,y-56*s,x+10*s,y-52*s,
                                      x+14*s,y-56*s,x+18*s,y-51*s,fill=look["accent"],outline="")
        # Hands on reins, boots, scarf/strap and character-specific accessory accents.
        self.canvas.create_line(x+17*s,y-28*s,x+29*s,y-17*s,fill="#e4b58d",width=max(2,int(4*s)))
        self.canvas.create_line(x+28*s,y-17*s,x+40*s,y-20*s,fill="#5c3d35",width=max(1,int(2*s)))
        self.canvas.create_line(x+4*s,y-12*s,x-6*s,y+2*s,fill="#4e3933",width=max(2,int(4*s)))
        self.canvas.create_line(x-7*s,y+1*s,x-14*s,y+4*s,fill="#2c282a",width=max(2,int(4*s)))
        if character == "Gyro Zeppeli":
            self.canvas.create_line(x+2*s,y-24*s,x-5*s,y-16*s,fill="#f2eee0",width=max(2,int(4*s)))
            self.canvas.create_oval(x+20*s,y-30*s,x+28*s,y-22*s,fill="#dbe7dc",outline="#8d9d9d",width=1)
        if character == "Johnny Joestar":
            self.canvas.create_polygon(x+6*s,y-33*s,x+12*s,y-30*s,x+6*s,y-24*s,
                                      x+1*s,y-28*s,fill="#f4e7c1",outline="")
        if ally:
            self.canvas.create_oval(x-4*s,y-75*s,x+5*s,y-66*s,fill=TEAL,outline=WHITE,width=1)
        if name:
            self.canvas.create_text(x,y-82*s,text=name,fill=PAPER,font=("Arial",max(8,int(10*s)),"bold"),anchor="s")
        if player and self.dodge>0:
            self.canvas.create_oval(x-50*s,y-89*s,x+54*s,y+43*s,outline=PURPLE,width=max(2,int(3*s)),dash=(5,4))

    def enter_town(self):
        self.checkpoint_progress = max(self.checkpoint_progress, self.progress)
        self.town_x, self.town_z = 0.0, 0.0
        self.town_combat_cooldown = 0.0
        self.town_player_hp = min(100.0, max(40.0, self.hp))
        self.town_enemy_count = 0; self.town_reward = 0; self.town_attacks = []
        self.town_enemies = []
        for i in range(7):
            self.town_enemies.append({"name":random.choice(["Outlaw","Rival Racer","Bandit","Stand User","Bounty Hunter"]),
                "x":random.uniform(-8,8),"z":random.uniform(7,27),"hp":90.0 if i==6 else random.choice([55.0,65.0,75.0]),
                "max_hp":90.0,"cooldown":random.uniform(.5,2.0),"color":random.choice(["#b86b48","#6d8eaa","#b5a15c","#8e75a9","#77956d"]),"stun":0.0,"alive":True,"boss":i==6})
        self.town_message="Checkpoint town! Explore the street and defeat its outlaws for race rewards."
        self.town_message_timer=4.0; self.state="town"; self.last_tick=time.perf_counter()

    def town_attack(self):
        if self.town_combat_cooldown>0: return
        self.town_combat_cooldown=.42; target=None; best=2.4
        for e in self.town_enemies:
            if e["alive"]:
                d=math.hypot(e["x"]-self.town_x,e["z"]-self.town_z)
                if d<best: target,best=e,d
        if not target:
            self.town_message="No enemy in range. Move close to an outlaw, then press SPACE."; self.town_message_timer=1.3; return
        damage=25+(12 if self.stand else 0); target["hp"]-=damage; target["stun"]=.7
        self.town_attacks.append({"x":target["x"],"z":target["z"],"timer":.28,"kind":"hit"})
        if target["hp"]<=0:
            target["alive"]=False; self.town_enemy_count+=1; reward=180 if target["boss"] else 75
            self.town_reward+=reward; self.score+=reward; self.overdrive=min(100,self.overdrive+12)
            self.town_message=f"{target['name']} defeated! +{reward} race points."; self.town_message_timer=2.1
            if target["boss"]: self.hp=min(self.max_hp(),self.hp+22)
        else:
            self.town_message=f"Hit {target['name']} for {damage} damage!"; self.town_message_timer=1.2

    def town_stand_attack(self):
        if not self.stand:
            self.town_message="No Stand equipped. Collect a Corpse Part during the race to awaken one."; self.town_message_timer=2.0; return
        if self.stand_cooldown>0:
            self.town_message=f"Stand recharging: {self.stand_cooldown:.1f}s"; self.town_message_timer=1.0; return
        self.stand_cooldown=3.0; hits=0
        for e in self.town_enemies:
            if e["alive"] and math.hypot(e["x"]-self.town_x,e["z"]-self.town_z)<5.2:
                e["hp"]-=36*max(.8,float(self.stand.get("combat",1))); e["stun"]=1.0; hits+=1
                self.town_attacks.append({"x":e["x"],"z":e["z"],"timer":.4,"kind":"stand"})
                if e["hp"]<=0:
                    e["alive"]=False; self.town_enemy_count+=1; self.score+=75; self.town_reward+=75
        self.town_message=f"{self.stand['name']} attacks! Hit {hits} outlaw(s)."; self.town_message_timer=1.8

    def town_interact(self):
        remaining=sum(1 for e in self.town_enemies if e["alive"])
        if remaining==0:
            self.hp=min(self.max_hp(),self.hp+35); self.stamina=min(100,self.stamina+45)
            self.town_message="Town cleared! The doctor restored health and stamina. Press T to return."
        else: self.town_message=f"Town doctor: {remaining} troublemaker(s) remain. Defeat them to earn rewards."
        self.town_message_timer=2.8

    def update_town(self,dt):
        self.elapsed+=dt; self.town_message_timer=max(0,self.town_message_timer-dt)
        self.town_combat_cooldown=max(0,self.town_combat_cooldown-dt); self.stand_cooldown=max(0,self.stand_cooldown-dt)
        speed=5.2*dt*(1.55 if "shift_l" in self.keys or "shift_r" in self.keys else 1)
        dx=(1 if "d" in self.keys or "right" in self.keys else 0)-(1 if "a" in self.keys or "left" in self.keys else 0)
        dz=(1 if "w" in self.keys or "up" in self.keys else 0)-(1 if "s" in self.keys or "down" in self.keys else 0)
        if dx and dz: dx*=.7071; dz*=.7071
        self.town_x=clamp(self.town_x+dx*speed,-13,13); self.town_z=clamp(self.town_z+dz*speed,-3,32)
        for e in self.town_enemies:
            if not e["alive"]: continue
            e["stun"]=max(0,e["stun"]-dt); e["cooldown"]-=dt
            dist=math.hypot(e["x"]-self.town_x,e["z"]-self.town_z)
            if e["stun"]<=0 and dist>1.35:
                step=min(dt*1.5,dist-1.25); e["x"]+=(self.town_x-e["x"])/max(.01,dist)*step; e["z"]+=(self.town_z-e["z"])/max(.01,dist)*step
            if dist<1.5 and e["cooldown"]<=0 and e["stun"]<=0:
                e["cooldown"]=random.uniform(1.1,1.8); self.town_player_hp-=random.uniform(4,8)*(1.4 if e["boss"] else 1)
                self.town_attacks.append({"x":self.town_x,"z":self.town_z,"timer":.25,"kind":"enemy"})
                self.town_message=f"{e['name']} hit you! Fight back with SPACE."; self.town_message_timer=1.2
                if self.town_player_hp<=0:
                    self.town_player_hp=55; self.town_x,self.town_z=0,0; self.notify("You recovered at the town clinic.",2.5)
        for fx in self.town_attacks: fx["timer"]-=dt
        self.town_attacks=[fx for fx in self.town_attacks if fx["timer"]>0]

    def draw_town_3d(self):
        surf=self.canvas.surface; surf.fill((203,158,109))
        for i in range(24): pygame.draw.rect(surf,(min(255,115+i*4),min(255,157+i*3),min(255,185+i*2)),(0,i*12,WIDTH,12))
        horizon=int(HEIGHT*.43)
        pygame.draw.polygon(surf,(155,101,69),[(0,horizon+55),(90,horizon-8),(205,horizon+42),(335,horizon-32),(480,horizon+30),(640,horizon-18),(795,horizon+38),(960,horizon-4),(1120,horizon+50),(1120,HEIGHT),(0,HEIGHT)])
        pygame.draw.polygon(surf,(120,79,59),[(0,horizon+72),(130,horizon+22),(255,horizon+70),(410,horizon+8),(565,horizon+72),(770,horizon+18),(940,horizon+68),(1120,horizon+27),(1120,HEIGHT),(0,HEIGHT)])
        focal=650.0
        def project(wx,wz,height=0):
            depth=wz-self.town_z+5
            if depth<1: return None
            scale=focal/depth; return (int(WIDTH*.5+(wx-self.town_x)*scale),int(horizon+focal*1.22/depth-height*scale),scale,depth)
        road=[project(-5.5,34),project(5.5,34),project(5.5,-1),project(-5.5,-1)]
        if all(road): pygame.draw.polygon(surf,(184,132,82),[p[:2] for p in road])
        for lane in (-3.8,-2,0,2,3.8):
            a,b=project(lane,33),project(lane,-1)
            if a and b: pygame.draw.line(surf,(142,96,61),a[:2],b[:2],max(1,int(min(4,b[2]*.012))))
        palette=[(145,91,62),(170,113,73),(125,83,61),(188,137,91),(133,102,79)]
        buildings=[]
        for z in range(-1,39,5):
            for side in (-1,1):
                wx=side*(7.6+(int(z*3+(0 if side<0 else 7))%5)*.42); bh=2.4+(int(z*2+(0 if side<0 else 3))%4)*.43
                buildings.append((z,side,wx,bh,palette[int(abs(z*7+side*11))%len(palette)]))
        for z,side,wx,bh,col in sorted(buildings,reverse=True):
            pr=project(wx,z); top=project(wx,z,bh)
            if not pr or not top or pr[3]<1.8 or pr[3]>60 or not -250<pr[0]<WIDTH+250: continue
            x,y,sc,depth=pr; fw=max(4,int(2.8*sc)); sw=max(3,int(2.1*sc)); hp=max(8,int(bh*sc)); yt=top[1]
            shade=tuple(max(0,c-38) for c in col); light=tuple(min(255,c+22) for c in col)
            pygame.draw.polygon(surf,shade,[(x+fw,yt),(x+fw+sw,yt+int(5*sc)),(x+fw+sw,y+int(5*sc)),(x+fw,y)])
            pygame.draw.rect(surf,col,(x,yt,fw,hp)); pygame.draw.polygon(surf,light,[(x,yt),(x+fw,yt),(x+fw+int(2*sc),yt-int(4*sc)),(x+int(2*sc),yt-int(4*sc))])
            pygame.draw.rect(surf,(82,52,39),(x+fw//3,y-int(2*sc),max(2,fw//3),max(4,int(1.2*sc))))
            for wxi in (x+int(.35*fw),x+int(.73*fw)):
                pygame.draw.rect(surf,(105,177,190),(wxi,yt+int(hp*.34),max(2,int(.42*sc)),max(3,int(.55*sc))))
        # Enemies are drawn in depth order, with perspective scaling and visible health bars.
        for e in sorted(self.town_enemies,key=lambda e:e["z"],reverse=True):
            if not e["alive"]: continue
            pr=project(e["x"],e["z"])
            if not pr or pr[3]<1.3 or pr[3]>42 or not -100<pr[0]<WIDTH+100: continue
            x,y,sc,depth=pr; h=max(15,int((34 if e["boss"] else 25)*sc)); w=max(8,int((18 if e["boss"] else 12)*sc)); col=PygameCanvas._color(e["color"])
            pygame.draw.ellipse(surf,(82,58,43),(x-w,y-2,x+w,y+max(2,int(4*sc))))
            pygame.draw.rect(surf,(35,31,37),(x-w//2,y-h,w,h)); pygame.draw.rect(surf,col,(x-w//2+1,y-h+2,max(2,w-2),int(h*.53)))
            pygame.draw.circle(surf,(224,183,150),(x,y-h-max(2,int(3*sc))),max(3,int(5*sc)))
            pygame.draw.line(surf,(33,27,32),(x-w//2,y-h//2),(x-w,y),max(1,int(sc*2))); pygame.draw.line(surf,(33,27,32),(x+w//2,y-h//2),(x+w,y),max(1,int(sc*2)))
            bw=max(14,int(28*sc)); by=y-h-max(10,int(9*sc)); pygame.draw.rect(surf,(54,34,38),(x-bw//2,by,bw,max(3,int(3*sc))))
            pygame.draw.rect(surf,(218,74,79),(x-bw//2,by,int(bw*max(0,e["hp"])/e["max_hp"]),max(3,int(3*sc))))
            if e["boss"]: self._town_text(e["name"],x,by-10,12,(255,226,157),True)
        px,py=WIDTH//2,HEIGHT-112
        pygame.draw.ellipse(surf,(93,61,42),(px-31,py+43,62,16))
        if self.stand:
            sk=self.stand.get("name") if self.stand.get("name") in self.stand_sprite_images else ("PART 8" if any(t in self.stand.get("name","") for t in ("Wet","Wonder","Killer Queen")) else "PART 7")
            spr=self.stand_sprite_images.get(sk)
            if spr: surf.blit(pygame.transform.smoothscale(spr,(68,90)),(px-75,py-30))
        pygame.draw.polygon(surf,(50,57,78),[(px-14,py-20),(px+14,py-20),(px+21,py+28),(px-20,py+28)])
        pygame.draw.circle(surf,(230,188,159),(px,py-31),13); pygame.draw.polygon(surf,(45,40,48),[(px-14,py-34),(px-10,py-49),(px+8,py-48),(px+16,py-35),(px+7,py-39),(px-5,py-39)])
        pygame.draw.line(surf,(35,31,38),(px-10,py-5),(px-23,py+21),6); pygame.draw.line(surf,(35,31,38),(px+10,py-5),(px+23,py+21),6)
        pygame.draw.rect(surf,(19,24,34),(18,16,395,92),border_radius=10); pygame.draw.rect(surf,(229,185,91),(18,16,395,92),2,border_radius=10)
        self._town_text("CHECKPOINT TOWN  •  3D EXPLORATION",31,27,17,(244,205,119),True,"topleft")
        self._town_text(f"RACE CHECKPOINT {self.checkpoint_index}/4   •   BOUNTY {self.town_enemy_count}/7",31,55,13,(242,235,217),True,"topleft")
        self._town_text(f"TOWN HP {int(self.town_player_hp)}",31,79,13,(245,137,135),True,"topleft")
        pygame.draw.rect(surf,(25,29,39),(WIDTH-380,16,360,80),border_radius=10); pygame.draw.rect(surf,(115,196,190),(WIDTH-380,16,360,80),2,border_radius=10)
        self._town_text("WASD / ARROWS Move  •  SHIFT Sprint",WIDTH-365,27,13,WHITE,True,"topleft")
        self._town_text("SPACE Punch  •  K Stand ability",WIDTH-365,51,13,WHITE,True,"topleft")
        self._town_text("E Talk / heal  •  T or Q Return",WIDTH-365,74,13,WHITE,True,"topleft")
        if self.town_message_timer>0:
            pygame.draw.rect(surf,(19,23,33),(WIDTH//2-350,HEIGHT-53,700,35),border_radius=8); pygame.draw.rect(surf,(226,184,91),(WIDTH//2-350,HEIGHT-53,700,35),1,border_radius=8)
            self._town_text(self.town_message,WIDTH//2,HEIGHT-36,13,(255,238,199),True)
        for fx in self.town_attacks:
            pr=project(fx["x"],fx["z"])
            if pr: pygame.draw.circle(surf, (255,220,116) if fx["kind"]!="enemy" else (255,105,108), (pr[0],pr[1]-15), max(5,int((24 if fx["kind"]=="stand" else 14)*pr[2])), 2)

    def _town_text(self,text,x,y,size=16,color=(255,255,255),bold=False,anchor="center"):
        font=pygame.font.SysFont("Arial",max(8,int(size)),bold=bold); image=font.render(str(text),True,color); rect=image.get_rect()
        if anchor=="topleft": rect.topleft=(int(x),int(y))
        else: rect.center=(int(x),int(y))
        self.canvas.surface.blit(image,rect)

    def draw_stand_companion(self, x, y, stand, scale=1.0, phase=0.0, love_train=False):
        """Draw a distinct, proportional manga-inspired Stand sprite behind its user."""
        if not stand:
            return
        c = self.canvas
        name = stand.get("name", "Stand")
        s = max(0.45, float(scale))
        sprite_key = name if name in self.stand_sprite_images else ("PART 8" if any(k in name for k in ("Soft & Wet", "Wonder of U", "Killer Queen", "Paisley Park", "Speed King", "Born This Way", "King Nothing", "Vitamin C", "Blue Hawaii", "Doctor Wu", "Ozon Baby")) else "PART 7")
        sprite = self.stand_sprite_images.get(sprite_key)
        if sprite is not None:
            sw, sh = max(24, int(68*s)), max(32, int(92*s))
            rendered = pygame.transform.smoothscale(sprite, (sw, sh))
            bob = math.sin(float(phase)*3.0)*2.0*s
            c.surface.blit(rendered, (int(x-sw/2), int(y-sh+bob)))
            if name == "D4C" and love_train:
                pygame.draw.arc(c.surface, (255,232,157), (int(x-43*s),int(y-98*s),int(86*s),int(130*s)), .2, 5.5, max(1,int(2*s)))
            return
        bob = math.sin(float(phase)*3.0)*2.0*s
        x, y = float(x), float(y) + bob
        col = stand.get("color", "#9a9bc8")
        dark = hexmix(col, "#171823", .53)
        light = hexmix(col, "#fff5df", .54)
        outline = "#24212d"
        # Ground haze and unique aura silhouettes; the actual body is always drawn separately.
        c.create_oval(x-29*s, y+30*s, x+29*s, y+39*s,
                      fill="#342b3a", outline="")
        if name == "D4C" and love_train:
            for n in range(4):
                c.create_arc(x-45*s-n*6*s, y-99*s-n*5*s,
                             x+45*s+n*6*s, y+36*s+n*5*s,
                             start=30+phase*28, extent=270,
                             style="arc", outline="#ffe9a0", width=max(1,int(2*s)))
        # Legs, arms, and torso are separate shapes to keep each silhouette readable.
        if name in ("Tusk Act 1", "Hey Ya!"):
            c.create_line(x-7*s,y+1*s,x-12*s,y+27*s,fill=col,width=max(3,int(7*s)))
            c.create_line(x+7*s,y+1*s,x+13*s,y+27*s,fill=col,width=max(3,int(7*s)))
            c.create_line(x-17*s,y-42*s,x-28*s,y-20*s,x-20*s,y-12*s,fill=col,width=max(2,int(6*s)))
            c.create_line(x+17*s,y-42*s,x+27*s,y-22*s,x+20*s,y-12*s,fill=col,width=max(2,int(6*s)))
        else:
            c.create_polygon(x-13*s,y-10*s,x-10*s,y+25*s,x-2*s,y+27*s,
                             x-1*s,y+2*s,x+5*s,y+2*s,x+7*s,y+27*s,
                             x+15*s,y+25*s,x+15*s,y-11*s,
                             fill=dark,outline=outline,width=max(1,int(1.2*s)))
            c.create_line(x-15*s,y-43*s,x-27*s,y-21*s,x-22*s,y-7*s,
                          fill=col,width=max(2,int(7*s)))
            c.create_line(x+15*s,y-43*s,x+26*s,y-23*s,x+20*s,y-8*s,
                          fill=col,width=max(2,int(7*s)))
        if name == "Scary Monsters":
            # Dinosaur limbs, claws, and a tail unique to Diego's Stand.
            c.create_line(x-7*s,y+8*s,x-23*s,y+17*s,x-37*s,y+13*s,
                          fill=col,width=max(3,int(7*s)))
            c.create_polygon(x-12*s,y-49*s,x-22*s,y-59*s,x-17*s,y-40*s,
                             x-27*s,y-32*s,x-11*s,y-32*s,fill=col,outline=outline,width=1)
            c.create_polygon(x+12*s,y-49*s,x+22*s,y-59*s,x+17*s,y-40*s,
                             x+27*s,y-32*s,x+11*s,y-32*s,fill=col,outline=outline,width=1)
        elif name == "D4C":
            c.create_polygon(x-22*s,y-48*s,x-29*s,y-36*s,x-20*s,y-8*s,
                             x-12*s,y+3*s,x+12*s,y+3*s,x+20*s,y-8*s,
                             x+29*s,y-36*s,x+22*s,y-48*s,x+10*s,y-55*s,
                             x-10*s,y-55*s,fill=col,outline=outline,width=max(1,int(2*s)))
        elif name == "The World (Alternate Universe)":
            # AU THE WORLD: broad gold armor, segmented chest, shoulder guards and a horned helmet.
            c.create_polygon(x-23*s,y-48*s,x-31*s,y-35*s,x-25*s,y-8*s,
                             x-15*s,y+4*s,x+15*s,y+4*s,x+25*s,y-8*s,
                             x+31*s,y-35*s,x+23*s,y-48*s,x+12*s,y-56*s,
                             x-12*s,y-56*s,fill="#d8b63e",outline="#473b26",width=max(1,int(2*s)))
            c.create_polygon(x-16*s,y-42*s,x,y-34*s,x+16*s,y-42*s,
                             x+11*s,y-12*s,x,y-5*s,x-11*s,y-12*s,
                             fill="#f5dc68",outline="#6b5426",width=max(1,int(1.5*s)))
            c.create_line(x-10*s,y-31*s,x+10*s,y-31*s,fill="#4c3b28",width=max(1,int(2*s)))
            c.create_line(x-9*s,y-22*s,x+9*s,y-22*s,fill="#4c3b28",width=max(1,int(2*s)))
            c.create_polygon(x-17*s,y-49*s,x-29*s,y-63*s,x-7*s,y-58*s,
                             x-3*s,y-48*s,fill="#f1d45c",outline="#473b26",width=1)
            c.create_polygon(x+17*s,y-49*s,x+29*s,y-63*s,x+7*s,y-58*s,
                             x+3*s,y-48*s,fill="#f1d45c",outline="#473b26",width=1)
            c.create_oval(x-9*s,y-51*s,x+9*s,y-35*s,fill="#f8e68a",outline="#5b4829",width=1)
            c.create_line(x-6*s,y-43*s,x+6*s,y-43*s,fill="#403225",width=max(1,int(2*s)))
        elif name == "Ball Breaker":
            c.create_oval(x-25*s,y-32*s,x+25*s,y+13*s,outline="#f8dc8b",width=max(2,int(3*s)))
            for n in range(3):
                c.create_arc(x-34*s-n*4*s,y-67*s-n*3*s,x+34*s+n*4*s,y+15*s+n*3*s,
                             start=205+n*35,extent=220,style="arc",outline="#f2d486",width=max(1,int(2*s)))
        elif name == "Cream Starter":
            c.create_polygon(x-16*s,y-53*s,x-22*s,y-40*s,x-15*s,y-19*s,
                             x+15*s,y-19*s,x+22*s,y-40*s,x+16*s,y-53*s,
                             fill=light,outline=outline,width=max(1,int(1.5*s)))
            for n in (-10,0,10):
                c.create_line(x+n*s,y-16*s,x+n*s,y+5*s,fill=light,width=max(1,int(2*s)))
        elif name == "Mandom":
            c.create_oval(x-32*s,y-65*s,x+32*s,y-2*s,outline="#e2c4f6",width=max(2,int(3*s)))
            c.create_line(x,y-57*s,x,y-33*s,fill="#f4e7ce",width=max(1,int(2*s)))
            c.create_line(x,y-33*s,x+14*s,y-25*s,fill="#f4e7ce",width=max(1,int(2*s)))
        elif name == "Catch the Rainbow":
            c.create_polygon(x-24*s,y-53*s,x-22*s,y-33*s,x-15*s,y-21*s,
                             x+15*s,y-21*s,x+22*s,y-33*s,x+24*s,y-53*s,
                             x+12*s,y-61*s,x-12*s,y-61*s,fill=dark,outline="#c3edf0",width=max(1,int(2*s)))
            for n in range(5):
                xx=x+(-20+n*10)*s
                c.create_line(xx,y-8*s,xx-4*s,y+10*s,fill="#93dbe5",width=max(1,int(s)))
        elif name == "In a Silent Way":
            for n in range(3):
                c.create_arc(x-37*s-n*4*s,y-48*s-n*4*s,x+37*s+n*4*s,y+21*s+n*4*s,
                             start=200+phase*25,extent=135,style="arc",outline="#ffe0a0",width=max(1,int(2*s)))
        elif name == "Hey Ya!":
            c.create_oval(x-19*s,y-53*s,x+19*s,y-19*s,fill=light,outline=outline,width=1)
            c.create_oval(x-25*s,y-59*s,x-10*s,y-43*s,fill="#f6cf78",outline=outline,width=1)
            c.create_oval(x+10*s,y-59*s,x+25*s,y-43*s,fill="#f6cf78",outline=outline,width=1)
        elif name == "Ticket to Ride":
            c.create_arc(x-29*s,y-72*s,x+29*s,y-16*s,start=0,extent=180,style="arc",outline="#fff8df",width=max(1,int(3*s)))
            c.create_line(x-24*s,y-18*s,x-34*s,y+9*s,fill="#fff8df",width=max(2,int(5*s)))
            c.create_line(x+24*s,y-18*s,x+34*s,y+9*s,fill="#fff8df",width=max(2,int(5*s)))
        elif name == "Oh! Lonesome Me":
            c.create_line(x-30*s,y-44*s,x-37*s,y-4*s,x-23*s,y+8*s,
                          fill="#d7bf9d",width=max(2,int(3*s)))
            c.create_line(x+21*s,y-42*s,x+38*s,y-24*s,x+24*s,y-8*s,
                          fill="#d7bf9d",width=max(2,int(3*s)))
        elif name == "Civil War":
            c.create_polygon(x-23*s,y-48*s,x-15*s,y-61*s,x,y-54*s,x+15*s,y-61*s,
                             x+23*s,y-48*s,x+17*s,y+18*s,x-17*s,y+18*s,
                             fill=light,outline=outline,width=max(1,int(2*s)))
            c.create_line(x-14*s,y-34*s,x+14*s,y-8*s,fill=dark,width=max(2,int(3*s)))
            c.create_line(x+14*s,y-34*s,x-14*s,y-8*s,fill=dark,width=max(2,int(3*s)))
        elif name == "Chocolate Disco":
            c.create_polygon(x-22*s,y-49*s,x+22*s,y-49*s,x+18*s,y+20*s,x-18*s,y+20*s,
                             fill=col,outline=outline,width=max(1,int(2*s)))
            for j in range(3):
                c.create_line(x-15*s+j*10*s,y-42*s,x-15*s+j*10*s,y+13*s,fill=light,width=1)
            for j in range(4):
                c.create_line(x-17*s,y-34*s+j*14*s,x+17*s,y-34*s+j*14*s,fill=light,width=1)
        elif name == "Killer Queen":
            c.create_polygon(x-21*s,y-49*s,x-15*s,y-59*s,x-4*s,y-53*s,x+4*s,y-53*s,
                             x+15*s,y-59*s,x+21*s,y-49*s,x+16*s,y+19*s,x-16*s,y+19*s,
                             fill=col,outline=outline,width=max(1,int(2*s)))
            for side in (-1,1):
                c.create_polygon(x+side*13*s,y-47*s,x+side*24*s,y-62*s,x+side*19*s,y-35*s,
                                 fill=light,outline=outline,width=1)
        elif name == "Paisley Park":
            c.create_polygon(x-20*s,y-52*s,x-27*s,y-31*s,x-18*s,y+20*s,
                             x+18*s,y+20*s,x+27*s,y-31*s,x+20*s,y-52*s,
                             fill=col,outline=light,width=max(1,int(2*s)))
            c.create_arc(x-12*s,y-42*s,x+12*s,y-18*s,start=10,extent=320,style="arc",outline=light,width=2)
        elif name == "Born This Way":
            c.create_polygon(x-22*s,y-48*s,x-13*s,y-59*s,x,y-52*s,x+13*s,y-59*s,
                             x+22*s,y-48*s,x+16*s,y+20*s,x-16*s,y+20*s,
                             fill=col,outline=light,width=max(1,int(2*s)))
            for j in range(3):
                c.create_line(x-19*s+j*19*s,y-24*s,x-25*s+j*19*s,y-11*s,fill="#dff5ff",width=2)
        elif name == "Speed King":
            c.create_polygon(x-18*s,y-52*s,x-25*s,y-33*s,x-16*s,y+20*s,
                             x+16*s,y+20*s,x+25*s,y-33*s,x+18*s,y-52*s,
                             fill=col,outline=outline,width=max(1,int(2*s)))
            for j in range(3):
                c.create_line(x-12*s,y-36*s+j*15*s,x+12*s,y-30*s+j*15*s,fill="#fff0a6",width=2)
        elif name == "Wonder of U":
            c.create_polygon(x-20*s,y-51*s,x-31*s,y-33*s,x-24*s,y+23*s,
                             x+24*s,y+23*s,x+31*s,y-33*s,x+20*s,y-51*s,
                             fill=dark,outline="#c5b9e7",width=max(1,int(2*s)))
            c.create_polygon(x-23*s,y-56*s,x-16*s,y-70*s,x+16*s,y-70*s,
                             x+23*s,y-56*s,fill="#d9d4e7",outline=outline,width=1)
        else:
            c.create_polygon(x-18*s,y-47*s,x-22*s,y-29*s,x-14*s,y-8*s,
                             x+14*s,y-8*s,x+22*s,y-29*s,x+18*s,y-47*s,
                             fill=col,outline=outline,width=max(1,int(1.5*s)))
        # Main torso over the limbs; D4C has its split pale-blue/pink armor and seam marks.
        if name == "D4C":
            c.create_polygon(x-17*s,y-42*s,x-24*s,y-28*s,x-17*s,y-5*s,
                             x,y+1*s,x,y-46*s,fill="#d6d9ef",outline=outline,width=1)
            c.create_polygon(x,y-46*s,x+17*s,y-42*s,x+24*s,y-28*s,
                             x+17*s,y-5*s,x,y+1*s,fill="#d86ba9",outline=outline,width=1)
            for j in range(3):
                c.create_line(x-19*s,y-33*s+j*8*s,x-7*s,y-32*s+j*8*s,fill="#8d8da9",width=1)
                c.create_line(x+7*s,y-32*s+j*8*s,x+19*s,y-33*s+j*8*s,fill="#f5c6df",width=1)
        elif name == "Scary Monsters":
            c.create_polygon(x-17*s,y-43*s,x-23*s,y-31*s,x-16*s,y-8*s,
                             x-4*s,y+4*s,x+16*s,y-7*s,x+22*s,y-31*s,
                             x+15*s,y-43*s,x,y-48*s,fill=col,outline=outline,width=2)
            # Rib bands and dorsal plates make the silhouette read as a dinosaur.
            for j in range(3):
                c.create_line(x-12*s,y-28*s+j*6*s,x+10*s,y-27*s+j*6*s,
                              fill=hexmix(col,"#e3e3ac",.48),width=max(1,int(2*s)))
            for j in range(4):
                px=x+(-11+j*7)*s
                c.create_polygon(px,y-43*s,px-3*s,y-52*s,px+4*s,y-45*s,
                                 fill="#d6d39a",outline=outline,width=1)
        elif name not in ("Scary Monsters", "Wonder of U"):
            c.create_polygon(x-15*s,y-43*s,x-20*s,y-24*s,x-15*s,y-5*s,
                             x+15*s,y-5*s,x+20*s,y-24*s,x+15*s,y-43*s,
                             fill=col,outline=outline,width=max(1,int(1.5*s)))
        # Head / face / expression marks, unique headgear by Stand.
        if name.startswith("Tusk Act"):
            c.create_oval(x-17*s,y-75*s,x+17*s,y-43*s,fill=light,outline=outline,width=1)
            if name == "Tusk Act 1":
                c.create_polygon(x-12*s,y-68*s,x-24*s,y-98*s,x-7*s,y-80*s,fill=col,outline=outline,width=1)
                c.create_polygon(x+12*s,y-68*s,x+24*s,y-98*s,x+7*s,y-80*s,fill=col,outline=outline,width=1)
            elif name == "Tusk Act 2":
                c.create_polygon(x-15*s,y-64*s,x-24*s,y-86*s,x-5*s,y-78*s,fill="#e9dfbd",outline=outline,width=1)
                c.create_polygon(x+15*s,y-64*s,x+24*s,y-86*s,x+5*s,y-78*s,fill="#e9dfbd",outline=outline,width=1)
                c.create_arc(x-23*s,y-46*s,x+23*s,y-15*s,start=185,extent=170,style="arc",outline="#f6e8c7",width=2)
            elif name == "Tusk Act 3":
                c.create_polygon(x-20*s,y-60*s,x-22*s,y-83*s,x-8*s,y-75*s,x,y-84*s,x+8*s,y-75*s,x+22*s,y-83*s,x+20*s,y-60*s,fill=col,outline=outline,width=1)
                c.create_oval(x-8*s,y-62*s,x+8*s,y-46*s,fill="#22283c",outline="#e7eef6",width=1)
            else:
                c.create_polygon(x-22*s,y-62*s,x-24*s,y-83*s,x-12*s,y-75*s,x,y-91*s,x+12*s,y-75*s,x+24*s,y-83*s,x+22*s,y-62*s,fill="#e8e4dc",outline=outline,width=1)
                c.create_text(x,y-70*s,text="★",fill="#efcc70",font=("Arial",max(8,int(10*s)),"bold"))
            c.create_oval(x-8*s,y-63*s,x-3*s,y-57*s,fill=outline,outline="")
            c.create_oval(x+3*s,y-63*s,x+8*s,y-57*s,fill=outline,outline="")
            c.create_line(x-6*s,y-52*s,x+6*s,y-52*s,fill="#a96b72",width=1)
        elif name == "Scary Monsters":
            c.create_polygon(x-18*s,y-46*s,x-20*s,y-64*s,x-8*s,y-58*s,
                             x,y-67*s,x+8*s,y-58*s,x+20*s,y-64*s,
                             x+18*s,y-46*s,fill=col,outline=outline,width=1)
            c.create_oval(x-13*s,y-53*s,x-3*s,y-44*s,fill="#f2e8b0",outline=outline,width=1)
            c.create_oval(x+3*s,y-53*s,x+13*s,y-44*s,fill="#f2e8b0",outline=outline,width=1)
        elif name == "D4C":
            c.create_oval(x-16*s,y-68*s,x+16*s,y-40*s,fill="#ded9e9",outline=outline,width=1)
            # Signature long tapered ears with segmented braid-like markings.
            c.create_polygon(x-10*s,y-62*s,x-20*s,y-104*s,x-3*s,y-76*s,
                             x-5*s,y-61*s,fill="#d9d9ea",outline=outline,width=1)
            c.create_polygon(x+10*s,y-62*s,x+20*s,y-104*s,x+3*s,y-76*s,
                             x+5*s,y-61*s,fill="#d9d9ea",outline=outline,width=1)
            for j in range(4):
                yy=(76+j*6)*s
                c.create_line(x-15*s,y-yy,x-6*s,y-(yy-4*s),fill="#9c9bb5",width=max(1,int(2*s)))
                c.create_line(x+15*s,y-yy,x+6*s,y-(yy-4*s),fill="#9c9bb5",width=max(1,int(2*s)))
            c.create_line(x-10*s,y-55*s,x+10*s,y-55*s,fill="#6a506e",width=max(1,int(2*s)))
            for j in range(4):
                c.create_line(x-8*s+j*5*s,y-63*s,x-8*s+j*5*s,y-47*s,fill="#a6a2c4",width=1)
        elif name == "Wonder of U":
            c.create_oval(x-13*s,y-63*s,x+13*s,y-40*s,fill="#ded8ec",outline=outline,width=1)
            c.create_line(x-8*s,y-53*s,x+8*s,y-53*s,fill="#494558",width=2)
        elif name == "Ball Breaker":
            c.create_oval(x-16*s,y-71*s,x+16*s,y-39*s,fill="#d4bd7e",outline=outline,width=1)
            c.create_line(x-10*s,y-56*s,x+10*s,y-56*s,fill="#fff0ad",width=2)
        else:
            c.create_oval(x-15*s,y-68*s,x+15*s,y-39*s,fill=light,outline=outline,width=1)
            c.create_line(x-9*s,y-54*s,x-3*s,y-54*s,fill=outline,width=2)
            c.create_line(x+3*s,y-54*s,x+9*s,y-54*s,fill=outline,width=2)
        # Stamps/ornaments give each form a visual identity even at race scale.
        if name in ("Soft & Wet", "Soft & Wet: Go Beyond"):
            for j in range(3):
                bx=x+(-18+j*18)*s
                by=y-82*s+math.sin(phase*3+j)*3*s
                c.create_oval(bx-6*s,by-6*s,bx+6*s,by+6*s,fill="#b7f2ee",outline="#f7ffff",width=1)
                c.create_text(bx,by,text="★",fill="#4d929d",font=("Arial",max(6,int(8*s)),"bold"))
        elif name == "Soft & Wet: Go Beyond":
            # Bright, almost invisible spin bubble with a broken-ring trail.
            c.create_oval(x-19*s, y-88*s, x+19*s, y-50*s,
                          fill="#eaffff", outline="#75d9e4", width=max(1,int(2*s)))
            c.create_oval(x-25*s, y-94*s, x+25*s, y-44*s,
                          outline="#b9fff5", width=max(1,int(1.5*s)))
            c.create_text(x, y-69*s, text="∞", fill="#3f9ca9",
                          font=("Arial", max(7,int(15*s)), "bold"))
            for j in range(3):
                bx=x+(-23+j*23)*s
                by=y-97*s+math.sin(phase*4+j)*4*s
                c.create_oval(bx-4*s,by-4*s,bx+4*s,by+4*s,
                              fill="#f3ffff",outline="#70cbd7",width=1)
        elif name.startswith("Tusk Act"):
            for j in range(3):
                c.create_oval(x+(-9+j*9)*s,y-18*s,x+(-4+j*9)*s,y-12*s,fill="#f7e6ba",outline=outline,width=1)
            if name == "Tusk Act 4":
                for j in range(5):
                    c.create_text(x+(-20+j*10)*s,y-28*s,text="★",fill="#ffe6a3",font=("Arial",max(6,int(8*s)),"bold"))
        elif name == "The World (Alternate Universe)":
            c.create_polygon(x,y-37*s,x+8*s,y-29*s,x,y-21*s,x-8*s,y-29*s,
                             fill="#fff0a0",outline="#725a27",width=1)
            c.create_line(x-12*s,y-18*s,x+12*s,y-18*s,fill="#fff0a0",width=max(1,int(2*s)))
        elif name == "D4C":
            c.create_polygon(x-12*s,y-29*s,x-7*s,y-34*s,x-2*s,y-29*s,x-7*s,y-24*s,fill="#f8d7e7",outline="")
            c.create_polygon(x+12*s,y-29*s,x+17*s,y-34*s,x+22*s,y-29*s,x+17*s,y-24*s,fill="#f8d7e7",outline="")
        elif name == "Catch the Rainbow":
            for j in range(4):
                bx=x+(-12+j*8)*s
                c.create_line(bx,y+7*s,bx-4*s,y+16*s,fill="#ade6ec",width=1)
        # Sprite-style finish pass: shoulder plates, segmented forearms, boots,
        # chest emblem and high-contrast face marks make each Stand read as a small
        # manga character sprite rather than a generic colored silhouette.
        if not name.startswith("Tusk Act") and name not in ("Scary Monsters", "Wonder of U", "Hey Ya!"):
            c.create_polygon(x-17*s,y-42*s,x-28*s,y-39*s,x-24*s,y-27*s,x-15*s,y-25*s,
                             fill=light,outline=outline,width=max(1,int(s)))
            c.create_polygon(x+17*s,y-42*s,x+28*s,y-39*s,x+24*s,y-27*s,x+15*s,y-25*s,
                             fill=light,outline=outline,width=max(1,int(s)))
            c.create_polygon(x-12*s,y+17*s,x-11*s,y+27*s,x-1*s,y+27*s,x-2*s,y+17*s,
                             fill=dark,outline=outline,width=1)
            c.create_polygon(x+2*s,y+17*s,x+1*s,y+27*s,x+12*s,y+27*s,x+11*s,y+17*s,
                             fill=dark,outline=outline,width=1)
        # Small panel lines and chest crest are tailored by Stand color/name.
        c.create_line(x-10*s,y-34*s,x-5*s,y-28*s,x-10*s,y-22*s,
                      fill=light,width=max(1,int(1.5*s)))
        c.create_line(x+10*s,y-34*s,x+5*s,y-28*s,x+10*s,y-22*s,
                      fill=light,width=max(1,int(1.5*s)))
        if name == "D4C":
            c.create_polygon(x,y-37*s,x+5*s,y-31*s,x,y-25*s,x-5*s,y-31*s,
                             fill="#fff0d8",outline="#9b7193",width=1)
            for side in (-1,1):
                for j in range(3):
                    yy=(13+j*5)*s
                    c.create_line(x+side*16*s,y-yy,x+side*20*s,y-(yy-2*s),fill=light,width=1)
        elif name == "Catch the Rainbow":
            c.create_polygon(x-7*s,y-35*s,x,y-42*s,x+7*s,y-35*s,x,y-27*s,
                             fill="#d5f7f4",outline="#3e7f8a",width=1)
        elif name == "Ball Breaker":
            c.create_oval(x-6*s,y-36*s,x+6*s,y-24*s,fill="#f8dc8b",outline="#6c5730",width=1)
        elif name in ("Soft & Wet", "Soft & Wet: Go Beyond"):
            c.create_oval(x-5*s,y-35*s,x+5*s,y-25*s,fill="#e7ffff",outline="#3f9caa",width=1)
        elif name == "Soft & Wet: Go Beyond":
            c.create_oval(x-8*s,y-37*s,x+8*s,y-21*s,fill="#eaffff",outline="#3f9ca9",width=1)
            c.create_text(x,y-29*s,text="∞",fill="#3f9ca9",font=("Arial",max(6,int(10*s)),"bold"))
        elif name == "Wonder of U":
            c.create_line(x-13*s,y-31*s,x-5*s,y-27*s,x,y-31*s,x+5*s,y-27*s,x+13*s,y-31*s,
                          fill="#b8acd6",width=max(1,int(2*s)))
        # High-detail sprite pass: crisp silhouette rim, layered armor plates,
        # joint seams, hands, boots, and individualized face marks.  These are
        # original vector-drawn sprites (not stretched placeholders), so they
        # stay sharp at menu and in-race sizes.
        rim = hexmix(col, "#ffffff", .28)
        c.create_line(x-14*s, y-39*s, x-19*s, y-26*s, x-14*s, y-15*s,
                      fill=rim, width=max(1, int(1.6*s)), smooth=True)
        c.create_line(x+14*s, y-39*s, x+19*s, y-26*s, x+14*s, y-15*s,
                      fill=rim, width=max(1, int(1.6*s)), smooth=True)
        # Forearm gauntlets and articulated fingers make the arms read as a
        # humanoid Stand sprite instead of simple lines.
        for side in (-1, 1):
            ax, ay = x+side*23*s, y-17*s
            c.create_polygon(ax-side*4*s, ay-5*s, ax+side*2*s, ay-4*s,
                             ax+side*3*s, ay+5*s, ax-side*3*s, ay+6*s,
                             fill=light, outline=outline, width=max(1, int(s)))
            c.create_line(ax, ay+4*s, ax+side*2*s, ay+9*s,
                          fill=light, width=max(1, int(1.5*s)))
        # Chest armor is split into a shadow plate and a bright inset, with
        # markings tailored to recognizable Steel Ball Run Stand designs.
        if name.startswith("Tusk Act"):
            c.create_polygon(x-10*s,y-38*s,x,y-32*s,x+10*s,y-38*s,
                             x+7*s,y-20*s,x,y-16*s,x-7*s,y-20*s,
                             fill="#e9e0c8", outline="#34354a", width=max(1,int(s)))
            c.create_line(x,y-29*s,x,y-19*s,fill="#7d91b6",width=max(1,int(1.5*s)))
            if name == "Tusk Act 4":
                c.create_polygon(x-13*s,y-43*s,x-18*s,y-49*s,x-9*s,y-46*s,
                                 x,y-50*s,x+9*s,y-46*s,x+18*s,y-49*s,
                                 x+13*s,y-43*s,fill="#f0eadc",outline="#6b5a43",width=1)
        elif name == "Soft & Wet":
            c.create_polygon(x-12*s,y-42*s,x-7*s,y-46*s,x,y-42*s,
                             x+7*s,y-46*s,x+12*s,y-42*s,x+9*s,y-25*s,
                             x,y-20*s,x-9*s,y-25*s,fill="#d9f3ef",outline="#397e8c",width=max(1,int(s)))
            for side in (-1, 1):
                c.create_oval(x+side*7*s-2*s,y-37*s,x+side*7*s+2*s,y-33*s,
                              fill="#4d929d",outline="")
        elif name == "Scary Monsters":
            c.create_line(x-9*s,y-35*s,x-3*s,y-29*s,x-8*s,y-23*s,
                          fill="#e6e0ac",width=max(1,int(2*s)))
            c.create_line(x+9*s,y-35*s,x+3*s,y-29*s,x+8*s,y-23*s,
                          fill="#e6e0ac",width=max(1,int(2*s)))
            c.create_polygon(x-10*s,y-5*s,x-16*s,y+2*s,x-5*s,y+3*s,
                             fill="#d6d39a",outline=outline,width=1)
            c.create_polygon(x+10*s,y-5*s,x+16*s,y+2*s,x+5*s,y+3*s,
                             fill="#d6d39a",outline=outline,width=1)
        elif name == "D4C":
            # D4C's pink/pale split armor and forehead stripe are kept distinct.
            c.create_line(x,y-43*s,x,y-7*s,fill="#f7d9e8",width=max(1,int(2*s)))
            c.create_polygon(x-8*s,y-40*s,x-3*s,y-34*s,x-8*s,y-27*s,
                             fill="#e8e6f4",outline="#8c8ba5",width=1)
            c.create_polygon(x+8*s,y-40*s,x+3*s,y-34*s,x+8*s,y-27*s,
                             fill="#f4c0db",outline="#9d4f82",width=1)
            for side in (-1, 1):
                c.create_oval(x+side*7*s-2*s,y-57*s,x+side*7*s+2*s,y-53*s,
                              fill="#44394e",outline="")
        elif name == "Wonder of U":
            c.create_polygon(x-10*s,y-40*s,x,y-34*s,x+10*s,y-40*s,
                             x+7*s,y-22*s,x,y-18*s,x-7*s,y-22*s,
                             fill="#e0d9ec",outline="#655b7d",width=1)
            for side in (-1, 1):
                c.create_line(x+side*8*s,y-47*s,x+side*12*s,y-39*s,
                              fill="#c9bfdc",width=max(1,int(s)))
        else:
            c.create_polygon(x-8*s,y-39*s,x,y-43*s,x+8*s,y-39*s,
                             x+6*s,y-24*s,x,y-20*s,x-6*s,y-24*s,
                             fill=light,outline=outline,width=max(1,int(s)))
        # Individual boot caps and a small shoulder insignia add definition
        # without changing the silhouette or scaling the sprite unnaturally.
        for side in (-1, 1):
            bx=x+side*8*s
            c.create_line(bx-3*s,y+24*s,bx+3*s,y+24*s,
                          fill=rim,width=max(1,int(s)))
            c.create_oval(x+side*18*s-2*s,y-41*s,x+side*18*s+2*s,y-37*s,
                          fill=light,outline=outline,width=1)
        if name == "Ball Breaker":
            c.create_line(x-10*s,y-27*s,x,y-34*s,x+10*s,y-27*s,
                          fill="#fff0ad",width=max(1,int(2*s)))
        elif name == "Mandom":
            c.create_text(x,y-30*s,text="↶",fill="#f4e7ce",
                          font=("Arial",max(7,int(12*s)),"bold"))
        elif name == "Catch the Rainbow":
            for j in range(3):
                c.create_line(x+(-7+j*7)*s,y-20*s,x+(-10+j*7)*s,y-12*s,
                              fill="#aeeaf0",width=max(1,int(s)))

        if stand.get("affinity_bonus"):
            c.create_text(x, y-105*s, text="TRUE USER ★", fill="#ffdb80",
                          font=("Arial",max(6,int(7*s)),"bold"))
        if love_train and name == "D4C":
            c.create_oval(x-53*s,y-95*s,x+53*s,y+43*s,outline="#fff0a4",width=max(2,int(3*s)))

    def draw_palm(self,p):
        x=self.world_x(p["p"]); y=LANE_Y[p["lane"]]
        if -45<x<WIDTH+45 and not p["taken"]:
            self.canvas.create_oval(x-29,y-54,x+29,y+4,outline="#7454b3",width=3)
            self.canvas.create_polygon(x,y-53,x+19,y-26,x,y+1,x-19,y-26,fill="#7654ae",outline="#d9c5ff",width=2)
            self.canvas.create_polygon(x,y-42,x+9,y-26,x,y-12,x-9,y-26,fill="#e9ddff",outline="")
            self.canvas.create_text(x,y-63,text="CORPSE PART SITE",fill="#513977",font=("Arial",9,"bold"))
            if p["part"] and not p.get("part_claimed",False):
                self.canvas.create_oval(x-7,y-80,x+7,y-66,fill=GOLD,outline=WHITE,width=2)
                self.canvas.create_text(x,y-90,text="CORPSE PART",fill="#fff4d4",font=("Arial",8,"bold"))

    def draw_pickups_hazards(self):
        for p in self.pickups:
            if p["kind"]=="corpse_site": self.draw_palm(p)
            elif p["kind"] == "skull_sun" and not p["taken"]:
                x=self.world_x(p["p"]); y=LANE_Y[p["lane"]]
                if -55 < x < WIDTH+55:
                    self.canvas.create_oval(x-25,y-42,x+25,y+8,outline="#f2be73",width=3)
                    self.canvas.create_oval(x-15,y-32,x+15,y-2,fill="#f0d29b",outline="#633d56",width=2)
                    self.canvas.create_oval(x-10,y-23,x-4,y-17,fill="#342741",outline="")
                    self.canvas.create_oval(x+4,y-23,x+10,y-17,fill="#342741",outline="")
                    self.canvas.create_line(x-7,y-8,x+7,y-8,fill="#6b3d57",width=3)
                    self.canvas.create_text(x,y-55,text="SKULL SUN — CORPSE PART",fill="#fff0cd",font=("Arial",9,"bold"))
                    if not p.get("part_claimed",False):
                        self.canvas.create_oval(x-6,y-64,x+6,y-52,fill=GOLD,outline=WHITE,width=2)
            elif not p["taken"]:
                x=self.world_x(p["p"]);y=LANE_Y[p["lane"]]
                if -45<x<WIDTH+45:
                    if p["kind"] == "jesus_encounter":
                        pulse = 1.0 + .08 * math.sin(self.elapsed * 4)
                        self.canvas.create_oval(x-25*pulse,y-55*pulse,x+25*pulse,y-5*pulse,outline="#fff0c1",width=3)
                        self.canvas.create_oval(x-10,y-48,x+10,y-28,fill="#f2d7b7",outline="#7e5b65",width=2)
                        self.canvas.create_line(x,y-28,x,y-5,fill="#f4eadc",width=8)
                        self.canvas.create_line(x,y-23,x-13,y-12,fill="#f4eadc",width=4)
                        self.canvas.create_line(x,y-23,x+13,y-12,fill="#f4eadc",width=4)
                        self.canvas.create_text(x,y-68,text="JESUS",fill="#fff4d2",font=("Arial",10,"bold"))
                    elif p["kind"] == "spin_token":
                        pulse = 1.0 + .12 * math.sin(self.elapsed * 8 + p["p"])
                        r = 13 * pulse
                        self.canvas.create_oval(x-r,y-30-r,x+r,y-30+r,fill="#e8b949",outline="#fff2a8",width=3)
                        self.canvas.create_text(x,y-30,text="S",fill="#6e3c24",font=("Arial",13,"bold"))
                        self.canvas.create_text(x,y-51,text="SPIN",fill="#fff0bd",font=("Arial",8,"bold"))
                    elif p["kind"] == "horseshoe":
                        self.canvas.create_arc(x-14,y-43,x+14,y-15,start=205,extent=310,style="arc",outline="#ffe08a",width=6)
                        self.canvas.create_oval(x-12,y-32,x-7,y-27,fill="#fff4c0",outline="")
                        self.canvas.create_oval(x+7,y-32,x+12,y-27,fill="#fff4c0",outline="")
                        self.canvas.create_text(x,y-52,text="SHIELD",fill="#fff0bd",font=("Arial",8,"bold"))
                    elif p["kind"] == "race_star":
                        pulse = 1.0 + .12 * math.sin(self.elapsed * 7 + p["p"])
                        self.canvas.create_text(x,y-30,text="★",fill="#fff5a8",font=("Arial",int(26*pulse),"bold"))
                        self.canvas.create_text(x,y-51,text="SPEED",fill="#fff0bd",font=("Arial",8,"bold"))
                    else:
                        self.canvas.create_oval(x-12,y-18,x+12,y-8,fill="#739947",outline="#3e6335")
                        self.canvas.create_oval(x+3,y-17,x+12,y-9,fill="#e46e60",outline="")
        for h in self.hazards:
            if h["hit"]:continue
            x=self.world_x(h["p"]);y=LANE_Y[h["lane"]]
            if -30<x<WIDTH+30:
                if h["kind"]=="rock":
                    self.canvas.create_polygon(x-17,y+21,x-10,y-2,x+4,y-10,x+20,y+12,x+14,y+22,fill="#70665e",outline="#b2a291")
                elif h["kind"]=="cactus":
                    self.canvas.create_rectangle(x-7,y-28,x+7,y+19,fill="#3f805d",outline="#2e6149")
                    self.canvas.create_rectangle(x-18,y-12,x-7,y+5,fill="#3f805d",outline="")
                    self.canvas.create_rectangle(x+7,y-3,x+18,y+12,fill="#3f805d",outline="")
                else:
                    self.canvas.create_line(x-24,y+9,x+24,y+2,fill="#70503a",width=13)
                    self.canvas.create_line(x-20,y+5,x+20,y-1,fill="#a47a52",width=4)

    def draw_ability_effects(self):
        if getattr(self, "time_stop_timer", 0) > 0:
            # Gold clock-like rays frame the road while NPCs remain frozen.
            c = self.canvas
            c.create_rectangle(0, 0, WIDTH, HEIGHT, outline="#f4d75e", width=3, stipple="gray25")
            for ray in range(12):
                x = WIDTH * ray / 11
                c.create_line(WIDTH/2, 115, x, HEIGHT-55, fill="#f4d75e", width=1, stipple="gray50")
            c.create_text(WIDTH/2, 72, text=f"ZA WARUDO!  TIME STOP {self.time_stop_timer:.1f}s  •  YOU CAN STILL MOVE!",
                          fill="#fff0a0", font=("Arial", 15, "bold"))
        for event in self.visual_crushes:
            x = self.world_x(event["p"])
            lane_float = clamp(event["lane"], 0, 3)
            y = sum(LANE_Y[int(i)]*(1-abs(lane_float-i)) for i in range(4)
                    if abs(lane_float-i) < 1)
            pulse = 1 + max(0, event["until"]-self.elapsed)*1.2
            if -80 < x < WIDTH+80:
                self.canvas.create_oval(x-32*pulse,y-55*pulse,x+32*pulse,y+20*pulse,outline="#bfa7ff",width=4)
                self.canvas.create_line(x-40*pulse,y-48*pulse,x+40*pulse,y+18*pulse,fill="#e8deff",width=4)
                self.canvas.create_line(x+40*pulse,y-48*pulse,x-40*pulse,y+18*pulse,fill="#e8deff",width=4)
                self.canvas.create_text(x,y-68*pulse,text="CALAMITY",fill="#e8deff",font=("Arial",10,"bold"))
        for ball in self.steel_ball_projectiles:
            x = self.world_x(ball["p"])
            lane_float = clamp(ball["lane"], 0, 3)
            y = sum(LANE_Y[int(i)]*(1-abs(lane_float-i)) for i in range(4)
                    if abs(lane_float-i) < 1) - 20
            if -30 < x < WIDTH+30:
                self.canvas.create_oval(x-11,y-11,x+11,y+11,fill="#e8c35c",outline="#fff0ae",width=2)
                self.canvas.create_oval(x-6,y-6,x+6,y+6,fill="#fff4c8",outline="#b58c2e",width=1)
                for trail in range(3):
                    self.canvas.create_line(x-12-trail*7,y+4+trail*2,x-25-trail*8,y+2+trail*2,fill="#f0d477",width=2)
        for bubble in self.visual_bubbles:
            x = self.world_x(bubble["p"]) + math.sin(self.elapsed*8.0+bubble["phase"])*6
            lane_float = clamp(bubble["lane"], 0, 3)
            y = sum(LANE_Y[int(i)]*(1-abs(lane_float-i)) for i in range(4)
                    if abs(lane_float-i) < 1) - 26 - (self.elapsed*22 % 18)
            pulse = 1.0 + .16*math.sin(self.elapsed*10+bubble["phase"])
            radius = 8*pulse
            if -30 < x < WIDTH+30:
                self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,
                                        fill="#a8eee9",outline="#f5ffff",width=2)
                self.canvas.create_oval(x-radius*.55,y-radius*.55,x+radius*.55,y+radius*.55,
                                        outline="#58aeb8",width=1)
                self.canvas.create_text(x,y,text="★",fill="#4b949e",font=("Arial",8,"bold"))

    def draw_hud(self):
        c=self.canvas
        c.create_rectangle(16,14,352,117,fill="#222631",outline="#4a4d55",width=1)
        c.create_text(32,29,text="RACE STATUS",anchor="nw",fill=GOLD,font=("Arial",10,"bold"))
        current_stage = "SKULL SUN TERRITORY" if abs(self.progress-self.skull_sun["p"]) < self.skull_sun["width"] / 2 else self.stage_names()[self.stage_index()]
        c.create_text(32,52,text=current_stage,anchor="nw",fill=PAPER,font=("Arial",14,"bold"))
        c.create_rectangle(32,84,330,95,fill="#4b4e56",outline="")
        c.create_rectangle(32,84,32+298*self.progress/RACE_LENGTH,95,fill=GOLD,outline="")
        c.create_text(330,68,text=f"{self.progress/RACE_LENGTH*100:4.1f}%",anchor="ne",fill=PAPER,font=("Arial",10,"bold"))
        spin_label = "GOLDEN SPIN: UNLOCKED (G)" if self.spin_ability_unlocked else f"SPIN TOKENS: {min(5, self.total_spin_tokens)}/5 TO UNLOCK"
        c.create_text(32,101,text=spin_label,anchor="nw",fill="#ffe08a" if self.spin_ability_unlocked else PAPER,font=("Arial",9,"bold"))
        c.create_rectangle(WIDTH-270,14,WIDTH-16,156,fill="#222631",outline="#4a4d55")
        c.create_text(WIDTH-250,28,text="HORSE STAMINA",anchor="nw",fill=PAPER,font=("Arial",10,"bold"))
        c.create_rectangle(WIDTH-250,51,WIDTH-35,63,fill="#4b4e56",outline="")
        c.create_rectangle(WIDTH-250,51,WIDTH-250+215*self.stamina/100,63,fill=TEAL,outline="")
        c.create_text(WIDTH-250,76,text="RIDER HEALTH",anchor="nw",fill=PAPER,font=("Arial",10,"bold"))
        c.create_rectangle(WIDTH-250,98,WIDTH-35,110,fill="#4b4e56",outline="")
        c.create_rectangle(WIDTH-250,98,WIDTH-250+215*clamp(self.hp/self.max_hp(),0,1),110,fill=RED,outline="")
        c.create_text(WIDTH-250,122,text=f"SCORE  {self.score:06d}     ALLIES {self.allies}",anchor="nw",fill=GOLD,font=("Arial",10,"bold"))
        c.create_text(WIDTH-250,137,text=f"OVERDRIVE  {int(self.overdrive)}%  [X]",anchor="nw",fill="#ffbf72",font=("Arial",10,"bold"))
        c.create_rectangle(WIDTH-250,153,WIDTH-35,163,fill="#38343a",outline="#70616a")
        c.create_rectangle(WIDTH-250,153,WIDTH-250+215*clamp(self.overdrive/100,0,1),163,fill="#ff9e48",outline="")
        if self.overdrive_active > 0:
            c.create_text(WIDTH-35,177,text=f"OVERDRIVE! {self.overdrive_active:.1f}s",anchor="ne",fill="#ffb56c",font=("Arial",13,"bold"))
        elif self.bounty_name:
            c.create_text(WIDTH-35,177,text=f"BOUNTY: {self.bounty_name}  +{self.bounty_reward}",anchor="ne",fill="#ffe17c",font=("Arial",11,"bold"))
        # Compact contract panel makes optional objectives easy to read at a glance.
        if self.state == "race":
            contract_titles = {"SPRINT":"SPRINT FOR 4 SECONDS", "PICKUPS":"COLLECT 2 PICKUPS", "COMBAT":"LAND 3 ATTACKS", "DISTANCE":"COVER 950 METERS"}
            c.create_rectangle(WIDTH/2-150, 14, WIDTH/2+150, 83, fill="#211f2a", outline="#8d78bd", width=2)
            c.create_text(WIDTH/2, 27, text=f"RACE CONTRACT  {self.contract_timer:04.1f}s" if self.contract_timer > 0 else "RACE CONTRACT", fill="#d8c8ff", font=("Arial", 10, "bold"))
            c.create_text(WIDTH/2, 44, text=contract_titles.get(self.contract_kind, "SIDE CHALLENGE"), fill="#fff0d0", font=("Arial", 10, "bold"))
            ratio = clamp(self.contract_progress / max(1.0, self.contract_target), 0.0, 1.0)
            c.create_rectangle(WIDTH/2-125, 57, WIDTH/2+125, 65, fill="#48404f", outline="")
            c.create_rectangle(WIDTH/2-125, 57, WIDTH/2-125+250*ratio, 65, fill="#b99aff", outline="")
            if self.contract_timer > 0:
                c.create_text(WIDTH/2, 75, text=f"{self.contract_progress:.1f} / {self.contract_target:.0f}  •  REWARD: SCORE + OVERDRIVE", fill="#d8d0e6", font=("Arial", 8, "bold"))
        if self.race_event and self.race_event_timer > 0:
            event_colors = {"GOLDEN RUSH":"#ffe27b", "SANDSTORM":"#d8c3a0", "SPIN SURGE":"#8ce8ee", "STAMPede":"#ffb36b"}
            c.create_rectangle(WIDTH/2-190, 125, WIDTH/2+190, 158, fill="#24232b", outline=event_colors.get(self.race_event, GOLD), width=2)
            c.create_text(WIDTH/2, 141, text=f"RACE EVENT: {self.race_event.upper()}  {self.race_event_timer:.1f}s", fill=event_colors.get(self.race_event, GOLD), font=("Arial",12,"bold"))
        elif self.state == "race" and self.race_event_countdown > 0:
            c.create_text(WIDTH/2, 137, text=f"NEXT RACE EVENT IN {int(self.race_event_countdown)+1}s", fill="#fff0ce", font=("Arial",10,"bold"))
        if self.combo > 1 and self.combo_timer > 0:
            c.create_text(WIDTH-24,174,text=f"COMBO x{self.combo}  •  {self.combo_timer:.1f}s",anchor="ne",fill="#ffe17c",font=("Arial",14,"bold"))
        # Stand card and stat trade-offs.
        c.create_rectangle(16,HEIGHT-105,475,HEIGHT-16,fill="#222631",outline="#4a4d55")
        if not self.stand:
            c.create_text(32,HEIGHT-91,text="STAND: NOT AWAKENED",anchor="nw",fill=MUTED,font=("Arial",14,"bold"))
            c.create_text(32,HEIGHT-62,text=f"Corpse Part sites: {CORPSE_PART_CHANCE}% part chance • Skull Sun always has one",anchor="nw",fill=PAPER,font=("Arial",9))
        else:
            c.create_oval(31,HEIGHT-87,59,HEIGHT-59,fill=self.stand["color"],outline=PAPER,width=2)
            c.create_text(70,HEIGHT-92,text=self.stand["name"].upper(),anchor="nw",fill=self.stand["color"],font=("Arial",14,"bold"))
            c.create_text(70,HEIGHT-65,text="BUFF  "+self.stand["buff"],anchor="nw",fill="#9de0b2",font=("Arial",9))
            c.create_text(70,HEIGHT-45,text="NERF  "+self.stand["nerf"],anchor="nw",fill="#f2a3a3",font=("Arial",9))
            c.create_text(70,HEIGHT-26,text="ABILITY  "+self.stand["ability"],anchor="nw",fill="#8edee5",font=("Arial",8))
            if self.stand.get("affinity_bonus"):
                c.create_text(70,HEIGHT-8,text=self.stand.get("affinity_text","LEGITIMATE USER BONUS"),anchor="nw",fill="#ffdc88",font=("Arial",8,"bold"))
            cd=f"K: ABILITY READY" if self.stand_cooldown<=0 else f"K: {self.stand_cooldown:.1f}s"
            c.create_text(450,HEIGHT-83,text=cd,anchor="ne",fill=GOLD,font=("Arial",10,"bold"))
        attack_hint = "SPACE steel balls" if self.character_name == "Gyro Zeppeli" else "SPACE horse ram"
        dash_hint = "Q burst READY" if self.dash_cooldown <= 0 else f"Q burst {self.dash_cooldown:.1f}s"
        spin_hint = (f"G Spin {self.spin_ability_cooldown:.1f}s" if self.spin_ability_unlocked and self.spin_ability_cooldown > 0
                     else "G Golden Spin" if self.spin_ability_unlocked else f"Collect Spin {min(5, self.total_spin_tokens)}/5")
        c.create_text(WIDTH-16,HEIGHT-14,text=f"←/→ lane   SHIFT sprint   Q burst   X overdrive   {attack_hint}   K Stand   {spin_hint}   E ally   ESC quit",anchor="se",fill="#fff3dc",font=("Arial",9,"bold"))
        if self.corpse_parts:
            c.create_text(WIDTH-18,177,text="CORPSE PARTS: "+", ".join(self.corpse_parts[-3:]),anchor="ne",fill="#fff0b7",font=("Arial",9,"bold"))
        if self.message_timer>0:
            c.create_rectangle(205,174,WIDTH-205,218,fill="#20232c",outline="#5e5c58",width=1)
            c.create_text(WIDTH/2,196,text=self.message,fill=WHITE,font=("Arial",12,"bold"),width=680)

    def draw_title(self):
        c = self.canvas
        self.draw_background()
        # High-contrast title screen: the old layout pushed text into the bottom
        # edge and made the controls difficult to find on scaled/fullscreen displays.
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101520", stipple="gray50", outline="")
        c.create_rectangle(35, 28, WIDTH-35, HEIGHT-28, fill="#1b2330", outline="#d4b16d", width=3)
        c.create_rectangle(46, 39, WIDTH-46, HEIGHT-39, outline="#485466", width=1)
        for i in range(18):
            xx = 55 + i*60
            c.create_line(xx, 220, xx-70, 355, fill="#303b4d", width=1)
        c.create_polygon(62, 54, 255, 54, 230, 78, 62, 78, fill="#9e3f4b", outline="")
        c.create_text(76, 61, text="THE CROSS-COUNTRY RACE", anchor="nw", fill="#fff0cd", font=("Arial", 10, "bold"))
        c.create_text(WIDTH/2, 104, text="STEEL BALL RUN", fill="#f8ecd4", font=("Arial", 43, "bold"))
        c.create_text(WIDTH/2, 151, text="S T A N D   R U S H", fill="#edc45f", font=("Arial", 21, "bold"))
        c.create_line(315, 174, WIDTH-315, 174, fill="#edc45f", width=2)

        # Character showcase kept inside the left half, leaving room for a clear menu.
        self.draw_horse(190, 340, "#d7d9d3", True, False, name="Johnny Joestar", phase=1.2)
        self.draw_horse(360, 354, "#9a5634", False, False, name="Gyro Zeppeli", phase=3.1)
        c.create_text(270, 400, text="RACE • FIGHT • AWAKEN STANDS", fill="#f5e9d0", font=("Arial", 13, "bold"))
        c.create_text(270, 425, text="Collect Corpse Parts and Spin tokens", fill="#91ded7", font=("Arial", 11, "bold"))

        # Clear menu panel with matching shortcut labels; every action has a visible key.
        c.create_rectangle(600, 202, 1038, 488, fill="#222c3b", outline="#d4b16d", width=2)
        c.create_text(819, 218, text="GAME SELECT", fill="#edc45f", font=("Arial", 19, "bold"))
        c.create_text(819, 232, text="PRESS B OR CLICK THE CHESS DUEL ROW BELOW", fill="#f0d69d", font=("Arial", 8, "bold"))
        menu_rows = [
            ("ENTER", "START RACE", "#f8ecd4"),
            ("S", "SETTINGS", "#91ded7"),
            ("V", "CHARACTER SELECT", "#91ded7"),
            ("C", "STAND ARCHIVE", "#c6b4ff"),
            ("I / F1", "HOW TO PLAY", "#f0d69d"),
            ("R", "RACE RECORDS", "#f0d69d"),
            ("B", "PLAY CHESS DUEL — 800 ELO", "#edc45f"),
        ]
        for i, (key_label, label, color) in enumerate(menu_rows):
            yy = 248 + i*32
            c.create_rectangle(630, yy-14, 1008, yy+14, fill="#303d50" if i == 0 else "#273241", outline="#536174")
            c.create_rectangle(642, yy-10, 710, yy+10, fill="#8d3f4a" if i == 0 else "#3b4b60", outline="")
            c.create_text(676, yy, text=key_label, fill="#fff0cd", font=("Arial", 10, "bold"))
            c.create_text(729, yy, text=label, anchor="w", fill=color, font=("Arial", 12, "bold"))

        pulse = .72 + .28*math.sin(self.elapsed*3.5)
        world_label = "ALTERNATE UNIVERSE MODE" if self.alternate_universe else "ORIGINAL STEEL BALL RUN MODE"
        c.create_text(WIDTH/2, 500, text=f"WORLD: {world_label}  •  PRESS T TO SWITCH", fill="#e7c84f" if self.alternate_universe else "#91ded7", font=("Arial", 12, "bold"))
        c.create_text(WIDTH/2, 488, text=f"RIDER THIS RUN: {self.character_name.upper()}", fill="#91ded7", font=("Arial", 13, "bold"))
        c.create_text(WIDTH/2, 516, text=f"WINS  {self.total_wins}     WIN STREAK  {self.wins_in_row}/5     STANDS FOUND  {len(self.unlocked_stands)}", fill="#f5e9d0", font=("Arial", 12, "bold"))
        spin_text = "GOLDEN SPIN UNLOCKED — PRESS G IN A RACE" if self.spin_ability_unlocked else f"GOLDEN SPIN: {min(5, self.total_spin_tokens)}/5 SPIN TOKENS COLLECTED"
        c.create_text(WIDTH/2, 541, text=spin_text, fill="#edc45f", font=("Arial", 11, "bold"))
        c.create_text(WIDTH/2, 578, text="← / → OR A / D  CHANGE LANES     SHIFT SPRINT     SPACE ATTACK     Q DASH", fill="#c4ccd8", font=("Arial", 10, "bold"))
        c.create_text(WIDTH/2, 601, text="K STAND ABILITY     G GOLDEN SPIN     E RECRUIT ALLY     T WORLD MODE", fill="#c4ccd8", font=("Arial", 10, "bold"))
        c.create_text(WIDTH/2, 645, text="T: SWITCH WORLD  •  Alternate Universe ends with Diego Brando (AU) and The World.", fill="#e7c84f" if self.alternate_universe else "#91ded7", font=("Arial", 10, "bold"))
        c.create_text(WIDTH/2, 686, text="PRESS ENTER TO RACE", fill=hexmix("#edc45f", "#ffffff", pulse), font=("Arial", 17, "bold"))

    def chess_evaluate(self, board):
        """Lightweight material/position score from Black's point of view."""
        values = {chess.PAWN: 100, chess.KNIGHT: 315, chess.BISHOP: 330,
                  chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
        score = 0
        for sq, piece in board.piece_map().items():
            sign = -1 if piece.color == chess.WHITE else 1
            score += sign * values[piece.piece_type]
            file, rank = chess.square_file(sq), chess.square_rank(sq)
            center = 7 - (abs(3.5-file) + abs(3.5-rank))
            if piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                score += sign * center * 5
            if piece.piece_type == chess.PAWN:
                advance = rank if piece.color == chess.WHITE else 7-rank
                score += sign * advance * 4
        return score

    def chess_search(self, board, depth, alpha, beta):
        if depth <= 0 or board.is_game_over():
            if board.is_checkmate():
                return 99999 if board.turn == chess.WHITE else -99999
            return self.chess_evaluate(board)
        maximizing = board.turn == chess.BLACK
        best = -100000 if maximizing else 100000
        moves = list(board.legal_moves)
        # Captures/promotions first improve alpha-beta pruning.
        moves.sort(key=lambda m: (board.is_capture(m), m.promotion is not None), reverse=True)
        for move in moves:
            board.push(move)
            score = self.chess_search(board, depth-1, alpha, beta)
            board.pop()
            if maximizing:
                best = max(best, score); alpha = max(alpha, best)
            else:
                best = min(best, score); beta = min(beta, best)
            if beta <= alpha:
                break
        return best

    def chess_ai_move(self):
        if not chess or self.chess_board is None or self.chess_board.turn != chess.BLACK or self.chess_board.is_game_over():
            return
        board = self.chess_board
        candidates = []
        for move in list(board.legal_moves):
            board.push(move)
            score = self.chess_search(board, 1, -100000, 100000)
            board.pop()
            candidates.append((score, move))
        if not candidates:
            return
        # An intentionally modest opponent: usually selects among the best few
        # moves, and occasionally overlooks a tactic to approximate beginner play.
        candidates.sort(key=lambda item: item[0], reverse=True)
        if random.random() < 0.16 and len(candidates) > 5:
            pool = candidates[3:min(10, len(candidates))]
        else:
            pool = candidates[:min(4, len(candidates))]
        _, move = random.choice(pool)
        board.push(move)
        self.play_sfx("check" if board.is_check() else "move")
        self.chess_last_move = move
        if board.is_checkmate():
            self.chess_message = "Checkmate — the 800 ELO bot wins. Press R to try again."
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves():
            self.chess_message = "Draw. Press R for a rematch."
        else:
            self.chess_message = f"Bot played {move.uci()}. Your move."

    def chess_click(self, pos):
        if not chess or self.chess_board is None or self.chess_board.turn != chess.WHITE or self.chess_board.is_game_over():
            return
        x, y = pos
        left, top, size = 54, 104, 576
        if not (left <= x < left+size and top <= y < top+size):
            return
        file = int((x-left)/(size/8))
        rank_from_top = int((y-top)/(size/8))
        square = chess.square(file, 7-rank_from_top)
        piece = self.chess_board.piece_at(square)
        if self.chess_selected is None:
            if piece and piece.color == chess.WHITE:
                self.play_sfx("select")
                self.chess_selected = square
            return
        move = chess.Move(self.chess_selected, square)
        if self.chess_board.piece_at(self.chess_selected).piece_type == chess.PAWN and chess.square_rank(square) == 7:
            move = chess.Move(self.chess_selected, square, promotion=chess.QUEEN)
        if move in self.chess_board.legal_moves:
            san = self.chess_board.san(move)
            self.chess_board.push(move)
            self.play_sfx("move")
            self.chess_last_move = move
            self.chess_selected = None
            if self.chess_board.is_checkmate():
                self.chess_message = "You checkmated the 800 ELO bot! Press R for another game."
            elif self.chess_board.is_stalemate() or self.chess_board.is_insufficient_material():
                self.chess_message = "Draw. Press R to play again."
            else:
                self.chess_message = f"You played {san}. The bot is thinking..."
                self.chess_ai_move()
        elif piece and piece.color == chess.WHITE:
            self.chess_selected = square
        else:
            self.chess_selected = None

    def draw_chess(self):
        c = self.canvas
        # Chess.com-inspired dark play room, board-first layout and player panels.
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#202d28", outline="")
        c.create_rectangle(0, 0, WIDTH, 76, fill="#17231f", outline="")
        c.create_text(34, 37, text="♞", fill="#8fc7a5",
                      font=("DejaVu Sans", 31, "bold"), anchor="w")
        c.create_text(82, 37, text="CHESS DUEL", fill="#f4f5ed",
                      font=("Arial", 23, "bold"), anchor="w")
        c.create_text(WIDTH-28, 38, text="STEEL BALL RUN  •  800 ELO BOT",
                      fill="#b6c9bd", font=("Arial", 10, "bold"), anchor="e")

        left, top, cell = 54, 104, 72
        board_size = cell * 8
        legal_targets = set()
        legal_captures = set()
        if self.chess_board and self.chess_selected is not None:
            selected_moves = [m for m in self.chess_board.legal_moves
                              if m.from_square == self.chess_selected]
            legal_targets = {m.to_square for m in selected_moves}
            legal_captures = {m.to_square for m in selected_moves
                              if self.chess_board.is_capture(m)}

        symbols = {
            "K":"♔","Q":"♕","R":"♖","B":"♗","N":"♘","P":"♙",
            "k":"♚","q":"♛","r":"♜","b":"♝","n":"♞","p":"♟"
        }

        if self.chess_board:
            # Board coordinates and chess.com-like green / cream squares.
            for rank in range(8):
                for file in range(8):
                    sqr = chess.square(file, 7-rank)
                    x, y = left + file*cell, top + rank*cell
                    light = (rank + file) % 2 == 0
                    base = "#eeeed2" if light else "#769656"
                    if self.chess_last_move and sqr in (
                        self.chess_last_move.from_square, self.chess_last_move.to_square
                    ):
                        base = "#f6f669" if light else "#baca44"
                    if self.chess_selected == sqr:
                        base = "#f7ec67"
                    c.create_rectangle(x, y, x+cell, y+cell, fill=base, outline="")

                    piece = self.chess_board.piece_at(sqr)
                    if sqr in legal_targets:
                        if piece:
                            c.create_oval(x+7, y+7, x+cell-7, y+cell-7,
                                          outline="#294b32", width=5)
                        else:
                            c.create_oval(x+cell/2-8, y+cell/2-8,
                                          x+cell/2+8, y+cell/2+8,
                                          fill="#294b32", outline="")

                    if piece:
                        glyph = symbols[piece.symbol()]
                        # Soft drop shadow + clean outlined piece glyph gives every
                        # chessman a distinct, readable icon rather than plain text.
                        px, py = x+cell/2, y+cell/2+1
                        is_white = piece.color == chess.WHITE
                        fill = "#fffdf2" if is_white else "#202522"
                        outline = "#424b43" if is_white else "#f0f0df"
                        c.create_text(px+2, py+3, text=glyph,
                                      fill="#1a211d", font=("DejaVu Sans", 48, "bold"))
                        c.create_text(px, py, text=glyph, fill=fill,
                                      font=("DejaVu Sans", 48, "bold"))
                        c.create_text(px, py, text=glyph, fill=fill,
                                      font=("Segoe UI Symbol", 48, "bold"))

                    if file == 0:
                        c.create_text(x+5, y+4, text=str(8-rank),
                                      fill="#526b42" if light else "#e8edcf",
                                      font=("Arial", 9, "bold"), anchor="nw")
                    if rank == 7:
                        c.create_text(x+cell-5, y+cell-4, text="abcdefgh"[file],
                                      fill="#526b42" if light else "#e8edcf",
                                      font=("Arial", 9, "bold"), anchor="se")

            c.create_rectangle(left, top, left+board_size, top+board_size,
                               outline="#17231f", width=3)

            # Right-hand player / game panel.
            panel_x, panel_w = 666, 426
            c.create_rectangle(panel_x, 104, panel_x+panel_w, 684,
                               fill="#263831", outline="#40564a", width=2)

            bot_active = self.chess_board.turn == chess.BLACK and not self.chess_board.is_game_over()
            you_active = self.chess_board.turn == chess.WHITE and not self.chess_board.is_game_over()

            def player_card(y, name, rating, color, active, icon):
                bg = "#354c40" if active else "#2b3b33"
                c.create_rectangle(panel_x+14, y, panel_x+panel_w-14, y+68,
                                   fill=bg, outline="#65806c" if active else "#3c5045",
                                   width=2 if active else 1)
                c.create_oval(panel_x+27, y+12, panel_x+69, y+54,
                              fill=color, outline="#d8e4d7", width=2)
                c.create_text(panel_x+48, y+33, text=icon, fill="#ffffff",
                              font=("DejaVu Sans", 23, "bold"))
                c.create_text(panel_x+82, y+25, text=name, fill="#f0f4ed",
                              font=("Arial", 13, "bold"), anchor="w")
                c.create_text(panel_x+82, y+47, text=rating, fill="#b8c9bd",
                              font=("Arial", 10), anchor="w")
                if active:
                    c.create_text(panel_x+panel_w-28, y+34, text="●",
                                  fill="#8bd49e", font=("Arial", 14, "bold"))

            player_card(120, "COMPUTER", "800 ELO  •  BLACK", "#242a27", bot_active, "♟")
            player_card(198, "YOU", "PLAYER  •  WHITE", "#e7e7df", you_active, "♙")

            if self.chess_board.is_checkmate():
                status = "CHECKMATE"
            elif self.chess_board.is_stalemate():
                status = "STALEMATE"
            elif self.chess_board.is_game_over():
                status = "GAME OVER"
            elif self.chess_board.is_check():
                status = "CHECK"
            else:
                status = "YOUR TURN" if you_active else "BOT THINKING"

            c.create_text(panel_x+24, 292, text=status, fill="#a7d7ad",
                          font=("Arial", 15, "bold"), anchor="w")
            c.create_text(panel_x+24, 320, text=self.chess_message,
                          fill="#e4e9e1", font=("Arial", 10), anchor="w",
                          width=panel_w-48)

            c.create_line(panel_x+18, 350, panel_x+panel_w-18, 350,
                          fill="#496052", width=1)
            c.create_text(panel_x+24, 370, text="MOVE HISTORY",
                          fill="#c4d7c8", font=("Arial", 10, "bold"), anchor="w")

            # Rebuild SAN from the actual move stack so notation stays accurate.
            replay = chess.Board()
            sans = []
            for move in self.chess_board.move_stack:
                move_no = replay.fullmove_number
                is_white = replay.turn == chess.WHITE
                san = replay.san(move)
                sans.append((move_no, is_white, san))
                replay.push(move)
            history_text = []
            for idx in range(0, len(sans), 2):
                white_move = sans[idx]
                black_move = sans[idx+1] if idx+1 < len(sans) else None
                row = f"{white_move[0]}. {white_move[2]}"
                if black_move:
                    row += f"     {black_move[2]}"
                history_text.append(row)
            if history_text:
                visible = history_text[-10:]
                for n, row in enumerate(visible):
                    c.create_rectangle(panel_x+16, 390+n*22, panel_x+panel_w-16,
                                       411+n*22,
                                       fill="#31463a" if n % 2 == 0 else "#293b32",
                                       outline="")
                    c.create_text(panel_x+28, 400+n*22, text=row,
                                  fill="#e4e9e1", font=("Consolas", 10), anchor="w")
            else:
                c.create_text(panel_x+26, 408, text="Make your first move to begin.",
                              fill="#9eb3a3", font=("Arial", 10), anchor="w")

            c.create_line(panel_x+18, 630, panel_x+panel_w-18, 630,
                          fill="#496052", width=1)
            c.create_text(panel_x+24, 650,
                          text="CLICK A PIECE, THEN A LEGAL SQUARE",
                          fill="#c4d7c8", font=("Arial", 9, "bold"), anchor="w")
            c.create_text(panel_x+24, 670, text="R  NEW GAME     ESC  MAIN MENU",
                          fill="#9eb3a3", font=("Arial", 9, "bold"), anchor="w")

            c.create_text(left+board_size/2, 692,
                          text="WHITE TO MOVE" if you_active else ("BLACK TO MOVE" if bot_active else "GAME FINISHED"),
                          fill="#dce9df", font=("Arial", 11, "bold"))
        else:
            c.create_rectangle(170, 220, WIDTH-170, 500, fill="#263831", outline="#65806c", width=2)
            c.create_text(WIDTH/2, 275, text="CHESS DUEL — 800 ELO",
                          fill="#edc45f", font=("Arial", 25, "bold"))
            c.create_text(WIDTH/2, 340, text="Chess support is not installed yet.",
                          fill="#f6ead0", font=("Arial", 18, "bold"))
            c.create_text(WIDTH/2, 385, text="Open Command Prompt in your game folder and run:",
                          fill="#c4ccd8", font=("Arial", 13, "bold"))
            c.create_text(WIDTH/2, 425, text="py -m pip install python-chess",
                          fill="#91ded7", font=("Consolas", 19, "bold"))
            c.create_text(WIDTH/2, 475, text="Then restart the game and press B again.  ESC = Main Menu",
                          fill="#f0d69d", font=("Arial", 12, "bold"))

    def draw_character_select(self):
        c = self.canvas
        characters = list(CHARACTER_LOOKS)
        if self.selected_character_name not in characters:
            self.selected_character_name = characters[0]
        self.character_menu_index = characters.index(self.selected_character_name)
        name = self.selected_character_name
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101520", outline="")
        c.create_rectangle(55, 34, WIDTH-55, HEIGHT-34, fill="#1b2330", outline="#d4b16d", width=3)
        c.create_text(WIDTH/2, 82, text="CHOOSE YOUR RIDER", fill="#f8ecd4", font=("Arial", 34, "bold"))
        c.create_text(WIDTH/2, 119, text="Pick your racer before the starting gun", fill="#91ded7", font=("Arial", 14, "bold"))
        # Large animated rider preview, using the game's own drawn horse/rider art.
        self.draw_horse(355, 365, HORSE_COATS.get(name, "#9a5634"), True, False,
                        name=name, phase=self.elapsed, stand=None, depth_scale=1.25)
        c.create_text(355, 475, text=name.upper(), fill=CHARACTER_LOOKS[name]["accent"], font=("Arial", 22, "bold"))
        c.create_text(355, 509, text=f"RIDER {self.character_menu_index+1} / {len(characters)}", fill="#91ded7", font=("Arial", 12, "bold"))
        c.create_rectangle(610, 178, 1015, 520, fill="#222c3b", outline="#536174", width=2)
        c.create_text(812, 207, text="RIDER ROSTER", fill="#edc45f", font=("Arial", 18, "bold"))
        for i, character in enumerate(characters):
            # Compact rows keep the extra Alternate Universe riders inside the roster panel.
            y = 237 + i*21
            selected = character == name
            c.create_rectangle(636, y-9, 989, y+9,
                               fill="#70404a" if selected else "#2b3545",
                               outline="#edc45f" if selected else "#465467", width=2 if selected else 1)
            c.create_text(650, y, text=("▶ " if selected else "  ")+character,
                          anchor="w", fill="#fff0cd" if selected else "#cbd3df",
                          font=("Arial", 9, "bold" if selected else "normal"))
        c.create_text(WIDTH/2, 575, text="← / → OR A / D: CHANGE RIDER     ENTER / SPACE: START RACE",
                      fill="#f5e9d0", font=("Arial", 13, "bold"))
        c.create_text(WIDTH/2, 608, text="ESC: BACK TO MAIN MENU  •  Your unlocked Stands and progress are preserved",
                      fill="#91ded7", font=("Arial", 11, "bold"))
        c.create_text(WIDTH/2, 667, text="THE STEEL BALL RUN AWAITS", fill="#edc45f", font=("Arial", 16, "bold"))

    def draw_howto(self):
        c = self.canvas
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101520", outline="")
        c.create_rectangle(72, 42, WIDTH-72, HEIGHT-42, fill="#1d2430", outline="#d4b16d", width=3)
        c.create_text(WIDTH/2, 88, text="RIDER'S FIELD GUIDE", fill="#f8ecd4", font=("Arial", 32, "bold"))
        c.create_text(WIDTH/2, 128, text="Your quick guide to surviving the Steel Ball Run", fill="#91ded7", font=("Arial", 14, "bold"))
        guide = [
            ("RACE", "Move between four lanes to dodge hazards and overtake rival riders."),
            ("SPEED", "Hold SHIFT to sprint; watch stamina. Q performs a burst dash. Stars grant a speed burst."),
            ("COMBAT", "SPACE attacks rivals. K uses your equipped Stand. G uses Golden Spin after 5 tokens."),
            ("ALLIES", "Press E near a rider to recruit them. Allies attack bosses and can help restore health."),
            ("PROGRESSION", "Collect Corpse Parts to awaken Stands. Use C on the title screen to equip unlocked Stands."),
            ("BOSSES", "Finish a stage, then press ENTER at the boss introduction to begin the showdown. Press T on the title screen to switch to Alternate Universe mode."),
            ("PICKUPS", "Golden horseshoes give brief protection; race stars grant speed and points. Near-misses build combo bonuses."),
            ("TIP", "Food restores resources. Save sprint stamina for hazards and boss phases."),
        ]
        for i, (label, desc) in enumerate(guide):
            yy = 184 + i*61
            c.create_rectangle(125, yy-19, WIDTH-125, yy+26, fill="#273241", outline="#4c5b6e")
            c.create_text(150, yy+2, text=label, anchor="w", fill="#edc45f", font=("Arial", 12, "bold"))
            c.create_text(255, yy+2, text=desc, anchor="w", fill="#f5e9d0", font=("Arial", 11), width=WIDTH-400)
        c.create_text(WIDTH/2, HEIGHT-70, text="ENTER / SPACE / ESC — BACK TO MAIN MENU", fill="#edc45f", font=("Arial", 13, "bold"))

    def draw_records(self):
        c = self.canvas
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101520", outline="")
        c.create_rectangle(100, 50, WIDTH-100, HEIGHT-50, fill="#1d2430", outline="#d4b16d", width=3)
        c.create_text(WIDTH/2, 98, text="RACE RECORDS", fill="#f8ecd4", font=("Arial", 34, "bold"))
        stats = [
            ("TOTAL VICTORIES", str(self.total_wins)),
            ("CURRENT WIN STREAK", f"{self.wins_in_row} / 5"),
            ("UNLOCKED STANDS", f"{len(self.unlocked_stands)} / {len(STANDS)}"),
            ("CORPSE PARTS COLLECTED", "YES" if self.has_ever_collected_part else "NOT YET"),
            ("GOLDEN SPIN", "UNLOCKED" if self.spin_ability_unlocked else f"{min(5, self.total_spin_tokens)} / 5 TOKENS"),
        ]
        for i, (label, value) in enumerate(stats):
            yy = 175 + i*75
            c.create_rectangle(230, yy-22, WIDTH-230, yy+30, fill="#273241", outline="#536174")
            c.create_text(260, yy+4, text=label, anchor="w", fill="#d4dbe7", font=("Arial", 13, "bold"))
            c.create_text(WIDTH-260, yy+4, text=value, anchor="e", fill="#edc45f", font=("Arial", 15, "bold"))
        c.create_text(WIDTH/2, HEIGHT-86, text="Keep racing to discover more Stands and unlock Golden Spin.", fill="#91ded7", font=("Arial", 12, "bold"))
        c.create_text(WIDTH/2, HEIGHT-58, text="ENTER / SPACE / ESC — BACK TO MAIN MENU", fill="#edc45f", font=("Arial", 12, "bold"))

    def draw_settings(self):
        c = self.canvas
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101520", outline="")
        c.create_rectangle(190, 95, WIDTH-190, HEIGHT-90, fill="#1d2430", outline="#d4b16d", width=3)
        c.create_text(WIDTH/2, 145, text="RACE SETTINGS", fill="#f8ecd4", font=("Arial", 34, "bold"))
        c.create_text(WIDTH/2, 184, text="UP/DOWN select  •  LEFT/RIGHT change  •  ENTER apply/back", fill="#91ded7", font=("Arial", 12, "bold"))
        items = [
            ("DIFFICULTY", self.settings["difficulty"], "Changes incoming damage"),
            ("HORSE SPEED", self.settings["horse_speed"], "Faster horses mean a shorter race"),
            ("ROAD HAZARDS", self.settings["hazards"], "Turn rocks, cacti and logs on/off"),
            ("CONTROLS", self.settings["controls"], "Choose arrow keys or WASD for lane changes"),
            ("BACK TO MAIN MENU", "", "Return to the title screen"),
        ]
        for i, (label, value, hint) in enumerate(items):
            y = 250 + i*76
            selected = i == self.settings_index
            c.create_rectangle(245, y-23, WIDTH-245, y+39,
                               fill="#354153" if selected else "#242c39",
                               outline="#edc45f" if selected else "#49515e", width=2 if selected else 1)
            c.create_text(275, y-5, text=("▶ " if selected else "")+label, anchor="w",
                          fill="#edc45f" if selected else "#f6ead0", font=("Arial", 15, "bold"))
            if value:
                c.create_text(WIDTH-275, y-5, text=value, anchor="e", fill="#91ded7",
                              font=("Arial", 16, "bold"))
            c.create_text(WIDTH/2, y+22, text=hint, fill="#b4b6b2", font=("Arial", 10))
        c.create_text(WIDTH/2, HEIGHT-115, text="F11 toggles fullscreen  •  ESC returns to menu", fill="#f0d69d", font=("Arial", 11, "bold"))

    def keep_stand_selection_visible(self):
        """Keep the selected Stand inside the archive's visible scrolling window."""
        options = self.stand_menu_options()
        visible_rows = 9
        if self.stand_menu_index < self.stand_scroll_offset:
            self.stand_scroll_offset = self.stand_menu_index
        elif self.stand_menu_index >= self.stand_scroll_offset + visible_rows:
            self.stand_scroll_offset = self.stand_menu_index - visible_rows + 1
        self.stand_scroll_offset = max(0, min(self.stand_scroll_offset, max(0, len(options) - visible_rows)))

    def scroll_stand_archive(self, amount):
        """Scroll the archive with the mouse wheel while preserving selection."""
        options = self.stand_menu_options()
        visible_rows = 9
        self.stand_scroll_offset = max(0, min(max(0, len(options) - visible_rows), self.stand_scroll_offset + amount))
        self.stand_menu_index = max(self.stand_scroll_offset,
                                    min(self.stand_menu_index, min(len(options) - 1, self.stand_scroll_offset + visible_rows - 1)))

    def draw_stand_select(self):
        c = self.canvas
        c.create_rectangle(0,0,WIDTH,HEIGHT,fill="#111722",outline="")
        c.create_rectangle(74,48,WIDTH-74,HEIGHT-48,fill="#1d2430",outline="#d4b16d",width=3)
        c.create_text(WIDTH/2,84,text="STAND ARCHIVE",fill="#f8ecd4",font=("Arial",32,"bold"))
        c.create_text(WIDTH/2,119,text="Choose a Stand you have discovered in previous races",fill="#91ded7",font=("Arial",13))
        options = self.stand_menu_options()
        selected_option = self.selected_stand_name or "RANDOM / AWAKEN IN RACE"
        visible_rows = 9
        max_offset = max(0, len(options) - visible_rows)
        self.stand_scroll_offset = max(0, min(self.stand_scroll_offset, max_offset))
        # Draw only the visible rows so the archive never paints over its footer.
        first = self.stand_scroll_offset
        last = min(len(options), first + visible_rows)
        for idx in range(first, last):
            option = options[idx]
            row = idx - first
            y = 157 + row*31
            stand = next((st for st in STANDS if st["name"] == option), None)
            color = stand["color"] if stand else "#e6c37c"
            if idx == self.stand_menu_index:
                c.create_rectangle(150,y-12,WIDTH-150,y+13,fill="#343f50",outline="#f0ce7a",width=2)
                c.create_text(164,y,text="▶",anchor="w",fill="#f0ce7a",font=("Arial",12,"bold"))
            c.create_text(190,y,text=option,anchor="w",fill=color,font=("Arial",12,"bold"))
            if stand:
                c.create_text(WIDTH-170,y,text=stand["ability"],anchor="e",fill="#d8dce4",font=("Arial",8))
        # Scroll position indicator and clear direction hints.
        if len(options) > visible_rows:
            c.create_text(WIDTH-105,174,text=f"{first+1}–{last} / {len(options)}",fill="#c3cada",font=("Arial",9,"bold"))
            if first > 0:
                c.create_text(WIDTH-105,151,text="▲ MORE",fill="#91ded7",font=("Arial",8,"bold"))
            if last < len(options):
                c.create_text(WIDTH-105,444,text="▼ MORE",fill="#91ded7",font=("Arial",8,"bold"))
        lock_y = 463
        if "Wonder of U" not in self.unlocked_stands:
            c.create_text(WIDTH/2,lock_y,text="LOCKED: WONDER OF U — WIN 5 RACES IN A ROW AND COLLECT A CORPSE PART",fill="#ef9c9c",font=("Arial",10,"bold"))
        else:
            c.create_text(WIDTH/2,lock_y,text="WONDER OF U UNLOCKED — CALAMITY CRUSHES ANYONE WHO ATTACKS YOU",fill="#c3a7ff",font=("Arial",10,"bold"))
        c.create_text(WIDTH/2,HEIGHT-78,text="↑/↓ or W/S scroll/select    Mouse wheel scroll    ENTER select    ESC back",fill="#d2d8e3",font=("Arial",11,"bold"))
        c.create_text(WIDTH/2,HEIGHT-55,text="Your selected Stand is equipped at the start of each race.",fill="#a9b3c4",font=("Arial",10))

    def draw_boss_character_portrait(self, boss):
        """Draw distinct, manga-inspired silhouettes for the non-Valentine bosses."""
        c = self.canvas
        name = boss["name"]
        x, y = 790, 430
        bob = math.sin(self.elapsed * 2.1) * 2
        c.create_oval(x-95, y+113, x+95, y+137, fill="#201d29", outline="")
        if name == "Ringo Roadagain":
            # Ringo: lean gunfighter, broad hat, long coat, neck scarf and revolver.
            coat, hat, hair, trim = "#6e7e9d", "#d5c7a1", "#b7c7df", "#e5d7b7"
            c.create_polygon(x-39,y-48,x-56,y-15,x-44,y+82,x-17,y+72,x-8,y+2,
                             x+9,y+2,x+17,y+72,x+44,y+82,x+56,y-15,x+39,y-48,
                             fill=coat,outline="#293343",width=3)
            c.create_polygon(x-18,y-45,x,y-20,x+18,y-45,x+9,y+25,x,y+34,x-9,y+25,
                             fill=trim,outline="#293343",width=2)
            c.create_line(x-48,y-19,x-79,y+16,x-66,y+38,fill=coat,width=14)
            c.create_line(x+47,y-18,x+74,y+4,x+91,y-5,fill=coat,width=14)
            c.create_line(x+89,y-6,x+113,y-10,fill="#c7cbd1",width=6)
            c.create_oval(x-29,y-103+bob,x+29,y-45+bob,fill="#efc7a7",outline="#3c3441",width=2)
            c.create_polygon(x-39,y-93+bob,x-29,y-121+bob,x+24,y-121+bob,x+39,y-93+bob,
                             x+54,y-83+bob,x-53,y-83+bob,fill=hat,outline="#403b45",width=2)
            c.create_polygon(x-20,y-95+bob,x-27,y-72,x-17,y-51,x-6,y-76,
                             x+4,y-52,x+22,y-78,x+20,y-98+bob,fill=hair,outline="#3c3441",width=1)
            c.create_line(x-14,y-73,x-4,y-71,fill="#342d36",width=3)
            c.create_line(x+5,y-71,x+15,y-73,fill="#342d36",width=3)
            c.create_text(x,y+151,text="RINGO ROADAGAIN",fill="#f2e7cf",font=("Arial",19,"bold"))
            c.create_text(x,y+176,text="GUNFIGHTER • MANDOM",fill=boss["color"],font=("Arial",10,"bold"))
        elif name == "Wekapipo":
            # Wekapipo: pale military uniform, angular side-parted hair and metal arm guards.
            coat, trim = "#78869b", "#d5d8df"
            c.create_polygon(x-43,y-48,x-62,y-18,x-48,y+75,x+48,y+75,x+62,y-18,x+43,y-48,
                             fill=coat,outline="#303747",width=3)
            c.create_polygon(x-21,y-43,x,y-20,x+21,y-43,x+12,y+27,x,y+36,x-12,y+27,
                             fill="#e6e5e1",outline="#4c5668",width=2)
            for yy in (y-12,y+5,y+22):
                c.create_oval(x-5,yy-3,x+5,yy+3,fill="#5e687a",outline="")
            c.create_line(x-54,y-15,x-82,y+19,x-68,y+39,fill=coat,width=16)
            c.create_polygon(x-82,y+18,x-91,y+27,x-76,y+45,x-62,y+35,
                             fill="#c7cbd2",outline="#4a5363",width=2)
            c.create_line(x+54,y-15,x+79,y+17,x+94,y+10,fill=coat,width=16)
            c.create_oval(x+82,y+2,x+107,y+27,fill="#c7cbd2",outline="#4a5363",width=2)
            c.create_oval(x-29,y-103+bob,x+29,y-45+bob,fill="#e9c2a5",outline="#303747",width=2)
            c.create_polygon(x-31,y-87+bob,x-27,y-113+bob,x-7,y-120+bob,x+24,y-108+bob,
                             x+30,y-85+bob,x+10,y-94+bob,x-5,y-88+bob,x-18,y-96+bob,
                             fill="#d7d9dd",outline="#4c5668",width=2)
            c.create_line(x-15,y-73,x-5,y-71,fill="#303747",width=3)
            c.create_line(x+5,y-71,x+15,y-73,fill="#303747",width=3)
            # Wrecking Ball: canonical Spin weapon, not a Stand in the manga.
            orb_x, orb_y = x+111, y+45
            c.create_line(x+75,y+8,orb_x,orb_y,fill="#d8dbe2",width=3)
            c.create_oval(orb_x-17,orb_y-17,orb_x+17,orb_y+17,fill="#bfc7d3",outline="#f2f4f6",width=3)
            c.create_line(orb_x-10,orb_y,orb_x+10,orb_y,fill="#626e7e",width=2)
            c.create_text(x,y+151,text="WEKAPIpo".upper(),fill="#f2f3f7",font=("Arial",19,"bold"))
            c.create_text(x,y+176,text="SPIN TECHNIQUE • WRECKING BALL",fill=boss["color"],font=("Arial",10,"bold"))
        elif name == "Blackmore":
            # Blackmore: dark raincoat, high collar, brimmed hat and rain-streak details.
            coat, trim = "#384a66", "#a5cbd5"
            c.create_polygon(x-42,y-48,x-62,y-19,x-50,y+82,x+50,y+82,x+62,y-19,x+42,y-48,
                             fill=coat,outline="#1b293d",width=3)
            c.create_polygon(x-28,y-44,x-14,y-16,x,y-4,x+14,y-16,x+28,y-44,
                             fill="#182638",outline=trim,width=2)
            c.create_line(x,y-6,x,y+70,fill=trim,width=2)
            for j in range(5):
                c.create_line(x-56+j*24,y-25,x-65+j*24,y+10,fill="#91d9e4",width=2)
            c.create_line(x-52,y-12,x-79,y+28,x-65,y+45,fill=coat,width=15)
            c.create_line(x+52,y-12,x+78,y+22,x+66,y+42,fill=coat,width=15)
            c.create_oval(x-29,y-103+bob,x+29,y-45+bob,fill="#e5bea5",outline="#202c40",width=2)
            c.create_polygon(x-39,y-89+bob,x-32,y-113+bob,x+25,y-113+bob,x+39,y-89+bob,
                             x+50,y-82+bob,x-50,y-82+bob,fill="#293b52",outline=trim,width=2)
            c.create_polygon(x-24,y-91+bob,x-19,y-105+bob,x+21,y-101+bob,x+28,y-81+bob,
                             x+12,y-91+bob,x-2,y-86+bob,fill="#202b3d",outline="#202b3d",width=1)
            c.create_line(x-14,y-73,x-4,y-72,fill="#202b3d",width=3)
            c.create_line(x+5,y-72,x+15,y-73,fill="#202b3d",width=3)
            c.create_text(x,y+151,text="BLACKMORE",fill="#e1f7fa",font=("Arial",19,"bold"))
            c.create_text(x,y+176,text="CATCH THE RAINBOW",fill=boss["color"],font=("Arial",10,"bold"))

    def draw_boss(self):
        c = self.canvas
        # Cinematic showdown: layered dusk, drifting dust, animated dimensional seams.
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#171722", outline="")
        for band in range(7):
            yy = 150 + band * 25
            c.create_line(0, yy, WIDTH, yy-35, fill=hexmix("#292334", "#574052", band/7), width=2)
        c.create_rectangle(0, 285, WIDTH, HEIGHT, fill="#342d3a", outline="")
        c.create_polygon(0, 430, 170, 365, 340, 440, 540, 370, 760, 435, 950, 360, WIDTH, 415,
                         WIDTH, HEIGHT, 0, HEIGHT, fill="#493542", outline="")
        # Bright cracks in the air suggest D4C's parallel-world power.
        for i in range(9):
            xx = (i * 157 + int(self.elapsed * 38)) % (WIDTH + 120) - 60
            yy = 150 + (i % 4) * 64
            c.create_line(xx, yy, xx+24, yy+31, fill="#b97da9", width=2)
            c.create_line(xx+24, yy+31, xx+12, yy+54, fill="#e4b7d9", width=1)
        for i in range(7):
            c.create_arc(WIDTH/2-175-i*18, 105-i*10, WIDTH/2+175+i*18, 590+i*9,
                         start=20+self.elapsed*8, extent=285, style="arc",
                         outline=hexmix("#c14f78", "#8d80c9", i/7), width=2)
        # D4C stands behind Valentine; Love Train's golden dimensional wall cycles on and off.
        d4c = next((st for st in STANDS if st["name"] == "D4C"), None)
        if self.current_stage != 3:
            d4c = None
        if self.current_stage == 3 and self.boss_love_train_active:
            for ray in range(17):
                rx = 585 + ray*31
                sway = math.sin(self.elapsed*2.6 + ray*.7)*15
                c.create_line(rx, 175+sway, rx-90, 570, fill="#fff0a6", width=2)
                c.create_line(rx+5, 175+sway, rx-80, 570, fill="#dbb75d", width=1)
            c.create_arc(635, 230, 1015, 620, start=90+self.elapsed*12, extent=290,
                         style="arc", outline="#fff2a9", width=4)
            c.create_text(805, 155, text="D4C — LOVE TRAIN", fill="#fff0a6", font=("Arial", 20, "bold"))
        elif self.current_stage == 3 and self.boss_love_train_unlocked:
            c.create_text(805, 155, text="LOVE TRAIN BARRIER FLICKERING — ATTACK NOW",
                          fill="#f4d58f", font=("Arial", 11, "bold"))
        boss = self.current_boss()
        boss_power = boss.get("stand")
        if boss_power in ("Mandom", "Catch the Rainbow"):
            boss_stand = next((st for st in STANDS if st["name"] == boss_power), None)
            if boss_stand:
                self.draw_stand_companion(947, 416, boss_stand, 1.42, self.elapsed)
        elif boss_power == "Wrecking Ball":
            # Wekapipo is canonically not a Stand user; show his signature Spin weapon.
            wx = 940 + math.sin(self.elapsed*3.2)*15
            wy = 425 + math.cos(self.elapsed*2.6)*12
            for ring in range(3):
                c.create_arc(wx-35-ring*7,wy-35-ring*7,wx+35+ring*7,wy+35+ring*7,
                             start=self.elapsed*90+ring*70,extent=245,style="arc",
                             outline="#d9e0ec",width=2)
            c.create_oval(wx-22,wy-22,wx+22,wy+22,fill="#bbc4d1",outline="#f5f5f5",width=3)
            c.create_line(wx-13,wy,wx+13,wy,fill="#69778b",width=3)
            c.create_text(940, 355, text="WRECKING BALL • SPIN", fill="#dce4f1", font=("Arial",11,"bold"))
        if d4c:
            self.draw_stand_companion(947, 416, d4c, 1.48, self.elapsed,
                                      love_train=self.boss_love_train_active)
        if self.alternate_universe and boss.get("stand") == "The World (Alternate Universe)":
            world_au = next((st for st in STANDS if st["name"] == "The World (Alternate Universe)"), None)
            if world_au:
                self.draw_stand_companion(947, 416, world_au, 1.48, self.elapsed)
        # Cinematic side character / player, with their awakened Stand visibly manifested behind them.
        if self.stand:
            self.draw_stand_companion(218, 438, self.stand, 1.12, self.elapsed,
                                      love_train=False)
        self.draw_horse(250, 475, HORSE_COATS.get(self.character_name, "#d7d9d3"),
                        True, False, name=self.character_name, stand=self.stand)
        # Recruited friends physically appear in boss battles and visibly attack on their own.
        boss_allies = [ally for ally in self.racers if ally.ally and not ally.out]
        for ally_index, ally in enumerate(boss_allies[:6]):
            ax = 90 + ally_index * 92
            ay = 650 + math.sin(self.elapsed * 5.5 + ally_index) * 3
            if ally.stand:
                self.draw_stand_companion(ax-20, ay-33, ally.stand, .46, self.elapsed + ally_index * .7)
            self.draw_horse(ax, ay, ally.color, False, True, ally.name, True,
                            self.elapsed + ally_index * 1.3, ally.stand, .58)
            # Animated attack slash/pulse to make their independent boss attacks legible.
            if (self.elapsed * (1.0 + ally_index*.07)) % 1.65 < .30:
                c.create_line(ax+18, ay-28, ax+49, ay-52, fill=ally.stand["color"] if ally.stand else "#f1d08a", width=4)
                c.create_text(ax+35, ay-61, text="HIT!", fill="#fff0cf", font=("Arial", 8, "bold"))
        if len(boss_allies) > 6:
            c.create_text(92, 700, text=f"+ {len(boss_allies)-6} MORE ALLIES", fill="#80e6c1", font=("Arial", 9, "bold"), anchor="w")
        # Funny Valentine: broad-shouldered pink presidential suit, long blond hair,
        # star-marked forehead, patterned lapels, gloves, and a confident stance.
        x, y = 790, 430
        boss = self.current_boss()
        if boss["name"] != "Funny Valentine":
            self.draw_boss_character_portrait(boss)
        else:
            boss_palette = {
                "Ringo Roadagain": ("#6e7e9d", "#d5c7a1", "#b7c7df"),
                "Wekapipo": ("#78869b", "#d5d8df", "#a8b4c9"),
                "Blackmore": ("#384a66", "#a5cbd5", "#78c7d2"),
                "Funny Valentine": ("#bd527e", "#e7d7a6", "#d5d5cb"),
            }
            jacket_color, hair_color, cap_color = boss_palette[boss["name"]]
            bob = math.sin(self.elapsed*2.2)*2
            # Ground shadow and back hair silhouette.
            c.create_oval(x-112, y+116, x+112, y+143, fill="#201d29", outline="")
            c.create_polygon(x-48, y-84+bob, x-77, y-55+bob, x-72, y+30,
                             x-62, y+81, x-37, y+55, x-29, y-44,
                             x+35, y-44, x+44, y+58, x+68, y+82,
                             x+77, y+15, x+62, y-58+bob, x+38, y-86+bob,
                             fill="#e6d7ad", outline="#6c5366", width=2)
            # Legs and boots.
            c.create_polygon(x-45, y+60, x-6, y+61, x-13, y+120, x-43, y+120,
                             fill="#39303d", outline="#d5a6b7", width=2)
            c.create_polygon(x+6, y+61, x+44, y+60, x+48, y+120, x+20, y+120,
                             fill="#39303d", outline="#d5a6b7", width=2)
            c.create_line(x-48, y+121, x-9, y+121, fill="#e5c9d2", width=5)
            c.create_line(x+17, y+121, x+54, y+121, fill="#e5c9d2", width=5)
            # Strong torso and jacket.
            c.create_polygon(x-48, y-49+bob, x-73, y-24+bob, x-58, y+63,
                             x+59, y+63, x+74, y-24+bob, x+47, y-49+bob,
                             x+25, y-59+bob, x-25, y-59+bob,
                             fill=jacket_color, outline="#f1bfd0", width=3)
            # Jacket panels and central shirt/tie.
            c.create_polygon(x-27, y-48+bob, x-4, y-30+bob, x-15, y+25,
                             x-39, y-21, fill="#f0d8df", outline="#6b3a58", width=2)
            c.create_polygon(x+27, y-48+bob, x+4, y-30+bob, x+15, y+25,
                             x+39, y-21, fill="#f0d8df", outline="#6b3a58", width=2)
            c.create_polygon(x-8, y-30+bob, x+8, y-30+bob, x+15, y+27,
                             x, y+39, x-15, y+27, fill="#6c274d", outline="#f1bfd0", width=1)
            # Heart/diamond motifs on Valentine's suit.
            for dx, dy in [(-49,-12),(49,-12),(-43,24),(43,24),(-25,45),(25,45)]:
                c.create_polygon(x+dx, y+dy-5, x+dx-5, y+dy-10, x+dx-10, y+dy-6,
                                 x+dx, y+dy+5, x+dx+10, y+dy-6, x+dx+5, y+dy-10,
                                 fill="#f3d8e4", outline="#7d3158", width=1)
            # Arms and white gloves; one hand held out in a commanding pose.
            c.create_line(x-58, y-22+bob, x-83, y+22, x-65, y+48,
                          fill=jacket_color, width=17)
            c.create_oval(x-76, y+40, x-55, y+59, fill="#f0e5e7", outline="#80566a", width=2)
            c.create_line(x+58, y-22+bob, x+91, y+1, x+115, y-18,
                          fill=jacket_color, width=17)
            c.create_oval(x+105, y-29, x+126, y-8, fill="#f0e5e7", outline="#80566a", width=2)
            # Head, long blond hair framing the face, and signature forehead star.
            c.create_oval(x-31, y-103+bob, x+31, y-43+bob,
                          fill="#efc8a8", outline="#533746", width=2)
            c.create_polygon(x-34, y-83+bob, x-39, y-113+bob, x-18, y-127+bob,
                             x+7, y-119+bob, x+31, y-129+bob, x+39, y-91+bob,
                             x+24, y-101+bob, x+10, y-93+bob, x-7, y-103+bob,
                             x-23, y-94+bob, fill=hair_color, outline="#6c5366", width=2)
            c.create_polygon(x-28, y-91+bob, x-43, y-67+bob, x-37, y-28,
                             x-22, y-51, fill=hair_color, outline="#6c5366", width=2)
            c.create_polygon(x+26, y-92+bob, x+43, y-64+bob, x+36, y-20,
                             x+20, y-51, fill=hair_color, outline="#6c5366", width=2)
            # Pale military-style cap brim and ribbed front plate, matching the manga design.
            c.create_polygon(x-44, y-106+bob, x-31, y-115+bob, x+30, y-115+bob,
                             x+46, y-105+bob, x+30, y-101+bob, x-29, y-101+bob,
                             fill=cap_color, outline="#61576b", width=2)
            c.create_polygon(x-28, y-116+bob, x-22, y-129+bob, x+19, y-129+bob,
                             x+30, y-115+bob, fill="#bdbfc1", outline="#61576b", width=2)
            for ridge in range(4):
                rx=x-17+ridge*10
                c.create_line(rx, y-124+bob, rx+1, y-116+bob, fill="#707383", width=2)
            c.create_oval(x-8,y-122+bob,x+8,y-114+bob,fill="#b6a6be",outline="#5d4c65",width=1)
            c.create_line(x-19, y-75+bob, x-7, y-73+bob, fill="#352b3b", width=3)
            c.create_line(x+7, y-73+bob, x+19, y-75+bob, fill="#352b3b", width=3)
            c.create_line(x-8, y-55+bob, x+8, y-55+bob, fill="#8c405b", width=2)
            c.create_polygon(x-5, y-91+bob, x, y-97+bob, x+5, y-91+bob,
                             x, y-85+bob, fill="#fff0b5", outline="#9d5472", width=1)
            c.create_text(x, y+158, text=boss["name"].upper(), fill="#ffe6ef", font=("Arial", 22, "bold"))
            c.create_text(x, y+181, text=boss["subtitle"], fill=boss["color"], font=("Arial", 10, "bold"))
            if self.boss_slow > 0:
                for j in range(9):
                    bx = x + math.sin(self.elapsed*5+j*1.4)*(42+j*3)
                    by = y-57 + math.cos(self.elapsed*4+j*1.1)*(27+j*2)
                    c.create_oval(bx-8,by-8,bx+8,by+8,fill="#a8eee9",outline="#f5ffff",width=2)
                    c.create_text(bx,by,text="★",fill="#4b949e",font=("Arial",8,"bold"))
        # Cinematic boss HUD and letterbox bars.
        c.create_rectangle(250, 55, 870, 126, fill="#171722", outline="#c78aa8", width=2)
        c.create_text(WIDTH/2, 70, text=f"STAGE {self.current_stage + 1} SHOWDOWN", fill="#f0c16c", font=("Arial", 12, "bold"))
        c.create_rectangle(290, 94, 830, 107, fill="#57404f", outline="")
        boss = self.current_boss()
        c.create_rectangle(290, 94, 290+540*clamp(self.boss_hp/float(boss["hp"]),0,1), 107, fill=boss["color"], outline="")
        c.create_text(WIDTH/2, 116, text=f"{boss['name'].upper()}  {max(0,int(self.boss_hp))}/{int(boss['hp'])}",
                      fill=PAPER, font=("Arial", 10, "bold"))
        c.create_rectangle(18, HEIGHT-100, 440, HEIGHT-16, fill="#20202b", outline="#8b6378")
        c.create_text(34, HEIGHT-85, text=f"HEALTH  {int(max(0,self.hp))}/{int(self.max_hp())}     ALLIES  {self.allies}",
                      anchor="nw", fill=PAPER, font=("Arial", 14, "bold"))
        c.create_text(WIDTH/2, HEIGHT-30, text="SPACE ATTACK    K STAND    HOLD SHIFT TO GUARD    H HELP",
                      fill=PAPER, font=("Arial", 12, "bold"))
        if self.allies > 0:
            c.create_text(WIDTH-24, HEIGHT-76,
                          text=f"ALLY ASSISTS  {self.allies}  •  TEAM DAMAGE {self.ally_boss_damage_total}",
                          anchor="ne", fill="#80e6c1", font=("Arial", 11, "bold"))
        if self.message_timer > 0:
            c.create_rectangle(220, 196, WIDTH-220, 239, fill="#1b1925", outline="#8b6378")
            c.create_text(WIDTH/2, 217, text=self.message, fill=WHITE, font=("Arial", 12, "bold"), width=680)
        # Animated cinematic bars.
        bar_h = 20 + int(4*math.sin(self.elapsed*1.5))
        c.create_rectangle(0, 0, WIDTH, bar_h, fill="#08090f", outline="")
        c.create_rectangle(0, HEIGHT-bar_h, WIDTH, HEIGHT, fill="#08090f", outline="")

    def draw_end(self):
        c=self.canvas
        self.draw_background()
        c.create_rectangle(0,0,WIDTH,HEIGHT,fill="#151923",stipple="gray50",outline="")
        c.create_rectangle(220,185,900,545,fill="#20242e",outline="#786b56",width=2)
        won=self.state=="victory"
        c.create_text(WIDTH/2,245,text="RACE COMPLETE!" if won else "YOUR RUN ENDS HERE",fill=GOLD if won else RED,font=("Arial",40,"bold"))
        c.create_text(WIDTH/2,330,text=f"FINAL SCORE  {self.score:07d}",fill=PAPER,font=("Arial",23,"bold"))
        c.create_text(WIDTH/2,375,text=f"ALLIES RECRUITED  {self.allies}     CORPSE PARTS  {len(self.corpse_parts)}",fill=TEAL,font=("Arial",14,"bold"))
        c.create_text(WIDTH/2,410,text=f"WIN STREAK  {self.wins_in_row}/5     TOTAL WINS  {self.total_wins}",fill="#c6b4ff" if won else PAPER,font=("Arial",14,"bold"))
        if won and getattr(self,"unlock_notice",None):
            c.create_text(WIDTH/2,458,text=self.unlock_notice,fill="#e0c4ff",font=("Arial",11,"bold"))
        elif not won:
            c.create_text(WIDTH/2,458,text="Your consecutive-win streak has reset.",fill="#eaa0a0",font=("Arial",11,"bold"))
        c.create_text(WIDTH/2,492,text="ENTER race again     M main menu / Stand Archive     ESC quit",fill=PAPER,font=("Arial",14,"bold"))

    def draw(self):
        self.canvas.delete("all")
        if self.state=="title": self.draw_title()
        elif self.state=="settings": self.draw_settings()
        elif self.state=="stand_select": self.draw_stand_select()
        elif self.state=="character_select": self.draw_character_select()
        elif self.state=="howto": self.draw_howto()
        elif self.state=="records": self.draw_records()
        elif self.state=="chess": self.draw_chess()
        elif self.state=="town": self.draw_town_3d()
        elif self.state in ("race","bossintro"):
            self.draw_background();self.draw_depth_track();self.draw_pickups_hazards()
            for r in sorted(self.racers,key=lambda q:q.lane):
                x=self.world_x(r.progress)
                if not (-100<x<WIDTH+100): continue
                ry=LANE_Y[int(clamp(round(r.lane),0,3))]
                if r.out or r.knocked>0:
                    # Cartoon dust, a fallen rider, and stars communicate a knockout without gore.
                    if r.out and r.out_timer<=0: continue
                    self.canvas.create_oval(x-37,ry+2,x+40,ry+28,fill="#d9b87e",outline="")
                    self.canvas.create_oval(x-13,ry-8,x+8,ry+5,fill="#edc39c",outline="#775748")
                    self.canvas.create_line(x-8,ry+4,x+16,ry+14,fill=r.color,width=8)
                    self.canvas.create_line(x+5,ry+10,x+23,ry+22,fill="#4b3c36",width=4)
                    for n in range(3):
                        self.canvas.create_text(x-15+n*15,ry-20-abs(math.sin(self.elapsed*8+n))*8,text="★",fill=GOLD,font=("Arial",13,"bold"))
                    if r.out:
                        self.canvas.create_text(x,ry+36,text="ELIMINATED",fill=PAPER,font=("Arial",8,"bold"))
                    continue
                lane_idx = int(clamp(round(r.lane), 0, 3))
                depth = [0.72, 0.82, 0.92, 1.02][lane_idx]
                if r.stand:
                    self.draw_stand_companion(x-34*depth, ry-24*depth, r.stand, .76*depth,
                                              self.elapsed+r.progress*.01)
                self.draw_horse(x,ry,r.color,False,True,r.name,r.ally,self.elapsed+r.progress*.01,r.stand,depth)
            player_lane_idx = int(clamp(round(self.lane), 0, 3))
            player_y = LANE_Y[player_lane_idx]
            player_depth = [0.72, 0.82, 0.92, 1.02][player_lane_idx]
            if self.stand:
                self.draw_stand_companion(218, player_y-29*player_depth, self.stand, 1.0*player_depth,
                                          self.elapsed)
            player_horse_x = 325 if self.dismounted_timer > 0 else 255
            self.draw_horse(player_horse_x,player_y,HORSE_COATS.get(self.character_name,"#d7d9d3"),True,False,
                            name=self.character_name,phase=self.elapsed,stand=self.stand,depth_scale=player_depth)
            if self.dismounted_timer > 0 and self.character_name != "Sandman":
                # Separate rider silhouette makes it visually clear the player has fallen off.
                rx, ry = 220, player_y + 1
                look = CHARACTER_LOOKS.get(self.character_name, CHARACTER_LOOKS["Johnny Joestar"])
                if self.character_name == "Johnny Joestar":
                    # Johnny crawls along the ground while dismounted, reflecting his limited leg mobility.
                    crawl = math.sin(self.elapsed * 10.0) * 4
                    self.canvas.create_oval(rx-24,ry-16,rx+17,ry+1,fill=look["shirt"],outline="#2a2227",width=2)
                    self.canvas.create_oval(rx+9,ry-28,rx+27,ry-11,fill=look["hair"],outline="#2a2227",width=2)
                    self.canvas.create_polygon(rx+7,ry-18,rx+24,ry-17,rx+29,ry-11,rx+10,ry-9,
                                               fill=look["headgear"],outline="#2a2227",width=1)
                    self.canvas.create_line(rx-12,ry-4,rx-25,ry+8+crawl,rx-35,ry+9+crawl,
                                            fill=look["shirt"],width=6,smooth=True)
                    self.canvas.create_line(rx+3,ry-5,rx+14,ry+4-crawl,rx+24,ry+5-crawl,
                                            fill=look["shirt"],width=6,smooth=True)
                    self.canvas.create_line(rx-14,ry-8,rx-5,ry+2,rx+2,ry+6,fill="#4a3938",width=5,smooth=True)
                    self.canvas.create_line(rx+2,ry-8,rx-2,ry+2,rx-12,ry+7,fill="#4a3938",width=5,smooth=True)
                    self.canvas.create_text(rx,ry-40,text="JOHNNY CRAWLING",fill="#ffcf9b",font=("Arial",9,"bold"))
                else:
                    self.canvas.create_oval(rx-9,ry-38,rx+9,ry-20,fill=look["hair"],outline="#2a2227",width=2)
                    self.canvas.create_polygon(rx-10,ry-22,rx+10,ry-22,rx+14,ry+3,rx-12,ry+3,
                                               fill=look["shirt"],outline="#2a2227",width=2)
                    self.canvas.create_line(rx-6,ry+1,rx-18,ry+17,fill=look["shirt"],width=6)
                    self.canvas.create_line(rx+6,ry+1,rx+18,ry+15,fill=look["shirt"],width=6)
                    self.canvas.create_line(rx-6,ry+3,rx-12,ry+25,fill="#4a3938",width=6)
                    self.canvas.create_line(rx+6,ry+3,rx+12,ry+25,fill="#4a3938",width=6)
                    self.canvas.create_text(rx,ry-53,text="RIDER DOWN",fill="#ffcf9b",font=("Arial",9,"bold"))
            # High-speed streaks and drifting dust add motion without external assets.
            if self.speed > 265 or self.overdrive_active > 0 or self.race_event in ("GOLDEN RUSH", "STAMPede"):
                intensity = 5 if self.overdrive_active <= 0 else 11
                for streak in range(intensity):
                    sy = 145 + ((streak * 53 + int(self.elapsed * (180 + self.speed))) % (HEIGHT - 220))
                    sx = (streak * 137 + int(self.elapsed * (260 + self.speed * .55))) % (WIDTH + 100)
                    length = 24 + int(min(70, self.speed * .12))
                    col = "#f2d49b" if self.overdrive_active > 0 else "#9dc9d9"
                    self.canvas.create_line(sx, sy, sx-length, sy+2, fill=col, width=1 if streak % 3 else 2)
            # Dust particles scroll at different speeds for a layered sense of depth.
            for particle in self.ambient_dust:
                particle["x"] -= particle["speed"] / 30.0
                if particle["x"] < -5:
                    particle["x"] = WIDTH + random.uniform(0, 80)
                    particle["y"] = random.uniform(130, HEIGHT-70)
                if 0 <= particle["x"] <= WIDTH:
                    px, py = particle["x"], particle["y"]
                    self.canvas.create_oval(px, py, px+particle["size"], py+particle["size"], fill="#cbbd9d", outline="")
            self.draw_ability_effects()
            self.draw_hud()
            if self.balance_qte_timer > 0:
                self.canvas.create_rectangle(260, 190, WIDTH-260, 265, fill="#4c2632", outline="#ffe0a4", width=3)
                self.canvas.create_text(WIDTH/2, 211, text="STAY IN THE SADDLE!", fill="#fff0d0", font=("Arial", 21, "bold"))
                self.canvas.create_text(WIDTH/2, 241, text=f"MASH SPACE / E / K / G / Q / ENTER  •  {self.balance_qte_taps}/{self.balance_qte_needed}", fill="#ffffff", font=("Arial", 12, "bold"))
            elif self.dismounted_timer > 0:
                self.canvas.create_rectangle(300, 190, WIDTH-300, 260, fill="#4c2632", outline="#ffe0a4", width=3)
                self.canvas.create_text(WIDTH/2, 211, text="THROWN OFF YOUR HORSE!", fill="#fff0d0", font=("Arial", 19, "bold"))
                self.canvas.create_text(WIDTH/2, 239, text=f"MASH SPACE / E / ENTER TO REMOUNT  •  {self.mount_recovery}/5", fill="#ffffff", font=("Arial", 11, "bold"))
            if self.show_help and self.state == "race":
                self.canvas.create_rectangle(245, 150, WIDTH-245, 360, fill="#171d29", outline="#edc45f", width=2)
                self.canvas.create_text(WIDTH/2, 178, text="QUICK RIDER GUIDE", fill="#edc45f", font=("Arial", 20, "bold"))
                guide = ["← / → or A / D: change lanes and dodge hazards", "SHIFT: sprint (uses stamina)   •   Q: burst dash",
                         "SPACE: attack rivals   •   K: use your equipped Stand   •   G: Golden Spin (after 5 tokens)", "E: recruit a nearby rider as an ally",
                         "Collect food, shield horseshoes, speed stars, and Spin tokens for bonuses.",
                         "Dodge hazards at the last moment for CLOSE CALL combo points.",
                         "At each stage finish, defeat the boss. Allies attack and heal during boss fights.",
                         "Press T during a race to explore the 3D town; SPACE fights, K uses your Stand.",
                         "Press H to close this guide."]
                for i, line in enumerate(guide):
                    self.canvas.create_text(WIDTH/2, 211+i*21, text=line, fill="#f6ead0", font=("Arial", 11, "bold"))
            if self.state=="bossintro":
                self.canvas.create_rectangle(0,0,WIDTH,HEIGHT,fill="#10101a",stipple="gray50",outline="")
                for i in range(15):
                    xx = (i*91 + int(self.elapsed*95)) % (WIDTH+80) - 40
                    self.canvas.create_line(xx,80,xx-105,HEIGHT-65,fill=hexmix("#3b233d","#9c456b",(i%7)/7),width=2)
                self.canvas.create_rectangle(0,0,WIDTH,34,fill="#08090f",outline="")
                self.canvas.create_rectangle(0,HEIGHT-34,WIDTH,HEIGHT,fill="#08090f",outline="")
                self.canvas.create_rectangle(135,200,985,488,fill="#191925",outline="#d4a2bd",width=3)
                boss = self.current_boss()
                self.canvas.create_text(WIDTH/2,240,text=f"STAGE {self.current_stage + 1}  •  {self.stage_names()[self.current_stage]}",fill="#efc16d",font=("Arial",15,"bold"))
                self.canvas.create_text(WIDTH/2,307,text=boss["name"].upper(),fill=boss["color"],font=("Arial",38,"bold"))
                self.canvas.create_line(330,337,790,337,fill=boss["color"],width=3)
                self.canvas.create_text(WIDTH/2,373,text=boss["subtitle"],fill="#d99bb9",font=("Arial",16,"bold"))
                self.canvas.create_text(WIDTH/2,426,text=f"Stage {self.current_stage + 1} ends here. Press ENTER to challenge {boss['name']}.",fill=WHITE,font=("Arial",13,"bold"))
                self.canvas.create_text(WIDTH/2,446,text=f"TEAM READY: {self.allies} ALLIES  •  Allies attack automatically and can heal you.",fill="#80e6c1",font=("Arial",11,"bold"))
                pulse = .6 + .4*math.sin(self.elapsed*4)
                self.canvas.create_text(WIDTH/2,461,text=self.stage_names()[self.current_stage],fill=hexmix(boss["color"],"#fff0cf",pulse),font=("Arial",13,"bold"))
        elif self.state=="boss": self.draw_boss()
        else:self.draw_end()
        if IS_BROWSER:
            c = self.canvas
            c.create_rectangle(WIDTH-153, 7, WIDTH-9, 38, fill='#1d202b', outline=GOLD, width=2)
            c.create_text(WIDTH-81, 22, text='[ ] FULLSCREEN', fill=PAPER,
                          font=('Arial', 13, 'bold'))

    def tick(self):
        previous_state = self.state
        now = time.perf_counter()
        dt = min(now - self.last_tick, 0.06)
        self.last_tick = now
        if self.state == "title":
            self.elapsed += dt
        elif self.state == "race":
            self.update(dt)
        elif self.state == "boss":
            self.update_boss(dt)
        elif self.state == "bossintro":
            self.elapsed += dt
            self.message_timer = max(0, self.message_timer - dt)
        elif self.state == "town":
            self.update_town(dt)
        if self.state in ("victory", "failed"):
            self.record_run_result()
        if self.state == "victory" and previous_state != "victory":
            self.play_sfx("win")
        elif self.state == "failed" and previous_state != "failed":
            self.play_sfx("hit")
        self._set_music_for_state()
        # Draw to the fixed-size game surface, then scale it to the real
        # display surface. This avoids black frames caused by SDL fullscreen
        # mode changes returning a surface with unexpected dimensions.
        self.draw()
        if self.screen.get_size() == (WIDTH, HEIGHT):
            self.screen.blit(self.game_surface, (0, 0))
        else:
            frame = pygame.transform.smoothscale(self.game_surface, self.screen.get_size())
            self.screen.blit(frame, (0, 0))
        pygame.display.flip()

    def browser_fullscreen(self):
        """Request real browser fullscreen from a user key/mouse event."""
        if not IS_BROWSER:
            return
        try:
            from platform import window
            doc = window.document
            if doc.fullscreenElement:
                doc.exitFullscreen()
            else:
                doc.documentElement.requestFullscreen()
        except Exception as exc:
            print('Fullscreen request unavailable:', exc, flush=True)

    async def run(self):
        key_names = {
            pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
            pygame.K_a: "a", pygame.K_d: "d", pygame.K_SPACE: "space",
            pygame.K_k: "k", pygame.K_e: "e", pygame.K_c: "c", pygame.K_q: "q", pygame.K_g: "g",
            pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_w: "w", pygame.K_s: "s",
            pygame.K_RETURN: "return", pygame.K_m: "m", pygame.K_h: "h", pygame.K_t: "t", pygame.K_b: "b", pygame.K_r: "r", pygame.K_F1: "f1",
            pygame.K_ESCAPE: "escape", pygame.K_LSHIFT: "shift_l",
            pygame.K_RSHIFT: "shift_r",
        }
        from types import SimpleNamespace
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                    break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if IS_BROWSER:
                        dw, dh = self.screen.get_size()
                        mx = event.pos[0] * WIDTH / max(1, dw)
                        my = event.pos[1] * HEIGHT / max(1, dh)
                        if WIDTH-153 <= mx <= WIDTH-9 and 7 <= my <= 38:
                            self.browser_fullscreen()
                            continue
                        # Audio unlock after a real user interaction.
                        if self.audio_enabled and self.music_state is None:
                            self._set_music_for_state(force=True)
                    # The Chess Duel menu row is clickable as well as keyboard-accessible.
                    # Coordinates match the visible B row in draw_title().
                    if self.state == "title":
                        mx, my = event.pos
                        if 600 <= mx <= 1038 and 426 <= my <= 456:
                            self.open_chess_duel()
                            continue
                    if self.state == "chess":
                        self.chess_click(event.pos)
                elif event.type == pygame.MOUSEWHEEL:
                    if self.state == "stand_select":
                        self.scroll_stand_archive(-event.y)
                elif event.type == pygame.KEYDOWN:
                    # Handle the title-screen B shortcut at the event source as
                    # well as in key_down(). This avoids keyboard-name/focus
                    # translation issues preventing the menu transition.
                    # Accept both the physical B keycode and the text generated by
                    # the keyboard. Do not depend on the menu's secondary key handler.
                    typed = getattr(event, "unicode", "")
                    if self.state in ("title", "menu", "main_menu") and (
                        event.key == pygame.K_b or typed.lower() == "b"
                    ):
                        self.open_chess_duel()
                        continue
                    if event.key == pygame.K_F11 and IS_BROWSER:
                        self.browser_fullscreen()
                        continue
                    if event.key == pygame.K_F11 and not IS_BROWSER:
                        # Recreate only the presentation window. The logical
                        # game surface and its drawing canvas are never reset.
                        try:
                            if self.fullscreen:
                                self.screen = pygame.display.set_mode(
                                    (WIDTH, HEIGHT), pygame.RESIZABLE
                                )
                                self.fullscreen = False
                            else:
                                info = pygame.display.Info()
                                desktop_size = (
                                    max(WIDTH, info.current_w),
                                    max(HEIGHT, info.current_h),
                                )
                                self.screen = pygame.display.set_mode(
                                    desktop_size, pygame.FULLSCREEN
                                )
                                self.fullscreen = True
                        except pygame.error:
                            # Recover to a known-good windowed mode rather
                            # than leaving the game attached to a black surface.
                            self.screen = pygame.display.set_mode(
                                (WIDTH, HEIGHT), pygame.RESIZABLE
                            )
                            self.fullscreen = False

                        self.last_tick = time.perf_counter()
                        continue
                    name = key_names.get(event.key)
                    if name:
                        self.key_down(SimpleNamespace(keysym=name))
                elif event.type == pygame.KEYUP:
                    name = key_names.get(event.key)
                    if name:
                        self.key_up(SimpleNamespace(keysym=name))
            if self.running:
                self.tick()
                if not IS_BROWSER:
                    self.clock.tick(60)
            await asyncio.sleep(1 / 60 if IS_BROWSER else 0)
        pygame.quit()

if __name__ == "__main__":
    async def main():
        print("STAND RUSH: initializing", flush=True)
        try:
            game = SteelBallRunGame()
            print("STAND RUSH: initialized; drawing title screen", flush=True)
            game.tick()
            await asyncio.sleep(0)
            await game.run()
        except Exception:
            import traceback
            traceback.print_exc()
            raise
    asyncio.run(main())
