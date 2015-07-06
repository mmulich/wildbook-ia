"""
CommandLine:
    rm -rf /media/raid/work/PZ_MTEST/_ibsdb/_ibeis_cache/match_thumbs/
    python -m ibeis.gui.inspect_gui --test-test_inspect_matches --show --verbose-thumb
"""
from __future__ import absolute_import, division, print_function
from guitool.__PYQT__ import QtGui, QtCore
#import cv2  # NOQA
#import numpy as np
import utool
#import time
#from six.moves import zip
from os.path import exists
from vtool import image as gtool
#from vtool import linalg, geometry
from vtool import geometry
#from multiprocessing import Process
#from guitool import guitool_components as comp
#(print, print_, printDBG, rrr, profile) = utool.inject(__name__, '[APIThumbDelegate]', DEBUG=False)
import utool as ut
ut.noinject(__name__, '[APIThumbDelegate]', DEBUG=False)


VERBOSE_QT = ut.get_argflag(('--verbose-qt', '--verbqt'))
VERBOSE_THUMB = utool.VERBOSE or ut.get_argflag(('--verbose-thumb', '--verbthumb')) or VERBOSE_QT


MAX_NUM_THUMB_THREADS = 1


def read_thumb_size(thumb_path):
    if VERBOSE_THUMB:
        print('[ThumbDelegate] Reading thumb size')
    npimg = gtool.imread(thumb_path, delete_if_corrupted=True)
    (height, width) = npimg.shape[0:2]
    del npimg
    return width, height


def test_show_qimg(qimg):
    qpixmap = QtGui.QPixmap(qimg)
    lbl = QtGui.QLabel()
    lbl.setPixmap(qpixmap)
    lbl.show()   # show label with qim image
    return lbl


#@ut.memprof
def read_thumb_as_qimg(thumb_path):
    r"""
    Args:
        thumb_path (?):

    Returns:
        tuple: (qimg, width, height)

    CommandLine:
        python -m guitool.api_thumb_delegate --test-read_thumb_as_qimg --show

    Example:
        >>> # ENABLE_DOCTEST
        >>> from guitool.api_thumb_delegate import *  # NOQA
        >>> import guitool
        >>> # build test data
        >>> thumb_path = ut.grab_test_imgpath('carl.jpg')
        >>> # execute function
        >>> guitool.ensure_qtapp()
        >>> (qimg) = ut.memprof(read_thumb_as_qimg)(thumb_path)
        >>> if ut.show_was_requested():
        >>>    lbl = test_show_qimg(qimg)
        >>>    guitool.qtapp_loop()
        >>> # verify results
        >>> print(qimg)

    Timeit::
        %timeit np.dstack((npimg, np.full(npimg.shape[0:2], 255, dtype=np.uint8)))
        %timeit cv2.cvtColor(npimg, cv2.COLOR_BGR2BGRA)
        npimg1 = np.dstack((npimg, np.full(npimg.shape[0:2], 255, dtype=np.uint8)))
        # seems to be memory leak in cvtColor?
        npimg2 = cv2.cvtColor(npimg, cv2.COLOR_BGR2BGRA)

    """
    if VERBOSE_THUMB:
        print('[ThumbDelegate] Reading thumb as qimg. thumb_path=%r' % (thumb_path,))
    # Read thumbnail image and convert to 32bit aligned for Qt
    #if False:
    #    data  = np.dstack((npimg, np.full(npimg.shape[0:2], 255, dtype=np.uint8)))
    #if False:
    #    # Reading the npimage and then handing it off to Qt causes a memory
    #    # leak. The numpy array probably is never unallocated because qt doesn't
    #    # own it and it never loses its reference count
    #    #npimg = gtool.imread(thumb_path, delete_if_corrupted=True)
    #    #print('npimg.dtype = %r, %r' % (npimg.shape, npimg.dtype))
    #    #npimg   = cv2.cvtColor(npimg, cv2.COLOR_BGR2BGRA)
    #    #format_ = QtGui.QImage.Format_ARGB32
    #    ##    #data    = npimg.astype(np.uint8)
    #    ##    #npimg   = np.dstack((npimg[:, :, 3], npimg[:, :, 0:2]))
    #    ##    #data    = npimg.astype(np.uint8)
    #    ##else:
    #    ## Memory seems to be no freed by the QImage?
    #    ##data = np.ascontiguousarray(npimg[:, :, ::-1].astype(np.uint8), dtype=np.uint8)
    #    ##data = np.ascontiguousarray(npimg[:, :, :].astype(np.uint8), dtype=np.uint8)
    #    #data = npimg
    #    ##format_ = QtGui.QImage.Format_RGB888
    #    #(height, width) = data.shape[0:2]
    #    #qimg    = QtGui.QImage(data, width, height, format_)
    #    #del npimg
    #    #del data
    #else:
    #format_ = QtGui.QImage.Format_ARGB32
    #qimg    = QtGui.QImage(thumb_path, format_)
    qimg    = QtGui.QImage(thumb_path)
    return qimg


RUNNING_CREATION_THREADS = {}


def register_thread(key, val):
    global RUNNING_CREATION_THREADS
    RUNNING_CREATION_THREADS[key] = val


def unregister_thread(key):
    global RUNNING_CREATION_THREADS
    del RUNNING_CREATION_THREADS[key]


DELEGATE_BASE = QtGui.QItemDelegate


class APIThumbDelegate(DELEGATE_BASE):
    """
    There is one Thumb Delegate per column. Keep that in mind when writing for
    this class.

    TODO: The delegate can have a reference to the view, and it is allowed
    to resize the rows to fit the images.  It probably should not resize columns
    but it can get the column width and resize the image to that size.

    get_thumb_size is a callback function which should return whatever the
    requested thumbnail size is

    SeeAlso:
         api_item_view.infer_delegates
    """
    def __init__(dgt, parent=None, get_thumb_size=None):
        if VERBOSE_THUMB:
            print('[ThumbDelegate] __init__ parent=%r, get_thumb_size=%r' %
                    (parent, get_thumb_size))
        DELEGATE_BASE.__init__(dgt, parent)
        dgt.pool = None
        # TODO: get from the view
        if get_thumb_size is None:
            dgt.get_thumb_size = lambda: 128  # 256
        else:
            dgt.get_thumb_size = get_thumb_size  # 256
        dgt.last_thumbsize = None

    def get_model_data(dgt, qtindex):
        """
        The model data for a thumb should be a tuple:
        (thumb_path, img_path, imgsize, bboxes, thetas)
        """
        model = qtindex.model()
        datakw = dict(thumbsize=dgt.get_thumb_size())
        data = model.data(qtindex, QtCore.Qt.DisplayRole, **datakw)
        if data is None:
            return None
        # The data should be specified as a thumbtup
        #if isinstance(data, QtCore.QVariant):
        if hasattr(data, 'toPyObject'):
            data = data.toPyObject()
        if data is None:
            return None
        assert isinstance(data, tuple), (
            'data=%r is %r. should be a thumbtup' % (data, type(data)))
        thumbtup = data
        #(thumb_path, img_path, bbox_list) = thumbtup
        return thumbtup

    def spawn_thumb_creation_thread(dgt, thumb_path, img_path, img_size, qtindex, view, offset, bbox_list, theta_list):
        if VERBOSE_THUMB:
            print('[ThumbDelegate] Spawning thumbnail creation thread')
        thumbsize = dgt.get_thumb_size()
        thumb_creation_thread = ThumbnailCreationThread(
            thumb_path, img_path, img_size, thumbsize,
            qtindex, view, offset, bbox_list, theta_list
        )
        #register_thread(thumb_path, thumb_creation_thread)
        # Initialize threadcount
        if dgt.pool is None:
            #dgt.pool = QtCore.QThreadPool()
            #dgt.pool.setMaxThreadCount(MAX_NUM_THUMB_THREADS)
            dgt.pool = QtCore.QThreadPool.globalInstance()
        dgt.pool.start(thumb_creation_thread)
        # print('[ThumbDelegate] Waiting to compute')

    def get_thumb_path_if_exists(dgt, view, offset, qtindex):
        """
        Checks if the thumbnail is ready to paint

        Returns:
            thumb_path if computed otherwise returns None
        """

        # Check if still in viewport
        if view_would_not_be_visible(view, offset):
            return None

        # Get data from the models display role
        try:
            data = dgt.get_model_data(qtindex)
            if data is None:
                if VERBOSE_THUMB:
                    print('[thumb_delegate] no data')
                return
            (thumb_path, img_path, img_size, bbox_list, theta_list) = data
            invalid = (thumb_path is None or img_path is None or bbox_list is None
                       or img_size is None)
            if invalid:
                print('[thumb_delegate] something is wrong')
                return
        except AssertionError as ex:
            utool.printex(ex, 'error getting thumbnail data')
            return

        # Check if still in viewport
        if view_would_not_be_visible(view, offset):
            return None

        if not exists(thumb_path):
            if not exists(img_path):
                if VERBOSE_THUMB:
                    print('[ThumbDelegate] SOURCE IMAGE NOT COMPUTED: %r' % (img_path,))
                return None
            dgt.spawn_thumb_creation_thread(
                thumb_path, img_path, img_size, qtindex, view, offset,
                bbox_list, theta_list)
            return None
        else:
            # thumb is computed return the path
            return thumb_path

    def adjust_thumb_cell_size(dgt, qtindex, width, height):
        """
        called during paint to ensure that the cell is large enough for the
        image.
        """
        view = dgt.parent()
        if isinstance(view, QtGui.QTableView):
            # dimensions of the table cells
            col_width = view.columnWidth(qtindex.column())
            col_height = view.rowHeight(qtindex.row())
            thumbsize = dgt.get_thumb_size()
            if thumbsize != dgt.last_thumbsize:
                # has thumbsize changed?
                if thumbsize != col_width:
                    view.setColumnWidth(qtindex.column(), thumbsize)
                if height != col_height:
                    view.setRowHeight(qtindex.row(), height)
                dgt.last_thumbsize = thumbsize
            # Let columns shrink
            if thumbsize != col_width:
                view.setColumnWidth(qtindex.column(), thumbsize)
            # Let rows grow
            if height > col_height:
                view.setRowHeight(qtindex.row(), height)
            # Let rows shrink
            # IF THERE IS MORE THAN ONE COLUMN WITH THUMBS THEN THIS WILL CAUSE
            # COLS TO BE RESIZED MANY TIMES UNDER THE HOOD. THAT CAUSES
            # MULTIPLE READS OF THE THUMBS WHICH CAUSES MAJOR SLOWDOWNS.
            #if height < col_height:
            #    view.setRowHeight(qtindex.row(), height)
        elif isinstance(view, QtGui.QTreeView):
            col_width = view.columnWidth(qtindex.column())
            col_height = view.rowHeight(qtindex)
            # TODO: finishme

    def paint(dgt, painter, option, qtindex):
        """
        TODO: prevent recursive paint
        """
        view = dgt.parent()
        offset = view.verticalOffset() + option.rect.y()
        # Check if still in viewport
        if view_would_not_be_visible(view, offset):
            return None
        try:
            thumb_path = dgt.get_thumb_path_if_exists(view, offset, qtindex)
            if thumb_path is not None:
                # Check if still in viewport
                if view_would_not_be_visible(view, offset):
                    return None
                # Read the precomputed thumbnail
                qimg = read_thumb_as_qimg(thumb_path)
                width, height = qimg.width(), qimg.height()
                # Adjust the cell size to fit the image
                dgt.adjust_thumb_cell_size(qtindex, width, height)
                # Check if still in viewport
                if view_would_not_be_visible(view, offset):
                    return None
                # Paint image on an item in some view
                painter.save()
                painter.setClipRect(option.rect)
                painter.translate(option.rect.x(), option.rect.y())
                painter.drawImage(QtCore.QRectF(0, 0, width, height), qimg)
                painter.restore()
        except Exception as ex:
            # PSA: Always report errors on Exceptions!
            print('Error in APIThumbDelegate')
            utool.printex(ex, 'Error in APIThumbDelegate')
            painter.save()
            painter.restore()

    def sizeHint(dgt, option, qtindex):
        view = dgt.parent()
        offset = view.verticalOffset() + option.rect.y()
        try:
            thumb_path = dgt.get_thumb_path_if_exists(view, offset, qtindex)
            if thumb_path is not None:
                # Read the precomputed thumbnail
                width, height = read_thumb_size(thumb_path)
                return QtCore.QSize(width, height)
            else:
                #print("[APIThumbDelegate] Name not found")
                return QtCore.QSize()
        except Exception as ex:
            print("Error in APIThumbDelegate")
            utool.printex(ex, 'Error in APIThumbDelegate', tb=True)
            return QtCore.QSize()


def view_would_not_be_visible(view, offset):
    viewport = view.viewport()
    height = viewport.size().height()
    height_offset = view.verticalOffset()
    current_offset = height_offset + height // 2
    # Check if the current scroll position is far beyond the
    # scroll position when this was initially requested.
    return abs(current_offset - offset) >= height


def get_thread_thumb_info(bbox_list, theta_list, thumbsize, img_size):
    r"""
    Args:
        bbox_list (list):
        theta_list (list):
        thumbsize (?):
        img_size (?):

    CommandLine:
        python -m guitool.api_thumb_delegate --test-get_thread_thumb_info

    Example:
        >>> # ENABLE_DOCTEST
        >>> from guitool.api_thumb_delegate import *  # NOQA
        >>> # build test data
        >>> bbox_list = [(100, 50, 400, 200)]
        >>> theta_list = [0]
        >>> thumbsize = 128
        >>> img_size = 600, 300
        >>> # execute function
        >>> result = get_thread_thumb_info(bbox_list, theta_list, thumbsize, img_size)
        >>> # verify results
        >>> print(result)
        ((128, 64), [[[21, 11], [107, 11], [107, 53], [21, 53], [21, 11]]])

    """
    theta_list = [theta_list] if not utool.is_listlike(theta_list) else theta_list
    max_dsize = (thumbsize, thumbsize)
    dsize, sx, sy = gtool.resized_clamped_thumb_dims(img_size, max_dsize)
    # Compute new verts list
    new_verts_list = list(gtool.scaled_verts_from_bbox_gen(bbox_list, theta_list, sx, sy))
    return dsize, new_verts_list


def make_thread_thumb(img_path, dsize, new_verts_list):
    r"""
    Args:
        img_path (?):
        dsize (tuple):  width, height
        new_verts_list (list):

    Returns:
        ?: thumb

    CommandLine:
        python -m guitool.api_thumb_delegate --test-make_thread_thumb --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from guitool.api_thumb_delegate import *  # NOQA
        >>> import plottool as pt
        >>> # build test data
        >>> img_path = ut.grab_test_imgpath('carl.jpg')
        >>> dsize = (32, 32)
        >>> new_verts_list = []
        >>> # execute function
        >>> thumb = make_thread_thumb(img_path, dsize, new_verts_list)
        >>> ut.quit_if_noshow()
        >>> pt.imshow(thumb)
        >>> pt.show_if_requested()
    """
    orange_bgr = (0, 128, 255)
    # imread causes a MEMORY LEAK most likely!
    img = gtool.imread(img_path)  # Read Image (.0424s) <- Takes most time!
    #if False:
    #    #http://stackoverflow.com/questions/9794019/convert-numpy-array-to-pyside-qpixmap
    #    # http://kogs-www.informatik.uni-hamburg.de/~meine/software/vigraqt/qimage2ndarray.py
    #    #import numpy as np
    #    #qimg = QtGui.QImage(img_path, str(QtGui.QImage.Format_RGB32))
    #    #temp_shape = (qimg.height(), qimg.bytesPerLine() * 8 // qimg.depth(), 4)
    #    #result_shape = (qimg.height(), qimg.width())
    #    #buf = qimg.bits().asstring(qimg.numBytes())
    #    #result  = np.frombuffer(buf, np.uint8).reshape(temp_shape)
    #    #result = result[:, :result_shape[1]]
    #    #result = result[..., :3]
    #    #img = result
    thumb = gtool.resize(img, dsize)  # Resize to thumb dims (.0015s)
    del img
    # Draw bboxes on thumb (not image)
    for new_verts in new_verts_list:
        if new_verts is not None:
            geometry.draw_verts(thumb, new_verts, color=orange_bgr, thickness=2, out=thumb)
        #thumb = geometry.draw_verts(thumb, new_verts, color=orange_bgr, thickness=2)
    return thumb


RUNNABLE_BASE = QtCore.QRunnable


class ThumbnailCreationThread(RUNNABLE_BASE):
    """
    Helper to compute thumbnails concurrently

    References:
        TODO:
        http://stackoverflow.com/questions/6783194/background-thread-with-qthread-in-pyqt
    """

    def __init__(thread, thumb_path, img_path, img_size, thumbsize, qtindex, view, offset, bbox_list, theta_list):
        RUNNABLE_BASE.__init__(thread)
        thread.thumb_path = thumb_path
        thread.img_path = img_path
        thread.img_size = img_size
        thread.qtindex = qtindex
        thread.offset = offset
        thread.thumbsize = thumbsize
        thread.view = view
        thread.bbox_list = bbox_list
        thread.theta_list = theta_list

    def thumb_would_not_be_visible(thread):
        return view_would_not_be_visible(thread.view, thread.offset)

    def _run(thread):
        """ Compute thumbnail in a different thread """
        #time.sleep(.005)  # Wait a in case the user is just scrolling
        if thread.thumb_would_not_be_visible():
            return
        # Precompute info BEFORE reading the image (.0002s)
        dsize, new_verts_list = get_thread_thumb_info(
            thread.bbox_list, thread.theta_list, thread.thumbsize, thread.img_size)
        #time.sleep(.005)  # Wait a in case the user is just scrolling
        if thread.thumb_would_not_be_visible():
            return
        # -----------------
        # This part takes time, hopefully the user actually wants to see this
        # thumbnail.
        thumb = make_thread_thumb(thread.img_path, dsize, new_verts_list)
        if thread.thumb_would_not_be_visible():
            return
        gtool.imwrite(thread.thumb_path, thumb)
        del thumb
        if thread.thumb_would_not_be_visible():
            return
        #print('[ThumbCreationThread] Thumb Written: %s' % thread.thumb_path)
        thread.qtindex.model().dataChanged.emit(thread.qtindex, thread.qtindex)
        #unregister_thread(thread.thumb_path)

    def run(thread):
        try:
            thread._run()
        except Exception as ex:
            utool.printex(ex, 'thread failed', tb=True)
            #raise

    #def __del__(self):
    #    print('About to delete creation thread')


# GRAVE:
#print('[APIItemDelegate] Request Thumb: rc=(%d, %d), nBboxes=%r' %
#      (qtindex.row(), qtindex.column(), len(bbox_list)))
#print('[APIItemDelegate] bbox_list = %r' % (bbox_list,))

def simple_thumbnail_widget():
    r"""
    Very simple example to test thumbnails

    CommandLine:
        python -m guitool.api_thumb_delegate --test-simple_thumbnail_widget  --show
        python -m guitool.api_thumb_delegate --test-simple_thumbnail_widget  --show --tb

    Example:
        >>> # GUI_DOCTEST
        >>> from guitool.api_thumb_delegate import *  # NOQA
        >>> import guitool
        >>> guitool.ensure_qapp()  # must be ensured before any embeding
        >>> wgt = simple_thumbnail_widget()
        >>> ut.quit_if_noshow()
        >>> wgt.show()
        >>> guitool.qtapp_loop(wgt, frequency=100)
    """
    import guitool
    guitool.ensure_qapp()
    col_name_list = ['rowid', 'image_name', 'thumb']
    col_types_dict = {
        'thumb': 'PIXMAP',
    }

    guitool_test_thumbdir = ut.ensure_app_resource_dir('guitool', 'thumbs')
    ut.delete(guitool_test_thumbdir)
    ut.ensuredir(guitool_test_thumbdir)
    import vtool as vt
    from os.path import join

    def thumb_getter(id_, thumbsize=128):
        """ Thumb getters must conform to thumbtup structure """
        #print(id_)
        if id_ == 'doesnotexist.jpg':
            return None
            img_path = None
            img_size = (100, 100)
        else:
            img_path = ut.grab_test_imgpath(id_, verbose=False)
            img_size = vt.open_image_size(img_path)
        thumb_path = join(guitool_test_thumbdir, ut.hashstr(str(img_path)) + '.jpg')
        if id_ == 'carl.jpg':
            bbox_list = [(10, 10, 200, 200)]
            theta_list = [0]
        elif id_ == 'lena.png':
            #bbox_list = [(10, 10, 200, 200)]
            bbox_list = [None]
            theta_list = [None]
        else:
            bbox_list = []
            theta_list = []
        thumbtup = (thumb_path, img_path, img_size, bbox_list, theta_list)
        #print('thumbtup = %r' % (thumbtup,))
        return thumbtup
        #return None

    #imgname_list = sorted(ut.TESTIMG_URL_DICT.keys())
    imgname_list = ['carl.jpg', 'lena.png', 'patsy.jpg']

    imgname_list += ['doesnotexist.jpg']

    col_getter_dict = {
        'rowid': list(range(len(imgname_list))),
        'image_name': imgname_list,
        'thumb': thumb_getter
    }
    col_ider_dict = {
        'thumb': 'image_name',
    }
    col_setter_dict = {}
    editable_colnames = []
    sortby = 'rowid'
    get_thumb_size = lambda: 128
    col_width_dict = {}
    col_bgrole_dict = {}

    api = guitool.CustomAPI(
        col_name_list, col_types_dict, col_getter_dict,
        col_bgrole_dict, col_ider_dict, col_setter_dict,
        editable_colnames, sortby, get_thumb_size, True, col_width_dict)
    headers = api.make_headers(tblnice='Utool Test Images')

    wgt = guitool.APIItemWidget()
    wgt.change_headers(headers)
    wgt.resize(600, 400)
    #guitool.qtapp_loop(qwin=wgt, ipy=ipy, frequency=loop_freq)
    return wgt


if __name__ == '__main__':
    """
    CommandLine:
        python -m guitool.api_thumb_delegate
        python -m guitool.api_thumb_delegate --allexamples
        python -m guitool.api_thumb_delegate --allexamples --noface --nosrc
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
