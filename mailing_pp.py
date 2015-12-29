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

import ssl
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

#dirname = tkFileDialog.askdirectory(parent=root,initialdir="/",title='Please select a directory')
# vers les profs
# pathprof = askopenfilename(initialdir="", defaultextension=".csv",\
#                        title="Fichier à traiter", filetypes=[("CSV", "*.csv")])
# fprof=open(pathprof, encoding="utf8")
# dialect=csv.Sniffer().sniff(fprof.readline())
# fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
# reader = csv.DictReader(fprof, dialect=dialect)
# 
# PP = dict()
# for e in reader:
#     PP[e["nom_scribe"]] = e
# 
# #regexp eleve classe:
# GET_ELEVE = re.compile("(\w+\.\w+) \(élève de ([^)]+)")
# pathquotas = askopenfilename(initialdir="", defaultextension=".txt",\
#                        title="Fichier des quotas", filetypes=[("TXT", "*.txt")])
# 
# quota = open(pathquotas, "r")
# L = quota.readline()
# while L:
#     a = GET_ELEVE.search(L)
#     if a and "over" in PP[a.group(2)]:
#         (PP[a.group(2)]["over"]).append(a.group(1))
#     elif a:
#         PP[a.group(2)]["over"] = [a.group(1)]
#     L = quota.readline()
# 
# quota.close()
# 
# for k,i in PP.items():
#     if "over" in i:
#         print(i["Nom"], len(i["over"]))
#r2 = tk.Tk()
#A = tk.Frame(master=r2)
class Mailing():
    sending_param= {'test': True, 'dir': None, 'default_to':"boris@bebop",\
                    'sender': "Boris.Mauricette@ac-lyon.fr", 'relay':'smtps.ac-lyon.fr',
                    'port': 587}

    def __init__(self):
        self.pathprof = askopenfilename(initialdir="", defaultextension=".csv",\
                                   title="Fichier des profs principaux",\
                                   filetypes=[("CSV", "*.csv")])
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
        
    def _quota_analysis(self, file):
        """
        rempli les dictionnaires self.PPscribe avec une clé 'over' contenant 
        la liste des élèves en overquota.
        file: str chemin du fichier de quota (copie/colle de la sortie web
        scribe)
        """

        # remplissage profs pour scribe
        fprof=open(self.pathprof, encoding="utf8")
        dialect=csv.Sniffer().sniff(fprof.readline())
        fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fprof, dialect=dialect)
        for e in reader:
            self.PPscribe[e["nom_scribe"]] = e
        fprof.close()

        # remplissage élèves csv file
##        GET_ELEVE = re.compile("(\w+\.\w+) \(élève de ([^)]+)")
##        quota = open(file, "r") #, encoding="latin1"
##        L = quota.readline()
##        while L:
##            a = GET_ELEVE.search(L)
##            if a and "over" in self.PPscribe[a.group(2)]:
##                (self.PPscribe[a.group(2)]["over"]).append(a.group(1))
##            elif a:
##                self.PPscribe[a.group(2)]["over"] = [a.group(1)]
##            L = quota.readline()
##        quota.close()

        #analyse de la colonne "Utilisateur"
        GET_ELEVE = re.compile("(\w+\.\w+) \(élève de ([^)]+)")
        quota = open(file, "r", encoding="latin1")
        dialect=csv.Sniffer().sniff(quota.readline())
        quota.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(quota, dialect=dialect)
        self.nbel = 0 #nb élèves
        for e in reader:
            a = GET_ELEVE.search(e["Utilisateur"])
            if a and "over" in self.PPscribe[a.group(2)]:
                (self.PPscribe[a.group(2)]["over"]).append(a.group(1))
                self.nbel += 1 #nb élèves
            elif a:
                self.PPscribe[a.group(2)]["over"] = [a.group(1)]
                self.nbel += 1 #nb élèves
        quota.close()

    def _idnew_analysis(self, file):
        """
        rempli les dictionnaires self.PPelycee avec une clé 'Eleve' et ou 'Tuteur' contenant 
        la liste des nouveaux élèves et tuteurs.
        file: str chemin du fichier d'identifiants.
        """

        # remplissage profs pour elycee
        fprof=open(self.pathprof, encoding="utf8")
        dialect=csv.Sniffer().sniff(fprof.readline())
        fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fprof, dialect=dialect)
        for e in reader:
            self.PPelycee[e["nom_elycee"]] = e
        fprof.close()

        # remplissage élèves et tuteurs
        fid = open(file, "r", encoding="latin1")
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

    def _idbase_analysis(pathid):
        #todo: convert the id_extractor.py to a class
        pass

    def admin_quota(self):
        """lancer l'analyse des quotas
        """
        self.pathquotas = askopenfilename(initialdir="", defaultextension=".csv",\
                                     title="Fichier des quotas",\
                                     filetypes=[("CSV", "*.csv")])
        self._quota_analysis(self.pathquotas)
        #self.mailing("quota", **self.sending_param)

    def admin_idnew(self):
        """lancer l'analyse des nouveaux identifiants
        """
        self.pathid = askopenfilename(initialdir="", defaultextension=".txt",\
                                     title="Fichier des *nouveaux identifiants*",\
                                     filetypes=[("CSV", "*.csv")])
        self._idnew_analysis(self.pathid)
        #self.mailing("idnew", **self.sending_param)

    def admin_idbase(self):
        """génération des fichiers d'identifiants par classe, envoi aux pp
        """
        self.pathid = askopenfilename(initialdir="", defaultextension=".txt",\
                                     title="Fichier général des identifiants",\
                                     filetypes=[("CSV", "*.csv")])
        self._idbase_analysis(self.pathid)
        #self.mailing("idbase", **self.sending_param)
        
    def mailing(self, cible, **param):
        """fonction de mailing aux profs principaux
        cible: str in ["quota", "idgen", "idnew"]
        param: dictionnaire de paramètres
        test: boolean indique si on simule le mailing auquel cas, l'adresse de 
           sortie est default_to
        dir: str directory where to look for message attachments
        default_to: default target mail adr in case of test
        default_from: str who is sending
        relayhost: str smtp relay name
        port: int port value for the relay 587 for secured transaction.
        TODO: GUI, config file to save sending options.
        """

        smtprelay = ('localhost' if param["test"] else relay)
        #s = (smtplib.SMTP(smtprelay) if (param["test"] or (port not in [465, 587]))\
        #     else smtplib.SMTP_SSL(param["smtprelay"], port=param["port"]))
        if cible == "quota":
            pp = [self.PPscribe[e] for e in self.PPscribe if "over" in self.PPscribe[e]]
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
                #s.send_message(M)
                if param["test"]:
                    print(msg)
            print(self.nbel, " élèves détectés")
            print(len(pp), " profs contactés")
            #s.quit()

        elif cible == "idnew":
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
                msg+= "Merci de leur transmettre leur identifiant + mot de passe (ENT).\
\nBien cordialement,\nB.M."
                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["nom_elycee"]
                M['From'] = param["sender"]
                M['To'] = (param["default_to"] if param["test"] else E["E-mail"])
                #encoders.encode_base64(tmp)
                #s.send_message(M)
                if param["test"]:
                    print(msg)
            print(COUNT, "nouveaux élèves")
            print(len(pp), " profs contactés")
        elif cible == "idgen":
            pathid = askdirectory(initialdir="")
            pp = [self.PPelycee[e] for e in self.PPelycee]
            msg="Cher collègue, tu es prof principal de la "+E["nom_elycee"]+".\n"
            msg+="Voici la liste des identifiants et mot de passe de tes élèves en pièce jointe\n"
            msg+="Bien cordialement,\nB.M."
            M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["nom_elycee"]
            M['From'] = param["sender"]
            M['To'] = (param["default_to"] if param["test"] else E["E-mail"])
            #ajouter la pj liée au pp
            for E in pp:
                print(M)
                #s.send_message(M)
            print(len(pp), " profs contactés")

##
##a = Mailing()
##a.admin_idnew()
##exit()
