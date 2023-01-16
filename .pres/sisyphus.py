#!/usr/bin/env python3
import pygame
import math
from random import randrange
from random import choice as randchoice
from snake import Vector
from snake import SnakePart, Snake
from snake import SnakeController, FoodProvider, SnakeGame

HEIGHT = 480
WIDTH = 640
RADIUS = 10
REFRESH_RATE = 120
EPSILON = 0.01
LEARNING_RATE = 0.01
MUTATION_ARR = [1] + [0 for i in range(50)]


adam = [
        [-0.5, -0.1, 0, 0.1, 0.5],
        [ [1, 0.5, 1, 0], [0, 1, 0.5, 1] ],
        [[ -0.5, 0.5]]
    ]
def get_random_network(shape):
    return adam
    E = shape[0]//2
    net = []
    eyes = [ p/E for p in range(-E, E+1)]
    net.append(eyes)
    for i in range(1, len(shape)):
        layer = [ [ randrange(-10, 10) for neuron in net[-1] ] for size in range(shape[i])]
        net.append(layer)
    return net

def modify_network(network):
    return adam
    # eyes unchanged
    new_net = [network[0]]
    for layer in network[1:]:
        new_layer = [ 
                [ weight + LEARNING_RATE * randrange(-3, 3) * randchoice(MUTATION_ARR) for weight in neuron ] 
            for neuron in layer ]
        new_net.append(new_layer)
    return new_net

class SequentialFoodProvider(FoodProvider):
    def __init__(self, config, seq):
        self.config = config
        self.seq = seq
        self.feeder = self.__food_gen()

    def __food_gen(self):
        for e in self.seq:
            yield e

    def get_food(self):
        return next(self.feeder)

class RaycastSnakeGame(SnakeGame):
    def raycast(self, position, direction):
        direction = direction.normalize()
        ## FIXME: distance is rounded up in a ugly way
        ## cast to food
        to_food = self.food - position
        cosinus = direction * to_food.normalize()
        if cosinus > 0:
            angle = math.acos(cosinus)
            if (to_food * math.sin(angle)).length() - self.config["food_radius"] < EPSILON:
                return to_food.length() * cosinus

        ## cast to tail
        to_tail = [ part.position - position for part in self.snake[:-1] ]
        cosinus, vec = max( [ (direction * vec.normalize(), vec) for vec in to_tail ], key=lambda x: x[0] )
        if cosinus > 0:
            angle = math.acos(cosinus)
            if (vec * math.sin(angle)).length() - self.config["snake_radius"] < EPSILON:
                return vec.length() * cosinus

        ## direction is into wall
        pX, pY = tuple(position)
        dX, dY = tuple(direction)
        wX = 640 if dX > 0 else 0
        wY = 480 if dY > 0 else 0
        sc = -1 if dX * dY == 0 else dX*dY / math.fabs(dX*dY)
        vX = vY = 0

        if ( Vector(wX, wY) - position ) * Vector(-dY, dX) * sc > 0:
            vX, vY = 0, 1
        else:
            vX, vY = 1, 0

        ## Was used to check wall selection
        #return f"({wX}, {wY}) -> ({vX}, {vY}) "

        n = Vector(-vY, vX)
        dd = n * (position - Vector(wX, wY))
        cosinus = direction * n
        return math.fabs(dd / cosinus)

class NeuroController(SnakeController):
    def __init__(self, network):
        self.network = network

    def get_direction(self, game):
        d = game.snake.head.vector.normalize()
        alphas = [ k * math.pi / 2 for k in self.network[0]]
        vectors = [Vector(
            d*Vector(math.cos(alpha), -math.sin(alpha)),
            d*Vector(math.sin(alpha),  math.cos(alpha)))
        for alpha in alphas]

        inputs = [game.raycast(game.snake.head.position, vector) for vector in vectors]
        ans = self.network_solve(inputs)
        alpha = ans * math.pi / 2
        ret = Vector(
                d*Vector(math.cos(alpha), -math.sin(alpha)),
                d*Vector(math.sin(alpha),  math.cos(alpha))
            )
        return ret.normalize()

    def network_solve(self, inputs):
        activation = self.activation
        results = inputs
        for layer in self.network[1:]:
            results = [activation(sum([results[i] * neuron[i] for i in range(len(neuron))])) for neuron in layer]
        return results[0]
    
    def activation(self, x):
        return x
        return math.tanh(x)

if __name__ == "__main__":
    colorPairs = [ ("red", "orange"), ("forestgreen", "yellow"), ("blue", "white"), ("purple", "violet"),
                  ("brown", "crimson"), ("darkorange", "cyan"), ("tomato", "fuchsia"), ("gold", "grey"),
                  ("crimson", "darkmagenta"), ("yellow", "blue")]
    snakeColorsVariants = [ [primar, primar, primar, second] for primar, second in colorPairs ]
    manyVariants = []
    for i in range(1):
        manyVariants += snakeColorsVariants
    colored_snakes = [(colors[-1], Snake(30, colors)) for colors in snakeColorsVariants ]
    shape = [10, 5, 1]
    #ctrl = SnakeController()
    config = {
            "height": HEIGHT,
            "width": WIDTH,
            "snake_radius": RADIUS,
            "food_radius": RADIUS/1.5,
        }
    food_seq = [
        Vector(
            randrange(config["snake_radius"], config["width"]-config["snake_radius"]), 
            randrange(config["snake_radius"], config["height"]-config["snake_radius"])
        ) for i in range(10) ]

    clock = pygame.time.Clock()
    start_t = pygame.time.get_ticks()
    finished = []

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Snake!")
    games = [RaycastSnakeGame(screen, snake,
                              NeuroController(get_random_network(shape)),
                              SequentialFoodProvider(config, food_seq),
                              {**config, "food_color": color})
                              for color, snake in colored_snakes]
    ## action!
    start_t = pygame.time.get_ticks()
    while True:
        delta_t = clock.tick(REFRESH_RATE)
        for event in pygame.event.get():
          if event.type == pygame.QUIT:
            exit()
        screen.fill((255, 200, 200))

        if len(games) > 0: 
            for game in games:
                game.tick(delta_t)
                if game.finished:
                    finished.append( (game, pygame.time.get_ticks() - start_t ) )
                    games.remove(game)
        else:
            ## Instead of fitness function
            bests = sorted(finished, reverse=True,
                key=lambda pair: (pair[0].score, pair[1] ))[:1] # GA control
            bests = sorted(finished, reverse=True,
                key=lambda pair: (pair[1]) )[:1] # Lifespan only
            print("Winner is: ", bests[0][0].snake.colors, bests[0][0].score, bests[0][1])
            best_networks = [best[0].controller.network for best in bests]
            colored_snakes = [(colors[-1], Snake(30, colors)) for colors in manyVariants ]
            games = [RaycastSnakeGame(screen, snake,
                                      NeuroController(modify_network(best_networks[0])),
                                      SequentialFoodProvider(config, food_seq),
                                      {**config, "food_color": color})
                                      for color, snake in colored_snakes]
            finished = []
            start_t = pygame.time.get_ticks()


        pygame.display.update()
