'''
Created on 25-04-2015

@author: kaszagrzegorz
'''
from scripting import *
import os
import sys
import re
import csv
# get a CityEngine instance
ce = CE()

for pliki in ce.getObjectsFrom(ce.toFSPath("scripts")+'/geometria/', ce.isFile):
    ce.delete(pliki)
print 'wyczyszczono katalog roboczy'
#pusta zmienna, którą będziemy zapełniać listą wierzchołków w formacie WKT. znak /n oznacza załamanie linii
geometria_WKT ='WKT,\n'

#zmienna zawierająca geometrię na której operujemy
zaznaczenie = ce.selection()
obiekty = ce.getObjectsFrom(zaznaczenie)
print "zaznaczono",len(obiekty),"obiektow"
#iterujemy przez zaznaczone obiekty i każdy tłumaczymy na WKT
for geometria in obiekty:
    geometria_WKT +='"POLYGON (('
    #zmienna zawierająca ilość wierzchołków geometrii 
    ilosc_wierzcholkow = (len(ce.getVertices(geometria))/3) 
    #zmienna zawierająca zbiór wierzchołków XYZ
    wierzcholki = ce.getVertices(geometria)    
    #iterujemy przez wierzchołki i odczytujemy tylko wartości X i Y, pomijamy Z
    for n in range(ilosc_wierzcholkow):
        #formuła, która dla każdego n-tego wierzchołka bierze tylko współrzędną 1 i 3, pomijając 2 która jest wysokością
        x = ce.getVertices(geometria)[3*(n+1)-3]
        x = round(x,2)
        #cityengine przechowuje współrzędną Y z minusem. Dla zgodności z szejpami zewnętrzymi trzeba przemnożyć przez -1. Uwaga: przy ładowaniu geometrii z powrotem do CityEngine trzeba przemnozyć przez -1 jeszcze raz
        y = ce.getVertices(geometria)[3*(n+1)-1]*(-1)
        y = round(y,2)
        #dołączamy do zmiennej kolejno wspólrzędną x, spację, współrzędną y i przecinek
        geometria_WKT +=`x`
        geometria_WKT +=" "
        geometria_WKT +=`y`
        geometria_WKT +=","    
    #ucinamy ostatni przecinek    
    geometria_WKT = geometria_WKT[:-1]
    #zamykamy geometrię dwoma nawiasami i cudzysłowiem
    geometria_WKT +='))"\n'
#ustalamy ścieżkę zapisu i nazwę pliku csv
plik = ce.toFSPath("scripts")+"/geometria/geometria_WKT.csv"
#otwieramy plik z prawami zapisu
zapis = open(plik, "w")
#dodajemy do pliku zawartość zmiennej
zapis.write(geometria_WKT)
#zamykamy plik
zapis.close()
print 'zapisano csv'
#ustalamy ścieżkę zapisu i nazwę pliku po konwersji do shp
nazwa_plik_shp = 'geometria_SHP'
plik_shp = ce.toFSPath("scripts")+'/geometria/'+nazwa_plik_shp+".shp"
#oruchomienie zewnetrznej aplikacji ogr2ogr do konwersji csv na shp
os.system("ogr2ogr "+plik_shp+" "+plik)
print 'konwersja csv do shp zakonczona'
#dodanie pustej kolumny do umożliwienia agregacji; brudny trick; lepsze byłoby agregowanie wszystkiego z pominięciem tego kroku
os.system('ogrinfo '+plik_shp+' -sql "ALTER TABLE '+nazwa_plik_shp+' ADD COLUMN kolumna character(10)"')
print 'dodano kolumne agregacji'
#ustalamy ścieżkę zapisu i nazwę pliku shp po agregacji
shp_agre = ce.toFSPath("scripts")+"/geometria/geometria_agre.shp"
os.system("ogr2ogr -explodecollections "+shp_agre+" "+plik_shp+" -dialect sqlite -sql 'SELECT kolumna,ST_Union(geometry) AS geometry FROM "+nazwa_plik_shp+" GROUP BY kolumna'")
print 'agregacja zakonczona'
#ustalamy ścieżkę zapisu i nazwę pliku shp po konwersji do csv
plik_csv_agre = ce.toFSPath("scripts")+"/geometria/geometria_WKT_agre.csv"
#konwersja zagregowanego pliku shp do csv z geometrią WKT
os.system("ogr2ogr -f CSV "+plik_csv_agre+" "+shp_agre+" -lco GEOMETRY=AS_WKT")
print 'konwersja do CSV WKT zakonczona'
#otwieramy plik z geometrią WKT
otwarcie_WKT = open(plik_csv_agre, "r")
#ustalenie zmiennej w której znajduje się treśc otwartego pliku CSV
odczyt_WKT = otwarcie_WKT.read()
#zamykamy plik, nie jest już potrzebny
otwarcie_WKT.close()
#zamiana linijek tekstu na elementy listy
podzial_linii = re.compile("[^\n]+")
#ustalenie zmiennej w której znajduje się lista zrobiona z linijek tekstu
zbior_linii = podzial_linii.findall(odczyt_WKT)
#usunięcie pierwszego elementu listy zawierającego ciąg znaków "WKT,kolumna,"
zbior_linii.pop(0)
for poligon in zbior_linii:
    #ustalenie pustej listy zapelnianej wierzcholkami do stworzenia nowej geometrii w CityEngine
    wierzcholki = []
    #usuwamy zbędne ciągi znaków wynikające z konstrukcji WKT
    poligon = poligon.replace('"POLYGON ((','')
    poligon = poligon.replace('))",','')
    #rozbijamy uzyskany ciąg znaków na listę wierzchołków o konstrukcji x y, x y, x y,...
    poligon = poligon.split(',')
    #iterujemy przez każdy wierzchołek poligonu by wydobyć współrzędne wierzchołków
    for wierzcholek in poligon:
        #rozbijamy konstrukcję [x y] na dwa elementy [x,y] za pomocą rozdzielającej spacji    
        wierzcholek = wierzcholek.split(' ')
        #konwersja tekstu (str) na float
        wspolrzedne = [float(x) for x in wierzcholek]
        wspolrzedna_x = wspolrzedne[0]
        #przemnażamy z powrotem współrzędną y przez -1
        wspolrzedna_y = wspolrzedne[1]*(-1)
        #dodajemy wspolrzedną z
        wspolrzedna_z = 0
        #dodajemy do listy wspolrzednych poligonu uzyskane wspolrzedne wierzcholka. UWAGA: dodajemy w odwrotnej kolejności (yzx, zamiast xzy) oraz nie do końca listy, ale do jej początku. W ten sposób uzyskana póxniej geometria odwrócona jest do góry, a nie do dołu. Zachowanie niewyjaśnione.
        wierzcholki.insert(0,wspolrzedna_y)
        wierzcholki.insert(0,wspolrzedna_z)
        wierzcholki.insert(0,wspolrzedna_x) 
    #usunięcie ostatniego wierzcholka, będącego zdublowanym pierwszym wierzcholkiem. UWAGA: zachowanie niewyjasnione
    wierzcholki = wierzcholki[:-3]
    #tworzymy ksztalt w CityEngine za pomocą listy wspolrzednych
    ce.createShape(None, wierzcholki)
print 'koniec'
print '___________________________'
