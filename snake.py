#!/usr/bin/env python3
import pygame
from random import randrange
import math
HEIGHT = 480
WIDTH = 640
RADIUS = 10
REFRESH_RATE = 60

class Vector():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def dot_prod(self, other):
        return self.x * other.x + self.y * other.y

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        return Vector(self.x/self.length(), self.y/self.length())

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"

    def __iter__(self):
        yield self.x
        yield self.y

    def __add__(self, shift):
        return Vector(self.x + shift.x, self.y + shift.y)

    def __sub__(self, shift):
        return Vector(self.x - shift.x, self.y - shift.y)

    def __mul__(self, scalar_or_vector):
        if isinstance(scalar_or_vector, Vector):
            vector = scalar_or_vector
            return self.dot_prod(vector)
        else:
            scalar = scalar_or_vector
            return Vector(self.x * scalar, self.y * scalar)

class SnakePart():
    def __init__(self, color, position, vector):
        self.color = color
        self.position = position
        self.vector = vector

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, tuple(self.position), RADIUS)

    def draw_head(self, screen):
        eye_vec = Vector(-self.vector.y, self.vector.x).normalize() * (RADIUS/2.5)
        pygame.draw.circle(screen, self.color, tuple(self.position), RADIUS)
        pygame.draw.circle(screen, "black", tuple(self.position + eye_vec), 1)
        pygame.draw.circle(screen, "black", tuple(self.position - eye_vec), 1)

class Snake():
    @property
    def head(self):
        return self.body[-1]

    def __init__(self, size, colors):
        self.body = [ SnakePart(
            colors[i%len(colors)],
            Vector(WIDTH//2 + i, HEIGHT//2), 
            Vector(1,0)
        ) for i in range(size)]
        self.colors = colors
        self.rotation_rate = 0.1

    def draw(self, screen):
        for part in self.body:
            part.draw(screen)
        self.head.draw_head(screen)

    def move(self, direction):
        tail = self.body[:-1]
        for i in range(len(tail)):
            self.body[i].position += self.body[i].vector
            self.body[i].vector = self.body[i+1].position - self.body[i].position

        self.head.position += self.head.vector

        ## in case it don't normailized
        direction = direction.normalize()
        ## in case that angle biger than 90 degrees
        if self.head.vector * direction < 0:
            dX, dY = tuple(direction)
            ## direction rotated counter clockwise by 90 degrees
            direction = Vector(-dY, dX)
            ## original direction was counter clockwise
            if direction * self.head.vector < 0:
                direction = Vector(-self.head.vector.y, self.head.vector.x)
            else:
                direction = Vector(self.head.vector.y, -self.head.vector.x)

        ## now direction normalized and angle is less than 90 degrees
        penpendicular = Vector(-self.head.vector.y, self.head.vector.x)
        rotation = penpendicular * (direction * penpendicular)
        self.head.vector += rotation * self.rotation_rate
        self.head.vector = self.head.vector.normalize()
        ### TODO: understang how i managed to accelerate before
        # self.head.vector += Vector(rotation.x/20, rotation.y/20)

    def self_collision(self):
        tail = self.body[:-1]
        for part in tail:
            if (part.position - self.head.position).length() < 1:
                return part
        return None

    def increase(self, size):
        self.body = [SnakePart(self.colors[i%len(self.colors)], self.body[0].position, Vector(0,0)) for i in range(size) ] + self.body

    def __iter__(self):
        for part in self.body:
            yield part

    def __getitem__(self, index):
        return self.body[index]

    def __len__(self):
        return len(self.body)

class FoodProvider():
    def __init__(self, config):
        self.config = config

    def get_food(self):
        config = self.config
        #return Vector(WIDTH//2+250, HEIGHT//2+50) # XXX: old cheese
        return Vector(
            randrange(config["snake_radius"], config["width"]-config["snake_radius"]), 
            randrange(config["snake_radius"], config["height"]-config["snake_radius"]))

class SnakeController():
    def get_direction(self, game):
        snake = game.snake
        mX, mY = pygame.mouse.get_pos()
        dX = mX - snake.head.position.x
        dY = mY - snake.head.position.y
        direction = Vector(dX, dY)
        return direction

class SnakeGame():
    def __init__(self, screen, snake, controller, fp, config):
        self.screen = screen
        self.snake = snake
        self.controller = controller
        self.feeder = fp.get_food
        self.config = config

        self.finished = False
        self.score = 0
        self.food = self.feeder()

    def tick(self, delta_t):
        if not self.finished:
            if self.screen:
                pygame.draw.circle(
                        self.screen,self.config["food_color"],tuple(self.food), self.config["food_radius"])
                self.snake.draw(self.screen)

            direction = self.controller.get_direction(self)
            self.snake.move(direction)

            if (self.snake.head.position - self.food).length() < self.config["snake_radius"]/2:
                self.eat_food()
            
            if self.snake.self_collision():
                self.finished = True
                if self.screen:
                    pygame.draw.circle(self.screen, "blue", (50, 50), self.config["snake_radius"])
                #print(f"Game finished due to self collision. score: {self.score}")

            if  (self.snake.head.position.x < 0 or 
                    self.snake.head.position.x > self.config["width"] or
                    self.snake.head.position.y < 0 or
                    self.snake.head.position.y > self.config["height"]):
                if self.screen:
                    pygame.draw.circle(self.screen, "red", (50, 50), self.config["snake_radius"])
                self.finished = True
                #print(f"Game finished due to wall collision. score: {self.score}")

        return self.score

    def eat_food(self):
        self.score += 5
        config = self.config
        self.food = self.feeder()
        self.snake.increase(5);

if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Snake!")
    ctrl = SnakeController()
    snakeColors = ["red", "red", "red", "orange"]
    config = {
            "height": HEIGHT,
            "width": WIDTH,
            "snake_radius": RADIUS,
            "food_radius": RADIUS/1.5,
            "food_color": "green"
        }
    fp = FoodProvider(config)
    game = SnakeGame(screen, Snake(30, snakeColors), ctrl, fp, config)

    clock = pygame.time.Clock()
    while True:
        delta_t = clock.tick(REFRESH_RATE)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            exit()
        screen.fill((255, 200, 200))

        score = game.tick(delta_t)
        pygame.display.set_caption(f"Snake! score: {score}")

        pygame.display.update()
