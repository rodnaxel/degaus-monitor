import sys

import collections

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PanelManager:
    def __init__(self, parent=None, size=None, *args, **kwargs):
        self.parent = parent
        self.modes = ["Амперметры", "Настройки"]
        self.states = ["Max", 'Min', 'Null', 'L']
        
        self.size = size

        self.page = 0
        self.pattern = [self.states[2] for i in range(self.size)]
        self.values = ["-" for i in range(self.size)]

        self._createUi()

    def _createUi(self):
        
        def _on_switch_panel():
            current = self.stack.currentIndex()
            if current == 0:
                self.stack.setCurrentIndex(1)
                self.buttonAll.setVisible(True)
                self.parent.setTitle(self.modes[1])
            else:
                self.stack.setCurrentIndex(0)
                self.buttonAll.setVisible(False)
                self.parent.setTitle(self.modes[0])

        def _on_switch_group(rbutton):
            """ If switch group, then rename field labels by panel"""
            group = rbutton.text()
            if group == "I":
                self.page = 0
            elif group == "II":
                self.page = 1
            elif group == "III":
                self.page = 2
            else:
                raise ValueError("Dont find group name")
            #current = self.stack.currentWidget()
            for i in range(2):
                self.stack.widget(i).set_page(self.page)


        def _on_switch_all_buttons():

            text = self.buttonAll.text()
            self.pattern = [text for i in range(self.size)]
            self.pcontrol.set_data(self.pattern)

        self.parent.setTitle('Амперметры')

        # Radiobuttons for switch group (only channels more than 50)
        self.radiobox = RadioBox(title="Группа обмоток: ", group_names=('I', 'II', 'III'))
        self.radiobox.setEnabled(False)

        #  Button used to switch all switcher of control panel at one time
        self.buttonAll = SwitchButton()
        self.buttonAll.setVisible(False)

        # Button used to switch between control and view panels
        self.buttonSwitch = SwitchButton(labels=["Настройки", "Амперметры"])
        self.buttonSwitch.setMinimumWidth(120)

        # Panels
        self.pview = PanelView(data=self.values)
        self.pcontrol = PanelControl(data=self.pattern)
        
        # Layouts
        hbox = QHBoxLayout()
        hbox.addWidget(self.radiobox)
        hbox.addStretch(2)
        hbox.addWidget(self.buttonAll)
        hbox.addWidget(self.buttonSwitch)

        stack = self.stack = QStackedLayout()
        stack.insertWidget(0, self.pview)
        stack.insertWidget(1, self.pcontrol)
        stack.setCurrentIndex(0)

        layout = self.layout = QVBoxLayout(self.parent)
        layout.addLayout(hbox)
        layout.setSpacing(10)
        layout.addLayout(stack)

        # Connect Signal/Slots
        self.radiobox.buttonClicked[QAbstractButton].connect(_on_switch_group)
        self.buttonAll.clicked.connect(_on_switch_all_buttons)
        self.buttonSwitch.clicked.connect(_on_switch_panel)

    def resize(self, n):
        self.size = n
        # Lock/Unlock radiobuttons {I, II, III}
        if self.size > 50:
            self.radiobox_enabled(True)
        else:
            self.radiobox_enabled(False)
        # Change pattern
        self.pattern = [self.states[2] for i in range(self.size)]
        self.pcontrol.set_data(self.pattern)
        # Change values
        self.values = ["-" for i in range(self.size)]
        self.pview.set_data(self.values)

    def show_panelview(self):
        self.stack.setCurrentIndex(0)
        self.parent.setTitle(self.modes[0])
        self.buttonAll.setVisible(False)  

    def fetch_pattern(self):
        return self.pattern

    def view_show(self, data):
        self.pview.set_data(data)

    def view_clear(self):
        self.pview.clear()

    def radiobox_enabled(self, enable):
        self.radiobox.setEnabled(enable)
        if not enable:
            default_button = self.radiobox.group.buttons()[0]
            default_button.setChecked(True)
            self.radiobox.buttonClicked.emit(default_button)


class PanelBase(QWidget):
    ROW = 10
    COL = 5
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.page = 0
        self.delegates = []
        self.data = []

    def _createUI(self, wgt, **kwargs):
        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        row, col = (PanelBase.ROW, PanelBase.COL)
        for c in range(col):
            for r in range(row):
                name = f'{c * row + r + 1}:'
                edit = wgt(name=name, **kwargs)
                self.layout().addWidget(edit, r, c)
                self.delegates.append(edit)

    def clear(self):
        print('<PanelBase.clear>')

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data
        self.update_()

    def set_page(self, page):
        self.page = page
        label = (str(i) for i in range(page * 50 + 1, page * 50 + 51))
        self.rename(label)
        self.update_()

    def rename(self, names):
        for delegate, name in zip(self.delegates, names):
            delegate.setName(name)

    def update_(self):
        print('Invoke <PanelBase.update_()>')


class PanelView(PanelBase):
    """ 
    This class representing widget to show values 
    of voltage/current in the channels 
    """

    def __init__(self, parent=None, data=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data = data
        self._createUI(NamedEdit)

        if self.data:
            self.update_()

    def clear(self):
        self.data = ['-' for v in self.data]
        self.update_()

    def update_(self):
        for delegate, value in zip(self.delegates, self.data[self.page * 50 : self.page * 50 + 50]):
            if isinstance(value, int):
                txt = '{0:=6.2f}'.format(value/100)
            else:
                txt = value
            delegate.display(txt)


class PanelControl(PanelBase):
    """ 
    The class representing widget to configure 
    of voltage/current in the channels 
    """
    def __init__(self, parent=None, data=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data = data

        self._createUI(NamedSwitchButton)

        # Connect signal/slot
        for delegate in self.delegates:
             delegate.clicked[int, str].connect(self._on_store)

        # If send data then update view
        if self.data:
            self.update_()

    def _on_store(self, index, value):
        try:
            self.data[index] = value
        except IndexError as e:
            print(e, index, value)

    def update_(self):
        # Delegates 50, Data 43
        values = self.data[self.page * 50 : self.page * 50 + 50]
        for delegate, value in zip(self.delegates, values):
           delegate.setText(value)

class NamedWidget(QWidget):
    """ This base class for named widgets """

    def __init__(self, parent, name, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.label = label = QLabel(name)
        label.setFixedWidth(40)
        label.setAlignment(QtCore.Qt.AlignCenter)

    def setName(self, name):
        self.label.setText(name + ":")


class NamedSwitchButton(NamedWidget):
    clicked = QtCore.pyqtSignal(int, str)

    def __init__(self, parent=None, name='Label', labels=None, *args, **kwargs):
        super().__init__(parent, name, *args, **kwargs)
        self.createUi()

    def createUi(self):
        self.button = button = SwitchButton()
        button.setFixedWidth(40)
        button.setFixedHeight(20)
        layout = QFormLayout(self)
        layout.setContentsMargins(2, 1, 1, 1)
        layout.addRow(self.label, self.button)

        # Connect signals/slots
        self.button.clicked.connect(self._on_wrapped_clicked)
    
    def _on_wrapped_clicked(self):
        index = int(self.label.text()[:-1]) - 1
        value = self.button.text()
        self.clicked.emit(index, value)

    def text(self):
        return self.button.text()

    def setText(self, text):
        self.button.setText(text)

    def switch_to(self, to):
        self.button.switch_to(to)

    def clear(self):
        self.button.reset()


class NamedEdit(NamedWidget):
    def __init__(self, parent=None, name='Label', *args, **kwargs):
        super().__init__(parent, name, *args, **kwargs)
        self.createUi()

    def createUi(self):
        self.edit = edit = QLineEdit()
        self.edit.setText('-')
        edit.setReadOnly(True)
        edit.setAlignment(QtCore.Qt.AlignCenter)

        layout = QFormLayout(self)
        layout.setContentsMargins(2, 1, 1, 1)
        layout.addRow(self.label, self.edit)

    def clear(self):
        self.edit.setText('-')

    def display(self, value):
        self.edit.setText(value)

    def value(self):
        return self.edit.text()


class SwitchButton(QPushButton):
    DEFAULT_LABELS = ["Max", 'Min', 'Null', 'L']

    def __init__(self, parent=None, labels=None, *args, **kwargs):
        super().__init__(text='text', *args, **kwargs)
        self.labels = labels or SwitchButton.DEFAULT_LABELS
        self.setText(self.labels[0])

    def mousePressEvent(self, e):
        self.switch()
        super().mousePressEvent(e)

    def reset(self):
        self.current = 0
        self.setText(self.labels[self.current])

    def switch(self):
        current_index = self.labels.index(self.text()) 
        try:
            next_state = self.labels[current_index + 1]
        except IndexError:
            next_state = self.labels[0]
        self.setText(next_state) 

    def switch_to(self, index):
        self.setText(self.labels[index])


class RadioBox(QWidget):
    buttonClicked = QtCore.pyqtSignal(QAbstractButton)

    def __init__(self, title, group_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.group_names = group_names

        self.createUi()

    def createUi(self):
        label = QLabel(self.title)
        layout = QHBoxLayout(self)
        layout.addWidget(label)

        group = self.group = QButtonGroup(self)
        for i, name in enumerate(self.group_names):
            rb = QRadioButton(name)
            if i == 0:
                rb.setChecked(True)
            group.addButton(rb)
            layout.addWidget(rb)

        # Connect signal/slot
        group.buttonClicked[QAbstractButton].connect(self.buttonClicked)
    
    def setChecked(self, index):
        btn = list(self.group.buttons())[index]
        btn.setChecked(True)
        self.buttonClicked.emit(btn)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
