import numpy as np
from PIL import Image
import imageio.v3 as iio  # imageio v3+ cho phép dùng imread tương tự scipy

def preprocess_input(x, v2=True):
    x = x.astype('float32') / 255.0
    if v2:
        x = (x - 0.5) * 2.0
    return x

def _imread(image_path):
    return iio.imread(image_path)  # imageio v3

def _imresize(image_array, size):
    image = Image.fromarray(image_array)
    image = image.resize(size, Image.ANTIALIAS)
    return np.asarray(image)

def to_categorical(integer_classes, num_classes=2):
    integer_classes = np.asarray(integer_classes, dtype='int')
    num_samples = integer_classes.shape[0]
    categorical = np.zeros((num_samples, num_classes))
    categorical[np.arange(num_samples), integer_classes] = 1
    return categorical
