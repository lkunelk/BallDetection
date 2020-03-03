from torch.utils.data import Dataset, DataLoader
import os
import cv2
import numpy as np
import torchvision
import matplotlib.pyplot as plt
from PIL import Image

train_path = '/home/nam/Desktop/bit-bots-ball-dataset-2018/train'
negative_path = '/home/nam/Desktop/bit-bots-ball-dataset-2018/negative'
test_path = '/home/nam/Desktop/bit-bots-ball-dataset-2018/test'


def initialize_loader(train_batch_size=2, validation_batch_size=64):
    transform = torchvision.transforms.Resize((150, 200))
    train_folders = [os.path.join(train_path, folder) for folder in os.listdir(train_path)]
    test_folders = [os.path.join(train_path, folder) for folder in os.listdir(train_path)]
    train_dataset = MyDataSet(train_folders, transform=transform)
    valid_dataset = MyDataSet(test_folders)
    train_loader = DataLoader(train_dataset, batch_size=train_batch_size, num_workers=4, shuffle=True, drop_last=True)
    test_loader = DataLoader(train_dataset, batch_size=train_batch_size, num_workers=4, shuffle=True, drop_last=True)
    return train_loader, test_loader


def display_image(img, y):
    '''
    :param img: torch tensor channelxWxH
    :param y: bounding rectangle 4-vector [x1, y1, x2, y2]
    :return: None
    '''
    img = img.numpy()
    img = np.rollaxis(img, 0, 3)  # HxWxchannel

    fig, ax = plt.subplots(1, 2)
    ax[0].imshow(img)
    ax[1].imshow(y, cmap='gray')
    plt.show()


def read_image(path):
    img = Image.open(path)
    # img = resize(img, (150, 200, 3))
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # img = np.rollaxis(img, 2)  # flip to channel*W*H
    return img


class MyDataSet(Dataset):
    def __init__(self, file_paths, transform=None):
        self.file_paths = file_paths
        self.valid_filenames = []
        self.transform = transform

        # add paths for train data with labels
        for path in file_paths:
            # find txt file with labels
            file_labels = None
            for file in os.listdir(path):
                if '.txt' in file:
                    file_labels = os.path.join(path, file)

            # store full path with label for each image
            with open(file_labels) as labels:
                for i, line in enumerate(labels):
                    if i > 5:  # ignore first few metadata lines
                        label, img, _, _, x1, y1, x2, y2, _, _, _, _ = line.split('|')
                        assert label == 'label::ball'
                        img_path = os.path.join(path, img)
                        self.valid_filenames.append([
                            img_path,
                            [(int(x1), int(y1)), (int(x2), int(y2))]
                        ])

        # add paths for negative examples (no ball in picture)
        for file in os.listdir(negative_path):
            img_path = os.path.join(negative_path, file)
            self.valid_filenames.append((img_path, [(0, 0), (0, 0)]))

    def __len__(self):
        return len(self.valid_filenames)

    def __getitem__(self, index):
        img_path, label = self.valid_filenames[index]
        img = read_image(img_path)

        if self.transform:
            img = self.transform(img)
        img = np.array(img)

        mask = np.zeros((150, 200))
        pt1 = np.array(label[0]) / 4
        pt2 = np.array(label[1]) / 4
        center = tuple(((pt1 + pt2) / 2).astype(np.int))
        size = tuple(((pt2 - pt1) / 2).astype(np.int))
        if not size == (0, 0):
            mask = cv2.ellipse(mask, center, size, 0, 0, 360, (255), -1)

        img = np.rollaxis(img, 2)  # flip to channel*W*H
        return img, mask
