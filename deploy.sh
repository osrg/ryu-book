#!/bin/bash

# exit with nonzero exit code if anything fails
set -e

# settings for the target directories
LANG_DIRS=(
en
ja
ko
zh_tw
)

# get the current commit
CURRENT_COMMIT=`git rev-parse --verify HEAD`
echo Current Commit: ${CURRENT_COMMIT}

# clone the gh-pages branch
git clone --depth=50 --branch=gh-pages https://${GH_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git gh-pages

# run our compile script
echo Targets: ${LANG_DIRS[@]}
for LANG_DIR in ${LANG_DIRS[@]}
do
    # build
    bash build.sh ${LANG_DIR}

    # update pdf
    rm -f gh-pages/${LANG_DIR}/Ryubook.pdf
    mv ${LANG_DIR}/build/latex/Ryubook.pdf gh-pages/${LANG_DIR}

    # make epub and mobi
    rm -f gh-pages/${LANG_DIR}/Ryubook.{epub,mobi}
    mv ${LANG_DIR}/build/epub/Ryubook.epub gh-pages/${LANG_DIR}
    ./kindlegen gh-pages/${LANG_DIR}/Ryubook.epub

    # make html
    rm -rf gh-pages/${LANG_DIR}/html
    mv ${LANG_DIR}/build/html gh-pages/${LANG_DIR}
done

# move on to gh-pages directory
cd gh-pages

# configure git user as Travis-CI
git config user.name "Travis-CI"
git config user.email "travis-ci@ryu-book"

# push to the remote repo's gh-pages branch.
git add --all .
git commit -m "${CURRENT_COMMIT}: Deploy to GitHub Pages"
git push --quiet origin gh-pages
