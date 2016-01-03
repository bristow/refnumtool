#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
import os
from odf.opendocument import OpenDocumentText
from odf.draw import Image, Frame
from odf.text import P, Span, Tab, List, ListItem
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.style import Style, GraphicProperties, TextProperties, ParagraphProperties, TableColumnProperties
from odf.style import PresentationPageLayout, MasterPage, PageLayout, PageLayoutProperties, Header, HeaderStyle, HeaderFooterProperties
from odf.style import TabStops, TabStop, FooterStyle, Footer

from tkinter.filedialog import askopenfilename
from zipfile import ZipFile
from os.path import basename, dirname, join, isdir, expanduser

from yaml import load, dump

class _ODFPY_Document_Generic(object):
    """Example of Document
    """

    def __init__(self):
        self.document = OpenDocumentText()
        self.defineStyles()

    def defineStyles(self):
        pass
    
    def addParagraphStyle(self, id, name, paragraph_properties={}, text_properties={}, graphic_properties={}):
        style = Style(name=name, family="paragraph")
        if len(paragraph_properties)>0:
            style.addElement(ParagraphProperties(**paragraph_properties))
        if len(text_properties)>0:
            style.addElement(TextProperties(**text_properties))
        setattr(self, id, style)
        self.document.styles.addElement(style)

    def addGraphicStyle(self, id, name, graphic_properties={}):
        style = Style(name=name, family="graphic")
        if len(graphic_properties)>0:
            style.addElement(GraphicProperties(**graphic_properties))
        setattr(self, id, style)
        self.document.styles.addElement(style)

    def addTableColumnStyle(self, id, name, properties={}):
        style = Style(name=name, family="table-column")
        style.addElement(TableColumnProperties(**properties))
        setattr(self, id, style)
        self.document.automaticstyles.addElement(style)

    def addPageLayoutStyle(self, id, name, properties={}):
        style = PageLayout(name=name)
        style.addElement(PageLayoutProperties(**properties))
        setattr(self, id, style)
        self.document.automaticstyles.addElement(style)


    def addParagraph(self, text, stylename):
        stylename = getattr(self, stylename, None)
        p = P(stylename=stylename, text=text)
        self.document.text.addElement(p)

    def addTable(self, content, cell_style, column_styles=[]):
        cell_style = getattr(self, cell_style, None)
        table = Table()
        for style in column_styles: 
            if "stylename" in style.keys():
                style["stylename"] = getattr(self, style["stylename"], None)
            table.addElement(TableColumn(**style))
        for row in content:
            tr = TableRow()
            table.addElement(tr)
            for cell in row:
                tc = TableCell()
                tr.addElement(tc)
                p = P(stylename=cell_style, text=cell)
                tc.addElement(p)
        self.document.text.addElement(table)

    def addList(self, content, stylename):        
        liste = List()
        for e in content:
            p = P(stylename=stylename, text=e)
            i = ListItem()
            i.addElement(p)
            liste.addElement(i)
        self.document.text.addElement(liste)


    def save(self, filename):
        self.document.save(filename)


class _ODFPY_Document_Template(_ODFPY_Document_Generic):
    """Example of document
    """

    def defineStyles(self):
        # entête
        s = Style(name = "Header", family ="paragraph")
        prop = {"numberlines":"false", "linenumber":"0"}
        P = ParagraphProperties(**prop)
        Q = TabStops()
        Q.addElement(TabStop(position="8.5cm", type="center"))
        Q.addElement(TabStop(position="17cm", type="right"))
        P.addElement(Q)
        s.addElement(P)
        prop2 = {"fontfamily": "Verdana", "fontweight": "bold", "fontsize": "14pt"}
        s.addElement(TextProperties(**prop2))
        self.document.styles.addElement(s)
        setattr(self, "Header", s)
        
        #autres 
        self.addParagraphStyle("heading1", "Heading 1",
                               paragraph_properties={"breakbefore": "page", "lineheight": "24pt"},
                               text_properties={"fontfamily": "Verdana", "fontweight": "bold", "fontsize": "14pt"}
                               )
        self.addParagraphStyle("heading2", "Heading 2",
                               paragraph_properties={"breakbefore": "false", "lineheight": "24pt"},
                               text_properties={"fontfamily": "Verdana", "fontweight": "italic", "fontsize": "14pt"}
                               )
        self.addParagraphStyle("heading3", "Heading 3",
                               paragraph_properties={"breakbefore": "false", "lineheight": "20pt"},
                               text_properties={"fontfamily": "Liberation Sans", "fontweight": "bold", "fontsize": "14pt"}
                               )
        self.addParagraphStyle("normal", "Normal",
                               paragraph_properties={"breakbefore": "false", "lineheight": "20pt"},
                               text_properties={"fontfamily": "Liberation Serif", "fontsize": "12pt"}
                               )
        self.addParagraphStyle("gras", "Bgr",
                               paragraph_properties={"breakbefore": "false", "lineheight": "20pt"},
                               text_properties={"fontfamily": "Liberation Serif", "fontweight": "bold", "fontsize": "12pt"}
                               )

        self.addParagraphStyle("tablecontents", "Table Contents",
                               paragraph_properties={"numberlines": "false", "linenumber": "0"} )
        self.addPageLayoutStyle("mpm1", "Mpm1", \
                                properties={"pagewidth":"21.001cm", "pageheight": "14.801cm",\
                                            "numformat": "1", "printorientation": "landscape",\
                                            "margintop":"1cm", "marginbottom": "1cm", "marginleft": "1cm",\
                                            "marginright": "1cm", "writingmode":"lr-tb"})#, "footnotemaxheight":"0cm"
        self.addTableColumnStyle("column1", "Left Column", properties={"columnwidth": "4cm"})
        self.addTableColumnStyle("column2", "Center Column", properties={"columnwidth": "4cm"})
        self.addTableColumnStyle("column3", "Right Column", properties={"columnwidth": "2cm"})

class parentId(_ODFPY_Document_Template):
    """générateur de sortie odt pour les tuteurs.
    Format A5, un tuteur par page.
    """

    def __init__(self, path, maj=False, data=None):
        """initialisation d'un générateur odt pour les tuteurs.
        
        En haut de chaque page A5 en sortie, il créée un tableau

        +----------------+-----------+--------+
        |  Responsable   | Élève     | Classe |
        +================+===========+========+
        |  nom resp      | nom eleve | cl     |
        +----------------+-----------+--------+

        :param str path: chemin vers le fichier des csv tuteurs
        :param boolean maj:  mode màj ou complet
        :param dict data: si maj=True, il doit contenir le dictionnaire des pp
            et tuteurs

        """
        self.nom = basename(path)[:-4] #nom du fichier sans extension
        base = dirname(path)
        #fallacieux en cas de màj.
        # .. todo:: vérifier utilité et effacer
        self.classe = ((self.nom).split('Tuteur_'))[-1] #vraiment lié au nom de fichier
        self.document = OpenDocumentText()
        self.defineStyles()
        # def du header complet
        head_style = getattr(self, "Header", None)
        p = P(stylename=head_style)
        mp = MasterPage(name="Standard", pagelayoutname="Mpm1")
        h = Header()
        h.addElement(p)
        mp.addElement(h)
        self.document.masterstyles.addElement(mp)
        
        #import des textes de la page odt tuteur
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader
        home = expanduser("~/.refnumtool.d")
        with open(join(home,"text_extract_tuteur.yaml")) as file:
            self.msg = load(file, Loader=Loader)

        if not(maj):
            file = open(path, "r", encoding="utf8")
            dialect=csv.Sniffer().sniff(file.readline())
            file.seek(0) # se remettre en début de fichier
            reader = csv.DictReader(file, dialect=dialect)
        
            for d in reader:
                self.make_parent_id(d)
            file.close()
            self.save(join(base, "ENT_id_Tuteur_"+self.classe+".odt")) 
        else: # cas d'une màj
            #for pp in data.values(): # superflu, génération par classe pour les tuteurs
            if "Tuteur" in data:  # test superflu en principe
                for d in data["Tuteur"]:
                    self.make_parent_id(d)
            self.save(join(base, "ENT_id_Tuteur_"+data["elycee"]+"_"+time.strftime("%d%m%Y")+".odt")) 
                   


    def make_parent_id(self, dict):
        """cree la page texte à partir des champs csv
        le texte est lu dans home/.refnumtool.d/text_extract_tuteur.yaml

        :param dict: dictionnaire des champs du tuteur issus du csv (elycee)
        """
        self.addParagraph("Remise Identifiant ENT: Responsable", "heading1")
        table_content = [["Responsable", "Élève", "Classe"],\
                         [dict["nom"]+" "+dict["prenom"],\
                         dict["nom enfant"]+ " " + dict["prenom enfant"],\
                         dict["classe"]]] # self.classe
        self.addTable(table_content, "tablecontents", 
                     [
                         {"numbercolumnsrepeated": 1, "stylename": "column1"},
                         {"numbercolumnsrepeated": 1, "stylename": "column2"},
                         {"numbercolumnsrepeated": 1, "stylename": "column3"}
                     ])
        self.addParagraph("", "normal")
        self.addParagraph(self.msg["annonce"][0], "normal")
        self.addParagraph(self.msg["annonce"][1], "normal")
        self.addParagraph(self.msg["annonce"][2], "normal")
        self.addParagraph(self.msg["annonce"][3], "normal")
        stylename = getattr(self, "gras", None)
        p = P(stylename=stylename, text="votre identifiant: "+dict["login"])
        #p.addElement(Tab())
        q = P(stylename=stylename, text="mot de passe provisoire: "+dict["mot de passe"])    
        self.document.text.addElement(p)
        self.document.text.addElement(q)
        self.addParagraph("", "normal")
        self.addParagraph(self.msg["annonce"][4], "normal")
        self.addList(self.msg["actions"], "normal")
        self.addParagraph(self.msg["annonce"][5], "normal")


class classeId(_ODFPY_Document_Template):
    """générateur d'une sortie odt pour les élèves d'une classe
    """

    def __init__(self, path):
        self.nom = basename(path)[:-4] #nom du fichier sans extension
        base = dirname(path)
        #vraiment lié au nom de fichier
        self.classe = ((self.nom).split('Eleve_'))[-1] 
        self.document = OpenDocumentText()
        self.defineStyles()
        # pas de header complet, on reste en A4

        file = open(path, "r", encoding="utf8")
        dialect=csv.Sniffer().sniff(file.readline())
        file.seek(0) # se remettre en début de fichier
        reader = csv.DictReader(file, dialect=dialect)
        
        self.addParagraph("Identifiants ENT élèves: "+self.classe, "heading1")
        self.addParagraph("nom prenom: identifiant -- mot de passe provisoire de chaque élève", "normal")
        L = List()
        for d in reader:
            L.addElement(self.make_eleve_id(d))
        self.document.text.addElement(L)
        file.close()
        self.save(join(base, "ENT_id_Eleve_"+self.classe+".odt"))            

    def make_eleve_id(self, dict):
        mdp = dict["mot de passe"]
        L = dict["nom"]+" "+dict["prenom"]+" :\t\t "+dict["login"]+" -- "+\
            (mdp if len(mdp)<=8 else "mdp déjà utilisé")
        stylename = getattr(self, "normal", None)
        p = P(stylename=stylename, text=L)
        i = ListItem()
        i.addElement(p)
        return i
