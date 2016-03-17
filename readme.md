===================
API-CORE
===================

Description rapide de l'api CORE

Cette API vient avec une méthode ``single_instance`` .

Compactible
* Python 2.6, 2.7, PyPy, 3.3, and 3.4 supported on Linux and OS X.
* Python 2.7, 3.3, and 3.4 supported on Windows (both 32 and 64 bit versions of Python).


![Géré par Charles](https://data.whicdn.com/images/222505936/superthumb.jpg) Readme par Charles


Attribution
===========

But: Projet de fin d'année SupTranscode.

Supported Libraries
===================

* `Flask <http://flask.pocoo.org/>`_ 0.10.1
* `Celery <http://www.celeryproject.org/>`_ 3.1.11
* `FFmpeg <http://www.faqforge.com/linux/how-to-install-ffmpeg-on-ubuntu-14-04/>

Quickstart
==========

Install:
```sh
    apt-get install python
```

Puis

```sh
    apt-get install python-pip
```
Vous avez une base fonctionnelle permettant le lancement du projet. Il faut désormais installer les dépendances à utiliser.

```sh
    pip install flask
```
et
```sh	
    pip install Celery
```
RabbitMQ est présent nativement dans Celery. Il n'y a donc pas d'utilité à faire un ``pip install rabbitmq``.


Examples
========

Lancement de l'API
-------------

```sh
   python app.py
```

Attention: FAITES UNE REDIRECTION DE PORT OU PENSEZ A FAIRE UN IPTABLES EN RAPPORT (l'application se lance sur le port 5000 par défaut):

```sh
   iptables -A INPUT -m state --state NEW -m tcp -p tcp --dport 5000 -j ACCEPT
```
Exemples d'utilisations
---------------
Extraction audio

```web
   http://localhost:5000/extract/name=test.mp4&output=test
```
Comme le nom l'indique... Extraction audio. Name est le fichier d'entrée, et output est le nom du fichier de sortie. Le fichier sera en mp3. 

Conversion vidéo
-------------
```sh
http://localhost:5000/convert/name=12.mp4&typec=avi
```
La vidéo à convertir. Name est le fichier d'entrée et typec est le type de sortie (ex: avi dans ce cas)

Couper vidéo en parties de 30 secondes
-------------
```sh
http://localhost:5000/separate/name=12.mp4
```
La vidéo sera coupée en parties de 30 secondes. Name est le fichier d'entrée

Créer liste txt des fichiers découpés => (NON OBLIGATOIRE, LE SEPARATE GENERE DEJA LE FICHIER TXT)
-------------
```sh
http://localhost:5000/generate/name=12.mp4
```


Concat des vidéos
-------------
```sh
http://localhost:5000/concat/name=BUU.mp4.txt
```
La vidéo sera regroupée. name est le fichier texte d'entrée

