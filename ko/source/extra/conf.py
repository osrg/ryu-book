# -*- coding: utf-8 -*-

import sys, os

sys.path.insert(0, os.path.abspath('..'))

from conf import *

latex_elements['preamble'] += (
u"""
% ---- Title page
\\makeatletter

\\def\\ryutitle{Ryuによる}
\\def\\ryutitleb{OpenFlowプログラミング}
\\def\\cho{著}
\\def\\ryutop{Build SDN agilely}
\\def\\ryuextra{OpenFlow 1.3対応}
"""
r"""
\renewcommand{\maketitle}{
 \begin{titlepage}
  \let\footnotesize\small
  \let\footnoterule\relax
  \ifsphinxpdfoutput
   \begingroup
   % These \defs are required to deal with multi-line authors; it
   % changes \\ to ', ' (comma-space), making it pass muster for
   % generating document info in the PDF file.
   \def\\{, }
   \def\and{and }
   \pdfinfo{
     /Author (\@author)
     /Title (\@title)
   }
   \endgroup
  \fi
  \begingroup
   \setlength{\unitlength}{1truemm}
   \begin{picture}(210,234)(25,38)
    \begingroup
     \makeatletter
     \ifx\svgwidth\undefined
      \setlength{\unitlength}{595.27558594bp}
      \ifx\svgscale\undefined
       \relax
      \else
       \setlength{\unitlength}{\unitlength * \real{\svgscale}}
      \fi
     \else
      \setlength{\unitlength}{\svgwidth}
     \fi
     \global\let\svgwidth\undefined
     \global\let\svgscale\undefined
     \begin{picture}(1,1.4142857)
      \put(0,0){\includegraphics[width=\unitlength]{coverpage.eps}}
      \put(0.920,0.600){\color[rgb]{1,1,1}\makebox(0,0)[rb]{\smash{\fontsize{46pt}{0pt}\selectfont{\sf \ryutitle}}}}
      \put(0.920,0.500){\color[rgb]{1,1,1}\makebox(0,0)[rb]{\smash{\fontsize{46pt}{0pt}\selectfont{\sf \ryutitleb}}}}
      \put(0.670,0.100){\color[rgb]{0,0,0}\makebox(0,0)[lb]{\smash{\fontsize{18pt}{0pt}\selectfont{\@author\hskip1em\cho}}}}
      \put(0.390,1.370){\color[rgb]{0,0,0}\makebox(0,0)[lb]{\smash{\fontsize{16pt}{0pt}\selectfont{\it \ryutop}}}}
      \put(0.900,1.320){\color[rgb]{1,1,1}\rotatebox{-45}{\makebox(0,0)[cb]{\smash{\fontsize{16pt}{0pt}\selectfont{\py@release\releaseinfo}}}}}
      \put(0.870,1.300){\color[rgb]{1,1,1}\rotatebox{-45}{\makebox(0,0)[cb]{\smash{\fontsize{16pt}{0pt}\selectfont{\ryuextra}}}}}
     \end{picture}
     \makeatother
    \endgroup
   \end{picture}
  \endgroup
  \@thanks
 \end{titlepage}
 \cleardoublepage
 \setcounter{footnote}{0}
 \let\thanks\relax\let\maketitle\relax
}

\makeatother
""")

latex_additional_files += ['extra/coverpage.eps']
latex_additional_files = ['../' + x for x in latex_additional_files]
