from BlazeSudio import ldtk
from BlazeSudio.Game import Game
from BlazeSudio import collisions
import BlazeSudio.Game.statics as Ss
from BlazeSudio.graphics import options as GO
from BlazeSudio.utils import approximate_polygon
import pygame

G = Game()
G.load_map("./levels.ldtk")
# TODO: A more uniform way to access things (e.g. the current level)

class DebugCommands:
    def __init__(self, Game):
        self.Game = Game
        Game.AddCommand('/load', 'Load any level', lambda x: Game.load_scene(lvl=int(x[0])))
        Game.AddCommand('/next', 'Load the next level', lambda: Game.load_scene(lvl=Game.currentScene.lvl+1))
        Game.AddCommand('/prev', 'Load the previous level', lambda: Game.load_scene(lvl=Game.currentScene.lvl-1))
        Game.AddCommand('/splash', 'Go back to the splash screen', lambda: Game.load_scene(SplashScreen))
        Game.AddCommand('/reload', 'Reload the current level', lambda: Game.load_scene(lvl=Game.currentScene.lvl))
        self.showingColls = False
        self.Game.AddCommand('/colls', 'Toggle collision debug', self.toggleColls)
    
    def toggleColls(self):
        self.showingColls = not self.showingColls
        self.Game.G.Toast(('Showing' if self.showingColls else 'Not showing') + ' collisions')

debug = DebugCommands(G)

def CollisionProcessor(e):
    if 'CircleRegion' in e.identifier or e.identifier == 'BlackHole':
        return collisions.Circle(e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.height/2, e.width/2)
    elif 'RectRegion' in e.identifier or e.identifier == 'Goal':
        return collisions.Rect(*e.ScaledPos, e.width, e.height)

class PlayerEntity(Ss.BaseEntity):
    def __init__(self, Game, entity):
        super().__init__(Game, entity)
        self.collided = False
        self.accel_amnt = [[2.5, 2.5], [0.5, 0.5]]
        self.max_accel = [30, 30]
        #self.friction = [0.1, 0.1]
        self.defcollideDelay = 3
        self.collidingDelay = self.defcollideDelay
        self.defClickDelay = 3
        self.clicked = 0
    
    def __call__(self, keys):
        oldPos = self.scaled_pos
        in_bh = collisions.Point(*oldPos).collides(self.Game.currentLvL.GetEntitiesByID('BlackHole', CollisionProcessor))
        if in_bh:
            objs = collisions.Shapes(*self.Game.currentScene.getBlackHoles())
        else:
            objs = collisions.Shapes(*self.Game.currentLvL.GetEntitiesByLayer('GravityFields', CollisionProcessor), 
                                     *self.Game.currentLvL.GetEntitiesByID('BlackHole', CollisionProcessor))
        thisObj = collisions.Point(*oldPos)
        cpoints = objs.closestPointTo(thisObj) # [(i, i.closestPointTo(curObj)) for i in objs]
        if cpoints:
            cpoints.sort(key=lambda x: (thisObj.x-x[0])**2+(thisObj.y-x[1])**2)
            closest = cpoints[0]
            angle = collisions.direction(closest, thisObj)
            gravity = collisions.pointOnUnitCircle(angle, -0.5)
        else:
            gravity = [0, 0]
        self.gravity = gravity
        self.handle_accel()
        oldaccel = self.accel
        outRect, self.accel, v = thisObj.handleCollisionsAccel(self.accel, self.Game.currentScene.collider(), False, verbose=True)
        mvementLine = collisions.Line(oldPos, outRect)
        if mvementLine.collides(collisions.Shapes(*[collisions.Circle(i.x, i.y, 1) for i in self.Game.currentScene.getBlackHoles()])):
            self.Game.load_scene(lvl=self.Game.currentScene.lvl)
        if mvementLine.collides(collisions.Shapes(*self.Game.currentLvL.GetEntitiesByID('Goal', CollisionProcessor))):
            if self.Game.currentScene.lvl+1 >= len(self.Game.world.ldtk.levels):
                self.Game.load_scene(SplashScreen)
            else:
                self.Game.load_scene(lvl=self.Game.currentScene.lvl+1)
            return
        if in_bh:
            self.collided = False
            self.collidingDelay = 3
        else:
            # If you bounced or you were going to be inside a gravity field, whether or not you bounced (so if you did it would still register)
            newcolliding = v[-1] or collisions.Line(oldPos, (oldPos[0]+oldaccel[0], oldPos[1]+oldaccel[1])).collides(self.Game.currentLvL.GetEntitiesByLayer('GravityFields', CollisionProcessor))
            if newcolliding != self.collided:
                if self.collidingDelay <= 0:
                    self.collided = newcolliding
                else:
                    self.collidingDelay -= 1
                    if self.collidingDelay <= 0:
                        self.collided = newcolliding
            else:
                if self.collidingDelay >= self.defcollideDelay:
                    pass
                else:
                    self.collidingDelay += 0.25
        self.pos = self.entity.unscale_pos(outRect)
    
    @property
    def scaled_pos(self):
        return self.entity.scale_pos(self.pos)

class SplashScreen(Ss.SkeletonScene):
    useRenderer = False
    def __init__(self, Game, **settings):
        super().__init__(Game, **settings)
        self.rendered = False
    def render(self):
        if not self.rendered:
            graphic = self.Game.G
            graphic.bgcol = self.Game.world.get_level(0).bgColour
            graphic.add_empty_space(GO.PCTOP, 0, 30)
            graphic.add_text('Gravity golf!', GO.CWHITE, GO.PCTOP, GO.FTITLE)
            graphic.add_button('Play!!!', GO.CGREEN, GO.PCCENTER, callback=lambda x: self.Game.load_scene())
            self.rendered = True

@G.DefaultSceneLoader
class MainGameScene(Ss.BaseScene):
    def __init__(self, Game, **settings):
        super().__init__(Game, **settings)
        self.CamDist = 2
        self.CamBounds = [None, None, None, None]
        self.lvl = settings.get('lvl', 0)
        self.bhs = None
        self.sur = None
        self.showingColls = True
        self.last_playerPos = [0, 0]
        self._collider = None
        for e in self.currentLvl.entities:
            if e.defUid == 7:
                self.entities.append(PlayerEntity(Game, e)) # The Player
                self.entities[0].pos = [e.UnscaledPos[0]+0.5, e.UnscaledPos[1]+0.5]
                break
        if self.entities == []:
            raise Ss.IncorrectLevelError(
                'Need a player start!'
            )
    
    def collider(self):
        if self._collider is not None:
            return self._collider
        outcolls = []
        for lay in self.Game.currentLvL.layers:
            if lay.type == 'Tiles':
                def translate_polygon(poly, translation, sze):
                    offset = lay.add_offset((translation[0], translation[1]), sze)
                    return collisions.Polygon(*[(i[0]+offset[0], i[1]+offset[1]) for i in poly])
                if lay.identifier == 'Planets':
                    tmpl = ldtk.layer(lay.data, lay.level)
                    d = lay.tileset.data.copy()
                    d.update({'relPath': d['relPath'] + '/../colls.png'})
                    tmpl.tileset = ldtk.Tileset(lay.tileset.fileLoc, d)

                    outcolls.extend(translate_polygon(approximate_polygon(t.getImg()), t.pos, t.getImg().get_size()) for t in tmpl.tiles)
                else:
                    outnews = []
                    cache = {}
                    for t in lay.tiles:
                        src = tuple(t.src)
                        if src not in cache:
                            cache[src] = approximate_polygon(t.getImg())
                        grid = t.layer.tileset.tileGridSize
                        if isinstance(cache[src], collisions.Line):
                            offset = lay.add_offset((t.pos[0], t.pos[1]), (grid, grid))
                            outcolls.append(collisions.Line(*[(i[0]+offset[0], i[1]+offset[1]) for i in cache[src]]))
                        elif isinstance(cache[src], collisions.Point):
                            offset = lay.add_offset((t.pos[0], t.pos[1]), (grid, grid))
                            outcolls.append(collisions.Point(cache[src].x+offset[0], cache[src].y+offset[1]))
                        else:
                            if all(round(i.tangent(0, (0, 0)), 5)%360 in (90, 270, 180, 0) for i in cache[src].toLines()):
                                r = translate_polygon(cache[src], t.pos, (grid, grid)).rect()
                                outnews.append(collisions.Rect(r[0], r[1], r[2]-r[0]+1, r[3]-r[1]+1))
                            else:
                                outcolls.append(translate_polygon(cache[src], t.pos, (grid, grid)))
                    outcolls.extend(collisions.ShapeCombiner.to_rects(*outnews))
            elif lay.type == 'IntGrid':
                outcolls.extend(collisions.ShapeCombiner.to_rects(*self.Game.currentLvL.layers[2].intgrid.getRects([1, 2])))
        self._collider = collisions.Shapes(*outcolls)
        return self._collider
    
    def tick(self, evs):
        super().tick(evs)
        playere = self.entities[0]
        didClick = any(e.type == pygame.MOUSEBUTTONDOWN for e in evs)
        if didClick or playere.clicked > 0:
            if playere.collided:
                playere.collidingDelay = playere.defcollideDelay
                playere.collided = False
                angle = collisions.direction(pygame.mouse.get_pos(), self.last_playerPos)
                addPos = collisions.pointOnUnitCircle(angle, -40)
                def sign(x):
                    if x > 0:
                        return 1
                    if x < 0:
                        return -1
                    return 0
                addAccel = [min(abs(addPos[0]), abs(self.last_playerPos[0]-pygame.mouse.get_pos()[0])/4)*sign(addPos[0]),
                            min(abs(addPos[1]), abs(self.last_playerPos[1]-pygame.mouse.get_pos()[1])/4)*sign(addPos[1])]
                playere.accel[0] += addAccel[0]
                playere.accel[1] += addAccel[1]
            else:
                if didClick:
                    playere.clicked = playere.defClickDelay
                else:
                    playere.clicked -= 1

    def getBlackHoles(self):
        if self.bhs is None:
            self.bhs = []
            for e in self.currentLvl.entities:
                if e.identifier == 'BlackHole':
                    self.bhs.append(collisions.Point(e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.height/2))
        return self.bhs
    
    @property
    def CamPos(self):
        return self.entities[0].scaled_pos

    def render(self):
        if self.sur is not None and debug.showingColls == self.showingColls:
            return self.sur
        self.showingColls = debug.showingColls
        lvl = self.currentLvl
        self.sur = pygame.Surface(lvl.sizePx)
        self.sur.fill(self.Game.currentLvL.bgColour)
        colls = self.collider()
        self.sur.blit(self.Game.world.get_pygame(self.lvl), (0, 0))
        
        for e in lvl.entities:
            if e.identifier == 'BlackHole':
                pygame.draw.circle(self.sur, (0, 0, 0), (e.ScaledPos[0]+e.width/2, e.ScaledPos[1]+e.height/2), e.width//2)
            if e.identifier == 'Goal':
                # The star shape was made by me which is why it probably doesn't look very good
                pygame.draw.polygon(self.sur, (255, 180, 10), [(e.ScaledPos[0]+i[0]*e.width, e.ScaledPos[1]+(1-i[1])*e.height) for i in 
                                               [(0, 0), (0.5, 0.23), (1, 0), (0.7, 0.35), 
                                                (1, 0.5), (0.6, 0.6), (0.5, 1), (0.4, 0.6), 
                                                (0, 0.5), (0.3, 0.35)]])
        
        if self.showingColls:
            for col, li in (((255, 10, 50), colls), ((10, 50, 50), self.Game.currentLvL.GetEntitiesByLayer('GravityFields', CollisionProcessor)), ((255, 255, 255), self.getBlackHoles())):
                for s in li:
                    if isinstance(s, collisions.Polygon):
                        pygame.draw.polygon(self.sur, col, s.toPoints(), 1)
                    if isinstance(s, collisions.Rect):
                        pygame.draw.rect(self.sur, col, (s.x, s.y, s.w, s.h), 1)
                    elif isinstance(s, collisions.Circle):
                        pygame.draw.circle(self.sur, col, (s.x, s.y), s.r, 1)
                    elif isinstance(s, collisions.Point):
                        pygame.draw.circle(self.sur, col, (s.x, s.y), 5)

        return self.sur
    
    def renderUI(self, win, offset, midp, scale):
        pos = self.entities[0].scaled_pos
        p = (pos[0]*scale+offset[0], pos[1]*scale+offset[1])
        pygame.draw.circle(win, (0, 0, 0), (p[0], p[1]), 10)
        pygame.draw.circle(win, (255, 255, 255), (p[0], p[1]), 10, 2)
        if self.entities[0].collided:
            angle = collisions.direction(pygame.mouse.get_pos(), self.last_playerPos)
            addPos = collisions.pointOnUnitCircle(angle, -200)
            pygame.draw.line(win, (255, 155, 155), (p[0], p[1]), 
                            (p[0]+addPos[0], p[1]+addPos[1]), 5)
        self.last_playerPos = (p[0], p[1])

G.load_scene(SplashScreen)

G.play(debug=True)
