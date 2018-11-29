import pygame
import math
import random
from enum import Enum
from pygame.math import Vector2 as Vec

screen_width = 720
screen_height = 720
border_width = 20

grace_distance = 5
default_size = 12

bg_color = (80, 80, 80)
edible_color = (255, 255, 255)
clickable_color = (200, 0, 0)
interactible_color = (200, 100, 0)
missile_color = (120, 120, 120)
missile_explosion_color = (200, 0, 0)
player_color = (0,25,255)
border_color = (0, 0, 0)
gravitywell_color = (0,200,200)

# Player Settings
# Lower is less friction
friction = 0.001
player_mass = 4
player_pull = 6

# Missile Settings
missile_radius = 4
missile_prox = 50
missile_explosion_radius = 15
missile_max_speed = 45
missile_homingness = 3

# Interactible Settings
interactible_mass = 6
interactible_size = 14
# Lower is less friction
interactible_friction = 0.05
interactible_pull = 2

# Gravitywell Settings
gravitywell_mass = 10
gravitation = 300

# Obstacle Settings
obstacle_width = 35

FPS = 60

# Default settings
player_pos = Vec(screen_width/2, screen_height/2)
n_edibles = 5
n_clickables = 6
n_missiles = 8
n_interactibles = 10
n_gravitywells = 0
n_borders = 5

def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((screen_width, screen_height))
    background = pygame.Surface(screen.get_size())
    background.fill(bg_color)
    background.convert()
    running = True

    player, entities, edibles, clickables = reset(0)

    while running:
        # restart if the player has eaten everything
        if len(edibles) == 0 or player.sfd:
            player, entities, edibles, clickables = reset(player.score)
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
                # The final clickable knows about the player
                if player.target is not None:
                    player.target.is_clicked = True
                    player.target.target = player
            elif event.type == pygame.MOUSEBUTTONUP:
                if player.target is not None:
                    player.target.is_clicked = False
                    player.target.target = None
                    player.target = None

        for entity in entities:
            entity.update(dt, entities)

        # Kill all entities scheduled for destruction
        entities = [e for e in entities if not e.sfd]
        edibles = [e for e in edibles if not e.sfd]
        clickables = [e for e in clickables if not e.sfd]

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

def collide(e1, e2):
    return rect_overlap(e1.get_bbox(), e2.get_bbox())

def get_dist(e1, e2):
    return e1.pos.distance_to(e2.pos)

def vec_from(e1, e2):
    return e2.pos - e1.pos

def unit_vec_from(e1, e2):
    return vec_from(e1, e2).normalize()

def wrap_val(x, max_x):
    if x < 0:
        return max_x + x
    elif x > max_x:
        return x - max_x
    else:
        return x

def wrap_around(p):
    new_p = Vec(0,0)
    new_p[0] = wrap_val(p[0], screen_width)
    new_p[1] = wrap_val(p[1], screen_height)
    return new_p

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
        self.is_solid = False

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
        self.is_solid = True

    def update(self, time, entities):
        for e in entities:
            # Kill killable entities that overlap
            if hasattr(e, "die") and collide(self, e):
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

    def __init__(self, entities, clickables, xpos, ypos,
            xsize=default_size, ysize=default_size, color=clickable_color):
        super().__init__(entities, xpos, ypos, xsize, ysize)
        self.target = None
        self.is_clicked = False
        clickables.append(self)
        # drawing surface
        self._surface = mk_square_surface(self.xsize, color)

    def update(self, time, entities):
        pass

    def draw(self, screen):
        super().draw(screen)

class Player(Entity):

    def __init__(self, entities, xpos, ypos):
        super().__init__(entities, xpos, ypos)
        self.score = 0
        self.reset(Vec(xpos, ypos))
        self.mass = player_mass
        self.is_solid = True
        # drawing surface
        self._surface = mk_square_surface(self.xsize, player_color)

    def reset(self, pos):
        self.target = None
        self.a = Vec(0,0)
        self.v = Vec(0,0)
        self.pos = pos 

    def die(self, msg):
        print(msg)
        self.reset(player_pos)
        self.score = 0
        self.sfd = True

    def update(self, time, entities):
        # Physics
        if self.target is not None:
            to_target = vec_from(self, self.target).normalize()
            #da = math.exp(-1/(to_target.length()))
            #to_target.scale_to_length(da)
            self.a = player_pull * to_target
        else:
            self.a = Vec(0,0)
        self.v -=self.v * friction
        self.v += self.a
        self.pos += self.v * time
        self.pos = wrap_around(self.pos)

        # Eat entities
        for e in entities:
            if hasattr(e, "eat") and collide(self, e):
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

def mk_wait_surface(xsize, ysize, center):
    surface = pygame.Surface((xsize, ysize), pygame.SRCALPHA, 32)
    pygame.draw.circle(surface, missile_color, center, missile_radius)
    pygame.draw.circle(surface, missile_color, center, missile_prox, 1)
    surface.convert_alpha()
    return surface

def mk_target_surface(xsize, ysize, center):
    #TODO: this is lazy blitting
    surface = pygame.Surface((xsize, ysize), pygame.SRCALPHA, 32)
    pygame.draw.circle(surface, missile_color, center, missile_radius)
    surface.convert_alpha()
    return surface

def mk_exploding_surface(xsize, ysize, center):
    surface = pygame.Surface((xsize, ysize), pygame.SRCALPHA, 32)
    pygame.draw.circle(surface, missile_explosion_color, center, missile_explosion_radius)
    surface.convert_alpha()
    return surface

class Missile(Entity):
    
    def __init__(self, player, entities, xpos, ypos):
        super().__init__(entities, xpos, ypos, 2*missile_prox, 2*missile_prox)
        self.target = player
        self.a = Vec(0, 0)
        self.v = Vec(0, 0)
        self.prox = missile_prox
        self.state_counter = 0
        self.explosion_radius = missile_explosion_radius
        self.max_speed = missile_max_speed
        self.sfd = False
        # Drawing surface and state counter
        self.set_state(MissileState.WAITING)

    def get_bbox(self):
        return (self.pos - (missile_radius, missile_radius), self.pos + (missile_radius, missile_radius))

    def set_state(self, state):
        if state == MissileState.WAITING:
            self.a = Vec(0,0)
            self.v = Vec(0,0)
            self._surface = mk_wait_surface(self.xsize, self.ysize, self.center)
        elif state == MissileState.TARGETING:
            self.a = Vec(0,0)
            self.v = Vec(0,0)
            self._surface = mk_target_surface(self.xsize, self.ysize, self.center)
        elif state == MissileState.EXPLODING:
            self.a = Vec(0,0)
            self.v = Vec(0,0)
            self._surface = mk_exploding_surface(self.xsize, self.ysize, self.center)
        self.state = state

    def update(self, time, entities):
        if (self.state == MissileState.WAITING):
            # Trigger if the player is close
            if get_dist(self, self.target) < self.prox:
                self.set_state(MissileState.TARGETING)
            # Trigger if the player clicks on something close
            elif self.target.target is not None:
                if get_dist(self, self.target.target) < self.prox:
                    self.set_state(MissileState.TARGETING)
        elif (self.state == MissileState.TARGETING):
            # Collision with solids
            for e in entities:
                if e.is_solid and collide(self, e):
                    self.die("")
            # Explode near the player
            if vec_from(self, self.target).length() < missile_explosion_radius + self.target.xsize/2:
                self.die("")
            # Accelerate towards the player
            da = vec_from(self, self.target)
            da += self.target.v * time
            da = da.normalize()
            da *= missile_homingness
            self.a = da
        elif (self.state == MissileState.EXPLODING):
            # TODO: lower velocity
            self.state_counter += 1
            # 10 frames of missile explosion
            # TODO: time-based?
            if self.state_counter == 10:
                self.sfd = True
            # Kill player if they are close
            if get_dist(self, self.target) < missile_explosion_radius + self.target.xsize:
                self.target.die("Blown up by a missile.")
        # Physics
        self.v += self.a
        if self.v.length() > missile_max_speed:
            self.v.scale_to_length(missile_max_speed)
        self.pos += self.v * time
        self.pos = wrap_around(self.pos)

    def draw(self, screen):
        if self.target is not None and self.state == MissileState.TARGETING:
            draw_line(screen, self.pos, self.target.pos, missile_explosion_color)
        super().draw(screen)

    def die(self, msg):
        self.set_state(MissileState.EXPLODING)

def get_collision_vectors(e1, e2):
    u = vec_from(e2, e1).normalize()
    vu1 = e1.v.dot(u)
    vu2 = e2.v.dot(u)
    wu1 = (e1.mass * vu1 + e2.mass * (2*vu2 - vu1))/(e1.mass + e2.mass)
    wu2 = (e2.mass * vu2 + e1.mass * (2*vu1 - vu2))/(e1.mass + e2.mass)
    w1 = e1.v + (u * (wu1 - vu1))
    w2 = e2.v + (u * (wu2 - vu2))
    return w1, w2

class Interactible(Clickable):

    def __init__(self, player, entities, clickables, xpos, ypos):
        super().__init__(entities, clickables, xpos, ypos,
                interactible_size, interactible_size, interactible_color)
        self.v = Vec(0,0)
        self.a = Vec(0,0)
        self.mass = interactible_mass
        self.is_solid = True

    def update(self, time, entities):
        # Check for collisions
        for e in entities:
            if e.is_solid and self.pos != e.pos and collide(self, e):
                # Bounce off of other things
                if hasattr(e, "v"):
                    v1, v2 = get_collision_vectors(self, e)
                    self.v = v1
                    e.v = v2
                # Bounce elastically off of other solids
                else:
                    self.v = -1 * self.v
        # Player pulls this
        if self.target is not None:
            pvec = vec_from(self, self.target)
            pvec = pvec.normalize() * interactible_pull
            self.a = pvec
        else:
            self.a = Vec(0,0)
        # Friction
        self.v -= self.v * interactible_friction

        # Physics
        self.v += self.a
        self.pos += self.v * time
        self.pos = wrap_around(self.pos)

    def draw(self,screen):
        super().draw(screen)

class GravityWell(Entity):

    def __init__(self, player, entities, xpos, ypos):
        super().__init__(entities, xpos, ypos)
        self.target = player
        self.mass = gravitywell_mass
        # Surface:
        self._surface = mk_square_surface(self.xsize, gravitywell_color)

    def update(self, time, entities):
        # pull the player towards it with gravitational force
        p_vec = vec_from(self.target, self)
        p_len = p_vec.length()
        p_force = gravitation * (self.mass * self.target.mass / (p_len * p_len))
        p_a = p_force / self.target.mass
        self.target.v += p_a * p_vec * time

    def draw(self, screen):
        super().draw(screen)

def random_pos():
    bw = border_width * 1.5
    p1 = random.uniform(bw, screen_width - bw)
    p2 = random.uniform(bw, screen_height - bw)
    return Vec(p1, p2)

def reset(score):
    # Clear the lists
    entities = []
    edibles = []
    clickables = []
    # Create the player
    player = Player(entities, player_pos[0], player_pos[1])
    player.score = score

    # Borders
    #b1 = Border(entities, screen_width/2, border_width/2, screen_width, border_width)
    #b2 = Border(entities, border_width/2, screen_height/2, border_width, screen_height)
    #b3 = Border(entities, screen_width/2, screen_height-border_width/2, screen_width, border_width)
    #b4 = Border(entities, screen_width-border_width/2, screen_height/2, border_width, screen_height)

    # Generate borders
    nb = 0
    while nb < n_borders:
        p = random_pos()
        if (p - player.pos).length() > 2 * obstacle_width:
            b = Border(entities, p[0], p[1], obstacle_width, obstacle_width)
            nb += 1
    # Generate clickables
    for i in range(n_clickables):
        p = random_pos()
        c = Clickable(entities, clickables, p[0], p[1])
    #TODO: edibles not inside borders!
    # Generate edibles
    for j in range(n_edibles):
        p = random_pos()
        e = Edible(entities, edibles, p[0], p[1])
    # Generate gravitywells
    for g in range(n_gravitywells):
        p = random_pos()
        g = GravityWell(player, entities, p[0], p[1])
    # Generate missiles
    nm = 0
    while nm < n_missiles:
        p = random_pos()
        # Only place if not too close to the player
        if (p - player.pos).length() > missile_prox:
            m = Missile(player, entities, p[0], p[1])
            nm += 1
    # Generate interactibles
    ni = 0
    while ni < n_interactibles:
        p = random_pos()
        if (p - player.pos).length() > interactible_size:
            i = Interactible(player, entities, clickables, p[0], p[1])
            ni += 1

    return player, entities, edibles, clickables

# Executable
if __name__=="__main__":
    main()

