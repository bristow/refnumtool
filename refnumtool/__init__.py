import tkinter as tk
import os
from os.path import basename, dirname, join, isdir, exists, expanduser
from yaml import load, dump
from shutil import copyfile

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
    2. génération d'un document .odt des identifiants ENT pour les tuteurs sur
       une mise à jour, envoi des identifiants élèves aux PP.
    3. génération globale des identifiants ENT tuteurs et élèves par classe
    4. envoi général des id élèves aux PP.
    5. quitter

    """
    
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid() 

        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        # paramètres généraux
        home = expanduser("~/.refnumtool.d")
        confpath = join(home,"config.yaml") 
        if not(exists(confpath)):
            # .. todo:: améliorer la recherche du modèle de config
            copyfile("refnumtool/configbase.yaml", confpath) 

        with open(confpath,"r") as conf_file:
            self.config = load(conf_file, Loader=Loader)

        txttuteurpath = join(home, "text_extract_tuteur.yaml")
        if not(exists(txttuteurpath)):
            copyfile("refnumtool/text_extract_tuteur.yaml", txttuteurpath)

        print("chargement du fichier des professeurs principaux")    
        self.mailing  = Mailing(self.config)
        self.options = {'1': self._quota, '2': self._idnew,\
                        '3': self.mailing.admin_idgen, '4': self._idgen,
                        '5': self._exit}

        self.__call__()
        
    def __call__(self):
        choix = ["1: envoi des overquotas aux pp",
                 "2: génération d'un .odt tuteurs, envoi des nouveaux id ENT aux pp",
                 "3: génération de tous les id ENT par classe",
                 "4: envoi des id élèves aux PP",
                 "5: quitter"]
        
        print(*choix, sep='\n')
        IN = input("choisir 1,2,3,4,5 :")
        while IN not in "12345":
            IN = input("choisir 1,2,3,4,5 :")
        self.options[IN]()

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
        tuteurs = parentId(self.mailing.pathid, maj=True, data=self.mailing.PP)
        print("fichier des nouveaux identifiants généré pour "+str(self.mailing.nbtu)+" tuteurs")
        
        pp = [self.mailing.PP[e] for e in self.mailing.PP if "Eleve"\
              in self.mailing.PP[e]]
        print(len(pp), " profs à contacter")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idnew")
        else:
            self.mailing._save_config()
            self.__call__()

    def _idgen(self):
        self.mailing._set_iddirectory("dossier des identifiants")
        self.mailing._set_prof("elycee")
        a = input("envoyer les id à tous les PP?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idgen")
        else:
            self.mailing._save_config()
            self.__call__()

    def _exit(self):
        exit()
