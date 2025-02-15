from BlazeSudio.Game import Game
from BlazeSudio.graphics import GUI
from BlazeSudio import collisions
import BlazeSudio.Game.statics as Ss
import pygame

G = Game()
G.load_map("./world.ldtk")

class DebugCommands: # TODO: Make this not floating around as a global variable
    def __init__(self, Game):
        self.Game = Game
        self.collTyp = False
        self.Game.AddCommand('colltyp', '/colltyp ...: Toggle collision type from/to point and box', self.toggleColls)
    
    def toggleColls(self, *args):
        self.collTyp = not self.collTyp
        self.Game.UILayer.append(GUI.Toast(self.Game, 'Changed to '+('point' if self.collTyp else 'box') + ' collisions'))

debug = DebugCommands(G)

class BaseEntity(Ss.BaseEntity):
    def __init__(self, Game, e):
        super().__init__(Game, e)
        self.gravity = [0, 2]
    
    def __call__(self, evs):
        self.handle_keys()
        self.apply_physics()
        colls = self.Game.currentLvL.layers[1].intgrid.getRects(1)
        #for i in colls:
        #    i.bounciness = 1
        if debug.collTyp:
            outRect, self.velocity = collisions.Point(self.scaled_pos[0], self.scaled_pos[1]).handleCollisionsVel(self.velocity, colls, False)
            outUnscaled = self.entity.unscale_pos(outRect)
        else:
            self.pos = [self.pos[0]-0.45, self.pos[1]-0.45]
            outRect, self.velocity = collisions.Rect(self.scaled_pos[0], self.scaled_pos[1], self.entity.gridSze*0.9, self.entity.gridSze*0.9).handleCollisionsVel(self.velocity, colls, False)
            outUnscaled = self.entity.unscale_pos((outRect.x, outRect.y))
            outUnscaled = [outUnscaled[0]+0.45, outUnscaled[1]+0.45]
        self.pos = outUnscaled
    
    @property
    def scaled_pos(self):
        return self.entity.scale_pos(self.pos)

def isValidLevel(lvl):
    return 0 <= lvl < len(G.world.ldtk.levels)

@G.DefaultSceneLoader
class MainGameScene(Ss.BaseScene):
    DefaultEntity = []
    def __init__(self, Game, **settings):
        self.lvl = settings.get('lvl', 0) # This before because it loads the bounds in the super() and it needs the level
        super().__init__(Game, **settings)
        self.sur = None
        self.CamDist = 8
        for e in self.currentLvl.entities:
            if e.defUid == 107:
                self.entities.append(BaseEntity(Game, e)) # The Player
                self.DefaultEntity.append(e)
                if settings.get('UsePlayerStart', False):
                    self.entities[0].pos = [e.UnscaledPos[0]+0.5, e.UnscaledPos[1]+0.5]
                else:
                    self.entities[0].pos = [settings.get('x', 0.5), settings.get('y', 0.5)]
                break
        if self.entities == []:
            if self.DefaultEntity != []:
                self.entities.append(BaseEntity(Game, self.DefaultEntity[-1]))
                self.entities[0].pos = [settings.get('x', 0.5), settings.get('y', 0.5)]
            else:
                raise Ss.IncorrectLevelError(
                    'Need a player start!'
                )
    
    @property
    def CamPos(self):
        return self.entities[0].scaled_pos
    
    def tick(self, evs):
        super().tick(evs)
        playere = self.entities[0]
        for n in self.currentLvl.neighbours: # TODO: Level offsets
            nxtLvl = [i.iid for i in self.Game.world.ldtk.levels].index(n['levelIid'])
            if playere.scaled_pos[0] >= self.currentLvl.sizePx[0] and n['dir'] == 'e':
                G.load_scene(lvl=nxtLvl, y=playere.pos[1])
            if playere.scaled_pos[0] <= 0 and n['dir'] == 'w':
                G.load_scene(lvl=nxtLvl, y=playere.pos[1], x=self.Game.world.get_level(nxtLvl).sizePx[0]/playere.entity.gridSze-0.5)
            if playere.scaled_pos[1] <= 0 and n['dir'] == 'n':
                G.load_scene(lvl=nxtLvl, x=playere.pos[0])
            if playere.scaled_pos[1] >= self.currentLvl.sizePx[1] and n['dir'] == 's':
                G.load_scene(lvl=nxtLvl, x=playere.pos[0], y=self.Game.world.get_level(nxtLvl).sizePx[1]/playere.entity.gridSze-0.5)
    
    def postProcessScreen(self, sur, diffs):
        ppos = self.entities[0].scaled_pos
        diff = (
            diffs[0]/self.CamDist-ppos[0],
            diffs[1]/self.CamDist-ppos[1]
        )
        sze = sur.get_size()
        psze = 10
        r = ((sze[0]-psze)/2-diff[0], (sze[1]-psze)/2-diff[1], psze, psze)
        pygame.draw.rect(sur, (0, 0, 0), r, border_radius=2)
        pygame.draw.rect(sur, (255, 255, 255), r, width=1, border_radius=2)
        return sur

G.load_scene(UsePlayerStart=True)

G.debug()
