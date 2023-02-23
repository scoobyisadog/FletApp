import cv2
import mediapipe as mp
import time
import math
from math import atan2, pi, degrees
import numpy as np


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class poseDetector():
    def __init__(self, mode=False, complexity=2, upBody=True, smooth=True,
                  detectionCon=0.9, trackCon=0.9):

        self.enable_segmentation = True
        self.mode = mode
        self.upBody = upBody
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.complexity = complexity
        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.mode, self.complexity, self.upBody, self.smooth,
                                     self.detectionCon, self.trackCon)
        #self.pose = self.mpPose.Pose()

        self.hipThenR = self.hipThenL = self.hipnowL = self.hipNowR=np.array([0, 0])
        self.thenthumb = np.array([0, 0, 0, 0, 0])

    def settings(self,VisThresh, MoveThresh, hipThresh, hipTrail, scale1):
        self.scale1 = scale1
        self.VisThresh=VisThresh
        self.MoveThresh=int(MoveThresh*scale1)
        self.hipThresh=int(hipThresh*scale1)
        self.hipTrail=hipTrail



    def findPose(self, img, draw=False):
        #added by garry
        #img = np.float32(img)

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        if self.results.pose_landmarks:
            if draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                           self.mpPose.POSE_CONNECTIONS)
        return img

    def findPosition(self, img, draw= False):
        self.lmList = []
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                # added to find visibility
                vis=lm.visibility

                h, w, c = img.shape
                # print(id, lm)
                cx, cy, cz= int(lm.x * w), int(lm.y * h), int(lm.z *w)
                self.lmList.append([id, cx, cy, cz, vis])
                # if draw:
                #      cv2.circle(img, (cx, cy, cx), 5, (255, 0, 0), cv2.FILLED)
        return self.lmList


    def findAngle(self,L, img, imgCanvas):
        self.img=img
        self.imgCanvas=imgCanvas
        if L=="L":
            shoulder, elbow, wrist= 11, 13, 15
        if L=='R':
            shoulder, elbow, wrist=12, 14, 16

            # Get the landmarks - p1, 2, 3 = , colour, 1, 2, 3 =
        x1, y1, z1, v1= self.lmList[shoulder][1:5]
        self.nowshoulder=(x1,y1,z1,v1); self.nowshoulder=np.array(self.nowshoulder)
        x2, y2, z2, v2= self.lmList[elbow][1:5]
        self.nowelbow=(x2, y2, z2, v2); self.nowelbow= np.array(self.nowelbow)
        x3, y3, z3, v3 = self.lmList[wrist][1:5]
        self.wristNow=(x3, y3, z3, v3);self.wristNow=np.array(self.wristNow)

        #finger coords - colour4
        x4, y4, z4, v4= self.lmList[wrist+6][1:5];
        self.nowthumb = (x4,y4,z4,v4); self.nowthumb = np.array(self.nowthumb)

        #calc angle
        Ax, Ay = x1 - x2, y1 - y2
        Cx, Cy = x3 - x2, y3 - y2
        a = atan2(Ay, Ax)
        c = atan2(Cy, Cx)
        if a < 0: a += pi * 2
        if c < 0: c += pi * 2
        self.angle= abs(180-degrees((pi * 2 + c - a) if a > c else (c - a)))

        #colour based on angle
        if v1 >=self.VisThresh and v2>=self.VisThresh and v3>=self.VisThresh:
            angleLnorm = self.angle / 180
            if angleLnorm < 0.25:
                self.angleColour = (0, 255, 100 + (920 * angleLnorm))
            if angleLnorm >= 0.25:
                self.angleColour = (0, 63.75 / angleLnorm, 255)
        else:
            self.angleColour=(120,120,120)

    #grey is no vis
        if v1 > self.VisThresh:
            colour1 = self.angleColour
        else:
            colour1 = (120, 120, 120)

        if v2 > self.VisThresh:
            colour2 = self.angleColour
        else:
            colour2 = (120, 120, 120)

        if v3 > self.VisThresh:
            colour3 = self.angleColour
        else:
            colour3 = (120, 120, 120)

#draw arm lines
        cv2.line(self.img, (x1, y1), (x2, y2), self.angleColour, 1)
        cv2.line(self.img, (x3, y3), (x2, y2), self.angleColour, 1)
        cv2.circle(self.img, (x1, y1), 5, colour1)
        cv2.circle(self.img, (x2, y2), 5, colour2)
        cv2.circle(self.img, (x3, y3), 5, colour3)

#draw hand circle
        if v4 < self.VisThresh: #thumb
            handColour = (120, 120, 120)
        else:
            handColour = (255, 255, 255)
        # finger
        cv2.circle(img, (x4, y4), 15, handColour, 1)

        return self.angle, self.angleColour


    def movement(self, L,thenthumb, hipThenL, hipThenR):


        hipnowR = np.array(self.lmList[24][1:3]); diffhipR = np.linalg.norm(hipnowR - self.hipThenR)
        hipnowL = np.array(self.lmList[23][1:3]); diffhipL = np.linalg.norm(hipnowL - self.hipThenL)
        hipnow = (hipnowL + hipnowR) / 2


        if L=='L':
            self.nowthumb=self.lmList[21][1:5]
            self.side=-10

        if L=='R':
            self.nowthumb=self.lmList[22][1:5]
            self.side = 120
        print(thenthumb)
        if thenthumb==[0,0]:
            self.hipthenL = hipnowL
            self.hipThenR = hipnowR
            thenthumb =self.nowthumb
        else:
            self.hipthenL = hipThenL
            self.hipThenR = hipThenR
            hipthen = (self.hipThenL + self.hipThenR) / 2


        # TODO check 2d vs 3d # 2d only?? add 1:4 for z axis??
        nowthumba = np.array(self.nowthumb[0:2])
        thenthumba = np.array(thenthumb[0:2])
        diffa = np.linalg.norm(nowthumba - thenthumba)

        if self.wristNow[3] >= self.VisThresh:
            colour = self.angleColour
            vis = 'ok'
# is moving? dynamic/static
            if (diffa > self.MoveThresh):
                cv2.line(self.imgCanvas, (int(nowthumba[0]), int(nowthumba[1])),
                         (int(thenthumba[0]), int(thenthumba[1])),
                         self.angleColour,2)
                move = "moving"
                if abs(diffhipR) >= self.hipThresh or abs(diffhipL) >= self.hipThresh:
                    static = 'dynamic'
                    colourmove = (255, 0, 255)  # colours in openCV are BGR
                    colour = colourmove
                    if self.hipTrail == "ON":
                        # cv2.line(self.imgCanvas, (int(hipnow[0]), int(hipnow[1])),
                        #          (int(hipthen[0]), int(hipthen[1])),
                        #          self.angleColour, 10)
                        cv2.circle(self.imgCanvas, (int(hipnow[0]), int(hipnow[1])), 5,
                                   self.angleColour, -1)
                else:
                    static = 'static'
                    colourmove = (255, 50, 50)
                    colour = colourmove
                    if self.hipTrail == "ON":
                        cv2.circle(self.imgCanvas, (int(hipnow[0]), int(hipnow[1])), 5,
                                   self.angleColour, -1)

                if self.hipTrail == "ON":
                    # vertial handline
                    cv2.line(self.img, (int(self.wristNow[0]), 0), (int(self.wristNow[0]), int(800*self.scale1)),
                             self.angleColour, 1)
            else:
                colourmove = (180, 180, 180)
                static = ''
                move = 'held'
                # log hold position?

        else:
            colourmove = (180, 180, 180)
            colour = (120, 120, 120)
            static = 'hidden'
            vis = 'lost'
            move='lost'

        self.colourmove=colourmove
        self.colour=colour
        self.static=static
        self.vis=vis
        self.move=move

        self.hipthenL=hipnowL
        self.hipThenR=hipnowR
        self.thenthumb=self.nowthumb

        return self.thenthumb, self.hipthenL, self.hipThenR



    def armCircles(self,frame_height):
        colour=self.colour
        colourmove=self.colourmove
        self.frame_height=frame_height

        side = self.side
        if self.angle < 10:
            side1 = side-10
        if self.angle > 10 and self.angle < 100:
            side1 = side-16
        if self.angle > 100:
            side1 = side - 26
        self.side1 = side1

        # outline
        cv2.circle(self.img, (int(self.scale1*(120 + side )), frame_height - int(150* self.scale1)), int(50* self.scale1), colour, 3)
        # filled
        cv2.circle(self.img, (int(self.scale1*(120 + side )), frame_height - int(150* self.scale1)), int(50* self.scale1), colourmove, -1)
        # number
        cv2.putText(self.img, str(int(self.angle)), (int((side1 +120)*self.scale1), frame_height - int(140* self.scale1)),
                    cv2.FONT_HERSHEY_PLAIN, int(self.scale1*2), colour, 2)
        cv2.ellipse(self.img, (int(self.scale1*(120 + side)), frame_height - int(self.scale1*(150))), (int(52* self.scale1), int(45* self.scale1)), angle=-90, startAngle=0, endAngle=self.angle * 2,
                    thickness=int(self.scale1*20),
                    color=colour)

    def moveUIL(self, L):
        side=self.side
        static=self.static
        colour=self.colour
        frame_height=self.frame_height
        # visL, staticL, sideL, frame_height, L):
        # static or dynamic or held
        if (self.vis == 'ok'):
            cv2.putText(self.img, str(static), (int(self.scale1*(side + 90)), frame_height - int(self.scale1*80)),
                        cv2.FONT_HERSHEY_PLAIN, 1.5, colour, 2)
            cv2.putText(self.img, f"{L}", (int(self.scale1*(side + 115)), frame_height - int(self.scale1*220)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (100, 100, 100), 2)
        else:
            cv2.putText(self.img, str(static), (int(self.scale1*(side + 65)), frame_height - int(self.scale1*60)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (80, 80, 80), 2)
            cv2.putText(self.img, f"{L}", (int(self.scale1 * (side + 115)), frame_height - int(self.scale1 * 220)),
                        cv2.FONT_HERSHEY_PLAIN, 1, (100, 100, 100), 2)




    def imgShift(self, image, shift_horizontal, shift_vertical):
            #image=imgCanvas
            # Define parameters for the translation
            #shift_horizontal = 200  # Number of pixels to shift horizontally
            #shift_vertical = 100  # Number of pixels to shift vertically
            # We define a 2D matrix in float32 to describe the translation
            matrix = np.float32([[1, 0, shift_horizontal],
                                 [0, 1, shift_vertical]])
            y = image.shape[0]  # Height of our image
            x = image.shape[1]  # Width of our image
            output_size = (x, y)  # Defines the output size of our image
            imgCanvas1 = cv2.warpAffine(image, matrix, output_size)
            return imgCanvas1






