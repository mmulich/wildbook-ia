#!/usr/bin/env python
# TODO: ADD COPYRIGHT TAG
from __future__ import absolute_import, division, print_function
import sys
from os.path import join, dirname, realpath
sys.path.append(realpath(join(dirname(__file__), '../..')))
from ibeis.tests import __testing__
import multiprocessing
import utool
# IBEIST
from ibeis.model.preproc import preproc_detectimg
print, print_, printDBG, rrr, profile = utool.inject(__name__, '[TEST_COMPUTE_DETECTIMG]')


def TEST_COMPUTE_DETECTIMG(ibs):
    # Create a HotSpotter API (hs) and GUI backend (back)
    print('get_valid_ROIS')
    rid_list = ibs.get_valid_rids()
    assert len(rid_list) > 0, 'database rois cannot be empty for TEST_COMPUTE_DETECTIMG'
    print(' * len(rid_list) = %r' % len(rid_list))
    preproc_detectimg.compute_and_write_detectimg(ibs, rid_list)
    return locals()


if __name__ == '__main__':
    multiprocessing.freeze_support()  # For windows
    main_locals = __testing__.main(defaultdb='testdb0')
    ibs = main_locals['ibs']    # IBEIS Control
    test_locals = __testing__.run_test(TEST_COMPUTE_DETECTIMG, ibs)
    execstr     = __testing__.main_loop(test_locals)
    exec(execstr)
