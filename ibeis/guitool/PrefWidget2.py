# -*- coding: utf-8 -*-
"""

python -m guitool.guitool_components ConfigConfirmWidget --show
python -m guitool.PrefWidget2 newConfigWidget --show --verbconf

"""
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import six  # NOQA
import traceback
from guitool.__PYQT__ import QtCore, QtGui  # NOQA
from guitool.__PYQT__ import QVariantHack
from guitool.__PYQT__.QtCore import Qt, QAbstractItemModel, QModelIndex, QObject
from guitool.__PYQT__.QtGui import QWidget
from guitool.__PYQT__ import _fromUtf8, _encoding, _translate  # NOQA
import utool as ut
ut.noinject(__name__, '[PrefWidget2]', DEBUG=False)

VERBOSE_CONFIG = ut.VERBOSE or ut.get_argflag('--verbconf')


def report_thread_error(fn):
    """
    Decorator to help catch errors that QT wont report
    """
    def report_thread_error_wrapper(*args, **kwargs):
        try:
            ret = fn(*args, **kwargs)
            return ret
        except Exception as ex:
            print('\n\n *!!* Thread Raised Exception: ' + str(ex))
            print('\n\n *!!* Thread Exception Traceback: \n\n' + traceback.format_exc())
            sys.stdout.flush()
            et, ei, tb = sys.exc_info()
            raise
    return report_thread_error_wrapper


def qindexstr(index):
    return 'QIndex(%r, %r)' % (index.row(), index.column())


"""
Notes:
    Combo Junmk
    # fill style options with item data
    #style = QtCore.QCoreApplication.instance().style()
    #opt.rect.setWidth(400)
    #print('opt.rect = %r' % (opt.rect,))
    #style.State style.StateFlag style.State_NoChange style.State_Sibling
    #style.State_Active style.State_FocusAtBorder style.State_None
    #style.State_Small style.State_AutoRaise style.State_HasFocus
    #style.State_Off style.State_Sunken style.State_Bottom
    #style.State_Horizontal style.State_On style.State_Top
    #style.State_Children style.State_Item style.State_Open
    #style.State_UpArrow style.State_DownArrow
    #style.State_KeyboardFocusChange style.State_Raised style.State_Window
    #style.State_Editing style.State_Mini style.State_ReadOnly
    #style.State_Enabled style.State_MouseOver style.State_Selected

    #opt.state |= style.State_Raised
    #opt.state |= style.State_UpArrow
    #opt.state |= style.State_AutoRaise
    #opt.state |= style.State_Active
    #opt.state |= style.State_Editing
    #opt.state |= style.State_Enabled
    #opt.state |= style.State_On
    #opt.state |= style.State_Open
    #opt.state |= style.State_HasFocus
    #opt.state |= style.State_FocusAtBorder
    #opt.state |= style.State_Selected

    #painter.drawText(option.rect, Qt.AlignLeft, "FOOBAR")
    #print('opt.state = %r' % (opt.state,))

    #else:
        #opt.state = style.State_Enabled | style.State_Active

    #self.initStyleOption(opt)

    #'currentIcon': <PyQt4.QtGui.QIcon object at 0x7fb19681b8a0>,
    #'currentText': '',
    #'direction': 0,
    #'editable': False,
    #'frame': True,
    #'iconSize': PyQt4.QtCore.QSize(-1, -1),
    #'palette': <PyQt4.QtGui.QPalette object at 0x7fb1959666e0>,
    #'popupRect': PyQt4.QtCore.QRect(),
    #'rect': PyQt4.QtCore.QRect(),
    #'state': <PyQt4.QtGui.State object at 0x7fb195966848>,
    #'activeSubControls': <PyQt4.QtGui.SubControls object at 0x7fb195966578>,
    #'subControls': <PyQt4.QtGui.SubControls object at 0x7fb1959668c0>,

    #opt.subControls = QtGui.QStyle.SC_All
    #print('QtGui.QStyle.SC_All = %r' % (QtGui.QStyle.SC_All,))
    #print('opt.subControls = %r' % (opt.subControls,))

    # draw item data as ComboBox
    #element = QtGui.QStyle.CE_ItemViewItem
    #QtGui.QStyle.SC_ComboBoxArrow
    #QtGui.QStyle.SC_ComboBoxEditField
    #QtGui.QStyle.SC_ComboBoxFrame
    #QtGui.QStyle.SC_ComboBoxListBoxPopup

    #style.drawPrimitive(QtGui.QStyle.PE_PanelButtonBevel, opt, painter)
    # Do I need to draw sub controls?

    #painter.save()
    #painter.restore()

    #self.drawDisplay(painter, opt, opt.rect, opt.currentText)
    #self.drawFocus(painter, opt, opt.rect)
    #QtGui.QItemDelegate
    #painter.restore()
    #return super(ConfigValueDelegate, self).paint(painter, option, index)
"""

#DELEGATE_BASE = QtGui.QStyledItemDelegate
#DELEGATE_BASE = QtGui.QAbstractItemDelegate
DELEGATE_BASE = QtGui.QItemDelegate


class ConfigValueDelegate(DELEGATE_BASE):
    """
    A delegate that decides what the editor should be for each row in a
    specific column

    CommandLine:
        python -m guitool.PrefWidget2 newConfigWidget --show
        python -m guitool.PrefWidget2 newConfigWidget --show --verbconf

    References:
        http://stackoverflow.com/questions/28037126/how-to-use-qcombobox-as-delegate-with-qtableview
        http://www.qtcentre.org/threads/41409-PyQt-QTableView-with-comboBox
        http://stackoverflow.com/questions/28680150/qtableview-data-in-background--cell-is-edited
        https://forum.qt.io/topic/46628/qtreeview-with-qitemdelegate-and-qcombobox-inside-not-work-propertly/5
        http://stackoverflow.com/questions/33990029/what-are-the-mechanics-of-the-default-delegate-for-item-views-in-qt
        #http://www.qtcentre.org/archive/index.php/t-64165.html
        #http://doc.qt.io/qt-4.8/style-reference.html

    """
    def __init__(self, parent):
        super(ConfigValueDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        # Get Item Data
        # value = index.data(QtCore.Qt.DisplayRole).toInt()[0]
        leafNode = index.internalPointer()
        if (VERBOSE_CONFIG and False):
            print('[DELEGATE] * painting editor for %s at %s' % (leafNode, qindexstr(index)))
            leafNode.print_tree()
            # print('[DELEGATE] * painting editor for %s at %s' % (leafNode, qindexstr(index)))
        if leafNode.is_combo:
            #print('[DELEGATE] * painting editor for %s at %s' % (leafNode, qindexstr(index)))
            #painter.save()
            curent_value = six.text_type(index.model().data(index))
            style = QtGui.QApplication.style()
            opt = QtGui.QStyleOptionComboBox()
            opt.currentText = curent_value
            opt.rect = option.rect
            opt.editable = False

            if leafNode.qt_is_editable():
                opt.state |= style.State_On
                opt.state |= style.State_Enabled
                opt.state = style.State_Enabled | style.State_Active

            element = QtGui.QStyle.CE_ComboBoxLabel
            control = QtGui.QStyle.CC_ComboBox

            style.drawComplexControl(control, opt, painter)
            style.drawControl(element, opt, painter)
        elif False and (leafNode is not None and leafNode.type_ is int):
            curent_value = six.text_type(index.model().data(index))
            # fill style options with item data
            style = QtGui.QApplication.style()
            opt = QtGui.QStyleOptionSpinBox()
            # opt.currentText doesn't exist for SpinBox
            opt.currentText = curent_value  #
            opt.rect = option.rect
            #opt.editable = False
            if leafNode.qt_is_editable():
                opt.state |= style.State_Enabled
            element = QtGui.QStyle.CE_ItemViewItem
            control = QtGui.QStyle.CC_SpinBox
            style.drawComplexControl(control, opt, painter)
            style.drawControl(element, opt, painter)
        else:
            return super(ConfigValueDelegate, self).paint(painter, option, index)

    #def sizeHint(self, option, index):
    #    size_hint = super(ConfigValueDelegate, self).sizeHint(option, index)
    #    print('size_hint = %r' % (size_hint,))
    #    #size_hint = QtCore.QSize(50, 21)
    #    size_hint = QtCore.QSize(40, 30)
    #    print('size_hint = %r' % (size_hint,))
    #    return size_hint

    def createEditor(self, parent, option, index):
        """
        Creates different editors for different types of data
        """
        leafNode = index.internalPointer()
        if VERBOSE_CONFIG:
            print('\n\n')
            print('[DELEGATE] newEditor for %s at %s' % (leafNode, qindexstr(index)))
        if leafNode is not None and leafNode.is_combo:
            import guitool
            options = leafNode.valid_values
            curent_value = index.model().data(index)
            if VERBOSE_CONFIG:
                print('[DELEGATE] * current_value = %r' % (curent_value,))
            editor = guitool.newComboBox(parent, options, default=curent_value)
            editor.currentIndexChanged['int'].connect(self.currentIndexChanged)
            editor.setAutoFillBackground(True)
            return editor
        elif leafNode is not None and leafNode.type_ is float:
            editor = QtGui.QDoubleSpinBox(parent)
            # TODO: min / max
            if False:
                editor.setMinimum(0.0)
                editor.setMaximum(1.0)
            editor.setSingleStep(0.1)
            editor.setAutoFillBackground(True)
            editor.setHidden(False)
            return editor
        elif leafNode is not None and leafNode.type_ is int:
            # TODO: Find a way for the user to enter a None into int boxes
            editor = QtGui.QSpinBox(parent)
            editor.setMinimum(-int(2 ** 29))
            editor.setMaximum(int(2 ** 29))
            if False:
                editor.setMinimum(0)
                editor.setMaximum(1)
            editor.setSingleStep(1)
            editor.setAutoFillBackground(True)
            editor.setHidden(False)
            return editor
        else:
            editor = super(ConfigValueDelegate, self).createEditor(parent, option, index)
            editor.setAutoFillBackground(True)
            return editor

            # return None

    def setEditorData(self, editor, index):
        leafNode = index.internalPointer()
        if VERBOSE_CONFIG:
            print('[DELEGATE] setEditorData for %s at %s' % (leafNode, qindexstr(index)))
        if leafNode is not None and leafNode.is_combo:
            editor.blockSignals(True)
            current_data = index.model().data(index)
            if VERBOSE_CONFIG:
                print('[DELEGATE] * current_data = %r' % (current_data,))
            editor.setCurrentValue(current_data)
            editor.blockSignals(False)
        else:
            return super(ConfigValueDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        leafNode = index.internalPointer()
        if VERBOSE_CONFIG:
            print('[DELEGATE] setModelData for %s at %s' % (leafNode, qindexstr(index)))
        if leafNode is not None and leafNode.is_combo:
            current_value = editor.currentValue()
            if VERBOSE_CONFIG:
                print('[DELEGATE] * current_value = %r' % (current_value,))
            model.setData(index, current_value)
        else:
            return super(ConfigValueDelegate, self).setModelData(editor, model, index)

    # @QtCore.pyqtSlot()
    def currentIndexChanged(self, combo_idx):
        if VERBOSE_CONFIG:
            print('[DELEGATE] Commit Data with combo_idx=%r' % (combo_idx,))
        self.commitData.emit(self.sender())

    def updateEditorGeometry(self, editor, option, index):
        if VERBOSE_CONFIG:
            print('[DELEGATE] updateEditorGeometry at %s' % (qindexstr(index)))
        editor.setGeometry(option.rect)
        #return super(ConfigValueDelegate, self).updateEditorGeometry(editor, option, index)

    #def editorChanged(self, index):
    #    check = self.editor.itemText(index)
    #    id_seq = self.parent.selectedIndexes[0][0]
    #    update.updateCheckSeq(self.parent.db, id_seq, check)


class QConfigModel(QAbstractItemModel):
    """
    Convention states only items with column index 0 can have children
    """
    @report_thread_error
    def __init__(self, parent=None, rootNode=None):
        super(QConfigModel, self).__init__(parent)
        self.rootNode  = rootNode

    @report_thread_error
    def index2Pref(self, index=QModelIndex()):
        """ Internal helper method """
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootNode

    #-----------
    # Overloaded ItemModel Read Functions
    @report_thread_error
    def rowCount(self, parent=QModelIndex()):
        parentPref = self.index2Pref(parent)
        return parentPref.qt_num_rows()

    @report_thread_error
    def columnCount(self, parent=QModelIndex()):
        parentPref = self.index2Pref(parent)
        return parentPref.qt_num_cols()

    @report_thread_error
    def data(self, qtindex, role=Qt.DisplayRole):
        """
        Returns the data stored under the given role
        for the item referred to by the qtindex.
        """
        if not qtindex.isValid():
            return QVariantHack()
        # Specify CheckState Role:
        flags = self.flags(qtindex)
        if role == Qt.CheckStateRole and flags & Qt.ItemIsUserCheckable:
            data = self.index2Pref(qtindex).qt_get_data(qtindex.column())
            return Qt.Checked if data else Qt.Unchecked
        #elif role == QtCore.Qt.SizeHintRole:
        #    #return QtCore.QSize(40, 30)
        #    return QVariantHack()
        if role != Qt.DisplayRole and role != Qt.EditRole:
            return QVariantHack()
        nodePref = self.index2Pref(qtindex)
        data = nodePref.qt_get_data(qtindex.column())
        if isinstance(data, float):
            var = QtCore.QLocale().toString(float(data), format='g', precision=6)
        else:
            var = data
        return str(var)

    @report_thread_error
    def setData(self, qtindex, value, role=Qt.EditRole):
        """
        Sets the role data for the item at qtindex to value.
        """
        if role == Qt.EditRole:
            data = value
        elif role == Qt.CheckStateRole:
            data = (value == Qt.Checked)
        else:
            return False
        if VERBOSE_CONFIG:
            print('[setData] --- setData() ---')
        leafPref = self.index2Pref(qtindex)
        old_data = leafPref.qt_get_data(qtindex.column())
        if VERBOSE_CONFIG:
            print('[setData] old_data = %r' % (old_data,))
            print('[setData] value = %r' % value)
            print('[setData] type(data) = %r' % type(data))
            print('[setData] type(value) = %r' % type(value))
        result = leafPref.qt_set_data(data)
        if VERBOSE_CONFIG:
            if result:
                print('[setData] Notified of acceptance')
            else:
                print('[setData] Notified of rejection')
        self.dataChanged.emit(qtindex, qtindex)
        if VERBOSE_CONFIG:
            print('[setData] --- FINISH setData() ---')
        return True

    @report_thread_error
    def index(self, row, col, parent=QModelIndex()):
        """
        Returns the index of the item in the model specified
        by the given row, column and parent index.
        """
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()
        parentPref = self.index2Pref(parent)
        childPref  = parentPref.qt_child(row)
        if childPref:
            return self.createIndex(row, col, childPref)
        else:
            return QModelIndex()

    @report_thread_error
    def parent(self, index=None):
        """
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.
        """
        if index is None:  # Overload with QObject.parent()
            return QObject.parent(self)
        if not index.isValid():
            return QModelIndex()
        nodePref = self.index2Pref(index)
        parentPref = nodePref.qt_parent()
        if parentPref == self.rootNode:
            return QModelIndex()
        return self.createIndex(parentPref.qt_parents_index_of_me(), 0, parentPref)

    @report_thread_error
    def flags(self, index):
        """
        Returns the item flags for the given index.
        """
        if index.column() == 0:
            # The First Column is just a label and unchangable
            flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif not index.isValid():
            flags = Qt.ItemFlag(0)
        else:
            childPref = self.index2Pref(index)
            if childPref and childPref.qt_is_editable():
                if childPref.is_checkable():
                    flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                else:
                    flags = Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                flags = Qt.ItemFlag(0)
        return flags

    @report_thread_error
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Fills in column headers in table / tree views
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == 0:
                return QVariantHack('Config Key')
            if section == 1:
                return QVariantHack('Config Value')
        return QVariantHack()


BOOL_AS_COMBO = False


class ConfigNodeWrapper(ut.NiceRepr):
    """
    Wraps a dtool.Config object for internal qt use
    """
    def __init__(self, name=None, config=None, parent=None, param_info=None):
        self.name = name
        self.config = config
        self.parent = parent
        self.children = None
        self.value = None
        self.param_info = param_info
        self._populate_children()

    def make_tree_strlist(self, indent='', verbose=False):
        """
        Creates tree structured printable represntation
        """
        if self.parent is None:
            typestr = 'Root'
        elif self.children is None:
            typestr = 'Leaf'
        else:
            typestr = 'Node'

        strlist = []
        if True:
            strlist += [
                indent + '┌── ',
                indent + '┃ %s(name=%r):' % (typestr, self.name,),
            ]
        if self.is_leaf():
            strlist += [
                indent + '┃     value = %r' % (self.value,),
                indent + '┃     original = %r' % (self.original,),
                indent + '┃     default = %r' % (self.param_info.default,),
            ]
        if verbose:
            strlist += [
                indent + '┃     type_ = %r' % (self.type_,),
                indent + '┃     is_combo = %r' % (self.is_combo,),
                indent + '┃     is_leaf = %r' % (self.is_leaf(),),
                indent + '┃     qt_num_rows = %r' % (self.qt_num_rows(),),
                indent + '┃     qt_is_editable = %r' % (self.qt_is_editable(),),
                indent + '┃     param_info = %r' % (self.param_info,),
            ]
        if True:
            strlist += [
                indent + '└──',
            ]
        for child in self.iter_children():
            childstr = child.make_tree_strlist(indent=indent + '|  ')
            strlist.extend(childstr)
        return strlist

    def print_tree(self):
        tree_str = '\n'.join(self.make_tree_strlist())
        print(tree_str)

    def __nice__(self):
        if self.is_leaf():
            return ' leaf(%s=%r)' % (self.name, self.value)
        else:
            return ' node(%s)' % (self.name)

    def _populate_children(self):
        if hasattr(self.config, 'items'):
            # Non-leaf
            self.children = []
            param_info_dict = self.config.get_param_info_dict()
            for key, val in self.config.items():
                param_info = param_info_dict[key]
                child_item = ConfigNodeWrapper(key, val, self, param_info)
                self.children.append(child_item)
        else:
            # Populate leaf
            self.value = self.config
            # Mark original value
            self.original = self.value
            self.children = None

    def _reset_to_default(self):
        if self.is_leaf():
            self.set_value(self.param_info.default)
        else:
            for child in self.children:
                child._reset_to_default()

    def _reset_to_original(self):
        if self.is_leaf():
            self.set_value(self.original)
        else:
            for child in self.children:
                child._reset_to_original()

    def iter_children(self):
        if self.children is None:
            raise StopIteration()
        for child in self.children:
            yield child

    @property
    def type_(self):
        if self.param_info is None:
            return None
        else:
            return self.param_info.type_

    @property
    def is_combo(self):
        if self.param_info is None:
            return False
        elif BOOL_AS_COMBO and self.type_ is bool:
            return True
        else:
            return self.param_info.valid_values is not None

    @property
    def valid_values(self):
        if self.is_combo:
            if BOOL_AS_COMBO and self.type_ is bool:
                return [True, False]
            else:
                return self.param_info.valid_values
        else:
            return None

    def is_checkable(self):
        return not BOOL_AS_COMBO and self.type_ is bool

    def is_leaf(self):
        return self.children is None

    def set_value(self, new_val):
        assert self.is_leaf(), 'can only set leaf values'
        # Update internals
        self.value = new_val
        # Update externals
        self.parent.config[self.name] = new_val

    def qt_child(self, row):
        return self.children[row]

    def qt_parent(self):
        return self.parent

    def qt_is_editable(self):
        """
        Really means able to change value.
        """
        if self.is_leaf():
            enabled = self.param_info.is_enabled(self.parent.config)
        else:
            enabled = False
        return enabled

    def qt_num_rows(self):
        if self.children is None:
            return 0
        else:
            return len(self.children)

    def qt_num_cols(self):
        return 2

    def qt_get_data(self, column):
        if column == 0:
            return self.name
        data = self.value
        if data is None:
            data = 'None'
        return data

    def qt_set_data(self, qvar):
        """
        Sets backend data using QVariants
        """
        if VERBOSE_CONFIG:
            print('[Wrapper] Attempting to set data')
        assert self.is_leaf(), 'must be a leaf'
        if self.parent is None:
            raise Exception('[Pref.qtleaf] Cannot set root preference')
        if self.qt_is_editable():
            new_val = '[Pref.qtleaf] BadThingsHappenedInPref'
            try:
                type_ = self.type_
                new_val = ut.smart_cast(qvar, type_)
            except Exception as ex:
                ut.printex(ex, keys=['qvar', 'type_'])
                raise

            if VERBOSE_CONFIG:
                print('[Wrapper] new_val=%r' % new_val)
                # print('[Wrapper] type(new_val)=%r' % type(new_val))
                # print('L____ [config.qt_set_leaf_data]')
            # TODO Add ability to set a callback function when certain
            # preferences are changed.
            self.set_value(new_val)
        if VERBOSE_CONFIG:
            print('[Wrapper] Accepted new value.')
        return True


class EditConfigWidget(QWidget):
    """
    Widget to edit a dtool.Config object
    """
    data_changed = QtCore.pyqtSignal()

    def __init__(self, rootNode, user_mode=False):
        super(EditConfigWidget, self).__init__()
        self.user_mode = user_mode
        self.init_layout()
        self.rootNode = rootNode
        self.config_model = QConfigModel(self, rootNode=rootNode)
        self.init_mvc()

    def init_layout(self):
        import guitool as gt
        self.vbox = QtGui.QVBoxLayout(self)
        self.tree_view = QtGui.QTreeView(self)
        self.delegate = ConfigValueDelegate(self.tree_view)
        self.tree_view.setItemDelegateForColumn(1, self.delegate)
        self.vbox.addWidget(self.tree_view)

        self.hbox = QtGui.QHBoxLayout()
        self.default_but = gt.newButton(self, 'Defaults', clicked=self.reset_to_default)
        self.default_but.setStyleSheet('QToolButton { border: none; }')
        self.hbox.addWidget(self.default_but)

        self.orig_but = gt.newButton(self, 'Original', clicked=self.reset_to_original)
        self.orig_but.setStyleSheet('QToolButton { border: none; }')
        self.hbox.addWidget(self.orig_but)

        if not self.user_mode:
            self.print_internals = gt.newButton(self, 'Print Internals',
                                                clicked=self.print_internals)
            self.hbox.addWidget(self.print_internals)
        self.vbox.addLayout(self.hbox)
        self.setWindowTitle(_translate('self', 'Edit Config Widget', None))
        #self.tree_view.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        #self.tree_view.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        #self.tree_view.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
        #                             QtGui.QSizePolicy.MinimumExpanding)
        # FIXME: http://doc.qt.io/qt-5/qsizepolicy.html
        #self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Preferred)
        #self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
        #                   QtGui.QSizePolicy.MinimumExpanding)
        if 0 or False:
            # debug code
            self.setStyleSheet("background-color: rgb(255,0,0); margin:5px; border:1px solid rgb(0, 255, 0); ")

    def init_mvc(self):
        import operator
        edit_triggers = reduce(operator.__or__, [
            QtGui.QAbstractItemView.CurrentChanged,
            QtGui.QAbstractItemView.DoubleClicked,
            QtGui.QAbstractItemView.SelectedClicked,
            # QtGui.QAbstractItemView.EditKeyPressed,
            # QtGui.QAbstractItemView.AnyKeyPressed,
        ])
        self.tree_view.setEditTriggers(edit_triggers)
        self.tree_view.setModel(self.config_model)
        view_header = self.tree_view.header()
        #import utool
        #utool.embed()
        #view_header.setDefaultSectionSize(250)
        #self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        #view_header.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
        #                          QtGui.QSizePolicy.MinimumExpanding)
        #view_header.setSizePolicy(QtGui.QSizePolicy.Preferred,
        #                          QtGui.QSizePolicy.Preferred)
        self.tree_view.resizeColumnToContents(0)
        self.tree_view.resizeColumnToContents(1)
        #self.tree_view.setAnimated(True)
        #view_header.setStretchLastSection(True)
        view_header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        #view_header.setResizeMode(QtGui.QHeaderView.Interactive)
        #import utool
        #utool.embed()
        #self.tree_view.header().resizeSection(0, 250)
        #setDefaultSectionSize(

        # from guitool import api_item_view
        # api_item_view.set_column_persistant_editor(self.tree_view, 1)
        # # Persistant editors
        #num_rows = 4  # self.tree_view.model.rowCount()
        #print('view.set_persistant: %r rows' % num_rows)
        if False:
            view = self.tree_view
            model = self.config_model
            column = 1
            for row in range(model.rowCount()):
                index  = model.index(row, column)
                view.openPersistentEditor(index)

        self.config_model.dataChanged.connect(self._on_change)

    def _on_change(self, top_left, bottom_right):
        self.data_changed.emit()

    def reset_to_default(self):
        print('Defaulting')
        self.rootNode._reset_to_default()
        self.refresh_layout()

    def reset_to_original(self):
        print('Defaulting')
        self.rootNode._reset_to_original()
        self.refresh_layout()

    def print_internals(self):
        print('Print Internals')
        self.rootNode.print_tree()

    def refresh_layout(self):
        self.config_model.layoutAboutToBeChanged.emit()
        self.config_model.layoutChanged.emit()


def newConfigWidget(config, user_mode=False):
    r"""
    Args:
        config (dtool.Config):

    CommandLine:
        python -m guitool.PrefWidget2 newConfigWidget --show
        python -m guitool.PrefWidget2 newConfigWidget --show --verbconf

    Example:
        >>> # DISABLE_DOCTEST
        >>> from guitool.PrefWidget2 import *  # NOQA
        >>> import guitool
        >>> guitool.ensure_qtapp()
        >>> import dtool
        >>> class ExampleConfig(dtool.Config):
        >>>     _param_info_list = [
        >>>         ut.ParamInfo('str_option', 'hello'),
        >>>         ut.ParamInfo('int_option', 42),
        >>>         ut.ParamInfo('float_option', 42.),
        >>>         ut.ParamInfo('none_option', None),
        >>>         ut.ParamInfo('none_combo_option', None, valid_values=[None, True, False]),
        >>>         ut.ParamInfo('combo_option', 'up', valid_values=['up', 'down', 'strange', 'charm', 'top', 'bottom']),
        >>>         ut.ParamInfo('bool_option', False),
        >>>         ut.ParamInfo('hidden_str', 'foobar', hideif=lambda cfg: not cfg['bool_option']),
        >>>         ut.ParamInfo('hidden_combo', 'one', valid_values=['oneA', 'twoB', 'threeC'], hideif=lambda cfg: not cfg['bool_option']),
        >>>     ]
        >>> config = ExampleConfig()
        >>> widget = newConfigWidget(config)
        >>> widget.rootNode.print_tree()
        >>> from plottool import fig_presenter
        >>> fig_presenter.register_qt4_win(widget)
        >>> widget.show()
        >>> ut.quit_if_noshow()
        >>> guitool.qtapp_loop(qwin=widget, freq=10)
    """
    rootNode = ConfigNodeWrapper('root', config)
    widget = EditConfigWidget(rootNode, user_mode=user_mode)
    return widget


if __name__ == '__main__':
    r"""
    CommandLine:
        python -m guitool.PrefWidget2
        python -m guitool.PrefWidget2 --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()  # for win32
    import utool as ut  # NOQA
    ut.doctest_funcs()
