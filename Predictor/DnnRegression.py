import tensorflow as tf
from keras.models import Sequential
from keras.models import model_from_json
from keras.layers.core import Dense #, Activation, Dropout
from keras.layers import LeakyReLU
from keras.regularizers import l1

import numpy as np

class DnnRegression:
    def __init__(self):
        self.model = Sequential()
        self.count = 0

    def build_model(self, input_dim, hidden_layers, learning_rate=0.001):
        self.model.add(Dense(hidden_layers[0], input_dim=input_dim))
        self.model.add(LeakyReLU(alpha=.02))
        # self.model.add(tf.nn.leaky_relu)
        for nodes in hidden_layers[1:]:
            self.model.add(Dense(nodes))
            self.model.add(LeakyReLU(alpha=.02))
            # self.model.add(tf.nn.leaky_relu)
        self.model.add(Dense(1, activity_regularizer=l1(0.01)))
        # self.model.add(BatchNormalization())
        self.model.add(LeakyReLU(alpha=.02))
        # self.model.add(tf.nn.leaky_relu)
        self.model.compile(loss='mse', optimizer=tf.train.AdamOptimizer(learning_rate=0.001))

    def train(self, X, Y, step, batch, verbose=2):
        self.model.fit(X, Y, batch_size=batch, epochs=step, verbose=2)

    def evaluate(self, X, Y):
        mse = self.model.evaluate(X, Y)
        return mse

    def predict(self, X, batch_size=None):
        self.count += 1
        if batch_size is None:
            batch_size = 1
        X = np.array([X])
        # st = tm.time()
        results = self.model.predict(X, batch_size)
        # print('predict time', tm.time()-st, 'seconds ')
        return results[0][0]

    def save(self, file_name):
        model_json = self.model.to_json()
        with open(file_name+'.json', "w") as json_file:
            json_file.write(model_json)
        # serialize weights to HDF5
        self.model.save_weights(file_name + ".h5")
        print("Saved model to disk")

    def load(self, file_name):
        json_file = open(file_name+'.json', 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        self.model = tf.keras.models.model_from_json(loaded_model_json)
        # load weights into new model
        self.model.load_weights(file_name + ".h5")
        # print(file_name)
        # for layers in self.model.layers:
        #     print(layers.get_weights())
        # print("Loaded model from disk")

