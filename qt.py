import time
import logging
import collections
try:
    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
except ImportError:
    from PySide2 import QtCore, QtGui, QtWidgets
    from PySide2.QtCore import Qt
    from PySide2.QtWidgets import QAction
from . import common
from . import htmlhandler
logger = logging.getLogger(__name__)


def block_signals(iterable, block):
    for i in iterable:
        i.blockSignals(block)


def update_style(obj, name, value):
    obj.setProperty(name, value)
    obj.setStyle(obj.style())


class BaseMixin():
    """Use this Mixin class to provide an automatic way to save and restore all the data for the UI state.
    You can pass arguments for the QSettings object like organization and application name and settings format.
    It can be used with a QMainWindow or QWidget like that:

    class BaseWindow(BaseMixin, QtWidgets.QMainWindow):
        def __init__(self, *args):
            super(BaseWindow, self).__init__()
            self.load_settings(*args)
    """
    def load_settings(self, *args):
        self.settings = QtCore.QSettings(*args)
        self.settings.beginGroup('mainWindow')
        self.restoreGeometry(self.settings.value('geometry'))
        try:
            self.restoreState(self.settings.value('saveState', self.saveState()))
        except AttributeError:
            pass
        self.move(self.settings.value('pos', self.pos()))
        self.resize(self.settings.value('size', self.size()))
        if common.string2bool(self.settings.value('maximized')):
           self.showMaximized()
        if common.string2bool(self.settings.value('fullScreen')):
           self.showFullScreen()
        self.settings.endGroup()

    def closeEvent(self, event):
        self.settings.beginGroup('mainWindow')
        self.settings.setValue('geometry', self.saveGeometry())
        try:
            self.settings.setValue('saveState', self.saveState())
        except AttributeError:
            pass
        if not self.isMaximized() and not self.isFullScreen():
            self.settings.setValue('pos', self.pos())
            self.settings.setValue('size', self.size())
        self.settings.setValue('maximized', self.isMaximized())
        self.settings.setValue('fullScreen', self.isFullScreen())
        self.settings.endGroup()


class FloatSlider(QtWidgets.QSlider):
    """Create a slider able to return floats as a value."""
    def __init__(self, parent, decimals=3, *args, **kargs):
        super(FloatSlider, self).__init__(parent, *args, **kargs)
        self._multi = 10 ** decimals
        self.setMinimum(self.minimum())
        self.setMaximum(self.maximum())

    def value(self):
        return float(super(FloatSlider, self).value()) / self._multi

    def setMinimum(self, value):
        return super(FloatSlider, self).setMinimum(value * self._multi)

    def setMaximum(self, value):
        return super(FloatSlider, self).setMaximum(value * self._multi)

    def setValue(self, value):
        super(FloatSlider, self).setValue(int(value * self._multi))


class RowLayout(QtWidgets.QHBoxLayout):
    """An object where you are able to add different UI elements easily and automatically."""
    def __init__(self, parent=None):
        super(RowLayout, self).__init__(parent)
        self.labels = []
        self.fields = []
        self.sliders = []
        self.spacers = []
        self.buttons = []
        self.comboboxes = []
        self.toolbuttons = []
        self.checkboxes = []
        self.separators = []

    def addLabel(self, text='', *args, **kwargs):
        self.label = QtWidgets.QLabel(*args, **kwargs)
        self.label.setText(text)
        # self.label.setMinimumSize(QtCore.QSize(125, 19))
        # self.label.setMaximumSize(QtCore.QSize(125, 16777215))
        self.labels.append(self.label)
        self.addWidget(self.label)
        return self.label

    def addSpacer(self):
        self.spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.spacers.append(self.spacer)
        self.addItem(self.spacer)
        return self.spacer

    def addField(self, text='', validator='', minimum=None, maximum=None, decimals=2, singlestep=1, accelerated=True, *args, **kwargs):
        self.field = BetterLineEdit(text, validator, *args, **kwargs)
        self.field.setDecimals(decimals)
        self.field.setSingleStep(singlestep)
        self.field.setAccelerated(accelerated)
        if validator in [QtGui.QIntValidator, QtGui.QDoubleValidator]:
            self.field.setMinimumSize(QtCore.QSize(80, 0))
            self.field.setMaximumSize(QtCore.QSize(80, 16777215))
        if minimum is not None:
            self.field.setMinimum(minimum)
        if maximum is not None:
            self.field.setMaximum(maximum)
        self.fields.append(self.field)
        self.addWidget(self.field)
        return self.field

    def addSlider(self, value=0, mode='', minimum=None, maximum=None, *args, **kwargs):
        if mode == 'float':
            self.slider = FloatSlider(*args, **kwargs)
        else:
            self.slider = QtWidgets.QSlider(*args, **kwargs)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        if minimum is not None:
            self.slider.setMinimum(minimum)
        if maximum is not None:
            self.slider.setMaximum(maximum)
        self.slider.setValue(value)
        self.sliders.append(self.slider)
        self.addWidget(self.slider)
        return self.slider

    def addCombobox(self, items=[], *args, **kwargs):
        self.combobox = QtWidgets.QComboBox(*args, **kwargs)
        for item in items:
            self.combobox.addItem(item)
        self.comboboxes.append(self.combobox)
        self.addWidget(self.combobox)
        return self.combobox

    def addToolbutton(self, *args, **kwargs):
        self.toolbutton = QtWidgets.QToolButton(*args, **kwargs)
        self.toolbuttons.append(self.toolbutton)
        self.addWidget(self.toolbutton)
        return self.toolbutton

    def addCheckbox(self, text='', state=False, *args, **kwargs):
        self.checkbox = ExclusiveCheckBox(text, *args, **kwargs)
        self.checkbox.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)
        self.checkboxes.append(self.checkbox)
        self.addWidget(self.checkbox)
        return self.checkbox

    def addButton(self, label='', size=[], *args, **kwargs):
        self.button = QtWidgets.QPushButton(*args, **kwargs)
        self.button.setText(label)
        if size:
            self.button.setMaximumSize(QtCore.QSize(*size))
        self.buttons.append(self.button)
        self.addWidget(self.button)
        return self.button

    def addSeparator(self, *args, **kwargs):
        self.separator = QtWidgets.QFrame(*args, **kwargs)
        self.separator.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.separators.append(self.separator)
        self.addWidget(self.separator)
        return self.separator

    def createValidator(self, validator, minimum=None, maximum=None, decimals=3):
        if validator == 'int':
            self.field.setValidator(QtWidgets.QIntValidator(minimum, maximum, self))
        elif validator == 'float':
            self.field.setValidator(QtWidgets.QDoubleValidator(minimum, maximum, decimals, self))
        else:
            return False
        return True

    def connectCheckboxState(self):
        """Disable/Enable all widgets depending of the state of the checkbox"""
        state = self.checkbox.checkState()
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.buttons:
            widget.setEnabled(state)

    def connectFieldSlider(self):
        self.field.valueChanged.connect(self.toSlider)
        self.slider.valueChanged.connect(self.toField)

    def toField(self, *args):
        self.field.blockSignals(True)
        self.field.setValue(self.slider.value())
        self.field.blockSignals(False)

    def toSlider(self, *args):
        self.slider.blockSignals(True)
        self.slider.setValue(args[0])
        self.slider.blockSignals(False)

    def setTexts(self, texts):
        for label, text in zip(self.labels, texts):
            label.setText(text)

    def setFields(self, values):
        for field, value in zip(self.fields, values):
            field.setText(value)

    def setStates(self, states):
        for checkbox, state in zip(self.checkboxes, states):
            checkbox.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    def setItems(self, items):
        for combobox, item in zip(self.comboboxes, items):
            combobox.setCurrentIndex(item)

    def getValues(self, by_objectnames=False):
        """You can automatically get, save and restore states of your UI elements:
        Either by objectNames if you set them as arguments each time you add an element
        Or by the order of wich they are created
        """
        if by_objectnames:
            data = {}
            for field in self.fields:
                data[field.objectName()] = field.text()
            for slider in self.sliders:
                data[slider.objectName()] = slider.value()
            for combobox in self.comboboxes:
                data[combobox.objectName()] = combobox.currentText()
            for checkbox in self.checkboxes:
                data[checkbox.objectName()] = bool(checkbox.checkState())
        else:
            data = {'field': [], 'sliders': [], 'combobox': [], 'checkbox': []}
            for field in self.fields:
                data['field'].append(field.text())
            for slider in self.sliders:
                data['combobox'].append(checkbox.setCheckState(slider.value()))
            for combobox in self.comboboxes:
                data['combobox'].append(combobox.currentText())
            for checkbox in self.checkboxes:
                data['checkbox'].append(bool(checkbox.checkState()))
        return data

    def restoreValues(self, values, by_objectnames=False):
        """Restore the states of your UI elements from getValues"""
        if by_objectnames:
            for field in self.fields:
                if values.get(field.objectName()):
                    field.setText(values[field.objectName()])
            for slider in self.sliders:
                if values.get(slider.objectName()):
                    slider.setCheckState(values[slider.objectName()])
            for combobox in self.comboboxes:
                if values.get(combobox.objectName()):
                    combobox.setCurrentIndex(combobox.findText(values[combobox.objectName()]))
            for checkbox in self.checkboxes:
                if values.get(checkbox.objectName()):
                    checkbox.setCheckState(QtCore.Qt.Checked if values[checkbox.objectName()] else QtCore.Qt.Unchecked)
        else:
            for i, field in enumerate(self.fields):
                field.setText(values['field'][i])
            for i, slider in enumerate(self.sliders):
                slider.setCheckState(values['sliders'][i])
            for i, combobox in enumerate(self.comboboxes):
                combobox.setCurrentIndex(values['combobox'][i])
            for i, checkbox in enumerate(self.checkboxes):
                checkbox.setCheckState(QtCore.Qt.Checked if values['checkbox'][i] else QtCore.Qt.Unchecked)

    def hide(self):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.hide()

    def show(self):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.show()

    def setToolTip(self, tip):
        """Add a general tooltip for all row"""
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.setToolTip(tip)

    def setEnabledChildren(self, state):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.setEnabled(state)


def GroupBox(title, items, collapsible=True, collapsed=False, *args, **kwargs):
    """Create a QGroupBox and add all elements in the 'items' argument to it.
    The collapsible argument make the QGroupBox foldable,
    """
    if collapsible:
        groupbox = CollapsibleGroupBox(title=title, collapsed=collapsed, *args, **kwargs)
    else:
        groupbox = QtWidgets.QGroupBox(title=title, *args, **kwargs)
    vbox = QtWidgets.QVBoxLayout()
    groupbox.setLayout(vbox)
    for i in items.values():
        vbox.addLayout(i)
    return groupbox


class CollapsibleGroupBox(QtWidgets.QGroupBox):
    """A QGroupBox that can be collapSed by clicking on its title.
    You can set the speed at which the animation goes by modifying the attribute 'animation_duration'.
    The prefix attribute can be used to add an ASCII icon in front of the title.
    """
    def __init__(self, title, collapsed=False, prefix={True: '▶  ', False: '▼  '}, *args, **kwargs):
        title = prefix[collapsed] + title
        super(CollapsibleGroupBox, self).__init__(title, *args, **kwargs)
        self.setStyleSheet('''
            QGroupBox:flat {{
                border-left: none;
                border-right: none;
                border-bottom: none;
                border-radius: 0px;
            }}''')
        self.animation_duration = 150
        self.prefix = prefix
        self.collapsed = collapsed
        if collapsed:
            self.on_toggle(collapsed)

    def on_toggle(self, collapsed):
        for i in [self, self.window()]:
            setattr(i, 'collapse_animation', QtCore.QPropertyAnimation(i, b'maximumHeight'))
            i.collapse_animation.setDuration(self.animation_duration)
            i.collapse_animation.setStartValue(i.sizeHint().height() if collapsed else 20)
            i.collapse_animation.setEndValue(20 if collapsed else i.sizeHint().height())
            i.collapse_animation.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
            i.collapse_animation.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        character = self.title()[:len(self.prefix[not collapsed])]
        title = self.title().replace(character, self.prefix[collapsed])
        self.setTitle(title)
        self.setFlat(collapsed)
        self.collapsed = collapsed

    def mouseReleaseEvent(self, event):
        super(CollapsibleGroupBox, self).mouseReleaseEvent(event)
        box = QtWidgets.QStyleOptionGroupBox()
        self.initStyleOption(box)
        hit = self.style().hitTestComplexControl(QtWidgets.QStyle.CC_GroupBox, box, event.pos())
        if (hit == QtWidgets.QStyle.SC_ScrollBarAddLine):
            self.on_toggle(not self.collapsed)


class QLoggerHandler(htmlhandler.HtmlStreamHandler):
    def __init__(self, signal):
        super(QLoggerHandler, self).__init__()
        self.signal = signal

    def emit(self, record):
        message = self.format(record)
        self.signal.emit(QtCore.SIGNAL('logMsg(QString)'), message)


class LogPanel(QtWidgets.QDockWidget):
    changed_loglevel = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(LogPanel, self).__init__(*args, **kwargs)
        self.setWindowTitle('Logs')
        self.setObjectName('logs')
        self.levels = ['Debug', 'Info', 'Warning', 'Error', 'Critical']
        self.interface = {}
        self.interface['main'] = QtWidgets.QWidget()
        self.interface['layoutv'] = QtWidgets.QVBoxLayout()
        self.interface['layouth'] = QtWidgets.QHBoxLayout()
        self.interface['label'] = QtWidgets.QLabel('Logs Level:')
        self.interface['levels'] = QtWidgets.QComboBox()
        self.interface['levels'].insertItems(0, self.levels)
        self.interface['levels'].currentIndexChanged.connect(self.changed_loglevel.emit)
        self.interface['textedit'] = QtWidgets.QTextBrowser()
        self.interface['textedit'].setOpenLinks(False)
        self.interface['clear'] = QtWidgets.QPushButton('Clear')
        self.interface['clear'].clicked.connect(self.interface['textedit'].clear)
        self.interface['layouth'].addStretch()
        self.interface['layouth'].addWidget(self.interface['label'])
        self.interface['layouth'].addWidget(self.interface['levels'])
        self.interface['layouth'].addStretch()
        self.interface['layouth'].addWidget(self.interface['clear'])
        self.interface['layoutv'].addLayout(self.interface['layouth'])
        self.interface['layoutv'].addWidget(self.interface['textedit'])
        self.interface['main'].setLayout(self.interface['layoutv'])
        self.setWidget(self.interface['main'])
        # Use old syntax signals as you can't have multiple inheritance with QObject
        self.emitter = QtCore.QObject()
        self.connect(self.emitter, QtCore.SIGNAL('logMsg(QString)'), self.interface['textedit'].append)
        self.handler = QLoggerHandler(self.emitter)
        formatter = logging.Formatter('<span title="line %(lineno)d">%(levelname)s %(name)s.%(funcName)s() - %(message)s</span>')
        self.handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.handler)


class KeySequenceRecorder(QtWidgets.QLineEdit):
    """A LineEdit that show the last key sequence pressed when the field was selected."""
    def __init__(self, keySequence, *args, **kwargs):
        super(KeySequenceRecorder, self).__init__(*args, **kwargs)
        self.keymap = {'Esc': ''}
        self.setKeySequence(keySequence)

    def setKeySequence(self, keySequence):
        try:
            self.keySequence = keySequence.toString(QtGui.QKeySequence.NativeText)
        except AttributeError:
            self.keySequence = keySequence
        self.keySequence = self.keymap.get(self.keySequence, self.keySequence)
        self.setText(self.keySequence)

    def keyPressEvent(self, e):
        if e.type() == QtCore.QEvent.KeyPress:
            key = e.key()
            if key == QtCore.Qt.Key_unknown:
                logger.warning('Unknown key for shortcut')
                return
            if(key == QtCore.Qt.Key_Control or
            key == QtCore.Qt.Key_Shift or
            key == QtCore.Qt.Key_Alt or
            key == QtCore.Qt.Key_Meta):
                return
            modifiers = e.modifiers()
            if modifiers & QtCore.Qt.ShiftModifier:
                key += QtCore.Qt.SHIFT
            if modifiers & QtCore.Qt.ControlModifier:
                key += QtCore.Qt.CTRL
            if modifiers & QtCore.Qt.AltModifier:
                key += QtCore.Qt.ALT
            if modifiers & QtCore.Qt.MetaModifier:
                key += QtCore.Qt.META
            self.setKeySequence(QtGui.QKeySequence(key))


class SystrayMixin():
    """Create a systray icon with basic interactivity to restore the main window and quit the main app.
    You need to give a reference to the main app as first argument.
    A settings attribute need to be created in the main class for the MessageBox to be displayed only once.

class Tray(SystrayMixin, QtWidgets.QWidget):
    def __init__(self, mainapp, *args, **kwargs):
        icon = QtGui.QIcon('icon.png')
        self.settings = QtCore.QSettings('organisation', 'appname')
        super(Tray, self).__init__(mainapp, icon, *args, **kwargs)

app = QtWidgets.QApplication(sys.argv)
tray = Tray(app)
sys.exit(app.exec())
    """
    def __init__(self, mainapp, icon=None, *args, **kwargs):
        super(SystrayMixin, self).__init__(*args, **kwargs)
        self.mainapp = mainapp
        self.create_tray_icon()
        if icon:
            self.set_icon(icon)

    def set_icon(self, icon):
        self.setWindowIcon(icon)
        self.trayicon.setIcon(icon)

    def restore(self):
        self.show()
        self.activateWindow()

    def iconActivated(self, reason):
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.restore()

    def create_tray_icon(self):
        self.quitAction = QAction('&Quit', self, triggered=self.quit)
        self.trayicon_menu = QtWidgets.QMenu(self)
        self.trayicon_menu.addSeparator()
        self.trayicon_menu.addAction(self.quitAction)
        self.trayicon = QtWidgets.QSystemTrayIcon(self)
        self.trayicon.setContextMenu(self.trayicon_menu)
        self.trayicon.messageClicked.connect(self.showNormal)
        self.trayicon.activated.connect(self.iconActivated)
        self.trayicon.show()

    def closeEvent(self, event):
        if self.trayicon.isVisible():
            if not self.settings.value('tray_showed_quitmessage'):
                QtWidgets.QMessageBox.information(self, 'Minimise to System Tray', 'The program will keep running in the system tray. To terminate the program, choose <b>Quit</b> in the context menu of the system tray icon.')
                self.settings.setValue('tray_showed_quitmessage', True)
            self.hide()
            event.ignore()
        else:
            super(SystrayMixin, self).closeEvent()
            self.quit()

    def quit(self):
        self.mainapp.quit()


class EditingFinishedMixin():
    """A Mixin that add a signal for editing finished to widgets that do not support it, like QTextEdit and QPlainTextEdit
    A  with a signal editingFinished missing from the official implementation."""
    editingFinished = QtCore.Signal()

    def focusOutEvent(self, event):
        super(EditingFinishedMixin, self).focusOutEvent(event)
        self.editingFinished.emit()


class LineditSpoilerMixin():
    """A Mixin that blur its content unless the mouse hover over it."""
    def __init__(self, spoilerblur=0, *args, **kwargs):
        super(LineditSpoilerMixin, self).__init__(*args, **kwargs)
        self._spoilerblur_effect = QtWidgets.QGraphicsBlurEffect(self)
        self.setSpoilerBlur(spoilerblur)

    def setSpoilerBlur(self, value):
        """Set the blur amount, can be set to 0 to disable it"""
        self._spoilerblur = value
        self._spoilerblur_effect.setBlurRadius(value)
        if value:
            self.setGraphicsEffect(self._spoilerblur_effect)
        else:
            self.setGraphicsEffect(0)  # TODO: Check if it works

    def enterEvent(self, event):
        self._spoilerblur_effect.setBlurRadius(0)
        super(LineditSpoilerMixin, self).enterEvent(event)

    def leaveEvent(self, event):
        self._spoilerblur_effect.setBlurRadius(self._spoilerblur)
        super(LineditSpoilerMixin, self).leaveEvent(event)



class BetterLineEdit(QtWidgets.QLineEdit):
    valueChanged = QtCore.Signal(str)

    def __init__(self, text='', validator=None, *args, **kwargs):
        super(BetterLineEdit, self).__init__(str(text), *args, **kwargs)
        self.validator = validator
        self._activate_undo = False
        self._decimals = 2
        self._singlestep = 1
        self._minimum = None
        self._maximum = None
        self._accelerated = 1
        self._accelerated_rate = 1
        self._accelerated_timer = 0
        self._accelerated_seconds = 3
        self._return_placeholder = True
        self.textChanged.connect(self.valueChanged.emit)

    def text(self):
        text = super(BetterLineEdit, self).text()
        if text == '' and self._return_placeholder:
            return self.placeholderText()
        return text

    def setDecimals(self, value):
        self._decimals = value

    def setSingleStep(self, value):
        self._singlestep = value

    def setMinimum(self, value):
        self._minimum = value

    def setMaximum(self, value):
        self._maximum = value

    def setAccelerated(self, value):
        self._accelerated = value

    def wheelEvent(self, event):
        sign = 1 if event.angleDelta().y() > 0 else -1
        self._event(event, sign)
        super(BetterLineEdit, self).wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down]:
            sign = 1 if event.key()==QtCore.Qt.Key_Up else -1
            if self._accelerated and self.validator in [QtGui.QIntValidator, QtGui.QDoubleValidator]:
                if event.isAutoRepeat():
                    elapsed = time.time() - self._accelerated_timer
                    power = int(elapsed/self._accelerated_seconds)
                    print(power)
                    self._accelerated_rate = pow(10, power)
                else:
                    self._accelerated_rate = 1
                    self._accelerated_timer = time.time()
            self._event(event, sign)
        super(BetterLineEdit, self).keyPressEvent(event)

    def _event(self, event, sign):
        if self.validator in [QtGui.QIntValidator, QtGui.QDoubleValidator]:
            multiplier = 0.1 if event.modifiers() == Qt.ControlModifier else 10 if event.modifiers() == Qt.ShiftModifier else 1

            try:
                value = float(self.text()) + sign * self._singlestep * multiplier * self._accelerated_rate
            except ValueError:
                value = 0  # If the value is not valid reset it

            if self._minimum is not None:
                min(value, self._minimum)
            if self._maximum is not None:
                max(value, self._maximum)
            self.setText(value)
        elif self._activate_undo:
            if sign > 0:
                self.undo()
            else:
                self.redo()
        event.accept()

    def setText(self, value):
        try:
            if self.validator == QtGui.QIntValidator:
                    value = str(int(value))
            elif self.validator == QtGui.QDoubleValidator:
                value = f'{float(value):.{self._decimals}f}'
        except ValueError:
            value = '0'  # If the value is not valid reset it
        super(BetterLineEdit, self).setText(value)

    def setValue(self, value):
        self.setText(str(value))

    def value(self):
        return self.text()


class ExclusiveCheckBox(QtWidgets.QCheckBox):
    _exclusives = collections.defaultdict(set)

    def __init__(self, text='', exclusive_group=None, always_one_active=False, *args, **kwargs):
        super(ExclusiveCheckBox, self).__init__(text, *args, **kwargs)
        self._exclusive_group = None
        self._always_one_active = False
        if exclusive_group:
            self.setExclusive(exclusive_group, always_one_active)

    def setExclusive(self, group, always_one_active=False):
        self.clicked.connect(self.checkExclusive)
        self._exclusives[group].add(self)
        self._exclusive_group = group
        for i in self._exclusives[group]:
            i._always_one_active = always_one_active

    def removeExclusive(self, group):
        self._exclusives[group].remove(self)
        self._exclusive_group = None

    def checkExclusive(self):
        if not self._exclusive_group:
            return
        if not self.isChecked() and not self._always_one_active:
            return
        if not self.isChecked() and self._always_one_active:  # always have one checkbox active
            t = common.Enum(self._exclusives[self._exclusive_group])
            obj = t.next(current=self)
            obj.setChecked(True)
            return
        for i in self._exclusives[self._exclusive_group]:  # Otherwise uncheck every other ones
            if i != self:
                i.setChecked(not self.isChecked())
