from os import path

from docutils import nodes
from docutils.io import FileOutput
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.builders.latex import LaTeXBuilder
from sphinx.writers.latex import LaTeXWriter, LaTeXTranslator


def setup(app):
    app.add_builder(RyuLaTeXBuilder)


class RyuLaTeXBuilder(LaTeXBuilder):
    name = 'ryulatex'
    format = 'latex'

    def write(self, *ignored):
        docwriter = RyuLaTeXWriter(self)
        docsettings = OptionParser(
            defaults=self.env.settings,
            components=(docwriter,)).get_default_values()

        self.init_document_data()

        for entry in self.document_data:
            docname, targetname, title, author, docclass = entry[:5]
            toctree_only = False
            if len(entry) > 5:
                toctree_only = entry[5]
            destination = FileOutput(
                destination_path=path.join(self.outdir, targetname),
                encoding='utf-8')
            self.info("processing " + targetname + "... ", nonl=1)
            doctree = self.assemble_doctree(docname, toctree_only,
                appendices=((docclass != 'howto') and
                            self.config.latex_appendices or []))
            self.post_process_images(doctree)
            self.info("writing... ", nonl=1)
            doctree.settings = docsettings
            doctree.settings.author = author
            doctree.settings.title = title
            doctree.settings.docname = docname
            doctree.settings.docclass = docclass
            docwriter.write(doctree, destination)
            self.info("done")


class RyuLaTeXWriter(LaTeXWriter):
    def translate(self):
        visitor = RyuLaTeXTranslator(self.document, self.builder)
        self.document.walkabout(visitor)
        self.output = visitor.astext()


class RyuLaTeXTranslator(LaTeXTranslator):
    def visit_literal_block(self, node):
        code = node.astext().rstrip('\n')
        self.builder.info('node=%s' % node)
        envname = node.get('classes', None)
        if not envname:
            return LaTeXTranslator.visit_literal_block(self, node)
        envname = envname[0]
        self.body.append('\n\\begin{%s}\n%s\n\\end{%s}\n' % 
                         (envname, code, envname))
        raise nodes.SkipNode

    def visit_title(self, node):
        parent = node.parent
        if isinstance(parent, addnodes.seealso):
            # the environment already handles this
            raise nodes.SkipNode
        elif self.this_is_the_title:
            if len(node.children) != 1 and not isinstance(node.children[0],
                                                          nodes.Text):
                self.builder.warn('document title is not a single Text node',
                                  (self.curfilestack[-1], node.line))
            if not self.elements['title']:
                # text needs to be escaped since it is inserted into
                # the output literally
                self.elements['title'] = node.astext().translate(tex_escape_map)
            self.this_is_the_title = 0
            raise nodes.SkipNode
        elif isinstance(parent, nodes.section):
            try:
                number = parent.get('classes', [])
                if not number or 'unnumbered' not in number:
                    self.body.append(r'\%s{' %
                                     self.sectionnames[self.sectionlevel])
                else:
                    self.body.append(r'\%s*{' %
                                     self.sectionnames[self.sectionlevel])
                    self.addcontentsline = (
                        '\n\\addcontentsline{toc}{%s}{' %
                        self.sectionnames[self.sectionlevel])
            except IndexError:
                # just use "subparagraph", it's not numbered anyway
                self.body.append(r'\%s{' % self.sectionnames[-1])
            self.context.append('}\n')

            if self.next_section_ids:
                for id in self.next_section_ids:
                    self.context[-1] += self.hypertarget(id, anchor=False)
                self.next_section_ids.clear()

        elif isinstance(parent, (nodes.topic, nodes.sidebar)):
            self.body.append(r'\textbf{')
            self.context.append('}\n\n\medskip\n\n')
        elif isinstance(parent, nodes.Admonition):
            self.body.append('{')
            self.context.append('}\n')
        elif isinstance(parent, nodes.table):
            self.table.caption = self.encode(node.astext())
            raise nodes.SkipNode
        else:
            self.builder.warn(
                'encountered title node not in section, topic, table, '
                'admonition or sidebar',
                (self.curfilestack[-1], node.line or ''))
            self.body.append('\\textbf{')
            self.context.append('}\n')
        self.in_title = 1

    def depart_title(self, node):
        self.in_title = 0
        self.body.append(self.context.pop())
        if self.addcontentsline:
            self.body.append('%s%s}\n' % (self.addcontentsline, node.astext()))
            self.addcontentsline = None
