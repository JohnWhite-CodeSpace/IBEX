import torch
import os
import numpy as np
from matplotlib import pyplot as plt
import gc


class PearsonsMatrixCreator:

    def __init__(self, terminal, hi_instruction_file, lo_instruction_file):
        self.data_container = None
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

    def calculate_and_save_pearsons_matrix(self, hi_tensor_directory, lo_tensor_directory):
        # Helper function to load tensor and split based on encoding list
        def process_tensor(tensor_directory, encoding_list, save_dir, group_pairs=False):
            # Load the main tensor
            main_tensor = torch.load(os.path.join(tensor_directory, os.listdir(tensor_directory)[0]))

            # Convert the encoding list to integers (assuming hexadecimal representation)
            encoding_ints = [int(encoding, 16) for encoding in encoding_list]

            # Create a directory to save the split tensors
            os.makedirs(save_dir, exist_ok=True)

            # Grouping flag
            paired_tensors = {}

            # Iterate over the unique encoding integers and split the tensor
            for encoding in encoding_ints:
                matching_tensor = main_tensor[main_tensor[:, 4] == encoding]

                # Group Lo channels if needed
                if group_pairs and encoding < 30:  # assuming 21-28 and 41-48
                    pair_encoding = encoding + 20  # match 21 with 41, 22 with 42, etc.
                    pair_tensor = main_tensor[main_tensor[:, 4] == pair_encoding]

                    # Combine the tensors
                    combined_tensor = torch.cat((matching_tensor, pair_tensor), dim=0)
                    paired_tensors[encoding] = combined_tensor

                    # Remove the pair from the encoding list to avoid duplication
                    encoding_ints.remove(pair_encoding)
                else:
                    # Save the tensor directly
                    paired_tensors[encoding] = matching_tensor

            # Save the split tensors
            for encoding, tensor in paired_tensors.items():
                tensor_save_path = os.path.join(save_dir, f"tensor_{encoding}.pt")
                torch.save(tensor, tensor_save_path)
                self.terminal.append(f"Saved tensor for encoding {encoding} to {tensor_save_path}")

            # Free space using garbage collector
            del main_tensor, paired_tensors
            gc.collect()

        # Process Hi tensors
        hi_save_dir = os.path.join(hi_tensor_directory, "split_tensors")
        process_tensor(hi_tensor_directory, self.Hi_channel_encoding_list, hi_save_dir)

        # Process Lo tensors, with grouping for pairs (21,41), (22,42), ...
        lo_save_dir = os.path.join(lo_tensor_directory, "split_tensors")
        process_tensor(lo_tensor_directory, self.Lo_channel_encoding_list, lo_save_dir, group_pairs=True)

        # Indicate completion
        self.terminal.append("Tensors split and saved successfully.")






