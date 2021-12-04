import pygame
import os
import random

pygame.init()
pygame.font.init()

WIDTH, HEIGHT = 1000, 1000  # resolution
FPS = 60  # frame rate
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# Load images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_red_small.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_green_small.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets", "pixel_ship_blue_small.png"))

# Player ship
YELLOW_SPACE_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "pixel_ship_yellow.png")), (50, 50))

# Lasers
RED_LASER = pygame.transform.scale(pygame.image.load(os.path.join("assets", "pixel_laser_red.png")), (50, 60))
GREEN_LASER = pygame.transform.scale(pygame.image.load(os.path.join("assets", "pixel_laser_green.png")), (50, 60))
BLUE_LASER = pygame.transform.scale(pygame.image.load(os.path.join("assets", "pixel_laser_blue.png")), (50, 60))
YELLOW_LASER = pygame.transform.scale(pygame.image.load(os.path.join("assets", "pixel_laser_yellow.png")), (50, 60))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets", "background-black.png")), (WIDTH, HEIGHT))

# SFX
LASER_SFX = pygame.mixer.Sound(os.path.join("assets", "laser.wav"))


class Laser:
    def __init__(self, x, y, img, enemy):
        self.x = x
        self.y = y
        self.img = img
        self.enemy = enemy
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move_laser(self, vel, player=None, enemies=None):
        if not self.enemy and enemies is not None:
            return self.move_player_laser(vel, enemies)
        elif player is not None:
            return self.move_enemy_laser(vel, player)

        return -1

    # return 0 if no collision, 1 if offscreen, 2 if enemy collision
    def move_player_laser(self, vel, objs):
        self.y -= vel

        if self.off_screen(HEIGHT):  # remove laser if offscreen
            return 1
        else:  # remove laser if collides with enemy and destroy it
            for obj in objs:
                if self.collision(obj):
                    objs.remove(obj)
                    return 2

        return 0

    # return 0 if no collision, 1 if offscreen, 2 if player collision
    def move_enemy_laser(self, vel, player_obj):
        self.y += vel

        if self.off_screen(HEIGHT):  # remove laser if offscreen
            return 1
        elif self.collision(player_obj):  # remove laser if collides with player and decrement hp
            player_obj.health -= 10
            return 2

        return 0

    def off_screen(self, height):
        return not height >= self.y >= 0

    def collision(self, obj):
        return collide(self, obj)


class Ship:

    def __init__(self, x, y, health=100, cooldown_time=30):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.cooldown_time = cooldown_time
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))

    def cooldown(self):
        if self.cool_down_counter >= self.cooldown_time:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1

    # return 0 if no laser is ready to fire or 1 if it is ready to fire
    def shoot(self):
        if self.cool_down_counter == 0:
            self.cool_down_counter = 1
            return 1
        else:
            return 0

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=1, cooldown=30):
        super().__init__(x, y, health, cooldown)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def healthbar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y + self.ship_img.get_height() + 10,
                                               self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y + self.ship_img.get_height() + 10,
                                               self.ship_img.get_width() * (self.health / self.max_health), 10))

    # return 0 if no laser is ready to fire or 1 if it is ready to fire
    def shoot(self):
        if self.cool_down_counter == 0:
            self.cool_down_counter = 1
            pygame.mixer.Sound.play(LASER_SFX)
            return 1
        else:
            return 0

    def draw(self, window):
        super().draw(window)
        #self.healthbar(window)


class Enemy(Ship):
    COLOR_MAP = {
        "red": (RED_SPACE_SHIP, RED_LASER),
        "green": (GREEN_SPACE_SHIP, GREEN_LASER),
        "blue": (BLUE_SPACE_SHIP, BLUE_LASER)
    }

    def __init__(self, x, y, color, health=100):
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    # return 1 if the enemy will collide with the edge of the screen
    def move(self, velx, vely):
        self.x += velx
        self.y += vely

        if self.x + velx + self.get_width() >= WIDTH:
            return 1
        else:
            return 0

    def edge_collide(self, vel, left):
        if not left and self.x + vel + self.get_width() >= WIDTH:  # collide with edge while moving right
            return 1
        elif left and self.x - vel <= 0:  # collide with edge while moving left
            return 1
        else:
            return 0


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def game_main(difficulty):
    run = True
    level = 0
    lives = 3

    score = 0
    hiscore = 0
    try:
        if os.path.exists(os.path.join("hi-score.txt")):
            hiscore_file = open("hi-score.txt", "r")
            hiscore = int(hiscore_file.readline())
    except:
        print("Hi-Score file could not be read.")

    main_font = pygame.font.SysFont("arial", 50)
    start_font = pygame.font.SysFont("arial", 60)
    lost_font = pygame.font.SysFont("arial", 60)

    # difficulty parameters (easy, normal, hard)
    laser_vels = [5, 8, 10]
    enemy_vels = [1, 3, 6]
    cooldowns = [30, 15, 10]
    enemy_fire_probs = [25, 15, 10]

    enemy_col = 10  # number of invaders per row
    enemy_velx = enemy_vels[difficulty]  # how fast enemies shuffle horizontally
    enemy_vely = 50  # how far enemies fall down
    enemy_fire_prob = enemy_fire_probs[difficulty]  # probability of enemies firing. higher number means less likely
    moving_left = False

    player_vel = 5
    laser_vel = laser_vels[difficulty]

    player = Player(WIDTH/2 - YELLOW_SPACE_SHIP.get_width()/2, 825, cooldown=cooldowns[difficulty])
    enemies = []
    lasers = []

    clock = pygame.time.Clock()

    start = True
    start_count = 0
    lost = False
    lost_count = 0

    def redraw_window():
        # draw background
        WIN.blit(BG, (0, 0))

        # text objects
        lives_label = main_font.render(f"Lives: {lives}", 1, (255, 255, 255))
        level_label = main_font.render(f"Level: {level}", 1, (255, 255, 255))
        score_label = main_font.render(f"Score: {score}", 1, (255, 255, 255))
        hiscore_label = main_font.render(f"Hi-Score: {hiscore}", 1, (255, 255, 255))

        # draw text to screen
        WIN.blit(lives_label, (10, HEIGHT - 10 - lives_label.get_height()))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, HEIGHT - 10 - level_label.get_height()))
        WIN.blit(score_label, (10, 10))
        WIN.blit(hiscore_label, (WIDTH - hiscore_label.get_width() - 10, 10))
        pygame.draw.rect(WIN, (255, 255, 255), (0, HEIGHT - 25 - lives_label.get_height(), WIDTH, 3))

        # redraw player, enemy, and laser sprites
        player.draw(WIN)

        for enemy_sprite in enemies:
            enemy_sprite.draw(WIN)

        for laser_sprite in lasers:
            laser_sprite.draw(WIN)

        # display start message at game beginning
        if start:
            start_label = start_font.render("Start", 1, (255, 255, 255))
            WIN.blit(start_label, (WIDTH / 2 - start_label.get_width() / 2, 350))

        # display game over message if player loses
        if lost:
            lost_label = lost_font.render("Game Over", 1, (255, 255, 255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width() / 2, 350))

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if player.health <= 0:
            if lives > 0:
                lives -= 1

            if lives <= 0:  # game over
                lost = True
                lost_count += 1

                # save hi-score in text file
                try:
                    if score > hiscore:
                        new_score_file = open("hi-score.txt", 'w')
                        new_score_file.write(str(score))
                        new_score_file.write('\n')
                        new_score_file.close()
                except:
                    print("Hi-Score file could not be written.")
            else:  # player loses a life and respawns
                player = Player(WIDTH/2 - YELLOW_SPACE_SHIP.get_width()/2, 825, cooldown=cooldowns[difficulty])
                # remove enemy lasers
                for alaser in lasers[:]:
                    if alaser.enemy:
                        if alaser in lasers:
                            lasers.remove(alaser)

        # display start msg for 2 seconds
        if start:
            if start_count > FPS * 2:
                start = False
            else:
                start_count += 1
                continue

        # display game over msg for 3 seconds
        if lost:
            if lost_count > FPS * 3:
                main_menu()
            else:
                continue

        # spawn enemies for new round
        if len(enemies) == 0:
            level += 1

            # place top enemies
            for i in range(enemy_col):
                # enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                #              random.choice(["red", "blue", "green"]))
                enemy = Enemy(10 + 60 * i, 70, "blue")
                enemies.append(enemy)

            # place middle enemies
            for i in range(enemy_col):
                # enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                #              random.choice(["red", "blue", "green"]))
                enemy = Enemy(60 * i, 120, "green")
                enemies.append(enemy)

            # place middle enemies
            for i in range(enemy_col):
                # enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                #              random.choice(["red", "blue", "green"]))
                enemy = Enemy(60 * i, 170, "green")
                enemies.append(enemy)

            # place bottom enemies
            for i in range(enemy_col):
                # enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                #              random.choice(["red", "blue", "green"]))
                enemy = Enemy(60 * i, 220, "red")
                enemies.append(enemy)

            # place bottom enemies
            for i in range(enemy_col):
                # enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100),
                #              random.choice(["red", "blue", "green"]))
                enemy = Enemy(60 * i, 270, "red")
                enemies.append(enemy)

        for event in pygame.event.get():
            # quit pygame if needed
            if event.type == pygame.QUIT:
                quit()

        keys = pygame.key.get_pressed()
        # move left
        if keys[pygame.K_a] and player.x - player_vel > 0:
            player.x -= player_vel
        elif keys[pygame.K_LEFT] and player.x - player_vel > 0:
            player.x -= player_vel

        # move right
        if keys[pygame.K_d] and player.x + player_vel + player.get_width() < WIDTH:
            player.x += player_vel
        elif keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH:
            player.x += player_vel

        # # move up
        # if keys[pygame.K_w] and player.y - player_vel > 0:
        #     player.y -= player_vel
        # elif keys[pygame.K_UP] and player.y - player_vel > 0:
        #     player.y -= player_vel
        #
        # # move down
        # if keys[pygame.K_s] and player.y + player_vel + player.get_height() + 15 < HEIGHT:
        #     player.y += player_vel
        # elif keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() + 15 < HEIGHT:
        #     player.y += player_vel

        # shoot laser
        if keys[pygame.K_SPACE]:
            if player.shoot():
                player_laser = Laser(player.x, player.y, player.laser_img, False)
                lasers.append(player_laser)

        # check if the enemies need to all be shuffled down
        move_down = False
        for enemy in enemies[:]:
            if enemy.edge_collide(enemy_velx, moving_left):
                move_down = True
                moving_left = not moving_left
                break

        for enemy in enemies[:]:
            if move_down:
                if not moving_left:
                    enemy.move(enemy_velx, enemy_vely)
                else:
                    enemy.move(-enemy_velx, enemy_vely)
            else:
                if not moving_left:
                    enemy.move(enemy_velx, 0)
                else:
                    enemy.move(-enemy_velx, 0)
            enemy.cooldown()

            if random.randrange(0, enemy_fire_prob * FPS) == 1:
                if enemy.shoot():
                    enemy_laser = Laser(enemy.x - 10, enemy.y, enemy.laser_img, True)
                    lasers.append(enemy_laser)

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > player.y:  # game over if enemies reach bottom of the screen
                lives = 0
                player.health = 0
                enemies.remove(enemy)

        player.cooldown()

        # move all lasers and check collisions
        for laser in lasers[:]:
            if laser.enemy:
                laser_collide = laser.move_laser(laser_vel, player=player)
                if laser_collide:
                    lasers.remove(laser)
            else:
                laser_collide = laser.move_laser(laser_vel, enemies=enemies)
                if laser_collide:
                    lasers.remove(laser)
                    if laser_collide == 2:
                        score += 10


def main_menu():
    clock = pygame.time.Clock()
    click = False
    difficulty = ["Difficulty: Easy", "Difficulty: Normal", "Difficulty: Hard"]
    diff_i = 0

    while True:
        clock.tick(FPS)
        WIN.blit(BG, (0, 0))

        mx, my = pygame.mouse.get_pos()

        text_color1 = (255, 255, 255)
        text_color2 = (255, 255, 255)
        text_color3 = (255, 255, 255)

        button_1 = pygame.Rect(250, 250, 500, 100)
        button_2 = pygame.Rect(250, 500, 500, 100)
        button_3 = pygame.Rect(250, 750, 500, 100)
        # check if menu items were pressed
        if button_1.collidepoint((mx, my)):
            text_color1 = (255, 232, 31)
            if click:
                game_main(diff_i)
        if button_2.collidepoint((mx, my)):
            text_color2 = (255, 232, 31)
            # change difficulty between easy, medium, hard
            if click:
                if diff_i == 2:
                    diff_i = 0
                else:
                    diff_i += 1
        if button_3.collidepoint((mx, my)):
            text_color3 = (255, 232, 31)
            if click:
                pygame.quit()

        pygame.draw.rect(WIN, (19, 17, 17), button_1)
        pygame.draw.rect(WIN, (19, 17, 17), button_2)
        pygame.draw.rect(WIN, (19, 17, 17), button_3)

        # display title
        title_font = pygame.font.SysFont("bauhaus 93", 85)
        title_label = title_font.render("Space Invaders", 1, (255, 255, 255))
        WIN.blit(title_label, ((WIDTH / 2 - title_label.get_width() / 2), 60))

        # display menu text labels
        menu_font = pygame.font.SysFont("arial", 50)
        play_label = menu_font.render("Start", 1, text_color1)
        WIN.blit(play_label, ((WIDTH / 2 - play_label.get_width() / 2), 250 + play_label.get_height()/2))
        diff_label = menu_font.render(difficulty[diff_i], 1, text_color2)
        WIN.blit(diff_label, ((WIDTH / 2 - diff_label.get_width() / 2), 500 + diff_label.get_height() / 2))
        exit_label = menu_font.render("Exit", 1, text_color3)
        WIN.blit(exit_label, ((WIDTH / 2 - exit_label.get_width() / 2), 750 + exit_label.get_height() / 2))

        click = False
        # check for mouse clicks or exiting the game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

        pygame.display.update()


main_menu()
