import pygame
import os
import pickle
import neat
import random
pygame.init()
pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)

def load_image(name):
    return pygame.image.load(os.path.join("imgs", name))

try:
    BIRD_IMGS = [
        pygame.transform.scale2x(load_image("bird1.png")),
        pygame.transform.scale2x(load_image("bird2.png")),
        pygame.transform.scale2x(load_image("bird3.png"))
    ]
    PIPE_IMG = pygame.transform.scale2x(load_image("pipe.png"))
    BASE_IMG = pygame.transform.scale2x(load_image("base.png"))
    BG_IMG = pygame.transform.scale2x(load_image("bg.png"))
except pygame.error as e:
    print(f"Error: {e}")
    exit()

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        displacement = self.vel * self.tick_count + 1.5 * self.tick_count ** 2

        if displacement >= 16:
            displacement = 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    BASE_VEL = 5

    def __init__(self, x, difficulty_multiplier=1.0):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        
        self.VEL = self.BASE_VEL * difficulty_multiplier
        
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:  
            return True
        return False

class Base:
    BASE_VEL = 5

    def __init__(self, y, difficulty_multiplier=1.0):
        self.y = y
        self.WIDTH = BASE_IMG.get_width()
        self.IMG = BASE_IMG
        self.VEL = self.BASE_VEL * difficulty_multiplier
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def get_difficulty_multiplier(score):
    """Рассчитываем множитель сложности на основе счета"""
    base_multiplier = 1.0 + (score // 5) * 0.1
    return min(base_multiplier, 3.0)

def draw_window(win, bird, pipes, base, score, difficulty):
    win.blit(BG_IMG, (0, 0))
    
    for pipe in pipes:
        pipe.draw(win)
    
    base.draw(win)
    bird.draw(win)
    
    score_text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    
    difficulty_text = STAT_FONT.render("Speed: " + f"{difficulty:.1f}x", 1, (255, 255, 0))
    win.blit(difficulty_text, (10, 10))
    
    pygame.display.update()

def play_with_human():
    """Игра с управлением человеком"""
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - Human")
    
    clock = pygame.time.Clock()
    
    bird = Bird(230, 350)
    base = Base(FLOOR)
    pipes = [Pipe(700)]
    
    score = 0
    current_difficulty = 1.0
    run = True
    
    while run:
        clock.tick(30)
        
        new_difficulty = get_difficulty_multiplier(score)
        if new_difficulty != current_difficulty:
            current_difficulty = new_difficulty
            for pipe in pipes:
                pipe.VEL = pipe.BASE_VEL * current_difficulty
            base.VEL = base.BASE_VEL * current_difficulty
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()
        
        bird.move()
        base.move()
        
        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            
            if pipe.collide(bird):
                print(f"Game Over! Score: {score}")
                run = False
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
        
        if add_pipe:
            score += 1
            pipes.append(Pipe(WIN_WIDTH, current_difficulty))
        
        for r in rem:
            pipes.remove(r)
        
        if bird.y + bird.img.get_height() >= FLOOR or bird.y < 0:
            print(f"Game Over! Score: {score}")
            run = False
        
        draw_window(win, bird, pipes, base, score, current_difficulty)
    
    pygame.quit()

def play_with_ai():
    """Игра с ИИ"""
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - AI")
    
    clock = pygame.time.Clock()
    
    try:
        with open('winner.pkl', 'rb') as f:
            winner_genome = pickle.load(f)
    except FileNotFoundError:
        print("Файл winner.pkl не найден. Сначала обучите ИИ!")
        return
    
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                             neat.DefaultSpeciesSet, neat.DefaultStagnation,
                             config_path)
    
    net = neat.nn.FeedForwardNetwork.create(winner_genome, config)
    
    bird = Bird(230, 350)
    base = Base(FLOOR)
    pipes = [Pipe(700)]
    
    score = 0
    current_difficulty = 1.0
    run = True
    
    while run:
        clock.tick(30)
        
        new_difficulty = get_difficulty_multiplier(score)
        if new_difficulty != current_difficulty:
            current_difficulty = new_difficulty
            for pipe in pipes:
                pipe.VEL = pipe.BASE_VEL * current_difficulty
            base.VEL = base.BASE_VEL * current_difficulty
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
        
        pipe_ind = 0
        if len(pipes) > 1 and bird.x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1
            
        output = net.activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
        
        if output[0] > 0.5:
            bird.jump()
        
        bird.move()
        base.move()
        
        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            
            if pipe.collide(bird):
                print(f"AI Game Over! Score: {score}")
                run = False
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
        
        if add_pipe:
            score += 1
            pipes.append(Pipe(WIN_WIDTH, current_difficulty))
        
        for r in rem:
            pipes.remove(r)
        
        if bird.y + bird.img.get_height() >= FLOOR or bird.y < 0:
            print(f"AI Game Over! Score: {score}")
            run = False
        
        draw_window(win, bird, pipes, base, score, current_difficulty)
    
    pygame.quit()

def main_menu():
    """Главное меню"""
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    pygame.display.set_caption("Flappy Bird - Menu")
    
    run = True
    while run:
        win.blit(BG_IMG, (0, 0))
        
        title_font = pygame.font.SysFont("comicsans", 70)
        menu_font = pygame.font.SysFont("comicsans", 50)
        
        title = title_font.render("FLAPPY BIRD", 1, (255, 255, 255))
        option1 = menu_font.render("1. Play Human", 1, (255, 255, 255))
        option2 = menu_font.render("2. Play AI", 1, (255, 255, 255))
        option3 = menu_font.render("3. Train AI", 1, (255, 255, 255))
        
        win.blit(title, (WIN_WIDTH/2 - title.get_width()/2, 150))
        win.blit(option1, (WIN_WIDTH/2 - option1.get_width()/2, 250))
        win.blit(option2, (WIN_WIDTH/2 - option2.get_width()/2, 320))
        win.blit(option3, (WIN_WIDTH/2 - option3.get_width()/2, 390))
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    play_with_human()
                    return
                elif event.key == pygame.K_2:
                    play_with_ai()
                    return
                elif event.key == pygame.K_3:
                    local_dir = os.path.dirname(__file__)
                    config_path = os.path.join(local_dir, 'config-feedforward.txt')
                    import flappy_bird_neat
                    flappy_bird_neat.run(config_path)
                    return
    
    pygame.quit()

if __name__ == "__main__":
    main_menu()