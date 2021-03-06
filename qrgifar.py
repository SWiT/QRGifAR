import numpy
import cv2
import zbar
import math, os
from PIL import Image

import qrcodes
import game

CV_CAP_PROP_FRAME_WIDTH     = 3
CV_CAP_PROP_FRAME_HEIGHT    = 4

# Blue, Green, Red, Yellow, Magenta, Cyan
def colorCode(color):
    color = color.lower()
    if color == "blue":
        return (255,0,0)
    elif color == "green":
        return (0,255,0)
    elif color == "red":
        return (0,0,255)
    elif color == "darkred":
        return (0,0,190)
    elif color == "yellow":
        return (0,255,255)
    elif color == "magenta":
        return (255,0,255)
    elif color == "cyan":
        return (255,255,0)
    elif color == "purple":
        return (128,0,128)

def drawBorder(img, points, color, thickness):
    for idx0,point in enumerate(points):
        if idx0+1 >= len(points):
            idx1 = 0
        else:
            idx1 = idx0+1
        cv2.line(img, points[idx0], points[idx1], colorCode(color), thickness)
    
# Initialize the camera.        
cap = cv2.VideoCapture(0)
cap.set(CV_CAP_PROP_FRAME_WIDTH, 1280)
cap.set(CV_CAP_PROP_FRAME_HEIGHT, 720)
outimgw = int(cap.get(CV_CAP_PROP_FRAME_WIDTH))
outimgh = int(cap.get(CV_CAP_PROP_FRAME_HEIGHT))
print "\nResolution:", outimgw, 'x', outimgh

# Create the openCV window.
windowname = "Augmented Reality Demo: Cats in QR Codes"
cv2.namedWindow(windowname, cv2.WINDOW_NORMAL)

# Initialize the Zbar scanner
scanner = zbar.ImageScanner()
scanner.set_config(0, zbar.Config.ENABLE, 0) # Disable all symbols.
scanner.set_config(zbar.Symbol.QRCODE, zbar.Config.ENABLE, 1) # Enable just QR codes.

# Print how to quit.
print "\n\tQ or Esc to exit.\n"

QRCodes = qrcodes.QRCodes(int(cap.get(CV_CAP_PROP_FRAME_HEIGHT)), int(cap.get(CV_CAP_PROP_FRAME_WIDTH)))

ball = game.Ball((outimgw/2, outimgh/2), colorCode("red"), outimgw, outimgh)

scores = game.Scores()
    
# Main Loop.
while(True):
    # Capture a frame from the camera, and get it's shape.
    ret, outimg = cap.read()  
    outimgh, outimgw, outimgd = outimg.shape

    # Convert to a RAW grayscale.
    gray = cv2.cvtColor(outimg, cv2.COLOR_BGR2GRAY) #convert to grayscale
    
    # Foreach QRCode already found scan the qrcode's roi.
    numfound = 0
    for qr in QRCodes.qrlist:
        roi = gray[qr.ymin:qr.ymax, qr.xmin:qr.xmax]
        h,w = roi.shape
        zbarimage = zbar.Image(w, h, 'Y800', roi.tostring())
        scanner.scan(zbarimage)
        for symbol in zbarimage:
            # If found update with offset.
            if symbol.data == qr.data:
                i = QRCodes.update(symbol.data, symbol.location, True)
                numfound += 1
                
                # Blank the region of the grayscaled image where the qrcode was found.
                poly = numpy.array(qr.location, numpy.int32)
                cv2.fillConvexPoly(gray, poly, 0)
            
            
    # If too few QR Codes were found Scan for new QR Codes.
    if numfound < 2:
        zbarimage = zbar.Image(outimgw, outimgh, 'Y800', gray.tostring())
        scanner.scan(zbarimage)
        # Foreach new symbol found
        for symbol in zbarimage:
            # try to update the QRCode if it exists
            i = QRCodes.update(symbol.data, symbol.location)
            if i == -1:
                # Add the QR Code
                i = QRCodes.add(symbol.data, symbol.location)
                
    # Remove Expired QRCodes
    QRCodes.removeExpired()
    
    # Output All QR Codes.
    for qr in QRCodes.qrlist:
        # Get the QRCode's GIF
        gif = qr.gif
        # Get the next frame of the GIF.
        gif.nextFrame()
        # Warp the GIF frame and insert the warped Gif into the output image.
        gif.warpimg(outimg, qr)
        
        # Draw a border around symbol.
        if qr.data == "A":
            color = "blue"
        elif qr.data == "B":
            color = "yellow"
        elif qr.data == "C":
            color = "green"
        elif qr.data == "D":
            color = "darkred"
        else:
            color = "magenta"
        drawBorder(outimg, qr.location, color, 6)
        
        # Draw the symbol's region of interest.
        #drawBorder(outimg, qr.roi, "cyan", 1)
        
    # Draw the Ball
    ball.move()
    ball.checkcollision(QRCodes, scores)
    ball.draw(outimg)
    
    # Mirror flip the output image.
    outimg = cv2.flip(outimg,1);
    
    # Draw the scores and message.
    font = cv2.FONT_HERSHEY_COMPLEX
    cv2.putText(outimg, str(scores.score1), (25,100), font, 3.5, colorCode("magenta"), 4)
    cv2.putText(outimg, str(scores.score2), (outimgw-125,100), font, 3.5, colorCode("magenta"), 4)
    if not scores.message.expired():
        cv2.putText(outimg, scores.message.text, (outimgw/2-450,300), font, 4.0, colorCode("magenta"), 8)
    
    
    # Display the resulting frame
    cv2.imshow(windowname, outimg)
    
    # Exit on Q or Esc.
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == ord('Q') or key ==27: 
        break
    # Reset game on 'spacebar' press.
    if key == ord(' '):
        print "Reset"
        scores.reset()
        ball.reset()
        
# Release the capture device and destory the windows.
cap.release()
cv2.destroyAllWindows()
