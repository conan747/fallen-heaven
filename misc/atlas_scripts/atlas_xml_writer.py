__author__ = 'cos'


from lxml.etree import *
import os
from PIL import Image



def main():

    os.chdir("/media/cos/Programas/fife/fifengine/demos/experiments/")

    imageName = "isometric_grass_and_water.png"

    image = Image.open(imageName, 'r')
    imWidth, imHeight = image.size

    print "Image size: ", image.size

    tilewidth= 64
    tileheight= 64

    tileCountH = imWidth / tilewidth
    tileCountV = imHeight / tileheight
    print "Number of tiles in image: ", tileCountH , 'x', tileCountV
    nameSpace = "ground"

    # root = Element('fife', type="atlas")
    atlas = Element('atlas', name=imageName, namespace=nameSpace, width=str(imWidth), height=str(imHeight))

    tree = ElementTree(atlas)


    for row in range(tileCountV):
        for column in range(tileCountH):
            gid = str(row * tileCountH + column +1) # this +1 is so that we don't start from 0
            xPos = str(column * tilewidth)
            yPos = str(row * tileheight)
            
            # Add the image tag
            SubElement(atlas, 'image',
                       source=gid,
                       xpos = xPos,
                       ypos = yPos,
                       width = str(tilewidth),
                       height = str(tileheight))
            
            # Add the object tag
            obj = SubElement(root, 'object',
                       id = gid,
                       namespace = nameSpace,
                       blocking ="0",
                       static = "1",
                       area_id="land")
            #add the image to the object
            SubElement(obj, 'image',
                       source = gid,
                       direction = "45")



    # outFile =
    tree.write(open('gras_and_water_atlas.xml', 'w'), pretty_print = True, xml_declaration="fife")
    # outFile.close()



if __name__ == "__main__":
    main()