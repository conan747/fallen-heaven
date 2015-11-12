#!/usr/bin/python2

__author__ = 'cos'

import xml.etree.ElementTree as ET
import sys
import glob

def main(arg):
    template = "Buggy.xml"

    with open(template, 'r') as text:
        initLine = text.readline()

    templateTree = ET.parse(template)
    templateRoot = templateTree.getroot()
    print templateRoot
    for el in templateRoot.findall("action"):
        if el.get("id") == "explode":
            explodeElement = el

    xmls = glob.glob("*.xml")

    for xml in xmls:
        if xml == template:
            continue

        tree = ET.parse(xml)
        root = tree.getroot()
        hasExplode = False
        for el in root.findall("action"):
            if el.get("id") == "explode":
                hasExplode = True

        if hasExplode:
            print xml, "already has explode."
            continue

        # IF we got here we should add the explodeElement
        root.append(explodeElement)
        tree.write(xml, xml_declaration="object")
        print "Writing ", xml
        with open(xml, 'r') as xmlFile:
            text = xmlFile.readlines()

        newText = [initLine] + text
        open(xml, 'w').writelines(newText)






if __name__ == "__main__":
    main(sys.argv)