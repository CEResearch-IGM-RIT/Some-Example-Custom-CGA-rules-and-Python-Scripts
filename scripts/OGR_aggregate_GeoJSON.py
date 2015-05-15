'''
Created on 15-05-2015

@author: GrzegorzKasza
'''

from scripting import *
import os
import sys
import re
import csv

# get a CityEngine instance
ce = CE()

#ścieżka systemowa do katalogu roboczego
tempdir = ce.toFSPath("scripts")+"/temp/"

def CreateTempDir():
    #tworzy katalog roboczy /temp/ jeśli nie istnieje
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    print 'Temp directory set'

def CleanTempDir():
    for files in ce.getObjectsFrom(tempdir, ce.isFile):
        ce.delete(files)
    print 'Temp directory cleaned'

def SetWorkGeometry():
    geometry = ce.getObjectsFrom(ce.selection())
    return geometry

def ConvertToGeoJSON(polygons):
    #pusta zmienna, którą będziemy zapełniać treścią w formacie GeoJSON; znak /n oznacza załamanie linii; już zawarta jest info o układzie współrzędnych (2000 zone 6)
    geometry_JSON ='{\n  "type": "FeatureCollection",\n  "crs": {\n    "type": "name",\n    "properties": {\n      "name": "urn:ogc:def:crs:EPSG::2177"\n      }\n    },\n  "features": [\n'    
    print len(polygons),"polygons selected"
    #iterujemy przez zaznaczone obiekty i każdy tłumaczymy na WKT
    for polygon in polygons:
        geometry_JSON +='    {\n      "type": "Feature",\n      "geometry": {\n        "type": "Polygon",\n        "coordinates": [['
        #zmienna zawierająca ilość wierzchołków geometrii 
        num_of_verts = (len(ce.getVertices(polygon))/3) 
        #zmienna zawierająca zbiór wierzchołków XYZ
        verts = ce.getVertices(polygon)    
        #iterujemy przez wierzchołki i odczytujemy tylko wartości X i Y, pomijamy Z
        for n in range(num_of_verts):            
            #formuła, która dla każdego n-tego wierzchołka bierze tylko współrzędną 1 i 3, pomijając 2 która jest wysokością
            x = ce.getVertices(polygon)[3*(n+1)-3]
            #x = round(x,2)
            #cityengine przechowuje współrzędną Y z minusem. Dla zgodności z szejpami zewnętrzymi trzeba przemnożyć przez -1. Uwaga: przy ładowaniu geometrii z powrotem do CityEngine trzeba przemnozyć przez -1 jeszcze raz
            y = ce.getVertices(polygon)[3*(n+1)-1]*(-1)
            #y = round(y,2)
            #dołączamy do zmiennej kolejno wspólrzędną x, spację, współrzędną y i przecinek
            geometry_JSON +="["
            geometry_JSON +=`x`
            geometry_JSON +=", "
            geometry_JSON +=`y`
            geometry_JSON +="], "
        #ucinamy ostatni przecinek i spację   
        geometry_JSON = geometry_JSON[:-2]
        #zamykamy geometrię dwoma nawiasami i zaczynamy część odpowiedzialną za atrybut
        geometry_JSON +=']]\n      },\n      "properties": {\n        "name": "'
        #atrybut zawierający numer porządkowy polugonu liczony od zera        
        #geometry_JSON += str(polygons.index(polygon))
        #atrybut zawierający kolumnę agregacji   
        geometry_JSON += '1'
        geometry_JSON +='"\n      }\n    },\n'    
    geometry_JSON += '  ]\n}'
    #ustalamy ścieżkę zapisu i nazwę pliku csv
    output = tempdir+"geometry_JSON.geojson"
    #otwieramy plik z prawami zapisu
    output_write = open(output, "w")
    #dodajemy do pliku zawartość zmiennej
    output_write.write(geometry_JSON)
    #zamykamy plik
    output_write.close()
    print 'saved JSON geometry as geoJSON'
    return output

def AggregateGeoJSON(input):    
    #ustalamy ścieżkę zapisu i nazwę pliku shp po agregacji
    output = tempdir+"geometry_agre.geojson"
    os.system("ogr2ogr -f GeoJSON -explodecollections "+output+" "+input+" -dialect sqlite -sql 'SELECT name,ST_Union(geometry) AS geometry FROM OGRGeoJSON GROUP BY name'")
    print 'Aggregation successfull'
    return output

if __name__ == '__main__':
    CreateTempDir()
    CleanTempDir()
    geometry = SetWorkGeometry()
    geometrygeojson = ConvertToGeoJSON(geometry)
    AggregateGeoJSON(geometrygeojson)
