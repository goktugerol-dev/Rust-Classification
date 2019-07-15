# =============================================================================
# this file holds the model trained on colab were VGG19 was used to train on our dataset
# =============================================================================



"""Rust Classification

Automatically generated by Colaboratory.

"""

import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing.image import ImageDataGenerator
print(tf.__version__)

"""## Setup Input Pipeline

Download the Rust dataset from my drive
"""

from google.colab import drive
drive.mount('/gdrive')
# %cd /gdrive

# =============================================================================
#   this part of the code was used in colab to unzip the dataset into folders given that its 
#   now a py file on our local machine this was commented
#import zipfile
# local_zip = '/gdrive/My Drive/rustimages/dataset.zip'
# zip_ref = zipfile.ZipFile(local_zip, 'r')
# zip_ref.extractall('/tmp')
# zip_ref.close()
# 
# local_zip = '/gdrive/My Drive/rustimages/testt.zip' 
# zip_ref = zipfile.ZipFile(local_zip, 'r')
# zip_ref.extractall('/tmp2')
# zip_ref.close()
# 
# =============================================================================


TRAINING_DIR = "/dataset/"

"""Use `ImageDataGenerator` to rescale the images.

Create the train generator and specify where the train dataset directory, image size, batch size.

Create the validation generator with similar approach as the train generator with the flow_from_directory() method.
"""

train_datagen = ImageDataGenerator(
      rotation_range=20,
      width_shift_range=0.2,
      height_shift_range=0.2,
      zoom_range=0.2,
      horizontal_flip=True,
      fill_mode='nearest',
      validation_split = 0.3)



train_generator = train_datagen.flow_from_directory(TRAINING_DIR,
                                                    batch_size=60,
                                                    class_mode='categorical',
                                                    target_size=(224, 224),
                                                    subset='training')


validation_generator = train_datagen.flow_from_directory(TRAINING_DIR,
                                                              batch_size=60,
                                                              class_mode='categorical',
                                                              target_size=(224, 224),
                                                              subset='validation')


for image_batch, label_batch in train_generator:
  break
image_batch.shape, label_batch.shape

"""Save the labels in a file which will be downloaded later."""

print (train_generator.class_indices)

labels = '\n'.join(sorted(train_generator.class_indices.keys()))



"""Create the base model from the pre-trained convnets

Create the base model from the **VGG19**  

 VGG-19 is a convolutional neural network that is trained on more than a million images from the
 ImageNet database. The network is 19 layers deep and can classify images into 1000 object categories,
 such as keyboard, mouse, pencil, and many animals. As a result, the network has learned rich feature
 representations for a wide range of images. The network has an image input size of 224-by-224

ImageNet dataset is a large dataset of 1.4M images and 1000 classes of web images.

 First, pick which intermediate layer will be used for feature extraction. A common practice is
 to use the output of the very last layer before the flatten operation, the so-called
 "bottleneck layer". The reasoning here is that the following fully-connected layers will be too 
 specialized to the task the network was trained on, and thus the features learned by these layers 
 won't be very useful for a new task. The bottleneck features, however, retain much generality.

Let's instantiate a new model pre-loaded with weights trained on ImageNet.
 By specifying the `include_top=False` argument, we load a network that doesn't include 
 the classification layers at the top, which is ideal for feature extraction.
"""

IMG_SHAPE = (224, 224, 3)

# Create the base model from the pre-trained model VGG19
base_model = tf.keras.applications.vgg19.VGG19(input_shape=IMG_SHAPE,
                                              include_top=False, 
                                              weights='imagenet')

"""Feature extraction
You will freeze the convolutional base created from the previous step and use that as a 
feature extractor, add a classifier on top of it and train the top-level classifier.
"""

base_model.trainable = False

"""### Add a classification head"""

model = tf.keras.Sequential([
  base_model,
  tf.keras.layers.Conv2D(32, 3, activation='relu'),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.GlobalAveragePooling2D(),
  tf.keras.layers.Dense(2, activation='softmax')
])

"""### Compile the model

You must compile the model before training it.  Since there are two classes, use a
 binary cross-entropy loss.
"""

model.compile(optimizer=tf.keras.optimizers.Adam(), 
              loss='binary_crossentropy', 
              metrics=['accuracy'])

model.summary()

print('Number of trainable variables = {}'.format(len(model.trainable_variables)))

from tensorflow import keras

callbacks = [
    keras.callbacks.EarlyStopping(
        # Stop training when `val_loss` is no longer improving
        monitor='val_loss',
        # "no longer improving" being defined as "no better than 1e-2 less"
        min_delta=1e-3,
        # "no longer improving" being further defined as "for at least 2 epochs"
        patience=10,
        verbose=1)
]

"""### Train the model

<!-- TODO(markdaoust): delete steps_per_epoch in TensorFlow r1.14/r2.0 -->
"""

epochs = 100

history = model.fit(train_generator, 
                    epochs=epochs,
                    callbacks = callbacks,
                    validation_data=validation_generator)

"""### Learning curves

Let's take a look at the learning curves of the training and validation accuracy/loss
 when using the MobileNet V2 base model as a fixed feature extractor.
"""

acc = history.history['acc']
val_acc = history.history['val_acc']

loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([min(plt.ylim()),1])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0,1.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.show()

"""## Fine tuning
In our feature extraction experiment, you were only training a few layers on top of an 
VGG19 base model. The weights of the pre-trained network were **not** updated during training.

One way to increase performance even further is to train (or "fine-tune") the weights of the top
layers of the pre-trained model alongside the training of the classifier you added. The training
 process will force the weights to be tuned from generic features maps to features associated 
 specifically to our dataset.

### Un-freeze the top layers of the model

All you need to do is unfreeze the `base_model` and set the bottom layers be un-trainable.
 Then, recompile the model (necessary for these changes to take effect), and resume training.
"""

base_model.trainable = True

# Let's take a look to see how many layers are in the base model
print("Number of layers in the base model: ", len(base_model.layers))

# Fine tune from this layer onwards
fine_tune_at = 0

# Freeze all the layers before the `fine_tune_at` layer
for layer in base_model.layers[:fine_tune_at]:
  layer.trainable =  False

"""### Compile the model

Compile the model using a much lower training rate.
"""

model.compile(loss='categorical_crossentropy',
              optimizer = tf.keras.optimizers.Adam(1e-5),
              metrics=['accuracy'])

model.summary()

print('Number of trainable variables = {}'.format(len(model.trainable_variables)))

"""### Continue Train the model"""

history_fine = model.fit(train_generator, 
                         epochs=200,
                         callbacks = callbacks,
                         validation_data=validation_generator)

acc = history_fine.history['acc']
val_acc = history_fine.history['val_acc']

loss = history_fine.history['loss']
val_loss = history_fine.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([-1,1])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([-1,1.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.show()




test_datagen = ImageDataGenerator()

test_generator = test_datagen.flow_from_directory(
    "/test/",
    batch_size=1,
    class_mode='categorical',
    target_size=(224, 224))

predict = model.evaluate_generator(test_generator,steps = 20)

print(predict)

print(model.metrics_names)

modelSaveName = 'VGG19_Model.h5'
path = F"/models/"+modelSaveName 
model.save(path)

predictions = model.predict(test_generator)
print(model.evaluate(test_generator))

# Print our model's predictions.
print(np.argmax(predictions, axis=1)) 
print (train_generator.class_indices)