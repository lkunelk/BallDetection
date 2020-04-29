import os
import torch
import numpy as np
from model import CNN, init_weights
from my_dataset import initialize_loader
from train import Trainer
import cv2
import util
import torchvision
from PIL import Image
from model import find_batch_bounding_boxes, Label

def train_model():
    experiment = {
        'seed': 1,
        'model_kernel': 3,
        'model_num_features': 16,
        'model_dropout_rate': 0.0,
        'train_class_weight': [.2, .1, .7],  # BALL, ROBOT, OTHER
        'train_learn_rate': 1e-2,
        'train_weight_decay': 0e-7,
        'train_batch_size': 16,
        'train_epochs': 20,
        'colour_jitter': [0.3, 0.3, 0.3, 0],  # brightness, contrast, saturation, hue
        'output_folder': 'outputs',
    }

    valid_final_losses = []
    test_final_losses = []
    test_precision = []
    test_recall = []
    for i in range(1):
        model = CNN(
            kernel=experiment['model_kernel'],
            num_features=experiment['model_num_features'],
            dropout=experiment['model_dropout_rate'])

        # Save directory
        output_folder = experiment['output_folder']
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        model.apply(init_weights)
        #model.load_state_dict(torch.load('outputs/model'))

        trainer = Trainer(model,
                          learn_rate=experiment['train_learn_rate'],
                          weight_decay=experiment['train_weight_decay'],
                          batch_size=experiment['train_batch_size'],
                          epochs=experiment['train_epochs'],
                          colour_jitter=experiment['colour_jitter'],
                          output_folder=experiment['output_folder'],
                          seed=experiment['seed'],
                          class_weights=experiment['train_class_weight'])
        trainer.train()

        valid_final_losses.append(trainer.valid_losses[-2])
        test_final_losses.append(trainer.valid_losses[-1])
        test_precision.append(trainer.precision)
        test_recall.append((trainer.recall))

    print(valid_final_losses)
    print(test_final_losses)
    print('valid mean loss:', np.mean(valid_final_losses), ', std:', np.std(valid_final_losses))
    print('test mean loss: ', np.mean(test_final_losses), ', std:', np.std(test_final_losses))
    print(test_precision)
    print(test_recall)
    print('test precision:', np.mean(test_precision), ', std:', np.std(test_precision))
    print('test recall: ', np.mean(test_recall), ', std:', np.std(test_recall))

    print(experiment)

    torch.save(model.state_dict(), 'outputs/model')


def display_dataset():
    model = CNN(kernel=3, num_features=16)
    model.load_state_dict(torch.load('outputs/model'))
    model.eval()
    [trainl, _, _], [traind, testd] = initialize_loader(6, num_workers=1, shuffle=False)
    testd.visualize_images(delay=10, model=model, start=0)


def test_model():
    model = CNN(kernel=3, num_features=10, dropout=0.2)
    model.cuda()
    model.load_state_dict(torch.load('outputs/model'))
    trainer = Trainer(model, 0.01, 1, 20, 'outputs')
    trainer.test_model('test')


def webcam():
    model = CNN()
    model.load_state_dict(torch.load('outputs/model'))
    # model.cuda()

    transform = torchvision.transforms.Compose([
        torchvision.transforms.ToPILImage(),
        torchvision.transforms.Resize(150, interpolation=Image.BILINEAR),
        torchvision.transforms.CenterCrop((150, 200)),
        # torchvision.transforms.
        torchvision.transforms.ToTensor()
    ])

    cap = cv2.VideoCapture(0)
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            img = transform(frame)
            img_batch = img.unsqueeze(0)
            outputs, _ = model(img_batch)
            bbxs = find_batch_bounding_boxes(outputs)[0]
            img = util.draw_bounding_boxes(img, bbxs[Label.ROBOT.value], (0, 0, 255))
            img = util.draw_bounding_boxes(img, bbxs[Label.BALL.value], (255, 0, 0))
            util.stream_image(img, wait=25, scale=4)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    webcam()
