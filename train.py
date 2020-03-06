import math

import numpy as np
from keras.applications.resnet50 import (ResNet50, decode_predictions,
                                         preprocess_input)
from keras.applications.inception_v3 import preprocess_input
from keras.callbacks import (EarlyStopping, LearningRateScheduler,
                             ModelCheckpoint, ReduceLROnPlateau)
from keras.initializers import glorot_uniform
from keras.layers import (Activation, Add, AveragePooling2D,
                          BatchNormalization, Conv2D, Dense, Dropout, Flatten,
                          Input, MaxPooling2D, ZeroPadding2D)
from keras.models import Model
from keras.optimizers import Adam
from keras.preprocessing import image
from keras.preprocessing.image import ImageDataGenerator
from keras.utils import plot_model

from util import Utility


def train(model, X_train, Y_train, X_test, Y_test, num_epochs, batch_size, data_augmentation=False):
    util = Utility()

    # Compile the model
    model.compile(optimizer=Adam(lr=util.lr_schedule(0), epsilon=1e-8),
                  loss='categorical_crossentropy', metrics=['accuracy'])

    modelCheckpoint = ModelCheckpoint(filepath=util.getModelPath(
    ), monitor='val_acc', verbose=1, save_best_only=True)
    learningRateScheduler = LearningRateScheduler(util.lr_schedule)
    lrReducer = ReduceLROnPlateau(factor=np.sqrt(
        0.1), cooldown=0.0, patience=5, min_lr=0.5e-6)
    #earlyStop = EarlyStopping(monitor='val_loss', patience=5, min_delta=1e-3,restore_best_weights=True,mode='auto')

    # Prepare callbacks
    callbacks = [modelCheckpoint, learningRateScheduler, lrReducer]
    if not data_augmentation:
        print('Not using data augmentation.')
        # Train the model
        model.fit(X_train, Y_train, epochs=num_epochs, batch_size=batch_size,
                  validation_data=(X_test, Y_test), shuffle=True, callbacks=callbacks)
    else:
        print('Using real-time data augmentation.')
        # This will do preprocessing and realtime data augmentation:
        datagen = ImageDataGenerator(
            # set input mean to 0 over the dataset
            featurewise_center=False,
            # set each sample mean to 0
            samplewise_center=False,
            # divide inputs by std of dataset
            featurewise_std_normalization=False,
            # divide each input by its std
            samplewise_std_normalization=False,
            # apply ZCA whitening
            zca_whitening=False,
            # epsilon for ZCA whitening
            zca_epsilon=1e-06,
            # randomly rotate images in the range (deg 0 to 180)
            rotation_range=0,
            # randomly shift images horizontally
            width_shift_range=0.1,
            # randomly shift images vertically
            height_shift_range=0.1,
            # set range for random shear
            shear_range=0.,
            # set range for random zoom
            zoom_range=0.,
            # set range for random channel shifts
            channel_shift_range=0.,
            # set mode for filling points outside the input boundaries
            fill_mode='nearest',
            # value used for fill_mode = "constant"
            cval=0.,
            # randomly flip images
            horizontal_flip=True,
            # randomly flip images
            vertical_flip=False,
            # set rescaling factor (applied before any other transformation)
            rescale=None,
            # set function that will be applied on each input
            preprocessing_function=None,
            # image data format, either "channels_first" or "channels_last"
            data_format=None,
            # fraction of images reserved for validation (strictly between 0 and 1)
            validation_split=0.0)

        # Compute quantities required for featurewise normalization
        # (std, mean, and principal components if ZCA whitening is applied).
        datagen.fit(X_train)

        # Fit the model on the batches generated by datagen.flow().
        model.fit_generator(datagen.flow(X_train, Y_train, batch_size=batch_size),
                            validation_data=(X_test, Y_test),
                            epochs=num_epochs, verbose=1, workers=4,
                            callbacks=callbacks,
                            steps_per_epoch=math.ceil(len(X_train) / batch_size))

    # Evaluate the model
    _, test_acc = model.evaluate(X_test, Y_test)
    print("Accuracy on the test set: " + str(test_acc * 100) + "%")


def trainRaw(model, trainDir, valDir, epochs):
    model.compile(
        Adam(lr=0.01), loss="sparse_categorical_crossentropy", metrics=['accuracy'])

    trainDataGen = ImageDataGenerator(rescale=1./255,
                                      preprocessing_function=preprocess_input,
                                      rotation_range=40,
                                      width_shift_range=0.2,
                                      height_shift_range=0.2,
                                      shear_range=0.2,
                                      zoom_range=0.2,
                                      horizontal_flip=True,
                                      fill_mode='nearest')
    trainGenerator = trainDataGen.flow_from_directory(trainDir,
                                                      batch_size=32,
                                                      class_mode="sparse",
                                                      target_size=(150, 150))
    valDataGen = ImageDataGenerator(rescale=1./255)
    valGenerator = valDataGen.flow_from_directory(valDir,
                                                  batch_size=32,
                                                  class_mode="sparse",
                                                  target_size=(150, 150))

    history = model.fit_generator(
        trainGenerator, epochs=epochs, verbose=1, validation_data=valGenerator, steps_per_epoch=100,validation_steps=50)

    return history
