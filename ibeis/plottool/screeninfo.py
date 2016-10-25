from __future__ import absolute_import, division, print_function
import six
from six.moves import range
import sys
import utool as ut
import numpy as np
try:
    import guitool
    from guitool.__PYQT__ import QtWidgets
except ImportError:
    try:
        from PyQt4 import QtGui as QtWidgets
    except ImportError:
        pass
    try:
        from PyQt5 import QtWidgets  # NOQA
    except ImportError:
        pass
    print('Warning: guitool did not import correctly')
#(print, print_, printDBG, rrr, profile) = ut.inject(__name__, '[screeninfo]', DEBUG=True)
ut.noinject(__name__, '[screeninfo]')


DEFAULT_MAX_ROWS = 3


# Win7 Areo
WIN7_SIZES = {
    'os_border_x':   20,
    'os_border_y':   35,
    'os_border_h':   30,
    'win_border_x':  17,
    'win_border_y':  10,
    'mpl_toolbar_y': 10,
}

# Ubuntu (Medeterrainian Dark)
GNOME3_SIZES = {
    'os_border_x':    0,
    'os_border_y':   35,  # for gnome3 title bar
    'os_border_h':    0,
    'win_border_x':   5,
    'win_border_y':  30,
    'mpl_toolbar_y':  0,
}

for key in GNOME3_SIZES:
    GNOME3_SIZES[key] += 5


def ensure_app_is_running():
    #print('[screeninfo] Ensuring that qtapp is running')
    app, is_root = guitool.init_qtapp()


def infer_monitor_specs(res_w, res_h, inches_diag):
    """
    monitors = [
        dict(name='work1', inches_diag=23, res_w=1920, res_h=1080),
        dict(name='work2', inches_diag=24, res_w=1920, res_h=1200),

        dict(name='hp-129', inches_diag=25, res_w=1920, res_h=1080),
        dict(name='?-26', inches_diag=26, res_w=1920, res_h=1080),
        dict(name='?-27', inches_diag=27, res_w=1920, res_h=1080),
    ]
    for info in monitors:
        name = info['name']
        inches_diag = info['inches_diag']
        res_h = info['res_h']
        res_w = info['res_w']
        print('---')
        print(name)
        inches_w = inches_diag * res_w / np.sqrt(res_h**2 + res_w**2)
        inches_h = inches_diag * res_h / np.sqrt(res_h**2 + res_w**2)
        print('inches diag = %.2f' % (inches_diag))
        print('inches WxH = %.2f x %.2f' % (inches_w, inches_h))

    #inches_w = inches_diag * res_w/sqrt(res_h**2 + res_w**2)
    """
    import sympy
    # Build a system of equations and solve it
    inches_w, inches_h = sympy.symbols('inches_w inches_h'.split(), real=True, positive=True)
    res_w, res_h = sympy.symbols('res_w res_h'.split(), real=True, positive=True)
    inches_diag, = sympy.symbols('inches_diag'.split(), real=True, positive=True)
    equations = [
        sympy.Eq(inches_diag, (inches_w ** 2 + inches_h ** 2) ** .5),
        sympy.Eq(res_w / res_h, inches_w / inches_h),
    ]
    print('Possible solutions:')
    query_vars = [inches_w, inches_h]
    for solution in sympy.solve(equations, query_vars):
        print('Solution:')
        reprstr = ut.repr3(ut.odict(zip(query_vars, solution)), explicit=True, nobr=1, with_comma=False)
        print(ut.indent(ut.autopep8_format(reprstr)))
    #(inches_diag*res_w/sqrt(res_h**2 + res_w**2), inches_diag*res_h/sqrt(res_h**2 + res_w**2))


def get_resolution_info(monitor_num=0):
    r"""
    Args:
        monitor_num (int): (default = 0)

    Returns:
        dict: info

    CommandLine:
        python -m plottool.screeninfo get_resolution_info --show
        xrandr | grep ' connected'
        grep "NVIDIA" /var/log/Xorg.0.log

    Example:
        >>> # DISABLE_DOCTEST
        >>> from plottool.screeninfo import *  # NOQA
        >>> monitor_num = 0
        >>> for monitor_num in range(get_number_of_monitors()):
        >>>     info = get_resolution_info(monitor_num)
        >>>     print('monitor(%d).info = %s' % (monitor_num, ut.repr3(info, precision=3)))
    """
    ensure_app_is_running()
    desktop = QtWidgets.QDesktopWidget()
    screen = desktop.screen(monitor_num)
    ppi_x = screen.logicalDpiX()
    ppi_y = screen.logicalDpiY()
    dpi_x = screen.physicalDpiX()
    dpi_y = screen.physicalDpiY()
    rect = desktop.availableGeometry(screen=monitor_num)
    pixels_w = rect.width()
    pixels_h = rect.height()

    inches_w = (pixels_w / dpi_x)
    inches_h = (pixels_h / dpi_y)
    inches_diag = (inches_w ** 2 + inches_h ** 2) ** .5

    mm_w = inches_w * ut.MM_PER_INCH
    mm_h = inches_h * ut.MM_PER_INCH
    mm_diag = inches_diag * ut.MM_PER_INCH

    ratio = min(mm_w, mm_h) / max(mm_w, mm_h)

    #pixel_density = dpi_x / ppi_x
    info = ut.odict([
        ('monitor_num', monitor_num),
        ('ratio', ratio),
        ('ppi_x', ppi_x),
        ('ppi_y', ppi_y),
        ('dpi_x', dpi_x),
        ('dpi_y', dpi_y),
        #'pixel_density', pixel_density),
        ('inches_w', inches_w),
        ('inches_h', inches_h),
        ('inches_diag', inches_diag),
        ('mm_w', mm_w),
        ('mm_h', mm_h),
        ('mm_diag', mm_diag),
        ('pixels_w', pixels_w),
        ('pixels_h', pixels_h),
    ])
    return info


def get_number_of_monitors():
    ensure_app_is_running()
    desktop = QtWidgets.QDesktopWidget()
    return desktop.numScreens()


def get_monitor_geom(monitor_num=0):
    r"""
    Args:
        monitor_num (int): (default = 0)

    Returns:
        tuple: geom

    CommandLine:
        python -m plottool.screeninfo get_monitor_geom --show

    Example:
        >>> # DISABLE_DOCTEST
        >>> from plottool.screeninfo import *  # NOQA
        >>> monitor_num = 0
        >>> geom = get_monitor_geom(monitor_num)
        >>> result = ('geom = %s' % (ut.repr2(geom),))
        >>> print(result)
    """
    ensure_app_is_running()
    desktop = QtWidgets.QDesktopWidget()
    rect = desktop.availableGeometry(screen=monitor_num)
    geom = (rect.x(), rect.y(), rect.width(), rect.height())
    return geom


def get_monitor_geometries():
    ensure_app_is_running()
    monitor_geometries = {}
    desktop = QtWidgets.QDesktopWidget()
    for screenx in range(desktop.numScreens()):
        rect = desktop.availableGeometry(screen=screenx)
        geom = (rect.x(), rect.y(), rect.width(), rect.height())
        monitor_geometries[screenx] = geom
    return monitor_geometries


def get_stdpxls():
    if sys.platform.startswith('win32'):
        stdpxls = WIN7_SIZES
    elif sys.platform.startswith('linux'):
        stdpxls = GNOME3_SIZES
    else:
        stdpxls = GNOME3_SIZES
    return stdpxls


def get_xywh_pads():
    stdpxls = get_stdpxls()
    w_pad =  stdpxls['win_border_x']
    y_pad =  stdpxls['win_border_y'] + stdpxls['mpl_toolbar_y']
    # Pads are applied to all windows
    x_pad =  stdpxls['os_border_x']
    y_pad =  stdpxls['os_border_y']
    return (x_pad, y_pad, w_pad, y_pad)


def get_avail_geom(monitor_num=None, percent_w=1.0, percent_h=1.0):
    stdpxls = get_stdpxls()
    if monitor_num is None:
        monitor_num = 0
    monitor_geometries = get_monitor_geometries()
    try:
        (startx, starty, availw, availh) = monitor_geometries[monitor_num]
    except KeyError:
        (startx, starty, availw, availh) = six.itervalues(monitor_geometries).next()
    available_geom = (startx,
                      starty,
                      availw * percent_w,
                      (availh - stdpxls['os_border_h']) * percent_h)
    return available_geom


def get_valid_fig_positions(num_wins, max_rows=None, row_first=True,
                            monitor_num=None, percent_w=1.0,
                            percent_h=1.0):
    """
    Returns a list of bounding boxes where figures can be placed on the screen
    """
    if percent_h is None:
        percent_h = 1.0
    if percent_w is None:
        percent_w = 1.0
    if max_rows is None:
        max_rows = DEFAULT_MAX_ROWS

    available_geom = get_avail_geom(monitor_num, percent_w=percent_w, percent_h=percent_h)
    # print('available_geom = %r' % (available_geom,))
    startx, starty, avail_width, avail_height = available_geom

    nRows = num_wins if num_wins < max_rows else max_rows
    nCols = int(np.ceil(num_wins / nRows))

    win_height = avail_height / nRows
    win_width  = avail_width  / nCols

    (x_pad, y_pad, w_pad, h_pad) = get_xywh_pads()

    # print('startx, startx = %r, %r' % (startx, starty))
    # print('avail_width, avail_height = %r, %r' % (avail_width, avail_height))
    # print('win_width, win_height = %r, %r' % (win_width, win_height))
    # print('nRows, nCols = %r, %r' % (nRows, nCols))

    def get_position_ix(ix):
        if row_first:
            rowx = ix % nRows
            colx = int(ix // nRows)
        else:
            colx = (ix % nCols)
            rowx = int(ix // nCols)
        w = win_width  - w_pad
        h = win_height - h_pad
        x = startx + colx * (win_width)  + x_pad
        y = starty + rowx * (win_height) + y_pad
        return (x, y, w, h)
    valid_positions = [get_position_ix(ix) for ix in range(num_wins)]
    return valid_positions


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m plottool.screeninfo
        python -m plottool.screeninfo --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
