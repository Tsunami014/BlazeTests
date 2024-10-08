from BlazeSudio.ldtk import sync
if not sync.is_synced():
    print(sync.explanation())
    print("For this file, it's best to use it with the 'after save', so it will automatically update the file.")
    print(sync.generate_sync_code('wrap.py', 'planetWrapping'))
    exit()

import os
from BlazeSudio.Game import world
from BlazeSudio.utils import wrap

world = world.World("./planets.ldtk")

imgs = [[], []]
szes = []
for lvl in range(len(world.ldtk.levels)):
    Ro = None
    Ri = None
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
    szes.append(size)

    i1, i2 = wrap.wrapLevel(world, lvl)
    imgs[0].append(i1)
    imgs[1].append(i2)

pth = os.path.dirname(__file__) + "/"

wrap.save(imgs[0], pth+"out/out.png", szes)
wrap.save(imgs[1], pth+"out/colls.png", szes)
