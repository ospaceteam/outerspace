#
#  Copyright 2001 - 2006 Ludek Smid [http://www.ospace.net/]
#
#  This file is part of Pygame.UI.
#
#  Pygame.UI is free software; you can redistribute it and/or modify
#  it under the terms of the Lesser GNU General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
#  Pygame.UI is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  Lesser GNU General Public License for more details.
#
#  You should have received a copy of the Lesser GNU General Public License
#  along with Pygame.UI; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#

from distutils.core import setup
import py2exe

setup(
	name='Pygame.UI',
	version='0.4',
	description = 'Pluggable GUI library for Pygame.',
	maintainer = 'Ludek Smid',
	maintainer_email = 'qark@seznam.cz',
	url = 'http://www.ospace.net/',
	packages =['pygameui', 'pygameui.demo'],
	data_files = [
		['pygameui/demo', ['pygameui/demo/img.png', 'pygameui/demo/reddot.png']],
		['pygameui', ['pygameui/LICENSE.txt', 'pygameui/README.txt']],
	],
)
