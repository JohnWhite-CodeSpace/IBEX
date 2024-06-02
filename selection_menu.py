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
        self.extra_calculation_option = 0
        self.setFixedSize(QSize(380, 400))
        self.setWindowTitle("Select sorting options:")
        self.init_sub_ui()
        self.load_qt_stylesheet("Themes/dark_stylesheet.css")

    def load_qt_stylesheet(self, stylesheet):
        try:
            with open(stylesheet, 'r', encoding='utf-8') as file:
                style_str = file.read()
            self.setStyleSheet(style_str)
        except Exception as e:
            self.terminal.append(f"Failed to load stylesheet: {e}")

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

        bottom_layout = QHBoxLayout()
        confirm = QPushButton("Confirm")
        cancel = QPushButton("Cancel")
        bottom_layout.addWidget(confirm)
        bottom_layout.addWidget(cancel)

        confirm.clicked.connect(self.on_confirm)
        cancel.clicked.connect(self.close)

        main_layout.addLayout(middle_frame_layout)
        main_layout.addLayout(bottom_layout)

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

    def on_confirm(self):
        instruction = self.instruction_combobox.currentText()
        quaternion = self.quaternion_combobox.currentText()
        event = self.event_combobox.currentText()
        qualh = self.qualh_combobox.items()
        file_types = self.filetype_combobox.items()
        options = {
            'instruction': instruction,
            'quaternion': quaternion,
            'event': event,
            'qualh': qualh,
            'file_types': file_types
        }
        self.sorting_options_selected.emit(options)
        self.close()
