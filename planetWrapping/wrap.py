from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', 'planetWrapping'))
    exit()

# TODO: Clean up?
# Thanks to https://stackoverflow.com/questions/38745020/wrap-image-around-a-circle !
import math as m
import pygame, os
from BlazeSudio.Game import world

world = world.World("./planets.ldtk")

imgs = [[], []]
for outlining in (False, True):
    for lvl in range(len(world.ldtk.levels)):
        Ro = 100.0
        Ri = 50.0
        size = 128
        settingsExists = False
        for e in world.ldtk.levels[lvl].entities:
            if e.identifier == 'Settings':
                settingsExists = True
                for i in e.fieldInstances:
                    if i['__identifier'] == 'Ro':
                        Ro = i['__value'] or Ro
                    if i['__identifier'] == 'Ri':
                        Ri = i['__value'] or Ri
                    if i['__identifier'] == 'size':
                        size = i['__value'] or size
        if not settingsExists:
            continue

        cir = [[(0, 0, 0, 0) for x in range(int(Ro * 2))] for y in range(int(Ro * 2))]

        if outlining:
            for i in world.get_level(lvl).layers:
                i.tileset = None  # So it has to render blocks instead >:)
        pg = world.get_pygame(lvl, transparent_bg=True)
        width, height = pg.get_size()
        pixels = pygame.surfarray.pixels3d(pg)
        alpha = pygame.surfarray.pixels_alpha(pg)

        for i in range(int(Ro)):
            outer_radius = m.sqrt(Ro * Ro - i * i)
            for j in range(-int(outer_radius), int(outer_radius)):
                if i < Ri:
                    inner_radius = m.sqrt(Ri * Ri - i * i)
                else:
                    inner_radius = -1
                if j < -inner_radius or j > inner_radius:
                    x = Ro + j
                    y = Ro - i
                    angle = m.atan2(y - Ro, x - Ro) / 2
                    distance = m.sqrt((y - Ro) * (y - Ro) + (x - Ro) * (x - Ro))
                    distance = m.floor((distance - Ri + 1) * (height - 1) / (Ro - Ri))
                    if distance >= height:
                        distance = height - 1
                    col = pixels[int(width * angle / m.pi) % width, height - distance - 1]
                    a = alpha[int(width * angle / m.pi) % width, height - distance - 1]
                    if outlining:
                        if a == 3:
                            col = (0, 0, 0)
                            a = 255
                        else:
                            col = (255, 255, 255)
                            a = 255
                    cir[int(y)][int(x)] = (*col, a)
                    y = Ro + i
                    angle = m.atan2(y - Ro, x - Ro) / 2
                    distance = m.sqrt((y - Ro) * (y - Ro) + (x - Ro) * (x - Ro))
                    distance = m.floor((distance - Ri + 1) * (height - 1) / (Ro - Ri))
                    if distance >= height:
                        distance = height - 1
                    col = pixels[int(width * angle / m.pi) % width, height - distance - 1]
                    a = alpha[int(width * angle / m.pi) % width, height - distance - 1]
                    if outlining:
                        if a == 3:
                            col = (0, 0, 0)
                            a = 255
                        else:
                            col = (255, 255, 255)
                            a = 255
                    cir[int(y)][int(x)] = (*col, a)
        imgs[outlining].append(cir)

def render(imgs, fname):
    height = len(imgs) * len(imgs[0])
    width = len(imgs[0][0])
    new_image = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(imgs):
        for x, col in enumerate(row):
            for i, pixel in enumerate(col):
                new_image.set_at((x, y * len(col) + i), pixel)
    new_image = pygame.transform.scale(new_image, (size, size * len(imgs)))
    pygame.image.save(new_image, os.path.dirname(__file__) + "/" + fname)

render(imgs[0], "out.png")
render(imgs[1], "colls.png")
