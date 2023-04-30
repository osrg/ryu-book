FROM osrg/ryu
# ARG user=osrg

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get upgrade -y && \
    apt-get install -y -qq \
        lsb-release git sudo make \
    	inkscape texlive-latex-recommended \
    	texlive-latex-extra texlive-fonts-recommended \
    	python-minimal python-pip python-sphinx
# RUN useradd -ms /bin/bash devel
# RUN usermod -aG sudo devel
# RUN echo "devel	ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/devel
# USER devel
# WORKDIR /home/devel

CMD [ "/home/osrg/ryu-book/do-build.sh" ]
