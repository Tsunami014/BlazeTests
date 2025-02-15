from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', 'gravityGolf'))
    exit()

import os
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap

import pygame
pygame.init()
pygame.display.set_mode()
pygame.display.toggle_fullscreen()

world = world.World("./planets.ldtk")

imgs = [[], []]
for lvl in range(len(world.ldtk.levels)):
    for e in world.ldtk.levels[lvl].entities:
        if e.identifier == 'Settings':
            break
    else:
        continue

    i1, i2 = wrap.wrapLevel(world, lvl, top=0.5, bottom=-1, limit=False)
    imgs[0].append(i1)
    imgs[1].append(i2)

pth = os.path.dirname(__file__) + "/"

blanks = wrap.find_blanks(imgs[0], imgs[1])
wrap.save(imgs[0], pth+"out/out.png", 128, blanks)
wrap.save(imgs[1], pth+"out/colls.png", 128, blanks)
