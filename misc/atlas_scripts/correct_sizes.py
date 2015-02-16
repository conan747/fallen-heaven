__author__ = 'cos'

import os
from glob import glob
from PIL import Image





def main():
    xmlFiles = glob("../../objects/agents/units/*.xml")

    for xmlFile in xmlFiles:
        pngFile = xmlFile.replace(".xml", ".png")
        if os.path.isfile(pngFile):
            print pngFile , "exists!"
            img = Image.open(pngFile, 'r')
            # img.open(pngFile)
            print img.size

            xml = open(xmlFile, 'r')
            xmlText = xml.readlines()
            xml.close()

            newXML = []
            for line in xmlText:
                if line.__contains__('height="96"'):
                    line = line.replace('height="96"', 'height="' + str(img.size[1]) + '"')

                if line.__contains__('width="96"'):
                    line = line.replace('width="96"', 'width="' + str(img.size[0]) + '"')

                if line.__contains__("dir="):
                    if line.split("dir=")[1][1] != "0":
                        line = ""

                newXML.append(line)

            xml = open(xmlFile, 'w')
            xml.writelines(newXML)
            xml.close()










if __name__ == "__main__":
    main()