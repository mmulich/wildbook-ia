#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Exports subset of an IBEIS database to a new IBEIS database
"""
from __future__ import absolute_import, division, print_function
import utool as ut
from ibeis.other import ibsfuncs
from ibeis import constants as const


def check_merge(ibs_src, ibs_dst):
    aid_list1 = ibs_src.get_valid_aids()
    gid_list1 = ibs_src.get_annot_gids(aid_list1)
    gname_list1 = ibs_src.get_image_uris(gid_list1)
    image_uuid_list1 = ibs_src.get_image_uuids(gid_list1)
    gid_list2 = ibs_dst.get_image_gids_from_uuid(image_uuid_list1)
    gname_list2 = ibs_dst.get_image_uris(gid_list2)
    # Asserts
    ut.assert_all_not_None(gid_list1, 'gid_list1')
    ut.assert_all_not_None(gid_list2, 'gid_list2')
    ut.assert_lists_eq(gname_list1, gname_list2, 'faild gname')
    # Image UUIDS should be consistent between databases
    image_uuid_list2 = ibs_dst.get_image_uuids(gid_list2)
    ut.assert_lists_eq(image_uuid_list1, image_uuid_list2, 'failed uuid')

    aids_list1 = ibs_src.get_image_aids(gid_list1)
    aids_list2 = ibs_dst.get_image_aids(gid_list2)

    avuuids_list1 = ibs_src.unflat_map(
        ibs_src.get_annot_visual_uuids, aids_list1)
    avuuids_list2 = ibs_dst.unflat_map(
        ibs_dst.get_annot_visual_uuids, aids_list2)

    issubset_list = [set(avuuids1).issubset(set(avuuids2))
                     for avuuids1, avuuids2 in zip(avuuids_list1, avuuids_list2)]
    assert all(issubset_list), 'ibs_src must be a subset of ibs_dst: issubset_list=%r' % (
        issubset_list,)
    #aids_depth1 = ut.depth_profile(aids_list1)
    #aids_depth2 = ut.depth_profile(aids_list2)
    # depth might not be true if ibs_dst is not empty
    #ut.assert_lists_eq(aids_depth1, aids_depth2, 'failed depth')
    print('Merge seems ok...')


def merge_databases(ibs_src, ibs_dst, rowid_subsets=None, localize_images=True):
    """
    New way of merging using the non-hacky sql table merge.
    However, its only workings due to major hacks.

    FIXME: annotmatch table

    CommandLine:
        python -m ibeis --test-merge_databases

        python -m ibeis merge_databases:0
        python -m ibeis merge_databases:0 --db1 PZ_Master0 --db2 PZ_Master1
        python -m ibeis merge_databases:0 --db1 NNP_Master3 --db2 PZ_Master1

        python -m ibeis merge_databases:0 --db1 GZ_ALL --db2 GZ_Master1
        python -m ibeis merge_databases:0 --db1 lewa_grevys --db2 GZ_Master1

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.dbio.export_subset import *  # NOQA
        >>> import ibeis
        >>> db1 = ut.get_argval('--db1', str, default=None)
        >>> db2 = ut.get_argval('--db2', str, default=None)
        >>> dbdir1 = ut.get_argval('--dbdir1', str, default=None)
        >>> dbdir2 = ut.get_argval('--dbdir2', str, default=None)
        >>> delete_ibsdir = False
        >>> # Check for test mode instead of script mode
        >>> if db1 is None and db2 is None and dbdir1 is None and dbdir2 is None:
        ...     db1 = 'testdb1'
        ...     dbdir2 = 'testdb_dst'
        ...     delete_ibsdir = True
        >>> # Open the source and destination database
        >>> assert db1 is not None or dbdir1 is not None
        >>> assert db2 is not None or dbdir2 is not None
        >>> ibs_src = ibeis.opendb(db=db1, dbdir=dbdir1)
        >>> ibs_dst = ibeis.opendb(db=db2, dbdir=dbdir2, allow_newdir=True,
        >>>                        delete_ibsdir=delete_ibsdir)
        >>> merge_databases(ibs_src, ibs_dst)
        >>> check_merge(ibs_src, ibs_dst)
        >>> ibs_dst.print_dbinfo()
    """
    # TODO: ensure images are localized
    # otherwise this wont work
    print('BEGIN MERGE OF %r into %r' %
          (ibs_src.get_dbname(), ibs_dst.get_dbname()))
    # ibs_src.run_integrity_checks()
    # ibs_dst.run_integrity_checks()
    ibs_dst.update_annot_visual_uuids(ibs_dst.get_valid_aids())
    ibs_src.update_annot_visual_uuids(ibs_src.get_valid_aids())
    ibs_src.ensure_contributor_rowids()
    ibs_dst.ensure_contributor_rowids()
    ibs_src.fix_invalid_annotmatches()
    ibs_dst.fix_invalid_annotmatches()
    # Hack move of the external data
    if rowid_subsets is not None and const.IMAGE_TABLE in rowid_subsets:
        gid_list = rowid_subsets[const.IMAGE_TABLE]
    else:
        gid_list = ibs_src.get_valid_gids()
    imgpath_list = ibs_src.get_image_paths(gid_list)
    dst_imgdir = ibs_dst.get_imgdir()
    if localize_images:
        ut.copy_files_to(imgpath_list, dst_imgdir, overwrite=False, verbose=True)
    ignore_tables = [
        'lblannot', 'lblimage', 'image_lblimage_relationship',
        'annotation_lblannot_relationship', 'keys'
    ]
    # ignore_tables += [
    #     'contributors', 'party', 'configs'
    # ]
    # TODO: Fix database merge to allow merging tables with more than one superkey
    # and no primary superkey.
    error_tables = [
        'imageset_image_relationship',
        'annotgroup_annotation_relationship',
        # 'annotmatch',
    ]
    ignore_tables += error_tables
    ibs_dst.db.merge_databases_new(
        ibs_src.db, ignore_tables=ignore_tables, rowid_subsets=rowid_subsets)
    print('FINISHED MERGE %r into %r' %
          (ibs_src.get_dbname(), ibs_dst.get_dbname()))


def make_new_dbpath(ibs, id_label, id_list):
    """
    Creates a new database path unique to the exported subset of ids.
    """
    import ibeis
    tag_hash = ut.hashstr_arr(id_list, hashlen=8, alphabet=ut.ALPHABET_27)
    base_fmtstr = ibs.get_dbname() + '_' + id_label + 's=' + \
        tag_hash.replace('(', '_').replace(')', '_') + '_%d'
    dpath = ibeis.get_workdir()
    new_dbpath = ut.get_nonconflicting_path_old(base_fmtstr, dpath)
    return new_dbpath


def export_names(ibs, nid_list, new_dbpath=None):
    r"""
    exports a subset of names and other required info

    Args:
        ibs (IBEISController):  ibeis controller object
        nid_list (list):

    CommandLine:
        python -m ibeis.dbio.export_subset --test-export_names

    Example:
        >>> # DISABLE_DOCTEST
        >>> from ibeis.dbio.export_subset import *  # NOQA
        >>> import ibeis
        >>> # build test data
        >>> ibs = ibeis.opendb('testdb2')
        >>> ibs.delete_empty_nids()
        >>> nid_list = ibs._get_all_known_nids()[0:2]
        >>> # execute function
        >>> result = export_names(ibs, nid_list)
        >>> # verify results
        >>> print(result)
    """
    print('Exporting name nid_list=%r' % (nid_list,))
    if new_dbpath is None:
        new_dbpath = make_new_dbpath(ibs, 'nid', nid_list)

    aid_list = ut.flatten(ibs.get_name_aids(nid_list))
    gid_list = ut.unique_unordered(ibs.get_annot_gids(aid_list))

    return export_data(ibs, gid_list, aid_list, nid_list, new_dbpath=new_dbpath)


def find_gid_list(ibs, min_count=500, ensure_annots=False):
    import random
    gid_list = ibs.get_valid_gids()
    reviewed_list = ibs.get_image_reviewed(gid_list)

    if ensure_annots:
        aids_list = ibs.get_image_aids(gid_list)
        reviewed_list = [
            0 if len(aids) == 0 else reviewed
            for aids, reviewed in zip(aids_list, reviewed_list)
        ]

    # Filter by reviewed
    gid_list = [
        gid
        for gid, reviewed in zip(gid_list, reviewed_list)
        if reviewed == 1
    ]

    if len(gid_list) < min_count:
        return None

    while len(gid_list) > min_count:
        index = random.randint(0, len(gid_list) - 1)
        del gid_list[index]

    return gid_list


def __export_reviewed_subset(ibs, min_count=500, ensure_annots=False):
    from os.path import join
    gid_list = find_gid_list(
        ibs, min_count=min_count, ensure_annots=ensure_annots)
    if gid_list is None:
        return None
    new_dbpath = '/' + join('Datasets', 'BACKGROUND', ibs.dbname)
    print('Exporting to %r with %r images' % (new_dbpath, len(gid_list), ))
    return export_images(ibs, gid_list, new_dbpath=new_dbpath)


def export_images(ibs, gid_list, new_dbpath=None):
    """
    exports a subset of images and other required info

    TODO:
        PZ_Master1 needs to backproject information back on to NNP_Master3 and PZ_Master0

    Args:
        ibs (IBEISController):  ibeis controller object
        gid_list (list):  list of annotation rowids
        new_dbpath (None): (default = None)

    Returns:
        str: new_dbpath
    """
    print('Exporting image gid_list=%r' % (gid_list,))
    if new_dbpath is None:
        new_dbpath = make_new_dbpath(ibs, 'gid', gid_list)

    aid_list = ut.unique_unordered(ut.flatten(ibs.get_image_aids(gid_list)))
    nid_list = ut.unique_unordered(ibs.get_annot_nids(aid_list))

    return export_data(ibs, gid_list, aid_list, nid_list, new_dbpath=new_dbpath)


def export_annots(ibs, aid_list, new_dbpath=None):
    r"""
    exports a subset of annotations and other required info

    TODO:
        PZ_Master1 needs to backproject information back on to NNP_Master3 and
        PZ_Master0

    Args:
        ibs (IBEISController):  ibeis controller object
        aid_list (list):  list of annotation rowids
        new_dbpath (None): (default = None)

    Returns:
        str: new_dbpath

    CommandLine:
        python -m ibeis.dbio.export_subset export_annots
        python -m ibeis.dbio.export_subset export_annots --db NNP_Master3 \
            -a viewpoint_compare --nocache-aid --verbtd --new_dbpath=PZ_ViewPoints

        python -m ibeis.expt.experiment_helpers get_annotcfg_list:0 \
            --db NNP_Master3 \
            -a viewpoint_compare --nocache-aid --verbtd
        python -m ibeis.expt.experiment_helpers get_annotcfg_list:0 --db NNP_Master3 \
            -a viewpoint_compare --nocache-aid --verbtd
        python -m ibeis.expt.experiment_helpers get_annotcfg_list:0 --db NNP_Master3 \
            -a default:aids=all,is_known=True,view_pername=#primary>0&#primary1>0,per_name=4,size=200
        python -m ibeis.expt.experiment_helpers get_annotcfg_list:0 --db NNP_Master3 \
            -a default:aids=all,is_known=True,view_pername='#primary>0&#primary1>0',per_name=4,size=200 --acfginfo

        python -m ibeis.expt.experiment_helpers get_annotcfg_list:0 --db PZ_Master1 \
            -a default:has_any=photobomb --acfginfo

    Example:
        >>> # SCRIPT
        >>> from ibeis.dbio.export_subset import *  # NOQA
        >>> import ibeis
        >>> from ibeis.expt import experiment_helpers
        >>> ibs = ibeis.opendb(defaultdb='NNP_Master3')
        >>> acfg_name_list = ut.get_argval(('--aidcfg', '--acfg', '-a'), type_=list, default=[''])
        >>> acfg_list, expanded_aids_list = experiment_helpers.get_annotcfg_list(ibs, acfg_name_list)
        >>> aid_list = expanded_aids_list[0][0]
        >>> ibs.print_annot_stats(aid_list, yawtext_isect=True, per_image=True)
        >>> # Expand to get all annots in each chosen image
        >>> gid_list = ut.unique_ordered(ibs.get_annot_gids(aid_list))
        >>> aid_list = ut.flatten(ibs.get_image_aids(gid_list))
        >>> ibs.print_annot_stats(aid_list, yawtext_isect=True, per_image=True)
        >>> new_dbpath = ut.get_argval('--new-dbpath', default='PZ_ViewPoints')
        >>> new_dbpath = export_annots(ibs, aid_list, new_dbpath)
        >>> result = ('new_dbpath = %s' % (str(new_dbpath),))
        >>> print(result)
    """
    print('Exporting annotations aid_list=%r' % (aid_list,))
    if new_dbpath is None:
        new_dbpath = make_new_dbpath(ibs, 'aid', aid_list)
    gid_list = ut.unique(ibs.get_annot_gids(aid_list))
    nid_list = ut.unique(ibs.get_annot_nids(aid_list))
    return export_data(ibs, gid_list, aid_list, nid_list, new_dbpath=new_dbpath)


def export_data(ibs, gid_list, aid_list, nid_list, new_dbpath=None):
    """
    exports a subset of data and other required info

    Args:
        ibs (IBEISController):  ibeis controller object
        gid_list (list):  list of image rowids
        aid_list (list):  list of annotation rowids
        nid_list (list):  list of name rowids
        imgsetid_list (list):  list of imageset rowids
        gsgrid_list (list):  list of imageset-image pairs rowids
        new_dbpath (None): (default = None)

    Returns:
        str: new_dbpath
    """
    import ibeis

    imgsetid_list = ut.unique_unordered(ut.flatten(ibs.get_image_imgsetids(gid_list)))
    gsgrid_list = ut.unique_unordered(
        ut.flatten(ibs.get_image_gsgrids(gid_list)))

    # TODO: write SQL query to do this
    am_rowids = ibs._get_all_annotmatch_rowids()
    flags1_list = [
        aid in set(aid_list) for aid in ibs.get_annotmatch_aid1(am_rowids)]
    flags2_list = [
        aid in set(aid_list) for aid in ibs.get_annotmatch_aid2(am_rowids)]
    flag_list = ut.and_lists(flags1_list, flags2_list)
    am_rowids = ut.compress(am_rowids, flag_list)
    #am_rowids = ibs.get_valid_aids(ibs.get_valid_aids())

    rowid_subsets = {
        const.ANNOTATION_TABLE: aid_list,
        const.NAME_TABLE: nid_list,
        const.IMAGE_TABLE: gid_list,
        const.ANNOTMATCH_TABLE: am_rowids,
        const.GSG_RELATION_TABLE: gsgrid_list,
        const.IMAGESET_TABLE: imgsetid_list,
    }
    ibs_dst = ibeis.opendb(dbdir=new_dbpath, allow_newdir=True)
    # Main merge driver
    merge_databases(ibs, ibs_dst, rowid_subsets=rowid_subsets)
    print('Exported to %r' % (new_dbpath,))
    return new_dbpath


def slow_merge_test():
    r"""
    CommandLine:
        python -m ibeis.dbio.export_subset --test-slow_merge_test

    Example:
        >>> # SLOW_DOCTEST
        >>> from ibeis.dbio.export_subset import *  # NOQA
        >>> result = slow_merge_test()
        >>> print(result)
    """
    from ibeis.dbio import export_subset
    import ibeis
    ibs1 = ibeis.opendb('testdb2')
    ibs1.fix_invalid_annotmatches()
    ibs_dst = ibeis.opendb(
        db='testdb_dst2', allow_newdir=True, delete_ibsdir=True)
    export_subset.merge_databases(ibs1, ibs_dst)
    #ibs_src = ibs1
    check_merge(ibs1, ibs_dst)

    ibs2 = ibeis.opendb('testdb1')
    ibs1.print_dbinfo()
    ibs2.print_dbinfo()
    ibs_dst.print_dbinfo()

    ibs_dst.print_dbinfo()

    export_subset.merge_databases(ibs2, ibs_dst)
    #ibs_src = ibs2
    check_merge(ibs2, ibs_dst)

    ibs3 = ibeis.opendb('PZ_MTEST')
    export_subset.merge_databases(ibs3, ibs_dst)
    #ibs_src = ibs2
    check_merge(ibs3, ibs_dst)

    ibs_dst.print_dbinfo()
    return ibs_dst

    #ibs_src.print_annotation_table(exclude_columns=['annot_verts',
    #'annot_semantic_uuid', 'annot_note', 'annot_parent_rowid',
    #'annot_exemplar_flag,'])
    # ibs_dst.print_annotation_table()


def remerge_subset(ibs1, ibs2):
    """
    Assumes ibs1 is an updated subset of ibs2.
    Re-merges ibs1 back into ibs2.
    """
    import ibeis
    ibs1 = ibeis.opendb('PZ_PB_RF_TRAIN')
    ibs2 = ibeis.opendb('PZ_Master1')

    gids1, gids2 = ibs1.images(), ibs2.images()
    idxs1, idxs2 = ut.isect_indices(gids1.uuids, gids2.uuids)
    isect_gids1, isect_gids2 = gids1.take(idxs1), gids2.take(idxs2)

    assert all(
        set.issubset(set(a1), set(a2))
        for a1, a2 in zip(isect_gids1.annot_uuids, isect_gids2.annot_uuids)
    )

    annot_uuids = ut.flatten(isect_gids1.annot_uuids)
    aids1 = ibs1.annots(ibs1.get_annot_aids_from_uuid(annot_uuids), asarray=True)
    aids2 = ibs2.annots(ibs2.get_annot_aids_from_uuid(annot_uuids), asarray=True)
    import numpy as np

    to_aids2 = dict(zip(aids1, aids2))
    to_aids1 = dict(zip(aids2, aids1))

    # Step 1) Update individual annot properties
    # These annots need updates
    np.where(aids1.visual_uuids != aids2.visual_uuids)
    np.where(aids1.semantic_uuids != aids2.semantic_uuids)

    # Step 2) Update annotmatch - pairwise relationships
    from ibeis.algo.hots import graph_iden
    infr1 = graph_iden.AnnotInference(aids=aids1.aids, ibs=ibs1)
    infr2 = graph_iden.AnnotInference(aids=aids2.aids, ibs=ibs2)

    fb1 = infr1.read_ibeis_annotmatch_feedback()
    # feedback = fb1
    # fb1_df = infr1._pandas_feedback_format(fb1)

    # fb1_df = infr1._pandas_feedback_format(fb1)
    # fb2_df = infr2._pandas_feedback_format(
    #     infr2.read_ibeis_annotmatch_feedback())
    # map into ibs2 aids
    fb1_t = {(to_aids2[u], to_aids2[v]): val
             for (u, v), val in fb1.items()}
    fb1_df_t = infr2._pandas_feedback_format(fb1_t)
    infr2.reset_feedback()
    infr2.add_feedback_df(fb1_df_t)

    delta = infr2.match_state_delta()

    """
    TODO:
        Task 1:
            first transfer all singleton (non-name) properties
            of names from ibs1 to ibs2 (
                this includes bounding box, quality, viewpoint,
                unary_tags, orientation
            )

        Task 2:
            Build AnnotInfr for ibs2 then add all decision from
            ibs1 to the internal feedback dict.

            Ensure that all other (esp old name-id related) edges are correctly
            placed, then overrite with new vals (
                make sure implicit vals do not cuase conflicts with new
                explicit vals, but old explicit vals should cause a conflict).
            Then just commit to staging and then commit to annotmatch and
            re-infer the names.
    """

    # Print some info about the delta
    def _to_tup(x):
        return tuple(x) if isinstance(x, list) else x
    changetype_list = list(zip(
        delta['old_decision'], delta['new_decision'],
        map(_to_tup, delta['old_tags']),
        map(_to_tup, delta['new_tags'])))
    changetype_hist = ut.dict_hist(changetype_list, ordered=True)
    print(ut.align(ut.repr4(changetype_hist), ':'))

    import pandas as pd
    pd.options.display.max_rows = 20
    pd.options.display.max_columns = 40
    pd.options.display.width = 160
    pd.options.display.float_format = lambda x: '%.4f' % (x,)

    from ibeis.gui import inspect_gui
    a, b = 86,    6265
    c, d = to_aids1[a], to_aids1[b]
    inspect_gui.show_vsone_tuner(ibs2, a, b)
    inspect_gui.show_vsone_tuner(ibs1, to_aids1[a], to_aids1[b])
    am1 = ibs1.get_annotmatch_rowids_between([to_aids1[a]],
                                             [to_aids1[b]])
    am2 = ibs2.get_annotmatch_rowids_between([a], [b])
    print(ibs1.db.get_table_csv('annotmatch', rowids=am1))
    print(ibs2.db.get_table_csv('annotmatch', rowids=am2))

    inspect_gui.show_vsone_tuner(ibs2, 8, 242)
    inspect_gui.show_vsone_tuner(ibs2, 86, 103)
    inspect_gui.show_vsone_tuner(ibs2, 86, 6265)



def check_database_overlap(ibs1, ibs2):
    """
    CommandLine:
        python -m ibeis.other.dbinfo --test-get_dbinfo:1 --db PZ_MTEST
        dev.py -t listdbs
        python -m ibeis.dbio.export_subset check_database_overlap
        --db PZ_MTEST --db2 PZ_MOTHERS

    CommandLine:
        python -m ibeis.dbio.export_subset check_database_overlap

        python -m ibeis.dbio.export_subset check_database_overlap --db1=PZ_MTEST --db2=PZ_Master0  # NOQA
        python -m ibeis.dbio.export_subset check_database_overlap --db1=NNP_Master3 --db2=PZ_Master0  # NOQA

        python -m ibeis.dbio.export_subset check_database_overlap --db1=GZ_Master0 --db2=GZ_ALL
        python -m ibeis.dbio.export_subset check_database_overlap --db1=GZ_ALL --db2=lewa_grevys

        python -m ibeis.dbio.export_subset check_database_overlap --db1=PZ_FlankHack --db2=PZ_Master1
        python -m ibeis.dbio.export_subset check_database_overlap --db1=PZ_PB_RF_TRAIN --db2=PZ_Master1


    Example:
        >>> # SCRIPT
        >>> from ibeis.dbio.export_subset import *  # NOQA
        >>> import ibeis
        >>> import utool as ut
        >>> #ibs1 = ibeis.opendb(db='PZ_Master0')
        >>> #ibs2 = ibeis.opendb(dbdir='/raid/work2/Turk/PZ_Master')
        >>> db1 = ut.get_argval('--db1', str, default='PZ_MTEST')
        >>> db2 = ut.get_argval('--db2', str, default='testdb1')
        >>> dbdir1 = ut.get_argval('--dbdir1', str, default=None)
        >>> dbdir2 = ut.get_argval('--dbdir2', str, default=None)
        >>> ibs1 = ibeis.opendb(db=db1, dbdir=dbdir1)
        >>> ibs2 = ibeis.opendb(db=db2, dbdir=dbdir2)
        >>> check_database_overlap(ibs1, ibs2)
    """
    import numpy as np
    import vtool as vt

    def print_isect(items1, items2, lbl=''):
        set1_ = set(items1)
        set2_ = set(items2)
        items_isect = set1_.intersection(set2_)
        fmtkw1 = dict(part=1, lbl=lbl, num=len(set1_),
                      num_isect=len(items_isect),
                      percent=100 * len(items_isect) / len(set1_))
        fmtkw2 = dict(part=2, lbl=lbl, num=len(set2_),
                      num_isect=len(items_isect),
                      percent=100 * len(items_isect) / len(set2_))
        fmt_a = '  * Num {lbl} {part}: {num_isect} / {num} = {percent:.2f}%'
        # fmt_b = '  * Num {lbl} isect: {num}'
        print('Checking {lbl} intersection'.format(lbl=lbl))
        print(fmt_a.format(**fmtkw1))
        print(fmt_a.format(**fmtkw2))
        # print(fmt_b.format(lbl=lbl, num=len(items_isect)))
        # items = items_isect
        # list_ = items1
        x_list1 = ut.find_list_indexes(items1, items_isect)
        x_list2 = ut.find_list_indexes(items2, items_isect)
        return x_list1, x_list2

    gids1 = ibs1.images()
    gids2 = ibs2.images()

    # Find common images
    # items1, items2, lbl, = gids1.uuids, gids2.uuids, 'images'
    gx_list1, gx_list2 = print_isect(gids1.uuids, gids2.uuids, 'images')
    gids_isect1 = gids1.take(gx_list1)
    gids_isect2 = gids2.take(gx_list2)
    assert gids_isect2.uuids == gids_isect1.uuids, 'sequence must be aligned'

    SHOW_ISECT_GIDS = False
    if SHOW_ISECT_GIDS:
        if len(gx_list1) > 0:
            print('gids_isect1 = %r' % (gids_isect1,))
            print('gids_isect2 = %r' % (gids_isect2,))
            if False:
                # Debug code
                import ibeis.viz
                import plottool as pt
                gid_pairs = list(zip(gids_isect1, gids_isect2))
                pairs_iter = ut.ichunks(gid_pairs, chunksize=8)
                for fnum, pairs in enumerate(pairs_iter, start=1):
                    pnum_ = pt.make_pnum_nextgen(nRows=len(pairs), nCols=2)
                    for gid1, gid2 in pairs:
                        ibeis.viz.show_image(
                            ibs1, gid1, pnum=pnum_(), fnum=fnum)
                        ibeis.viz.show_image(
                            ibs2, gid2, pnum=pnum_(), fnum=fnum)

    # if False:
    #     aids1 = ibs1.get_valid_aids()
    #     aids2 = ibs2.get_valid_aids()
    #     ibs1.update_annot_visual_uuids(aids1)
    #     ibs2.update_annot_visual_uuids(aids2)
    #     ibs1.update_annot_semantic_uuids(aids1)
    #     ibs2.update_annot_semantic_uuids(aids2)

    # Check to see which intersecting images have different annotations
    image_aids_isect1 = gids_isect1.aids
    image_aids_isect2 = gids_isect2.aids
    image_avuuids_isect1 = np.array(
        ibs1.unflat_map(ibs1.get_annot_visual_uuids, image_aids_isect1))
    image_avuuids_isect2 = np.array(
        ibs2.unflat_map(ibs2.get_annot_visual_uuids, image_aids_isect2))
    changed_image_xs = np.nonzero(
        image_avuuids_isect1 != image_avuuids_isect2)[0]
    if len(changed_image_xs) > 0:
        print('There are %d images with changes in annotation visual information' % (
            len(changed_image_xs),))
        changed_gids1 = ut.take(gids_isect1, changed_image_xs)
        changed_gids2 = ut.take(gids_isect2, changed_image_xs)

        SHOW_CHANGED_GIDS = False
        if SHOW_CHANGED_GIDS:
            print('gids_isect1 = %r' % (changed_gids2,))
            print('gids_isect2 = %r' % (changed_gids1,))
            # if False:
            #     # Debug code
            #     import ibeis.viz
            #     import plottool as pt
            #     gid_pairs = list(zip(changed_gids1, changed_gids2))
            #     pairs_iter = ut.ichunks(gid_pairs, chunksize=8)
            #     for fnum, pairs in enumerate(pairs_iter, start=1):
            #         pnum_ = pt.make_pnum_nextgen(nRows=len(pairs), nCols=2)
            #         for gid1, gid2 in pairs:
            #             ibeis.viz.show_image(
            #                 ibs1, gid1, pnum=pnum_(), fnum=fnum)
            #             ibeis.viz.show_image(
            #                 ibs2, gid2, pnum=pnum_(), fnum=fnum)

    # Check for overlapping annotations (visual info only) in general
    aids1 = ibs1.annots()
    aids2 = ibs2.annots()

    # Check for overlapping annotations (visual + semantic info) in general
    aux_list1, aux_list2 = print_isect(
        aids1.uuids, aids2.uuids, 'uuids')
    avx_list1, avx_list2 = print_isect(
        aids1.visual_uuids, aids2.visual_uuids, 'vuuids')
    asx_list1, asx_list2 = print_isect(
        aids1.semantic_uuids, aids2.semantic_uuids, 'suuids')

    # Check which images with the same visual uuids have different semantic
    # uuids
    changed_ax_list1 = ut.setdiff_ordered(avx_list1, asx_list1)
    changed_ax_list2 = ut.setdiff_ordered(avx_list2, asx_list2)
    assert len(changed_ax_list1) == len(changed_ax_list2)
    assert ut.take(aids1.visual_uuids, changed_ax_list1) == ut.take(
        aids2.visual_uuids, changed_ax_list2)

    changed_aids1 = np.array(ut.take(aids1, changed_ax_list1))
    changed_aids2 = np.array(ut.take(aids2, changed_ax_list2))

    changed_sinfo1 = ibs1.get_annot_semantic_uuid_info(changed_aids1)
    changed_sinfo2 = ibs2.get_annot_semantic_uuid_info(changed_aids2)
    sinfo1_arr = np.array(changed_sinfo1)
    sinfo2_arr = np.array(changed_sinfo2)
    is_semantic_diff = sinfo2_arr != sinfo1_arr
    # Inspect semantic differences
    if np.any(is_semantic_diff):
        colxs, rowxs = np.nonzero(is_semantic_diff)
        colx2_rowids = ut.group_items(rowxs, colxs)
        prop2_rowids = ut.map_dict_keys(
            changed_sinfo1._fields.__getitem__, colx2_rowids)
        print('changed_value_counts = ' +
              ut.dict_str(ut.map_dict_vals(len, prop2_rowids)))
        yawx = changed_sinfo1._fields.index('yaw')

        # Show change in viewpoints
        if len(colx2_rowids[yawx]) > 0:
            vp_category_diff = ibsfuncs.viewpoint_diff(
                sinfo1_arr[yawx], sinfo2_arr[yawx]).astype(np.float)
            # Look for category changes
            #any_diff = np.floor(vp_category_diff) > 0
            #_xs    = np.nonzero(any_diff)[0]
            #_aids1 = changed_aids1.take(_xs)
            #_aids2 = changed_aids2.take(_xs)
            # Look for significant changes
            is_significant_diff = np.floor(vp_category_diff) > 1
            significant_xs = np.nonzero(is_significant_diff)[0]
            significant_aids1 = changed_aids1.take(significant_xs)
            significant_aids2 = changed_aids2.take(significant_xs)
            print('There are %d significant viewpoint changes' %
                  (len(significant_aids2),))
            #vt.ori_distance(sinfo1_arr[yawx], sinfo2_arr[yawx])
            #zip(ibs1.get_annot_yaw_texts(significant_aids1),
            #ibs2.get_annot_yaw_texts(significant_aids2))
            # print('yawdiff = %r' % )
            # if False:
            # Hack: Apply fixes
            # good_yaws = ibs2.get_annot_yaws(significant_aids2)
            # ibs1.set_annot_yaws(significant_aids1, good_yaws)
            #    pass
            if False:
                # Debug code
                import ibeis.viz
                import plottool as pt
                #aid_pairs = list(zip(_aids1, _aids2))
                aid_pairs = list(zip(significant_aids1, significant_aids2))
                pairs_iter = ut.ichunks(aid_pairs, chunksize=8)
                for fnum, pairs in enumerate(pairs_iter, start=1):
                    pnum_ = pt.make_pnum_nextgen(nRows=len(pairs), nCols=2)
                    for aid1, aid2 in pairs:
                        ibeis.viz.show_chip(
                            ibs1, aid1, pnum=pnum_(), fnum=fnum, show_yawtext=True, nokpts=True)
                        ibeis.viz.show_chip(
                            ibs2, aid2, pnum=pnum_(), fnum=fnum, show_yawtext=True, nokpts=True)

    #
    nAnnots_per_image1 = np.array(ibs1.get_image_num_annotations(gids1))
    nAnnots_per_image2 = np.array(ibs2.get_image_num_annotations(gids2))
    #
    images_without_annots1 = sum(nAnnots_per_image1 == 0)
    images_without_annots2 = sum(nAnnots_per_image2 == 0)
    print('images_without_annots1 = %r' % (images_without_annots1,))
    print('images_without_annots2 = %r' % (images_without_annots2,))

    nAnnots_per_image1

    class AlignedIndex(object):

        def __init__(self):
            self.iddict_ = {}

        def make_aligned_arrays(self, id_lists, data_lists):
            idx_lists = [vt.compute_unique_data_ids_(
                id_list, iddict_=self.iddict_) for id_list in id_lists]
            aligned_data = []
            for idx_list, data_array in zip(idx_lists, data_lists):
                array = np.full(len(self.iddict_), None)
                array[idx_list] = data_array
                aligned_data.append(array)
            return aligned_data

    # Try to figure out the conflicts
    # TODO: finishme

    # self = AlignedIndex()
    # id_lists = (image_uuids1, image_uuids2)
    # data_lists = (nAnnots_per_image1, nAnnots_per_image2)
    # aligned_data = self.make_aligned_arrays(id_lists, data_lists)
    # nAnnots1_aligned, nAnnots2_aligned = aligned_data

    # nAnnots_difference = nAnnots1_aligned - nAnnots2_aligned
    # nAnnots_difference = np.nan_to_num(nAnnots_difference)
    # print('images_with_different_num_annnots = %r' %
    #       (len(np.nonzero(nAnnots_difference)[0]),))


"""
def MERGE_NNP_MASTER_SCRIPT():
    print(ut.truncate_str(ibs_dst.db.get_table_csv(ibeis.const.ANNOTATION_TABLE,
        exclude_columns=['annot_verts', 'annot_semantic_uuid', 'annot_note', 'annot_parent_rowid']), 10000))
    print(ut.truncate_str(ibs_src1.db.get_table_csv(ibeis.const.ANNOTATION_TABLE,
        exclude_columns=['annot_verts', 'annot_semantic_uuid', 'annot_note', 'annot_parent_rowid']), 10000))
    print(ut.truncate_str(ibs_src1.db.get_table_csv(ibeis.const.ANNOTATION_TABLE), 10000))

    from ibeis.dbio.export_subset import *  # NOQA
    import ibeis
    # Step 1
    ibs_src1 = ibeis.opendb('GZC')
    ibs_dst = ibeis.opendb('NNP_Master3', allow_newdir=True)
    merge_databases(ibs_src1, ibs_dst)

    ibs_src2 = ibeis.opendb('NNP_initial')
    merge_databases(ibs_src2, ibs_dst)

    ## Step 2
    #ibs_src = ibeis.opendb('GZC')

    ## Check
    ibs1 = ibeis.opendb('NNP_initial')
    ibs2 = ibeis.opendb('GZC')
    ibs3 = ibs_dst

    #print(ibs1.get_image_time_statstr())
    #print(ibs2.get_image_time_statstr())
    #print(ibs3.get_image_time_statstr())
"""


if __name__ == '__main__':
    """
    python -m ibeis.dbio.export_subset
    python -m ibeis.dbio.export_subset --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()
    ut.doctest_funcs()
