import pygame
import math
import random
import sys

# ========== НАСТРОЙКА ==========
WIDTH, HEIGHT = 1000, 700
FPS = 60
PLAYER_SPEED = 4
BULLET_SPEED = 12
ENEMY_SPEED = 2.2
PLAYER_HP = 100
ENEMY_HP = 50

# Түстөр
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
DARK_GREEN = (30, 120, 30)
GRAY = (60, 60, 60)
DARK_GRAY = (40, 40, 40)
YELLOW = (255, 220, 50)
BLUE = (50, 100, 220)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Counter-Strike Style")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)
big_font = pygame.font.SysFont("Arial", 48, bold=True)

# ========== КЛАССТАР ==========
class Wall:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        pygame.draw.rect(surface, DARK_GRAY, self.rect)
        pygame.draw.rect(surface, GRAY, self.rect, 2)


class Bullet:
    def __init__(self, x, y, angle, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.owner = owner  # "player" же "enemy"
        self.speed = BULLET_SPEED
        self.radius = 4
        self.alive = True

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.alive = False

    def draw(self, surface):
        color = YELLOW if self.owner == "player" else RED
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 18
        self.hp = PLAYER_HP
        self.ammo = 30
        self.max_ammo = 30
        self.reload_timer = 0
        self.shoot_cooldown = 0
        self.alive = True

    def update(self, keys, walls):
        if not self.alive:
            return

        dx, dy = 0, 0
        if keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_s]: dy += 1
        if keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_d]: dx += 1

        # Нормализация
        if dx != 0 or dy != 0:
            length = math.sqrt(dx*dx + dy*dy)
            dx /= length
            dy /= length

        new_x = self.x + dx * PLAYER_SPEED
        new_y = self.y + dy * PLAYER_SPEED

        # Дубалдар менен коллизия
        player_rect = pygame.Rect(new_x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
        can_move_x = True
        for wall in walls:
            if player_rect.colliderect(wall.rect):
                can_move_x = False
                break
        if can_move_x:
            self.x = new_x

        player_rect = pygame.Rect(self.x - self.radius, new_y - self.radius, self.radius*2, self.radius*2)
        can_move_y = True
        for wall in walls:
            if player_rect.colliderect(wall.rect):
                can_move_y = False
                break
        if can_move_y:
            self.y = new_y

        # Чектер
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.reload_timer > 0:
            self.reload_timer -= 1
            if self.reload_timer == 0:
                self.ammo = self.max_ammo

    def shoot(self, mx, my):
        if not self.alive or self.ammo <= 0 or self.shoot_cooldown > 0 or self.reload_timer > 0:
            return None
        angle = math.atan2(my - self.y, mx - self.x)
        self.ammo -= 1
        self.shoot_cooldown = 8  # атуу ылдамдыгы
        return Bullet(self.x, self.y, angle, "player")

    def reload(self):
        if self.ammo < self.max_ammo and self.reload_timer == 0:
            self.reload_timer = 90  # ~1.5 секунд

    def draw(self, surface, mx, my):
        if not self.alive:
            return
        # Дене
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius, 2)

        # Багыт (мылтык)
        angle = math.atan2(my - self.y, mx - self.x)
        end_x = self.x + math.cos(angle) * 30
        end_y = self.y + math.sin(angle) * 30
        pygame.draw.line(surface, BLACK, (self.x, self.y), (end_x, end_y), 5)


class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 16
        self.hp = ENEMY_HP
        self.shoot_cooldown = random.randint(30, 90)
        self.alive = True

    def update(self, player, walls, bullets):
        if not self.alive or not player.alive:
            return

        # Оюнчуга карай жүрүү
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist > 40:
            angle = math.atan2(dy, dx)
            new_x = self.x + math.cos(angle) * ENEMY_SPEED
            new_y = self.y + math.sin(angle) * ENEMY_SPEED

            # Жөнөкөй коллизия
            enemy_rect = pygame.Rect(new_x - self.radius, self.y - self.radius, self.radius*2, self.radius*2)
            can_x = all(not enemy_rect.colliderect(w.rect) for w in walls)
            if can_x:
                self.x = new_x

            enemy_rect = pygame.Rect(self.x - self.radius, new_y - self.radius, self.radius*2, self.radius*2)
            can_y = all(not enemy_rect.colliderect(w.rect) for w in walls)
            if can_y:
                self.y = new_y

        # Атуу
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist < 450:
            angle = math.atan2(player.y - self.y, player.x - self.x)
            # Кичине каталык
            angle += random.uniform(-0.15, 0.15)
            bullets.append(Bullet(self.x, self.y, angle, "enemy"))
            self.shoot_cooldown = random.randint(40, 80)

    def draw(self, surface):
        if not self.alive:
            return
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 2)


# ========== КАРТА ==========
def create_walls():
    walls = [
        # Сырткы дубалдар
        Wall(0, 0, WIDTH, 20),
        Wall(0, HEIGHT-20, WIDTH, 20),
        Wall(0, 0, 20, HEIGHT),
        Wall(WIDTH-20, 0, 20, HEIGHT),

        # Ички тоскоолдуктар
        Wall(200, 150, 20, 200),
        Wall(400, 100, 180, 20),
        Wall(550, 100, 20, 180),
        Wall(700, 300, 20, 250),
        Wall(300, 450, 250, 20),
        Wall(150, 500, 20, 150),
        Wall(800, 150, 150, 20),
        Wall(450, 300, 20, 120),
    ]
    return walls


# ========== НЕГИЗГИ ОЮН ==========
def main():
    player = Player(150, 350)
    walls = create_walls()
    bullets = []
    enemies = [
        Enemy(800, 150),
        Enemy(750, 500),
        Enemy(600, 200),
        Enemy(850, 350),
        Enemy(500, 550),
    ]
    score = 0
    game_over = False

    running = True
    while running:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()
        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    player.reload()
                if event.key == pygame.K_SPACE and game_over:
                    # Кайра баштоо
                    player = Player(150, 350)
                    bullets.clear()
                    enemies = [
                        Enemy(800, 150),
                        Enemy(750, 500),
                        Enemy(600, 200),
                        Enemy(850, 350),
                        Enemy(500, 550),
                    ]
                    score = 0
                    game_over = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                bullet = player.shoot(mx, my)
                if bullet:
                    bullets.append(bullet)

        if not game_over:
            player.update(keys, walls)

            for enemy in enemies:
                enemy.update(player, walls, bullets)

            # Окторду жаңыртуу
            for bullet in bullets[:]:
                bullet.update()
                if not bullet.alive:
                    bullets.remove(bullet)
                    continue

                # Дубалга тийсе
                for wall in walls:
                    if wall.rect.collidepoint(bullet.x, bullet.y):
                        bullet.alive = False
                        break

                # Оюнчуга тийсе
                if bullet.owner == "enemy" and player.alive:
                    dist = math.sqrt((bullet.x - player.x)**2 + (bullet.y - player.y)**2)
                    if dist < player.radius:
                        player.hp -= 12
                        bullet.alive = False
                        if player.hp <= 0:
                            player.alive = False
                            game_over = True

                # Душманга тийсе
                if bullet.owner == "player":
                    for enemy in enemies:
                        if enemy.alive:
                            dist = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                            if dist < enemy.radius:
                                enemy.hp -= 25
                                bullet.alive = False
                                if enemy.hp <= 0:
                                    enemy.alive = False
                                    score += 100

            # Бардык душмандар өлсө — жаңы толкун
            if all(not e.alive for e in enemies):
                enemies = [
                    Enemy(random.randint(600, 900), random.randint(100, 600)),
                    Enemy(random.randint(600, 900), random.randint(100, 600)),
                    Enemy(random.randint(500, 900), random.randint(100, 600)),
                    Enemy(random.randint(700, 950), random.randint(80, 620)),
                ]

        # ========== ЧИЙҮҮ ==========
        screen.fill((25, 30, 35))

        for wall in walls:
            wall.draw(screen)

        for bullet in bullets:
            bullet.draw(screen)

        for enemy in enemies:
            enemy.draw(screen)

        player.draw(screen, mx, my)

        # UI
        hp_text = font.render(f"HP: {max(0, player.hp)}", True, GREEN if player.hp > 30 else RED)
        ammo_text = font.render(f"Ammo: {player.ammo}" + (" (Reloading...)" if player.reload_timer > 0 else ""), True, WHITE)
        score_text = font.render(f"Score: {score}", True, YELLOW)
        screen.blit(hp_text, (30, 30))
        screen.blit(ammo_text, (30, 60))
        screen.blit(score_text, (30, 90))

        controls = font.render("WASD - Move | Mouse - Aim & Shoot | R - Reload", True, (180, 180, 180))
        screen.blit(controls, (WIDTH//2 - 220, HEIGHT - 35))

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))
            go_text = big_font.render("YOU DIED", True, RED)
            restart = font.render("Press SPACE to Restart", True, WHITE)
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 40))
            screen.blit(restart, (WIDTH//2 - restart.get_width()//2, HEIGHT//2 + 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
