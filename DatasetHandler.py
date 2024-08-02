import gzip
import pickle
import torch
from torch.utils.data import Dataset, DataLoader
import time

class DatasetHandler(Dataset):
    def __init__(self, terminal,  transform=None, target_transform=None):
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
            if isinstance(val, float):
                float_values.append(val)
            else:
                string_values.append(val)

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

    def save_dataset(self, filepath):
        with gzip.open(filepath, 'wb') as f:
            pickle.dump(self.data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def append(self, new_data):
        for ins in new_data:
            trans_line = []
            for item in ins:
                try:
                    float_val = float(item)
                    trans_line.append(float_val)
                except ValueError:
                    trans_line.append(item)
            self.data.append(tuple(trans_line))

    def show_dataset(self, data):
        if data:
            for i in data:
                self.terminal.append(data[i])
                time.sleep(0.1)
        self.terminal.append("Error while displaying dataset!")
    def load_dataset(self , filepath, transform=None, target_transform=None):
        with gzip.open(filepath, 'rb') as f:
            data = pickle.load(f)
        print("loading done")
        self.show_dataset(data)
        # return cls(data=data, transform=transform, target_transform=target_transform)
