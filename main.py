# REMEMBER - this code shouldnt be used as a tutorial
# it is very buggy, has random solutions, and i wrote this with little to no experience in game developing
import os
import random
import keyboard
from enum import Enum
from math import sin, cos
from PIL import Image
from time import sleep
from time import time
import ctypes

#frame settings, not recommended to change
width = 256
height = 66
aspect = width/height
#symbols are not entirely square, so i calculated that they are 11x24 pixels in size
pixelaspect = 11/24
#creating the frame buffer
frame = list(' '*(width * height))

#setting the console
os.system("@echo off")
os.system("mode con cols={width} lines={height}")
os.system("title Backrooms")


# using fast print library that my friend has made for me (because curses sucks)
lib = ctypes.CDLL("./libs/fastprint.dll")
print_ = getattr(lib, "print")
gethandle = getattr(lib, "createConsoleHandle")


# initial variables
work = True # set loop to active, when it becomes false - the program stops
t = 0 # timer variable

#width and height of the map, i was too lazy to get it from image
mapWidth = 101 
mapHeight = 101

#get time to make movement speed independent from the framerate
t1 = time()
t2 = time()



#definitely did not stole vec2 from stackoverflow
# UPDATE: i stole only 50% of it
# UPDATE 2: ok, i'll try to explain what it does

class vec2:
    # mainly operator overload
    # init class
    def __init__(self, x, y):
        self.x = x
        self.y = y
    # not an actual vector division (it does not exist), but convenient for usage
    def __truediv__(self, other):
        return vec2(self.x/other.x, self.y/other.y)

    # not an actual vector multiplication, but convenient for usage
    def __mul__(self, other):
        return vec2(self.x*other.x, self.y*other.y)

    # why not, __repr__ and __str__ for debug
    def __repr__(self):
        return 'vec2({}, {})'.format(self.x, self.y)

    def __str__(self):
        return '({}, {})'.format(self.x, self.y)

    # in vector math, a(ax, ay) + b(bx, by) = c(ax+bx, ay+by)
    def __add__(self, other):
        return vec2(self.x + other.x, self.y + other.y)

    # same, but for a(ax,ay)+= b(bx,by)
    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        return self

    # kinda obvious, but in vector math, a(ax, ay) - b(bx, by) = c(ax-bx, ay-by)
    def __sub__(self, other):
        return vec2(self.x - other.x, self.y - other.y)
    # same, but for a(ax,ay)+= b(bx,by)
    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        return self

    # |a| = sqrt(ax**2 + ay**2)
    def __abs__(self):
        return (self.x**2+self.y**2)**0.5

    #absolutely not needed, but why not
    def __bool__(self):
        return self.x != 0 or self.y != 0

    # -a(ax, ay) = a(-ax, -ay)
    def __neg__(self):
        return vec2(-self.x, -self.y)

# get gradient from brightness
def getColor(x: int, gradientmode=None) -> str:
    if gradientmode is None: gradientmode = 0
    # 2 types of gradient, one for walls and one for floor
    gradient = ' .:!/r(;14HZ9W8$@'
    shortgradient = ' -~=x'
    # min(max(x, a),b) clamps x between a and b (if x<a returns a, if x>b returns b, else returns x)
    if gradientmode == 0: return gradient[min(max(x, 0), len(gradient)-1)]
    if gradientmode == 1: return shortgradient[min(max(x, 0), len(shortgradient)-1)]
def drawImage(img: Image):
    #set frame from external png
    img = img.convert('L')
    image = list(' '*(width * height))
    if not img.size == (width, height): img = img.resize((width, height))
    for i in range(width):
        for j in range(height):
            brightness = img.getpixel((i, j)) / 255 * 17 #17 because of gradient lengh
            pixel = getColor(int(brightness))
            image[i+j*width] = pixel
    return image
def loadLevel(img: Image):
    #load level from image
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
level = loadLevel(Image.open('assets/maze.png'))

class Player:
    def __init__(self, pos: vec2, angle, fov=3.1415926535897/3, renderDistance=16, size=0.1, speed=1, stamina=2):
        self.pos = pos
        self.fov = fov
        self.angle = angle
        self.renderDistance = renderDistance
        self.size = size
        self.speed = speed
        self.stamina = stamina
mainPlayer = Player(vec2(1.5,1.5), 0, 3.1415926535897 / 3, 16)
stamina = 1
noiselevel = 0

walls = {
    '#' : "walls/basic.png",
    '@' : "walls/bricks.png",
    '0' : "walls/finale.png"
    }
def textureToList(img):
    wallTexture = list(' '*1024)
    for i in range(32):
        for j in range(32):
            wallTexture[(j<<5)+i] = img.getpixel((i, j)) / 255
    return wallTexture
wallTextures = {key:textureToList(Image.open('assets/' + value).convert('L')) for (key,value) in walls.items()}


def getTexture(x, y, wallType):
    global wallTextures
    try: wallTextures[wallType]
    except KeyError: return 0
    wallColor = wallTextures[wallType][int(x*32)+(int(y*32))]
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
                distanceToWall-=0.049
                while not hitWall:
                    distanceToWall += 0.001
                    testX = int(startPos.x + eye.x*distanceToWall)
                    testY = int(startPos.y + eye.y*distanceToWall)
                    if level[int(testY*mapWidth+testX)] in wallTextures or testX >= mapWidth or testY >= mapHeight or testX < 0  or testY < 0:
                        distanceToWall-=0.00009
                        while not hitWall:
                            distanceToWall += 0.00001
                            testX = int(startPos.x + eye.x*distanceToWall)
                            testY = int(startPos.y + eye.y*distanceToWall)
                            if level[int(testY*mapWidth+testX)] in wallTextures or testX >= mapWidth or testY >= mapHeight or testX < 0  or testY < 0: hitWall = True
            elif level[int(testY*mapWidth+testX)] == ',': 
                hitWall = True
                hitPortal = True
        self.lengh = distanceToWall
        self.hitFlags =  (hitPortal<<1) + hitWall
        self.wallObject = level[int(testY*mapWidth+testX)]
        self.endPoint = vec2(startPos.x + eye.x*distanceToWall, startPos.y + eye.y*distanceToWall)
def render(frame):
    global width
    global height
    global mainPlayer
    global mapWidth
    global mapHeight
    global noiselevel
    halfScreenConst = height/2
    widthFovConst = width / mainPlayer.fov
    centerAngleConst = (mainPlayer.angle - mainPlayer.fov/2)
    for x in range(width):
        rayAngle = centerAngleConst + x / widthFovConst
        ray = Ray(mainPlayer.pos, rayAngle, mainPlayer.renderDistance)
        ProjectionDistance = ray.lengh * cos(mainPlayer.angle - rayAngle)
        ceiling = halfScreenConst-height/ProjectionDistance
        floor = height - ceiling
        Shade = 1-max(min(ray.lengh/mainPlayer.renderDistance,1),0)
        if noiselevel: Shade+=noiselevel*random.random()
        Shade *= 17
        if not ray.hitFlags & 0b1: Shade = 0
        textureX = (ray.endPoint.x+ray.endPoint.y)%1
        mapConst = (height-ceiling*2)/32
        for y in range(height):
            if y <= ceiling:
                b = 1-y/halfScreenConst # (height/2-y) / (height/2) but optimised
                pixel = getColor(int(b*5), 1)
                frame[y*width + x] = pixel
            elif y > ceiling and y <= floor:
                frame[y*width + x] = getColor(int(Shade*((getTexture(textureX, int((y-ceiling)/mapConst), ray.wallObject)))))
            else:
                b = y/halfScreenConst-1 # (y - height/2) / (height/2) but optimised
                pixel = getColor(int(b*5), 1)
                frame[y*width + x] = pixel
    return frame


def processControls():
    global noiselevel
    global mainPlayer
    global t1, t2
    global level
    global wallTextures
    movementKeys = {
        'forward': keyboard.is_pressed('w'),
        'backward': keyboard.is_pressed('s'),
        'left': keyboard.is_pressed('a'),
        'right': keyboard.is_pressed('d')
    }
    t2 = time()
    elapsedTime = (t2 - t1)
    t1 = t2
    if any(movementKeys) and keyboard.is_pressed('shift'):
        mainPlayer.speed = 1 + mainPlayer.stamina
        mainPlayer.stamina -= 0.2 * elapsedTime
    else: 
        mainPlayer.stamina += 0.15 * elapsedTime
        mainPlayer.speed = 1
    mainPlayer.stamina = min(max(mainPlayer.stamina, 0), 2)
    def inWallCheck(pos): return level[int(pos.y)*mapWidth + int(pos.x)] in wallTextures
    def inPortalCheck(pos): return level[int(pos.y)*mapWidth + int(pos.x)] == ','
    def getHitbox():
        return [mainPlayer.pos+vec2(mainPlayer.size, mainPlayer.size), mainPlayer.pos+vec2(-mainPlayer.size, mainPlayer.size), mainPlayer.pos-vec2(-mainPlayer.size, mainPlayer.size), mainPlayer.pos-vec2(mainPlayer.size, mainPlayer.size)]
    playerHitbox = getHitbox()
    if movementKeys['forward']:
        shift = vec2(sin(mainPlayer.angle) * elapsedTime * mainPlayer.speed, cos(mainPlayer.angle) * elapsedTime * mainPlayer.speed)
        mainPlayer.pos.x += shift.x
        playerHitbox = getHitbox()
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.x -= shift.x
        mainPlayer.pos.y += shift.y
        playerHitbox = getHitbox()
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.y -= shift.y
    if movementKeys['backward']: 
        shift = vec2(sin(mainPlayer.angle) * elapsedTime * mainPlayer.speed, cos(mainPlayer.angle) * elapsedTime * mainPlayer.speed)
        mainPlayer.pos.x -= shift.x
        playerHitbox = getHitbox()
        if any(map(inWallCheck, playerHitbox)):
            mainPlayer.pos.x += shift.x
        mainPlayer.pos.y -= shift.y
        playerHitbox = getHitbox()
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
    if movementKeys['left']: mainPlayer.angle -= 1.5 * elapsedTime
    if movementKeys['right']: mainPlayer.angle += 1.5 * elapsedTime
    return elapsedTime

sleep(1)
handle = gethandle()
while True:
    frame = render(frame)
    controlsResult = int(1/processControls())
    displaystamina = list('Stamina: '+str(round(mainPlayer.stamina, 3)))
    displayfps = list('FPS: '+str(controlsResult))
    frame[:len(displayfps)] = displayfps
    frame[width:width+len(displaystamina)] = displaystamina
    print_(''.join(frame), width, height, handle)
