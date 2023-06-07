import logging
from PySide2 import QtCore, QtGui, QtWidgets
from . import htmlhandler
logger = logging.getLogger(__name__)


def block_signals(iterable, block):
    for i in iterable:
        i.blockSignals(block)


def update_style(obj, name, value):
    obj.setProperty(name, value)
    obj.setStyle(obj.style())



class BaseWindow(QtWidgets.QWidget):
    def __init__(self, title=''):
        super(BaseWindow, self).__init__()
        # self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        self.setWindowTitle(title)

    def load_qsettings(self):
        self.settings = QtCore.QSettings('regnareb', 'Stream Manager')
        if self.settings.value('initialised_once'):
            self.restoreGeometry(self.settings.value('geometry'))
            self.restoreState(self.settings.value('windowState'))
        else:
            logger.info('First launch.')
            self.settings.setValue('initialised_once', 1)

    def quit(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())


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
        self.parent = parent
        self.labels = []
        self.fields = []
        self.sliders = []
        self.spacers = []
        self.buttons = []
        self.comboboxes = []
        self.toolbuttons = []
        self.checkboxes = []
        self.separators = []

    def addLabel(self, text=''):
        self.label = QtWidgets.QLabel(self.parent)
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

    def addField(self, value=0, validator='', minimum=None, maximum=None, decimals=3):
        if validator == 'float':
            self.field = QtWidgets.QDoubleSpinBox(self.parent)
            self.field.setDecimals(decimals)
            self.field.setSingleStep(0.5)
            self.field.setCorrectionMode(QtWidgets.QAbstractSpinBox.CorrectToNearestValue)
        else:
            self.field = QtWidgets.QSpinBox(self.parent)
        self.field.setAccelerated(True)
        self.field.setMinimumSize(QtCore.QSize(70, 0))
        self.field.setMaximumSize(QtCore.QSize(70, 16777215))
        self.field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        if minimum:
            self.field.setMinimum(minimum)
        if maximum:
            self.field.setMaximum(maximum)
        self.field.setValue(value)
        self.fields.append(self.field)
        self.addWidget(self.field)
        return self.field

    def addSlider(self, value=0, mode='', minimum=None, maximum=None):
        if mode == 'float':
            self.slider = FloatSlider(self.parent)
        else:
            self.slider = QtWidgets.QSlider(self.parent)
        self.slider.setOrientation(QtCore.Qt.Horizontal)
        if minimum is not None:
            self.slider.setMinimum(minimum)
        if maximum is not None:
            self.slider.setMaximum(maximum)
        self.slider.setValue(value)
        self.sliders.append(self.slider)
        self.addWidget(self.slider)
        return self.slider

    def addCombobox(self, items=[]):
        self.combobox = QtWidgets.QComboBox(self.parent)
        for item in items:
            self.combobox.addItem(item)
        self.comboboxes.append(self.combobox)
        self.addWidget(self.combobox)
        return self.combobox

    def addToolbutton(self):
        self.toolbutton = QtWidgets.QToolButton(self.parent)
        self.toolbuttons.append(self.toolbutton)
        self.addWidget(self.toolbutton)
        return self.toolbutton

    def addCheckbox(self, text='', state=False):
        self.checkbox = QtWidgets.QCheckBox(text, parent=self.parent)
        self.checkbox.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)
        self.checkboxes.append(self.checkbox)
        self.addWidget(self.checkbox)
        return self.checkbox

    def addButton(self, label='', size=[]):
        self.button = QtWidgets.QPushButton(self.parent)
        self.button.setText(label)
        if size:
            self.button.setMaximumSize(QtCore.QSize(*size))
        self.buttons.append(self.button)
        self.addWidget(self.button)
        return self.button

    def addSeparator(self):
        self.separator = QtWidgets.QFrame(self.parent)
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

    def connectFieldSlider(self):
        self.field.valueChanged.connect(self.toSlider)
        self.slider.valueChanged.connect(self.toField)

    def toField(self, *args):
        self.field.setValue(self.slider.value())

    def toSlider(self, *args):
        self.slider.setValue(args[0])

    def setText(self, texts):
        for label, text in zip(self.labels, texts):
            label.setText(text)

    def setValue(self, values):
        for field, value in zip(self.fields, values):
            field.setValue(value)
        for checkbox, state in zip(self.checkboxes, values):
            checkbox.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)

    def setItem(self, items):
        for combobox, item in zip(self.comboboxes, items):
            combobox.setCurrentIndex(item)

    def getValue(self):
        values = []
        for field in self.fields:
            values.append(field.valueFromText(field.text()))
        for combobox in self.comboboxes:
            values.append(combobox.currentIndex())
        for checkbox in self.checkboxes:
            state = checkbox.checkState()
            values.append(bool(state))
        return values

    def hide(self):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.hide()

    def show(self):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.show()

    def setToolTip(self, tip):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.setToolTip(tip)

    def setStatusTip(self, tip):
        for widget in self.labels + self.fields + self.sliders + self.comboboxes + self.toolbuttons + self.checkboxes + self.separators + self.buttons:
            widget.setToolTip(tip)




class QLoggerHandler(htmlhandler.HtmlStreamHandler):
    def __init__(self, signal):
        super(QLoggerHandler, self).__init__()
        self.signal = signal

    def emit(self, record):
        message = self.format(record)
        self.signal.emit(QtCore.SIGNAL("logMsg(QString)"), message)



class LogPanel(QtWidgets.QDockWidget):
    changed_loglevel = QtCore.Signal(str)

    def __init__(self, parent=None, title=''):
        super(LogPanel, self).__init__(parent=parent)
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
        self.connect(self.emitter, QtCore.SIGNAL("logMsg(QString)"), self.interface['textedit'].append)
        self.handler = QLoggerHandler(self.emitter)
        formatter = logging.Formatter('<span title="line %(lineno)d">%(levelname)s %(name)s.%(funcName)s() - %(message)s</span>')
        self.handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.handler)



class KeySequenceRecorder(QtWidgets.QLineEdit):
    def __init__(self, keySequence, parent=None):
        super(KeySequenceRecorder, self).__init__(parent)
        self.setKeySequence(keySequence)

    def setKeySequence(self, keySequence):
        try:
            self.keySequence = keySequence.toString(QtGui.QKeySequence.NativeText)
        except AttributeError:
            self.keySequence = keySequence
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



class Systray(QtWidgets.QMainWindow):
    def __init__(self):
        super(Systray, self).__init__()
        self.createTrayIcon()

    def setIcon(self, icon):
        self.setWindowIcon(icon)
        self.trayIcon.setIcon(icon)

    def restore(self):
        self.show()
        self.activateWindow()

    def iconActivated(self, reason):
        if reason in (QtWidgets.QSystemTrayIcon.Trigger, QtWidgets.QSystemTrayIcon.DoubleClick):
            self.restore()

    def createTrayIcon(self):
        self.quitAction = QtWidgets.QAction("&Quit", self, triggered=self.quit)
        self.trayIconMenu = QtWidgets.QMenu(self)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIcon = QtWidgets.QSystemTrayIcon(self)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.messageClicked.connect(self.showNormal)
        self.trayIcon.activated.connect(self.iconActivated)
        self.trayIcon.show()

    def closeEvent(self, event):
        if self.trayIcon.isVisible():
            if not self.settings.value('showed_quitmessage'):
                QtWidgets.QMessageBox.information(self, "Minimise to System Tray", "The program will keep running in the system tray. To terminate the program, choose <b>Quit</b> in the context menu of the system tray icon.")
                self.settings.setValue("showed_quitmessage", True)
            self.hide()
            event.ignore()
        else:
            self.quit()

    def quit(self):
        QtGui.qApp.quit()





class PlainTextEdit(QtWidgets.QPlainTextEdit):
    editingFinished = QtCore.Signal()

    def focusOutEvent(self, event):
        super(PlainTextEdit, self).focusOutEvent(event)
        self.editingFinished.emit()



class LineditSpoiler(QtWidgets.QLineEdit):
    def __init__(self, blurAmount=10, parent=None):
        super(LineditSpoiler, self).__init__(parent=parent)
        self.blurAmount = blurAmount
        self.effect = QtWidgets.QGraphicsBlurEffect(self)
        self.effect.setBlurRadius(blurAmount)
        self.setGraphicsEffect(self.effect)

    def enterEvent(self, event):
        self.effect.setBlurRadius(0)
        super(LineditSpoiler, self).enterEvent(event)

    def leaveEvent(self, event):
        self.effect.setBlurRadius(self.blurAmount)
        super(LineditSpoiler, self).leaveEvent(event)



class KeySequenceRecorder(QtWidgets.QLineEdit):
    def __init__(self, keySequence, parent=None):
        super(KeySequenceRecorder, self).__init__(parent)
        self.setKeySequence(keySequence)

    def setKeySequence(self, keySequence):
        try:
            self.keySequence = keySequence.toString(QtGui.QKeySequence.NativeText)
        except AttributeError:
            self.keySequence = keySequence
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
