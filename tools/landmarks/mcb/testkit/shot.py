import sys
from PIL import ImageGrab
im = ImageGrab.grab(xdisplay=":99")
im.save(sys.argv[1]); print(im.size)
