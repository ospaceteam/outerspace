#!/usr/bin/env python2
#
#  Copyright 2001 - 2018 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Outer Space.
#
#  Outer Space is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  Outer Space is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Outer Space; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

# setup library path
import sys
sys.path.append("../server/lib")

# install i18n helpers
def N_(text):
    return text
sys.modules["__builtin__"].N_ = N_

FONT_TYPE = "Vera.ttf"
FONT_SIZE = 13

# os web style
foreground = 0xff, 0xff, 0xff
hForeground = 0xff, 0xff, 0xce
disablesForeground = 0xff, 0xff, 0x55
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
    "m": "Mutant",
    "r": "Renegade",
    "e": "EDEN",
    "p": "Pirate",
}

import os
from optparse import OptionParser

# parse command line arguments (needs to be first, so we have configDir ready when importing)
parser = OptionParser()
parser.add_option("",  "--configdir", dest = "configDir",
    metavar = "DIRECTORY", default = os.path.join(os.path.expanduser("~"), ".outerspace"),
    help = "Override default configuration directory",)

options, args = parser.parse_args()


# imports
import ige.ospace.Rules as Rules
Rules.init(options.configDir)

import ige.ospace.TechHandlers as TechHandlers
import pygame
import pygame.locals


class Node(object):
    def __init__(self, parent, tech):
        self.parent = parent
        self.tech = tech
        self.children = []
        self.final_row = None
        self.final_column = None

    @property
    def subtree_row(self):
        if self.children:
            return sum(map(lambda x: x.subtree_row, self.children))
        else:
            return 1

    def _child_row_offset(self, child):
        offset = 0
        for child_ in self.children:
            if child_ == child:
                return offset
            offset += child_.subtree_row
        return offset

    def row_offset(self, child=None):
        offset = self.parent.row_offset(self)

        if child is None:
            return offset
        return offset + self._child_row_offset(child)

    @property
    def row(self):
        if self.final_row is None:
            return self.row_offset()
        return self.final_row

    @property
    def column(self):
        if self.final_column is None:
            return 1 + max(self.parent.column, self.tl_offset_query(self.tech.level) - 1)
        return self.final_column

    def finalize(self):
        self.final_column = self.column
        self.final_row = self.row

    def tl_offset(self, tl):
        if self.tech.level > tl:
            return 0
        if self.children:
            child_offset = max(map(lambda x: x.tl_offset(tl), self.children))
        else:
            child_offset = 0
        if self.tech.level == tl:
            return 1 + child_offset
        else:
            return child_offset

    def tl_offset_query(self, tl):
        return self.parent.tl_offset_query(tl)

    def insert(self, tech):
        parent_id = tech.researchRequires[0][0]
        if self.tech and self.tech.id == parent_id:
            for child in self.children:
                if tech == child.tech:
                    return True
            self.children.append(Node(self, tech))
            return True
        elif not self.children:
            return False
        for child in self.children:
            if child.insert(tech):
                return True
        return False

    def __repr__(self):
        return str((self.tech.name, self.row, self.column))

class RootNode(Node):
    def __init__(self):
        super(RootNode, self).__init__(None, None)

    @property
    def column(self):
        return -1

    def row_offset(self, child=None):
        offset = 0
        if child is None:
            return offset
        return offset + self._child_row_offset(child)

    def tl_offset(self, tl):
        if self.children:
            return max(map(lambda x: x.tl_offset(tl), self.children))
        else:
            return 0

    def tl_offset_query(self, tl):
        offset = 0
        for i in range(1, tl):
            offset += self.tl_offset(i)
        return offset

    def insert(self, tech):
        try:
            parent_id = tech.researchRequires[0][0]
        except IndexError:
            self.children.append(Node(self, tech))
            return True
        super(RootNode, self).insert(tech)

    def __repr__(self):
        return "---ROOT---"

class Grid(object):
    def __init__(self):
        self.root = RootNode()

    def add_node(self, tech):
        self.root.insert(tech)

    def get_max_size(self):
        max_column = 0
        max_row = 0
        for node in self.get_list():
            max_column = max(max_column, node.column)
            max_row = max(max_row, node.row)
        return max_column, max_row

    def get_list(self):
        old_list = None
        new_list = self.root.children[:]
        while old_list != new_list:
            old_list = new_list[:]
            for node in old_list:
                for child in node.children:
                    if child not in new_list:
                        new_list.append(child)
        return new_list
    
    def print_ascii(self):
        print(len(self.get_list()), self.get_list())

    def cell_size(self, node):
        font = pygame.font.Font(FONT_TYPE, FONT_SIZE)
        w, h = font.size(self.get_description(node.tech))
        return w + 6 + 12, h + 6

    def get_description(self, tech):
        suffix = ""
        if tech.researchReqSRes:
            srList = []
            for sres in tech.researchReqSRes:
                srList.append(stratRes[sres])
            suffix += " [%s]" % (", ".join(srList))
        if set(tech.researchRaces) < set("BCH"):
            rList = []
            for race in tech.researchRaces:
                if race not in "BCH":
                    continue
                rList.append(race2Name[race])
            suffix += " (%s)" % (", ".join(rList))
        if tech.finishResearchHandler == TechHandlers.finishResTLAdvance:
            suffix += " <TL%d>" % (tech.level + 1)
        return "%s%s" % (
            tech.name,
            suffix,
        )

    def render_node(self, tech, width, height):
        surface = pygame.Surface((width, height))
        font = pygame.font.Font(FONT_TYPE, FONT_SIZE)
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
            text = font.render(self.get_description(tech), 1, disablesForeground)
        elif tech.researchRaces != "BCH":
            text = font.render(self.get_description(tech), 1, hForeground)
        else:
            text = font.render(self.get_description(tech), 1, foreground)
        surface.blit(text, (15, (height - text.get_height()) / 2))
        return surface

    def print_SDL(self):
        # grid config
        blank_space = 12
        padx = 1
        pady = 1
        font = pygame.font.Font(None, 14)
        #
        max_column, max_row = self.get_max_size()
        # get size of the grid
        width = height = 0
        for node in self.get_list():
            w, h = self.cell_size(node)
            width = max(width, w)
            height = max(height, h)
        node_width = width + 2 * padx + blank_space
        node_height = height + 2 * pady
        # grid surface
        surface = pygame.Surface(((max_column + 1) * node_width, (max_row + 1) * node_height))
        surface.fill(screenbg)
        # draw tree
        for node in self.get_list():
            node_surface = self.render_node(node.tech, width, height)
            surface.blit(node_surface, (node.column * node_width, node.row * node_height))
            parent = node.parent
            if parent.tech is None:
                continue
            pygame.draw.lines(surface, foreground, 0,
                (
                    (parent.column * node_width + width, parent.row * node_height + node_height / 2),
                    (parent.column * node_width + width + blank_space / 2, parent.row * node_height + node_height / 2),
                    (parent.column * node_width + width + blank_space / 2, node.row * node_height + node_height / 2),
                    (node.column * node_width, node.row * node_height + node_height / 2),
                ),
            )
            # improvement requiremt
            try:
                impr = node.tech.researchRequires[0][1]
                text = font.render(str(impr), 1, foreground)
                surface.blit(text, (node.column * node_width - text.get_width() - 1, node.row * node_height))
            except IndexError:
                continue
        return surface

def useful_tech(tech, races):
    return "#" not in tech.researchRaces and tech.level <= 6 and set(races) & set(tech.researchRaces)

def add_techs(grid, techs):
    old_size = 0
    new_size = len(grid.get_list())
    while old_size != new_size:
        old_size = new_size
        for tech in techs[:]:
            if not tech.researchRequires:
                techs.remove(tech)
                continue
            if tech.researchRequires:
                if grid.add_node(tech):
                    techs.remove(tech)
        new_size = len(grid.get_list())

def techtree(filename, races):
    # process tree
    grid = Grid()
    techs = [tech for tech in list(Rules.techs.itervalues()) if useful_tech(tech, races)]
    techs = sorted(techs, key=lambda x: x.level)
    # adding roots
    for tech in techs:
        if not tech.researchRequires:
            grid.add_node(tech)

    # adding the rest (by tech levels, so visually, it looks sorted (cascading effect))
    for tl in range(1, 7):
        tl_techs = [tech for tech in techs if tech.level == tl]
        add_techs(grid, tl_techs)

    grid.root.finalize()
    for node in grid.get_list():
        node.finalize()

    pygame.image.save(grid.print_SDL(), filename + ".png")

pygame.init()
techtree("techtree", "BCH")
techtree("techtree_bionic", "B")
techtree("techtree_cyborg", "C")
techtree("techtree_human", "H")
techtree("techtree_mutant", "m")
techtree("techtree_renegade", "r")
