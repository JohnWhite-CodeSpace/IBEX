import sys
import os
import threading
from PyQt5.QtCore import QSize, pyqtSignal, Qt, QObject
from PyQt5.QtGui import QKeySequence, QIcon
from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QTextEdit, QPushButton, QFileDialog, QAction,
    QProgressBar, QVBoxLayout, QHBoxLayout, QFrame, QApplication, QTreeWidget,
    QTreeWidgetItem, QShortcut
)
import sorting_algorithm
from selection_menu import SelectionFrame
import DatasetHandler as dhs

class DirectoryLoader(QObject):
    update_progress = pyqtSignal(int)
    update_tree = pyqtSignal(object)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.total_items = 0
        self.loaded_items = 0
        self.icon_folder = QIcon('res/folder.png')
        self.icon_textfile = QIcon('res/textfile.png')
        self.icon_unknownfile = QIcon('res/unknownfile.png')

    def count_items(self, path):
        for root, dirs, files in os.walk(path):
            self.total_items += len(dirs) + len(files)

    def load_directory(self):
        def add_items(parent_item, path):
            items = sorted(os.listdir(path))
            for item in items:
                full_path = os.path.join(path, item)
                child_item = QTreeWidgetItem(parent_item, [item])
                if os.path.isdir(full_path):
                    child_item.setIcon(0, self.icon_folder)
                    add_items(child_item, full_path)
                elif item.endswith('.txt'):
                    child_item.setIcon(0, self.icon_textfile)
                else:
                    child_item.setIcon(0, self.icon_unknownfile)
                self.loaded_items += 1
                progress = int((self.loaded_items / self.total_items) * 100)
                self.update_progress.emit(progress)

        self.count_items(self.path)
        root = QTreeWidgetItem([self.path])
        add_items(root, self.path)
        self.update_tree.emit(root)

class MainWindow(QMainWindow):
    update_progress_signal = pyqtSignal(int)
    update_label_signal = pyqtSignal(str)
    update_tree_signal = pyqtSignal(object)
    update_second_progress_signal = pyqtSignal(int)
    update_second_label_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selection_frame = None
        self.setFixedSize(QSize(1200, 700))
        self.setWindowTitle("IBEX Data Sorter")
        self.path = os.getcwd()
        self.txt_file_path = None
        self.save_option = 1
        main_frame = QFrame(self)
        self.setCentralWidget(main_frame)
        main_layout = QVBoxLayout(main_frame)
        self.dataset_handler = None
        top_layout = QHBoxLayout()

        self.file_dialog_frame = QFrame(self)
        self.file_dialog_label = QLabel("Current path: ", self.file_dialog_frame)
        self.file_tree = QTreeWidget(self.file_dialog_frame)
        self.file_tree.setHeaderHidden(True)
        file_dialog_layout = QVBoxLayout(self.file_dialog_frame)
        file_dialog_layout.addWidget(self.file_dialog_label)
        file_dialog_layout.addWidget(self.file_tree)
        top_layout.addWidget(self.file_dialog_frame, stretch=2)

        self.txt_display_frame = QFrame(self)
        self.txt_edit = QTextEdit(self)
        self.txt_edit.setReadOnly(False)
        self.txt_label = QLabel("Sorting Manual display (.txt):")
        text_display_layout = QVBoxLayout(self.txt_display_frame)
        text_display_layout.addWidget(self.txt_label)
        text_display_layout.addWidget(self.txt_edit)
        top_layout.addWidget(self.txt_display_frame, stretch=4)

        main_layout.addLayout(top_layout)

        self.terminal = QTextEdit(self)
        self.terminal.setReadOnly(True)
        self.terminal_display_frame = QFrame(self)
        terminal_layout = QVBoxLayout(self.terminal_display_frame)
        terminal_label = QLabel("Console:")
        terminal_layout.addWidget(terminal_label)
        terminal_layout.addWidget(self.terminal)
        main_layout.addWidget(self.terminal_display_frame, stretch=3)

        bottom_layout = QHBoxLayout()

        progress_layout = QVBoxLayout()
        self.progress_label = QLabel("Current progress:")
        self.progress_bar = QProgressBar(self)
        self.second_progress_label = QLabel("Folder scanning progress:")
        self.second_progress_bar = QProgressBar(self)
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.second_progress_label)
        progress_layout.addWidget(self.second_progress_bar)

        buttons_layout = QVBoxLayout()
        self.start_button_DB = QPushButton('Start sorting data (Save As DataBase)', self)
        self.start_button_DS = QPushButton('Start sorting data (Save As DataSet)', self)
        self.start_button_DB.pressed.connect(self.confirm_sorting_DB)
        self.start_button_DS.pressed.connect(self.confirm_sorting_DS)
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.pressed.connect(self.stop_sorting_process)
        buttons_layout.addWidget(self.start_button_DB)
        buttons_layout.addWidget(self.start_button_DS)
        buttons_layout.addWidget(self.stop_button)

        bottom_layout.addLayout(progress_layout, stretch=3)
        bottom_layout.addLayout(buttons_layout, stretch=1)

        main_layout.addLayout(bottom_layout, stretch=1)

        self.create_menubar()

        self.update_progress_signal.connect(self.progress_bar.setValue)
        self.update_tree_signal.connect(self.update_file_tree)
        self.update_second_progress_signal.connect(self.second_progress_bar.setValue)

        self.update_label_signal.connect(self.progress_label.setText)
        self.update_second_label_signal.connect(self.second_progress_label.setText)

        self.sorting_alg = sorting_algorithm.SortingAlgorithm(self.terminal, os.getcwd())

        self.sorting_alg.update_progress.connect(self.update_progress_signal)
        self.sorting_alg.update_second_progress.connect(self.update_second_progress_signal)
        self.sorting_alg.update_label.connect(self.update_label_signal)
        self.sorting_alg.update_second_label.connect(self.update_second_label_signal)

        self.start_directory_loading(os.getcwd())

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_txt_file)
        self.load_qt_stylesheet("Themes/dark_stylesheet.css")

    def create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        open_catalog_action = QAction("Open catalog", self)
        open_catalog_action.triggered.connect(self.open_catalog)
        file_menu.addAction(open_catalog_action)

        open_txt_action = QAction("Open text file", self)
        open_txt_action.triggered.connect(self.open_txt_file)
        file_menu.addAction(open_txt_action)

        file_menu.addAction("Save as...")
        file_menu.addAction("Save")
        file_menu.addAction("Settings")
        preferences_menu = menubar.addMenu("&Preferences")
        dataset_menu = menubar.addMenu("&Datasets")
        load_dataset = QAction('Load Dataset', self)
        load_dataset.triggered.connect(self.load_dataset)
        create_batch = QAction('Create Data Batch', self)
        dataset_menu.addAction(load_dataset)
        dataset_menu.addAction(create_batch)
        theme_menu = preferences_menu.addMenu('Themes')
        dark_theme = QAction('Dark_theme', self)
        dark_theme.triggered.connect(lambda: self.load_qt_stylesheet("Themes/dark_stylesheet.css"))
        light_theme = QAction('Light theme', self)
        light_theme.triggered.connect(lambda: self.load_qt_stylesheet("Themes/light_stylesheet.css"))
        classic_theme = QAction('Classic Theme', self)
        classic_theme.triggered.connect(lambda: self.load_qt_stylesheet("Themes/classic_stylesheet.css"))
        external_theme = QAction('Load External Theme...', self)
        external_theme.triggered.connect(self.load_external_qt_stylesheet)
        clear_terminals = QAction('Clear Terminals', self)
        clear_terminals.triggered.connect(self.clear_terminals)
        preferences_menu.addAction(clear_terminals)
        theme_menu.addAction(dark_theme)
        theme_menu.addAction(light_theme)
        theme_menu.addAction(classic_theme)
        theme_menu.addAction(external_theme)

        preferences_menu.addMenu(theme_menu)
        help_menu = menubar.addMenu("&Help")

    def load_qt_stylesheet(self, stylesheet):
        try:
            with open(stylesheet, 'r', encoding='utf-8') as file:
                style_str = file.read()
            self.setStyleSheet(style_str)
        except Exception as e:
            self.terminal.append(f"Failed to load stylesheet: {e}")

    def load_external_qt_stylesheet(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter(self.tr("StyleSheets (*.qss *.css)"))
        stylesheet, _ = dialog.getOpenFileName()
        if stylesheet:
            self.load_qt_stylesheet(stylesheet)
        else:
            self.terminal.append(f"Error: Cannot load theme {stylesheet}")

    def update_file_tree(self, root_item):
        self.file_tree.clear()
        self.file_tree.addTopLevelItem(root_item)
        self.file_tree.expandAll()

    def open_catalog(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Directory", os.getcwd())
        if selected_dir:
            self.path = selected_dir
            self.file_dialog_label.setText(f"Current path: {selected_dir}")
            self.progress_bar.setValue(0)
            self.second_progress_bar.setValue(0)
            self.start_directory_loading(selected_dir)

    def open_txt_file(self):
        txt_file_path, _ = QFileDialog.getOpenFileName(self, "Open Text File", "", "Text Files (*.txt)")
        if txt_file_path:
            self.txt_file_path = txt_file_path
            with open(txt_file_path, 'r') as file:
                self.txt_edit.setText(file.read())

    def save_txt_file(self):
        if self.txt_file_path:
            with open(self.txt_file_path, 'w') as file:
                file.write(self.txt_edit.toPlainText())
        else:
            self.save_txt_as()

    def save_txt_as(self):
        txt_file_path, _ = QFileDialog.getSaveFileName(self, "Save Text File As", "", "Text Files (*.txt)")
        if txt_file_path:
            self.txt_file_path = txt_file_path
            self.save_txt_file()

    def start_directory_loading(self, path):
        self.directory_loader = DirectoryLoader(path)
        self.directory_loader.update_progress.connect(self.update_progress_signal)
        self.directory_loader.update_tree.connect(self.update_tree_signal)

        self.thread = threading.Thread(target=self.directory_loader.load_directory)
        self.thread.start()

    def confirm_sorting_DB(self):
        self.save_option = 1
        self.selection_frame = SelectionFrame()
        self.sorting_alg.get_saving_option(self.save_option)
        self.selection_frame.sorting_options_selected.connect(self.start_sorting_data_with_options)
        self.selection_frame.show()

    def confirm_sorting_DS(self):
        self.save_option = 2
        self.selection_frame = SelectionFrame()
        self.sorting_alg.get_saving_option(self.save_option)
        self.selection_frame.sorting_options_selected.connect(self.start_sorting_data_with_options)
        self.selection_frame.show()

    def start_sorting_data_with_options(self, options):
        print(options['instruction'])
        print(options['quaternion'])
        print(options['event'])
        print(options['qualh'])
        print(options['file_types'])
        print(options['channels'])
        print(options['particle_events'])
        self.sorting_alg.set_instruction_file(options['instruction'])
        self.sorting_alg.set_quaternion_file_type(options['quaternion'])
        self.sorting_alg.set_event_type(options['event'])
        self.sorting_alg.set_qualh(options['qualh'], options['instruction'])
        self.sorting_alg.set_filenames_for_sorting(options['file_types'])
        self.sorting_alg.set_channels(options['channels'])
        self.sorting_alg.set_particle_events(options['particle_events'])
        if self.save_option == 1:
            self.start_sorting_data_DB()
        else:
            self.start_sorting_data_DS()

    def start_sorting_data_DB(self):
        self.sorting_thread = threading.Thread(target=self.run_sorting_process_DB)
        self.sorting_thread.start()

    def start_sorting_data_DS(self):
        self.sorting_thread = threading.Thread(target=self.run_sorting_process_DS)
        self.sorting_thread.start()

    def stop_sorting_process(self):
        self.sorting_alg.stop_sorting_process()

    def run_sorting_process_DB(self):
        self.sorting_alg.set_path(self.path)
        name, _ = QFileDialog.getSaveFileName(self, "Save DataBase File As", "", "DataBase Files (*.db)")

        if name:
            self.sorting_alg.set_database_connection(name)
            self.sorting_alg.first_stage_processing()
            self.terminal.append("Sorting completed. Saving results...")
            save_file_path, _ = QFileDialog.getSaveFileName(self, "Save text file with correct data paths", "",
                                                            "Text Files (*.txt)")
            self.sorting_alg.save_loading_log()
            if save_file_path:
                self.save_thread = threading.Thread(target=self.sorting_alg.save_correct_paths_to_file,
                                                    args=(save_file_path,))
                self.save_thread.start()
        else:
            self.terminal.append("Choose database file first!")

    def run_sorting_process_DS(self):
        self.sorting_alg.set_path(self.path)
        name, _ = QFileDialog.getSaveFileName(self, "Save Dataset File As", "", "Compressed Pickle Files (*.pt)")

        if name:
            self.sorting_alg.set_dataset(name)
            self.sorting_alg.first_stage_processing()
            self.terminal.append("Sorting completed. Saving results...")
            self.sorting_alg.save_dataset_to_file()
            save_file_path, _ = QFileDialog.getSaveFileName(self, "Save text file with correct data paths", "",
                                                            "Text Files (*.txt)")
            self.sorting_alg.save_loading_log()
            if save_file_path:
                self.save_thread = threading.Thread(target=self.sorting_alg.save_correct_paths_to_file,
                                                    args=(save_file_path,))
                self.save_thread.start()
        else:
            self.terminal.append("Choose dataset file first!")

    def load_dataset(self):
        name, _ = QFileDialog.getOpenFileName(self, "Select Dataset file", "", "Pickled datasets (*.pt)")
        if name:
            self.terminal.append(f"Loading dataset from {name}...")
            self.dataset_handler = dhs.DatasetHandler(self.terminal)
            self.load_thread = threading.Thread(target=self.dataset_handler.unpack_dataset, args=(name,))
            self.load_thread.start()
        else:
            self.terminal.append("Cannot open this dataset!")

    def clear_terminals(self):
        self.terminal.clear()
        self.txt_edit.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
