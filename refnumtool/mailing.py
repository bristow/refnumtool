#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
import re
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from os.path import basename, dirname, join, isdir, exists, expanduser
from os import mkdir, sep
from yaml import load, dump
from shutil import copyfile

from refnumtool.id_extractor import Extractor
import refnumtool.parametre as param

import ssl
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class Mailing():
    """Objet pour diffusion aux profs principaux.
    L'initialisation demande de choisir un fichier csv des PP.
    """
    def __init__(self, param=dict()):
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        self.config = param
        initdir = (self.config["initialdir"] if "initialdir" \
                   in self.config else "")
        self._update_config(("initialdir", initdir))

        home = expanduser("~/.refnumtool.d")
        # texte des quotas
        confquota = join(home,"textquota.yaml") 
        with open(confquota,"r") as conf_file:
            self.textquota = load(conf_file, Loader=Loader)
        # texte des newid
        confidnew = join(home,"textidnew.yaml") 
        with open(confidnew,"r") as conf_file:
            self.textidnew = load(conf_file, Loader=Loader)
        # texte des idgen
        confidgen = join(home,"textidgen.yaml") 
        with open(confidgen,"r") as conf_file:
            self.textidgen = load(conf_file, Loader=Loader)

        self.pathprof = askopenfilename(initialdir=self.config["initialdir"],\
                                        defaultextension=".csv",\
                                        title="Fichier des profs principaux",\
                                        filetypes=[("CSV", "*.csv")])
        self._update_config(("initialdir", dirname(self.pathprof)))
        self.logfile = join(dirname(self.pathprof), "log_refnumtool"+\
                            time.strftime("%H-%M-%S-%d-%m-%Y")+".log")
        self.PP = dict()

    def _update_config(self, pair):
        self.config.update(dict([pair]))

    def _save_config(self):
        try:
            from yaml import CDumper as Dumper
        except ImportError:
            from yaml import Dumper
        #out = dump(self.config, Dumper=Dumper)
        home = expanduser("~/.refnumtool.d")
        with open(join(home,"config.yaml"), "w") as f:
            dump(self.config, f, Dumper=Dumper,default_flow_style=False )

    def _switch_test(self):
         self.config["test"]=not(self.config["test"])

    def _set_prof(self, choix):
        """charge les données prof

        :param choix: in ["elycee", "quota"]
        """
        #nom de l'entrée csv
        ext = (choix if choix=="elycee" else "scribe")
        # remplissage profs pour elycee
        fprof=open(self.pathprof, encoding="utf8")
        dialect=csv.Sniffer().sniff(fprof.readline())
        fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fprof, dialect=dialect)
        if choix=="elycee":
            for e in reader:
                if e[ext]:
                    self.PP[e[ext]] = e
        elif choix=="quota":
            for e in reader:
                if e[ext]:
                    self.PP[e[ext]] = e
        fprof.close()

    def admin_quota(self):
        """lancer l'analyse des quotas: rempli les dictionnaires self.PP avec une
        clé 'over' contenant la liste des élèves en overquota.

        file: str chemin du fichier de quota
        (copie/colle de la sortie web scribe)
        """
        self.pathquotas = askopenfilename(initialdir=self.config["initialdir"],\
                                          defaultextension=".csv",\
                                          title="Fichier des quotas",\
                                          filetypes=[("CSV", "*.csv")])
        self._set_prof("quota")
        # remplissage élèves csv file
        #analyse de la colonne "Utilisateur"
        GET_ELEVE = re.compile("(\w+\.\w+) \(élève de ([^)]+)")
        quota = open(self.pathquotas, "r") #, encoding="latin1"
        dialect=csv.Sniffer().sniff(quota.readline())
        quota.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(quota, dialect=dialect)
        self.nbel = 0 #nb élèves
        for e in reader:
            a = GET_ELEVE.search(e["Utilisateur "])
            if a and "over" in self.PP[a.group(2)]:
                (self.PP[a.group(2)]["over"]).append(a.group(1))
                self.nbel += 1 #nb élèves
            elif a:
                self.PP[a.group(2)]["over"] = [a.group(1)]
                self.nbel += 1 #nb élèves
        quota.close()

    def admin_idnew(self):
        """lancer l'analyse des nouveaux identifiants: rempli les dictionnaires
        self.PP avec une clé 'Eleve' et ou 'Tuteur' contenant la liste
        des nouveaux élèves et tuteurs.
        """
        self._set_pathid(invite="Fichier des *nouveaux identifiants*")
        self._set_prof("elycee")

        # remplissage élèves et tuteurs
        fid = open(self.pathid, "r", encoding="latin1")
        dialect=csv.Sniffer().sniff(fid.readline())
        fid.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fid, dialect=dialect)
        self.nbel = 0 #nb élèves
        self.nbtu = 0 #nb tuteurs
        for e in reader:
            if e["profil"] in ["Eleve", "Tuteur"]:
                p = e["profil"]
                self.nbel +=(1 if p=="Eleve" else 0)
                self.nbtu +=(1 if p== "Tuteur" else 0)
                if p not in self.PP[e["classe"]]:
                    self.PP[e["classe"]][p] =[e]
                else:
                   self.PP[e["classe"]][p].append(e)
        fid.close()

    def admin_idgen(self):
        """génération des fichiers d'identifiants par classe.
        """
        self._set_pathid("Fichier général des identifiants")
        self._set_prof("elycee")
        I = Extractor(self.pathid)
        # rediriger le chemin vers le dossier des id.
        self.pathid = join(dirname(self.pathid), "identifiantsENT")


    def _set_pathid(self, invite=""):
        self.pathid = askopenfilename(initialdir=self.config["initialdir"],\
                                      defaultextension=".csv",\
                                      title=invite,\
                                      filetypes=[("CSV", "*.csv")])
        self.config["initialdir"] = dirname(self.pathid)

    def _set_iddirectory(self, invite):
        self.pathid = askdirectory(title=invite,\
                                   initialdir=self.config["initialdir"],)
        
    def mailing(self, cible):
        """fonction de mailing aux profs principaux
        les paramètres sont lus dans self.config importé de refnumtool.

        :param cible: in ["quota", "idgen", "idnew"]
        :type cible: str
        :param test: indique si on simule le mailing auquel cas, l'adresse de\
        sortie est default_to
        :type test: boolean
        :param dir: directory where to look for message attachments
        :type dir: str
        :param default_to: default target mail adr in case of test
        :type default_to: str
        :param default_from: who is sending
        :type default_from: str
        :param smtp: smtp relay name
        :type smtp: str
        :param port: port value for the relay 587 for secured transaction.
        :type port: int

        """

        cfg = self.config
        smtprelay = ('localhost' if cfg["test"] else cfg["smtp"])
        s = (smtplib.SMTP(smtprelay) if (cfg["test"] or (cfg["port"] not in [465, 587]))\
             else smtplib.SMTP(smtprelay, port=cfg["port"]))
        # s = smtplib.SMTP(smtprelay, port=cfg["port"])
        #smtplib.SMTP_SSL(smtprelay, port=cfg["port"]))
        #login et mdp
        #en clair mais que pour qq secondes sur un écran et pas sur le réseau.
        if not(cfg["test"]) and cfg["port"] in [465, 587]:
            if "login" not in cfg:
                cfg["loging"] = input("Entrez votre login sur le serveur "+\
                              cfg["smtp"]+": ")
            pwd = input("pwd (en clair, dsl) :")
            context = ssl.create_default_context()
            s.starttls(context=context)
            s.login(cfg["login"], pwd)

        LOG = open(self.logfile, "w")
        if cible == "quota":
            pp = [self.PP[e] for e in self.PP if "over" in self.PP[e]]
            COUNT = 0
            for E in pp:
                n = len(E["over"]) # nb d'overquotas
                msg = self.textquota[0]+E["scribe"]+".\n"
                msg += self.textquota[1]
                for x in E["over"]:
                    msg+= x+"\n"
                msg += self.textquota[2]
                msg += cfg["sig"]
                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' dépassement'+("s" if n>=2 else "") +\
                               " de quota en "+E["scribe"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                try:
                    COUNT += 1
                    s.send_message(M)
                    print("1 msg à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(self.nbel, " élèves détectés", file=LOG)
            print(str(COUNT)+" profs contactés", file=LOG)
            print(self.nbel, " élèves détectés")
            print(str(COUNT)+" profs contactés")
        elif cible == "idnew":
            # .. todo: et les nouveaux tuteurs?
            # filtrer seulement les élèves pour les pp?
            pp = [v for v in self.PP.values() if "Eleve" in v]
            COUNT = 0
            COUNTPP = 0
            for E in pp:
                n = len(E["Eleve"]) # nb nv élèves
                COUNT += n
                msg = self.textidnew[0]+E["elycee"]+".\n"
                msg += self.textidnew[1]
                for x in E["Eleve"]:
                    msg+= x["nom"]+ " " +x["prenom"]+ " : "+x["login"] +" -- "+x["mot de passe"]+"\n"
                msg += self.textidnew[2]
                msg += cfg["sig"]

                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["elycee"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                #encoders.encode_base64(tmp)
                try:
                    COUNTPP += 1
                    s.send_message(M)
                    print("1 msg à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(COUNT, "nouveaux élèves", file=LOG)
            print(str(COUNTPP)+" profs contactés", file=LOG)
            print(COUNT, "nouveaux élèves")
            print(str(COUNTPP)+" profs contactés")

        elif cible == "idgen":
            pathid = self.pathid
            pp = [self.PP[e] for e in self.PP]
            COUNT = 0
            for E in pp:
                msg=self.textidgen[0]+E["elycee"]+".\n"
                msg += self.textidgen[1]
                msg += cfg["sig"]
                M = MIMEMultipart()
                M['Subject'] = "liste des comptes élève en "+E["elycee"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                M.attach(MIMEText(msg, 'plain', _charset='utf-8'))
                #ajouter la pj liée au pp, le nom du fichier doit être:
                F = join(pathid, "ENT_id_Eleve_"+E["elycee"]+".odt")
                #open and join a file
                ctype = (mimetypes.guess_type(basename(F)))[0]
                maintype, subtype = ctype.split('/', 1)
            
                with open(F, 'rb') as f:
                    p = MIMEBase(maintype, subtype)
                    p.set_payload(f.read())
                    encoders.encode_base64(p)
                    p.add_header('Content-Disposition', 'attachment',
                                 filename=basename(F))
                    M.attach(p)
                try:
                    COUNT += 1
                    s.send_message(M)
                    print("1 msg+pj à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(str(COUNT)+" profs contactés", file=LOG)
            print(str(COUNT)+" profs contactés")
        LOG.close()
        self.config = cfg
        s.quit()
        self._save_config()
