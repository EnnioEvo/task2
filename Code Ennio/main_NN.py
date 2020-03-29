import numpy as np
import pandas as pd
import scipy as sp
from keras.models import Sequential
from keras.layers import Dense
from keras import optimizers
from keras import metrics
from keras.datasets import mnist
from sklearn.metrics import classification_report, confusion_matrix

model =Sequential()
model.add(Dense(units=20, activation='relu', input_dim=50))
model.add(Dense(units=10, activation='softmax'))
sgd =optimizers.SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='mean_squared_error', optimizer=sgd, metrics =[metrics.mae, metrics.categorical_accuracy])
(x_train, y_train),(x_test, y_test) = mnist.load_data()
model.fit(x_train, y_train, batch_size=32, epochs=5,validation_split=0.2, shuffle=True)

# Data import from folder
X_train_raw = sp.array(pd.read_csv("../data/train_features.csv"), dtype=sp.float64)
Y_train = sp.array(pd.read_csv("../data/train_labels.csv"), dtype=sp.float64)
test_features = sp.array(pd.read_csv("../data/test_features.csv"), dtype=sp.float64)

X_train = X_train_raw
X_train[np.isnan(X_train_raw)]= 0
X_train = X_train[0:1000,:]
Y_train = X_train[:,1]
