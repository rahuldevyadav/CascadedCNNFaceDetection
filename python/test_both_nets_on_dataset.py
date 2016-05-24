from keras.models import Sequential
import model_architecture
import time
import imageloader as il
import math
import sys
import imagepyramid
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import cv2
import preprocess_48net as net
import visualize_results as vr
import compute_accuracy as acc


model12FileName = str(sys.argv[1])
model48FileName = str(sys.argv[2])
windowSize = 24
windowSize48 = 48
windowSize12 = 24
scaleFactor = 2
stepSize = 24
T12 = 0 #threshold for it is passed to 48net
T48 = 0 #threshold for if it is a high label for the final evaluation

#================================================
# Preprocessing
#================================================

print("======Loading and Preprocessing...======")
start_time = time.time()

#If path to image passed as argument load and process that image, otherwise load from annotations(evaluation images)
if (len(sys.argv) > 3):
        imdb =[il.loadAndPreProcessSingle(str(sys.argv[3]), scaleFactor, (windowSize, windowSize))]
else:
    imdb = il.loadAndPreProcessIms('annotations_short.txt', scaleFactor, (windowSize,windowSize))

print("Image database: {0} images".format(len(imdb)))
[X, Y, W] = il.getCNNFormat(imdb, stepSize, windowSize)
print("finished preprocessing in {0}".format(time.time()-start_time))
print('X-shape')
print(X.shape)
print('Y-shape: ')
print(Y.shape)
print('W-shape')
print(W.shape)

print("=========================================")
#================================================
# 12 net
#================================================

print("\n\n============== 12Net ====================")
model12 = model_architecture.setUp12net(windowSize)
print("Loading model from: " + model12FileName)
model12.load_weights(model12FileName)

model48 = model_architecture.setUp48net(windowSize48)
print("Loading model from: " + model48FileName)
model48.load_weights(model48FileName)

# Get best predictions
predictions_12 = model12.predict(X, batch_size=16, verbose=1)
# Get top 10%
#targets  = np.squeeze(predictions_12)
#nb_top_targets = int(math.ceil(targets.shape[0]*0.1))
#p_idx = np.argsort(targets)[-nb_top_targets:]

#print('===========P===========')
#print(p_idx)
#predictions_12 = predictions_12[p_idx,:]
#Y = Y[p_idx,:]
#X = X[p_idx,:, :, :]
#W = W[p_idx, :, :]



#predictions_high = predictions_12[high_idx,:]
#predictions_low = predictions_12[low_idx,:]

X_high = []
W_high = []
X_per_image = []
W_per_image = []
pred_per_image = []
predictions_high = []
previmageidx = W[0][0][3]
X_per_image = np.asarray(X_per_image)
pred_per_image = np.asarray(pred_per_image)
W_per_image = np.asarray(W_per_image)


for i in range(0, predictions_12.shape[0]):
	imageidx = W[i][0][3]
	if(imageidx == previmageidx):
		pred_per_image = np.append(pred_per_image, predictions_12[i, :])
		X_per_image = np.append(X_per_image, X[i,:,:, :])
		W_per_image = np.append(W_per_image, W[i,:,:])
	else:
		print(X_per_image.shape)
		nb_top_targets = int(math.ceil(len(pred_per_image)*0.1))
		high_idx = np.argsort(pred_per_image)[-nb_top_targets:]
		X_high = np.concatenate((X_high, X_per_image[high_idx, :, :, :]), axis=0)
		W_high = np.concatenate((W_high, W_per_image[high_idx, :, :]), axis = 0)
		predictions_high = np.concatenate((predictions_high + pred_per_image[high_idx, : ]), axis = 0)
		pred_per_image = []
		X_per_image = []
		W_per_image = []
		previmageidx = imageidx	




	
	#else:	
	#	predictions_high = pred_image[high_idx,:]
	#	pred_image = []
	#previmageidx = imageidx



##================================================
# 48 net
#================================================

print("\n\n============== 48Net ====================")
start_time = time.time()
[X_48, Y_48, W_48, windowSize, imdb_48] = net.preProcess48Net(imdb, X, predictions_12, W, windowSize12, T12)
print("preprocessing in {0}".format(time.time()-start_time))
predictions_48 = model48.predict_on_batch(X_48)
print("prediction in {0} s".format(time.time()-start_time))
#================================================
# Evaluation
#================================================
## To map input to 48 with original image
maxlabels = []
previmageidx = W_48[0][0][3]
maxlabel = -1
label = -1
maxindex = -1

for i in range(0, W_48.shape[0]):
	imageidx = W_48[i][0][3]
	if(imageidx == previmageidx):
		label = predictions_48[i][:]
		if (maxlabel < label):
			maxlabel = label
			maxindex = i
	else:	
		maxlabels.append([maxlabel,maxindex])
		maxlabel = 0
	previmageidx = imageidx
maxlabels.append([maxlabel,maxindex])


maxlabels = np.asarray(maxlabels)
print(maxlabels.shape)
#===========================
# Evaluation for a data set
#===========================

W_48 = np.squeeze(W_48)
windows = []
images = []

for i in range(maxlabels.shape[0]):
	maxindex = int(maxlabels[i][1])
	imageidx = W_48[maxindex,3]
	windows.append(W_48[maxindex,:])
	images.append(imdb[imageidx].image)
	

windows = np.asarray(windows)
#windows = np.squeeze(windows)

acc = acc.compute_accuracy_dataset(maxlabels, imdb, W_48)



title = "Top predicted face image from 48Net"
vr.visualizeResultNoSubImage(title,images, windows)



