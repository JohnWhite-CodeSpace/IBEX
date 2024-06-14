import os
import re
import time

import pandas as pd
import sqlite3
from PyQt5.QtCore import pyqtSignal, QObject
import numpy as np


class SortingAlgorithm(QObject):
    update_progress = pyqtSignal(int)
    update_second_progress = pyqtSignal(int)
    update_label = pyqtSignal(str)
    update_second_label = pyqtSignal(str)

    def __init__(self, terminal, path):
        super().__init__()
        self.qualh = None
        self.event = None
        self.quaternion = None
        self.noquaternion = None
        self.instruction = None
        self.filters = None
        self.terminal = terminal
        self.path = path
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
        self.particle_event = []
        self.channels = []
        self.time_log = []

    def set_instruction_file(self, instruction):
        self.instruction = instruction

    def set_path(self, path):
        self.path = path

    def set_quaternion_file_type(self, quaternion):
        self.quaternion = quaternion
        self.noquaternion = ".attd2a" if quaternion == ".attdba" else ".attdba"

    def set_event_type(self, event):
        self.event = event

    def set_qualh(self, qualh, instruction):
        self.condition.clear()
        if instruction == "HiCullGoodTimes.txt":
            if "Q-ABC" in qualh:
                self.condition.extend(["0A", "0E", "05"])
            if "Q-AB" in qualh:
                self.condition.extend(["09", "0D", "04"])
            if "Q-BC" in qualh:
                self.condition.extend(["03"])
            if "Q-AC" in qualh:
                self.condition.extend(["08"])
            if "None" in qualh:
                self.condition.extend(["0C", "0F", "07", "02", "06", "00", "0B", "01"])
        elif instruction == "LoGoodTimes.txt":
            TOF0 = {"40", "41", "42", "43", "44", "45", "46", "47"}
            TOF1 = {"40", "41", "42", "43", "49", "4A", "4B"}
            TOF2 = {"40", "41", "44", "45", "48", "49", "4C", "4D"}
            TOF3 = {"40", "42", "44", "46", "48", "4A", "4C", "4E"}
            self.condition = {"40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "4A", "4B", "4C", "4D", "4E"}
            if "TOF0" in qualh:
                self.condition.intersection_update(TOF0)
            if "TOF1" in qualh:
                self.condition.intersection_update(TOF1)
            if "TOF2" in qualh:
                self.condition.intersection_update(TOF2)
            if "TOF3" in qualh:
                self.condition.intersection_update(TOF3)

            self.condition = list(self.condition)

        print(self.condition)

    def set_particle_events(self, part_eve):
        if self.instruction == "LoGoodTimes.txt":
            if "Hydrogen" in part_eve:
                self.particle_event.extend([f"2{i}" for i in self.channels])
            if "Oxygen" in part_eve:
                self.particle_event.extend([f"4{i}" for i in self.channels])
        else:
            self.particle_event = [f"1{i}" for i in self.channels]
        print(self.particle_event)

    def set_channels(self, channels):
        for i in range(1, 9):
            if f"Channel {i}" in channels and "All" not in channels:
                self.channels.append(i)
        if "All" in channels and "Channel" not in channels:
            for i in range(1, 9):
                self.channels.append(i)
        print(self.channels)

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
        self.time_log.append("Time:\tFile:\tNumber of lines:\n")
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
            proglabel = f"Scanning directory: {root}"
            self.scanned_dirs += 1
            self.update_progress.emit(int((self.scanned_dirs / self.total_dirs) * 100))
            self.update_second_progress.emit(0)
            self.update_label.emit(proglabel)

            if any(file.endswith(self.quaternion) for file in files) and not any(
                    file.endswith(self.noquaternion) for file in files):
                double_obs_info = self.check_double_observation(root)
                self.correct_dir_paths.append((os.path.abspath(root), double_obs_info))
                self.terminal.append(
                    f"Found '{self.quaternion}' file in: {self.correct_dir_paths[-1][0]} (Double Observation: {double_obs_info})")
                self.total_files = len(files)
                self.scanned_files = 0
                for file in files:
                    if self.stop_flag:
                        self.terminal.append("Sorting process stopped.")
                        return
                    proglabel2 = f"Processing file: {file}"
                    self.update_second_progress.emit(int((self.scanned_files / self.total_files) * 100))
                    self.update_second_label.emit(proglabel2)
                    if any(str(num) in file for num in self.channels):
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
                elif file.endswith("hihb-3.txt"):
                    hi3_file = os.path.join(root, file)
                if hi2_file and hi3_file:
                    if os.path.getsize(hi3_file) >= 1.8 * os.path.getsize(hi2_file):
                        self.terminal.append(f"Double observation occurred in {root}")
                        return "True"
        return "False"

    def second_stage_processing(self, file, path):
        if (any(sub in file for sub in self.filenames_for_sorting) and
                file.endswith(".txt") and
                not any(file.endswith(ext) for ext in [self.quaternion, ".star-spin-nep.txt", "ibex_state_GSE.txt"])):
            filepath = os.path.join(path, file)
            if not self.check_filter_in_filepath(filepath) or not self.check_channel_observation(filepath):
                return
            self.terminal.append(f"Found file in: {filepath}")
            start = round(time.time()*1000)
            lines = np.loadtxt(filepath, dtype="str")
            end = round(time.time()*1000)
            load_time = end - start
            self.time_log.append(f"{load_time}\t{file}\t{len(lines)}\n")
            data = self.process_filtered_lines(lines, filepath)
            self.write_to_database(data)

    def process_filtered_lines(self, lines, filepath):
        filtered_data = []
        self.total_lines = len(lines)
        self.scanned_lines = 0

        met_values = lines[:, 0].astype(float)
        ch_values = lines[:, 3]
        ty_values = lines[:, 4]

        for filter_entry in self.filters:
            if filter_entry[0] in filepath:
                start_value = float(filter_entry[1])
                end_value = float(filter_entry[2])
                mask = (met_values >= start_value) & (met_values <= end_value)
                filtered_lines = lines[mask]
                filtered_ch_values = ch_values[mask]
                filtered_ty_values = ty_values[mask]

                for line, ty, ch in zip(filtered_lines, filtered_ty_values, filtered_ch_values):
                    if ty in self.condition and ch in self.particle_event:
                        filtered_data.append(line)

        return filtered_data

    def write_to_database(self, data):
        if len(data) == 0:
            return
        columns = ["MET", "RA", "Decl", "ch", "ty", "count", "selnbits", "phase", "locXRE", "locYRE", "locZRE"]
        df = pd.DataFrame(data, columns=columns)
        try:
            df.to_sql('data', self.conn, if_exists='append', index=False)
        except sqlite3.Error as e:
            self.terminal.append(f"SQLite error: {e}")

    def load_filtering_instructions(self, filename):
        try:
            lines = np.loadtxt(filename, dtype='str')
            self.filters = lines
            return self.filters
        except FileNotFoundError:
            self.terminal.append(f"Error: Instruction file '{filename}' not found.")
            return None

    def check_filter_in_filepath(self, filepath):
        return any(filter_entry[0] in filepath for filter_entry in self.filters) if self.filters is not None else True

    def check_channel_observation(self, filepath):
        if self.filters is None:
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
                        (is_hide and 1 <= channel_number <= 6 and filter_entry[-7:][channel_number - 1] == '1' and
                         filter_entry[-1] == '2'):
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

    def save_loading_log(self):
        with open("TimeLoadingLogNumpy.txt", 'a') as time_file:
            time_file.writelines(self.time_log)
        self.terminal.append(f"Time Log saved to {time}")