%
% sphinxryu.cls for Sphinx (http://sphinx.pocoo.org/)
%

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{sphinxryu}[2013/11/14 Document class (Sphinx ryu)]

% chapters starting at odd pages (overridden by 'openany' document option)
\PassOptionsToClass{openright}{\sphinxdocclass}

% 'oneside' option overriding the 'twoside' default
\newif\if@oneside
\DeclareOption{oneside}{\@onesidetrue}
% Pass remaining document options to the parent class.
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{\sphinxdocclass}}
\ProcessOptions\relax

% Defaults two-side document
\if@oneside
% nothing to do (oneside is the default)
\else
\PassOptionsToClass{twoside}{\sphinxdocclass}
\fi

\LoadClass{\sphinxdocclass}

% Set some sane defaults for section numbering depth and TOC depth.  You can
% reset these counters in your preamble.
%
\setcounter{secnumdepth}{2}
\setcounter{tocdepth}{1}

% Change the title page to look a bit better, and fit in with the fncychap
% ``Bjarne'' style a bit better.
%
\renewcommand{\maketitle}{%
  \begin{titlepage}%
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
        %\input{coverpage.eps_tex}
        \begingroup%
          \makeatletter%
          \ifx\svgwidth\undefined%
            \setlength{\unitlength}{595.27558594bp}%
            \ifx\svgscale\undefined%
              \relax%
            \else%
              \setlength{\unitlength}{\unitlength * \real{\svgscale}}%
            \fi%
          \else%
            \setlength{\unitlength}{\svgwidth}%
          \fi%
          \global\let\svgwidth\undefined%
          \global\let\svgscale\undefined%
          \begin{picture}(1,1.4142857)%
            \put(0,0){\includegraphics[width=\unitlength]{coverpage.eps}}%
            \put(0.920,0.600){\color[rgb]{1,1,1}\makebox(0,0)[rb]{\smash{\fontsize{46pt}{0pt}\selectfont{\sf Ryuによる}}}}%
            \put(0.920,0.500){\color[rgb]{1,1,1}\makebox(0,0)[rb]{\smash{\fontsize{46pt}{0pt}\selectfont{\sf OpenFlowプログラミング}}}}%
            \put(0.670,0.100){\color[rgb]{0,0,0}\makebox(0,0)[lb]{\smash{\fontsize{18pt}{0pt}\selectfont{\@author　著}}}}%
            \put(0.390,1.370){\color[rgb]{0,0,0}\makebox(0,0)[lb]{\smash{\fontsize{16pt}{0pt}\selectfont{\it Build SDN agilely}}}}%
            \put(0.900,1.320){\color[rgb]{1,1,1}\rotatebox{-45}{\makebox(0,0)[cb]{\smash{\fontsize{16pt}{0pt}\selectfont{\py@release\releaseinfo}}}}}%
            \put(0.870,1.300){\color[rgb]{1,1,1}\rotatebox{-45}{\makebox(0,0)[cb]{\smash{\fontsize{16pt}{0pt}\selectfont{OpenFlow 1.3対応}}}}}%
          \end{picture}%
          \makeatother%
        \endgroup%
      \end{picture}
    \endgroup
    \@thanks
  \end{titlepage}%
  \cleardoublepage%
  \setcounter{footnote}{0}%
  \let\thanks\relax\let\maketitle\relax
}


% Catch the end of the {abstract} environment, but here make sure the abstract
% is followed by a blank page if the 'openright' option is used.
%
\let\py@OldEndAbstract=\endabstract
\renewcommand{\endabstract}{
  \if@openright
    \ifodd\value{page}
      \typeout{Adding blank page after the abstract.}
      \vfil\pagebreak
    \fi
  \fi
  \py@OldEndAbstract
}

% This wraps the \tableofcontents macro with all the magic to get the spacing
% right and have the right number of pages if the 'openright' option has been
% used.  This eliminates a fair amount of crud in the individual document files.
%
\let\py@OldTableofcontents=\tableofcontents
\renewcommand{\tableofcontents}{%
  \setcounter{page}{1}%
  \pagebreak%
  \pagestyle{plain}%
  {%
    \parskip = 0mm%
    \py@OldTableofcontents%
    \if@openright%
      \ifodd\value{page}%
        \typeout{Adding blank page after the table of contents.}%
        \pagebreak\hspace{0pt}%
      \fi%
    \fi%
    \cleardoublepage%
  }%
  \pagenumbering{arabic}%
  \@ifundefined{fancyhf}{}{\pagestyle{normal}}%
}

% This is needed to get the width of the section # area wide enough in the
% library reference.  Doing it here keeps it the same for all the manuals.
%
\renewcommand*\l@section{\@dottedtocline{1}{1.5em}{2.6em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{4.1em}{3.5em}}

% Fix the bibliography environment to add an entry to the Table of
% Contents.
% For a report document class this environment is a chapter.
\let\py@OldThebibliography=\thebibliography
\renewcommand{\thebibliography}[1]{
  \cleardoublepage
  \phantomsection
  \py@OldThebibliography{1}
  \addcontentsline{toc}{chapter}{\bibname}
}
