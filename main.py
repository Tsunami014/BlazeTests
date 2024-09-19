import os
import json
import importlib

allGames = [i for i in os.listdir() if '.' not in i and i != '__pycache__']

with open('data.json') as f:
    gameData = json.load(f)
    folders = [i['Folder'] for i in gameData]

print('Type a number to play that demo game!')
idx = 0
for i in allGames:
    if i in folders:
        print(f'{idx}: {gameData[folders.index(i)]["Name"]}. {gameData[folders.index(i)]["Description"]}')
    else:
        print(f'{idx}: {i}. UNKNOWN - NOT IN GAMEDATA')
    idx += 1

i = input("> ")
if i.isdecimal():
    i = int(i)
    if 0 <= i < len(allGames):
        if allGames[i] in folders:
            print(f'Starting demo game {i}: {gameData[folders.index(allGames[i])]["Name"]}...')
        else:
            print(f'Starting demo game {i}: {allGames[i]}...')
        os.chdir(os.path.join(os.getcwd(), allGames[i]))
        importlib.import_module('main')
    else:
        print('Number out of range! Exiting...')
else:
    print('Is not a number! Exiting...')
