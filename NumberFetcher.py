"""

Number Fetcher Version 1.2

This is a program to read a number from a screenshot and display it as a trendline.
Originally this was intended to be used for the Total Counts in the Roentdek
Software Cobold which has no trendline, so optimizing for Cobold Counts is 
generally not that easy without this GUI. Can be used for optimizing:
 - Laser Focus Position over ToF/VMI
 - Laser Chirp
 - i.g. anything influencing detector counts

This GUI takes screenshots and uses pytesseract (install with pip) which does
character recognition on the screenshot. pytesseract is a wrapper for the
tesseract.exe which has to be installed, this link shows you how to:

https://github.com/tesseract-ocr/tesseract/wiki (For Ubuntu & Windows)

Have fun with this thing. Edit as you like :I

"""

#------------------------------------------------------------------------------------------#
#IMPORTED MODULES
#------------------------------------------------------------------------------------------#

#to create the GUI and it's elements
import tkinter as tk

#Plotting and figures
import matplotlib
import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

#OS stuff
from ctypes import windll, Structure, c_long, byref
import win32api
import os
import threading
import time

#Image related things
import cv2
import PIL.ImageGrab
import pytesseract as tes

#Array stuff
import numpy


#------------------------------------------------------------------------------------------#
#EXTERNAL FUNCTIONS
#------------------------------------------------------------------------------------------#
def mergeInCaseOfSplitted(stringstomerge):
    merged=""
    for text in stringstomerge:
        merged += text
    return merged

class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


#------------------------------------------------------------------------------------------#
#THE GUI CLASS
#------------------------------------------------------------------------------------------#
class NumberTracing(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        #Variables for ROIframe
        self.varX1 = tk.StringVar()
        self.varY1 = tk.StringVar()
        self.varX2 = tk.StringVar()
        self.varY2 = tk.StringVar()

        self.varX1.set("0")
        self.varY1.set("0")
        self.varX2.set("0")
        self.varY2.set("0")
    
        #Variables for the tesseract loop
        self.values = []
        self.times = []
        self.running = False
        self.idle = tk.DoubleVar()
        self.idle.set(1.0)
        self.i = 0
        self.memory = numpy.nan
        self.latestDiff = 0.
        self.shortMem = []

        #Frames
        self.left = tk.Frame(self.parent, borderwidth=1, relief="solid")
        self.right = tk.Frame(self.parent, borderwidth=1, relief="solid")
        self.righttop = tk.Frame(self.right, borderwidth=1, relief="solid")
        self.rightmiddle = tk.Frame(self.right, borderwidth=1, relief="solid")
        self.rightbottom = tk.Frame(self.right, borderwidth=1, relief="solid")

        #Labels
        self.delimiterL = tk.Label(self.rightmiddle, text="Delimiter:")
        self.idleL = tk.Label(self.rightmiddle, text="Time delay:")

        #Buttons
        ROIb = tk.Button(self.righttop, text="Define ROI",
                                command=lambda:self.start_klickYourROI(None))
        saveROIb = tk.Button(self.righttop, text="Save ROI",
                                command=lambda:self.start_saveROI(None))
        loadROIb = tk.Button(self.righttop, text="Load ROI",
                                command=lambda:self.start_loadROI(None))
        runb = tk.Button(self.rightmiddle, text="Start", bg="LightBlue1",
                                command=lambda:self.start_run(None))
        stopb = tk.Button(self.rightmiddle, text="Stop", bg="orange2",
                                command=lambda:self.start_stop(None))
        clearb = tk.Button(self.rightmiddle, text="Clear",
                                command=lambda:self.start_clear(None))
        lastminb = tk.Button(self.rightmiddle, text="Last Minute",
        	                    command=lambda:self.start_lastminute(None))
        saveb = tk.Button(self.rightmiddle, text="Save Graph",
        	                    command=lambda:self.start_savegraph(None))

        #Entry fields
        self.delimiterE = tk.Entry(master=self.rightmiddle)
        self.idleE = tk.Entry(master=self.rightmiddle)

        #Figures
        self.fig = Figure(figsize=(2,1))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.rightbottom)

        self.figleft = Figure(figsize=(6,2))
        self.canvasleft = FigureCanvasTkAgg(self.figleft, master=self.left)

        #Opening image
        image = cv2.imread("dogwithfish.jpg")
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.subfleft = self.figleft.add_subplot(111)
        self.subfleft.axis('off')
        self.subfleft.imshow(image)

        #Checkboxes
        self.difference = tk.IntVar()
        self.totalordifferenceCB = tk.Checkbutton(self.rightmiddle, text="Difference?",
                                                variable = self.difference)

        #Packing it all
        self.left.pack(side="left", expand=True, fill="both")
        self.right.pack(side="right", expand=True, fill="both")
        self.righttop.pack(side="top", expand=True, fill="both")
        self.rightbottom.pack(side="bottom", expand=True, fill="both")
        self.rightmiddle.pack(side="bottom", expand=True, fill="both")
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvasleft.get_tk_widget().pack(fill="both", expand=True)

        ROIb.pack(fill=tk.X, padx=2, pady=2)
        saveROIb.pack(fill=tk.X, padx=2, pady=2)
        loadROIb.pack(fill=tk.X, padx=2, pady=2)

        self.delimiterL.pack(fill=tk.X, padx=2, pady=2)
        self.delimiterE.pack(fill=tk.X, padx=2, pady=2)
        self.idleL.pack(fill=tk.X, padx=2, pady=2)
        self.idleE.pack(fill=tk.X, padx=2, pady=2)

        runb.pack(fill=tk.X, padx=2, pady=2)
        stopb.pack(fill=tk.X, padx=2, pady=2)
        clearb.pack(fill=tk.X, padx=2, pady=2)
        lastminb.pack(fill=tk.X, padx=2, pady=2)

        self.totalordifferenceCB.pack(fill=tk.X, padx=2, pady=2)
        saveb.pack(fill=tk.X, padx=2, pady=2)

    #Functions
    def queryMousePosition(self):    
        pt = POINT()
        windll.user32.GetCursorPos(byref(pt))
        return pt.x, pt.y

    #Button Functions
    def klickYourROI(self):
        klicksdone = 0
        state_left = win32api.GetKeyState(0x01)
        print("Klick upper left!")

        while klicksdone < 1:
            a = win32api.GetKeyState(0x01)
            if a != state_left:  # Button state changed
                state_left = a
                if a < 0:
                    print(' ')
                else:
                    #print('Left Button Released1')
                    x1, y1 = self.queryMousePosition()
                    klicksdone = 1

        print("Klick lower right!")        
        while klicksdone < 2:
            a = win32api.GetKeyState(0x01)
            if a != state_left:  # Button state changed
                state_left = a
                if a < 0:
                    print(' ')
                else:
                    #print('Left Button Released2')
                    x2, y2 = self.queryMousePosition()
                    klicksdone = 2

        self.varX1.set(str(x1))
        self.varY1.set(str(y1))
        self.varX2.set(str(x2))
        self.varY2.set(str(y2))

        self.parent.update_idletasks()
        print(x1, y1, x2, y2)
        return 0

    def start_klickYourROI(self, event):
        global ROI_thread
        ROI_thread = threading.Thread(target=self.klickYourROI)
        ROI_thread.deamon = True
        ROI_thread.start()


    def saveROI(self):
        with open("ROI.txt", "w") as ROIfile:
            ROIfile.write("{}\n{}\n{}\n{}".format(self.varX1.get(),
                                                  self.varY1.get(),
                                                  self.varX2.get(),
                                                  self.varY2.get()))

    def start_saveROI(self, event):
        self.saveROI()


    def loadROI(self):
        with open("ROI.txt", "r") as ROIfile:
            data = ROIfile.read().splitlines()
        
        self.varX1.set(data[0])
        self.varY1.set(data[1])
        self.varX2.set(data[2])
        self.varY2.set(data[3])
        
        image = PIL.ImageGrab.grab(bbox=(int(self.varX1.get()),
                                         int(self.varY1.get()),
                                         int(self.varX2.get()),
                                         int(self.varY2.get())))
        
        subf = self.fig.add_subplot(111)
        subf.clear()
        subf.axis('off')
        subf.imshow(image)
        
        self.canvas.draw()

    def start_loadROI(self, event):
        self.loadROI()

    def stop(self):
        self.running = False
        print("Stopped!")

    def start_stop(self, event):
        self.stop()

    def run(self):
        print("Running!")
        T = float(self.idleE.get())
        print(T)
        splitting = True
        delimiter = self.delimiterE.get()
        if delimiter == "":
            splitting = False
        print(delimiter)

        if self.difference.get() == 1:
            mode = "Difference"
        else:
            mode = "Total"

        #while self.running == True:
        startt = time.time()
        image = PIL.ImageGrab.grab(bbox=(int(self.varX1.get()),
                                         int(self.varY1.get()),
                                         int(self.varX2.get()),
                                         int(self.varY2.get())))

        subf = self.fig.add_subplot(111)
        subf.clear()
        subf.axis('off')
        subf.imshow(image)
        self.canvas.draw()

        opencvImage = cv2.cvtColor(numpy.array(image), cv2.COLOR_BGR2GRAY)

        #use tesseract to read the numbers from the chosen frame
        results = tes.image_to_string(opencvImage)
        results = mergeInCaseOfSplitted(results)
        results = results.replace(" ", "")

        if splitting == True:
            try:
                splitresults = results.split(delimiter)   #Split the string at the commata and match together
                number = ""
                for j in range(len(splitresults)):
                    number += splitresults[j]
                print(splitresults, number, self.i)
                number = float(number)
            except:                                 #Problem with the splitting
                print("Result is not float!")
                number = numpy.nan

        else:
            print(results)
            try:
                number = float(results)
                print(number)
            except:
                number = numpy.nan
                print("Result is not float!")

        #Append Values to arrays and check for potential problems
        self.times.append(int(self.i)*T)

        if mode == "Difference":
            print("Mode is Difference!")
            try:
                if self.i < 2:               #for the first number there is no earlier number, so set to NaN
                    self.shortMem.append(number)
                    self.values.append(numpy.nan)
                    self.memory = numpy.nan
                    if self.i == 1:
                        self.latestDiff = self.shortMem[1] - self.shortMem[0]
                else:
                    if number-self.memory < 0.0001:        #adjust for display and screenshot not synched (python too fast)
                        self.values.append(self.latestDiff)
                    else:
                        self.latestDiff = number-self.memory  #if everything is fine just add the difference between current and last
                        self.values.append(self.latestDiff)
            except Exception as e:                                 #add NaN if anything goes wrong
                self.values.append(numpy.nan)
                print(e)

            try:
                self.memory = number
            except:
                self.memory = numpy.nan

            print("Memory = {}".format(self.memory))

        if mode == "Total":
            print("Mode is Total!")
            try:
                if self.i < 1:                          #for the first number there is no earlier number, so set to NaN
                    self.values.append(numpy.nan)
                else:
                    self.values.append(number)
            except:                                 #add NaN if anything goes wrong
                self.values.append(numpy.nan)

        self.figleft.delaxes(self.subfleft)
        self.subfleft = self.figleft.add_subplot(111)
        self.subfleft.clear()
        self.subfleft.set_title("Behaviour of Variable")
        self.subfleft.set_xlabel("Time [s]")
        self.subfleft.set_ylabel("Value")
        self.subfleft.plot(numpy.array(self.times), numpy.array(self.values))
        self.subfleft.grid()
        self.canvasleft.draw()

        endt = time.time()
        diff = endt-startt
        print(diff)
        print(T)
        print(threading.active_count())
        try:
            time.sleep(T-diff)
        except Exception as e:
            print(e)
            print("Issue with time delay.")

        self.i += 1
    
        if self.running == True:
            self.after(1, self.run)


    def start_run(self, event):
        self.running = True
        self.run()

    def clear(self):
        self.times = []
        self.values = []
        self.i = 0

        subfleft = self.figleft.add_subplot(111)
        subfleft.clear()

    def start_clear(self, event):
        self.clear()

    def lastminute(self):
        #Calculate how many indicees have to be cut off to get one minute:
        #Number of indicees is 60 seconds devided by the repetition rate T 
        indicees = int(60./float(self.idleE.get()))
        self.times = self.times[-1*indicees:-1]
        self.values = self.values[-1*indicees:-1]

    def start_lastminute(self, event):
    	self.lastminute()

    def savegraph(self):
        f = open('countsOverTime.txt', 'w')
        for j in range(len(self.values)):
            f.write(str(self.times[j])+'\t'+str(self.values[j])+'\n')
        f.close()
        
    def start_savegraph(self, event):
    	self.savegraph()


#------------------------------------------------------------------------------------------#
#RUNNING THE THING
#------------------------------------------------------------------------------------------#
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Number Tracing")
    root.geometry("720x480")
    NumberTracing(root).pack()
    root.mainloop()


