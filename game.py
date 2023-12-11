# https://opengameart.org/node/32390
# https://opengameart.org/content/2d-enemy-characters-pack-20x20
# https://opengameart.org/content/grass-pixel-art
# https://opengameart.org/content/tiles-3
# https://xdeviruchi.itch.io/8-bit-fantasy-adventure-music-pack


# modules
import random
import math

# pgzero modules
from pgzero.builtins import Actor
from pgzero.builtins import music
from pgzero.builtins import clock
from pgzero.builtins import animate
from pgzero.builtins import keys
from pgzero.builtins import keyboard
from pgzero.builtins import sounds
import pgzero.screen
screen : pgzero.screen.Screen
import pgzrun


# constants
HEIGHT = 500
WIDTH = 500
TRANSITION_DICT = {
    "up": [(250, -250), (250, 750), 0, 2, 0, 1, 0, 500],
    "down": [(250, 750), (250, -250), 0, -2, 0, -1, 0, -500],
    "left": [(-250, 250), (750, 250), 2, 0, -1, 0, 500, 0],
    "right": [(750, 250), (-250, 250), -2, 0, 1, 0, -500, 0],
}
# {direction: [background1_starting_pos, background0_finishing_pos, if_false_player_x_change, if_false_player_y_change, x_coord_change, y_coord_change, animation_x_change, animation_y_change]}
SLIME_FILENAMES = [["slime_blue_left.png", "slime_blue_right.png"],
                   ["slime_green_left.png", "slime_green_right.png"],
                   ["slime_orange_left.png", "slime_orange_right.png"],
                   ["slime_pink_left.png", "slime_pink_right.png"]]
BOSS_FILENAMES = [["boss_blue_left", "boss_blue_right"],
                 ["boss_green_left", "boss_green_right"],
                 ["boss_orange_left", "boss_orange_right"],
                 ["boss_pink_left", "boss_pink_right"]]
PROJECTILE_FILENAMES = ["projectile_blue.png", "projectile_green.png", "projectile_orange.png", "projectile_pink.png"]


# variables
# background
background0 = Actor("background.png")
background1 = Actor("background.png")
start_menu = Actor("start_menu.png")
boss_arena = Actor("boss_arena.png")

# character
character = Actor("character_down.png")

# sword
sword = Actor("sword_right.png")

# lives
empty_hearts = [
    Actor("heart_empty.png", (20, 20)),
    Actor("heart_empty.png", (60, 20)),
    Actor("heart_empty.png", (100, 20)),
]
hearts = [
    Actor("heart.png", (20, 20)),
    Actor("heart.png", (60, 20)),
    Actor("heart.png", (100, 20)),
]
lives = 3
life_powerups = []

# enemies
enemies = []
bosses = []
projectiles = []

# score
score = 0
high_score = 0

# map
map = {"coords": [0, 0], (0, 0): {"life_powerups": [], "enemies": [], "bosses": []}}

# states
transition = False
stun = False
sword_activated = False
sword_activated = False
ts = False
last_direction = None
sword_allowed = True
boss = False
game_state = 0


# initialisation
def reset_game():
    global game_state, lives, life_powerups, enemies, bosses, boss, projectiles, score, high_score, map
    # game state
    game_state = 0

    # character
    character.center = (250, 250)

    # lives
    lives = 3
    life_powerups = []

    # enemies
    enemies = []
    bosses = []
    projectiles = []
    boss = False

    # music
    music.set_volume(0.5)
    if (ts == True):
        music.play("illicit_affairs.wav")
    else:
        music.play("background.wav")

    # score
    if (score > high_score):
        high_score = score
    score = 0

    # map
    map = {"coords": [0, 0], (0, 0): {"life_powerups": [], "enemies": [], "bosses": []}}
reset_game()


# counter alternates between 0 and 1 every 0.15s for animations
counter_val = 0
def counter():
    global counter_val
    counter_val += 1
    counter_val %= 2
clock.schedule_interval(counter, 0.15)

# boss projectile creation
def remove_projectile():
    projectiles.pop(0)
def shoot_projectile():
    projectiles.append(Actor(PROJECTILE_FILENAMES[bosses[0].color], bosses[0].pos))
    deltax = (character.x - projectiles[-1].x)
    deltay = (character.y - projectiles[-1].y)
    vectormag = math.sqrt(deltax**2 + deltay**2)
    deltax /= vectormag
    deltay /= vectormag
    deltax *= 2
    deltay *= 2
    projectiles[-1].deltax = deltax
    projectiles[-1].deltay = deltay
    clock.schedule(remove_projectile, 5.0)

# new screen
def new_screen(coords):
    if not (boss):
        if (random.random() < 0.8):
            for x in range(random.randint(1, 3)):
                color = random.randint(0, 3)
                map[coords]["enemies"].append(Actor(SLIME_FILENAMES[color][0], (random.randint(100, 400), random.randint(100, 400))))
                map[coords]["enemies"][-1].save = False
                map[coords]["enemies"][-1].color = color
        else:
            map[coords]["life_powerups"].append(Actor("heart.png", (random.randint(100, 400), random.randint(100, 400))))
            map[coords]["life_powerups"][-1].save = False
    else:
        color = random.randint(0, 3)
        map[coords]["bosses"].append(Actor(BOSS_FILENAMES[color][0] + "0.png", (250, 250)))
        map[coords]["bosses"][-1].save = False
        map[coords]["bosses"][-1].health = 5
        map[coords]["bosses"][-1].color = color
        clock.schedule_interval(shoot_projectile, 1.5)


# map
# returns map coordinates as a tuple
def get_map_coords():
    return tuple(map["coords"])

# adds coordinates as key to map if it doesn't already exist
def create_map_coords(coords):
    global map, life_powerups, enemies
    if not (get_map_coords() in map.keys()):
        map[coords] = {"life_powerups": [], "enemies": [], "bosses": []}
        return True
    else:
        return False

# unloads entities and saves them in map
def save_entities():
    for life in life_powerups.copy():
        if (life.save):
            life.save = False
            life_powerups.remove(life)
            life.center = life.oldpos
            map[life.coords]["life_powerups"].append(life)
    for enemy in enemies.copy():
        if (enemy.save):
            enemy.save = False
            enemies.remove(enemy)
            enemy.center = enemy.oldpos
            map[enemy.coords]["enemies"].append(enemy)

# transitions current enemies offscreen, updates coords and loads new enemies
def transition_map(coords, direction):
    for enemy in enemies:
        enemy.coords = coords
        enemy.oldpos = enemy.center
        enemy.save = True
        animate(enemy, pos=(enemy.x+TRANSITION_DICT[direction][6], enemy.y+TRANSITION_DICT[direction][7]))
    for life in life_powerups:
        life.coords = coords
        life.oldpos = life.center
        life.save = True
        animate(life, pos=(life.x+TRANSITION_DICT[direction][6], life.y+TRANSITION_DICT[direction][7]))

    map["coords"][0] += TRANSITION_DICT[direction][4]
    map["coords"][1] += TRANSITION_DICT[direction][5]
    coords = get_map_coords()
    if (create_map_coords(coords)):
        new_screen(coords)

    life_powerups.extend(map[coords]["life_powerups"])
    map[coords]["life_powerups"].clear()
    enemies.extend(map[coords]["enemies"])
    map[coords]["enemies"].clear()
    bosses.extend(map[coords]["bosses"])
    map[coords]["bosses"] = []
    for enemy in enemies:
        if not (enemy.save):
            enemy.x -= TRANSITION_DICT[direction][6]
            enemy.y -= TRANSITION_DICT[direction][7]
            animate(enemy, pos=(enemy.x+TRANSITION_DICT[direction][6], enemy.y+TRANSITION_DICT[direction][7]))
    for life in life_powerups:
        if not (life.save):
            life.x -= TRANSITION_DICT[direction][6]
            life.y -= TRANSITION_DICT[direction][7]
            animate(life, pos=(life.x+TRANSITION_DICT[direction][6], life.y+TRANSITION_DICT[direction][7]))
    for boss_enemy in bosses:
        boss_enemy.x -= TRANSITION_DICT[direction][6]
        boss_enemy.y -= TRANSITION_DICT[direction][7]
        animate(boss_enemy, pos=(boss_enemy.x+TRANSITION_DICT[direction][6], boss_enemy.y+TRANSITION_DICT[direction][7]))

    clock.schedule(save_entities, 1.0)


# functions
# completes background transition
def complete_transition():
    global transition
    background0.center = (250, 250)
    transition = False

# unstuns enemies
def unstun_enemies():
    global stun
    stun = False
    clock.schedule_interval(shoot_projectile, 1.5)

# transitions background
def transition_background(char_check_pos, new_char_pos, direction):
    global transition, boss
    if (char_check_pos > 225) and (char_check_pos < 275) and not (boss):
        animate(character, pos=new_char_pos)
        animate(sword, pos=new_char_pos)
        animate(background0, pos=TRANSITION_DICT[direction][1])

        new_coords = (map["coords"][0] + TRANSITION_DICT[direction][4], map["coords"][1] + TRANSITION_DICT[direction][5])
        if (random.random() < 0.2) and not (new_coords in map.keys()):
            boss_arena.center = TRANSITION_DICT[direction][0]
            animate(boss_arena, pos=(250, 250), on_finished=complete_transition)
            boss = True
            music.play("boss.wav")
        else:
            background1.center = TRANSITION_DICT[direction][0]
            animate(background1, pos=(250, 250), on_finished=complete_transition)

        transition = True
        transition_map(get_map_coords(), direction)
    else:
        character.x += TRANSITION_DICT[direction][2]
        character.y += TRANSITION_DICT[direction][3]

# deactivates sword
def deactivate_sword():
    global sword_activated
    sword_activated = False

# allows sword to be used
def allow_sword():
    global sword_allowed
    sword_allowed = True


# event hooks
# when key pressed
def on_key_down(key):
    global last_direction, sword_activated, sword_allowed
    #if (key == keys.E):
    #    enemies.append(Actor("slime_pink_left.png", (400, 250)))
    #if (key == keys.Q):
    #    life_powerups.append(Actor("heart.png", (100, 250)))
    if (key in [keys.W, keys.A, keys.S, keys.D]):
        last_direction = key
    if (key == keys.SPACE) and (sword_allowed):
        sword_activated = True
        sword_allowed = False
        clock.schedule(deactivate_sword, 0.5)
        clock.schedule(allow_sword, 1.0)


# when key released
def on_key_up(key):
    global last_direction
    if (key in [keys.W, keys.A, keys.S, keys.D]):
        last_direction = True


# redraw screen
def draw():
    # resets screen
    screen.clear()

    # start menu
    if (game_state == 0):
        start_menu.draw()
        screen.draw.text("High score: " + str(high_score), center=(250, 83), fontsize=32, fontname="pixel.ttf")
        screen.draw.text("Press space to start", center=(250, 167), fontsize=32, fontname="pixel.ttf")
        screen.draw.text("WASD to move\nSpace to use sword", center=(250, 375), fontsize=32, fontname="pixel.ttf")

    # game over screen
    if (game_state == 2):
        screen.fill("black")
        screen.draw.text("GAME OVER", center=(250, 250), fontsize=100, fontname="pixel.ttf")
        screen.draw.text("Press left shift to restart", center=(250, 300), fontsize=20, fontname="pixel.ttf")

    # main game
    if (game_state == 1):
        # draws background
        background0.draw()

        # draws boss arena
        if (boss):
            boss_arena.draw()
        else:
            background1.draw()

        # draws character
        character.draw()

        # draws hearts
        for empty_heart in empty_hearts:
            empty_heart.draw()
        for x in range(lives):
            hearts[x].draw()

        # draws life powerups
        for life in life_powerups:
            life.draw()

        # draws enemies
        for enemy in enemies:
            enemy.draw()

        # draws bosses
        for boss_enemy in bosses:
            boss_enemy.draw()

        # draws projectiles
        for projectile in projectiles:
            projectile.draw()

        # draws sword
        if (sword_activated):
            sword.draw()

        # draws score
        screen.draw.text(str(score), topright=(495, 5), fontsize=32, fontname="pixel.ttf")


# main game loop
def update():
    global lives, stun, game_state, score, boss

    # start menu
    if (game_state == 0):
        if (keyboard.space):
            game_state = 1

    # game over screen
    if (game_state == 2):
        if (keyboard.lshift):
            reset_game()

    # main game
    if (game_state == 1):
        # player and sword
        if (not transition):
            # up
            if (keyboard.w) and ((last_direction == keys.W) or (last_direction == True)):
                # movement
                character.y -= 2

                # update images
                character.image = "character_up" + str(counter_val) + ".png"
                sword.image = "sword_up.png"

                # update sword position
                sword.center = character.center
                sword.x += 0
                sword.y -= 30

                # transition background
                if (character.midtop[1] < 0):
                    transition_background(character.midtop[0], (character.midtop[0], 480), "up")

            # down
            if (keyboard.s) and ((last_direction == keys.S) or (last_direction == True)):
                # movement
                character.y += 2

                # update images
                character.image = "character_down" + str(counter_val) + ".png"
                sword.image = "sword_down.png"

                # update sword position
                sword.center = character.center
                sword.x += 0
                sword.y += 30

                # transition background
                if (character.midbottom[1] > 500):
                    transition_background(character.midbottom[0], (character.midbottom[0], 20), "down")

            # left
            if (keyboard.a) and ((last_direction == keys.A) or (last_direction == True)):
                # movement
                character.x -= 2

                # update images
                character.image = "character_left" + str(counter_val) + ".png"
                sword.image = "sword_left.png"

                # update sword position
                sword.center = character.center
                sword.x -= 15
                sword.y += 5

                # transition background
                if (character.midleft[0] < 0):
                    transition_background(character.midleft[1], (480, character.midleft[1]), "left")

            # right
            if (keyboard.d) and ((last_direction == keys.D) or (last_direction == True)):
                # movement
                character.x += 2

                # update images
                character.image = "character_right" + str(counter_val) + ".png"
                sword.image = "sword_right.png"

                # update sword position
                sword.center = character.center
                sword.x += 15
                sword.y += 5

                # transition background
                if (character.midright[0] > 500):
                    transition_background(character.midright[1], (20, character.midright[1]), "right")

        # lives
        # life power-up collection
        for life in life_powerups:
            if character.colliderect(life):
                sounds.powerup.play()
                if lives != 3:
                    lives += 1
                else:
                    score += 10
                life_powerups.remove(life)

        # enemies
        for enemy in enemies:
            # stun enemies and remove a life
            if (character.colliderect(enemy)) and (not stun):
                sounds.damage.play()
                stun = True
                clock.unschedule(shoot_projectile)
                clock.schedule(unstun_enemies, 1.0)
                if lives != 1:
                    lives -= 1
                else:
                    music.stop()
                    sounds.game_over.play()
                    game_state = 2

            # enemy movement
            if (not stun) and (not transition):
                if (random.randint(0, 1) == 0):
                    if (enemy.x > character.x):
                        enemy.x -= 1
                        enemy.image = SLIME_FILENAMES[enemy.color][0]
                    elif (enemy.x < character.x):
                        enemy.x += 1
                        enemy.image = SLIME_FILENAMES[enemy.color][1]
                else:
                    if (enemy.y > character.y):
                        enemy.y -= 1
                    elif (enemy.y < character.y):
                        enemy.y += 1

            # kill enemy
            if (sword_activated):
                if (sword.colliderect(enemy)):
                    enemies.remove(enemy)
                    score += 10
                    if (ts):
                        if (random.random() > 0.2):
                            sounds.lwymmd.play()
                        else:
                            sounds.oh.play()
                    else:
                        sounds.splat.play()

        # bosses
        for boss_enemy in bosses:
            # stun enemies and remove a life
            if (character.colliderect(boss_enemy)) and (not stun):
                sounds.damage.play()
                stun = True
                clock.unschedule(shoot_projectile)
                clock.schedule(unstun_enemies, 1.0)
                if lives != 1:
                    lives -= 1
                else:
                    music.stop()
                    sounds.game_over.play()
                    game_state = 2

            # boss movement
            if (not stun) and (not transition):
                if (boss_enemy.x > character.x):
                    boss_enemy.x -= 0.5
                    boss_enemy.image = BOSS_FILENAMES[boss_enemy.color][0] + str(counter_val) + ".png"
                else:
                    boss_enemy.x += 0.5
                    boss_enemy.image = BOSS_FILENAMES[boss_enemy.color][1] + str(counter_val) + ".png"
                if (boss_enemy.y > character.y):
                    boss_enemy.y -= 0.5
                else:
                    boss_enemy.y += 0.5

            # deal damage to boss
            if (sword_activated):
                if (sword.colliderect(boss_enemy)):
                    boss_enemy.health -= 1
                    # knockback
                    if (sword.image == "sword_up.png"):
                        boss_enemy.y -= 50
                    if (sword.image == "sword_down.png"):
                        boss_enemy.y += 50
                    if (sword.image == "sword_left.png"):
                        boss_enemy.x -= 50
                    if (sword.image == "sword_right.png"):
                        boss_enemy.x += 50
                    # kill boss
                    if (boss_enemy.health == 0):
                        bosses.remove(boss_enemy)
                        if (ts == True):
                            music.play("illicit_affairs.wav")
                        else:
                            music.play("background.wav")
                        clock.unschedule(shoot_projectile)
                        boss = False
                        score += 50
                        if (ts):
                            if (random.random() > 0.2):
                                sounds.lwymmd.play()
                            else:
                                sounds.oh.play()
                        else:
                            sounds.splat.play()
                    else:
                        sounds.boss_damage.play()

        # projectiles
        for projectile in projectiles:
            projectile.x += projectile.deltax
            projectile.y += projectile.deltay

            if (character.colliderect(projectile)) and (not stun):
                sounds.damage.play()
                stun = True
                clock.unschedule(shoot_projectile)
                clock.schedule(unstun_enemies, 1.0)
                if lives != 1:
                    lives -= 1
                else:
                    music.stop()
                    sounds.game_over.play()
                    game_state = 2

pgzrun.go()