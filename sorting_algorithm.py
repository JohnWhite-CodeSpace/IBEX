import os
from PyQt5.QtCore import pyqtSignal, QObject


class SortingAlgorithm(QObject):
    update_progress = pyqtSignal(int)

    def __init__(self, terminal, path, progresslabel):
        super().__init__()
        self.terminal = terminal
        self.path = path
        self.proglabel = progresslabel
        self.correct_dir_paths = []
        self.total_dirs = 0
        self.scanned_dirs = 0

    def first_stage_sorting(self):
        self.total_dirs = sum(len(dirs) for _, dirs, _ in os.walk(self.path))
        self.scanned_dirs = 0
        self.correct_dir_paths.clear()
        for root, dirs, files in os.walk(self.path):
            self.proglabel.setText(f"Scanning directory: {root}")
            self.scanned_dirs += 1
            progress = int((self.scanned_dirs / self.total_dirs) * 100)
            self.update_progress.emit(progress)
            if any(file.endswith(".attdba") for file in files if os.path.isfile(os.path.join(root, file))) \
                    and not any(file.endswith(".attd2a") for file in files if os.path.isfile(os.path.join(root, file))):
                self.correct_dir_paths.append(os.path.abspath(root))
                self.terminal.append(f"Found '.attdba' file in: {self.correct_dir_paths[-1]}\n")

    def save_correct_paths_to_file(self, name):
        with open(name, 'w') as file:
            for i, path in enumerate(self.correct_dir_paths):
                self.update_progress.emit(int((i + 1) / len(self.correct_dir_paths) * 100))
                file.write(f"{i}: {path}\n")