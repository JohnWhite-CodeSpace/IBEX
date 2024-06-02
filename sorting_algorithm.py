import os
import re
import pandas as pd
import sqlite3
from PyQt5.QtCore import pyqtSignal, QObject

class SortingAlgorithm(QObject):
    update_progress = pyqtSignal(int)
    update_second_progress = pyqtSignal(int)
    update_third_progress = pyqtSignal(int)

    def __init__(self, terminal, path, progresslabel, progresslabel2, progresslabel3):
        super().__init__()
        self.qualh = None
        self.event = None
        self.quaternion = None
        self.noquaternion = None
        self.instruction = None
        self.filters = None
        self.terminal = terminal
        self.path = path
        self.proglabel = progresslabel
        self.proglabel2 = progresslabel2
        self.proglabel3 = progresslabel3
        self.correct_dir_paths = []
        self.total_dirs = 0
        self.scanned_dirs = 0
        self.total_files = 0
        self.scanned_files = 0
        self.total_lines = 0
        self.scanned_lines = 0
        self.condition = ["0A", "0E", "05"]
        self.filenames_for_sorting = []
        self.stop_flag = False

    def set_instruction_file(self, instruction):
        self.instruction = instruction

    def set_path(self, path):
        self.path = path

    def set_quaternion_file_type(self, quaternion):
        self.quaternion = quaternion
        self.noquaternion = ".attd2a" if quaternion == ".attdba" else ".attdba"

    def set_event_type(self, event):
        self.event = event

    def set_qualh(self, qualh):
        if "Q-ABC" in qualh:
            self.condition = ["0A", "0E", "05"]
        if "Q-AB" in qualh:
            self.condition = ["09", "0D", "04"]
        if "Q-BC" in qualh:
            self.condition = ["03"]
        if "Q-AC" in qualh:
            self.condition = ["08"]
        if "None" in qualh:
            self.condition = ["0C", "0F", "07", "02", "06", "00", "0B", "01"]

    def set_filenames_for_sorting(self, filenames):
        self.filenames_for_sorting = filenames

    def create_table(self):
        columns = ["MET", "RA", "Decl", "ch", "ty", "count", "selnbits", "phase", "locXRE", "locYRE", "locZRE"]
        column_definitions = ', '.join([f'{column} TEXT' for column in columns])
        query = f'CREATE TABLE IF NOT EXISTS data ({column_definitions})'
        try:
            self.cursor.execute(query)
            self.conn.commit()
        except sqlite3.Error as e:
            self.terminal.append(f"SQLite error: {e}")

    def set_database_connection(self, name):
        self.conn = sqlite3.connect(name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def first_stage_processing(self):
        self.terminal.append("Starting first stage processing...")
        self.total_dirs = sum(len(dirs) for _, dirs, _ in os.walk(self.path))
        self.scanned_dirs = 0
        self.correct_dir_paths.clear()
        self.filters = self.load_filtering_instructions(self.instruction)
        if self.filters is None:
            self.terminal.append("Error: Filters could not be loaded.")
            return

        for root, dirs, files in os.walk(self.path):
            if self.stop_flag:
                self.terminal.append("Sorting process stopped.")
                return
            self.proglabel.setText(f"Scanning directory: {root}")
            self.scanned_dirs += 1
            self.update_progress.emit(int((self.scanned_dirs / self.total_dirs) * 100))
            self.update_second_progress.emit(0)
            self.update_third_progress.emit(0)

            if any(file.endswith(self.quaternion) for file in files) and not any(file.endswith(self.noquaternion) for file in files):
                double_obs_info = self.check_double_observation(root)
                self.correct_dir_paths.append((os.path.abspath(root), double_obs_info))
                self.terminal.append(f"Found '{self.quaternion}' file in: {self.correct_dir_paths[-1][0]} (Double Observation: {double_obs_info})")
                self.total_files = len(files)
                self.scanned_files = 0
                for file in files:
                    if self.stop_flag:
                        self.terminal.append("Sorting process stopped.")
                        return
                    self.update_second_progress.emit(int((self.scanned_files / self.total_files) * 100))
                    self.proglabel2.setText(f"Processing file: {file}")
                    self.second_stage_processing(file, os.path.abspath(root))
                    self.scanned_files += 1

    def save_correct_paths_to_file(self, name):
        with open(name, 'w') as file:
            for i, (path, double_obs_info) in enumerate(self.correct_dir_paths):
                file.write(f"{i}: {path} (Double Observation: {double_obs_info})\n")

    def check_double_observation(self, path):
        hi2_file = None
        hi3_file = None
        for root, _, files in os.walk(path):
            if self.stop_flag:
                return "Sorting process stopped."
            for file in files:
                if file.endswith("hihb-2.txt"):
                    hi2_file = os.path.join(root, file)
                    self.terminal.append(f"Found file: {file}")
                elif file.endswith("hihb-3.txt"):
                    hi3_file = os.path.join(root, file)
                if hi2_file and hi3_file:
                    if os.path.getsize(hi3_file) >= 1.8 * os.path.getsize(hi2_file):
                        self.terminal.append(f"Double observation occurred in {root}")
                        return "Double observation: Yes"
        return "Double observation: No"

    def second_stage_processing(self, file, path):
        if (any(sub in file for sub in self.filenames_for_sorting) and
                file.endswith(".txt") and
                not any(file.endswith(ext) for ext in [self.quaternion, ".star-spin-nep.txt", "ibex_state_GSE.txt"])):
            filepath = os.path.join(path, file)
            if not self.check_filter_in_filepath(filepath) or not self.check_channel_observation(filepath):
                return
            self.terminal.append(f"Found file in: {filepath}")
            self.proglabel.setText(f"Scanning file: {filepath}...")
            with open(filepath, "r") as filedata:
                lines = filedata.readlines()
            data = self.process_filtered_lines(lines, filepath)
            self.write_to_database(data)

    def process_filtered_lines(self, lines, filepath):
        filtered_data = []
        self.total_lines = len(lines)
        self.scanned_lines = 0

        for line in lines:
            if self.stop_flag:
                self.terminal.append("Sorting process stopped.")
                return filtered_data
            if line.startswith("#"):
                continue
            split_line = re.split('\s+', line.strip())
            met_value = float(split_line[0])

            for filter_entry in self.filters:
                if filter_entry[0] in filepath:
                    start_value = float(filter_entry[1])
                    end_value = float(filter_entry[2])
                    if start_value <= met_value <= end_value:
                        filtered_data.append((line, split_line[4], split_line[3]))
            self.scanned_lines += 1
            if (self.instruction == "HiCullGoodTimes.txt" and self.scanned_lines % 500 == 0) or (self.scanned_lines % 200 == 0):
                progress3 = int((self.scanned_lines / self.total_lines) * 100)
                self.update_third_progress.emit(progress3)
                self.proglabel3.setText(f"Scanned lines: {self.scanned_lines} out of {self.total_lines}")

        return filtered_data

    def write_to_database(self, data):
        columns = ["MET", "RA", "Decl", "ch", "ty", "count", "selnbits", "phase", "locXRE", "locYRE", "locZRE"]
        df = pd.DataFrame([dict(zip(columns, re.split('\s+', line.strip()))) for line, _, _ in data])
        try:
            df.to_sql('data', self.conn, if_exists='append', index=False)
        except sqlite3.Error as e:
            self.terminal.append(f"SQLite error: {e}")

    def load_filtering_instructions(self, filename):
        try:
            with open(filename, 'r') as instruction:
                lines = instruction.readlines()
            filters = [re.split("\s+", line.strip()) for line in lines if not line.startswith("#") and line.strip()]
            return filters
        except FileNotFoundError:
            self.terminal.append(f"Error: Instruction file '{filename}' not found.")
            return None

    def check_filter_in_filepath(self, filepath):
        return any(filter_entry[0] in filepath for filter_entry in self.filters) if self.filters else True

    def check_channel_observation(self, filepath):
        if not self.filters:
            return False
        match = re.search(r'-(\d+)\.txt$', filepath)
        if not match:
            return False
        channel_number = int(match.group(1))
        is_lode = 'lode' in filepath
        is_hide = 'hide' in filepath

        for filter_entry in self.filters:
            if filter_entry[0] in filepath:
                if (is_lode and 1 <= channel_number <= 8 and filter_entry[-8:][channel_number - 1] == '1') or \
                   (is_hide and 1 <= channel_number <= 6 and filter_entry[-7:][channel_number - 1] == '1' and filter_entry[-1] == '2'):
                    return True
        return False

    def get_path(self, conditions):
        for path, _ in self.correct_dir_paths:
            if conditions[0] in path:
                return path
        return ""

    def close_connection(self):
        self.conn.close()

    def stop_sorting_process(self):
        self.stop_flag = True
