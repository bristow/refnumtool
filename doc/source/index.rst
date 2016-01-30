.. refnumtool documentation master file, created by
   sphinx-quickstart on Tue Dec 29 22:17:15 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bienvenue dans la doc de refnumtool!
====================================

:Author: Boris Mauricette <Boris point Mauricette at ac - lyon point fr> ou <teddy_boomer at yahoo point fr>
:Date: |today| 
:Revision: |version|
:page Github: https://github.com/TeddyBoomer/refnumtool
:Téléchargement: https://github.com/TeddyBoomer/refnumtool/releases

Présentation
^^^^^^^^^^^^

Le module vise à faciliter la vie des référents numériques: d'un côté ils
disposent de bases de données (identifiants, quotas, profs principaux), de
l'autre ils doivent diffuser des informations aux profs principaux.

Il s'agit donc de publiposter les bonnes informations (identifiants, mdp,
quotas) aux profs principaux.

Sécurité
^^^^^^^^

Est-il judicieux de choisir une diffusion par mail? C'est clairement un point
de fragilité quant à la sécurité des données. Toutefois, ici on diffuse au
travers du smtp sécurisé du rectorat: les messages restent à l'intérieur des
machines académiques et sont délivrés directement dans les boîtes
académiques. A priori, à aucun moment, les messages ne vont transiter sur
d'autres serveurs.

Par ailleurs, la connexion smtp est sécurisée (transaction SSL). Donc la
sécurité des données peut-être considérée comme garantie.

Il faut juste veiller (évidemment…) à choisir les adresses académiques des PP
pour la diffusion.

Table des matières:
^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 2

   install.rst
   history.rst
   api.rst
