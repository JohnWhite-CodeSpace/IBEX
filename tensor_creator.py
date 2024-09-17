import torch
import numpy as np
import os
import gc
from PyQt5.QtCore import pyqtSignal, QObject


class TensorCreator(QObject):
    update_progress = pyqtSignal(int)
    update_second_progress = pyqtSignal(int)
    update_label = pyqtSignal(str)
    update_second_label = pyqtSignal(str)

    def __init__(self, terminal, path):
        super().__init__()
        self.channel_division = None # option to divide tensors by observed ENA channels
        self.path = path
        self.terminal = terminal
        self.instruction = None
        self.quaternion_file = None  # .atttba/.attd2a
        self.file_type = None  # lode, hide - direct event; lohb, hihb - histogram events
        self.savefile_prefix = "None"  # prefix of saved tensor before structure indicator (half year/year/all)
        self.structure_attribute = 0  # 0 = tensor/half year; 1 = tensor/year; 2 = tensor with all data
        self.include_hex_flags = True
        self.stop_tensor = False
        self.scanned_dirs = 0
        self.total_dirs = 0
        self.scanned_files = 0
        self.total_files = 0


    def set_path(self, path):
        self.path = path

    def set_instruction(self, instruction):
        self.instruction = instruction

    def set_file_prefix(self, file_prefix):
        self.savefile_prefix = file_prefix

    def set_quaternion_file(self, quaternion_file):
        self.quaternion_file = quaternion_file

    def set_filetype(self, file_type):
        self.file_type = file_type

    def set_channel_division(self, channel_division):
        self.channel_division = channel_division

    def set_timespan_attribute(self, timespan_attribute):
        if timespan_attribute == "Every half year":
            self.structure_attribute = 0
        elif timespan_attribute == "Every year":
            self.structure_attribute = 1
        elif timespan_attribute == "All at once":
            self.structure_attribute = 2

    def set_hex(self, hex):
        if hex == "Translate to int":
            self.include_hex_flags = True
        elif hex == "Replace with '0'":
            self.include_hex_flags = True

    def create_data_tensor(self):
        self.terminal.append("Initialising tensor creation with raw data...")
        if self.structure_attribute == 0:
            self.init_half_year_tensors()
        elif self.structure_attribute == 1:
            self.init_year_tensors()
        elif self.structure_attribute == 2:
            self.init_alldata_tensors()
        else:
            self.terminal.append("Invalid tensor creation option selected!")
            return

    def init_half_year_tensors(self):
        half_year_dirs = [d for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, d))]
        self.total_dirs = len(half_year_dirs)
        self.scanned_dirs = 0
        self.update_second_progress.emit(0)
        self.update_progress.emit(0)
        for half_year_dir in half_year_dirs:
            if self.stop_tensor:
                proglabel = "Data processing stopped!"
                self.update_label.emit(proglabel)
                return
            subdir_path = os.path.join(self.path, half_year_dir)
            proglabel = f"Processing half year directory: {subdir_path}"
            self.update_label.emit(proglabel)
            data_list = []
            self.scanned_dirs += 1
            self.update_progress.emit(int((self.scanned_dirs/self.total_dirs)*100))
            gc.collect()
            for root, _, files in os.walk(subdir_path):
                self.total_files = len(files)
                self.scanned_files = 0
                if self.stop_tensor:
                    proglabel = "Data processing stopped!"
                    self.update_label.emit(proglabel)
                    return
                if any(file.endswith(self.quaternion_file) for file in files):
                    for file in files:
                        if self.file_type in file:
                            file_path = os.path.join(root, file)
                            proglabel2 = f"Loading file: {file_path}"
                            self.update_second_label.emit(proglabel2)
                            text = np.loadtxt(file_path, dtype='str')
                            text = self.remove_or_convert_hex_flags(text)
                            text = np.array(text, dtype=float)
                            data_list.append(text)
                        self.scanned_files+=1
                        self.update_second_progress.emit(int((self.scanned_files/self.total_files)*100))
                        gc.collect()
            if data_list:
                combined_data = np.vstack(data_list)
                save_path = f"{self.savefile_prefix}_half_year_{half_year_dir}.pt"
                torch.save(torch.tensor(combined_data), save_path)
                self.terminal.append(f"Saved tensor for {half_year_dir} to {save_path}")
        proglabel = "Data processing finished!"
        self.update_label.emit(proglabel)
        gc.collect()

    def init_year_tensors(self):
        # Identify all unique years
        year_dirs = sorted({d[:4] for d in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, d))})
        self.total_dirs = len(year_dirs)
        self.scanned_dirs = 0
        self.update_second_progress.emit(0)
        self.update_progress.emit(0)

        for year_dir in year_dirs:
            if self.stop_tensor:
                proglabel = "Data processing stopped!"
                self.update_label.emit(proglabel)
                return

            proglabel = f"Processing year directory: {year_dir}"
            self.update_label.emit(proglabel)

            data_list = []
            self.scanned_dirs += 1
            self.update_progress.emit(int((self.scanned_dirs / self.total_dirs) * 100))

            for half in ['A', 'B']:
                half_year_dir = f"{year_dir}{half}"
                subdir_path = os.path.join(self.path, half_year_dir)

                if os.path.isdir(subdir_path):
                    for root, _, files in os.walk(subdir_path):
                        self.total_files = len(files)
                        self.scanned_files = 0

                        if self.stop_tensor:
                            proglabel = "Data processing stopped!"
                            self.update_label.emit(proglabel)
                            return

                        if any(file.endswith(self.quaternion_file) for file in files):
                            for file in files:
                                if self.file_type in file:
                                    file_path = os.path.join(root, file)
                                    proglabel2 = f"Loading file: {file_path}"
                                    self.update_second_label.emit(proglabel2)

                                    text = np.loadtxt(file_path, dtype='str')
                                    text = self.remove_or_convert_hex_flags(text)
                                    text = np.array(text, dtype=float)
                                    data_list.append(text)

                                self.scanned_files += 1
                                self.update_second_progress.emit(int((self.scanned_files / self.total_files) * 100))

                            gc.collect()

            if data_list:
                combined_data = np.vstack(data_list)
                save_path = f"{self.savefile_prefix}_year_{year_dir}.pt"
                torch.save(torch.tensor(combined_data), save_path)
                self.terminal.append(f"Saved tensor for year {year_dir} to {save_path}")
                print(f"Shape of combined data for year {year_dir}: {combined_data.shape}")

        proglabel = "Data processing finished!"
        self.update_label.emit(proglabel)
        gc.collect()

    def init_alldata_tensors(self):
        proglabel = "Processing all data..."
        self.update_label.emit(proglabel)

        batch_size_limit = 2 * 1024 ** 3  # 2 GB limit per batch
        batch_data_list = []
        batch_current_size = 0
        first_batch = True
        save_path = f"{self.savefile_prefix}_all_data.pt"

        self.total_dirs = sum(len(dirs) for _, dirs, _ in os.walk(self.path))
        self.scanned_dirs = 0
        self.update_second_progress.emit(0)
        self.update_progress.emit(0)

        for root, dirs, files in os.walk(self.path):
            if self.stop_tensor:
                proglabel = "Data processing stopped!"
                self.update_label.emit(proglabel)
                return

            self.scanned_dirs += 1
            self.update_progress.emit(int((self.scanned_dirs / self.total_dirs) * 100))
            self.scanned_files = 0
            self.total_files = len(files)

            if any(file.endswith(self.quaternion_file) for file in files):
                for file in files:
                    if self.file_type in file:
                        file_path = os.path.join(root, file)
                        proglabel2 = f"Loading file: {file_path}"
                        self.update_second_label.emit(proglabel2)

                        text = np.loadtxt(file_path, dtype='str')
                        text = self.remove_or_convert_hex_flags(text)
                        text = np.array(text, dtype=float)

                        batch_data_list.append(text)
                        batch_current_size += text.nbytes

                        if batch_current_size >= batch_size_limit:
                            self.save_batch(batch_data_list, save_path, first_batch)
                            first_batch = False
                            batch_data_list = []
                            batch_current_size = 0

                        self.scanned_files += 1
                        self.update_second_progress.emit(int((self.scanned_files / self.total_files) * 100))
                        gc.collect()

        if batch_data_list:
            self.save_batch(batch_data_list, save_path, first_batch)

        proglabel = "Data processing finished!"
        self.update_label.emit(proglabel)
        gc.collect()

    def save_batch(self, batch_data_list, save_path, first_batch):
        """Save the batch of data to a file, appending if not the first batch."""
        combined_data = np.vstack(batch_data_list)
        tensor_data = torch.tensor(combined_data, dtype=torch.float)

        if first_batch:
            torch.save(tensor_data, save_path)
            self.terminal.append(f"Saved initial batch to {save_path}")
        else:
            existing_data = torch.load(save_path)
            updated_data = torch.cat((existing_data, tensor_data), dim=0)
            torch.save(updated_data, save_path)
            self.terminal.append(f"Appended batch to {save_path}")

        gc.collect()

    def remove_or_convert_hex_flags(self, data_list):
        if self.include_hex_flags:
            ch_column = data_list[:, 3]
            ty_column = data_list[:, 4]
            int_ch_column = np.vectorize(lambda x: int(x, 16))(ch_column)
            int_ty_column = np.vectorize(lambda x: int(x, 16))(ty_column)
            data_list[:, 3] = int_ch_column # changing ch from hex to int
            data_list[:, 4] = int_ty_column # changing ty from hex to int
            data_list[:, 6] = '0' # selnbits are not used so ve just ignore them (i dont know what they are and i dont care tbh)
        else:
            data_list[:, 3] = '0'
            data_list[:, 4] = '0'
            data_list[:, 6] = '0' # still ignoring them fuckers
        gc.collect()
        return data_list

    def stop_tensor_creation_process(self):
        self.stop_tensor = True