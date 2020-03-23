#!/usr/bin/python
import numpy as np
import pygame
import pygame_textinput as pgt
import sys
import text
import board
import bot
import game

SCREENX = 1000
SCREENY = 800
STROKEW = 2
RADIUS = 70
HEIGHT = int(np.sqrt(RADIUS**2 - (RADIUS/2)**2))
STRUCTURE = {
    0 : [5, 2, 2],
    1 : [5, 2, 1],
    2 : [4, 3, 1],
    3 : [4, 3, 2],
    4 : [5, 2, 3],
    5 : [4, 1, 2],
    6 : [4, 1, 1],
    7 : [4, 1, 0],
    8 : [5, 2, 0],
    9 : [4, 3, 0],
    10 : [3, 4, 0],
    11 : [3, 4, 1],
    12 : [3, 4, 2],
    13 : [4, 3, 3],
    14 : [5, 2, 4],
    15 : [4, 1, 3],
    16 : [3, 0, 2],
    17 : [3, 0, 1],
    18 : [3, 0, 0],
}

DIRECTIONS = [0, 1*np.pi/3, 2*np.pi/3, np.pi, 4*np.pi/3, 5*np.pi/3]

screen = pygame.display.set_mode((SCREENX, SCREENY))
match_bot = bot.get_net("mismatch199")
pygame.display.set_caption("ML Project")
screen.fill((255,255,255))
textinput = pgt.TextInput()
clock = pygame.time.Clock()
global turn
global wc
global bc
global pwc
global pbc
turn = 0
wc = board.WHITEC
bc = board.BLACKC
pwc = board.WHITEC
pbc = board.BLACKC

def reset_board(screen):
    b = board.Board()
    path = []
    vic = ""
    done = False
    screen.fill((255,255,255))
    globals()["turn"] = 0
    globals()["wc"] = board.WHITEC
    globals()["bc"] = board.BLACKC
    globals()["pwc"] = board.WHITEC
    globals()["pbc"] = board.BLACKC

    return b, path, vic, done

b, path, vic, done = reset_board(screen)

def random_fill(b):
    for i in range(1, 19):
        b.move(i, board.COLOR_NAMES[np.random.randint(-2, 0)], board.DIRECTIONS[np.random.randint(0,6)])

def draw_hex(surf, x, y, radius = RADIUS, color = (0,0,0), numSides = 6, tiltAngle = 0):
  pts = []
  h = int(np.sqrt(radius**2 - (radius/2)**2))
  for i in range(numSides):
    x = x + radius * np.cos(tiltAngle + np.pi * 2 * i / numSides)
    y = y + radius * np.sin(tiltAngle + np.pi * 2 * i / numSides)
    pts.append([int(x) - radius/2, int(y) - h])
  pygame.draw.lines(surf, color, True, pts, STROKEW)

def draw_marker(surf, color, direction, x, y, TSIZE=int(RADIUS/1.61)):
    pts = []
    pts.append([-TSIZE/2, TSIZE/4])
    pts.append([TSIZE/2, TSIZE/4])
    pts.append([0, -TSIZE/4])
    theta = DIRECTIONS[direction]

    for p in pts:
        x_p = np.cos(theta)*p[0] - np.sin(theta)*p[1] + x
        y_p = np.cos(theta)*p[1] + np.sin(theta)*p[0] + y
        p[0], p[1] = x_p, y_p
    
    if color == -2:
        pygame.draw.polygon(surf, (0,0,0), pts)
    else:
        pygame.draw.lines(surf, (0,0,0), True, pts, STROKEW)


def get_center(tile):
    base_x = SCREENX/2 - 3 * RADIUS
    base_y = SCREENY/2 - (STRUCTURE[tile][0] - 1) * HEIGHT

    return (base_x + 3 * RADIUS * STRUCTURE[tile][1]/2, base_y + 2*STRUCTURE[tile][2]*HEIGHT)


def draw_board(surf):
    for tile in range(len(STRUCTURE)):
       center = get_center(tile)
       draw_hex(surf, *center)
       text.text_to_screen(surf, "B: {}, W: {}".format(globals()["pbc"], globals()["pwc"]), SCREENX - 100, 10)
       text.text_to_screen(surf, "{}".format(tile), center[0] - 6 * len(str(tile)), center[1] + RADIUS/2)


def draw_path(surf, path):
    pts = [get_center(tile) for tile in path]
    if pts:
        pygame.draw.lines(surf, (255,0,0), False, pts, STROKEW)


def draw_state(surf, state):
    for tile_n, tile_state in enumerate(state):
        if tile_state.any():
            color = -(2 - int(np.where(tile_state.any(axis=0))[0]))
            direction = int(np.where(tile_state.any(axis=1))[0])
            draw_marker(surf, color, direction, *get_center(tile_n))

def process_place_command(command):
    if len(command.split()) == 3:
        tile, color, direction = command.split()
        tile = int(tile)
    else:
        tile, color, direction = 0, 'black', 'N'
    return tile, color, direction

def clear_text(surf):
    pygame.draw.rect(surf, (255, 255, 255), (10,10,SCREENX, 50), 0)


while (True):
   # check for quit events
   events = pygame.event.get()
   for event in events:
        if event.type == pygame.QUIT:
             pygame.quit(); sys.exit();
        if event.type == pygame.KEYDOWN and event.key == pygame.locals.K_ESCAPE:
             b, path, vic, done = reset_board(screen)
             continue
   
   clear_text(screen)

   if textinput.update(events) or turn == 0:
        raw_command = textinput.get_text()
        textinput.clear_text()
        if raw_command == 'rand':
            b, path, vic, done = reset_board(screen)
            random_fill(b)
            print(b.greedy_swap())
            continue
        try:
           if not b.complete:
               if not turn == 0:
                   tile, color, direction = process_place_command(raw_command) 
               else:
                   tile, color, direction = 0, 'black', 'N'
               if not b.move(tile, color, direction) and turn != 0:
                   print("Invalid command")
               else:
                   if turn != 0:
                       turn += 1
                       if color == 'white':
                           pwc -= 1
                       else:
                           pbc -= 1
                   if not turn % 2 and not b.complete:
                       c = game.best_legal_move(b, match_bot.activate(b.state.flatten()), wc, bc)
                       if c == 'white':
                           wc -= 1
                       else:
                           bc -= 1
                       turn += 1
                   if turn == 18:
                       print b.greedy_swap()
           elif not done:
               if len(raw_command.split()) == 4:
                   t1, t2, t3, t4 = map(int, raw_command.split())
                   b.swap(t1, t2)
                   b.swap(t3, t4)
                   path, vic, _ = b.eval()
                   done = True
                   screen.fill((255,255,255))
               else:
                   print("Invalid swap")
        except Exception, e:
            print(e)

   screen.blit(textinput.get_surface(), (10,10))

   # draw the game board
   draw_board(screen)
   draw_state(screen, b.state)
   draw_path(screen, path)
   text.text_to_screen(screen, vic, 10, SCREENY - 50)

   # update the screen
   pygame.display.update()
   clock.tick(30)

