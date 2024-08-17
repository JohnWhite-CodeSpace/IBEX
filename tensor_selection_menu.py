from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, QMainWindow, QFrame
)


class TensorSelectionFrame(QMainWindow):
    tensor_options_selected = pyqtSignal(dict)

    def __init__(self, stylesheet):
        super().__init__()
        self.stylesheet = stylesheet
        self.quaternion_file = [".attdba", ".attd2a"]
        self.instruction_file = ["HiCullGoodTimes.txt", "LoGoodTimes.txt"]
        self.file_types = ["hide", "lode", "hihb", "lohb"]
        self.structure_attribute = ["Every half year", "Every year", "All at once"]
        self.remove_hex_flags = ["Translate to int", "Replace with '0'"]
        self.setFixedSize(QSize(300, 380))
        self.setWindowTitle("Select tensor options:")
        self.init_sub_ui()
        self.load_qt_stylesheet(self.stylesheet)

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

        self.instruction_combobox = self.add_combobox(selection_layout, "Instruction File", self.instruction_file)
        self.quaternion_combobox = self.add_combobox(selection_layout, "Quaternion File Type",
                                                     self.quaternion_file)
        self.filetype_combobox = self.add_combobox(selection_layout, "File types", self.file_types)
        self.timespan_combobox = self.add_combobox(selection_layout, "Timespan attribute",
                                                   self.structure_attribute)
        self.hex_combobox = self.add_combobox(selection_layout, "Hex flags", self.remove_hex_flags)

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
        self.update_additional_comboboxes()

    def add_combobox(self, layout, label_text, options):
        label = QLabel(label_text)
        combobox = QComboBox()
        for option in options:
            combobox.addItem(option)
        layout.addWidget(label)
        layout.addWidget(combobox)
        return combobox

    def update_additional_comboboxes(self):
        instruction = self.instruction_combobox.currentText()
        self.filetype_combobox.clear()
        if instruction == "HiCullGoodTimes.txt":
            self.filetype_combobox.addItems(["hide", "hihb"])
        elif instruction == "LoGoodTimes.txt":
            self.filetype_combobox.addItems(["lode", "lohb"])
        else:
            return

    def on_confirm(self):
        instruction = self.instruction_combobox.currentText()
        quaternion = self.quaternion_combobox.currentText()
        file_type = self.filetype_combobox.currentText()
        timespan = self.timespan_combobox.currentText()
        hex = self.hex_combobox.currentText()
        options = {
            'instruction': instruction,
            'quaternion': quaternion,
            'file_type': file_type,
            'timespan': timespan,
            'hex': hex,
        }
        self.tensor_options_selected.emit(options)
        self.close()
