import sys

import collections

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PanelManager:
    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent

        self.modes = ["Амперметры", "Настройки"]
        self.states = ["Max", 'Min', 'Null', 'L']

        self.pattern = None
        self.values = None

        self.create_widget()

    def create_widget(self):
        self.parent.setTitle('Амперметры')

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
            print(list(self.pcontrol.get_states()))
            group_name = rbutton.text()
            if group_name == "I":
                new_names = (str(i) for i in range(1,51))
            elif group_name == "II":
                new_names = (str(i) for i in range(51,101))
            elif group_name == "III":
                new_names = (str(i) for i in range(101,151))
            else:
                raise ValueError("Dont find group name")
            current_panel = self.stack.currentWidget()
            current_panel.rename(new_names)

        def _on_switch_pattern():
            state = self.buttonAll.text()
            index = self.states.index(state)
            self.pcontrol.set_states(index)

        # Radiobuttons for switch group (only channels more than 50)
        self.radiobox = radiobox = RadioBox(title="Группа обмоток: ", group_names=('I', 'II', 'III'))
        self.radiobox.setEnabled(False)

        #  Button used to switch all switcher of control panel at one time
        self.buttonAll = SwitchButton(labels=self.states)
        self.buttonAll.setVisible(False)

        # Button used to switch between control and view panels
        self.buttonSwitch = SwitchButton(labels=["Настройки", "Амперметры"])

        # Panels
        self.pview = PanelView()
        self.pcontrol = PanelControl(states=self.states)

        # Layouts
        hbox = QHBoxLayout()
        hbox.addWidget(radiobox)
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
        radiobox.buttonClicked[QAbstractButton].connect(_on_switch_group)
        self.buttonAll.clicked.connect(_on_switch_pattern)
        self.buttonSwitch.clicked.connect(_on_switch_panel)

    def switch_to_panelview(self):
        self.stack.setCurrentIndex(0)
        self.parent.setTitle(self.modes[0])
        self.buttonAll.setVisible(False)  

    def control_fetch(self):
        return self.pcontrol.get_states()

    def control_clear(self):
        self.pcontrol.clear()

    def view_update(self, data):
        self.pview.update_(data)

    def view_clear(self):
        self.pview.clear()

    def radiobox_locked(self, locked):
        self.radiobox.setEnabled(locked)
        if not locked:
            #self.radiobox.setToDefault()
            default_button = self.radiobox.group.buttons()[0]
            default_button.setChecked(True)
            self.radiobox.buttonClicked.emit(default_button)
        self.pattern = 150 * [self.states[2]]


class PanelBase(QWidget):
    ROW = 10
    COL = 5
    
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.items = []

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

    def createUI(self, wgt, **kwargs):
        row, col = (PanelBase.ROW, PanelBase.COL)
        for c in range(col):
            for r in range(row):
                name = f'{c * row + r + 1}:'
                edit = wgt(name=name, **kwargs)
                self.layout().addWidget(edit, r, c)
                self.items.append(edit)

    def clear(self):
        for item in self.items:
            item.clear()

    def rename(self, names):
        for item,name in zip(self.items, names):
            item.setName(name)


class PanelView(PanelBase):
    """ This class representing widget to show values of voltage/current in the channels """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.createUI(NamedEdit)

    def update_(self, data):
        for item, value in zip(self.items, data):
            txt = '{0:=6.2f}'.format(value/100)
            item.display(txt)


class PanelControl(PanelBase):
    """ The class representing widget to configure of voltage/current in the channels """

    def __init__(self, parent=None, states=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.states = states
        self.createUI(NamedSwitchButton, labels=self.states)

        # Connect signal/slot
        for item in self.items:
             item.clicked[int, str].connect(self._on_store_data)
    
    def _on_store_data(self, index, value):
        print(index, value)
        

    def update_(self, data):
        for item, value in zip(self.items, data):
            item.setText(value)

    def set_states(self, states):
        for item in self.items:
            item.switch_to(states)
        #print(list(self.get_states()))

    def get_states(self):
        return (item.text() for item in self.items)


class NamedWidget(QWidget):
    """ This base class for named widgets """

    def __init__(self, parent, name, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.label = label = QLabel(name)
        label.setFixedWidth(40)
        label.setAlignment(QtCore.Qt.AlignCenter)

    def setName(self, name):
        self.label.setText(name)


class NamedSwitchButton(NamedWidget):
    clicked = QtCore.pyqtSignal(int, str)

    def __init__(self, parent=None, name='Label', labels=None, *args, **kwargs):
        super().__init__(parent, name, *args, **kwargs)

        self.button = button = SwitchButton(labels=labels)
        button.setFixedWidth(40)
        button.setFixedHeight(20)
        layout = self.layout = QFormLayout(self)
        layout.setContentsMargins(2, 1, 1, 1)
        self.layout.addRow(self.label, self.button)

        self.button.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
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

        self.edit = edit = QLineEdit()
        edit.setReadOnly(True)
        edit.setText('-')
        edit.setAlignment(QtCore.Qt.AlignCenter)

        layout = self.layout = QFormLayout(self)
        layout.setContentsMargins(2, 1, 1, 1)
        self.layout.addRow(self.label, self.edit)

    def clear(self):
        self.edit.clear()
        self.edit.setText('-')

    def display(self, value):
        self.edit.setText(value)

    def value(self):
        return self.edit.text()


class SwitchButton(QPushButton):
    def __init__(self, parent=None, labels=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.labels = labels # [1,2,3,4]
        self.current = 0
        self.count = len(self.labels)
        self.setText(self.labels[self.current])

    def reset(self):
        self.current = 0
        self.setText(self.labels[self.current])

    def mousePressEvent(self, e):
        self.switch()
        super().mousePressEvent(e)

    def switch(self):
        if self.current < (self.count - 1):
            self.current += 1
        else:
            self.current = 0
        self.setText(self.labels[self.current])

    def switch_to(self, to):
        self.current = to
        self.setText(self.labels[self.current])


class RadioBox(QWidget):
    buttonClicked = QtCore.pyqtSignal(QAbstractButton)

    def __init__(self, title, group_names, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.group_names = group_names

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

        group.buttonClicked[QAbstractButton].connect(self.buttonClicked)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
