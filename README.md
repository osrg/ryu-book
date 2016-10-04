ryu-book
========

Currently, Japanese, English, Chinese and Korean editions are available. You can get the various formats; pdf, mobi, epub, and html (automatically updated every time the source is updated) at:

# http://osrg.github.io/ryu/resources.html#books


Building Ryu-Book on local
==========================

Before building the Ryu-Book for each language,
please set up the building environment as follow.

Ubuntu 16.04 LTS:

```
# Install the requirements
$ sudo apt-get update
$ sudo apt-get -y install inkscape texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended

# Set up the building environment
# Note: It is highly recommended to use a virtualenv.
$ sudo pip install virtualenv
$ virtualenv venv
$ source venv/bin/activate
(venv) $ pip install -r requirements.txt
(venv) $ python setup.py install

# e.g.) Build the English version
(venv) $ bash ./build.sh en
```


Building Ryu-Book on Travis-CI
==============================

You can build the Ryu-Book on Travis-CI and deploy to the GitHub pages
on your forked repository.
For setting up your Travis-CI environment, please create your GItHub
[Personal access tokens](https://github.com/settings/tokens/new) first.
If your repository is public, please enable "public_repo" scope.
And please set your GitHub token into `.travis.yml` by using
[`travis` command](https://github.com/travis-ci/travis.rb) as follow.

```
$ gem install travis
$ travis encrypt -r <your Travis-CI account>/ryu-book GH_TOKEN=<your GitHub token> --add
```

Please confirm the encrypted GitHub token is updated in `.travis.yml`.

```
$ git diff .travis.yml
...(snip)
 env:
   global:
-    secure: <original GitHub token>  # if exist, remove original one
+  - secure: <your GitHub token(encrypted)>
```

By the default, Travis-CI will build "master" branch only.
If you want to build other branches, please modify "branches.only" key
in `.travis.yml` as follow.

```
$ git diff .travis.yml
...(snip)
 branches:
-  only:
-  - master
+  except:
+  - gh-pages
 install:
...(snip)
```

Finally, please add your forked repository on your Travis-CI and enable
"Build only if .travis.yml is present" and "Build pushes" at "General
Settings" for your repository.
Then, your can see your "own" Ryu-Book should be built on Travis-CI
when pushing your branches to your repository.

Note: If you have modified `.travis.yml` for your repository, please
do NOT merge it to upstream of Ryu-Book.
