import pygame
import pytmx
import pyscroll
from sys import exit
import math
import random
import time
from pygame.font import Font
from settings import *
import os

pygame.init()

# Creating the window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game_Survie")
clock = pygame.time.Clock()

script_dir = os.path.dirname(os.path.abspath(__file__))


# Loads images
tmx_file_path = os.path.join(script_dir, "Map", "World.tmx")
tmx_data = pytmx.util_pygame.load_pygame(tmx_file_path)
map_data = pyscroll.data.TiledMapData(tmx_data)
map_layer = pyscroll.orthographic.BufferedRenderer(map_data, (WIDTH, HEIGHT))
group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=2)
map_layer.zoom = 1.5

tsx_file_path = os.path.join(script_dir, "Map", "nature.tsx")

Walls = []

for obj in tmx_data.objects:
    if obj.type == "collision":
        Walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        player_sprite_path = os.path.join(script_dir, "Player", "0.png")
        self.sprite_sheet = pygame.image.load(player_sprite_path)
        self.image = self.get_image(0, 0)
        self.image.set_colorkey([0, 0, 0])
        self.image_player = self.image.get_rect()


        self.health = 100
        self.pos = [x, y]
        self.width = width
        self.height = height
        self.speed = PLAYER_SPEED
        self.last_hit_time = 0

        self.feet = pygame.Rect(0, 0, self.image_player.width * 0.5, 12)

        self.images = { "down" : self.get_image(0,128), "left" : self.get_image(0,64), "right" : self.get_image(0,192), "up" : self.get_image(0,0)}

        self.base_player_image = self.image
        self.hitbox_rect = self.base_player_image.get_rect(center=self.pos)
        self.rect = self.hitbox_rect.copy()

        self.shoot = False
        self.shoot_cooldown = 0

        self.gun_barrel_offset = pygame.math.Vector2(GUN_OFFSET_X, GUN_OFFSET_Y)

    def save_location(self): self.rect = self.hitbox_rect.copy()
    def change_animation(self, name):
        self.image = self.images[name]
        self.image.set_colorkey([0, 0, 0])

    def player_rotation(self):
        self.mouse_coords = pygame.mouse.get_pos()
        self.x_change_mouse_player = (self.mouse_coords[0] - self.hitbox_rect.centerx)
        self.y_change_mouse_player = (self.mouse_coords[1] - self.hitbox_rect.centery)
        self.angle = math.degrees(math.atan2(self.y_change_mouse_player, self.x_change_mouse_player))
        # self.image = pygame.transform.rotate(self.base_player_image, -self.angle)
        self.rect = self.image.get_rect(center=self.hitbox_rect.center)

    def user_input(self):
        self.velocity_x = 0
        self.velocity_y = 0

        keys = pygame.key.get_pressed()

        if keys[pygame.K_z]:
            self.velocity_y = -self.speed
            self.change_animation('up')
        if keys[pygame.K_s]:
            self.velocity_y = self.speed
            self.change_animation('down')
        if keys[pygame.K_d]:
            self.velocity_x = self.speed
            self.change_animation('right')
        if keys[pygame.K_q]:
            self.velocity_x = -self.speed
            self.change_animation('left')

        if self.velocity_x != 0 and self.velocity_y != 0:  # moving diagonally
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)

        if pygame.mouse.get_pressed() == (1, 0, 0) or keys[pygame.K_SPACE]:
            self.shoot = True
            self.is_shooting()
        else:
            self.shoot = False

    def is_shooting(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_bullet_pos = self.pos + self.gun_barrel_offset.rotate(self.angle)
            self.bullet = Bullet(spawn_bullet_pos[0], spawn_bullet_pos[1], self.angle)
            bullet_group.add(self.bullet)
            all_sprites_group.add(self.bullet)

    def check_collision(self, proposed_rect):
        feet_rect = self.feet.move(self.velocity_x, self.velocity_y)

        for wall_rect in Walls:
            if feet_rect.colliderect(wall_rect):
                return True  # Collision détectée au niveau des pieds
        return False

    def update(self):
        self.user_input()
        self.move()
        self.player_rotation()
        self.feet.midbottom = self.rect.midbottom
        self.rect.topleft = self.hitbox_rect.topleft

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self):
        proposed_rect = self.rect.move(self.velocity_x, self.velocity_y)

        if not self.check_collision(proposed_rect):
            self.pos += pygame.math.Vector2(self.velocity_x, self.velocity_y)
            self.hitbox_rect.center = self.pos
            self.rect.center = self.hitbox_rect.center

    def take_damage(self, amount):
        current_time = time.time()

        # Vérifiez si le temps écoulé depuis la dernière attaque est supérieur à 30 secondes
        if current_time - self.last_hit_time > 1:
            if self.health > 0:
                self.health -= amount
                self.last_hit_time = current_time

    def get_image(self, x, y):
        image = pygame.Surface([64, 64])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 64, 64))
        return image

    def center_player_and_update_position(self):
        # Centrer l'image du joueur sur sa position
        self.rect.x = self.pos.x - self.width / 2
        self.rect.y = self.pos.y - self.height / 2

        # Mettre à jour la position du joueur pour permettre aux ennemis de se diriger vers le centre
        self.pos.x = self.rect.x + self.width / 2
        self.pos.y = self.rect.y + self.height / 2


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        Bullet_sprite_path = os.path.join(script_dir, "Player", "1.png")
        self.image = pygame.image.load(Bullet_sprite_path).convert_alpha()
        self.image = pygame.transform.rotozoom(self.image, 0, BULLET_SCALE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.x_vel = math.cos(self.angle * (2 * math.pi / 360)) * self.speed
        self.y_vel = math.sin(self.angle * (2 * math.pi / 360)) * self.speed
        self.bullet_lifetime = BULLET_LIFETIME
        self.spawn_time = pygame.time.get_ticks()  # gets the specific time that the bullet was created

    def bullet_movement(self):
        self.x += self.x_vel
        self.y += self.y_vel

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

        if pygame.time.get_ticks() - self.spawn_time > self.bullet_lifetime:
            self.kill()

    def update(self):
        self.bullet_movement()
        if pygame.sprite.spritecollide(self, enemy_group, False):
            enemy_hit = pygame.sprite.spritecollide(self, enemy_group, False)[0]
            enemy_hit.hit_counter += 1
            if enemy_hit.hit_counter >= 3:
                enemy_hit.kill()
                global enemy_deaths
                enemy_deaths += 1
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        Enemy_sprite_path = os.path.join(script_dir, "Enemy", "02.png")
        self.sprite_sheet = pygame.image.load(Enemy_sprite_path)
        self.image = self.get_image(0, 0)
        self.image.set_colorkey([0, 0, 0])
        self.rect = self.image.get_rect()
        self.position = [x, y]
        self.hit_counter = 0

        self.direction = pygame.math.Vector2()
        self.velocity = pygame.math.Vector2()
        self.speed = speed

        self.position = pygame.math.Vector2(self.position)

    def hunt_player(self):
        player_vector = pygame.math.Vector2(player.hitbox_rect.center)
        enemy_vector = pygame.math.Vector2(self.rect.center)
        distance = self.get_vector_distance(player_vector, enemy_vector)

        if distance > 0:
            self.direction = (player_vector - enemy_vector).normalize()
        else:
            self.direction = pygame.math.Vector2()

        self.velocity = self.direction * self.speed
        self.position += self.velocity

        self.rect.centerx = self.position.x
        self.rect.centery = self.position.y

    def get_vector_distance(self, vector_1, vector_2):
        return (vector_1 - vector_2).magnitude()

    def update(self):
        self.rect.topleft = self.position
        self.hunt_player()

    def get_image(self, x, y):
        image = pygame.Surface([64, 64])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 64, 64))
        return image


class Mouse(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        Mouse_sprite_path = os.path.join(script_dir, "Player", "crosshairs64.png")
        self.sprite_sheet = pygame.image.load(Mouse_sprite_path)
        self.image = self.get_image(0, 0)
        self.image.set_colorkey([0, 0, 0])
        self.rect = self.image.get_rect()

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.rect.topleft = (mouse_pos[0] - self.rect.width // 2, mouse_pos[1] - self.rect.height // 2)

    def get_image(self, x, y):
        image = pygame.Surface([64, 64])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 64, 64))
        return image

class PlayerUI(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.font = Font(None, 36)
        self.image = self.render_text()
        self.rect = self.image.get_rect()
        self.rect.topleft = (10, 10)

    def render_text(self):
        hp_text = f"HP: {self.player.health}"
        return self.font.render(hp_text, True, (255, 255, 255))

    def update(self):
        self.image = self.render_text()

def spawn_enemy():
    random_wall = random.choice(Walls)
    x = random.uniform(random_wall.left, random_wall.right)
    y = random.uniform(random_wall.top, random_wall.bottom)

    new_enemy = Enemy(x, y, speed=ENEMY_SPEED)
    enemy_group.add(new_enemy)
    all_sprites_group.add(new_enemy)

def Vage_text():
    game_info_text = f"Vague : {current_wave}"
    game_info_surface = pygame.font.Font(None, 24).render(game_info_text, True, (255, 255, 255))
    game_info_rect = game_info_surface.get_rect(center=(WIDTH // 2, 20))
    screen.blit(game_info_surface, game_info_rect)

def Counter():
    global total_game_time  # Assurez-vous que total_game_time est une variable globale

    time_in_seconds = int(total_game_time)
    hours = time_in_seconds // 3600
    minutes = (time_in_seconds % 3600) // 60
    seconds = time_in_seconds % 60

    total_game_time += 1

    game_info_text = f"Temps de jeu : {hours:02d}:{minutes:02d}:{seconds:02d}  Morts d'ennemis : {enemy_deaths}"
    game_info_surface = pygame.font.Font(None, 24).render(game_info_text, True, (255, 255, 255))
    game_info_rect = game_info_surface.get_rect(right=WIDTH - 10, top=10)
    screen.blit(game_info_surface, game_info_rect)

def game_over_screen():
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 36)

    # Afficher les statistiques
    stats_text = [
        f"Temps de vie : {format_time(total_game_time)}",
        f"Nombre d'ennemis tués : {enemy_deaths}",
        f"Vague atteinte : {current_wave}"
    ]

    # Afficher les statistiques à l'écran
    for i, stat in enumerate(stats_text):
        text = font.render(stat, True, (255, 255, 255))
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + i * 40))
        screen.blit(text, text_rect)

    # Afficher le bouton pour relancer le jeu
    restart_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
    pygame.draw.rect(screen, (255, 0, 0), restart_button)
    restart_text = font.render("Relancer le jeu", True, (255, 255, 255))
    restart_text_rect = restart_text.get_rect(center=restart_button.center)
    screen.blit(restart_text, restart_text_rect)

    pygame.display.flip()

    # Attendre que le joueur clique sur le bouton
    waiting_for_restart = True
    while waiting_for_restart:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if restart_button.collidepoint(event.pos):
                    waiting_for_restart = False

        pygame.mouse.set_visible(True)
        pygame.time.Clock().tick(60)  # Limiter la boucle à 30 FPS

    pygame.time.delay(500)  # Attendre un court instant pour éviter une double détection de clic
    reset_game()

def reset_game():
    global total_game_time, enemy_deaths, current_wave

    # Réinitialiser le temps de jeu, les morts d'ennemis et la vague actuelle
    total_game_time = 0
    enemy_deaths = 0
    current_wave = 0

    # Réinitialiser la position du joueur en utilisant les coordonnées du joueur initial à partir du fichier TMX
    PLAYER_START = tmx_data.get_object_by_name("player")
    player.pos = pygame.math.Vector2(PLAYER_START.x, PLAYER_START.y)
    player.hitbox_rect.center = player.pos
    player.rect.center = player.hitbox_rect.center

    # Réinitialiser la santé du joueur
    player.health = 100


def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


##########################################

all_sprites_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
player_ui_group = pygame.sprite.Group()

PLAYER_START = tmx_data.get_object_by_name("player")
player = Player(PLAYER_START.x, PLAYER_START.y, 75, 75)
enemy = Enemy(40, 40, ENEMY_SPEED)
mouse = Mouse()

all_sprites_group.add(player, mouse)

player_ui = PlayerUI(player)
player_ui_group.add(player_ui)


while True:
    keys = pygame.key.get_pressed()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused
                pygame.mouse.set_visible(paused)

    if not paused:

        if player.health <= 0:
            game_over_screen()

        else:

            all_sprites_group.update()
            bullet_group.update()
            enemy_group.update()
            player_ui_group.update()

            if pygame.sprite.spritecollide(player, enemy_group, False):
                player.take_damage(10)


            if len(enemy_group) == 0 and not wave_in_progress:
                wave_in_progress = True
                current_wave += 1
                time_since_last_wave = 0
                enemies_to_spawn = enemies_per_wave * current_wave

                # Spawnez des ennemis pour la nouvelle vague
                for _ in range(enemies_to_spawn):
                    spawn_enemy()


            group.add(player, mouse)
            group.add(enemy_group)
            group.add(bullet_group)

            group.draw(screen)
            player_ui_group.draw(screen)
            group.center(player.rect.center)
            pygame.mouse.set_visible(False)

            Vage_text()
            Counter()
    else:

        pause_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(pause_surface, (0, 0, 0, 128), (0, 0, WIDTH, HEIGHT))
        font = pygame.font.Font(None, 36)
        text = font.render("Pause", True, (255, 255, 255))
        pause_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - text.get_height() // 2))
        screen.blit(pause_surface, (0, 0))

    pygame.display.update()
    clock.tick(FPS)

    if wave_in_progress:
        time_since_last_wave += 1 / FPS

        # Vérifiez si le temps de la vague est écoulé
        if time_since_last_wave >= time_between_waves:
            wave_in_progress = False
            time_since_last_wave = 0