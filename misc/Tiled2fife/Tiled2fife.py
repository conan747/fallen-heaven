__author__ = 'cos'

from lxml.etree import *
import os


_CELL_CACHE = True # determines if the cell cache should be added.


def main():
    os.chdir("/media/cos/Programas/fife/fifengine/demos/experiments/")

    tileFile = "testAtlas.xml"
    nameSpace = "ground"
    fileName = tileFile.split(".")[0]

    tiledMap = ElementTree()
    tiledMap.parse(fileName + ".xml")
    root = tiledMap.getroot()

    mapElement = Element('map')
    fifeMap = ElementTree(mapElement)
    mapId = fileName
    mapDict = {"id": mapId,
               "format": "1.0"}
    [mapElement.set(key, mapDict[key]) for key in mapDict.keys()]

    imp = SubElement(mapElement, 'import', file=tileFile)

    # Start with the layers.
    allLayers = root.findall('layer')
    print "Number of layers in the parsed file: ", len(allLayers)

    layerAttibs = {"id": "",
                   "x_offset": "0.000000",
                   "y_offset": "0.000000",
                   "z_offset": "0.000000",
                   "x_scale": "1.000000",
                   "y_scale": "1.000000",
                   "rotation": "0.000000",
                   "grid_type": "square",
                   "transparency": "0",
                   "pathing": "cell_edges_and_diagonals",
                   "sorting": "camera",
                   "layer_type": "interact",
                   "layer_type_id": "TechdemoMapGroundObjectLayer"}

    cellCaches = SubElement(mapElement, 'cellcaches')

    for layer in allLayers:
        layerAttibs["id"] = layer.attrib["name"]
        mapLayer = SubElement(mapElement, 'layer')
        [mapLayer.set(key, layerAttibs[key]) for key in layerAttibs.keys()]

        # instances
        instancesEl = SubElement(mapLayer, 'instances')
        print "Number of instances for this layer", len(layer[0])
        dataList = layer[0]
        xMax = int(layer.attrib["width"])
        yMax = int(layer.attrib["height"])
        print "Size of the layer: ", xMax, "x", yMax

        if _CELL_CACHE:
            cellCache = SubElement(cellCaches, 'cellcache',
                                   id=layer.attrib["name"],
                                   default_cost="1.0",
                                   default_speed="1.0",
                                   search_narrow="1")

        for x in range(xMax):
            for y in range(yMax):
                item = dataList[x + y * xMax]
                SubElement(instancesEl, 'i',
                           ns=nameSpace,
                           o=item.attrib["gid"],
                           x=str(x - xMax / 2),
                           y=str(y - yMax / 2),
                           z="0.0",
                           r="0",
                           stackpos="0")
                if _CELL_CACHE:
                    SubElement(cellCache, 'cell',
                               x=str(x - xMax / 2),
                               y=str(y - yMax / 2)
                    )

    layerName = allLayers[0].attrib["name"]
    # Add a camera:
    SubElement(mapElement, 'camera',
               id="main",
               ref_layer_id=layerName,
               zoom="1",
               tilt="-60",
               rotation="-45.000000",
               viewport="0,0,1024,768",
               ref_cell_width="64",
               ref_cell_height="32")

    fifeMap.write(open('fifeMap.xml', 'w'), pretty_print=True, xml_declaration=True)


if __name__ == "__main__":
    main()