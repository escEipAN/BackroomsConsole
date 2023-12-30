import os
import random
import keyboard
from enum import Enum
#from math import sin, cos, tan, atan, asin, acos
from fastmath import sin, cos
from PIL import Image
#from level import level
from time import sleep
from time import time
import curses
os.system("@echo off")
os.system("mode con cols=256 lines=66")
os.system("title Backrooms")
stdscr = curses.initscr()
curses.noecho()
width = 256
height = 66
aspect = width/height
pixelaspect = 11/24
frame = list(' '*(width * height))
#frame[width*height] = '\0'
work = True
t = 0 
mapWidth = 101
mapHeight = 101
t1 = time()
t2 = time()
#definitely did not stole vec2 from stackoverflow
# UPDATE: i stole only 50% of it

class vec2:

    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __truediv__(self, other):
        return vec2(self.x/other.x, self.y/other.y)

    def __mul__(self, other):
        return vec2(self.x*other.x, self.y*other.y)

    def __repr__(self):
        return 'vec2({}, {})'.format(self.x, self.y)

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    def __abs__(self):
        return (self.x**2+self.y**2)**0.5

    def __bool__(self):
        return self.x != 0 or self.y != 0

    def __neg__(self):
        return vec2(-self.x, -self.y)

def getColor(x: int, gradientmode=None):
    if gradientmode is None: gradientmode = 0
    gradient = ' .:!/r(;14HZ9W8$@'
    shortgradient = '~=x'
    if gradientmode == 0: return gradient[min(max(x, 0), len(gradient)-1)]
    if gradientmode == 1: return shortgradient[min(max(x, 0), len(shortgradient)-1)]
def drawImage(img: Image):
    img = img.convert('L')
    image = list(' '*(width * height))
    if not img.size == (width, height): img = img.resize((width, height))
    for i in range(width):
        for j in range(height):
            brightness = img.getpixel((i, j)) / 255 * 17
            pixel = getColor(int(brightness))
            image[i+j*width] = pixel
    return image
def LoadLevel(img: Image):
    global mapWidth
    global mapHeight
    image = list(' '*(mapWidth * mapHeight))
    img = img.convert('L')
    for i in range(mapWidth):
        for j in range(mapHeight):
            brightness = img.getpixel((i, j))
            if brightness == 0: pixel = '#'
            elif brightness == 65: pixel = "'"
            elif brightness == 128: pixel = ","
            elif brightness == 192: pixel = "@"
            elif brightness == 224: pixel = "0"
            else: pixel = '.'
            image[i+j*mapWidth] = pixel
    return image
level = LoadLevel(Image.open('assets/maze.png'))
def normalize(vec):
    return vec/vec2(abs(vec),abs(vec))
def dot(a: vec2, b: vec2):
    return a.x * b.x + a.y * b.y

class Player:
    def __init__(self, pos: vec2, angle, fov, renderDistance):
        self.pos = pos
        self.fov = fov
        self.angle = angle
        self.renderDistance = renderDistance

mainPlayer = Player(vec2(1.5,1.5), 0, 3.1415926 / 3, 16)
stamina = 1
noiselevel = 0

walls = {
    '#' : "walls/basic.png",
    '@' : "walls/bricks.png",
    '0' : "walls/finale.png"
    }
def textureToList(img):
    wallTexture = list(' '*32*32)
    for i in range(32):
        for j in range(32):
            wallTexture[j*32+i] = img.getpixel((i, j)) / 255
    return wallTexture
wallTextures = {key:textureToList(Image.open('assets/' + value).convert('L')) for (key,value) in walls.items()}
#wall = Image.open('assets/walls.png')


def getTexture(pos: vec2, wallType):
    global wallTextures
    try: wallTextures[wallType]
    except KeyError: return 0
    wallColor = wallTextures[wallType][int(pos.x*32)+(int((pos.y)*32))]
    return wallColor
class Raytype(Enum):
    RENDERLIGHT = 1
    PISTOL = 2 #unused


class Ray:
    def __init__(self, startPos: vec2, rayAngle, maxDistance, type=Raytype.RENDERLIGHT):
        global level
        global mapWidth
        global mapHeight
        global wallTextures
        distanceToWall = 0
        hitWall = False
        hitPortal = False
        eye = vec2(sin(rayAngle), cos(rayAngle))
        while not hitWall and distanceToWall < maxDistance:
            distanceToWall += 0.05
            testX = int(startPos.x + eye.x*distanceToWall)
            testY = int(startPos.y + eye.y*distanceToWall)

            if level[int(testY*mapWidth+testX)] in wallTextures or testX >= mapWidth or testY >= mapHeight or testX < 0  or testY < 0: 
                distanceToWall-=0.04
                while not hitWall:
                    distanceToWall += 0.01
                    testX = int(startPos.x + eye.x*distanceToWall)
                    testY = int(startPos.y + eye.y*distanceToWall)
                    if level[int(testY*mapWidth+testX)] in wallTextures or testX >= mapWidth or testY >= mapHeight or testX < 0  or testY < 0:
                        distanceToWall-=0.009
                        while not hitWall:
                            distanceToWall += 0.001
                            testX = int(startPos.x + eye.x*distanceToWall)
                            testY = int(startPos.y + eye.y*distanceToWall)
                            if level[int(testY*mapWidth+testX)] in wallTextures or testX >= mapWidth or testY >= mapHeight or testX < 0  or testY < 0: hitWall = True
                # Block boundaries
                # UPD: go fuck yourself, i'm not doing this 
                # UPD 2: go fuck yourself, i did this
                # UPD 3: why i even did this?
                #p = []
                #for tx in range(0,2):
                #    for ty in range(0,2):
                #        v = vec2(testX + tx - mainPlayer.pos.x, testY + ty - mainPlayer.pos.y)
                #        d = abs(v)
                #        v = normalize(v)
                #        p.append([d,dot(eye, v)])
                #p.sort(key=lambda l: l[0])
                #bound = 0.01
                #if acos(p[0][1]) < bound: boundary = True
                #if acos(p[1][1]) < bound: boundary = True
            elif level[int(testY*mapWidth+testX)] == ',': 
                hitWall = True
                hitPortal = True
        self.lengh = distanceToWall
        self.hitFlags =  hitPortal * 2 + hitWall
        self.wallObject = level[int(testY*mapWidth+testX)]
        self.endPoint = vec2(startPos.x + eye.x*distanceToWall, startPos.y + eye.y*distanceToWall)
def render():
    global width
    global height
    global mainPlayer
    frame = list(' '*width*height)
    global mapWidth
    global mapHeight
    global noiselevel
    for x in range(width):
        rayAngle = (mainPlayer.angle - mainPlayer.fov/2) + x / width * mainPlayer.fov
        ray = Ray(mainPlayer.pos, rayAngle, mainPlayer.renderDistance)
        ProjectionDistance = ray.lengh * cos(mainPlayer.angle - rayAngle)
        ceiling = height/2-height/ProjectionDistance
        floor = height - ceiling
        #pixel = ' '
        Shade = max(min(1-ray.lengh/mainPlayer.renderDistance,1),0)
        #pixel = getColor(int(Shade*17))
        if noiselevel: Shade+=noiselevel*random.random()
        if not ray.hitFlags & 0b1: Shade = 0
        #if distanceToWall <= mainPlayer.renderDistance / 3: pixel = '@'
        #elif distanceToWall < mainPlayer.renderDistance / 2: pixel = 'H'
        #elif distanceToWall < mainPlayer.renderDistance / 1.5: pixel = 'Z'
        #elif distanceToWall < mainPlayer.renderDistance: pixel = '1'
        texturePos = (ray.endPoint.x+ray.endPoint.y)%1
        mapConst = (height-2*ceiling)/32
        for y in range(height):
            if y <= ceiling:
                b = (height / 2 - y) / (height / 2)
                pixel = getColor(int(b*3), 1)
                frame[y*width + x] = pixel
            elif y > ceiling and y <= floor:
                frame[y*width + x] = getColor(int(Shade*((getTexture(vec2(texturePos,int((y-ceiling)/mapConst)), ray.wallObject)))*17))
                #frame[y*width + x] = pixel
                #if ray.hitFlags & 0b10:
                #    frame[y*width + x] = random.choice(["*", "0"])
                #frame[y*width + x] = getColor(int(Shade*17))
            else:
                b = (y - height / 2) / (height / 2)
                pixel = getColor(int(b*3), 1)
                frame[y*width + x] = pixel
    return frame
#if __name__ == '__main__':
#    lock = Lock()
#
#    for num in range(1):
#        Process(target=render, args=(lock, 0,width)).start()






def processControls():
    global noiselevel
    global mainPlayer
    global t1, t2
    global level
    global wallTextures
    stamina = 1
    t2 = time()
    elapsedTime = (t2 - t1)
    #elapsedTime = 0.01
    t1 = t2
    if keyboard.is_pressed('shift'):
        runLevel = 1 + stamina
        stamina -= 0.2 * elapsedTime
    else: 
        stamina += 0.15 * elapsedTime
        runLevel = 1
    stamina = min(max(stamina, 0), 1)
    def inWallCheck(pos): return level[int(pos.y)*mapWidth + int(pos.x)] in wallTextures
    def inPortalCheck(pos): return level[int(pos.y)*mapWidth + int(pos.x)] == ','
    playerHitbox = [mainPlayer.pos+vec2(0.1, 0.1), mainPlayer.pos+vec2(-0.1, 0.1), mainPlayer.pos-vec2(-0.1, 0.1), mainPlayer.pos-vec2(0.1, 0.1)]
    if keyboard.is_pressed('w'):
        shift = vec2(sin(mainPlayer.angle) * elapsedTime * runLevel, cos(mainPlayer.angle) * elapsedTime * runLevel)
        mainPlayer.pos.x += shift.x
        playerHitbox = [mainPlayer.pos+vec2(0.1, 0.1), mainPlayer.pos+vec2(-0.1, 0.1), mainPlayer.pos-vec2(-0.1, 0.1), mainPlayer.pos-vec2(0.1, 0.1)]
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.x -= shift.x
        mainPlayer.pos.y += shift.y
        playerHitbox = [mainPlayer.pos+vec2(0.1, 0.1), mainPlayer.pos+vec2(-0.1, 0.1), mainPlayer.pos-vec2(-0.1, 0.1), mainPlayer.pos-vec2(0.1, 0.1)]
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.y -= shift.y
    if keyboard.is_pressed('s'): 
        shift = vec2(sin(mainPlayer.angle) * elapsedTime * runLevel, cos(mainPlayer.angle) * elapsedTime * runLevel)
        mainPlayer.pos.x -= shift.x
        playerHitbox = [mainPlayer.pos+vec2(0.1, 0.1), mainPlayer.pos+vec2(-0.1, 0.1), mainPlayer.pos-vec2(-0.1, 0.1), mainPlayer.pos-vec2(0.1, 0.1)]
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.x += shift.x
        mainPlayer.pos.y -= shift.y
        playerHitbox = [mainPlayer.pos+vec2(0.1, 0.1), mainPlayer.pos+vec2(-0.1, 0.1), mainPlayer.pos-vec2(-0.1, 0.1), mainPlayer.pos-vec2(0.1, 0.1)]
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.y += shift.y
    if any(map(inPortalCheck, playerHitbox)):
        portal = int(mainPlayer.pos.y)*mapWidth + int(mainPlayer.pos.x)
        while any(map(inWallCheck, playerHitbox)):
            shift = vec2(random.random()*10-5, random.random()*10-5)
            mainPlayer.pos += shift
            if any(map(inWallCheck, playerHitbox)):
                mainPlayer.pos -= shift
        level = list(level)
        level[portal] = '.'
        level = ''.join(level)
    if level[int(mainPlayer.pos.y)*mapWidth + int(mainPlayer.pos.x)] == "'":
        noiselevel += 0.01 * elapsedTime
    else:
        noiselevel = 0
    if keyboard.is_pressed('a'): mainPlayer.angle -= 1.5 * elapsedTime
    if keyboard.is_pressed('d'): mainPlayer.angle += 1.5 * elapsedTime
    return elapsedTime
width = 128
height = 33
resmodifier = 2
while True:
    introMessage = f'Set resolution: {width*resmodifier}/{height*resmodifier}'
    stdscr.addstr(int(height*resmodifier/2), int((width*resmodifier-len(introMessage))/2), introMessage)
    if resmodifier==3: stdscr.addstr(int(height*resmodifier/2), int((width*resmodifier-len('Warning! max resolution is very unstable for some reason (probably skill issue)'))/2), 'Warning! max resolution is very unstable for some reason (probably skill issue)')
    stdscr.refresh()
    if (keyboard.is_pressed('Right') or keyboard.is_pressed('d')) and resmodifier<3: 
        resmodifier +=1
        os.system(f"mode con cols={width*resmodifier} lines={height*resmodifier}")
        sleep(0.5)
    if (keyboard.is_pressed('Left') or keyboard.is_pressed('a')) and resmodifier>0: 
        resmodifier -=1
        os.system(f"mode con cols={width*resmodifier} lines={height*resmodifier}")
        sleep(0.5)
    if keyboard.is_pressed('Enter'): break
width *= resmodifier
height *= resmodifier

#del stdscr
#curses.endwin()
os.system(f"mode con cols={width} lines={height}")
if height == 33: height*=2
sleep(1)
stdscr = curses.initscr()
curses.noecho()
#os.system("mode con cols=256 lines=66")
while True:
    #sleep(0.1)p
    #render(0, width)
    #for ny in range(mapHeight):
    #    for nx in range(mapWidth):
    #        frame[(ny+2)*width + nx] = level[ny * mapWidth + nx]
    #frame[(int(mainPlayer.pos.y+2)) * width + int(mainPlayer.pos.x)] = 'P'
    #frame = render(0, width)
    controlsResult = processControls()
    frame = render()
    stdscr.addstr(0, 0, ''.join(frame[:-1]))
    stdscr.addstr(0, 0, str(1/controlsResult))
    stdscr.refresh()
    #stdscr.addstr(0, 0, ''.join(frame[:-2]))
    #stdscr.addch(frame[-1])
    #stdscr.refresh()