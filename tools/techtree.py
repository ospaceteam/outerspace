# setup library path
import sys
sys.path.append("../server/lib")

# install i18n helpers
def N_(text):
    return text
sys.modules["__builtin__"].N_ = N_

# constants
#foreground = 0x30, 0xe0, 0x30, 0x00
#background = 0x20, 0x40, 0x20, 0x00
#screenbg = 0x00, 0x00, 0x00, 0x00

# white style
#foreground = 0x00, 0x00, 0x00, 0x00
#background = 0xff, 0xff, 0xff, 0x00
#screenbg = 0xff, 0xff, 0xff, 0x00

# os web style
foreground = 0xff, 0xff, 0xff
#hForeground = 0xff, 0xff, 0x55
hForeground = 0xff, 0xff, 0xce
disablesForeground = 0xff, 0xff, 0x55
#disablesForeground = 0xc0, 0xff, 0xc0
background = 0x3d, 0x7a, 0x99
screenbg = 0x2d, 0x5a, 0x71

tl2color = {
    1: (255, 128, 64),  #orange
    2: (255, 255, 128), #yellow
    3: (128, 255, 0),   #green
    4: (0, 128, 255),   #blue
    5: (196, 0, 255),   #purple
    6: (196, 0, 0),     #red
}

stratRes = {
	0: "None",
	1: "Ur",
	2: "Ti",
	3: "Chrom",
	4: "Silic",
	5: "Carb",
	6: "Anti",
	7: "Plut",
	8: "Wolf",
	100: "Mutagen",
	1000: "Unnilseptium"
}

race2Name = {
    "B": "Bionic",
    "C": "Cyborg",
    "H": "Human",
}

# imports
from ige.ospace import Rules, TechHandlers

import pygame
from pygame.locals import *

def getDescription(tech):
    suffix = ""
    if tech.researchReqSRes:
        srList = []
        for sres in tech.researchReqSRes:
            srList.append(stratRes[sres])
        suffix += " [%s]" % (", ".join(srList))
    if tech.researchRaces != "BCH":
        rList = []
        for race in tech.researchRaces:
            rList.append(race2Name[race])
        suffix += " (%s)" % (", ".join(rList))
    if tech.finishResearchHandler == TechHandlers.finishResTLAdvance:
        suffix += " <TL%d>" % (tech.level + 1)
    return "%s%s" % (
        tech.name,
        suffix,
    )

def getMinSize(tech):
    font = pygame.font.Font("Vera.ttf", 13)
    w, h = font.size(getDescription(tech))
    return w + 6 + 12, h + 6

def renderNode(tech, width, height):
    surface = pygame.Surface((width, height))
    font = pygame.font.Font("Vera.ttf", 13)
    surface.fill(foreground)
    surface.fill(background, (1, 1, width - 2, height - 2))
    # TL label
    color = tl2color[tech.level]
    surface.fill(color, (1, 1, 12, height - 2))
    font.set_bold(1)
    text = font.render(str(tech.level), 1, (0x00, 0x00, 0x00))
    surface.blit(text, (2 + (12 - text.get_width()) / 2, (height - text.get_height()) / 2))
    # tech name
    font.set_bold(0)
    if tech.researchDisables:
        text = font.render(getDescription(tech), 1, disablesForeground)
    elif tech.researchRaces != "BCH":
        text = font.render(getDescription(tech), 1, hForeground)
    else:
        text = font.render(getDescription(tech), 1, foreground)
    surface.blit(text, (15, (height - text.get_height()) / 2))
    return surface

def getParent(tech):
    if tech.researchRequires:
        return Rules.techs[tech.researchRequires[0][0]]
    else:
        return None

def getChildren(tech):
    return tech.researchEnables[1] + tech.researchEnables[2] + tech.researchEnables[3] + \
        tech.researchEnables[4] + tech.researchEnables[5]

# layout the tree
class Grid:

    def __init__(self, honorTL = False):
        self.grid = {}
        self.honorTL = honorTL
        self.newRootRow = 0

    def addRoot(self, tech):
        if self.honorTL:
            self.grid[self.newRootRow, tech.level - 1] = tech
        else:
            self.grid[self.newRootRow, 0] = tech
        self.newRootRow += 1
        return

    def addChild(self, child):
        # find parent
        parent = getParent(child)
        found = False
        for parentR, parentC in self.grid:
            if self.grid[parentR, parentC] == parent:
                found = True
                break
        assert found
        # find first cell empty right to the parent or occupied by non-child
        childC = parentC + 1
        maxR, maxC = self.getMaxRowCol()
        for childR in range(parentR, maxR + 2):
            if (childR, childC) in self.grid:
                if parent != getParent(self.grid[childR, childC]):
                    break
            else:
                break
        # move everyting down if space is needed
        if parentR != childR:
            maxR, maxC = self.getMaxRowCol()
            for r in range(maxR + 1, childR - 1, -1):
                for c in range(0, maxC + 1):
                    if (r, c) in self.grid:
                        self.grid[r + 1, c] = self.grid[r, c]
                        del self.grid[r, c]
        # find suitable column for this tech's TL
        found = False
        while not found and self.honorTL:
            found = True
            for r in range(0, maxR + 1):
                if (r, childC) in self.grid and self.grid[r, childC].level < child.level:
                    childC += 1
                    found = False
                    break
        self.grid[childR, childC] = child
        # if anything in this column is on higher TL than child,
        # move all techs on tl > child.tech to the right
        move = False
        maxR, maxC = self.getMaxRowCol()
        for r in range(0, maxR + 1):
            if (r, childC) in self.grid and self.grid[r, childC].level > child.level:
                move = True
        if move and self.honorTL:
            for r in range(0, maxR + 1):
                for c in range(maxC, childC - 1, -1):
                    if (r, c) in self.grid and self.grid[r, c].level > child.level:
                        self.grid[r, c + 1] = self.grid[r, c]
                        del self.grid[r, c]

    def getMaxRowCol(self):
        maxR = 0
        maxC = 0
        for row, col in self.grid:
            maxR = max(row, maxR)
            maxC = max(col, maxC)
        return maxR, maxC

    def printAscii(self):
        maxR, maxC = self.getMaxRowCol()
        print maxR, maxC, "LAYOUT"
        for r in range(0, maxR + 1):
            for c in range(0, maxC + 1):
                if (r, c) in self.grid:
                    name = self.grid[r, c].name
                else:
                    name = "-----"
                print "%-10s " % name,
            print

    def printSDL(self):
        # grid config
        lSpace = 12
        padx = 1
        pady = 1
        font = pygame.font.Font(None, 14)
        #
        maxR, maxC = self.getMaxRowCol()
        # get size of the grid
        width = height = 0
        for r in range(0, maxR + 1):
            for c in range(0, maxC + 1):
                if (r, c) in self.grid:
                    w, h = getMinSize(self.grid[r, c])
                    width = max(width, w)
                    height = max(height, h)
        gWidth = width + 2 * padx + lSpace
        gHeight = height + 2 * pady
        # grid surface
        gSurface = pygame.Surface(((maxC + 1) * gWidth, (maxR + 1) * gHeight))
        gSurface.fill(screenbg)
        # draw tree
        for r in range(0, maxR + 1):
            for c in range(0, maxC + 1):
                if (r, c) in self.grid:
                    node = self.grid[r, c]
                    nodeSurf = renderNode(node, width, height)
                    gSurface.blit(nodeSurf, (c * gWidth, r * gHeight))
                    # get parent
                    parent = getParent(node)
                    if parent:
                        found = False
                        for pR, pC in self.grid:
                            if self.grid[pR, pC] == parent:
                                found = True
                                break
                        assert found
                        # check if cell above has the same parent
                        if (r - 1, c) in self.grid and getParent(self.grid[r - 1, c]) == parent:
                            # draw the line to the sibling above
                            # draw the line to the parent
                            pygame.draw.lines(gSurface, foreground, 0,
                                (
                                    ((c - 1) * gWidth + width + lSpace / 2, (r - 1) * gHeight + gHeight / 2),
                                    ((c - 1) * gWidth + width + lSpace / 2, r * gHeight + gHeight / 2),
                                    (c * gWidth, r * gHeight + gHeight / 2),
                                ),
                            )
                        else:
                            # draw the line to the parent
                            pygame.draw.lines(gSurface, foreground, 0,
                                (
                                    (pC * gWidth + width, pR * gHeight + gHeight / 2),
                                    (pC * gWidth + width + lSpace / 2, pR * gHeight + gHeight / 2),
                                    (pC * gWidth + width + lSpace / 2, r * gHeight + gHeight / 2),
                                    (c * gWidth, r * gHeight + gHeight / 2),
                                ),
                            )
                        # improvement requiremt
                        impr = node.researchRequires[0][1]
                        text = font.render(str(impr), 1, foreground)
                        gSurface.blit(text, (c * gWidth - text.get_width() - 1, r * gHeight))
        return gSurface

def waitForKey():
    while 1:
        evt = pygame.event.wait()
        if evt.type == KEYUP:
            break

#initialize SDL and prepare screen
pygame.init()
screen = pygame.display.set_mode((1000, 800), SWSURFACE, 32)
pygame.mouse.set_visible(1)
pygame.display.set_caption('Tech tree')

# process tree
grid = Grid(False)

# layout roots
for tl in range(1, 10):
    for tech in Rules.techs.itervalues():
        if tech.researchRequires or tl != tech.level or tech.level >= 99 or \
            1000 in tech.researchReqSRes:
            continue
        # this is a root
        print "Laying out TL", tech.level, "ROOT", tech.name
        grid.addRoot(tech)

#screen.blit(grid.printSDL(), (0, 0))
#pygame.display.update()

# layout children
for tech in Rules.techs.itervalues():
    if tech.researchRequires:
        continue
    # this is a root
    print "Processing TL", tech.level, "ROOT", tech.name
    # find it's children
    todo = getChildren(tech)
    # process them
    while todo:
        current = Rules.techs[todo.pop(0)]
        if current.level >= 99 or 1000 in current.researchReqSRes:
            print "   skipping", current.name
            continue
        print "   ...", current.name
        # lay it out
        grid.addChild(current)
        # display
        #screen.blit(grid.printSDL(), (0, 0))
        #pygame.display.update()
        # add it's children
        todo.extend(getChildren(current))

screen.blit(grid.printSDL(), (0, 0))
pygame.display.update()

pygame.image.save(grid.printSDL(), "techtree.bmp")
#waitForKey()
