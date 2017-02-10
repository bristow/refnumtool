Personnaliser
=============

Le dossier des paramètres généraux est `%homeuser%/.refnumtool.d`.

Il contient des fichiers yaml contenant les paramètres suivants:

* config.yaml:
  
  - default_to: adresse de destinataire par défaut en cas d'activation du mode test
  - initialdir: répertoire de recherche par défaut pour les fichiers csv    
  - login: identifiant pour l'envoi mail
  - port: port d'envoi smtp
  - sender: adresse mail d'expéditeur
  - sig: signature à apposer à la fin des messages
  - smtp: nom du serveur d'envoi smtp
  - test: true/false activation du mode test pour le publipostage.

    En mode test, les messages sont envoyés en local vers default_to (ceci
    fonctionne sous linux quand un MTU type postfix est configuré).

* Les autres fichiers yaml contiennent la liste des phrases pour les
  publipostages.
