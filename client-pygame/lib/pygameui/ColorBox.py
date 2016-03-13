from pygame.locals import *
from Const import *
from Widget import Widget, registerWidget

class ColorBox(Widget):

	def __init__(self, parent, **kwargs):
		Widget.__init__(self, parent)
		# data
		self.color = None
		self.margins = (0, 0, 0, 0)
		# flags
		self.processKWArguments(kwargs)
		parent.registerWidget(self)

	def draw(self, surface):
		oldClip = surface.get_clip()
		surface.set_clip(self.rect.left + self.margins[0], self.rect.top + self.margins[1], 
		                 self.rect.width - self.margins[2] - self.margins[0], self.rect.height - self.margins[3] - self.margins[1])
		surface.fill(self.color)
		surface.set_clip(oldClip)
		return self.rect

registerWidget(ColorBox, 'colorbox')
