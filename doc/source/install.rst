Installation
============

Python
^^^^^^

Les scripts sont écrits en Python3. Il vous est conseillé d'utiliser une
version de Python >=3.4. En effet, à partir de là, l'installateur pip
standardise l'installation des modules (et utilise le plus récent format
d'archive **wheel**)

le module dépend de **odfpy** et **pyyaml** pour la génération de fichiers
opendocument et l'utilisation de fichiers de configuration au format yaml
(texte lisible par les humains).

Il s'agit donc d'installer d'abord les dépendances puis l'archive wheel .whl

Pour windows::

  py -3 -m pip install odfpy pyyaml \chemin\vers\refnumtool-0.1-py3-none-any.whl

Pour linux::

  sudo pip3 install odfpy pyyaml /chemin/vers/refnumtool-0.1-py3-none-any.whl

Il peut y avoir des messages de warning pour l'installation de pyyaml du fait
d'une liaison possible à d'autres bibliothèques (plus rapides)… pas
d'inquiétude.
