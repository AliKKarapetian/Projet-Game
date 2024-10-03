# Game setup
WIDTH = 1280 #1280
HEIGHT = 720 #720
FPS = 60

# Player settings
#PLAYER_SIZE = 0.35
PLAYER_SPEED = 5
GUN_OFFSET_X = 45
GUN_OFFSET_Y = 20


ENEMY_SPEED = 1
PLAYER_SPEED = 5
PLAYER_SPEED = 5


# Bullet settings
SHOOT_COOLDOWN = 20
BULLET_SCALE = 1.4
BULLET_SPEED = 20
BULLET_LIFETIME = 750

current_wave = 0
time_since_last_wave = 0
time_between_waves = 20  # Temps en secondes entre chaque vague
enemies_per_wave = 2
wave_in_progress = False
paused = False

total_game_time = 0
enemy_deaths = 0

current_wave = 0