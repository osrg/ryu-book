ryu-book
========

The first relase of Korean version is made by Ian Y. Choi (ian@naimnetworks.com), supported by NAIM Networks Inc. and OpenFlow Korea.

Welcome to join us to help Korean readers to more understand about Ryu.

This Korean version now supports HTML, EPUB and PDF format.
You can use "make html" to get the HTML file or "make epub" to get EPUB file.
You can use "make latexpdfko" to get Korean version PDF file.

Although kotex is more widely used in Korean, 
I configured to use XeLaTeX because kotex is not familiar with foreigners. 
I mainly refered to the configuration from @peteryui, 
who created Chinese version of this book.

Because using LaTeX to generate PDF by sphinx does not support Korean by default,
you need to install XeLaTeX to replace pdfLaTeX before you get the PDF file. 
(if you install MacTeX on MAC OS then XeLaTeX will be installed by default)

Please follow the step below to get Korean PDF file.
1. Install XeLateX.
2. Edit source/conf.py if you change to another Korean fonts:
    % English fonts
    \setmainfont{Apple SD Gothic Neo Medium}
    % Korean fonts
    \setCJKmainfont{Apple SD Gothic Neo Medium}
    \setCJKmonofont{Apple SD Gothic Neo Medium}
    \setCJKsansfont{Apple SD Gothic Neo Medium}
    \setCJKfamilyfont{APPLE}{Apple Gothic}
3. use "make latexpdfko" to get PDF file at "build/latex/".

I tested in my macbook and it works well with mactex.env.sh and changing LC_CTYPE to C.

For more information you can check the link below.
# http://osrg.github.io/ryu/resources.html#books
