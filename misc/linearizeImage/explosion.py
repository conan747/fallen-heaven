#!/usr/bin/python2

__author__ = 'cos'

#from Pillow import Image
from PIL import Image


def main():
    filename = "explosion.png"
    rows = 4
    cols = 3
    originalIm = Image.open(filename, 'r')
    originalSize = originalIm.size
    cellsize = (originalSize[0]/cols, originalSize[1]/rows)
    print "Cell size: ", cellsize

    resultIm = Image.new("RGBA", (originalSize[0] * rows, cellsize[1]))

    for rowNum in range(rows):
        firstPoint = (0, cellsize[1]*rowNum)
        lastPoint = (originalSize[0], cellsize[1]*(rowNum+1))
        line = originalIm.crop(firstPoint + lastPoint)
        #line.show()

        resultIm.paste(line, (originalSize[0] * rowNum, 0))



    resultIm.save("out.png")


if __name__ == "__main__":
    main()