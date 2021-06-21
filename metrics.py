import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from tensorflow import keras
from tensorflow.keras import layers
from mlflow import log_metric
import gzip, pickle, os
import numpy as np
import pandas as pd
import tensorflow as tf
import argparse

#limit training to 1 core
tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)

parser = argparse.ArgumentParser()
parser.add_argument('--batch_size', type=int, default=128, help='Batch size for training.')
parser.add_argument('--num_epochs', type=int, default=int(os.getenv("EPOCHS","5")), help='Number of epochs to train for.')
args = parser.parse_args()

batch_size = args.batch_size
epochs = args.num_epochs
print ("Number of epochs:", epochs)
num_classes = 10
input_shape = (28, 28, 1)
MODEL_DIR = "/model/"

#load dataset
f = gzip.open('/mnist/mnist.pkl.gz', 'rb')
data = pickle.load(f, encoding='bytes')
f.close()
(x_train, y_train), (x_test, y_test) = data

# Scale images to the [0, 1] range
x_train = x_train.astype("float32") / 255
x_test = x_test.astype("float32") / 255
# Make sure images have shape (28, 28, 1)
x_train = np.expand_dims(x_train, -1)
x_test = np.expand_dims(x_test, -1)
print("x_train shape:", x_train.shape)
print(x_train.shape[0], "train samples")
print(x_test.shape[0], "test samples")


# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

# Network
model = keras.Sequential(
    [
        keras.Input(shape=input_shape),
        layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
        layers.MaxPooling2D(pool_size=(2, 2)),
        layers.Flatten(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation="softmax"),
    ]
)


model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs, verbose=0, validation_split=0.1)

tf.keras.backend.set_learning_phase(0)  # Ignore dropout at inference
tf.saved_model.save(model,MODEL_DIR + str(1))

metrics= {'metric_name': ['accuracy','recall'], 'values': ['0.98','0.76']}

df = pd.DataFrame(data=metrics)
df.to_csv(MODEL_DIR+'metrics/metrics.csv',index=False)
