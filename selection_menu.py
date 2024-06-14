from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QMainWindow, QFrame
)

class CheckableComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view().pressed.connect(self.handle_item_pressed)
        self.setModel(QtGui.QStandardItemModel(self))
        self._changed = False

    def addItem(self, text, data=None):
        item = QtGui.QStandardItem(text)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        item.setData(QtCore.Qt.Unchecked, Qt.CheckStateRole)
        if data is not None:
            item.setData(data)
        self.model().appendRow(item)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self._changed = True

    def hidePopup(self):
        if self._changed:
            self._changed = False
        else:
            super().hidePopup()

    def items(self):
        items = []
        for index in range(self.model().rowCount()):
            item = self.model().item(index)
            if item.checkState() == Qt.Checked:
                items.append(item.text())
        return items


class SelectionFrame(QMainWindow):
    sorting_options_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.condition = None
        self.quaternion_file_type = [".attdba", ".attd2a"]
        self.instruction = ["HiCullGoodTimes.txt", "LoGoodTimes.txt"]
        self.QualH_num = ["Q-ABC", "Q-AB", "Q-BC", "Q-AC", "None"]
        self.event_types = ['Direct events', 'Histogram events']
        self.file_types = ["hide", "lode", "hihb", "lohb"]
        self.setFixedSize(QSize(380, 500))  # Adjusted size to accommodate new elements
        self.setWindowTitle("Select sorting options:")
        self.init_sub_ui()
        self.load_qt_stylesheet("Themes/dark_stylesheet.css")

    def load_qt_stylesheet(self, stylesheet):
        try:
            with open(stylesheet, 'r', encoding='utf-8') as file:
                style_str = file.read()
            self.setStyleSheet(style_str)
        except Exception as e:
            print(f"Failed to load stylesheet: {e}")

    def init_sub_ui(self):
        frame = QFrame()
        main_layout = QVBoxLayout(frame)

        middle_frame_layout = QHBoxLayout()
        selection_layout = QVBoxLayout()
        display_layout = QVBoxLayout()
        middle_frame_layout.addLayout(selection_layout)
        middle_frame_layout.addLayout(display_layout)

        self.instruction_combobox = self.add_combobox(selection_layout, "Instruction File", self.instruction)
        self.quaternion_combobox = self.add_combobox(selection_layout, "Quaternion File Type", self.quaternion_file_type)
        self.event_combobox = self.add_combobox(selection_layout, "Event types", self.event_types)
        self.qualh_combobox = self.add_checkable_combobox(selection_layout, "QualH", self.QualH_num)
        self.filetype_combobox = self.add_checkable_combobox(selection_layout, "File Types", self.file_types)

        self.channels_combobox = CheckableComboBox()
        self.particle_events_combobox = CheckableComboBox()

        selection_layout.addWidget(QLabel("Channels"))
        selection_layout.addWidget(self.channels_combobox)
        selection_layout.addWidget(QLabel("Particle Events"))
        selection_layout.addWidget(self.particle_events_combobox)

        bottom_layout = QHBoxLayout()
        confirm = QPushButton("Confirm")
        cancel = QPushButton("Cancel")
        bottom_layout.addWidget(confirm)
        bottom_layout.addWidget(cancel)

        confirm.clicked.connect(self.on_confirm)
        cancel.clicked.connect(self.close)

        main_layout.addLayout(middle_frame_layout)
        main_layout.addLayout(bottom_layout)
        self.instruction_combobox.currentTextChanged.connect(self.update_additional_comboboxes)
        self.setCentralWidget(frame)

    def add_combobox(self, layout, label_text, options):
        label = QLabel(label_text)
        combobox = QComboBox()
        for option in options:
            combobox.addItem(option)
        layout.addWidget(label)
        layout.addWidget(combobox)
        return combobox

    def add_checkable_combobox(self, layout, label_text, options):
        label = QLabel(label_text)
        combobox = CheckableComboBox()
        combobox.addItems(options)
        layout.addWidget(label)
        layout.addWidget(combobox)
        return combobox

    def update_additional_comboboxes(self):
        instruction = self.instruction_combobox.currentText()
        self.channels_combobox.clear()
        self.particle_events_combobox.clear()
        self.qualh_combobox.clear()

        if instruction == "HiCullGoodTimes.txt":
            self.channels_combobox.addItems([f"Channel {i}" for i in range(1, 7)])
            self.channels_combobox.addItem("All")
            self.particle_events_combobox.addItem("All")
            self.qualh_combobox.addItems(["Q-ABC", "Q-AB", "Q-BC", "Q-AC"])
        elif instruction == "LoGoodTimes.txt":
            self.channels_combobox.addItems([f"Channel {i}" for i in range(1, 9)])
            self.channels_combobox.addItem("All")
            self.particle_events_combobox.addItems(["Hydrogen", "Oxygen"])
            self.qualh_combobox.addItems([f"TOF{i}" for i in range(0, 4)])
        else:
            return
    def on_confirm(self):
        instruction = self.instruction_combobox.currentText()
        quaternion = self.quaternion_combobox.currentText()
        event = self.event_combobox.currentText()
        qualh = self.qualh_combobox.items()
        file_types = self.filetype_combobox.items()
        channels = self.channels_combobox.items()
        particle_events = self.particle_events_combobox.items()
        options = {
            'instruction': instruction,
            'quaternion': quaternion,
            'event': event,
            'qualh': qualh,
            'file_types': file_types,
            'channels': channels,
            'particle_events': particle_events
        }
        self.sorting_options_selected.emit(options)
        self.close()
