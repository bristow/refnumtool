#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
import re
import shelve
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
from os.path import basename, dirname, join, isdir, exists
from os import mkdir, sep

from refnumtool.id_extractor import Extractor

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

    sending_param= {'test': True, 'dir': None, 'default_to':"boris@bebop",\
                    'sender': "Boris.Mauricette@ac-lyon.fr",\
                    'relay':'smtps.ac-lyon.fr',
                    'port': 587}

    def __init__(self):
        self.pathprof = askopenfilename(initialdir="", defaultextension=".csv",\
                                   title="Fichier des profs principaux",\
                                   filetypes=[("CSV", "*.csv")])
        self.logfile = join(dirname(self.pathprof), "log_refnumtool.log")
        self.PPscribe = dict()
        self.PPpronote = dict()
        self.PPelycee = dict()
        if exists("config_mailing"):
            with shelve.open('config_mailing') as db:
                self.config = db['config']
        else:
            self.config = self.sending_param
        #self.set_sending_param()


##    def set_sending_param(self):
##        global r2
##        A = tk.Frame(master=r2)
##        TEST = tk.IntVar()
##        TEST.set(1 if self.sending_param["test"] else 0)
##        w = tk.Checkbutton( A, text="sending test", fg="red",
##                            variable=TEST,
##                            command=self._switch_test)
##        w.pack(side="top")
##        QUIT = tk.Button(A, text="QUIT", fg="red",
##                                            command=r2.destroy)
##        QUIT.pack(side="bottom")


    def _switch_test(self):
         self.sending_param["test"]=not(self.sending_param["test"])
        

    def _set_prof(self, choix):
        """charge les données prof

        :param choix: in ["elycee", "quota"]
        """
        #nom de l'entrée csv
        ext = "nom_"+(choix if choix=="elycee" else "scribe")
        # remplissage profs pour elycee
        fprof=open(self.pathprof, encoding="utf8")
        dialect=csv.Sniffer().sniff(fprof.readline())
        fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fprof, dialect=dialect)
        if choix=="elycee":
            for e in reader:
                if e[ext]:
                    self.PPelycee[e[ext]] = e
        elif choix=="quota":
            for e in reader:
                if e[ext]:
                    self.PPscribe[e[ext]] = e
        fprof.close()

    def admin_quota(self):
        """lancer l'analyse des quotas: rempli les dictionnaires self.PPscribe avec une
        clé 'over' contenant la liste des élèves en overquota.

        file: str chemin du fichier de quota
        (copie/colle de la sortie web scribe)
        """
        self.pathquotas = askopenfilename(initialdir="", defaultextension=".csv",\
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
            if a: print(a.group(1), a.group(2))
            if a and "over" in self.PPscribe[a.group(2)]:
                (self.PPscribe[a.group(2)]["over"]).append(a.group(1))
                self.nbel += 1 #nb élèves
            elif a:
                self.PPscribe[a.group(2)]["over"] = [a.group(1)]
                self.nbel += 1 #nb élèves
        quota.close()

    def admin_idnew(self):
        """lancer l'analyse des nouveaux identifiants: rempli les dictionnaires
        self.PPelycee avec une clé 'Eleve' et ou 'Tuteur' contenant la liste
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
                if p not in self.PPelycee[e["classe"]]:
                    self.PPelycee[e["classe"]][p] =[e]
                else:
                   self.PPelycee[e["classe"]][p].append(e)
        fid.close()

    def admin_idgen(self):
        """génération des fichiers d'identifiants par classe.
        """
        self._set_pathid("Fichier général des identifiants")
        self._set_prof("elycee")
        I = Extractor(self._set_pathid)
        # rediriger le chemin vers le dossier des id.
        self.pathid = join(dirname(self.pathid), "identifiantsENT")


    def _set_pathid(self, invite=""):
        self.pathid = askopenfilename(initialdir="", defaultextension=".csv",\
                                     title=invite,\
                                     filetypes=[("CSV", "*.csv")])

    def _set_iddirectory(self, invite):
        self.pathid = askdirectory(title=invite, initialdir="")

        
    def mailing(self, cible, **param):
        """fonction de mailing aux profs principaux

        :param cible: in ["quota", "idgen", "idnew"]
        :type cible: str
        :param param: dictionnaire de paramètres
        :type param: dict
        :param test: indique si on simule le mailing auquel cas, l'adresse de\
        sortie est default_to
        :type test: boolean
        :param dir: directory where to look for message attachments
        :type dir: str
        :param default_to: default target mail adr in case of test
        :type default_to: str
        :param default_from: who is sending
        :type default_from: str
        :param relayhost: smtp relay name
        :type relayhost: str
        :param port: port value for the relay 587 for secured transaction.
        :type port: int

        .. todo :: config yaml file to save sending options.
        """

        smtprelay = ('localhost' if param["test"] else relay)
        s = (smtplib.SMTP(smtprelay) if (param["test"] or (port not in [465, 587]))\
             else smtplib.SMTP_SSL(param["smtprelay"], port=param["port"]))
        LOG = open(self.logfile, "w")
        if cible == "quota":
            pp = [self.PPscribe[e] for e in self.PPscribe if "over" in self.PPscribe[e]]
            LOG = open(self.logfile, "w")
            for E in pp:
                n = len(E["over"]) # nb d'overquotas
                msg="Cher collègue, tu es prof principal de la "+E["nom_pronote"]+".\n"
                msg+="Les élèves suivants sont en dépassement de quota:\n"
                for x in E["over"]:
                    msg+= x+"\n"
                msg+= "Merci de leur indiquer d'effacer leurs fichiers superflus, puis de bien faire\
 *vider la corbeille* même si elle semble vide.\nBien cordialement,\nB.M."
                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' dépassement'+("s" if n>=2 else "") +\
                               " de quota en "+E["nom_pronote"]
                M['From'] = param["sender"]
                M['To'] = (param["default_to"] if param["test"] else E["E-mail"])
                #encoders.encode_base64(tmp)
                s.send_message(M)
                print("1 msg à "+E["Nom"]+" " +E["Prénom"], file=LOG)
                # if param["test"]:
                #     print(msg)
            print(self.nbel, " élèves détectés", file=LOG)
            print(len(pp), " profs contactés", file=LOG)
            print(self.nbel, " élèves détectés")
            print(len(pp), " profs contactés")

            #s.quit()

        elif cible == "idnew":
            # .. todo: et les nouveaux tuteurs?
            pp = [self.PPelycee[e] for e in self.PPelycee if "Eleve" in self.PPelycee[e]]
                 # "Tuteur" in self.PPscribe[e]\
            COUNT = 0
            # filtrer seulement les élèves pour les pp?
            for E in pp:
                n = len(E["Eleve"]) # nb nv élèves
                COUNT += n
                msg="Cher collègue, tu es prof principal de la "+E["nom_elycee"]+".\n"
                msg+="Les nouveaux élèves suivants sont arrivés dans ta classe:\n"
                for x in E["Eleve"]:
                    msg+= x["nom"]+ " " +x["prenom"]+ " : "+x["login"] +" -- "+x["mot de passe"]+"\n"
                msg+= "Merci de leur transmettre leur identifiant + mot de passe (ENT)."
                msg+="\nBien cordialement,\nB.M."
                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["nom_elycee"]
                M['From'] = param["sender"]
                M['To'] = (param["default_to"] if param["test"] else E["E-mail"])
                #encoders.encode_base64(tmp)
                s.send_message(M)
                print("1 msg à "+E["Nom"]+" " +E["Prénom"], file=LOG)
                # if param["test"]:
                #     print(msg)
            print(COUNT, "nouveaux élèves", file=LOG)
            print(len(pp), " profs contactés", file=LOG)
            print(COUNT, "nouveaux élèves")
            print(len(pp), " profs contactés")

        elif cible == "idgen":
            pathid = self.pathid  # askdirectory(title="dossier des identifiants", initialdir="")
            pp = [self.PPelycee[e] for e in self.PPelycee]
            for E in pp:
                msg="Cher collègue, tu es prof principal de la "+E["nom_elycee"]+".\n"
                msg+="Voici la liste des identifiants et mot de passe provisoire de tes élèves en pièce jointe\n"
                msg+="Bien cordialement,\nB.M."
                M = MIMEMultipart()
                M['Subject'] = "liste des comptes élève en "+E["nom_elycee"]
                M['From'] = param["sender"]
                M['To'] = (param["default_to"] if param["test"] else E["E-mail"])
                M.attach(MIMEText(msg, 'plain', _charset='utf-8'))
                #ajouter la pj liée au pp, le nom du fichier doit être:
                F = join(pathid, "ENT_id_Eleve_"+E["nom_elycee"]+".odt")
                #open and join a file
                ctype = (mimetypes.guess_type(basename(F)))[0]
                maintype, subtype = ctype.split('/', 1)
            
                with open(F, 'rb') as f:
                    p = MIMEBase(maintype, subtype)
                    p.set_payload(f.read())
                    encoders.encode_base64(p)
                    p.add_header('Content-Disposition', 'attachment', filename=basename(F))
                    M.attach(p)
                s.send_message(M)
                print("1 msg+pj à "+E["Nom"]+" " +E["Prénom"], file=LOG)
            print(len(pp), " profs contactés", file=LOG)
            print(len(pp), " profs contactés")
        LOG.close()
