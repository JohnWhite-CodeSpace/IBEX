import gzip
import pickle
import torch
from torch.utils.data import Dataset, DataLoader


class DatasetHandler(Dataset):
    def __init__(self, datapath=None, data=None, transform=None, target_transform=None):
        super().__init__()
        self.data = []
        self.datapath = datapath
        self.transform = transform
        self.target_transform = target_transform
        if datapath:
            with open(datapath) as dataset:
                for line in dataset.readlines():
                    temp = line.strip().split(',')
                    trans_line = []
                    for ins in temp:
                        try:
                            float_val = float(ins)
                            trans_line.append(float_val)
                        except ValueError:
                            trans_line.append(ins)
                    self.data.append(tuple(trans_line))
        elif data:
            self.data = data

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

    @classmethod
    def load_dataset(cls, filepath, transform=None, target_transform=None):
        with gzip.open(filepath, 'rb') as f:
            data = pickle.load(f)
        return cls(data=data, transform=transform, target_transform=target_transform)
