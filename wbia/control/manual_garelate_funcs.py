# -*- coding: utf-8 -*-
"""
Autogenerated IBEISController functions

TemplateInfo:
    autogen_time = 13:34:34 2015/04/28
    autogen_key = gar

ToRegenerate:
    python -m wbia.templates.template_generator --key gar --Tcfg with_web_api=True with_api_cache=False with_deleters=True no_extern_deleters=True --diff
    python -m wbia.templates.template_generator --key gar --Tcfg with_web_api=True with_api_cache=False with_deleters=True no_extern_deleters=True --write
"""
from __future__ import absolute_import, division, print_function
from six.moves import zip
from wbia import constants as const
import utool as ut
from wbia.control import controller_inject
from wbia.control import accessor_decors

print, rrr, profile = ut.inject2(__name__)

# Create dectorator to inject functions in this module into the IBEISController
CLASS_INJECT_KEY, register_ibs_method = controller_inject.make_ibs_register_decorator(
    __name__
)


register_api = controller_inject.get_wbia_flask_api(__name__)


def testdata_ibs(defaultdb='testdb1'):
    import wbia

    ibs = wbia.opendb(defaultdb=defaultdb)
    config2_ = None  # qreq_.qparams
    return ibs, config2_


# AUTOGENED CONSTANTS:
GAR_ROWID = 'gar_rowid'
ANNOTGROUP_ROWID = 'annotgroup_rowid'
ANNOT_ROWID = 'annot_rowid'


@register_ibs_method
# @register_api('/api/gar/', methods=['GET'])
def _get_all_gar_rowids(ibs):
    """ all_gar_rowids <- gar.get_all_rowids()

    Returns:
        list_ (list): unfiltered gar_rowids

    TemplateInfo:
        Tider_all_rowids
        tbl = gar

    Example:
        >>> # ENABLE_DOCTEST
        >>> from wbia.control.manual_garelate_funcs import *  # NOQA
        >>> ibs, config2_ = testdata_ibs()
        >>> ibs._get_all_gar_rowids()
    """
    all_gar_rowids = ibs.db.get_all_rowids(const.GA_RELATION_TABLE)
    return all_gar_rowids


@register_ibs_method
# @register_api('/api/gar/', methods=['POST'])
def add_gar(ibs, annotgroup_rowid_list, aid_list):
    """
    Returns:
        returns gar_rowid_list of added (or already existing gars)

    TemplateInfo:
        Tadder_native
        tbl = gar
    """
    # WORK IN PROGRESS
    colnames = (
        ANNOTGROUP_ROWID,
        ANNOT_ROWID,
    )
    # if aid_list is None:
    #    aid_list = [None] * len(annotgroup_rowid_list)
    params_iter = (
        (annotgroup_rowid, aid,)
        for (annotgroup_rowid, aid,) in zip(annotgroup_rowid_list, aid_list)
    )
    get_rowid_from_superkey = ibs.get_gar_rowid_from_superkey
    # FIXME: encode superkey paramx
    superkey_paramx = (0, 1)
    gar_rowid_list = ibs.db.add_cleanly(
        const.GA_RELATION_TABLE,
        colnames,
        params_iter,
        get_rowid_from_superkey,
        superkey_paramx,
    )
    return gar_rowid_list


@register_ibs_method
# @register_api('/api/gar/', methods=['DELETE'])
def delete_gar(ibs, gar_rowid_list, config2_=None):
    """ gar.delete(gar_rowid_list)

    delete gar rows

    Args:
        gar_rowid_list

    Returns:
        int: num_deleted

    TemplateInfo:
        Tdeleter_native_tbl
        tbl = gar

    Example:
        >>> # DISABLE_DOCTEST
        >>> from wbia.control.manual_garelate_funcs import *  # NOQA
        >>> ibs, config2_ = testdata_ibs()
        >>> gar_rowid_list = ibs._get_all_gar_rowids()[:2]
        >>> num_deleted = ibs.delete_gar(gar_rowid_list)
        >>> print('num_deleted = %r' % (num_deleted,))
    """
    # from wbia.algo.preproc import preproc_gar
    # NO EXTERN IMPORT
    if ut.VERBOSE:
        print('[ibs] deleting %d gar rows' % len(gar_rowid_list))
    # Prepare: Delete externally stored data (if any)
    # preproc_gar.on_delete(ibs, gar_rowid_list, config2_=config2_)
    # NO EXTERN DELETE
    # Finalize: Delete self
    ibs.db.delete_rowids(const.GA_RELATION_TABLE, gar_rowid_list)
    num_deleted = len(ut.filter_Nones(gar_rowid_list))
    return num_deleted


@register_ibs_method
@accessor_decors.getter_1to1
# @register_api('/api/gar/annot/rowid/', methods=['GET'])
def get_gar_aid(ibs, gar_rowid_list, eager=True, nInput=None):
    """ aid_list <- gar.aid[gar_rowid_list]

    gets data from the "native" column "aid" in the "gar" table

    Args:
        gar_rowid_list (list):

    Returns:
        list: aid_list

    TemplateInfo:
        Tgetter_table_column
        col = aid
        tbl = gar

    Example:
        >>> # ENABLE_DOCTEST
        >>> from wbia.control.manual_garelate_funcs import *  # NOQA
        >>> ibs, config2_ = testdata_ibs()
        >>> gar_rowid_list = ibs._get_all_gar_rowids()
        >>> eager = True
        >>> aid_list = ibs.get_gar_aid(gar_rowid_list, eager=eager)
        >>> assert len(gar_rowid_list) == len(aid_list)
    """
    id_iter = gar_rowid_list
    colnames = (ANNOT_ROWID,)
    aid_list = ibs.db.get(
        const.GA_RELATION_TABLE,
        colnames,
        id_iter,
        id_colname='rowid',
        eager=eager,
        nInput=nInput,
    )
    return aid_list


@register_ibs_method
@accessor_decors.getter_1to1
# @register_api('/api/gar/annotgroup/rowid/', methods=['GET'])
def get_gar_annotgroup_rowid(ibs, gar_rowid_list, eager=True, nInput=None):
    """ annotgroup_rowid_list <- gar.annotgroup_rowid[gar_rowid_list]

    gets data from the "native" column "annotgroup_rowid" in the "gar" table

    Args:
        gar_rowid_list (list):

    Returns:
        list: annotgroup_rowid_list

    TemplateInfo:
        Tgetter_table_column
        col = annotgroup_rowid
        tbl = gar

    Example:
        >>> # ENABLE_DOCTEST
        >>> from wbia.control.manual_garelate_funcs import *  # NOQA
        >>> ibs, config2_ = testdata_ibs()
        >>> gar_rowid_list = ibs._get_all_gar_rowids()
        >>> eager = True
        >>> annotgroup_rowid_list = ibs.get_gar_annotgroup_rowid(gar_rowid_list, eager=eager)
        >>> assert len(gar_rowid_list) == len(annotgroup_rowid_list)
    """
    id_iter = gar_rowid_list
    colnames = (ANNOTGROUP_ROWID,)
    annotgroup_rowid_list = ibs.db.get(
        const.GA_RELATION_TABLE,
        colnames,
        id_iter,
        id_colname='rowid',
        eager=eager,
        nInput=nInput,
    )
    return annotgroup_rowid_list


@register_ibs_method
def get_gar_rowid_from_superkey(
    ibs, annotgroup_rowid_list, aid_list, eager=True, nInput=None
):
    """ gar_rowid_list <- gar[annotgroup_rowid_list, aid_list]

    Args:
        superkey lists: annotgroup_rowid_list, aid_list

    Returns:
        gar_rowid_list

    TemplateInfo:
        Tgetter_native_rowid_from_superkey
        tbl = gar
    """
    colnames = (GAR_ROWID,)
    # FIXME: col_rowid is not correct
    params_iter = zip(annotgroup_rowid_list, aid_list)
    andwhere_colnames = [ANNOTGROUP_ROWID, ANNOT_ROWID]
    gar_rowid_list = ibs.db.get_where_eq(
        const.GA_RELATION_TABLE,
        colnames,
        params_iter,
        andwhere_colnames,
        eager=eager,
        nInput=nInput,
    )
    return gar_rowid_list
