import json
import os.path
import sys
import logging

from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from panel import Panel

import proxy

__title__ = "Мониторинг последовательного канала КЭД КФ1/1М"
__version__ = "v0.1.0"
__author__ = "Александр Смирнов"

config = {
    "degaus": {
        "headers": ["CM2", "AMК/СМ2"],
        "channels": ["43", "121", "150"],
        "currents": ["10", "55"],
        "interval": ["1000"]
    }
}


class Ui(QMainWindow):
    def __init__(self):
        super().__init__()

        self.isBlink = False
        self.status = {}

        self.createUI()

    def _center(self):
        """ This method aligned main window related center screen """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def createUI(self):
        self.setWindowTitle("{0} (ver. {1})".format(__title__, __version__))
        self.setWindowIcon(QIcon(":/rc/logo.png"))
        self.setMaximumSize(600, 500)

        centralWgt = QWidget(self)
        self.setCentralWidget(centralWgt)
        self.createStatusbar()

        self.portbox = self.createPortbox()
        self.degausbox = self.createDegausBox()
        self.control = self.createButtons()

        gbox = QGroupBox()
        self.panel = Panel(gbox)

        # Layouts
        centralLayout = QVBoxLayout(centralWgt)

        settingsLayout = QHBoxLayout()
        settingsLayout.addWidget(self.portbox)
        settingsLayout.addWidget(self.degausbox, 2)
        centralLayout.addLayout(settingsLayout)

        centralLayout.addWidget(gbox)

        centralLayout.addWidget(self.control)

        self._center()
        self.show()

    def createButtons(self):
        wgt = QWidget()
        layout = QHBoxLayout(wgt)
        layout.setContentsMargins(0,10,0,0)

        self.buttons = {}
        for (name, key, enabled, icon) in (
                ('старт', 'start', True, ':/rc/red-start.png'),
                ('стоп', 'stop', False, ':/rc/red-stop.png'),
                ('сброс', 'reset', True, ':/rc/red-stop.png'),
                ('справка', 'about', True, ':/rc/red-about.png'),
                ('выход', 'exit', True, ':/rc/red-quit.png')
        ):
            self.buttons[key] = button = QPushButton(name.capitalize())
            button.setEnabled(enabled)
            button.setIcon(QIcon(icon))
            layout.addWidget(button)
        return wgt

    def createPortbox(self):
        """ Widget port settings"""
        wgt = QGroupBox('Настройки порта', self)
        layout = QGridLayout(wgt)
    
        # Input port
        port_input = QComboBox()
        port_input.setObjectName("port_input")

        # Output port
        port_output = QComboBox()
        port_output.setObjectName("port_output")

        # Button find available ports
        btnRescan = QPushButton("Обновить")

        layout.addWidget(QLabel('Порт АЦП:'), 0, 0)
        layout.addWidget(port_input, 0, 1)
        layout.addWidget(QLabel("Порт КЭД:"), 1, 0)
        layout.addWidget(port_output, 1, 1)
        layout.addWidget(btnRescan, 3, 1)

        # Slots
        def _on_change_port():
            self.ports_config = {
                "port_input": wgt.findChild(QComboBox, "port_input").currentText(),
                "port_output": wgt.findChild(QComboBox, "port_output").currentText()
            }

        def _on_find_ports():
            port_input.clear()
            port_output.clear()
            ports = proxy.scan()
            port_input.addItems(ports)
            port_output.addItems(ports)

            if len(ports) > 1:
                port_input.setEnabled(True)
                port_input.setCurrentIndex(0)
                port_output.setEnabled(True)
                port_output.setCurrentIndex(1)
            else:
                port_input.setDisabled(True)
                port_output.setDisabled(True)

        # Connect signal/slot
        port_input.currentTextChanged['QString'].connect(_on_change_port)
        port_output.currentTextChanged['QString'].connect(_on_change_port)
        btnRescan.clicked.connect(_on_find_ports)

        _on_find_ports()
        _on_change_port()

        return wgt

    def createDegausBox(self):
        """
        Widget degaus settings
        """
        wgt = QGroupBox('Настройки сообщения', self)
        layout = QGridLayout(wgt)

        self.degaus_config = {}

        def _update_data():
            self.degaus_config = {
              #  "header": wgt.findChild(QComboBox, 'header').currentText(),
                "channels": int(wgt.findChild(QComboBox, 'channels').currentText()),
                "channels_byte": bool(wgt.findChild(QCheckBox, 'channels_byte').checkState()),
                "imax": int(wgt.findChild(QComboBox, 'imax').currentText()),
                "imax_byte": bool(wgt.findChild(QCheckBox, 'imax_byte').checkState()),
                "interval": int(wgt.findChild(QComboBox, 'interval').currentText())
            }

        self.degausbox_widgets = {}
        row, col = (0, 0)
        for key, title, items in (
                ('header', 'Протокол', config['degaus']['headers']),
                ('channels', 'Число каналов', config['degaus']['channels']),
                ('imax', 'Макс. ток, А', config['degaus']['currents']),
                ('interval', 'Интервал, мс', config['degaus']['interval'])
        ):
            if key in "header":
                continue
            combo = QComboBox()
            combo.setObjectName(key)
            combo.setFixedWidth(65)
            combo.addItems(items)
            combo.setStyleSheet("text-align: right")

            # Signal/Slo
            combo.currentTextChanged['QString'].connect(_update_data)
            layout.addWidget(QLabel(title + ":"), row, 0)
            layout.addWidget(combo, row, 1)

            self.degausbox_widgets[key] = combo

            # If check byte include in header message
            if key in ['channels', 'imax']:
                check = QCheckBox("Доп. байт")
                check.setObjectName("{}_byte".format(key))
                if key == "channels":
                    check.setChecked(True)
                layout.addWidget(check, row, 2)
                check.stateChanged['int'].connect(_update_data)
                self.degausbox_widgets["{}_byte".format(key)] = check

            layout.setColumnStretch(2, 2)
            row += 1

        _update_data()

        return wgt

    def createStatusbar(self):
        pix = QLabel()
        self.statusBar().addPermanentWidget(pix)
        self.status['pixmap'] = pix
        self.updatePixmap('noconnect')

    def _lock(self, is_lock):
        self.portbox.setDisabled(is_lock)
        self.degausbox.setDisabled(is_lock)
        self.buttons['start'].setDisabled(is_lock)
        self.buttons['stop'].setEnabled(is_lock)

    def blinkPixmap(self):
        if self.isBlink:
            self.updatePixmap('tx')
            self.isBlink = False
        else:
            self.updatePixmap('rx')
            self.isBlink = True

    def updatePixmap(self, state=None):
        if not state:
            state = "noconnect"
        pixmaps = {
            'noconnect': {'ico': ":/rc/network-offline.png", 'description': 'нет подключения'},
            'idle': {'ico': ":/rc/network-idle.png", 'description': 'ожидание'},
            'rx': {'ico': ":/rc/network-receive.png", 'description': 'прием'},
            'tx': {'ico': ":/rc/network-transmit.png", 'description': 'передача'},
            'error': {'ico': ":/rc/network-error.png", 'description': 'ошибка'}
        }
        self.status['pixmap'].setPixmap(QPixmap(pixmaps[state]['ico']))
        self.status['pixmap'].setToolTip(pixmaps[state]['description'])

    def updateStatus(self, key, value):
        self.status[key].setText(' {}: {}'.format('отп', value))


class ProxyApp(Ui):
    def __init__(self):
        super(ProxyApp, self).__init__()

        self.timer_id = None

        # TODO: Widget disabled because there is no implementation
#        self.degausbox_widgets['header'].setDisabled(True)

        # Connect signal/slot
        self.buttons['start'].clicked.connect(self.on_start)
        self.buttons['stop'].clicked.connect(self.on_stop)
        self.buttons['reset'].clicked.connect(self.on_reset)
        self.buttons['exit'].clicked.connect(self.on_quit)

        self.degausbox_widgets['channels'].currentTextChanged['QString'].connect(self.on_change_channels)

    def closeEvent(self, event):
        self.on_quit()

    def timerEvent(self, event):
        self.on_run()

    def get_settings(self):
        config = dict(self.degaus_config)
        config.update(self.ports_config)
        return config

    def get_pattern(self):
        return list(self.panel.control_fetch())

    def on_change_channels(self, text: str):
        self.panel.control_clear()
        nChannels = int(text)

        if nChannels > 50:
            self.panel.visible_radiobox(True)
        else:
            self.panel.visible_radiobox(False)

    def on_run(self):
        """ """
        # Its Debug code
        time = QtCore.QTime()
        print("Event: ", time.currentTime().toString('hh:mm:ss:zz'))

        if proxy.QUEUE:
            data = proxy.QUEUE.popleft()
            self.panel.view_update(data)
            input_str = "Voltage: " + ",".join([str(i) for i in proxy.QUEUE_INPUT.popleft()])
            self.statusBar().showMessage(input_str)

        config = self.get_settings()
        pattern = self.get_pattern()
        proxy.run(pattern, config)

    def on_reset(self):
        self.panel.control_clear()

    def on_start(self):
        # if config['port_input'] == config['port_output']:
        #     self.statusBar().showMessage("Необходимо выбрать разные порты!", 2000)
        #     return

        self.panel.switch_to_panelview()
        self._lock(True)

        settings = self.get_settings()
        pattern = self.get_pattern()
        proxy.run(pattern, settings)

        self.timer_id = self.startTimer(settings['interval'], timerType=QtCore.Qt.PreciseTimer)

    def on_stop(self):
        self._lock(False)

        if self.timer_id:
            self.killTimer(self.timer_id)
            self.timer_id = 0

        self.panel.view_clear()
        self.statusBar().showMessage("Отключено", 2000)

    def on_quit(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
            self.timer_id = 0
        QtCore.QCoreApplication.exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Add icon in the taskbar (only windows))
    if sys.platform == 'win32':
        import ctypes

        myappid = u'navi-dals.kf1-m.proxy.001'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        app.setWindowIcon(QIcon(':/rc/Interdit.ico'))

    pui = ProxyApp()
    sys.exit(app.exec_())