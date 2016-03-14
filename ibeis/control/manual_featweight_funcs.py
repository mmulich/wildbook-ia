# -*- coding: utf-8 -*-
"""
"""
from __future__ import absolute_import, division, print_function
import functools  # NOQA
import six  # NOQA
from six.moves import map, range, zip  # NOQA
import utool as ut
from ibeis.control import controller_inject
from ibeis.control import accessor_decors  # NOQA
print, print_, printDBG, rrr, profile = ut.inject(__name__, '[autogen_featweight]')

# Create dectorator to inject functions in this module into the IBEISController
CLASS_INJECT_KEY, register_ibs_method = controller_inject.make_ibs_register_decorator(__name__)
register_route = controller_inject.get_ibeis_flask_route(__name__)


def testdata_ibs(defaultdb='testdb1'):
    import ibeis
    ibs = ibeis.opendb(defaultdb=defaultdb)
    config2_ = None  # qreq_.qparams
    return ibs, config2_

# AUTOGENED CONSTANTS:
ANNOT_ROWID                 = 'annot_rowid'
CHIP_ROWID                  = 'chip_rowid'
CONFIG_ROWID                = 'config_rowid'
FEATURE_ROWID               = 'feature_rowid'
FEATWEIGHT_FORGROUND_WEIGHT = 'featweight_forground_weight'
FEATWEIGHT_ROWID            = 'featweight_rowid'
FEAT_ROWID                  = 'feature_rowid'

NEW_DEPC = True


@register_ibs_method
def get_annot_featweight_rowids(ibs, aid_list, config2_=None, ensure=True, eager=True, nInput=None):
    if NEW_DEPC:
        return ibs.depc.get_rowids('featweight', aid_list, config=config2_)
    ## Get leaf_parent rowids
    #feat_rowid_list = ibs.get_annot_feat_rowids(
    #    aid_list, config2_=config2_, ensure=ensure)
    #featweight_rowid_list = get_feat_featweight_rowids(
    #    ibs, feat_rowid_list, config2_=config2_, ensure=ensure)
    #return featweight_rowid_list


@register_ibs_method
def get_annot_fgweights(ibs, aid_list, config2_=None, ensure=True):
    """ featweight_rowid_list <- annot.featweight.fgweights[aid_list]

    Get fgweight data of the annot table using the dependant featweight table

    Args:
        aid_list (list):

    Returns:
        list: fgweight_list

    TemplateInfo:
        Tgetter_rl_pclines_dependant_column
        root = annot
        col  = fgweight
        leaf = featweight
    """
    if NEW_DEPC:
        return ibs.depc.get('featweight', aid_list, 'fwg', config=config2_)


if __name__ == '__main__':
    """
    CommandLine:
        python -m ibeis.control._autogen_featweight_funcs
        python -m ibeis.control._autogen_featweight_funcs --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()
    import utool as ut
    ut.doctest_funcs()
