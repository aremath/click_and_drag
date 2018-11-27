import pygame
import math
from enum import Enum
from pygame.math import Vector2 as Vec

screen_width = 720
screen_height = 720
border_width = 20

grace_distance = 4
default_size = 8

bg_color = (76, 76, 76)
edible_color = (255, 255, 255)
clickable_color = (0, 0, 0)
missile_color = (120, 120, 120)
missile_explosion_color = (200, 0, 0)
player_color = (0,0,255)
border_color = (0, 0, 0)

friction = 0.1

default_player_mass = 15

missile_radius = 4
missile_prox = 50
missile_explosion_radius = 15
missile_max_speed = 45
missile_homingness = 3

FPS = 60


def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((screen_width, screen_height))
    background = pygame.Surface(screen.get_size())
    background.fill(bg_color)
    background.convert()
    running = True

    entities = []
    edibles = []
    clickables = []

    player = Player(entities, 300, 300)
    e = Edible(entities, edibles, 100, 100)
    c = Clickable(entities, clickables, 200, 200)
    m = Missile(player, entities, 225, 200)
    b1 = Border(entities, screen_width/2, border_width/2, screen_width, border_width)
    b2 = Border(entities, border_width/2, screen_height/2, border_width, screen_height)
    b3 = Border(entities, screen_width/2, screen_height-border_width/2, screen_width, border_width)
    b4 = Border(entities, screen_width-border_width/2, screen_height/2, border_width, screen_height)

    while running:
        # restart if the player has eaten everything
        if len(edibles) == 0:
            reset()
        time = clock.tick(FPS) # get the time passed since the last frame (in milliseconds)
        dt = time/1000
        # blit the background
        screen.blit(background, (0, 0))
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = Vec(pygame.mouse.get_pos())
                for c in clickables:
                    if pos.distance_to(c.pos) < c.xsize + grace_distance:
                        player.target = c
                        c.is_clicked = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if player.target is not None:
                    player.target.is_clicked = False
                    player.target = None

        for entity in entities:
            entity.update(dt, entities)

        # Kill all entities scheduled for destruction
        entities = [e for e in entities if not e.sfd]

        for entity in entities:
            entity.draw(screen)

        pygame.display.update()

def mk_rect_surface(xsize, ysize, color):
    s = pygame.Surface((xsize, ysize))
    pygame.draw.rect(s, color, (0,0,xsize,ysize))
    s.convert()
    return s

def mk_square_surface(size, color):
    return mk_rect_surface(size, size, color)

def rect_overlap(r1, r2):
    # Is one rectangle to the left of the other?
    if r1[0][0] > r2[1][0] or r2[0][0] > r1[1][0]:
        return False
    # Is one rectangle above the other?
    elif r1[0][1] > r2[1][1] or r2[0][1] > r1[1][1]:
        return False
    else:
        return True

def get_dist(e1, e2):
    return e1.pos.distance_to(e2.pos)

def vec_from(e1, e2):
    return e2.pos - e1.pos

def unit_vec_from(e1, e2):
    return vec_from(e1, e2).normalize()

def draw_line(screen, p1, p2, color):
    # TODO: this is lazy blitting
    lsurface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA, 32)
    pygame.draw.line(lsurface, color, p1, p2)
    lsurface.convert_alpha()
    screen.blit(lsurface, (0,0))

class Entity(object):
    
    def __init__(self, entities, xpos, ypos, xsize=default_size, ysize=default_size):
        self.pos = Vec(xpos, ypos)
        self.xsize = xsize
        self.ysize = ysize
        self.size_v = Vec(self.xsize/2, self.ysize/2)
        self.center = (int(self.xsize/2), int(self.ysize/2))
        entities.append(self)
        self._surface = None
        self.sfd = False

    def update(self, time, entities):
        pass

    def draw(self, screen):
        screen.blit(self._surface, self.pos - self.size_v)

    def get_bbox(self):
        return (self.pos - self.size_v, self.pos + self.size_v)

class Border(Entity):
    
    def __init__(self, entities, xpos, ypos, xsize, ysize):
        super().__init__(entities, xpos, ypos, xsize, ysize)
        # drawing surface
        self._surface = mk_rect_surface(self.xsize, self.ysize, border_color)

    def update(self, time, entities):
        for e in entities:
            # Kill killable entities that overlap
            if hasattr(e, "die"):
                if rect_overlap(self.get_bbox(), e.get_bbox()):
                    e.die("Shattered to pieces against a wall")

    def draw(self, screen):
        super().draw(screen)

class Edible(Entity):

    def __init__(self, entities, edibles, xpos, ypos):
        super().__init__(entities, xpos, ypos)
        edibles.append(self)
        # drawing surface
        self._surface = mk_square_surface(self.xsize, edible_color)

    def update(self, time, entities):
        pass

    def eat(self):
        print("EAT")
        self.sfd = True

    def draw(self, screen):
        super().draw(screen)

class Clickable(Entity):

    def __init__(self, entities, clickables, xpos, ypos):
        super().__init__(entities, xpos, ypos)
        self.is_clicked = False
        clickables.append(self)
        # drawing surface
        self._surface = mk_square_surface(self.xsize, clickable_color)

    def update(self, time, entities):
        pass

    def draw(self, screen):
        super().draw(screen)

class Player(Entity):

    def __init__(self, entities, xpos, ypos):
        super().__init__(entities, xpos, ypos)
        self.target = None
        self.a = Vec(0, 0)
        self.v = Vec(0, 0)
        self.score = 0
        self.mass = default_player_mass
        # drawing surface
        self._surface = mk_square_surface(self.xsize, player_color)

    def die(self, msg):
        print(msg)
        self.a = Vec(0, 0)
        self.v = Vec(0, 0)
        reset()
        #TODO

    def update(self, time, entities):
        # Physics
        if self.target is not None:
            to_target = vec_from(self, self.target)
            da = math.exp(-1/(to_target.length()))
            to_target.scale_to_length(da)
            self.a += to_target
        else:
            self.a -= self.a * friction
        self.v += self.a
        self.pos += self.v * time

        # Eat entities
        for e in entities:
            if hasattr(e, "eat"):
                if rect_overlap(self.get_bbox(), e.get_bbox()):
                    e.eat()
                    self.score += 1

    #TODO: player shadows
    def draw(self, screen):
        # Draw the line between here and the target
        if self.target is not None:
            draw_line(screen, self.pos, self.target.pos, (0,0,0))
        super().draw(screen)

class MissileState(Enum):
    WAITING = 1
    TARGETING = 2
    EXPLODING = 3

class Missile(Entity):
    
    def __init__(self, player, entities, xpos, ypos):
        super().__init__(entities, xpos, ypos, 2*missile_prox, 2*missile_prox)
        self.mode = MissileState.WAITING
        self.mode_counter = 0
        self.target = player
        self.a = Vec(0, 0)
        self.v = Vec(0, 0)
        self.prox = missile_prox
        self.explosion_radius = missile_explosion_radius
        self.max_speed = missile_max_speed
        self.sfd = False
        # Drawing surface
        self._surface = pygame.Surface((self.xsize, self.ysize), pygame.SRCALPHA, 32)
        pygame.draw.circle(self._surface, missile_color, self.center, missile_radius)
        pygame.draw.circle(self._surface, missile_color, self.center, missile_prox, 1)
        self._surface.convert_alpha()

    def get_bbox(self):
        return (self.pos - (missile_radius, missile_radius), self.pos + (missile_radius, missile_radius))

    def update(self, time, entities):
        if (self.mode == MissileState.WAITING):
            # Trigger if the player is close
            if get_dist(self, self.target) < self.prox:
                self.mode = MissileState.TARGETING
            # Trigger if the player clicks on something close
            elif self.target.target is not None:
                if get_dist(self, self.target.target) < self.prox:
                    self.mode = MissileState.TARGETING
                    #TODO: change surface to only the circle
        elif (self.mode == MissileState.TARGETING):
            # TODO: collision with interactibles
            # TODO: collision with player
            # Accelerate towards the player
            da = vec_from(self, self.target)
            da += self.target.v * time
            da = da.normalize()
            da *= missile_homingness
            self.a = da
        elif (self.mode == MissileState.EXPLODING):
            # TODO: lower velocity
            self.mode_counter += 1
            # 10 frames of missile explosion
            # TODO: time-based?
            if self.mode_counter == 10:
                self.sfd = True
            if get_dist(self, self.target) < missile_explosion_radius:
                self.target.die("Blown up by a missile.")

        # Physics
        self.v += self.a
        if self.v.length() > missile_max_speed:
            self.v.scale_to_length(missile_max_speed)
        self.pos += self.v * time

    def draw(self, screen):
        if self.target is not None and self.mode == MissileState.TARGETING:
            draw_line(screen, self.pos, self.target.pos, missile_explosion_color)
        super().draw(screen)

    def die(self, msg):
        pass

if __name__=="__main__":
    main()

