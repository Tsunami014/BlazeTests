from BlazeSudio.Game import Game
import BlazeSudio.Game.statics as Ss
from BlazeSudio.graphics import GUI, options as GO
G = Game()
G.G.bgcol = (200, 200, 200)

@G.DefaultSceneLoader
class MainGameScene(Ss.SkeletonScene):
    useRenderer = False
    def __init__(self, Game, **settings):
        super().__init__(Game, **settings)
        self.rendered = False
        self.title = settings.get('title', ' ')
        self.txt = settings.get('txt', ' ')
        self.buttons = settings.get('buttons', {})

        lay = self.Game.UILayer
        lay.add('Alls')
        G = self.Game.G
        centre = GO.PNEW([1, 0], GO.PCCENTER.func, 1, 1)
        G['Alls'].extend([
            GUI.Empty(G, GO.PCTOP, (0, 30)),
            GUI.Text(G, GO.PCTOP, self.title, GO.CACTIVE, GO.FTITLE),
            GUI.Text(G, GO.PCTOP, self.txt, GO.CINACTIVE),

            GUI.Empty(G, centre, (-50, 0))
        ])
        G['Alls'].extend([
            GUI.Button(G, centre, inf[0], n, func=lambda inf=inf: (
                self.Game.load_scene(txt=inf[1], buttons=inf[2]) if isinstance(inf[1], str) else inf[1]()
                )
            ) for n, inf in self.buttons.items()
        ])
        self.rendered = True

def load_title(*args):
    orng = GO.CORANGE
    return G.load_scene(title='Do you want to play the game?', buttons={
        "Yes": [GO.CGREEN, 'But are you *really* sure?', {
            "No": [GO.CGREEN, 'HEHE GOT YOUS!', {
                "Back to title!": [orng, load_title]
            }],
            "No ": [GO.CRED, 'AHA! I thought so much. You DISCUST ME.', {
                "OK.": [orng, load_title]
            }]
        }],
        "No": [GO.CRED, 'Ha. YOU LOOSE THEN.', {
            "OK.": [orng, load_title]
        }]
    })

load_title()

G.play()