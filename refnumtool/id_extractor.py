#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
from tkinter.filedialog import askopenfilename
from os.path import basename, dirname, join, isdir
from os import mkdir, sep

from refnumtool.id2odt import *

class Extractor():
    """Décomposer le CSV global des identifiants par classe
    générer un ODT des id élèves par classe (1 page)
    générer un ODT des id tuteurs par classe (1 page par tuteur)
    """
    def __init__(self, path):
        """extracteur des identifiants
        
        :param path: chemin du fichier csv des identifiants ENT
        :type path: str
        """
        
        file=open(path, encoding="latin1")
        dialect=csv.Sniffer().sniff(file.readline())
        file.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(file, dialect=dialect)
        # préfixe pour le chemin en sortie
        pre = join(dirname(path),"identifiantsENT")

        if not(isdir(pre)):
            mkdir(pre)

        consignes ="""Identifiants et mot de passe initiaux des élèves par classe.
        En cas de perte du mot de passe, vous pouvez le régénérer
        dans l'ENT en cherchant l'élève concerné dans l'annuaire."""

        CLASSES = dict()
        for nl in reader:
            # OBJET regroupant les élèves et tuteurs par classe
            if nl["classe"] not in CLASSES:
                CLASSES[nl["classe"]] = {"el":([nl] if nl["profil"]=="Eleve" else []),\
                                         "tu":([nl] if nl["profil"]=="Tuteur" else [])}
            elif nl["profil"]=="Eleve":
                CLASSES[nl["classe"]]["el"].append(nl)
            elif nl["profil"]=="Tuteur":
                CLASSES[nl["classe"]]["tu"].append(nl)

        if '' in CLASSES:# ne pas tenir compte des comptes sans classe
            del CLASSES['']
        CL = list(CLASSES.keys())
        CL.sort() # trier les classes

        OUT = open(join(pre,"ENT_eleves_complet.txt"), "w")
        ## dd/mm/yyyy format
        print(time.strftime("%d/%m/%Y"), file=OUT)
        print("liste des classes: ", CL, file=OUT)
        print(consignes, file=OUT)

        for c in CL:
            print("classe "+c, file=OUT)
            OUTcsv1 = open(join(pre,"ENT_id_Eleve_"+c+".csv"), "w")
            OUTcsv2 = open(join(pre,"ENT_id_Tuteur_"+c+".csv"), "w")
            COUNT = 0
            print("nom;prenom;login;mot de passe", file=OUTcsv1)
            print("nom;prenom;login;mot de passe;nom enfant;prenom enfant;classe", file=OUTcsv2)

            EL = sorted(CLASSES[c]["el"], key = lambda x: x["nom"])
            TU = sorted(CLASSES[c]["tu"], key = lambda x: x["nom"])

            for nl in EL:
                COUNT +=1
                print(*[nl["nom"],nl["prenom"],nl["login"], nl["mot de passe"]],\
                      sep="\t", file = OUT)

                print(*[nl["nom"],nl["prenom"],nl["login"], nl["mot de passe"]],\
                      sep=";", file = OUTcsv1)
            OUTcsv1.close()

            for nl in TU: # on filtre les tuteurs qui n'ont pas encore utilisé l'ENT
                if ">>>" not in nl["mot de passe"]:
                    print(*[nl["nom"],nl["prenom"],nl["login"], nl["mot de passe"],\
                            nl["nom enfant"], nl["prenom enfant"], nl["classe"]],\
                          sep=";", file = OUTcsv2)
            OUTcsv2.close()

            print("total: "+str(COUNT)+ " élèves", file=OUT)
            print("\n\n", file=OUT)
            print(c, "eleves tuteurs OK")
        print(str(len(CL))+" classes traitées")

        OUT.close()

        for c in CL:
            el = join(pre,"ENT_id_Eleve_"+c+".csv")
            tu = join(pre,"ENT_id_Tuteur_"+c+".csv")
            D = parentId(tu)
            E = classeId(el)
            print(c + ": export ODT tu,el OK")
            del D
            del E
