import gzip
import pickle
import torch
import numpy as np
from torch.utils.data import Dataset
import time


def convert_hex_flag_to_int(hex):
    return int(hex, 16)


class DatasetHandler(Dataset):
    def __init__(self, terminal, transform=None, target_transform=None):
        super().__init__()
        self.data = []
        self.transform = transform
        self.target_transform = target_transform
        self.terminal = terminal

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        temp = self.data[idx]
        float_values = []
        string_values = []

        for val in temp:
            if isinstance(val, torch.Tensor):
                val = val.item() if val.numel() == 1 else val.tolist()
            if isinstance(val, (int, float)):
                float_values.append(val)
            elif isinstance(val, str):
                string_values.append(val)
            else:
                self.terminal.append(f"Unexpected data type found in dataset: {type(val)}")

        sample = {
            'float_values': torch.tensor(float_values, dtype=torch.float),
            'string_values': string_values
        }

        if self.transform:
            sample['float_values'] = self.transform(sample['float_values'])
        if self.target_transform:
            sample['string_values'] = self.target_transform(sample['string_values'])

        return sample

    def getitem(self, idx):
        return self.data[idx]

    def create_batch(self, start_idx, stop_idx):
        batch = self.data[start_idx:stop_idx]
        return batch

    # def save_dataset(self, filepath):
    #     try:
    #         with gzip.open(filepath, 'wb') as f:
    #             pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)
    #         self.terminal.append(f"Dataset saved to {filepath}")
    #     except Exception as e:
    #         self.terminal.append(f"Error saving dataset: {e}")

    def save_dataset(self, filepath,):
        try:
            torch.save(self.data, filepath)
            self.terminal.append(f"Dataset successfully saved to {filepath}.")
        except (OSError, IOError) as e:
            self.terminal.append(f"Error saving dataset to {filepath}: {e}")
        except Exception as e:
            self.terminal.append(f"An unexpected error occurred: {e}")

    def append(self, new_data):
        for ins in new_data:
            trans_line = []
            for item in ins:
                try:
                    float_val = float(item)
                    trans_line.append(float_val)
                except ValueError:
                    try:
                        hex_val = convert_hex_flag_to_int(item)
                        trans_line.append(float(hex_val))
                    except ValueError:
                        trans_line.append(item)
            self.data.append(torch.tensor(trans_line, dtype=torch.float))

    # def show_dataset(self):
    #     if self.data:
    #         for entry in self.data:
    #             self.terminal.append(str(entry))
    #             time.sleep(0.1)
    #     else:
    #         self.terminal.append("No data to display!")

    def unpack_dataset(self, name):
        try:
            self.data = torch.load(name)
            self.terminal.append(f"Dataset loaded from {name}:")
            self.print_dataset_contents()
        except Exception as e:
            self.terminal.append(f"Error loading dataset: {e}")

    def print_dataset_contents(self):
        try:
            max_items_to_print = min(len(self.data), 20)
            for i in range(max_items_to_print):
                data = self.data[i]
                data_str = data.cpu().numpy().tolist() if isinstance(data, torch.Tensor) else str(data)
                self.terminal.append(f"Item {i + 1}: {data_str}")
            if len(self.data) > 20:
                self.terminal.append(f"... and {len(self.data) - 20} more items not shown.")
        except Exception as e:
            self.terminal.append(f"Error printing dataset contents: {str(e)}")
