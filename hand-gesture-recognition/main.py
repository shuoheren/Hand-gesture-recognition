
# coding: utf-8
import cv2
import numpy as np
from collections import deque

def make_frame_smaller(frame,scale):
    'Reduce the dimensions of the matrix, returns the processed image'
    height, width = frame.shape[:2]
    res = cv2.resize(frame,(int(scale*width), int(scale*height)), interpolation = cv2.INTER_CUBIC)
    return res

def background_removal(frame):
    'Remove all pixels in a certain range so that we can see our object, returns the processed image'
    height, width = frame.shape[:2]
    img = frame
    for h in range(height):
        for w in range(width):
            # input(img[h][w])
            b, g, r = img[h][w]
            if r > 150 and g < 100 and b < 100:
                img[h][w] = [255, 255, 255]
            else:
                img[h][w] = [0, 0, 0]
    return img

def template_matching(frame,template,original,name, t=150000000.0):
    'Find location of the template and the confidence. Input frame, template, original frame to draw, name of the template and the threshold'
    res = cv2.matchTemplate(frame.astype(np.float32),template.astype(np.float32),cv2.TM_SQDIFF)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if min_val < t:
        h, w = template.astype(np.float32).shape[:2]
        top_left = min_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        cv2.rectangle(original,top_left , bottom_right, 255, 2)
        
        cv2.putText(original, "%s: %.3f"%(name, min_val/1000000), (top_left[0], top_left[1] + h), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
    
        confidence = t/(t-min_val)
    else:
        confidence = 0
        top_left = None
        bottom_right = None 
        
    return original, (confidence, top_left, bottom_right, name)

def drawProbablyBox(resultList, output):
    'Draw the box with the highest probability to the output frame'
    if resultList == []:
        return output
    biggest = resultList[0]
    for n,i in enumerate(resultList[1:]):
        confidence, _, _, _ = i
        if confidence > biggest[0]:
            biggest = i

    confidence, top_left, bottom_right, name = biggest
    if confidence != 0:
        h = bottom_right[1]-top_left[1]
        cv2.rectangle(output,top_left , bottom_right, 255, 2)
        cv2.putText(output,"name: %s"%(name), (top_left[0], top_left[1] + h), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
    return output, top_left
    
def findOrnt(history, output, dist=30):
    'Find orientation of the gesture. Returns the frame with the result drawn on it'
    if len(history) < HISTORY_NUM:
        return output
    else:
        history = removeNone(history)
        if len(history) > 1:
            if history[-1][1] - history[0][1] > dist:
                # up
                cv2.putText(output,"down", (20,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
            elif history[0][1]- history[-1][1]  > dist:
                # down
                cv2.putText(output,"up", (20,20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))
        return output

def removeNone(history):
    'Find the consecutive motion of the object by removing None\'s'
    newhistory = []
    noneCount = 0
    noneMax = 5
    for n,i in enumerate(history):
        if i != None:
            newhistory.append(i)
        else:
            noneCount += 1
            if noneCount >= noneMax:
                # consider that movement incontinuous
                newhistory = []
    return newhistory

def getShape(cap):
    'Get the shape of the frame'
    ret, frame = cap.read()
    frame = make_frame_smaller(frame,0.2)
    return frame.shape[:2]

# initialize
cap = cv2.VideoCapture(0)
h, w = getShape(cap)
out = cv2.VideoWriter('output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 20.0,(int(cap.get(3)),int(cap.get(4))))
# get templates
openhand = cv2.imread("openhand.png")
cdopenhand = cv2.cvtColor(openhand, cv2.COLOR_BGR2GRAY)
fist = cv2.imread("fist.png")
fist = cv2.cvtColor(fist, cv2.COLOR_BGR2GRAY)
indexfinger = cv2.imread("indexfinger.png")
indexfinger = cv2.cvtColor(indexfinger, cv2.COLOR_BGR2GRAY)

backSub = cv2.createBackgroundSubtractorKNN()
history = deque()
HISTORY_NUM = 15
DEBUG = True

while(True):
    ret, frame = cap.read()
    frame = make_frame_smaller(frame,0.2)

    # initialize 3 frames
    original = frame.copy()
    output = frame.copy()
    fgMask = backSub.apply(frame)
    
    #template matching for your object
    frame, handresult = template_matching(fgMask,openhand,original,'hand',100000000.0)
    frame, fistresult = template_matching(fgMask,fist,original,'fist',16000000.0)
    frame, indexresult = template_matching(fgMask,indexfinger,original, 'indexfinger',22000000.0)
    
    output, top_left = drawProbablyBox([handresult, fistresult, indexresult], output)
    if len(history) > HISTORY_NUM:
        history.popleft()
    history.append(top_left)
    output = findOrnt(history, output)
    if top_left != None:
        cv2.putText(output,"%s"%str(top_left), (20,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255))

    # show images and store the video
    if DEBUG:
        cv2.imshow('frame',frame)
        cv2.imshow('FG Mask', fgMask)
    cv2.imshow('Output', output)
    out.write(output)
    
    k = cv2.waitKey(1)
    if k & 0xFF == ord('q'):
        # press q to quit
        break
    elif k & 0xFF == ord('s'):
        # press s to screenshot, but only one image comes out
        cv2.imwrite('mask.png', fgMask)
        cv2.imwrite('output.png', output)

# When everything done, release the video capture and video write objects
cap.release()
out.release()
 
# Closes all the frames
cv2.destroyAllWindows() 
