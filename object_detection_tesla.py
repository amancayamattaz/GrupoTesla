# -*- coding: utf-8 -*-
"""Object_Detection_Tesla.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1A4QM1EraL1acal2Q1lTFivDCZuHe_TqQ

# **Laboratory 13:** Object Detection

Object Detection is a challenging computer vision task that involves predicting both where the objects are in the image and what type of objects were detected. Even though this task can also be solved with a model developed from scratch, like image classification, a preferred approach in the computer vision community is to implement and retrain existent DL models for better performance. SSDs, R-CNNs, and YOLOs are among the state-of-the-art models when it comes about object detection. The latest, [YOLO](https://arxiv.org/abs/1506.02640) and its different versions, are  the most known and have evolved to become some of the most chosen object detectors nowadays. 

### History

When Joseph Redmon released the first YOLO version in May 2016, it was a big step forward real-time object detection and, many computer vision developers and researchers dared to implement it getting unrivaled results at that time. He and his team then worked on further enhancements and released two more versions: YOLO v2 and v3. However, after the release of version 3, Joseph Redmon announced that he had decided to stop any further research in this model to avoid the [misuse of the technology](https://analyticsindiamag.com/yolo-creator-joe-redmon-computer-vision-research-ethical-concern/). Against all odds, after three years, Alexey Bochkovskiy released YOLO v4 (April 2020) with the paper “YOLOv4: Optimal Speed and Accuracy of Object Detection”, and it performed much better than v3.

What's more impressive, after a few days of the fourth version release (June 2020), Glenn R. Jocher, Founder & CEO at Ultralytics, proposed a new version called YOLO v5 with several meaningful improvements. Being a researcher out of the main AI labs and not releaseing the fifth version through a regular paper caused many [controversies](https://github.com/AlexeyAB/darknet/issues/5920) to Glenn. Nevertheless, YOLOv5 is currently one of the most reusable networks and have been used as the baseline for YOLO v6 and YOLO v7, which can be trained/used similarly than YOLO v5. 

Even though the model is based on PyTorch, it is that usable and well-documented that does not require to code much with the framework but configure it for good performance. In this lab, we will apply YOLO v5 to the datasets obtained collectively by the course. You can find more tutorials and documentation about the model [here](https://github.com/ultralytics/yolov5). 

### Metrics

Some metrics obtained after applying YOLO v5 to MS COCO. 

<img src="https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F436969%2F44ea6fe6e61f22471be5788407518d7e%2FYOLOv4-performance.png?generation=1595469398768719&alt=media" width="500" align="center" />

## 1. Download the model

This time we will download the model from the official repository because this keeps updating and contains all latest updates. 

**After runnning the next cell, you will have to restart the session. This can be done by pressing 'Restart Runtime'**
"""

# Clone the model 
!git clone https://github.com/ultralytics/yolov5

# install dependencies
!pip install -U -r yolov5/requirements.txt

"""Yolo v5 comes with four main pretrained versions. 

<img src="https://user-images.githubusercontent.com/26833433/103595982-ab986000-4eb1-11eb-8c57-4726261b0a88.png" width="500" align="center" />

This time, we will use Yolov5l because we have only one class in the dataset, and the combined dataset will be relatively large. On the other hand, you can also try the other models if your task is more complex. As you can see, Yolov5x has more precision and is heavier, which might involve difficulties when deploying in limited devices. 
"""

# Commented out IPython magic to ensure Python compatibility.
# Access the yolov5 folder and show the model's architecture
# %cd /content/yolov5
# %cat /content/yolov5/models/yolov5l.yaml

"""## 2. Import main libraries"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil
import random
import cv2
import numpy as np

import torch
from IPython.display import Image  # for displaying images
from sklearn.model_selection import train_test_split

# check if we're using torch with GPU
print('Using torch %s %s' % (torch.__version__, torch.cuda.get_device_properties(0) if torch.cuda.is_available() else 'CPU'))

"""## 3. Download and explore the datasets

So far, we used public datasets to train our models. However, this is sometimes not possible due to different reasons. For example, the dataset for your problem would have not collected yet. Even though there might be related datasets to your problem, you might need something very specific to the problem's context and time. In such cases, you will need to create your dataset. Some good aspects to think of your dataet: 
- Define the setup
- Light conditions
- Variability among instances
- External elements apart from the objects
- The tools (cameras, additional lights, collaborators?). 
- Labelling/annotation tool

You can see a best practices and a comparison of tools based on their functions, cost, and availability [here](https://humansintheloop.medium.com/best-annotation-tools-for-computer-vision-of-2021-38cb0b57a434) and [here](https://blog.superannotate.com/guide-to-data-labeling/?fbclid=IwAR2RhqjTwsucacUChRkMcKSEGtYk_mPt6FY4O7KjQFXqWzLNMFMzSa02Enk). Some of these tools are [Roboflow](https://roboflow.com/) and [Superannotate](https://superannotate.com/), which  are two web platforms with multiple resources to annotate, train, and automate a computer vision pipeline, however, they are not open source, meaning the have limits in their functionalities that you should check first before using them.

This time, we used Roboflow to upload and annotate car instances because this platform has a feature to transform labells into Yolo v5 format. We'll start collecting all datasets labelled by the course according to the [Neighbourhood Assignation spreadsheet](https://docs.google.com/spreadsheets/d/1kio-v3r8qHjvWuG96f4TOm6qHfS_rOECz6QEwiMnjiY/edit?usp=sharing). For the following cell, you'll need to download the spreadsheet as a CSV file and upload it to this notebook. 
"""

# Open Neighbourhood Assignation spreadsheet
data = pd.read_csv("/content/neighbourhood_assignation.csv", index_col="num")
# Remove rows with empty values and reset index
data = data.dropna().reset_index(drop=True)

DATASETS_PATH = "/content/datasets/"
if os.path.exists(DATASETS_PATH):
  shutil.rmtree(DATASETS_PATH)

os.mkdir(DATASETS_PATH)

for idx, sample in data.iterrows():
  download_url = "https://public.roboflow.com/ds/"+sample["dataset_code"]+"?key="+sample["dataset_password"]
  labeller_name = sample["labeller"].split(" ")[0]
  !curl -L "$download_url" > roboflow.zip; unzip roboflow.zip -d "/content/datasets/$labeller_name" > /dev/null; rm roboflow.zip

"""Create a dataframe with all images"""

dataset = pd.DataFrame(columns=["labeller", "neighbourhood", "image", "label"]) 
for idx, sample in data.iterrows():
  labeller_name = sample["labeller"].split(" ")[0]
  for folder in os.listdir("/content/datasets/"+labeller_name):
    if folder in ["train","test","valid"]:
      sub_df = pd.DataFrame(columns=["labeller", "neighbourhood", "image", "label"]) 

      base_path = "/content/datasets/"+labeller_name+"/"+folder
      images = [base_path+"/images/"+image for image in os.listdir(base_path+"/images")]
      labels = [base_path+"/labels/"+label for label in os.listdir(base_path+"/labels")]
      labellers = [sample["labeller"] for val in images]
      hoods = [sample["neighbourhood"] for val in images]

      images.sort()
      labels.sort()

      sub_df["labeller"] = labellers
      sub_df["neighbourhood"] = hoods
      sub_df["image"] = images
      sub_df["label"] = labels

      dataset = pd.concat([dataset, sub_df], sort=False)

dataset = dataset.reset_index(drop=True)
dataset

"""### 3.1 Visualize some samples"""

# Show image with its bounding boxes from annotations in TXT format (Yolo)
def show_image_txt_label(dataset, classes, index): 
  image = cv2.imread(dataset.at[index,"image"])
  image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
  height, width, _ = image.shape

  with open(dataset.at[index,"label"]) as txt:
    lines = txt.readlines()
    for line in lines:
      id = line.split(" ")[0]
      if id!= "\n" and len(id) > 0:
        id = int(id)
        try:
          label = classes[id]
        
          x=float(line.split(" ")[1])
          y=float(line.split(" ")[2])
          w=float(line.split(" ")[3])
          h=float(line.split(" ")[4])

          # Convert Yolo format to rectangular coordinates
          l = int((x - w / 2) * width)
          r = int((x + w / 2) * width)
          t = int((y - h / 2) * height)
          b = int((y + h / 2) * height)

          if l < 0:
            l = 0
          if r > width - 1:
            r = width - 1
          if t < 0:
            t = 0
          if b > height - 1:
            b = height - 1

          font = cv2.FONT_HERSHEY_SIMPLEX
          # Put text
          cv2.putText(image, label,(l,t-10),font,1,(0,255,0),2,cv2.LINE_AA)
          # Draw bounding box
          cv2.rectangle(image, (l, t), (r, b), (0,255,0), 1)
        except:
          print("Error." + dataset.at[index,"labeller"] + " labelled with more than one class")
      else: 
        continue
  plt.rcParams["figure.figsize"] = (8,8) 
  plt.title("Labeller: " + dataset.at[index,"labeller"] + " - Dimensions: "+str(width)+"x"+str(height))
  plt.imshow(image)

classes = {0:"people"}
num = random.randint(0,len(dataset)-1)
show_image_txt_label(dataset, classes, num)

"""### 3.2 Show the number of images/instances per labeller"""

# This function shows the number of images and instances annotated by each participant
def find_labeller_distribution_txt(dataset):
  instances = {}
  images = {}
  for idx, sample in dataset.iterrows():
    if sample["labeller"] not in images.keys(): 
      images[sample["labeller"]] = 1
    else:
      images[sample["labeller"]] += 1


    with open(sample["label"]) as txt:
      lines = txt.readlines()
      for line in lines:
        if sample["labeller"] not in instances.keys(): 
          instances[sample["labeller"]] = 1
        else:
          instances[sample["labeller"]] += 1
  
  fig, ax = plt.subplots(1,2, figsize=(10,3))
  ax[0].bar(instances.keys(),instances.values())
  ax[0].set_xticklabels(labels=instances.keys(), rotation=45)
  ax[1].bar(images.keys(),images.values())
  ax[1].set_xticklabels(labels=images.keys(), rotation=45);

find_labeller_distribution_txt(dataset)

"""### 3.3 Move files"""

NEW_DATASET_PATH = "/content/people_dataset"

if os.path.exists(NEW_DATASET_PATH):
  shutil.rmtree(NEW_DATASET_PATH)

os.mkdir(NEW_DATASET_PATH)

def move_files(subset, subset_name): 
  os.mkdir(NEW_DATASET_PATH+"/"+subset_name)
  os.mkdir(NEW_DATASET_PATH+"/"+subset_name+"/images")
  os.mkdir(NEW_DATASET_PATH+"/"+subset_name+"/labels")
  
  for idx, sample in subset.iterrows():
    # Move images
    file_name = sample["image"].split("/")[6]
    target_file = NEW_DATASET_PATH+"/"+subset_name+"/images/"+file_name
    shutil.copy(sample["image"], target_file)

    # Move labels
    file_name = sample["label"].split("/")[6]
    target_file = NEW_DATASET_PATH+"/"+subset_name+"/labels/"+file_name
    shutil.copy(sample["label"], target_file)

def train_validate_test_split(df, train_percent=.7, validate_percent=.2, seed=None):
    np.random.seed(seed)
    perm = np.random.permutation(df.index)
    m = len(df.index)
    train_end = int(train_percent * m)
    validate_end = int(validate_percent * m) + train_end
    train = df.iloc[perm[:train_end]]
    validate = df.iloc[perm[train_end:validate_end]]
    test = df.iloc[perm[validate_end:]]
    return train, validate, test

print(len(dataset))
train_set, validation_set, test_set = train_validate_test_split(dataset, 0.7, 0.2)

print("Train set size: ", len(train_set), "Validation set size: ", len(validation_set), "Test set:", len(test_set))

move_files(train_set, "train")
move_files(test_set, "test")
move_files(validation_set, "valid")

"""## 4. Modify parameters of the model

Any Roboflow dataset comes with a `.yaml` file that will help us define the location of the training and testing subsets as well as the classes. Nevertheless, we won't use them this time. Let's just visualize it. 
"""

# Commented out IPython magic to ensure Python compatibility.
# Visualise the content of data.yaml
# %cat /content/datasets/Alex/data.yaml

# define the number of classes
num_classes = 1

# IPython is a great tool for interactive shells as Notebooks. It comes with 
# many utilities and we will use register_line_cell_magic
# to overwrite a file directly from a Colab cell. Otherwise, we would need to 
# download and upload the file. We define writetemplate to customize iPython 
# writefile 
from IPython.core.magic import register_line_cell_magic

@register_line_cell_magic
def writetemplate(line, cell):
    with open(line, 'w') as f:
        f.write(cell.format(**globals()))

# Commented out IPython magic to ensure Python compatibility.
# # change the location of the training and validation subsets. The rest
# # of the file remains equal. 
# 
# %%writetemplate /content/yolov5/data.yaml
# 
# train: /content/people_dataset/train/images
# val: /content/people_dataset/valid/images
# test: /content/people_dataset/test/images
# 
# nc: 1
# names: ['people']

# Commented out IPython magic to ensure Python compatibility.
# %cat data.yaml

# Commented out IPython magic to ensure Python compatibility.
# # Change the number of classes defined in the yolo v5 architectures. the rest remains the same. 
# %%writetemplate /content/yolov5/models/custom_yolov5l.yaml
# 
# # Parameters
# nc: {num_classes}  # number of classes
# depth_multiple: 1.0  # model depth multiple
# width_multiple: 1.0  # layer channel multiple
# anchors:
#   - [10,13, 16,30, 33,23]  # P3/8
#   - [30,61, 62,45, 59,119]  # P4/16
#   - [116,90, 156,198, 373,326]  # P5/32
# 
# # YOLOv5 v6.0 backbone
# backbone:
#   # [from, number, module, args]
#   [[-1, 1, Conv, [64, 6, 2, 2]],  # 0-P1/2
#    [-1, 1, Conv, [128, 3, 2]],  # 1-P2/4
#    [-1, 3, C3, [128]],
#    [-1, 1, Conv, [256, 3, 2]],  # 3-P3/8
#    [-1, 6, C3, [256]],
#    [-1, 1, Conv, [512, 3, 2]],  # 5-P4/16
#    [-1, 9, C3, [512]],
#    [-1, 1, Conv, [1024, 3, 2]],  # 7-P5/32
#    [-1, 3, C3, [1024]],
#    [-1, 1, SPPF, [1024, 5]],  # 9
#   ]
# 
# # YOLOv5 v6.0 head
# head:
#   [[-1, 1, Conv, [512, 1, 1]],
#    [-1, 1, nn.Upsample, [None, 2, 'nearest']],
#    [[-1, 6], 1, Concat, [1]],  # cat backbone P4
#    [-1, 3, C3, [512, False]],  # 13
# 
#    [-1, 1, Conv, [256, 1, 1]],
#    [-1, 1, nn.Upsample, [None, 2, 'nearest']],
#    [[-1, 4], 1, Concat, [1]],  # cat backbone P3
#    [-1, 3, C3, [256, False]],  # 17 (P3/8-small)
# 
#    [-1, 1, Conv, [256, 3, 2]],
#    [[-1, 14], 1, Concat, [1]],  # cat head P4
#    [-1, 3, C3, [512, False]],  # 20 (P4/16-medium)
# 
#    [-1, 1, Conv, [512, 3, 2]],
#    [[-1, 10], 1, Concat, [1]],  # cat head P5
#    [-1, 3, C3, [1024, False]],  # 23 (P5/32-large)
# 
#    [[17, 20, 23], 1, Detect, [nc, anchors]],  # Detect(P3, P4, P5)
#   ]

# Commented out IPython magic to ensure Python compatibility.
# %cat models/custom_yolov5l.yaml

"""## 5. Train the model

Training with Yolov5 can be done by using a script named `train.py`, which will require the following parameters:

* **img:** input image size (width == height)
* **batch:** batch size
* **epochs:** number of training epochs. 
* **data:** path to our yaml file
* **cfg:** model configuration
* **weights:** custom path to save the best weights. 
* **name:** output file with metric results
* **nosave:** boolean that specifies to only save the final checkpoint
* **cache:** boolean that specifies to cache images for faster training
"""

# Commented out IPython magic to ensure Python compatibility.
# Since we exported the dataset for Yolo v5, we don't need to resize the images.
# We will train the model for 5 epoch with batch size of 80, however, you can 
# change these parameters to get a better performance
# train.py uses the subsets information from data.yaml. 

# %cd /content/yolov5/
!python train.py --img 416 --batch 16 --epochs 30 --data './data.yaml' --cfg './models/custom_yolov5l.yaml' --weights ''

"""## 6. Evaluate the model

The point of downloading YOLO v5 from Github is that it comes with many scripts for training, evaluating, and ploting results. For instance, the repository includes a great utility class `ConfusionMatrix` that allows you to evaluate your model performance on the last training run:
"""

# Launch after you have started training to all the graphs needed for inspection
# logs are saved in the folder "runs"
from yolov5.utils.metrics import ConfusionMatrix
import cv2

confusion_matrix = ConfusionMatrix(nc=1)

confusion_matrix.plot()

img = cv2.imread("/content/yolov5/confusion_matrix.png")
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

"""Now, we can use the `detect.py` script to run the model inference with the best weights.
- **source:** input images directory or single image path or video path
- **weights:** trained model path
- **conf:** confidence threshold

The following command will process the test images and store them in our inference directory with the predicted bounding boxes.
"""

# Commented out IPython magic to ensure Python compatibility.
# final weights will be stored by default at /content/yolov5/runs/train/exp2/weights/best.pt
# %cd /content/yolov5/

!python detect.py --weights /content/yolov5/runs/train/exp/weights/best.pt --img 64 --conf 0.1 --source /content/people_dataset/test/images

"""Finally, we will use `glob` to find all the path names matching the specified pattern. Then, we will use the display module of IPython to display images easily."""

import glob
from IPython.display import Image, display

for image in glob.glob('/content/yolov5/runs/detect/exp8/*.jpg')[:10]:
    display(Image(filename=image))
    print("\n")

"""## 7. Saving the model
Now that we have successfully trained our custom model. We can download the weight files and save them in our local directory or in Google Drive.
"""

# Commented out IPython magic to ensure Python compatibility.
from google.colab import drive
drive.mount('/content/gdrive')

# %cp /content/yolov5/runs/train/exp/weights/best.pt /content/gdrive/My\ Drive

# Commented out IPython magic to ensure Python compatibility.
# %cp /content/yolov5/runs/detect/exp2/video.mp4 /content/gdrive/My\ Drive

"""## 8. Inference with videos"""

!python detect.py --weights /content/yolov5/runs/train/exp/weights/best.pt --img 416 --conf 0.4 --source /content/video.mp4

"""## 9. References
[1] YOLO v5 - Train Custom Data https://github.com/ultralytics/yolov5/wiki/Train-Custom-Data

[2] Object Detection Metrics With Worked Example IoU, AP, mAP
https://towardsdatascience.com/on-object-detection-metrics-with-worked-example-216f173ed31e 

[3] IPython documentation https://ipython.readthedocs.io/en/stable/index.html# 

"""