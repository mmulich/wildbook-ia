# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals
import utool as ut
from ibeis.templates import notebook_cells
from functools import partial


def autogen_ipynb(ibs, launch=None, run=None):
    r"""
    Autogenerates standard IBEIS Image Analysis IPython notebooks.

    CommandLine:
        python -m ibeis --tf autogen_ipynb --run --db lynx
        python -m ibeis --tf autogen_ipynb --ipynb --db lynx
        python -m ibeis --tf autogen_ipynb --ipynb --db Oxford -a default:qhas_any=\(query,\),dpername=1,exclude_reference=True,dminqual=good
        python -m ibeis --tf autogen_ipynb --ipynb --db PZ_MTEST -a default -t best:lnbnn_normalizer=[None,normlnbnn-test]

        python -m ibeis.templates.generate_notebook --exec-autogen_ipynb --db wd_peter_blinston --ipynb

        python -m ibeis --tf autogen_ipynb --db PZ_Master1 --ipynb
        python -m ibeis --tf autogen_ipynb --db PZ_Master1 -a timectrl:qindex=0:100 -t best best:normsum=True --ipynb --noexample
        python -m ibeis --tf autogen_ipynb --db PZ_Master1 -a timectrl --run
        jupyter-notebook Experiments-lynx.ipynb
        killall python

        python -m ibeis --tf autogen_ipynb --db humpbacks --ipynb -t default:proot=BC_DTW -a default:has_any=hasnotch
        python -m ibeis --tf autogen_ipynb --db humpbacks --ipynb -t default:proot=BC_DTW default:proot=vsmany -a default:has_any=hasnotch,mingt=2,qindex=0:50 --noexample

    Example:
        >>> # SCRIPT
        >>> from ibeis.templates.generate_notebook import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> result = autogen_ipynb(ibs)
        >>> print(result)
    """
    dbname = ibs.get_dbname()
    fname = 'Experiments-' + dbname
    nb_fpath = fname + '.ipynb'
    if ut.get_argflag('--cells'):
        notebook_cells = make_ibeis_cell_list(ibs)
        print('\n# ---- \n'.join(notebook_cells))
        return
    notebook_str = make_ibeis_notebook(ibs)
    ut.writeto(nb_fpath, notebook_str)
    run = ut.get_argflag('--run') if run is None else run
    launch = launch if launch is not None else ut.get_argflag('--ipynb')
    if run:
        run_nb = run_ipython_notebook(notebook_str)
        output_fpath = export_notebook(run_nb, fname)
        ut.startfile(output_fpath)
    elif launch:
        ut.cmd('jupyter-notebook', nb_fpath, detatch=True)
        #ut.cmd('ipython-notebook', nb_fpath)
        #ut.startfile(nb_fpath)
    else:
        print('notebook_str =\n%s' % (notebook_str,))


def get_default_cell_template_list(ibs):
    cells = notebook_cells

    noexample = ut.get_argflag('--noexample')

    cell_template_list = [
        cells.initialize,

        None if ibs.get_dbname() != 'humpbacks' else cells.fluke_select,

        cells.pipe_config_info,
        cells.annot_config_info,

        None if noexample else cells.timestamp_distribution,
        None if noexample else cells.example_annotations,
        None if noexample else cells.example_names,

        cells.per_annotation_accuracy,
        cells.per_name_accuracy,
        cells.timedelta_distribution,
        cells.config_overlap,
        #cells.dbsize_expt,

        None if ibs.get_dbname() == 'humpbacks' else cells.feat_score_sep,

        cells.all_annot_scoresep,
        cells.success_annot_scoresep,
        cells.easy_success_cases,
        cells.hard_success_cases,
        cells.failure_type1_cases,
        cells.failure_type2_cases,
        #cells.investigate_specific_case,
        #cells.view_intereseting_tags,

        # TODO:
        # show query chips

    ]
    cell_template_list = ut.filter_Nones(cell_template_list)
    return cell_template_list


def export_notebook(run_nb, fname):
    import IPython.nbconvert.exporters
    import codecs
    #exporter = IPython.nbconvert.exporters.PDFExporter()
    exporter = IPython.nbconvert.exporters.HTMLExporter()
    output, resources = exporter.from_notebook_node(run_nb)
    ext = resources['output_extension']
    output_fpath = fname + ext
    #codecs.open(output_fname, 'w', encoding='utf-8').write(output)
    codecs.open(output_fpath, 'w').write(output)
    return output_fpath
    #IPython.nbconvert.exporters.export_python(runner.nb)


def run_ipython_notebook(notebook_str):
    """
    References:
        https://github.com/paulgb/runipy
        >>> from ibeis.templates.generate_notebook import *  # NOQA
    """
    from runipy.notebook_runner import NotebookRunner
    import nbformat
    import logging
    log_format = '%(asctime)s %(levelname)s: %(message)s'
    log_datefmt = '%m/%d/%Y %I:%M:%S %p'
    logging.basicConfig(
        level=logging.INFO, format=log_format, datefmt=log_datefmt
    )
    #fpath = 'tmp.ipynb'
    #notebook_str = ut.readfrom(fpath)
    #nb3 = IPython.nbformat.reads(notebook_str, 3)
    #cell = nb4.cells[1]
    #self = runner
    #runner = NotebookRunner(nb3, mpl_inline=True)
    print('Executing IPython notebook')
    nb4 = nbformat.reads(notebook_str, 4)
    runner = NotebookRunner(nb4)
    runner.run_notebook(skip_exceptions=False)
    run_nb = runner.nb
    return run_nb


def make_autogen_str():
    import sys

    def get_regen_cmd():
        # TODO: move to utool
        try:
            if len(sys.argv) > 0 and ut.checkpath(sys.argv[0]):
                # Check if running python command
                if ut.is_python_module(sys.argv[0]):
                    python_exe = ut.python_executable(check=False)
                    modname = ut.get_modname_from_modpath(sys.argv[0])
                    new_argv = [python_exe, '-m', modname] + sys.argv[1:]
                    return ' '.join(new_argv)
        except Exception as ex:
            ut.printex(ex, iswarning=True)
        return ' '.join(sys.argv)

    autogenkw = dict(
        stamp=ut.timestamp('printable'),
        regen_cmd=get_regen_cmd()
        #' '.join(sys.argv)
    )
    return ut.codeblock(
        '''
        # Autogenerated on {stamp}
        # Regen Command:
        #    {regen_cmd}
        #
        '''
    ).format(**autogenkw)


def make_ibeis_notebook(ibs):
    r"""
    Args:
        ibs (IBEISController):  ibeis controller object

    CommandLine:
        python -m ibeis.templates.generate_notebook --exec-make_ibeis_notebook --db wd_peter_blinston
        python -m ibeis.templates.generate_notebook --exec-make_ibeis_notebook
        python -m ibeis --tf make_ibeis_notebook --db lynx
        jupyter-notebook tmp.ipynb

        runipy tmp.ipynb --html report.html
        runipy --pylab tmp.ipynb tmp2.ipynb

        sudo pip install runipy

        python -c "import runipy; print(runipy.__version__)"

    Example:
        >>> # SCRIPYT
        >>> from ibeis.templates.generate_notebook import *  # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb(defaultdb='testdb1')
        >>> notebook_str = make_ibeis_notebook(ibs)
        >>> print(notebook_str)
    """
    cell_list = make_ibeis_cell_list(ibs)
    notebook_str = make_notebook(cell_list)

    try:
        import json
        json.loads(notebook_str)
    except ValueError as ex:
        ut.printex(ex, 'Invalid notebook JSON')
        raise

    return notebook_str


def make_ibeis_cell_list(ibs):
    cell_template_list = get_default_cell_template_list(ibs)
    autogen_str = make_autogen_str()
    dbname = ibs.get_dbname()
    #if ut.get_argflag('--hacktestscore'):
    #    annotconfig_list_body = ut.codeblock(
    #        '''
    #        'timectrl',
    #        '''
    #    )
    #else:
    default_acfgstr = ut.get_argval('-a', type_=str, default='default:is_known=True')
    annotconfig_list_body = ut.codeblock(
        ut.repr2(default_acfgstr) + '\n' +
        ut.codeblock('''
        # See ibeis/expt/annotation_configs.py for names of annot configuration options
        #'default:has_any=(query,),dpername=1,exclude_reference=True',
        #'default:is_known=True',
        #'default:qsame_imageset=True,been_adjusted=True,excluderef=True'
        #'default:qsame_imageset=True,been_adjusted=True,excluderef=True,qsize=10,dsize=20',
        #'default:require_timestamp=True,min_timedelta=3600',
        #'default:species=primary',
        #'timectrl:',
        #'timectrl:been_adjusted=True,dpername=3',
        #'timectrl:qsize=10,dsize=20',
        #'unctrl:been_adjusted=True',
        ''')
    )
    #if ut.get_argflag('--hacktestscore'):
    #    pipeline_list_body = ut.codeblock(
    #        '''
    #        # See ibeis/algo/Config.py for names of pipeline config options
    #        'default:lnbnn_on=True,bar_l2_on=False,normonly_on=False,fg_on=True',
    #        'default:lnbnn_on=False,bar_l2_on=True,normonly_on=False,fg_on=True',
    #        'default:lnbnn_on=False,bar_l2_on=False,normonly_on=True,fg_on=True',
    #        'default:lnbnn_on=True,bar_l2_on=False,normonly_on=False,fg_on=False',
    #        'default:lnbnn_on=False,bar_l2_on=True,normonly_on=False,fg_on=False',
    #        'default:lnbnn_on=False,bar_l2_on=False,normonly_on=True,fg_on=False',
    #        '''
    #    )
    #elif True:
    default_pcfgstr_list = ut.get_argval(('-t', '-p'), type_=list, default='default')
    default_pcfgstr = ut.repr3(default_pcfgstr_list, nobr=True)

    pipeline_list_body = ut.codeblock(
        default_pcfgstr + '\n' +
        ut.codeblock('''
        #'default',
        #'default:K=1',
        #'default:K=1,AI=False',
        #'default:K=1,AI=False,QRH=True',
        #'default:K=1,RI=True,AI=False',
        #'default:K=1,adapteq=True',
        #'default:fg_on=[True,False]',
        ''')
    )
    locals_ = locals()
    _format = partial(format_cells, locals_=locals_)
    cell_list = ut.flatten(map(_format, cell_template_list))
    return cell_list


def format_cells(block, locals_=None):
    try:
        if isinstance(block, tuple):
            header, code = block
        else:
            header = None
            code = block
        if locals_ is not None:

            def modify_code_indent_formatdict(code, locals_):
                # Parse out search and replace locations in code
                ncl1 = ut.negative_lookbehind('{')
                ncl2 = ut.negative_lookahead('{')
                ncr1 = ut.negative_lookbehind('}')
                ncr2 = ut.negative_lookahead('}')
                left = ncl1 + '{' + ncl2
                right = ncr1 + '}' + ncr2
                fmtpat = left + ut.named_field('key', '[^}]*') + right
                spacepat = ut.named_field('indent', '^\s+')
                pattern = spacepat + fmtpat
                import re
                seen_ = set([])
                for m in re.finditer(pattern, code, flags=re.MULTILINE):
                    indent = (m.groupdict()['indent'])
                    key = (m.groupdict()['key'])
                    if key in locals_ and key not in seen_:
                        seen_.add(key)
                        locals_[key] = ut.indent_rest(locals_[key], indent)

            modify_code_indent_formatdict(code, locals_)
            code_ = code.format(**locals_)
            ut.is_valid_python(code_, reraise=True, ipy_magic_workaround=True)
        else:
            code_ = code
        if header is not None:
            return [markdown_cell(header), code_cell(code_)]
        else:
            return [code_cell(code_)]
    except Exception as ex:
        ut.printex(ex, 'failed to format cell', keys=['header', 'block'])
        raise


def code_cell(sourcecode):
    r"""
    Args:
        sourcecode (str):

    Returns:
        str: json formatted ipython notebook code cell

    CommandLine:
        python -m ibeis.templates.generate_notebook --exec-code_cell

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.templates.generate_notebook import *  # NOQA
        >>> sourcecode = notebook_cells.timestamp_distribution[1]
        >>> sourcecode = notebook_cells.initialize[1]
        >>> result = code_cell(sourcecode)
        >>> print(result)
    """
    from ibeis.templates.template_generator import remove_sentinals
    sourcecode = remove_sentinals(sourcecode)
    cell_header = ut.codeblock(
        """
        {
         "cell_type": "code",
         "execution_count": null,
         "metadata": {
          "collapsed": true
         },
         "outputs": [],
         "source":
        """)
    cell_footer = ut.codeblock(
        """
        }
        """)
    if sourcecode is None:
        source_line_repr = ' []\n'
    else:
        lines = sourcecode.split('\n')
        line_list = [line + '\n' if count < len(lines) else line
                     for count, line in enumerate(lines, start=1)]
        #repr_line_list = [repr_single(line) for line in line_list]
        repr_line_list = [repr_single(line) for line in line_list]
        source_line_repr = ut.indent(',\n'.join(repr_line_list), ' ' * 2)
        source_line_repr = ' [\n' + source_line_repr + '\n ]\n'
    return (cell_header + source_line_repr + cell_footer)


def markdown_cell(markdown):
    r"""
    Args:
        markdown (str):

    Returns:
        str: json formatted ipython notebook markdown cell

    CommandLine:
        python -m ibeis.templates.generate_notebook --exec-markdown_cell

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.templates.generate_notebook import *  # NOQA
        >>> markdown = '# Title'
        >>> result = markdown_cell(markdown)
        >>> print(result)
    """
    markdown_header = ut.codeblock(
        """
          {
           "cell_type": "markdown",
           "metadata": {},
           "source": [
        """
    )
    markdown_footer = ut.codeblock(
        """
           ]
          }
        """
    )
    return (markdown_header + '\n' +
            ut.indent(repr_single(markdown), ' ' * 2) +
            '\n' + markdown_footer)


def make_notebook(cell_list):
    """
    References:
        # Change cell width
        http://stackoverflow.com/questions/21971449/how-do-i-increase-the-cell-width-of-the-ipython-notebook-in-my-browser/24207353#24207353
    """
    header = ut.codeblock(
        """
        {
         "cells": [
        """
    )

    footer = ut.codeblock(
        """
         ],
         "metadata": {
          "kernelspec": {
           "display_name": "Python 2",
           "language": "python",
           "name": "python2"
          },
          "language_info": {
           "codemirror_mode": {
            "name": "ipython",
            "version": 2
           },
           "file_extension": ".py",
           "mimetype": "text/x-python",
           "name": "python",
           "nbconvert_exporter": "python",
           "pygments_lexer": "ipython2",
           "version": "2.7.6"
          }
         },
         "nbformat": 4,
         "nbformat_minor": 0
        }
        """)

    cell_body = ut.indent(',\n'.join(cell_list), '  ')
    notebook_str = header + '\n' + cell_body +  '\n' +  footer
    return notebook_str


def repr_single(s):
    r"""
    Args:
        s (str):

    Returns:
        str: str_repr

    CommandLine:
        python -m ibeis.templates.generate_notebook --exec-repr_single --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.templates.generate_notebook import *  # NOQA
        >>> s = '#HTML(\'<iframe src="%s" width=700 height=350></iframe>\' % pdf_fpath)'
        >>> result = repr_single(s)
        >>> print(result)
    """
    if True:
        str_repr = ut.reprfunc(s)
        import re
        if str_repr.startswith('\''):
            dq = (ut.DOUBLE_QUOTE)
            sq = (ut.SINGLE_QUOTE)
            bs = (ut.BACKSLASH)
            dq_, sq_, bs_ = list(map(re.escape, [dq, sq, bs]))
            no_bs = ut.negative_lookbehind(bs_)
            #no_sq = ut.negative_lookbehind(sq)
            #no_dq = ut.negative_lookbehind(dq)

            #inside = str_repr[1:-1]
            #inside = re.sub(no_bs + dq, bs + dq, inside)
            #inside = re.sub(no_bs + bs + sq, r"\\'", r"'", inside)
            #str_repr = '"' + inside + '"'
            #inside = re.sub(r'"', r'\\"', inside)
            #inside = re.sub(ut.negative_lookbehind(r"'") + r"\\'", r"'", inside)

            inside = str_repr[1:-1]
            # Escape double quotes
            inside = re.sub(no_bs + r'"', r'\\"', inside)
            # Unescape single quotes
            inside = re.sub(no_bs + bs_ + r"'", r"'", inside)
            # Append external double quotes
            str_repr = '"' + inside + '"'
        return str_repr
    else:
        return '"' + ut.reprfunc('\'' + s)[2:]


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.templates.generate_notebook
        python -m ibeis.templates.generate_notebook --allexamples
        python -m ibeis.templates.generate_notebook --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
