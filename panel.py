import sys

import collections

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class PanelManager:
    def __init__(self, parent=None, *args, **kwargs):
        print("Create PanelManager:", parent, args, kwargs)
        self.parent = parent
        self.modes = ["Амперметры", "Настройки"]
        self.states = ["Max", 'Min', 'Null', 'L']
        
        self.n_channels = kwargs['n_channels']
        
        self.createUi()

    def createUi(self):
        
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
                labels = (str(i) for i in range(1,51))
            elif group == "II":
                labels = (str(i) for i in range(51,101))
            elif group == "III":
                labels = (str(i) for i in range(101,151))
            else:
                raise ValueError("Dont find group name")
            current = self.stack.currentWidget()
            current.rename(labels)

        def _on_switch_all_buttons():
            label = self.buttonAll.text()
            data = [label for i in range(self.n_channels)]
            self.pcontrol.setModel(data)
            #index = self.states.index(label)
            #self.pcontrol.set_states(index)

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
        self.pview = PanelView()

        data = [self.states[2] for i in range(self.n_channels)]
        self.pcontrol = PanelControl(data=data)
        
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
        self.data = []

    def createUI(self, wgt, **kwargs):
        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

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
    """ 
    This class representing widget to show values 
    of voltage/current in the channels 
    """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.createUI(NamedEdit)

    def update_(self, data):
        for item, value in zip(self.items, data):
            txt = '{0:=6.2f}'.format(value/100)
            item.display(txt)


class PanelControl(PanelBase):
    """ The class representing widget to configure of voltage/current in the channels """

    def __init__(self, parent=None, data=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.data = data

        self.createUI(NamedSwitchButton)

        # Connect signal/slot
        for item in self.items:
             item.clicked[int, str].connect(self._on_store_data)

        # If send data then update view
        if self.data:
            self.update_()

    def _on_store_data(self, index, value):
        if index <= len(self.data):
            self.data[index] = value

    def set_data(self, data):
        self.data = data
        self.update_()
    
    def set_states(self, data):
        self.set_data(data)

    def get_states(self):
        print(".get_states: ", len(self.data), self.data)
        return self.data

    def update_(self):
        for item, value in zip(self.items, self.data):
            item.setText(value)



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
        self.labels = labels  or ["Max", 'Min', 'Null', 'L']
        self.createUi()

    def createUi(self):
        self.button = button = SwitchButton(labels=self.labels)
        button.setFixedWidth(40)
        button.setFixedHeight(20)
        layout =  QFormLayout(self)
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
    def __init__(self, parent=None, labels=None, *args, **kwargs):
        super().__init__(text='new', *args, **kwargs)
        self.labels = labels or ["Max", 'Min', 'Null', 'L']
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
