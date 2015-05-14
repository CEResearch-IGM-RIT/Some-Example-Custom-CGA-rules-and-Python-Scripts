'''
Created on 14-05-2015

@author: kaszagrzegorz
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

def ConvertToWKT(polygons):    
    #pusta zmienna, którą będziemy zapełniać listą wierzchołków w formacie WKT. znak /n oznacza załamanie linii
    geometry_WKT ='WKT,\n'    
    print len(polygons),"polygons selected"
    #iterujemy przez zaznaczone obiekty i każdy tłumaczymy na WKT
    for polygon in polygons:
        geometry_WKT +='"POLYGON (('
        #zmienna zawierająca ilość wierzchołków geometrii 
        num_of_verts = (len(ce.getVertices(polygon))/3) 
        #zmienna zawierająca zbiór wierzchołków XYZ
        verts = ce.getVertices(polygon)    
        #iterujemy przez wierzchołki i odczytujemy tylko wartości X i Y, pomijamy Z
        for n in range(num_of_verts):            
            #formuła, która dla każdego n-tego wierzchołka bierze tylko współrzędną 1 i 3, pomijając 2 która jest wysokością
            x = ce.getVertices(polygon)[3*(n+1)-3]
            x = round(x,2)
            #cityengine przechowuje współrzędną Y z minusem. Dla zgodności z szejpami zewnętrzymi trzeba przemnożyć przez -1. Uwaga: przy ładowaniu geometrii z powrotem do CityEngine trzeba przemnozyć przez -1 jeszcze raz
            y = ce.getVertices(polygon)[3*(n+1)-1]*(-1)
            y = round(y,2)
            #dołączamy do zmiennej kolejno wspólrzędną x, spację, współrzędną y i przecinek
            geometry_WKT +=`x`
            geometry_WKT +=" "
            geometry_WKT +=`y`
            geometry_WKT +=","
        #ucinamy ostatni przecinek    
        geometry_WKT = geometry_WKT[:-1]
        #zamykamy geometrię dwoma nawiasami i cudzysłowiem
        geometry_WKT +='))"\n'
    #ustalamy ścieżkę zapisu i nazwę pliku csv
    output = tempdir+"geometry_WKT.csv"
    #otwieramy plik z prawami zapisu
    output_write = open(output, "w")
    #dodajemy do pliku zawartość zmiennej
    output_write.write(geometry_WKT)
    #zamykamy plik
    output_write.close()
    print 'saved WKT geometry as CSV'
    return output

def ConvertWKTtoSHP(input):
    #ustalamy ścieżkę zapisu i nazwę pliku po konwersji do shp
    output_name = 'geometry_SHP'
    output = tempdir+output_name+".shp"
    #oruchomienie zewnetrznej aplikacji ogr2ogr do konwersji csv na shp
    os.system("ogr2ogr "+output+" "+input)
    print 'CSV to SHP conversion successfull'
    return output,output_name

def AggregateSHP(input,input_name):
    #dodanie pustej kolumny do umożliwienia agregacji; brudny trick; lepsze byłoby agregowanie wszystkiego z pominięciem tego kroku
    os.system('ogrinfo '+input+' -sql "ALTER TABLE '+input_name+' ADD COLUMN kolumna character(10)"')
    print 'Aggregation column added'
    #ustalamy ścieżkę zapisu i nazwę pliku shp po agregacji
    output = tempdir+"geometry_agre.shp"
    os.system("ogr2ogr -explodecollections "+output+" "+input+" -dialect sqlite -sql 'SELECT kolumna,ST_Union(geometry) AS geometry FROM "+input_name+" GROUP BY kolumna'")
    print 'Aggregation successfull'
    return output
    
def ConvertSHPtoWKT(input):
    #ustalamy ścieżkę zapisu i nazwę pliku shp po konwersji do csv
    output = tempdir+"geometry_CSV_agre.csv"
    #konwersja zagregowanego pliku shp do csv z geometrią WKT
    os.system("ogr2ogr -f CSV "+output+" "+input+" -lco GEOMETRY=AS_WKT")
    print 'SHP to CSV successfull'
    return output
    
def ImportWKTPolygons(input):
    #otwieramy plik z geometrią WKT
    input_open = open(input, "r")
    #ustalenie zmiennej w której znajduje się treśc otwartego pliku CSV
    input_read = input_open.read()
    #zamykamy plik, nie jest już potrzebny
    input_open.close()
    #zamiana linijek tekstu na elementy listy
    lines_break = re.compile("[^\n]+")
    #ustalenie zmiennej w której znajduje się lista zrobiona z linijek tekstu
    lines = lines_break.findall(input_read)
    #usunięcie pierwszego elementu listy zawierającego ciąg znaków "WKT,kolumna,"
    lines.pop(0)
    for polygon in lines:
        #ustalenie pustej listy zapelnianej wierzcholkami do stworzenia nowej geometrii w CityEngine
        verts = []
        #usuwamy zbędne ciągi znaków wynikające z konstrukcji WKT
        polygon = polygon.replace('"POLYGON ((','')
        polygon = polygon.replace('))",','')
        #rozbijamy uzyskany ciąg znaków na listę wierzchołków o konstrukcji x y, x y, x y,...
        polygon = polygon.split(',')
        #iterujemy przez każdy wierzchołek poligonu by wydobyć współrzędne wierzchołków
        for vertex in polygon:
            #rozbijamy konstrukcję [x y] na dwa elementy [x,y] za pomocą rozdzielającej spacji    
            vertex = vertex.split(' ')
            #konwersja tekstu (str) na float
            coords = [float(coord) for coord in vertex]
            coord_x = coords[0]
            #przemnażamy z powrotem współrzędną y przez -1
            coord_y = coords[1]*(-1)
            #dodajemy wspolrzedną z
            coord_z = 0
            #dodajemy do listy wspolrzednych poligonu uzyskane wspolrzedne wierzcholka. UWAGA: dodajemy w odwrotnej kolejności (yzx, zamiast xzy) oraz nie do końca listy, ale do jej początku. W ten sposób uzyskana póxniej geometria odwrócona jest do góry, a nie do dołu. Zachowanie niewyjaśnione.
            verts.insert(0,coord_y)
            verts.insert(0,coord_z)
            verts.insert(0,coord_x) 
        #usunięcie ostatniego wierzcholka, będącego zdublowanym pierwszym wierzcholkiem. UWAGA: zachowanie niewyjasnione
        verts = verts[:-3]
        #tworzymy ksztalt w CityEngine za pomocą listy wspolrzednych
        ce.createShape(None, verts)
        print 'WKT import as shape successfull'

if __name__ == '__main__':
    CreateTempDir()
    CleanTempDir()
    geometry = SetWorkGeometry()
    geometry_CSV = ConvertToWKT(geometry)
    geometry_SHP, geometry_SHP_name = ConvertWKTtoSHP(geometry_CSV)
    geometry_SHP_agre = AggregateSHP(geometry_SHP,geometry_SHP_name)
    geometry_CSV_agre = ConvertSHPtoWKT(geometry_SHP_agre)
    ImportWKTPolygons(geometry_CSV_agre)
