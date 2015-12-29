import tkinter as tk
import shelve
import os
#from os.path import exists
from mailing_pp import Mailing
from id2odt import *

class refnumTool():
    __doc__=""" classe principale de gestion pour référent numérique
        interface en ligne de commande par choix simple
        Vous devez avoir:
          * un csv des profs principaux
          * un csv des overquotas
          * un csv des identifiants ENT (général ou juste une màj)
        
        1: envoi de messages aux profs principaux pour les dépassements de quota
        2: génération d'un document .odt des identifiants ENT pour les tuteurs sur une mise
          à jour, envoi des identifiants élèves aux PP.
        3: génération globale des identifiants ENT tuteurs et élèves par classe puis envoi
          des id élèves aux PP.
        4: quitter
        """
    
    def __init__(self):
        self.options = {'1': self._quota, '2': self._idnew, '3': self._idgen, '4': self._exit}
        if os.path.exists("config_refnum"):
            with shelve.open('config_refnum') as db:
                self.config = db['config']
        else:
            self.config = dict()

        print("chargement du fichier des professeurs principaux")    
        self.mailing  = Mailing()
        self.__call__()
        
    def __call__(self):
        choix = ["1: envoi des overquotas aux pp",\
                 "2: génération d'un .odt tuteurs, envoi des nouveaux id ENT aux pp",\
                 "3: génération et envoi de tous les id ENT", "4: quitter"]
        
        print(*choix, sep='\n')
        IN = input("choisir 1,2,3,4 :")
        while IN not in "1234":
            IN = input("choisir 1,2,3,4 :")
        self.options[IN]()

    def _quota(self):
        self.mailing.admin_quota()
        pp = [self.mailing.PPscribe[e] for e in self.mailing.PPscribe if "over"\
              in self.mailing.PPscribe[e]]
        print(len(pp), " profs à contacter")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("quota", **self.mailing.sending_param)
        else:
            self.__call__()

    def _idnew(self):
        self.mailing.admin_idnew()
        #générer un .odt des identifiants Tuteur.
        tuteurs = parentId(self.mailing.pathid, maj=True, data=self.mailing.PPelycee)
        print("fichier des nouveaux identifiants généré pour "+str(self.mailing.nbtu)+" tuteurs")
        
        pp = [self.mailing.PPelycee[e] for e in self.mailing.PPelycee if "Eleve"\
              in self.mailing.PPelycee[e]]
        print(len(pp), " profs à contacter")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idnew", **self.mailing.sending_param)
        else:
            self.__call__()

    def _idgen(self):
        pass

    def _exit(self):
        exit()
  
app = refnumTool()


        
