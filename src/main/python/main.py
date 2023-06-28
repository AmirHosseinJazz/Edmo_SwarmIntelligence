import copy
import glob
import os
import socket
import sys
import threading
import time
from datetime import datetime
from functools import partial
from os import path
from queue import Queue
from typing import List

import numpy as np
# Ensure that you install the pyserial package
import serial
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, QRect, QSize
from PyQt5.QtGui import QPalette, QPainter, QBrush, QColor, QFont, QMovie
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QLabel, QLineEdit, QSlider, QWidget, QGridLayout, QComboBox, \
    QPushButton, QFrame, QTextBrowser, QStyleOptionSlider, QStyle
from fbs_runtime.application_context.PyQt5 import ApplicationContext

import optimization
import stopThreading


class MySlider(QSlider):
    # disable the original mousePressEvent, avoid the jump of the number
    def mousePressEvent(self, event):
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        rect = self.style().subControlRect(
            QStyle.CC_Slider, option, QStyle.SC_SliderHandle, self)
        if rect.contains(event.pos()):
            # reserve the drag function
            super(MySlider, self).mousePressEvent(event)
            return


MAX_WIDTH = 80
MAX_HEIGHT = 80


class AmplitudeAnimation(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.width = MAX_WIDTH
        self.height = MAX_HEIGHT
        self.setFixedHeight(self.height)
        self.setFixedWidth(self.width)
        self.amplitude = 0
        self.t = 0

        self.rate = 4

    def paintEvent(self, event):
        self.t += 1
        qp = QPainter(self)
        br = QBrush(QColor(2, 5, 10, 50))
        qp.setBrush(br)
        xc = int(self.width * 0.5)
        yc = int(self.height * 0.5)
        qp.drawRect(QRect(30, yc + 2, 20, 37))

        qp.translate(xc, yc)
        qp.rotate(np.sin(self.t / self.rate) * self.amplitude)

        qp.drawRect(QRect(-10, -30, 20, 40))
        qp.resetTransform()


class OffsetAnimation(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.width = MAX_WIDTH
        self.height = MAX_HEIGHT
        self.setFixedHeight(self.height)
        self.setFixedWidth(self.width)
        self.offset = 0

    def paintEvent(self, event):
        qp = QPainter(self)
        br = QBrush(QColor(2, 5, 10, 50))
        qp.setBrush(br)
        xc = int(self.width * 0.5)
        yc = int(self.height * 0.5)
        qp.drawRect(QRect(30, yc + 2, 20, 37))

        qp.translate(xc, yc)
        qp.rotate(self.offset)

        qp.drawRect(QRect(-10, -30, 20, 40))
        qp.resetTransform()


class FrequencyAnimation(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.width = MAX_WIDTH
        self.height = MAX_HEIGHT
        self.setFixedHeight(self.height)
        self.setFixedWidth(self.width)
        self.rotation = 0
        self.amplitude = 0
        self.offset = 0

        self.rate = 2

    def paintEvent(self, event):
        qp = QPainter(self)
        br = QBrush(QColor(2, 5, 10, 50))
        qp.setBrush(br)
        xc = int(self.width * 0.5)
        yc = int(self.height * 0.5)
        qp.drawRect(QRect(30, yc + 2, 20, 37))

        qp.translate(xc, yc)
        qp.rotate(np.degrees(np.sin(self.rotation / self.rate)) * 1.5)

        qp.drawRect(QRect(-10, -30, 20, 40))
        qp.resetTransform()


class Structure:

    def __init__(self, n_modules=1, name=''):
        self.name = name
        self.frequency = 0
        self.weight = 0.025
        self.phase_bias_matrix = np.zeros([n_modules, n_modules])

        self.modules = []
        for i in range(n_modules):
            self.modules.append(Module())


class Module:

    def __init__(self, parameters=np.array([0, 0])):
        self.amplitude = parameters[0]
        self.offset = parameters[1]

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude

    def set_offset(self, offset):
        self.offset = offset


'''
class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, n=1, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(1, 1, 1)
        super(MplCanvas, self).__init__(fig)
'''


class ModelWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(ModelWindow, self).__init__(*args, **kwargs)
        self.model = 0
        self.label_font = QFont('Arial', 14)
        self.own_style = "background: #a1c5d6"
        self.setStyleSheet(self.own_style)
        self.button_style = "QPushButton { " \
                            " border: 2px solid #000000;" \
                            " border-radius: 22px;" \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #77b4d1, stop:1 #0091d6);" \
                            " min-width: 96px;" \
                            " min-height: 74px " \
                            " } " \
                            "QPushButton:pressed { " \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop: 0 #dadbde, stop: 1 #8cabba);" \
                            " } "
        self.setWindowTitle("Please choose the model of Interface")

        layout = QGridLayout()

        label = QLabel("Choose the model of Interface:")
        label.setFont(self.label_font)
        layout.addWidget(label, 0, 0)

        button_layout = QGridLayout()
        self.cooperation_button = QPushButton("Cooperation")
        self.cooperation_button.setFont(self.label_font)
        self.cooperation_button.setStyleSheet(self.button_style)
        self.cooperation_button.setEnabled(True)
        self.cooperation_button.pressed.connect(self.on_co_button_clicked)
        button_layout.addWidget(self.cooperation_button, 0, 0)

        self.single_button = QPushButton("Single")
        self.single_button.setFont(self.label_font)
        self.single_button.setStyleSheet(self.button_style)
        self.single_button.setEnabled(True)
        self.single_button.pressed.connect(self.on_single_button_clicked)
        button_layout.addWidget(self.single_button, 0, 1)

        button_layout.setEnabled(False)
        layout.addLayout(button_layout, 1, 0)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def on_co_button_clicked(self):
        self.model = 1
        self.close()

    def on_single_button_clicked(self):
        self.model = 2
        self.close()


class CooperationSettingWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(CooperationSettingWindow, self).__init__(*args, **kwargs)
        self.isMajor = False
        self.model = 0
        self.name = ''
        self.label_font = QFont('Arial', 14)
        self.own_style = "background: #a1c5d6"
        self.setStyleSheet(self.own_style)
        self.button_style = "QPushButton { " \
                            " border: 2px solid #000000;" \
                            " border-radius: 22px;" \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #77b4d1, stop:1 #0091d6);" \
                            " min-width: 96px;" \
                            " min-height: 74px " \
                            " } " \
                            "QPushButton:pressed { " \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop: 0 #dadbde, stop: 1 #8cabba);" \
                            " } "
        self.setWindowTitle("Please choose Major")

        layout = QGridLayout()

        label = QLabel("Please input your name:")
        label.setFont(self.label_font)
        layout.addWidget(label, 0, 0)

        name_box = QLineEdit()
        name_box.setFont(self.label_font)
        name_box.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        name_box.textEdited.connect(partial(self.edit_box_listener, name_box))
        layout.addWidget(name_box, 1, 0)
        label = QLabel("Are you the Major : ")
        label.setFont(self.label_font)
        layout.addWidget(label, 2, 0)

        button_layout = QGridLayout()
        self.major_button = QPushButton("1")
        self.major_button.setFont(self.label_font)
        self.major_button.setStyleSheet(self.button_style)
        self.major_button.setEnabled(False)
        self.major_button.pressed.connect(self.on_mj_button_clicked)
        button_layout.addWidget(self.major_button, 0, 0)

        self.vice_button = QPushButton("2")
        self.vice_button.setFont(self.label_font)
        self.vice_button.setStyleSheet(self.button_style)
        self.vice_button.setEnabled(False)
        self.vice_button.pressed.connect(self.on_vi_button_clicked)
        button_layout.addWidget(self.vice_button, 0, 1)

        button_layout.setEnabled(False)
        layout.addLayout(button_layout, 3, 0)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def on_mj_button_clicked(self):
        self.model = 1
        self.close()

    def on_vi_button_clicked(self):
        self.model = 2
        self.close()

    def edit_box_listener(self, box):
        if box.text():
            self.name = box.text()
            self.major_button.setEnabled(True)
            self.vice_button.setEnabled(True)


def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class ModulesWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super(ModulesWindow, self).__init__(*args, **kwargs)
        self.n = 1
        self.name = ''
        self.com_port = ''

        self.label_font = QFont('Arial', 14)
        self.own_style = "background: #a1c5d6"
        self.setStyleSheet(self.own_style)
        self.button_style = "QPushButton { " \
                            " border: 2px solid #000000;" \
                            " border-radius: 22px;" \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #77b4d1, stop:1 #0091d6);" \
                            " min-width: 96px;" \
                            " min-height: 74px " \
                            " } " \
                            "QPushButton:pressed { " \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop: 0 #dadbde, stop: 1 #8cabba);" \
                            " } "

        self.setWindowTitle("Welkom!")

        layout = QGridLayout()

        label = QLabel("Welkom bij de EDMO-interface.")
        label.setFont(self.label_font)
        layout.addWidget(label, 0, 0)

        label = QLabel("Voer uw naam in:")
        label.setFont(self.label_font)
        layout.addWidget(label, 1, 0)

        name_box = QLineEdit()
        name_box.setFont(self.label_font)
        name_box.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        name_box.textEdited.connect(partial(self.edit_box_listener, name_box))
        layout.addWidget(name_box, 2, 0)

        label = QLabel('Aantal EDMO Modules:')
        label.setFont(self.label_font)
        layout.addWidget(label, 3, 0)
        widget = QComboBox()
        widget.setFont(self.label_font)
        widget.addItems(["Een", "Twee", "Drie"])
        widget.currentIndexChanged.connect(self.index_changed)
        layout.addWidget(widget, 3, 1)

        label = QLabel('USB:')
        label.setFont(self.label_font)
        layout.addWidget(label, 4, 0)
        self.com_box = QComboBox()
        self.com_box.addItems(serial_ports())
        layout.addWidget(self.com_box, 4, 1)

        self.continue_button = QPushButton("Doorgaan")
        self.continue_button.setFont(self.label_font)
        self.continue_button.setStyleSheet(self.button_style)
        self.continue_button.setEnabled(False)
        self.continue_button.pressed.connect(self.on_button_clicked)
        layout.addWidget(self.continue_button, 4, 2)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def index_changed(self, i):  # i is an int
        self.n = i + 1

    def on_button_clicked(self):
        self.com_port = self.com_box.currentText()
        self.close()

    def edit_box_listener(self, box):
        if box.text():
            self.name = box.text()
            self.continue_button.setEnabled(True)


def encode(target, value, module=None, coupled_module=None):
    if module is None:
        msg = target + ' ' + str(value) + '\n'
    elif coupled_module is None:
        msg = target + ' ' + str(module) + ' ' + str(value) + '\n'
    else:
        msg = target + ' ' + str(module) + ' ' + str(coupled_module) + ' ' + str(value) + '\n'
    return msg.encode()


# List indexes for suggestions
# Not futureproof for more (or less) than 2 arms or modules with more (or less) features
FREQUENCY = 0
AMPLITUDE_0 = 1
OFFSET_0 = 2
PHASE = 3
AMPLITUDE_1 = 4
OFFSET_1 = 5
SLIDERS = ["Snelheid", "Omvang", "Positie", "Relatie", "Omvang", "Positie"]
NO_OF_SLIDERS = len(SLIDERS)
NEW_SLIDERS_PER_MODULE = 3

# Suggestion types
TEXT = 0
PICTURE = 1
GIF = 2
SUGGESTIONS = ["Text", "Picture", "GIF"]

# Slider layout constants
LABEL_ROW = 0
SUGGESTION_ROW = 1
SLIDER_ROW = 2
OFFSET_ROW_START = 3

CONNECTION_ROW = 0
SINGLE_SUGGESTION_ROW = 1
FREQUENCY_ROW = 2
MODULE_ROW = 3
PHASE_ROW = 4
EXPERIMENT_ROW = 5

# Resources
RESOURCE_ROOT_FOLDER = os.getcwd() + "\\src\\main\\python\\resources\\"
PIC_FOLDER = RESOURCE_ROOT_FOLDER + "pictures\\"
PIC_DIR = PIC_FOLDER + "arrow.png"
GIF_DIR = PIC_FOLDER + "arrow.gif"
GIF_INV_DIR = PIC_FOLDER + "arrow_inv.gif"
# File-saving
SAVE_FOLDER = RESOURCE_ROOT_FOLDER + "save\\"
OSCILLATOR_FOLDER = SAVE_FOLDER + "oscillator\\"
IMU_FILES_PREFIX = OSCILLATOR_FOLDER + "potentials"
ANGLES_FILES_PREFIX = OSCILLATOR_FOLDER + "angles"
POTENTIALS_FILES_PREFIX = OSCILLATOR_FOLDER + "imu"
PARAMETERS_FILES_PREFIX = SAVE_FOLDER + "parameters"
SAVE_FILES_SUFFIX = "modules.txt"

# Suggestion mode
SINGLE = 0
MULTI = 1
SUGGESTION_MODE = SINGLE
# This ensures that the suggestions
SUGGESTION_MODE_SCALING = 2 - SUGGESTION_MODE

# Transformation and scaling variables
PIC_SIZE_SCALE = 0.2 * SUGGESTION_MODE_SCALING
PIC_SCALE = QtGui.QTransform().scale(PIC_SIZE_SCALE, PIC_SIZE_SCALE)
Y_FLIP = QtGui.QTransform().scale(-1, 1)
GIF_SIZE_SCALE = MAX_WIDTH * SUGGESTION_MODE_SCALING
GIF_SCALE = QSize().scaled(GIF_SIZE_SCALE, GIF_SIZE_SCALE, Qt.KeepAspectRatio)

# Slider history
SLIDER_HISTORY = 4

# Default slider values
DEFAULT_SLIDER_VALUE = 0


def create_empty_slider_history() -> Queue:
    """
    Creates a queue of lists where the queue has the length of SLIDER_HISTORY
    and the inner lists have the same length as the number of sliders,
    where all elements have the value DEFAULT_SLIDER_VALUE
    :return: A queue of lists
    """
    slider_histories = Queue(maxsize=SLIDER_HISTORY)
    for _ in range(SLIDER_HISTORY):
        slider_vals = []
        for _, _ in enumerate(SLIDERS):
            slider_vals.append(DEFAULT_SLIDER_VALUE)
        slider_histories.put(slider_vals)
    return slider_histories


def clear_suggestion_widget(layout, old_widget, row=SUGGESTION_ROW, col=0):
    """
    Removes the given suggestion widget,
    and add a new empty suggestion widget with fixed height,
    so it does not mess with the UI.
    :param layout: The layout where the new widget is added to.
    :param old_widget: The widget that needs to be removed, this should usually be the given layout.
    :param row: The row the placeholder widget is added to in the given layout.
    SUGGESTION_ROW by default.
    :param col: The column the placeholder widget is added to in the given layout.
    0 by default.
    :return: None
    """
    # Create new empty widget
    placeholder = QWidget()
    placeholder.setFixedHeight(MAX_HEIGHT * SUGGESTION_MODE_SCALING)
    # Remove old widget
    old_widget.setParent(None)
    # Add empty widget back
    layout.addWidget(placeholder, row, col)
    return placeholder


def reformat_sliders_to_backend(slider_list: List[int]) -> List[int]:
    """
    The front-end has everything that has to do with the sliders in the order of
    frequency, amplitude module 1, offset module 1, phase, amplitude module 2, offset module 2
    The back-end has everything that has to do with the sliders in the order of
    frequency, amplitude module 1, offset module 1, amplitude module 2, offset module 2, phase
    I.e., the 'phase' slider is taken to be at the end of the sequence in the back-end
    instead of in between the modules.
    :param slider_list: A list in the order of
    frequency, amplitude module 1, offset module 1, phase, amplitude module 2, offset module 2
    :return: The same list, but in the order of
    frequency, amplitude module 1, offset module 1, amplitude module 2, offset module 2, phase
    """
    reformatted_list = slider_list.copy()
    phase = reformatted_list.pop(PHASE)
    reformatted_list.append(phase)
    return reformatted_list


def reformat_sliders_to_frontend(slider_list: List[int]) -> List[int]:
    """
    The front-end has everything that has to do with the sliders in the order of
    frequency, amplitude module 1, offset module 1, phase, amplitude module 2, offset module 2
    The back-end has everything that has to do with the sliders in the order of
    frequency, amplitude module 1, offset module 1, amplitude module 2, offset module 2, phase
    I.e., the 'phase' slider is taken to be at the end of the sequence in the back-end
    instead of in between the modules.
    :param slider_list: A list in the order of
    frequency, amplitude module 1, offset module 1, amplitude module 2, offset module 2, phase
    :return: The same list, but in the order of
    frequency, amplitude module 1, offset module 1, phase, amplitude module 2, offset module 2
    """
    reformatted_list = copy.deepcopy(slider_list)
    phase = reformatted_list.pop()
    reformatted_list.insert(PHASE, phase)
    return reformatted_list


class MainWindow(QMainWindow):
    def __init__(self, structure, port, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # Connection stuff
        self.port = port
        self.k = 0
        self.values = []
        self.baud_rate = 9600
        self.connect = False
        self.ser = None

        # Position and size
        self.x_data = 0
        self.y_data_potentials = []
        self.y_data_angles = []
        self.plot_window = 250

        self.fill_box_size = 50

        self.structure = structure
        self.n = len(self.structure.modules)

        # Slider boundaries
        self.amplitude_bounds = [0, 90]
        self.offset_bounds = [-90, 90]
        self.phase_bias_bounds = [-90, 90]
        self.frequency_bounds = [0.0, 1.0]
        self.frequency_scale = 100
        self.weight_bounds = [0.0, 1.0]

        # Colours
        self.default_palette = QPalette()
        self.default_palette.setColor(QPalette.Window, QColor('white'))
        self.error_palette = QPalette()
        self.error_palette.setColor(QPalette.Window, QColor('red'))
        self.error_palette.setColor(QPalette.Text, QColor('red'))
        self.condition_green_palette = QPalette()
        self.condition_green_palette.setColor(QPalette.Window, QColor('green'))
        self.condition_green_palette.setColor(QPalette.Text, QColor('green'))

        # Font
        self.title_font = QFont('Arial', 16)
        self.label_font = QFont('Arial', 14)

        # Styling
        self.own_style = "background: #a1c5d6"
        self.setStyleSheet(self.own_style)
        self.slider_style = "QSlider {" \
                            " min-height: 80px;" \
                            " max-height: 256px;" \
                            " min-width: 256px" \
                            " } " \
                            "QSlider::groove:horizontal { " \
                            " border: 1px solid #000000;" \
                            " height: 32px;" \
                            " background: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7cbbd9, stop:1 #82aec4);" \
                            " margin: 0 4px;" \
                            " border-radius: 4px;" \
                            " } " \
                            "QSlider::handle:horizontal { " \
                            " background: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #77b4d1, stop:1 #0091d6);" \
                            " border: 2px solid #000000;" \
                            " height: 44px;" \
                            " width: 64px;" \
                            " margin: -22px -4px;" \
                            " border-radius: 6px;" \
                            " } " \
                            " QSlider::handle:pressed { " \
                            "background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop: 0 #dadbde, stop: 1 #3e9fcf); " \
                            " } "
        self.button_style = "QPushButton { " \
                            " border: 2px solid #000000;" \
                            " border-radius: 22px;" \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #77b4d1, stop:1 #0091d6);" \
                            " min-width: 96px;" \
                            " min-height: 74px " \
                            " } " \
                            "QPushButton:pressed { " \
                            " background-color: " \
                            "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop: 0 #dadbde, stop: 1 #8cabba);" \
                            " } "
        self.frame_style = "QFrame {  border: 5px solid #00ff00; border-radius: 10px;}"
        self.clear_frame_style = "QFrame {  border: 0px solid #00ff00; border-radius: 10px;}"

        # Buttons and values
        self.buttons = []
        self.amplitudes = []
        self.offsets = []
        self.phase_biases = []

        # Used for making the suggestions
        self.layout_widget_lst = []

        # Sliders and labels
        self.sliders = []
        self.slider_values = [0] * len(SLIDERS)
        self.amplitude_dials = []
        self.offset_dials = []
        self.phase_bias_dials = []
        self.amplitude_labels = []
        self.offset_labels = []

        # Slider histories
        self.slider_history = create_empty_slider_history()

        # Images for sliders
        self.offset_images = []
        self.amplitude_images = []

        self.frames = []

        self.running = True

        # Saving
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H-%M-%S")
        try:
            if not path.exists(SAVE_FOLDER):
                os.mkdir(SAVE_FOLDER)
        except OSError:
            print('save directory failed')
        try:
            if not path.exists(OSCILLATOR_FOLDER):
                os.mkdir(OSCILLATOR_FOLDER)
        except OSError:
            print('save directory failed')

        self.potentials_save_file = '%s %s %s %s %s' \
                                    % (POTENTIALS_FILES_PREFIX,
                                       dt_string,
                                       self.structure.name,
                                       self.n,
                                       SAVE_FILES_SUFFIX)
        self.potentials_save_file = open(self.potentials_save_file, 'a')

        self.angles_save_file = '%s %s %s %s %s' \
                                % (ANGLES_FILES_PREFIX,
                                   dt_string,
                                   self.structure.name,
                                   self.n,
                                   SAVE_FILES_SUFFIX)
        self.angles_save_file = open(self.angles_save_file, 'a')

        self.imu_save_file = '%s %s %s %s %s' \
                             % (IMU_FILES_PREFIX,
                                dt_string,
                                self.structure.name,
                                self.n,
                                SAVE_FILES_SUFFIX)
        self.imu_save_file = open(self.imu_save_file, 'a')
        self.imu_save_file.write(
            str(['timestamp', 'Accelermeters', 'Gyroscope', 'Magnetometers', 'System', 'Theta', 'Phi', 'Psi']) + '\n')

        self.parameters_save_file = '%s %s %s %s %s' \
                                    % (PARAMETERS_FILES_PREFIX,
                                       dt_string,
                                       self.structure.name,
                                       self.n,
                                       SAVE_FILES_SUFFIX)
        self.parameters_save_file = open(self.parameters_save_file, 'w')
        self.parameters_save_file.write(str(['timestamp', 'frequency', 'amplitudes', 'offsets', 'phase_biases']) + '\n')

        self.setWindowTitle("EDMO Interface")

        # More connecting
        self.general_layout = QGridLayout()
        self.error_label = QLineEdit()
        self.error_label.setReadOnly(True)
        self.error_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.error_label.setPalette(self.error_palette)
        self.serial_connect_button = QPushButton('Koppelen')
        self.serial_connect_button.setStyleSheet(self.button_style)
        self.serial_connect_button.setFont(self.label_font)
        self.serial_connect_button.pressed.connect(self.attempt_serial_connect)
        self.serial_connect_button.setEnabled(True)
        self.general_layout.addWidget(self.error_label, CONNECTION_ROW, 0)
        self.general_layout.addWidget(self.serial_connect_button, CONNECTION_ROW, 1)
        self.com_box = QComboBox()
        self.com_box.addItems(serial_ports())
        self.general_layout.addWidget(self.com_box, CONNECTION_ROW, 2)

        # Suggestion setup
        # Image and GIF loading
        self.pixmap = QtGui.QPixmap(PIC_DIR)
        self.gif = QMovie(GIF_DIR)
        self.gif_inv = QMovie(GIF_INV_DIR)
        # Create the suggestion list with no real suggestions
        # so switching can be performed without any given suggestions.
        self._suggestions = [0] * NO_OF_SLIDERS
        self.single_suggestion_widget = self.add_default_single_suggestion_widget()

        # Frequency bits
        frequency_layout = QGridLayout()
        freq_frame = QFrame()
        freq_frame.setLineWidth(0)
        freq_frame.setFrameStyle(QFrame.Panel)

        # Label
        frequency_label = QLabel("Snelheid:")
        frequency_label.setFont(self.label_font)
        frequency_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        frequency_layout.addWidget(frequency_label, LABEL_ROW, 1)

        self.add_default_multi_suggestion_widget(frequency_layout)

        # Image
        self.frequency_image = FrequencyAnimation()
        frequency_layout.addWidget(self.frequency_image, SLIDER_ROW, 0)

        # Slider
        self.frequency_slider = MySlider(Qt.Horizontal)
        self.frequency_slider.setMinimum(int(self.frequency_bounds[0] * self.frequency_scale))
        self.frequency_slider.setMaximum(int(self.frequency_bounds[1] * self.frequency_scale))
        self.frequency_slider.setValue(DEFAULT_SLIDER_VALUE)
        self.frequency_slider.setStyleSheet(self.slider_style)
        self.frequency_slider.valueChanged.connect(partial(self.frequency_slider_listener, self.frequency_slider))
        self.frequency_slider.sliderReleased.connect(partial(self.slider_released))
        frequency_layout.addWidget(self.frequency_slider, SLIDER_ROW, 1)
        self.sliders.append(self.frequency_slider)

        # Completing the frequecy UI element
        self.frequency_box = QLineEdit()
        self.frequency_box.setFont(self.label_font)
        self.frequency_box.setMaxLength(5)
        self.frequency_box.setFixedWidth(self.fill_box_size)
        self.frequency_box.setPlaceholderText(str(0.0))
        self.frequency_box.setReadOnly(True)

        frequency_layout.addWidget(self.frequency_box, 1, 2)

        freq_frame.setLayout(frequency_layout)
        self.frames.append(freq_frame)
        self.general_layout.addWidget(freq_frame, FREQUENCY_ROW, 0)

        module_layout = QGridLayout()
        phase_bias_layout = QGridLayout()

        # For each module, creating the UI-elements for amplitude and offset.
        # They all have the same structure as frequency
        for i in range(self.n):
            # Add 1 to the module number to make it more natural
            module_label = QLabel("Module %i" % (i + 1))
            module_label.setFont(self.title_font)
            module_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            module_layout.addWidget(module_label, 0, i)

            module_frame = QFrame()
            module_frame.setLineWidth(2)
            module_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
            slider_layout = QGridLayout()

            amplitude_layout = QGridLayout()
            amp_frame = QFrame()
            amp_frame.setLineWidth(0)
            amp_frame.setFrameStyle(QFrame.Panel)

            amplitude_label = QLabel("Omvang:")
            amplitude_label.setFont(self.label_font)
            amplitude_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.amplitude_labels.append(amplitude_label)
            amplitude_layout.addWidget(amplitude_label, LABEL_ROW, 1)

            self.add_default_multi_suggestion_widget(amplitude_layout)

            amplitude_image = AmplitudeAnimation()
            self.amplitude_images.append(amplitude_image)
            amplitude_layout.addWidget(amplitude_image, SLIDER_ROW, 0)

            amplitude_dial = MySlider(Qt.Horizontal)
            amplitude_dial.setFixedWidth(200)
            amplitude_dial.setMinimum(self.amplitude_bounds[0])
            amplitude_dial.setMaximum(self.amplitude_bounds[1])
            amplitude_dial.setValue(DEFAULT_SLIDER_VALUE)
            amplitude_dial.setStyleSheet(self.slider_style)
            amplitude_dial.valueChanged.connect(partial(self.dial_listener, amplitude_dial))
            amplitude_dial.sliderReleased.connect(partial(self.slider_released))
            self.amplitude_dials.append(amplitude_dial)
            amplitude_layout.addWidget(amplitude_dial, SLIDER_ROW, 1)
            self.sliders.append(amplitude_dial)

            amplitude_box = QLineEdit()
            amplitude_box.setFont(self.label_font)
            amplitude_box.setMaxLength(3)
            amplitude_box.setFixedWidth(self.fill_box_size)
            amplitude_box.setReadOnly(True)
            amplitude_box.setPlaceholderText(str(0.0))
            self.amplitudes.append(amplitude_box)
            amplitude_layout.addWidget(amplitude_box, SLIDER_ROW, 2)

            amp_frame.setLayout(amplitude_layout)
            self.frames.append(amp_frame)
            slider_layout.addWidget(amp_frame, 0, 0)

            offset_layout = QGridLayout()
            os_frame = QFrame()
            os_frame.setLineWidth(0)
            os_frame.setFrameStyle(QFrame.Panel)

            offset_label = QLabel("Positie:")
            offset_label.setFont(self.label_font)
            offset_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            self.offset_labels.append(offset_label)
            offset_layout.addWidget(offset_label, LABEL_ROW, 1)

            self.add_default_multi_suggestion_widget(offset_layout)

            offset_image = OffsetAnimation()
            self.offset_images.append(offset_image)
            offset_layout.addWidget(offset_image, SLIDER_ROW, 0)

            offset_dial = MySlider(Qt.Horizontal)
            offset_dial.setFixedWidth(200)
            offset_dial.setMinimum(self.offset_bounds[0])
            offset_dial.setMaximum(self.offset_bounds[1])
            offset_dial.setValue(DEFAULT_SLIDER_VALUE)
            offset_dial.setStyleSheet(self.slider_style)
            offset_dial.valueChanged.connect(partial(self.dial_listener, offset_dial))
            offset_dial.sliderReleased.connect(partial(self.slider_released))
            self.offset_dials.append(offset_dial)
            offset_layout.addWidget(offset_dial, SLIDER_ROW, 1)
            self.sliders.append(offset_dial)

            offset_box = QLineEdit()
            offset_box.setFont(self.label_font)
            offset_box.setMaxLength(3)
            offset_box.setFixedWidth(self.fill_box_size)
            offset_box.setReadOnly(True)
            offset_box.setPlaceholderText(str(0.0))
            self.offsets.append(offset_box)
            offset_layout.addWidget(offset_box, SLIDER_ROW, 2)

            os_frame.setLayout(offset_layout)
            self.frames.append(os_frame)
            slider_layout.addWidget(os_frame, 1, 0)

            module_frame.setLayout(slider_layout)

            # Do the same for the phase, but one less per module.
            # Since you do not want the phase between the first and last one
            if i < self.n - 1:
                phase_frame = QFrame()
                phase_frame.setLineWidth(0)
                phase_frame.setFrameStyle(QFrame.Panel)

                phase_bias_label = QLabel("Relatie:")
                phase_bias_label.setFont(self.label_font)
                phase_bias_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                phase_bias_layout.addWidget(phase_bias_label, LABEL_ROW, i)

                self.add_default_multi_suggestion_widget(phase_bias_layout, col=i)

                phase_bias_slider = MySlider(Qt.Horizontal)
                phase_bias_slider.setFixedWidth(200)
                phase_bias_slider.setMinimum(self.offset_bounds[0])
                phase_bias_slider.setMaximum(self.offset_bounds[1])
                phase_bias_slider.setValue(DEFAULT_SLIDER_VALUE)
                phase_bias_slider.setStyleSheet(self.slider_style)
                phase_bias_slider.valueChanged.connect(partial(self.phase_bias_slider_listener, phase_bias_slider))
                phase_bias_slider.sliderReleased.connect(partial(self.slider_released))
                self.phase_bias_dials.append(phase_bias_slider)
                phase_bias_layout.addWidget(phase_bias_slider, SLIDER_ROW, i)
                self.sliders.append(phase_bias_slider)

                bias_box = QLineEdit()
                bias_box.setFont(self.label_font)
                bias_box.setMaxLength(3)
                bias_box.setFixedWidth(self.fill_box_size)
                bias_box.setReadOnly(True)
                bias_box.setPlaceholderText(str(0.0))
                self.phase_biases.append(bias_box)
                phase_bias_layout.addWidget(bias_box, SLIDER_ROW + 1, i)

                self.frames.append(phase_frame)
                phase_frame.setLayout(phase_bias_layout)
                self.general_layout.addWidget(phase_frame, PHASE_ROW, 0)

            module_layout.addWidget(module_frame, 3, i)
            # canvas = MplCanvas(self, n=self.n, width=5, height=4, dpi=50)
            # self.canvases.append(canvas)
            # module_layout.addWidget(canvas, 4, i)

        self.general_layout.addLayout(module_layout, MODULE_ROW, 0)

        # Experimentation buttons
        # Start stop button
        self.start_stop_button = QPushButton("Stop")
        self.start_stop_button.setStyleSheet(self.button_style)
        self.start_stop_button.setFont(self.label_font)
        self.start_stop_button.pressed.connect(self.start_button_listener)
        self.general_layout.addWidget(self.start_stop_button, PHASE_ROW, 1)

        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(self.button_style)
        self.reset_button.setFont(self.label_font)
        self.reset_button.pressed.connect(self.reset_default_values)
        self.general_layout.addWidget(self.reset_button, PHASE_ROW, 2)

        # Suggestion dropdown
        self.suggestion_type = TEXT
        suggestion_type_layout = QGridLayout()
        suggestion_label = QLabel("Suggestion\ntype")
        suggestion_label.setFont(self.label_font)
        suggestion_type_layout.addWidget(suggestion_label, 0, 0)
        widget = QComboBox()
        widget.setFont(self.label_font)
        widget.addItems(SUGGESTIONS)
        widget.currentIndexChanged.connect(self.suggestion_button_listener)
        suggestion_type_layout.addWidget(widget, 1, 0)
        self.general_layout.addLayout(suggestion_type_layout, EXPERIMENT_ROW, 1)

        # Close button
        self.close_button = QPushButton("Sluiten")
        self.close_button.setStyleSheet(self.button_style)
        self.close_button.setFont(self.label_font)
        self.close_button.pressed.connect(self.close_listener)
        self.general_layout.addWidget(self.close_button, EXPERIMENT_ROW, 2)

        self.attempt_serial_connect()

        widget = QWidget()
        widget.setLayout(self.general_layout)
        self.setCentralWidget(widget)

        # All the timers
        self.timer1 = QTimer()
        self.timer1.setInterval(50)
        self.timer1.timeout.connect(self.animate)
        self.timer1.start()

        self.timer2 = QTimer()
        self.timer2.setInterval(2000)
        self.timer2.timeout.connect(self.check_serial_state)
        self.timer2.start()

        self.timer3 = QTimer()
        self.timer3.setInterval(25)
        self.timer3.timeout.connect(self.poti_read)
        self.timer3.start()

        # self.timer4 = QTimer()
        # self.timer4.setInterval(100)
        # self.timer4.timeout.connect(self.update_plot)
        # self.timer4.start()

    def get_slider_history(self) -> Queue:
        """
        Finds the history of all the sliders
        :return: A queue of lists of integers.
        Each queue is the values of all sliders when any slider is moved, the length of which is SLIDER_HISTORY.
        Each list item is a slider and is in the order of
        frequency, amplitude 0, offset 0, phase, amplitude 1, offset 1.
        The creation of the slider history can be seen in create_empty_slider_history
        """
        return self.slider_history

    def format_slider_history(self) -> List[List[int]]:
        """
        The back-end requires the slider history to be in a different format.
        This method performs the conversion to that format.
        :return: A list of lists. The outer list (1st dimension) is of length SLIDER_HISTORY.
        The inner list (2nd dimension) has the same length as the number of sliders,
        in this particular scope that is 6, and will always be 6 in this scope.
        For future use, this should be changed dynamically if a different number of sliders is used,
        because a different number of modules or modules with more sliders are used.
        The order of sliders of the 2nd dimension is
        frequency, amplitude module 1, offset module 1, amplitude module 2, offset module 2, phase
        See also: reformat_sliders
        """
        formatted_slider_history = []
        q_list = list(self.slider_history.queue)
        for slider_vals in q_list:
            reformatted_slider_vals = reformat_sliders_to_backend(slider_vals)
            formatted_slider_history.append(reformatted_slider_vals)
        return formatted_slider_history

    def start_button_listener(self):
        if self.running:
            if self.ser is not None:
                self.send_command(encode('freq', 0.0, module=None))
                self.start_stop_button.setText("Start")
                self.running = False
                self.parameters_save_file.write('STOP' + '\n')
        else:
            if self.ser is not None:
                self.start_stop_button.setText("Stop")
                self.running = True
                self.send_message()

    def suggestion_button_listener(self, i: int):
        # Switch the suggestion type
        self.suggestion_type = i
        # Makes the suggestions switch
        self.give_suggestion(self._suggestions)

    def give_suggestion(self, suggestion_lst):
        """
        Gives the suggestion to the user, using the corresponding SUGGESTION_MODE.
        Check the give_suggestion_single, and give_suggestion_multi methods for more info
        :param suggestion_lst: List of integers where each value should either be -1, 0 or 1.
        If it's -1, then the suggestion will be to decrease the slider of the corresponding index,
        if it's 1, then it the suggestion will be to increase that slider.
        If it's any other integer (preferably 0), then it will not do anything.
        The order should be: frequency, amplitude 0, offset 0, phase, amplitude 1, offset 1
        :return: None
        """
        # Used for suggestion switching
        self._suggestions = suggestion_lst
        self.remove_all_suggestions_and_highlights()
        if SUGGESTION_MODE == SINGLE:
            self.give_suggestion_single(suggestion_lst)
        elif SUGGESTION_MODE == MULTI:
            self.give_suggestion_multi(suggestion_lst)

    def give_suggestion_single(self, suggestion_lst):
        """
        Gives the suggestion for the corresponding slider using the selected suggestion type (self.suggestion_type).
        Only one suggestion should be given.
        :param suggestion_lst: List of integers where each value should either be -1, 0 or 1.
        If it's -1, then the suggestion will be to decrease the slider of the corresponding index,
        if it's 1, then it the suggestion will be to increase that slider.
        If it's any other integer (preferably 0), then it will not do anything.
        The order should be: frequency, amplitude 0, offset 0, phase, amplitude 1, offset 1
        :return: None
        """
        layout = self.general_layout
        new_widget = QWidget()
        for idx, suggestion in enumerate(suggestion_lst):
            new_widget = self.give_suggestion_helper(suggestion, idx)
            if suggestion in [-1, 1]:
                self.frames[idx].setStyleSheet(self.frame_style)
                # Stop loop if a suggestion is given
                break
        # Replace the old widget
        self.single_suggestion_widget = new_widget
        layout.addWidget(new_widget, SINGLE_SUGGESTION_ROW, 0)
        layout.update()

    def give_suggestion_multi(self, suggestion_lst):
        """
        Gives the suggestion for the corresponding slider using the selected suggestion type (self.suggestion_type).
        Multiple suggestions can be given
        :param suggestion_lst: List of integers where each value should either be -1, 0 or 1.
        If it's -1, then the suggestion will be to decrease the slider of the corresponding index,
        if it's 1, then it the suggestion will be to increase that slider.
        If it's any other integer (preferably 0), then it will not do anything.
        The order should be: frequency, amplitude 0, offset 0, phase, amplitude 1, offset 1
        :return: None
        """
        for idx, suggestion in enumerate(suggestion_lst):
            layout = self.layout_widget_lst[idx][0]
            # Positioning
            col = 1
            if idx == PHASE:
                col = 0
            new_widget = self.give_suggestion_helper(suggestion, idx)
            # Replace the old widget
            layout.addWidget(new_widget, SUGGESTION_ROW, col)
            layout.update()
            self.layout_widget_lst[idx][1] = new_widget

    def give_suggestion_helper(self, suggestion, slider_idx):
        """
        Removes the old widget from its layout and creates a new widget according to the suggestion type.
        :param suggestion: The suggestion direction for this slider
        :param slider_idx: The index of the slider that we want to  make a suggestion for.
        :return: The new widget
        """
        # Default widget so something will be returned
        new_widget = QLabel()
        # Center alignment, because it's prettier
        new_widget.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        # Fixing height so no weird UI switching happens
        new_widget.setFixedHeight(MAX_HEIGHT * SUGGESTION_MODE_SCALING)

        # Only create the widget if there's a suggestion
        if suggestion in [-1, 1]:
            # Suggestion using text
            if self.suggestion_type == TEXT:
                direction = ""
                if suggestion == -1:
                    direction = "Verlaag"
                elif suggestion == 1:
                    direction = "Verhoog"
                slider_name = SLIDERS[slider_idx]
                module_name = " "
                # If the slider index is amplitude or offset
                if slider_idx % 3 in [1, 2]:
                    module_name += "Module "
                    module_name += str(int(np.floor(slider_idx / 3)))
                label_text = direction + " " + slider_name + module_name
                new_widget.setText(label_text)
                new_widget.setFont(self.label_font)
            # Suggestion using a simple static arrow
            elif self.suggestion_type == PICTURE:
                pixmap = self.pixmap.copy()
                pixmap = pixmap.transformed(PIC_SCALE)
                if suggestion == -1:
                    pixmap = pixmap.transformed(Y_FLIP)
                new_widget.setPixmap(pixmap)
            # Suggestion using an animated arrow
            elif self.suggestion_type == GIF:
                gif = self.gif
                if suggestion == -1:
                    gif = self.gif_inv
                gif.setScaledSize(GIF_SCALE)
                new_widget.setMovie(gif)
                gif.start()
        return new_widget

    '''
    def update_plot(self):
        if len(self.y_data_potentials) > 0:
            # Drop off the first y element, append a new one.
            for i in range(self.n):
                self.canvases[i].axes.cla()  # Clear the canvas.
                self.canvases[i].axes.set_ylim([-120, 120])

                potentials_to_plot = np.array(self.y_data_potentials)[-self.plot_window:, i]
                angles_to_plot = np.array(self.y_data_angles)[-self.plot_window:, i]
                domain = np.arange(potentials_to_plot.shape[0])

                self.canvases[i].axes.plot(domain, potentials_to_plot, 'b', linewidth=0.25)
                self.canvases[i].axes.plot(domain, angles_to_plot, 'r', linewidth=0.25)
                # Trigger the canvas to update and redraw.
                self.canvases[i].draw()
    '''

    def check_serial_state(self):
        if self.ser is not None:
            try:
                if not self.running:
                    self.send_command(encode('freq', 0.0, module=None))
                else:
                    self.send_command(encode('freq', self.structure.frequency, module=None))
            except serial.SerialException:
                self.error_label.setText("Geen USB Verbinding")
                self.error_label.setPalette(self.error_palette)
                self.serial_connect_button.setEnabled(True)
                self.start_stop_button.setEnabled(False)
                self.start_stop_button.setText("Start")
                self.running = False
                self.connect = False
        else:
            self.com_box.clear()
            self.com_box.addItems(serial_ports())

    def attempt_serial_connect(self):
        self.port = self.com_box.currentText()
        msgbox = QMessageBox()
        msgbox.setWindowTitle('USB-verbinding tot stand brengen')
        msgbox.setText('Zorg ervoor dat de Micro Controller is aangesloten op de computer')
        msgbox.addButton(QPushButton('Opnieuw'), QMessageBox.YesRole)
        cancel = QPushButton('Sluiten')
        cancel.pressed.connect(self.cancel_listener)
        msgbox.addButton(cancel, QMessageBox.NoRole)
        while not self.connect:
            try:
                self.ser = serial.Serial(self.port, self.baud_rate)
                self.connect = True
                msgbox.close()
                self.serial_connect_button.setEnabled(False)
            except serial.SerialException:
                self.error_label.setText('Wachten op USB-verbinding')
                msgbox.exec_()

        if self.ser is None:
            self.error_label.setText("Geen USB-verbinding")
            self.error_label.setPalette(self.error_palette)
            self.serial_connect_button.setEnabled(True)
            self.start_stop_button.setEnabled(False)
        else:
            self.error_label.setText('Verbonden met Micro Controller')
            self.error_label.setPalette(self.condition_green_palette)
            self.serial_connect_button.setEnabled(False)
            self.start_stop_button.setEnabled(True)

    def reset_default_values(self):
        self.structure.frequency = 0.0
        self.structure.weight = 0.025

        self.frequency_box.setText(str(0.0))
        self.frequency_slider.setValue(int(0.0 * self.frequency_scale))

        for i in range(self.n):
            self.structure.modules[i].amplitude = 0.0
            self.structure.modules[i].offset = 0.0

            self.amplitudes[i].setText(str(0))
            self.amplitudes[i].setPalette(self.default_palette)
            self.offsets[i].setText(str(0))
            self.offsets[i].setPalette(self.default_palette)
            self.amplitude_dials[i].setValue(DEFAULT_SLIDER_VALUE)
            self.offset_dials[i].setValue(DEFAULT_SLIDER_VALUE)

            self.amplitude_images[i].amplitude = 0.0
            self.offset_images[i].offset = 0.0
            self.offset_images[i].update()

        self.structure.phase_bias_matrix = np.zeros([self.n, self.n])
        for i in range(self.n - 1):
            self.phase_biases[i].setText(str(0))
            self.phase_bias_dials[i].setValue(DEFAULT_SLIDER_VALUE)

        self.start_stop_button.setText("Stop")
        self.running = True
        self.timer2.start()

        if self.ser is not None and self.connect:
            self.send_message()

    def frequency_slider_listener(self, slider):
        v = slider.value() / self.frequency_scale
        self.update_slider_value(slider, v)
        self.structure.frequency = v
        self.frequency_box.setText(str(v))
        self.frequency_box.setPalette(self.default_palette)
        if self.running and self.ser is not None:
            self.send_command(encode('freq', self.structure.frequency, module=None))
            self.save_parameters()

    def phase_bias_slider_listener(self, slider):
        v = slider.value()
        self.update_slider_value(slider, v)
        i = self.phase_bias_dials.index(slider)
        self.structure.phase_bias_matrix[i, i + 1] = v
        self.structure.phase_bias_matrix[i + 1, i] = -v
        self.phase_biases[i].setText(str(v))
        self.phase_biases[i].setPalette(self.default_palette)
        if self.running and self.ser is not None:
            self.send_command(encode('phb', self.structure.phase_bias_matrix[i, i + 1],
                                     module=i, coupled_module=i + 1))
            self.save_parameters()

    def dial_listener(self, dial):
        v = dial.value()
        self.update_slider_value(dial, v)
        if dial in self.amplitude_dials:
            i = self.amplitude_dials.index(dial)
            self.amplitude_images[i].amplitude = v
            self.structure.modules[i].set_amplitude(v)
            self.amplitudes[i].setText(str(v))
            self.amplitudes[i].setPalette(self.default_palette)
            if self.running and self.ser is not None:
                self.send_command(encode('amp', self.structure.modules[i].amplitude, module=i))
                self.save_parameters()
        elif dial in self.offset_dials:
            i = self.offset_dials.index(dial)
            self.offset_images[i].offset = v
            self.offset_images[i].update()
            self.structure.modules[i].set_offset(v)
            self.offsets[i].setText(str(v))
            self.offsets[i].setPalette(self.default_palette)
            if self.running and self.ser is not None:
                self.send_command(encode('off', self.structure.modules[i].offset + 90, module=i))
                self.save_parameters()

    def poti_read(self):
        if self.ser is not None:
            try:
                while self.ser.in_waiting > 0:
                    line = self.ser.readline()
                    numbers = line.strip().decode('ASCII').split(', ')
                    vals = np.zeros([self.n, 2])
                    now = datetime.now()
                    timestamp = now.strftime('%H:%M:%S.%f')[:-3]
                    params = [str(timestamp), numbers[3], numbers[4], numbers[5], numbers[6], numbers[7],
                              numbers[8], numbers[9]]
                    self.imu_save_file.write(str(params) + '\n')
                    for j in range(self.n):
                        t = [float(k) for k in numbers[j].split(' ')]
                        t[1] -= 90
                        vals[j, :] = t
                    if self.running:
                        self.x_data += 1
                        self.y_data_potentials.append(vals[:, 0])
                        self.y_data_angles.append(vals[:, 1])

                        self.potentials_save_file.write(str([str(timestamp), str(vals[:, 0])]) + '\n')
                        self.angles_save_file.write(str([str(timestamp), str(vals[:, 1])]) + '\n')
            except (KeyboardInterrupt, ValueError, UnicodeDecodeError, serial.SerialException) as e:
                if e is serial.SerialException:
                    self.timer3.stop()

    def send_message(self):
        if self.running:
            try:
                self.send_command(encode('freq', self.structure.frequency, module=None))

                for i in range(self.n):
                    self.send_command(encode('amp', self.structure.modules[i].amplitude, module=i))
                    self.send_command(encode('off', self.structure.modules[i].offset + 90, module=i))

                    if i < self.n - 1:
                        self.send_command(encode('phb', self.structure.phase_bias_matrix[i, i + 1],
                                                 module=i, coupled_module=i + 1))
            except serial.SerialException:
                print('Error Sending Serial Message')
            self.save_parameters()

    def cancel_listener(self):
        self.connect = True

    def close_listener(self):
        if self.ser is not None and self.connect:
            self.reset_default_values()
            self.send_message()
            self.ser.flush()
            self.ser.close()
        self.angles_save_file.close()
        self.potentials_save_file.close()
        self.parameters_save_file.close()
        self.close()
        self.destroy()

    def print_structure_parameters(self):
        print('Frequency:', self.structure.frequency)
        print('Weight:', self.structure.weight)
        for i in range(self.n):
            print('-------------------------------')
            print('Module %i Amplitude' % i, self.structure.modules[i].amplitude)
            print('Module %i Offset' % i, self.structure.modules[i].offset)
        print('-------------------------------')
        print('Phase Bias Matrix:')
        print(self.structure.phase_bias_matrix)

    def filter_values(self):
        if self.structure.frequency < self.frequency_bounds[0] or self.structure.frequency > self.frequency_bounds[1]:
            print('Frequency Range Error')

        if self.structure.weight < self.weight_bounds[0] or self.structure.weight > self.weight_bounds[1]:
            print('Weight Range Error')

        for i in range(self.n):
            current = self.structure.modules[i]
            if current.amplitude < self.amplitude_bounds[0] or current.amplitude > self.amplitude_bounds[1]:
                print('Module %i Amplitude Range Error' % i)
            if current.offset < self.offset_bounds[0] or current.offset > self.offset_bounds[1]:
                print('Module %i Offset Range Error' % i)

            for j in range(self.n):
                if self.structure.phase_bias_matrix[i, j] < self.phase_bias_bounds[0] or \
                        self.structure.phase_bias_matrix[i, j] > self.phase_bias_bounds[1]:
                    print('Modules %i and %i Phase Bias Range Error' % (i, j))

    def save_parameters(self):
        now = datetime.now()
        timestamp = now.strftime('%H:%M:%S.%f')[:-3]
        amplitudes = []
        offsets = []
        phase_biases = []

        for i in range(self.n):
            amplitudes.append(self.structure.modules[i].amplitude)
            offsets.append(self.structure.modules[i].offset)
            if i < self.n - 1:
                phase_biases.append(self.structure.phase_bias_matrix[i, i + 1])

        params = [str(timestamp), str(self.structure.frequency), str(amplitudes), str(offsets), str(phase_biases)]
        self.parameters_save_file.write(str(params) + '\n')

    def send_command(self, msg):
        self.ser.write(msg)

    def animate(self, dt=0.01):
        self.frequency_image.rotation += self.structure.frequency
        for i in range(self.n):
            self.amplitude_images[i].t += dt
            self.amplitude_images[i].update()
        self.frequency_image.update()

    def add_default_single_suggestion_widget(self):
        """
        Creates a default suggestion widget and adds it to the general layout.
        Should only be used for single-suggestion mode.
        But there's a fail-save if you accidentally do
        :return: The default widget
        """
        placeholder = QWidget()
        if SUGGESTION_MODE == SINGLE:
            placeholder.setFixedHeight(MAX_HEIGHT * SUGGESTION_MODE_SCALING)
            self.general_layout.addWidget(placeholder, SINGLE_SUGGESTION_ROW, 0)
        return placeholder

    def add_default_multi_suggestion_widget(self, layout, row_start=0, col=1):
        """
        Creates a default suggestion widget and adds it to the given layout.
        Should only be used for multi-suggestion mode.
        But there's a fail-save if you accidentally do
        :param layout: The layout the widget needs to be added to
        :param row_start: The widget is always placed on SUGGESTION_ROW.
        If the slider it needs to be added to does not start at 0 in the given layout,
        it can be increased using this parameter.
        0 by default.
        :param col: The column it is added to in the layout
        :return: None
        """
        if SUGGESTION_MODE == MULTI:
            placeholder = QWidget()
            placeholder.setFixedHeight(MAX_HEIGHT * SUGGESTION_MODE_SCALING)
            self.layout_widget_lst.append([layout, placeholder])
            layout.addWidget(placeholder, row_start + SUGGESTION_ROW, col)

    def slider_released(self) -> None:
        """
        Removes all suggestions and highlights according to remove_suggestion_and_highlight.
        Updates the slider histories according to update_slider_history.
        Gets the suggestion from optimization.suggestion.
        Feeds this suggestion to give_suggestion
        :return: None
        """
        self.remove_all_suggestions_and_highlights()
        self.update_slider_history()
        formatted_slider_hist = self.format_slider_history()
        suggestion = optimization.suggestion(formatted_slider_hist)
        reformatted_suggestion = reformat_sliders_to_frontend(suggestion)
        self.give_suggestion(reformatted_suggestion)

    def remove_all_suggestions_and_highlights(self):
        """
        Removes the suggestions and highlights, but keeps the size of the widget.
        See clear_suggestion_widget for more details.
        :return: None
        """
        # Create new empty widget
        placeholder = QWidget()
        placeholder.setFixedHeight(MAX_HEIGHT * SUGGESTION_MODE_SCALING)
        if SUGGESTION_MODE == SINGLE:
            layout = self.general_layout
            old_widget = self.single_suggestion_widget
            clear_suggestion_widget(layout, old_widget, SINGLE_SUGGESTION_ROW)
        for slider_idx, frame in enumerate(self.frames):
            # Clear the highlight for all frames
            frame.setStyleSheet(self.clear_frame_style)
            if SUGGESTION_MODE == MULTI:
                layout = self.layout_widget_lst[slider_idx][0]
                old_widget = self.layout_widget_lst[slider_idx][1]
                # Positioning
                col = 1
                if slider_idx == PHASE:
                    col = 0
                placeholder_widget = clear_suggestion_widget(layout, old_widget, col=col)
                self.layout_widget_lst[slider_idx][1] = placeholder_widget

    def update_slider_history(self):
        """
        Dequeues and enqueues the slider values in the slider history.
        Should only be called when the slider is released.
        :return: None
        """
        # dequeue
        self.slider_history.get()
        # enqueue
        self.slider_history.put(self.slider_values)

    def update_slider_value(self, slider: MySlider, val: int) -> None:
        """
        Updates the slider values for the given slider with the given value
        :param slider: The slider
        :param val: The value
        :return: None
        """
        idx = self.sliders.index(slider)
        self.slider_values[idx] = val


class CoMainWindow(MainWindow):
    signal_write_msg = QtCore.pyqtSignal(str)

    def __init__(self, structure, port, *args, **kwargs):
        super(CoMainWindow, self).__init__(structure, port, *args, **kwargs)
        self.tcp_socket = None
        self.sever_th = None
        self.client_th = None
        self.client_socket_list = list()
        self.link = False

        self.setWindowTitle("EDMO Cooperation Mode Major")
        self.amplitude_dials[1].setEnabled(False)
        self.offset_dials[1].setEnabled(False)
        self.amplitude_labels[1].setStyleSheet("color:grey")
        self.offset_labels[1].setStyleSheet("color:grey")
        self.local_ip_label = QLabel("Local IP: ")
        self.local_ip_label.setFont(self.label_font)
        self.local_ip_lineEdit = QLineEdit()
        self.port_label = QLabel("Port: ")
        self.port_label.setFont(self.label_font)
        self.port_lineEdit = QLineEdit()
        self.target_ip_label = QLabel("Target IP: ")
        self.target_ip_label.setFont(self.label_font)
        self.target_ip_label.setStyleSheet("color:grey")
        self.target_ip_lineEdit = QLineEdit()
        self.tcp_connect_pushButton = QPushButton("Connect")
        self.tcp_connect_pushButton.setFont(self.label_font)
        self.tcp_connect_pushButton.setStyleSheet(self.button_style)
        self.tcp_disconnect_pushButton = QPushButton("Disconnect")
        self.tcp_disconnect_pushButton.setFont(self.label_font)
        self.tcp_disconnect_pushButton.setStyleSheet(self.button_style)
        self.textBrowser_recv = QTextBrowser()

        tcp_module_layout = QGridLayout()
        tcp_module_layout.addWidget(self.local_ip_label, 0, 0)
        tcp_module_layout.addWidget(self.local_ip_lineEdit, 1, 0, 1, 2)
        tcp_module_layout.addWidget(self.port_label, 2, 0)
        tcp_module_layout.addWidget(self.port_lineEdit, 3, 0, 1, 2)
        tcp_module_layout.addWidget(self.target_ip_label, 4, 0)
        tcp_module_layout.addWidget(self.target_ip_lineEdit, 5, 0, 1, 2)
        tcp_module_layout.addWidget(self.tcp_connect_pushButton, 6, 0)
        tcp_module_layout.addWidget(self.tcp_disconnect_pushButton, 6, 1)

        self.general_layout.addWidget(self.textBrowser_recv, 1, 1, 1, 2)
        self.general_layout.addLayout(tcp_module_layout, 2, 1, 1, 2)

        self.initial_set(False)
        self.tcp_reset()
        self.click_get_ip()
        self.function_connect()

    def function_connect(self):
        self.signal_write_msg.connect(self.write_msg)
        self.tcp_connect_pushButton.pressed.connect(self.click_link)
        self.tcp_disconnect_pushButton.pressed.connect(self.click_unlink)

        self.frequency_slider.sliderReleased.connect(partial(self.real_time_reaction, self.frequency_slider))
        self.amplitude_dials[0].sliderReleased.connect(partial(self.real_time_reaction, self.amplitude_dials[0]))
        self.offset_dials[0].sliderReleased.connect(partial(self.real_time_reaction, self.offset_dials[0]))
        self.phase_bias_dials[0].sliderReleased.connect(partial(self.real_time_reaction, self.phase_bias_dials[0]))

    def initial_set(self, state):
        self.frequency_slider.setEnabled(state)
        self.amplitude_dials[0].setEnabled(state)
        self.offset_dials[0].setEnabled(state)
        self.phase_bias_dials[0].setEnabled(state)

    def write_msg(self, msg):
        # signal_write_msg will activate this function
        """
        write the msg into text browser
        :return: None
        """
        self.textBrowser_recv.insertPlainText(msg)
        self.textBrowser_recv.moveCursor(QtGui.QTextCursor.End)

    def tcp_server_start(self):
        """
        tcp server start function
        :return: None
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.setblocking(False)
        try:
            port = int(self.port_lineEdit.text())
            self.tcp_socket.bind(('', port))
        except Exception:
            msg = 'please check out the port!\n'
            self.signal_write_msg.emit(msg)
        else:
            self.tcp_socket.listen()
            self.sever_th = threading.Thread(target=self.tcp_server_concurrency)
            self.sever_th.start()
            msg = 'TCP server are listening to:%s\n' % str(port)
            self.signal_write_msg.emit(msg)

    def tcp_server_concurrency(self):
        """
        thread function
        :return:None
        """
        while True:
            try:
                client_socket, client_address = self.tcp_socket.accept()
            except Exception:
                time.sleep(0.001)
            else:
                client_socket.setblocking(False)
                self.client_socket_list.append((client_socket, client_address))
                msg = 'TCP server already connect to IP:%sPort:%s\n' % client_address
                self.signal_write_msg.emit(msg)
            for client, address in self.client_socket_list:
                try:
                    recv_msg = client.recv(1024)
                    recv_msg = recv_msg.decode('utf-8')
                    mark = int(recv_msg[0])
                except Exception:
                    pass
                else:
                    scale = 1
                    slider = self.frequency_slider
                    if mark == 1:
                        scale = self.frequency_scale
                    elif mark == 4:
                        slider = self.amplitude_dials[1]
                    elif mark == 5:
                        slider = self.offset_dials[1]
                    elif mark == 6:
                        slider = self.phase_bias_dials[0]

                    if recv_msg:
                        msg = float(recv_msg[1:]) * scale
                        slider.setValue(msg)
                        msg = 'from IP:{} Port:{}:\n{}\n'.format(address[0], address[1], msg)
                        self.signal_write_msg.emit(msg)
                    else:
                        client.close()
                        self.client_socket_list.remove((client, address))

    def click_get_ip(self):
        """
        pushbutton_get_ip function
        :return: None
        """
        self.local_ip_lineEdit.clear()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            my_addr = s.getsockname()[0]
            self.local_ip_lineEdit.setText(str(my_addr))
        except Exception:
            try:
                my_addr = socket.gethostbyname(socket.gethostname())
                self.local_ip_lineEdit.setText(str(my_addr))
            except Exception:
                self.signal_write_msg.emit("can't get the IP, pls check the internet!\n")
        finally:
            s.close()

    def tcp_send(self, send_msg):
        """
        function for send message
        :return: None
        """
        if self.link is False:
            msg = 'please check the connection first!\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                for client, address in self.client_socket_list:
                    client.send(send_msg)
                msg = 'TCP server already sent\n'
                self.signal_write_msg.emit(msg)
            except Exception:
                msg = 'Send message failed!\n'
                self.signal_write_msg.emit(msg)

    def tcp_close(self):
        try:
            for client, address in self.client_socket_list:
                client.close()
            self.tcp_socket.close()
            if self.link is True:
                msg = 'TCP disconnect!\n'
                self.signal_write_msg.emit(msg)
        except Exception:
            pass

        try:
            stopThreading.stop_thread(self.sever_th)
        except Exception:
            pass
        try:
            stopThreading.stop_thread(self.client_th)
        except Exception:
            pass

    def click_link(self):
        self.tcp_server_start()
        self.link = True
        self.initial_set(True)
        self.tcp_connect_pushButton.setEnabled(False)
        self.tcp_disconnect_pushButton.setEnabled(True)

    def click_unlink(self):
        self.close_all()
        self.link = False
        self.initial_set(False)
        self.tcp_connect_pushButton.setEnabled(True)
        self.tcp_disconnect_pushButton.setEnabled(False)

    def close_all(self):
        self.tcp_close()
        self.tcp_reset()

    def tcp_reset(self):
        self.link = False
        self.client_socket_list = list()
        self.tcp_connect_pushButton.setEnabled(True)
        self.tcp_disconnect_pushButton.setEnabled(False)
        self.target_ip_label.setEnabled(False)
        self.target_ip_lineEdit.setReadOnly(True)

    def real_time_reaction(self, slider):
        scale = 1
        pre_str = str(1)
        if slider == self.frequency_slider:
            scale = self.frequency_scale
        if slider == self.amplitude_dials[0]:
            pre_str = str(2)
            scale = 1
        if slider == self.offset_dials[0]:
            pre_str = str(3)
            scale = 1
        if slider == self.phase_bias_dials[0]:
            pre_str = str(6)
            scale = 1

        v = slider.value() / scale
        if not self.tcp_socket:
            msg = "please check out the TCP connection first!\n"
            self.signal_write_msg(msg)
        else:
            v = (pre_str + str(v)).encode('utf-8')
            self.tcp_send(v)


class CoViceWindow(MainWindow):
    signal_write_msg = QtCore.pyqtSignal(str)

    def __init__(self, structure, port, *args, **kwargs):
        super(CoViceWindow, self).__init__(structure, port, *args, **kwargs)
        self.tcp_socket = None
        self.sever_th = None
        self.client_th = None
        self.client_socket_list = list()
        self.link = False

        self.setWindowTitle("EDMO Cooperation Mode Vice")
        self.amplitude_dials[0].setEnabled(False)
        self.offset_dials[0].setEnabled(False)
        self.amplitude_labels[0].setStyleSheet("color:grey")
        self.offset_labels[0].setStyleSheet("color:grey")
        self.local_ip_label = QLabel("Local IP: ")
        self.local_ip_label.setFont(self.label_font)
        self.local_ip_lineEdit = QLineEdit()
        self.port_label = QLabel("Port: ")
        self.port_label.setFont(self.label_font)
        self.port_lineEdit = QLineEdit()
        self.target_ip_label = QLabel("Target IP: ")
        self.target_ip_label.setFont(self.label_font)
        self.target_ip_lineEdit = QLineEdit()
        self.tcp_connect_pushButton = QPushButton("Connect")
        self.tcp_connect_pushButton.setFont(self.label_font)
        self.tcp_connect_pushButton.setStyleSheet(self.button_style)
        self.tcp_disconnect_pushButton = QPushButton("Disconnect")
        self.tcp_disconnect_pushButton.setFont(self.label_font)
        self.tcp_disconnect_pushButton.setStyleSheet(self.button_style)
        self.textBrowser_recv = QTextBrowser()

        tcp_module_layout = QGridLayout()
        tcp_module_layout.addWidget(self.local_ip_label, 0, 0)
        tcp_module_layout.addWidget(self.local_ip_lineEdit, 1, 0, 1, 2)
        tcp_module_layout.addWidget(self.port_label, 2, 0)
        tcp_module_layout.addWidget(self.port_lineEdit, 3, 0, 1, 2)
        tcp_module_layout.addWidget(self.target_ip_label, 4, 0)
        tcp_module_layout.addWidget(self.target_ip_lineEdit, 5, 0, 1, 2)
        tcp_module_layout.addWidget(self.tcp_connect_pushButton, 6, 0)
        tcp_module_layout.addWidget(self.tcp_disconnect_pushButton, 6, 1)

        self.general_layout.addWidget(self.textBrowser_recv, 1, 1, 1, 2)
        self.general_layout.addLayout(tcp_module_layout, 2, 1, 1, 2)

        self.initial_set(False)
        self.tcp_reset()
        self.click_get_ip()
        self.function_connect()

    def function_connect(self):
        self.signal_write_msg.connect(self.write_msg)
        self.tcp_connect_pushButton.pressed.connect(self.click_link)
        self.tcp_disconnect_pushButton.pressed.connect(self.click_unlink)

        self.frequency_slider.sliderReleased.connect(partial(self.real_time_reaction, self.frequency_slider))
        self.amplitude_dials[1].sliderReleased.connect(partial(self.real_time_reaction, self.amplitude_dials[1]))
        self.offset_dials[1].sliderReleased.connect(partial(self.real_time_reaction, self.offset_dials[1]))
        self.phase_bias_dials[0].sliderReleased.connect(partial(self.real_time_reaction, self.phase_bias_dials[0]))

    def initial_set(self, state):
        self.frequency_slider.setEnabled(state)
        self.amplitude_dials[1].setEnabled(state)
        self.offset_dials[1].setEnabled(state)
        self.phase_bias_dials[0].setEnabled(state)

    def write_msg(self, msg):
        # signal_write_msg will activate this function
        """
        write the msg into text browser
        :return: None
        """
        self.textBrowser_recv.insertPlainText(msg)
        self.textBrowser_recv.moveCursor(QtGui.QTextCursor.End)

    def tcp_client_start(self):
        """
        TCP client to server
        :return:
        """
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            address = (str(self.target_ip_lineEdit.text()), int(self.port_lineEdit.text()))
        except Exception:
            msg = 'please check the target IP and Port\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                msg = 'connecting to the server\n'
                self.signal_write_msg.emit(msg)
                self.tcp_socket.connect(address)
            except Exception:
                msg = 'can not connect to the server\n'
                self.signal_write_msg.emit(msg)
            else:
                self.client_th = threading.Thread(target=self.tcp_client_concurrency, args=(address,))
                self.client_th.start()
                msg = 'TCP client already connet to IP:%sPort:%s\n' % address
                self.signal_write_msg.emit(msg)

    def tcp_client_concurrency(self, address):
        """
        for TCP client get message
        :return:
        """
        while True:
            recv_msg = self.tcp_socket.recv(1024)
            recv_msg = recv_msg.decode('utf-8')
            mark = int(recv_msg[0])
            scale = 1
            slider = self.frequency_slider
            if mark == 1:
                scale = self.frequency_scale
            elif mark == 2:
                slider = self.amplitude_dials[0]
            elif mark == 3:
                slider = self.offset_dials[0]
            elif mark == 6:
                slider = self.phase_bias_dials[0]

            if recv_msg:
                msg = float(recv_msg[1:]) * scale
                slider.setValue(msg)
                msg = 'from IP:{}Port:{}:\n{}\n'.format(address[0], address[1], msg)
                self.signal_write_msg.emit(msg)
            else:
                self.tcp_socket.close()
                self.reset()
                msg = 'disconnect from the server!\n'
                self.signal_write_msg.emit(msg)
                break

    def tcp_send(self, send_msg):
        """
        function for send message
        :return: None
        """
        if self.link is False:
            msg = 'please check the connection first!\n'
            self.signal_write_msg.emit(msg)
        else:
            try:
                self.tcp_socket.send(send_msg)
                msg = 'TCP client sent!\n'
                self.signal_write_msg.emit(msg)
            except Exception:
                msg = 'Send message failed!\n'
                self.signal_write_msg(msg)

    def click_get_ip(self):
        """
        pushbutton_get_ip function
        :return: None
        """
        self.local_ip_lineEdit.clear()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            my_addr = s.getsockname()[0]
            self.local_ip_lineEdit.setText(str(my_addr))
        except Exception:
            try:
                my_addr = socket.gethostbyname(socket.gethostname())
                self.local_ip_lineEdit.setText(str(my_addr))
            except Exception:
                self.signal_write_msg.emit("can't get the IP, pls check the internet!\n")
        finally:
            s.close()

    def tcp_close(self):
        try:
            self.tcp_socket.close()
            if self.link is True:
                msg = 'Disconnect!\n'
                self.signal_write_msg.emit(msg)
        except Exception:
            pass

        try:
            stopThreading.stop_thread(self.sever_th)
        except Exception:
            pass
        try:
            stopThreading.stop_thread(self.client_th)
        except Exception:
            pass

    def click_link(self):
        self.tcp_client_start()
        self.link = True
        self.initial_set(True)
        self.tcp_connect_pushButton.setEnabled(False)
        self.tcp_disconnect_pushButton.setEnabled(True)

    def click_unlink(self):
        self.close_all()
        self.link = False
        self.initial_set(False)
        self.tcp_connect_pushButton.setEnabled(True)
        self.tcp_disconnect_pushButton.setEnabled(False)

    def close_all(self):
        self.tcp_close()
        self.tcp_reset()

    def tcp_reset(self):
        self.link = False
        self.client_socket_list = list()
        self.tcp_connect_pushButton.setEnabled(True)
        self.tcp_disconnect_pushButton.setEnabled(False)

    def real_time_reaction(self, slider):
        scale = 1
        pre_str = str(1)
        if slider == self.frequency_slider:
            scale = self.frequency_scale
        if slider == self.amplitude_dials[1]:
            pre_str = str(4)
            scale = 1
        if slider == self.offset_dials[1]:
            pre_str = str(5)
            scale = 1
        if slider == self.phase_bias_dials[0]:
            pre_str = str(6)
            scale = 1

        v = slider.value() / scale
        if not self.tcp_socket:
            msg = "please check out the TCP connection first!\n"
            self.signal_write_msg(msg)
        else:
            v = (pre_str + str(v)).encode('utf-8')
            self.tcp_send(v)


if __name__ == '__main__':

    app_init = ApplicationContext()
    app_init.app.setStyle("Fusion")
    window = ModelWindow()
    window.show()
    app_init.app.exec_()

    # Single
    if window.model == 2:
        app_init = ApplicationContext()
        app_init.app.setStyle("Fusion")
        window = ModulesWindow()
        window.show()
        app_init.app.exec_()

        structure = Structure(n_modules=window.n, name=window.name)

        app_init = ApplicationContext()
        app_init.app.setStyle("Fusion")
        window = MainWindow(structure, window.com_port)
        window.show()
        sys.exit(app_init.app.exec_())

    # Coop
    elif window.model == 1:
        app_init = ApplicationContext()
        app_init.app.setStyle("Fusion")
        window = CooperationSettingWindow()
        window.show()
        app_init.app.exec_()

        structure = Structure(n_modules=2, name=window.name)
        if window.model == 1:
            app_init = ApplicationContext()
            app_init.app.setStyle("Fusion")
            window = CoMainWindow(structure, '')
            window.show()
            sys.exit(app_init.app.exec_())
        elif window.model == 2:
            app_init = ApplicationContext()
            app_init.app.setStyle("Fusion")
            window = CoViceWindow(structure, '')
            window.show()
            sys.exit(app_init.app.exec_())
