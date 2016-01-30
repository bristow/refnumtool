import tkinter as tk
import os
from os.path import basename, dirname, join, isdir, exists, expanduser
from yaml import load, dump
from shutil import copyfile

try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader
    from yaml import Dumper

import refnumtool.parametre as param
from refnumtool.mailing import Mailing
from refnumtool.id2odt import *

class refnumTool(tk.Frame):
    """classe principale de gestion pour référent numérique
    interface en ligne de commande par choix simple
    Vous devez avoir:

    * un csv des profs principaux
    * un csv des overquotas
    * un csv des identifiants ENT (général ou juste une màj)
    
    1. envoi de messages aux profs principaux pour les dépassements de quota
    2. génération d'un document .odt par classe des identifiants ENT pour les
       tuteurs sur une mise à jour, envoi des identifiants élèves aux PP.
    3. génération globale des identifiants ENT tuteurs et élèves par classe
       les comptes tuteurs déjà utilisés sont expurgés
    4. envoi général des id élèves aux PP.
    5. envoi général des id tuteurs aux PP.
    6. quitter

    """
    global Dumper
    global Loader

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()         
        # paramètres généraux
        home = expanduser("~/.refnumtool.d")
        confpath = join(home,"config.yaml") 
        if not(exists(confpath)):
            print("création "+confpath)
            self.init_config(param.config, confpath)
            #copyfile("refnumtool/configbase.yaml", confpath) 
        with open(confpath,"r") as conf_file:
            self.config = load(conf_file, Loader=Loader)
        # texte de l'export odt tuteur
        txttuteurpath = join(home, "text_extract_tuteur.yaml")
        if not(exists(txttuteurpath)):
            print("création "+txttuteurpath)
            self.init_config(param.extract_tuteur, txttuteurpath)
            #copyfile("refnumtool/text_extract_tuteur.yaml", txttuteurpath)
        # texte des quotas
        confquota = join(home,"textquota.yaml") 
        if not(exists(confquota)):
            print("création "+confquota)
            self.init_config(param.txtquota, confquota)
            #copyfile("refnumtool/textquota.yaml", confquota) 
        # texte des newid
        confidnew = join(home,"textidnew.yaml") 
        if not(exists(confidnew)):
            print("création "+confidnew)
            self.init_config(param.txtidnew, confidnew)
            #copyfile("refnumtool/textidnew.yaml", confidnew) 
        # texte des idgen
        confidgen = join(home,"textidgen.yaml") 
        if not(exists(confidgen)):
            print("création "+confidgen)
            self.init_config(param.txtidgen, confidgen)
            #copyfile("refnumtool/textidgen.yaml", confidgen) 


        print("chargement du fichier des professeurs principaux")    
        self.mailing  = Mailing(self.config)
        self.options = {'1': self._quota, '2': self._idnew,\
                        '3': self.mailing.admin_idgen, '4': self._idgen,
                        '5': self._idgentu, '6': self._exit}

        self.__call__()
        
    def __call__(self):
        choix = ["1: envoi des overquotas aux pp",
                 "2: génération d'un .odt tuteurs, envoi des nouveaux id ENT aux pp",
                 "3: génération de tous les id ENT par classe",
                 "4: envoi des id élèves aux PP",
                 "5: envoi des id tuteurs aux PP",
                 "6: quitter"]
        
        print(*choix, sep='\n')
        IN = input("choisir 1,2,3,4,5,6 :")
        while IN not in "123456":
            IN = input("choisir 1,2,3,4,5,6 :")
        self.options[IN]()

    def init_config(self, val, path):
        """créer ou réinitialiser un fichier yaml de config

        :param val: valeurs à enregistrer
        :type val: dict list ou autre
        :param path: chemin d'enregistrement
        :type path: str
        """
        with open(path, "w") as f:
            dump(val, f, Dumper=Dumper,default_flow_style=False)
            # False permet d'avoir la syntaxe basique de yaml

    def _quota(self):
        self.mailing.admin_quota()
        pp = [v for v in self.mailing.PP.values() if "over" in v]
        print(len(pp), " profs à contacter")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("quota")
        else:
            self.mailing._save_config()
            self.__call__()
            
    def _idnew(self):
        self.mailing.admin_idnew()
        #générer un .odt des identifiants Tuteur.    
        pp = [e for e in self.mailing.PP.values() if "Eleve" in e]
        pptu = [e for e in self.mailing.PP.values() if "Tuteur" in e]
        
        for prof in pptu:
            tuteurs = parentId(self.mailing.pathid, maj=True, data=prof)
        print("fichiers des nouveaux identifiants généré pour "+str(self.mailing.nbtu)+" tuteurs")

        print(len(pp), " profs à contacter pour élèves")
        print(len(pptu), " profs à contacter pour tuteurs")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idnew")
        else:
            self.mailing._save_config()
            self.__call__()

    def _idgen(self):
        self.mailing._set_iddirectory("dossier des identifiants")
        self.mailing._set_prof("elycee")
        a = input("envoyer les id élèves à tous les PP?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idgen")
        else:
            self.mailing._save_config()
            self.__call__()

    def _idgentu(self):
        self.mailing._set_iddirectory("dossier des identifiants")
        self.mailing._set_prof("elycee")
        a = input("envoyer les id tuteurs à tous les PP?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idgentu")
        else:
            self.mailing._save_config()
            self.__call__()

    def _exit(self):
        exit()
