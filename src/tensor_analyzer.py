import re

import torch
import os
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import gc

from torch.utils.data import TensorDataset, DataLoader


class PearsonsMatrixCreator:

    def __init__(self, terminal, hi_tensor_directory, lo_tensor_directory, filename_prefix_hi, filename_prefix_lo,
                 hi_instruction_file, lo_instruction_file):
        self.hi_tensor_directory = hi_tensor_directory
        self.lo_tensor_directory = lo_tensor_directory
        self.filename_prefix_hi = filename_prefix_hi
        self.filename_prefix_lo = filename_prefix_lo
        self.hi_instruction_file = hi_instruction_file
        self.lo_instruction_file = lo_instruction_file
        self.channel_labels = [f'hi{i}' for i in range(1, 7)] + [f'lo{i}' for i in range(1, 9)]
        self.pearson_matrix = np.zeros((14, 14))
        self.terminal = terminal

    def load_tensor(self, path):
        return torch.load(path)

    def print_short_data_manual(self):
        self.terminal.append("File column description:")
        self.terminal.append("1) MET(s,GPS):   2) R.A.:   3) Decl:   4) ch:   5) ty:   6) count:   7) selnbits:   "
                             "8) phase:   9) loc-X-RE:  10) loc-Y-RE:  11) loc-Z-RE:")

        self.terminal.append("\n'ch' Legend:")
        self.terminal.append("The 'ch' column encodes species and ESA. High-order digit is species:\n"
                             "  1: Hydrogen\n  4: Oxygen\nLow-order digit is ESA (1-6 for Hi, 1-8 for Lo).")

        self.terminal.append("\n'ty' Legend:")
        self.terminal.append(
            "The 'ty' column encodes sensor type and coincidence type. High-order digit is sensor type:\n"
            "  0: Hi DE\n  1: Hi HB\n  4: Lo DE\n  8: Lo HB (6° histograms)\n  C: 60° monitors")
        self.terminal.append("Low-order digit is coincidence type (e.g., A: abcABC, 5: -b-ABC, E: ab-ABC).")

        self.terminal.append("\nEvent Classification:")
        self.terminal.append("abc: ABC pulses latched after short window\n"
                             "ABC: ABC pulses latched after long window\n"
                             "L-???: Long count coincidence histogram group\n"
                             "Q-???: Qualified count coincidence histogram group\n")

        self.terminal.append("TOF Flags (Hex):\n  0: Triple (all valid)\n  1-7: Various double/triple events\n"
                             "  8-F: Other TOF combinations, including single and absent events.")
        gc.collect()

    def translate_hex_to_int(self, hex_list):
        return [int(item, 16) for item in hex_list]

    def managing_data_based_on_instruction_files(self, tensor, tensor_name, instruction_file, is_hi_channel):
        if is_hi_channel:
            channel_num = int(re.search(r'channel_(.+?).pt', tensor_name).group(1))
            dtype = [('orbit', 'i4'), ('start_time', 'f8'), ('end_time', 'f8'), ('phase_start', 'i4'),
                     ('phase_end', 'i4'), ('dataset', 'U2'), ('channel_1', 'i4'), ('channel_2', 'i4'),
                     ('channel_3', 'i4'), ('channel_4', 'i4'), ('channel_5', 'i4'), ('channel_6', 'i4')]
        else:
            channel_num = int(
                re.search(r'channel_(.+?).pt', tensor_name).group(1)) - 6
            dtype = [('orbit', 'i4'), ('start_time', 'f8'), ('end_time', 'f8'), ('phase_start', 'i4'),
                     ('phase_end', 'i4'), ('dataset', 'U2'), ('channel_1', 'i4'), ('channel_2', 'i4'),
                     ('channel_3', 'i4'), ('channel_4', 'i4'), ('channel_5', 'i4'), ('channel_6', 'i4'),
                     ('channel_7', 'i4'), ('channel_8', 'i4')]

        instruction_data = np.genfromtxt(instruction_file, dtype=dtype, encoding=None)

        time_start_col = 1
        time_end_col = 2
        phase_start_col = 3
        phase_end_col = 4
        channel_bool_checker_col = 5 + channel_num

        good_data_intervals = []
        for row in instruction_data:
            if row[channel_bool_checker_col] == 1 and row[phase_start_col] == 0 and row[phase_end_col] == 59:
                start_time = row[time_start_col]
                end_time = row[time_end_col]
                good_data_intervals.append({'start_time': start_time, 'end_time': end_time})

        good_data_sums = []
        for interval in good_data_intervals:
            start_time = interval['start_time']
            end_time = interval['end_time']
            valid_data = tensor[(tensor[:, 0] >= start_time) & (tensor[:, 0] <= end_time)]
            sum_valid_data = valid_data[:, 5].sum().item()
            good_data_sums.append(sum_valid_data)
        gc.collect()
        return good_data_sums

    def weighted_pearsons_coefficient(self, X_vals, Y_vals, weights):
        """Oblicza ważony współczynnik Pearsona."""
        if len(X_vals) == 0 or len(Y_vals) == 0:
            return np.nan
        X_vals = np.array(X_vals)
        Y_vals = np.array(Y_vals)
        weights = np.array(weights)

        mean_x = np.average(X_vals, weights=weights)
        mean_y = np.average(Y_vals, weights=weights)

        covariance = np.sum(weights * (X_vals - mean_x) * (Y_vals - mean_y))
        std_x = np.sqrt(np.sum(weights * (X_vals - mean_x) ** 2))
        std_y = np.sqrt(np.sum(weights * (Y_vals - mean_y) ** 2))

        if std_x == 0 or std_y == 0:
            return np.nan
        gc.collect()
        return covariance / (std_x * std_y)

    def calculate_pearsons_for_all_channels(self):
        for i in range(1, 15):
            for j in range(1, 15):
                if i <= 6:
                    tensor_i_path = os.path.join(self.hi_tensor_directory, f"{self.filename_prefix_hi}{i}.pt")
                    instruction_file_i = self.hi_instruction_file
                    is_hi_channel_i = True
                else:
                    tensor_i_path = os.path.join(self.lo_tensor_directory, f"{self.filename_prefix_lo}{i - 6}.pt")
                    instruction_file_i = self.lo_instruction_file
                    is_hi_channel_i = False

                if j <= 6:
                    tensor_j_path = os.path.join(self.hi_tensor_directory, f"{self.filename_prefix_hi}{j}.pt")
                    instruction_file_j = self.hi_instruction_file
                    is_hi_channel_j = True
                else:
                    tensor_j_path = os.path.join(self.lo_tensor_directory, f"{self.filename_prefix_lo}{j - 6}.pt")
                    instruction_file_j = self.lo_instruction_file
                    is_hi_channel_j = False

                try:
                    tensor_i = self.load_tensor(tensor_i_path)
                    tensor_j = self.load_tensor(tensor_j_path)

                    counts_i = self.managing_data_based_on_instruction_files(tensor_i, f"channel_{i}.pt",
                                                                             instruction_file_i, is_hi_channel_i)
                    counts_j = self.managing_data_based_on_instruction_files(tensor_j, f"channel_{j}.pt",
                                                                             instruction_file_j, is_hi_channel_j)

                    min_length = min(len(counts_i), len(counts_j))
                    counts_i = counts_i[:min_length]
                    counts_j = counts_j[:min_length]

                    weights = np.ones(min_length)

                    pearson_value = self.weighted_pearsons_coefficient(counts_i, counts_j, weights)
                    self.pearson_matrix[i - 1, j - 1] = pearson_value
                    print(f"Weighted Pearson coefficient for channels {i} and {j}: {pearson_value}")

                except Exception as e:
                    print(f"Error calculating Pearson for channels {i} and {j}: {e}")
                    self.pearson_matrix[i - 1, j - 1] = np.nan
        gc.collect()

    def save_matrix_to_file(self, filename):
        np.savetxt(filename, self.pearson_matrix, delimiter=',', header=','.join(self.channel_labels),
                   fmt='%.4f')

    def plot_heatmap(self):
        plt.figure(figsize=(10, 8))
        sns.heatmap(self.pearson_matrix, annot=True, fmt=".4f", xticklabels=self.channel_labels,
                    yticklabels=self.channel_labels, cmap='coolwarm',
                    cbar_kws={'label': 'Pearson Coefficient (-1 to 1)'}, vmin=-1, vmax=1)
        plt.title('Pearson Correlation Matrix')
        plt.tight_layout()
        plt.show()






