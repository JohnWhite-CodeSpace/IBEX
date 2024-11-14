import torch
import os
import numpy as np
from matplotlib import pyplot as plt
import gc


class PearsonsMatrixCreator:

    def __init__(self, terminal, hi_instruction_file, lo_instruction_file):
        self.data_container = None
        data_container = None
        self.terminal = terminal
        self.visuals = False
        self.save_to_file = False
        self.Hi_instruction_file = hi_instruction_file
        self.Lo_instruction_file = lo_instruction_file
        self.Hi_channel_encoding_list = {11, 12, 13, 14, 15, 16}
        self.Lo_channel_encoding_list = {21, 22, 23, 24, 25, 26, 27, 28, 41, 42, 43, 44, 45, 46, 47, 48}

    def set_visuals(self, visuals):
        self.visuals = visuals

    def set_save_option(self, save_option):
        self.save_to_file = save_option

    def load_data(self, path):
        try:
            self.terminal.append(f"Loading {path} dataset...")
            self.data_container = torch.load(path)
            self.terminal.append(f"{path} dataset successfully loaded")
        except FileNotFoundError as e:
            self.terminal.append(f"File not found: {e}")
        except RuntimeError as e:
            self.terminal.append(f"Runtime error: {e}")
        except MemoryError as e:
            self.terminal.append(f"Memory error: {e}")
        except Exception as e:
            self.terminal.append(f"An unexpected error occurred while loading data: {e}")
        finally:
            gc.collect()

    def load_instruction_file(self, instruction_file):
        try:
            return np.loadtxt(instruction_file, dtype='str')
        except FileNotFoundError as e:
            self.terminal.append(f"File not found: {e}")

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

    def pearsons_coefficient_algorithm(self, X_vals, Y_vals):
        covXY = np.cov(X_vals, Y_vals)
        std_dev_X = np.std(X_vals)
        std_dev_Y = np.std(Y_vals)
        return covXY / (std_dev_X * std_dev_Y)

    def search_algorithm(self, data_container, instruction_file):
        if instruction_file == "HiCullGoodTimes.txt":
            inst_line_len = 14
            for i in range(len())
        elif instruction_file == "LoGoodTime.txt":
            inst_line_len = 13


