ryu-book
========

The first relase of Chinese version is made by SDN team of Institute for Information Industry in Taiwan.

Welcome to join us to help Chinese readers to more understand about Ryu.

The Chinese version test with support HTML, EPUB and PDF format.
You can use "make html" to get the HTML file or "make epub" to get EPUB file.

Because pdf generate by sphinx using LaTeX and it do not support Chinese by default.
You need XeLaTeX installed to replace pdfLaTeX beofre you get the PDF file. 
(if you install MacTeX on MAC OS then XeLaTeX will be installed by default)

Please follow the step below to get Chinese PDF file.
1. install XeLateX.
2. change the setting of Chinese fonts.
    edit the source/conf.py

    \setCJKmainfont[BoldFont=Microsoft JhengHei, ItalicFont=Microsoft JhengHei]{Microsoft JhengHei}
    \setCJKsansfont[BoldFont=Microsoft JhengHei, ItalicFont=Microsoft JhengHei]{Microsoft JhengHei}
    \setCJKmonofont[BoldFont=Microsoft JhengHei, ItalicFont=Microsoft JhengHei]{Microsoft JhengHei}
    \setCJKfamilyfont{JH}[BoldFont=Microsoft JhengHei]{Microsoft JhengHei}

    The fonts set to Microsoft JhengHei by default. Please change it depend on your environment.

3. use "make latex" to get LaTeX file.

4. go to "build/latex/" and use command "xelatex RyuBook.tex" twice to compile tex file.
    First time to generate index of TOC.
    Second time to get full document.

5. finally, get the "RyuBook.pdf" at "build/latex/"

For more information you can check the link below.
# http://osrg.github.io/ryu/resources.html#books
