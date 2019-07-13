#NumberFetcher

NumberFetcher is a software that uses tesseract to read numbers from screenshots and then displays those numbers
as a trendline.

##How to use the number fetcher:

First of all you have to define a region of interest. Therefor you define a rectangle which you want to read
the numbers from by klicking in the upper left and lower right corner of your rectangle. Your choice will be 
displayed in the lower right. If you are happy klick on save ROI so that you don't have to reenter the ROI
corners whenever you restart the program.
When this is done you can insert a delimiter for your number. If it has "xxx.xx" a format like this then you
don't need to enter anything. If your number looks like this "xx:xx" python cannot directly convert the number
to a float so you need to explicitly give the delimiter which is ":" in this case.
Then you need the time difference between readouts. Because tesseract needs at least around .7 seconds to
get the numbers from the image, it is useful to just chose 1.0 seconds to be on the safe side.
When you klick on "Start" the software will start to display your chosen number in a trendline. If it does not
work please have a look in the command line and the python file. Maybe you can figure it out.


##What environment is this tested in?
Windows10


##How to install:
download tesseract and add the path to your environment
install pytesseract, the python wrapper for pytesseract
adjust the paths in the .py file to match wherever you installed the NumberFetcher on your machine
*** you need all kinds of python packages:
tkinter
matplotlib
ctypes
win32api
os
threading
time
cv2
PIL.ImageGrab
pytesseract
numpy


##To do:
- check if the difference mode still works
- make the GUI independant of readout intervall -> smoother experience




