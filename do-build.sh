#!/bin/bash

cd $(dirname $0)
# sudo python -m pip install --upgrade pip
pip install -r requirements.txt
python setup.py install
make -C en clean
make -C en PAPER=a4 latexpdf
cp -vf en/build/latex/Ryubook.pdf en
