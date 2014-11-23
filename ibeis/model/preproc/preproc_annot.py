"""
The goal of this module is to offload annotation work from the controller into a
single place.
"""
from __future__ import absolute_import, division, print_function
from six.moves import zip, range, filter  # NOQA
import utool as ut  # NOQA
import uuid
from vtool import geometry
from ibeis import constants
(print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[preproc_annot]', DEBUG=False)


def generate_annot_properties(ibs, gid_list, bbox_list=None, theta_list=None,
                              species_list=None, nid_list=None, name_list=None,
                              detect_confidence_list=None, notes_list=None,
                              vert_list=None, annot_uuid_list=None,
                              viewpoint_list=None, quiet_delete_thumbs=False):
    #annot_uuid_list = ibsfuncs.make_annotation_uuids(image_uuid_list, bbox_list,
    #                                                      theta_list, deterministic=False)
    image_uuid_list = ibs.get_image_uuids(gid_list)
    if annot_uuid_list is None:
        annot_uuid_list = [uuid.uuid4() for _ in range(len(image_uuid_list))]
    # Prepare the SQL input
    assert name_list is None or nid_list is None, 'cannot specify both names and nids'
    # For import only, we can specify both by setting import_override to True
    assert bool(bbox_list is None) != bool(vert_list is None), 'must specify exactly one of bbox_list or vert_list'

    if theta_list is None:
        theta_list = [0.0 for _ in range(len(gid_list))]
    if name_list is not None:
        nid_list = ibs.add_names(name_list)
    if detect_confidence_list is None:
        detect_confidence_list = [0.0 for _ in range(len(gid_list))]
    if notes_list is None:
        notes_list = ['' for _ in range(len(gid_list))]
    if vert_list is None:
        vert_list = geometry.verts_list_from_bboxes_list(bbox_list)
    elif bbox_list is None:
        bbox_list = geometry.bboxes_from_vert_list(vert_list)

    len_bbox    = len(bbox_list)
    len_vert    = len(vert_list)
    len_gid     = len(gid_list)
    len_notes   = len(notes_list)
    len_theta   = len(theta_list)
    try:
        assert len_vert == len_bbox, 'bbox and verts are not of same size'
        assert len_gid  == len_bbox, 'bbox and gid are not of same size'
        assert len_gid  == len_theta, 'bbox and gid are not of same size'
        assert len_notes == len_gid, 'notes and gids are not of same size'
    except AssertionError as ex:
        ut.printex(ex, key_list=['len_vert', 'len_gid', 'len_bbox'
                                    'len_theta', 'len_notes'])
        raise

    if len(gid_list) == 0:
        # nothing is being added
        print('[ibs] WARNING: 0 annotations are beign added!')
        print(ut.dict_str(locals()))
        return []

    # Build ~~deterministic?~~ random and unique ANNOTATION ids
    image_uuid_list = ibs.get_image_uuids(gid_list)
    #annot_uuid_list = ibsfuncs.make_annotation_uuids(image_uuid_list, bbox_list,
    #                                                      theta_list, deterministic=False)
    if annot_uuid_list is None:
        annot_uuid_list = [uuid.uuid4() for _ in range(len(image_uuid_list))]
    if viewpoint_list is None:
        viewpoint_list = [-1.0] * len(image_uuid_list)
    nVert_list = [len(verts) for verts in vert_list]
    vertstr_list = [constants.__STR__(verts) for verts in vert_list]
    xtl_list, ytl_list, width_list, height_list = list(zip(*bbox_list))
    assert len(nVert_list) == len(vertstr_list)
    # Define arguments to insert


def get_annot_appearance_determenistic_info(ibs, aid_list):
    """
    Returns annotation UUID that is unique for the visual qualities
    of the annoation. does not include name ore species information.

    Example:
        >>> from ibeis.model.preproc.preproc_annot import *   # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid_list = ibs.get_valid_aids()
    """
    image_uuid_list = ibs.get_annot_image_uuids(aid_list)
    bbox_list       = ibs.get_annot_bboxes(aid_list)
    theta_list      = ibs.get_annot_thetas(aid_list)
    view_list       = ibs.get_annot_viewpoints(aid_list)
    info_iter = zip(image_uuid_list, bbox_list, theta_list, view_list)
    annot_appearance_determenistic_info_list = list(info_iter)
    return annot_appearance_determenistic_info_list


def get_annot_determenistic_info(ibs, aid_list):
    """
    Example:
        >>> from ibeis.model.preproc.preproc_annot import *   # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid_list = ibs.get_valid_aids()
    """
    image_uuid_list = ibs.get_annot_image_uuids(aid_list)
    bbox_list       = ibs.get_annot_bboxes(aid_list)
    theta_list      = ibs.get_annot_thetas(aid_list)
    name_list       = ibs.get_annot_names(aid_list)
    species_list    = ibs.get_annot_species(aid_list)
    view_list       = ibs.get_annot_viewpoints(aid_list)
    info_iter = zip(image_uuid_list, bbox_list, theta_list, name_list, species_list, view_list)
    annot_determenistic_info_list = list(info_iter)
    return annot_determenistic_info_list


def determenistic_annotation_uuids(ibs, aid_list):
    """
    Example:
        >>> from ibeis.model.preproc.preproc_annot import *   # NOQA
        >>> import ibeis
        >>> ibs = ibeis.opendb('testdb1')
        >>> aid_list = ibs.get_valid_aids()
    """
    annot_determenistic_info_list = get_annot_determenistic_info(ibs, aid_list)
    annot_uuid_list = [ut.augment_uuid(*tup) for tup in annot_determenistic_info_list]
    return annot_uuid_list


def make_annotation_uuids(image_uuid_list, bbox_list, theta_list, deterministic=True):
    try:
        # Check to make sure bbox input is a tuple-list, not a list-list
        if len(bbox_list) > 0:
            try:
                assert isinstance(bbox_list[0], tuple), 'Bounding boxes must be tuples of ints!'
                assert isinstance(bbox_list[0][0], int), 'Bounding boxes must be tuples of ints!'
            except AssertionError as ex:
                ut.printex(ex)
                print('bbox_list = %r' % (bbox_list,))
                raise
        annotation_uuid_list = [ut.augment_uuid(img_uuid, bbox, theta)
                                for img_uuid, bbox, theta
                                in zip(image_uuid_list, bbox_list, theta_list)]
        if not deterministic:
            # Augment determenistic uuid with a random uuid to ensure randomness
            # (this should be ensured in all hardward situations)
            annotation_uuid_list = [ut.augment_uuid(ut.random_uuid(), _uuid)
                                    for _uuid in annotation_uuid_list]
    except Exception as ex:
        ut.printex(ex, 'Error building annotation_uuids', '[add_annot]',
                      key_list=['image_uuid_list'])
        raise
    return annotation_uuid_list


def test_annotation_uuid(ibs):
    """ Consistency test """
    aid_list        = ibs.get_valid_aids()
    bbox_list       = ibs.get_annot_bboxes(aid_list)
    theta_list      = ibs.get_annot_thetas(aid_list)
    image_uuid_list = ibs.get_annot_image_uuids(aid_list)

    annotation_uuid_list1 = ibs.get_annot_uuids(aid_list)
    annotation_uuid_list2 = make_annotation_uuids(image_uuid_list, bbox_list, theta_list)

    assert annotation_uuid_list1 == annotation_uuid_list2
