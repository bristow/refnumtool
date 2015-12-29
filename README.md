refnumtool
==========

Utilitaire pour les référents numériques d'EPLE par exemple en
rhones-alpes-auvergne.

Il permet de diffuser les informations vers les profs principaux et générer des
documents odt pour les parents:

 - dépassement de quota des élèves sur le serveur scribe
 - identifiants ENT elycee

Il s'appuie sur des extractions au format CSV:
 - listes des profs principaux + email par classe (ex: export pronote)
 - copie du listing scribe des dépassements de quota et mise en CSV
 - fichier général des identifiants ENT elycee ou fichier des nouveaux
   identifiants.

dépendances python:
odfpy, pyyaml