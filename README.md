ryu-book
========

Currently, Japanese, English, Chinese and Korean editions are available. You can get the various formats; pdf, mobi, epub, and html (automatically updated every time the source is updated) at:

# http://osrg.github.io/ryu/resources.html#books


Build procedure
===============

Before building the Ryu-Book for each language,
please set up the building environment as follow.
The following is an example the creation of the English version.

Ubuntu 16.04 LTS:

```
$ sudo apt-get update
$ sudo apt-get -y install inkscape texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended
# It is highly recommended to use a virtualenv.
$ sudo pip install virtualenv
$ virtualenv venv
$ source venv/bin/activate
(venv) $ pip install .
(venv) $ ./build.sh en
```
