'''
calculate the distance in the image based on the reference length

'''

from tkinter import *
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageDraw, ImageFont, ImageGrab, ImageTk, PngImagePlugin
import math
import numpy as np

# the size of the GUI
tool_zone_width = 100
tool_zone_heigth = 300
canvas_zone_width = 300
canvas_zone_height = 300
buttom_zone_width = tool_zone_width + canvas_zone_width
buttom_zone_height = 20

button_width = 10 # button width

circle_radius = 3

# work status
class WorkState():
    def __init__(self):
        self.INITIALIZATION = 0
        self.UNCALIBREATED = 1
        self.CALIBRATING = 2
        self.CALIBRATED = 3
        self.MEASURE = 4
        self.ISDRAWING = 5 # ONLY select one point when choose point pairs
        
class PointCouple():
    # a pair of points
    def __init__(self):
        self.p1_x = 0
        self.p1_y = 0
        self.p2_x = 0
        self.p2_y = 0
    
    def isP1Full(self):
        return self.p1_x > 0 and self.p1_y > 0
    
    def isP2Full(self):
        return self.p2_x > 0 and self.p2_y > 0
    
    def isFull(self):
        return self.p1_x > 0 and self.p1_y > 0 and self.p2_x > 0 and self.p2_y > 0
                
    def distance(self):
        dis = math.sqrt((self.p1_x - self.p2_x)**2 + (self.p1_y - self.p2_y)**2)
        return dis

class HandDimension():
    def __init__(self):
        self.dimensions = []

    def setValue(self, index, value):
        self.dimensions[index] = value
        
class DrawState():
    # the state when drawn point pairs
    def __init__(self):
        self.isP1Drawn = False
        self.isLineDrawn = False
        self.isP2Drawn = False
        self.isTextDrawn = False
        
    def reset(self):
        self.isP1Drawn = False
        self.isLineDrawn = False
        self.isP2Drawn = False
        self.isTextDrawn = False
        
    def isDone(self):
        # if the draw is finished, return true
        return self.isP1Drawn and self.isP2Drawn and self.isLineDrawn and self.isTextDrawn
        
class MyGUI(object):
    def __init__(self, master):
        self.master = master
        self.master.title('Measure distance in the image!')
        
        # the frame grid
        self.frame_tools = Frame(self.master, 
                                 width = tool_zone_width, 
                                 height = tool_zone_heigth, 
                                 padx=3, pady=3, borderwidth = 2,
                                 highlightthickness=2,
                                 highlightbackground="black")
        
        self.frame_canvas = Frame(self.master, 
                                 width = canvas_zone_width, 
                                 height = canvas_zone_height, 
                                 padx=3, pady=3, borderwidth = 2,
                                 highlightthickness=2,
                                 highlightbackground="black")
        
        self.frame_buttom = Frame(self.master, 
                                  width = canvas_zone_width, 
                                  height = canvas_zone_height, 
                                  padx=3, pady=3, borderwidth = 2,
                                  highlightthickness=2,
                                  highlightbackground="black")

            # Layout all of the main containers
        self.master.grid_rowconfigure(0, weight=1) #Elastic top row
        self.master.grid_rowconfigure(1, weight=0)
        self.master.grid_columnconfigure(0, weight=0)
        self.master.grid_columnconfigure(1, weight=1) #Elastic second column
        
        self.text_path = StringVar()
        self.label_file_path = Label(self.frame_tools, width=button_width * 2, borderwidth=2, relief="groove", textvariable=self.text_path)
        self.button_load_path = Button(self.frame_tools, text='Load Path', width=button_width, command=self.__loadImagePath)
        self.button_load_image = Button(self.frame_tools, text='Load Image', width=button_width, command=self.__loadImage)
        self.button_calibrate = Button(self.frame_tools, text='Calibrate', width=button_width, command=self.__calibrate)
        self.button_set_ref_length = Button(self.frame_tools, text='Set Reference Length', width=button_width, command=self.__setReferenceLength)
        self.button_measure = Button(self.frame_tools, text='Start Measuring', width=button_width, command=self.__startMeasure)
        self.button_export_result = Button(self.frame_tools, text='Expert result', width=button_width, command=self.__exportResult)
        self.button_undo = Button(self.frame_tools, text='Undo', width=button_width, command=self.__undo)
        
        self.label_ref_length = Label(self.frame_tools, text='Set real Length (mm):')
        self.entry_ref_length = Entry(self.frame_tools, width=button_width)
        
        self.list_collected = Listbox(self.frame_tools, width=button_width*2)
        
        self.label_status = Label(self.frame_buttom, text="show imformation.")
        
        self.xscroll = Scrollbar(self.frame_canvas, orient=HORIZONTAL)
        self.yscroll = Scrollbar(self.frame_canvas, orient=VERTICAL)
        self.canvas = Canvas(self.frame_canvas, bd=0, 
                             xscrollcommand=self.xscroll.set, 
                             yscrollcommand=self.yscroll.set, 
                             highlightthickness=2,
                             highlightbackground="black")#, width=200, height=100)
    
        self.image_path = ''
        self.scale = 1 # the scale of the calibration # new real value = new pixel distance * (real ref distance / ref pixel distance)
        self.real_object_length = 1 # mm, the length of the real reference target.
        self.workState = WorkState()
        self.current_state = self.workState.INITIALIZATION
        self.calibrationPair = PointCouple()
        self.dimensions = []
        self.dimPntPair = PointCouple()
        self.counter = 0 # measurement counter
        self.dim_index = 0 # the index of measurement, do not include the calibration
        self.stack = [] # action stack
        self.drawState = DrawState()
        
        self.initGUI()
        
    def initGUI(self):
        self.frame_tools.grid(rowspan=2, column=0, sticky='ns')
        self.frame_canvas.grid(row=0,column=1, sticky='nsew')
        self.frame_buttom.grid(row=1,columnspan=2, sticky='ew')
        
        # widget grid
        # frame tools
        self.label_file_path.grid(row=0, column=0, columnspan=2, sticky='ew')
        self.button_load_path.grid(row=1, column=0, columnspan=1, sticky='ew')
        self.button_load_image.grid(row=1, column=1, columnspan=1, sticky='ew')
        self.label_ref_length.grid(row=2, column=0, columnspan=2, sticky='ew')
        self.entry_ref_length.grid(row=3, column=0, columnspan=2, sticky='ew')
        self.button_set_ref_length.grid(row=4, column=0, columnspan=2, sticky='ew')
        self.button_calibrate.grid(row=5, column=0, columnspan=2, sticky='ew')
        self.button_measure.grid(row=6, column=0, columnspan=2, sticky='ew')
        self.button_export_result.grid(row=7, column=0, columnspan=2, sticky='ew')
        self.button_undo.grid(row=8, column=0, columnspan=2, sticky='ew')
        self.list_collected.grid(row=9, column=0, columnspan=2, sticky='ew', padx=3, pady=3)
        
        
        # frame buttom 
        self.label_status.grid(row=0, column=0, sticky='w')
        #frame canvas
        self.frame_canvas.grid_rowconfigure(0, weight = 1)
        self.frame_canvas.grid_columnconfigure(0, weight = 1)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.xscroll.grid(row=1, column=0, sticky='ew')
        self.yscroll.grid(row=0, column=1, sticky='ns')
        
        self.xscroll.config(command=self.canvas.xview)
        self.yscroll.config(command=self.canvas.yview)
        
        self.canvas.bind("<Button 1>",self.__getCoordinate)
        
        self.master.minsize(width=600,height=400);
        
    
    def __showStatus(self, data):
        self.label_status.configure(text=data)
    
    def __getCoordinate(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.__showStatus('event: ({}, {}), (x, y): ({}, {})'.format(event.x, event.y, x, y))
        
        if self.current_state == self.workState.CALIBRATING and not self.calibrationPair.isFull():
            self.__measureReferenceObject(x, y)
        if self.current_state == self.workState.MEASURE:
            self.__measureDimension(x, y)
            
            
    def __measureDimension(self, x, y):
        if self.counter % 2 == 0:
            # the first click
            self.dimPntPair.p1_x = x
            self.dimPntPair.p1_y = y
            ac = self.canvas.create_oval(x-circle_radius, y-circle_radius, x + circle_radius, y+circle_radius, fill='green')
            self.stack.append(ac)
            
        elif self.counter % 2 == 1:
            self.dimPntPair.p2_x = x
            self.dimPntPair.p2_y = y
            ac = self.canvas.create_oval(x-circle_radius, y-circle_radius, x + circle_radius, y+circle_radius, fill='green')
            self.stack.append(ac)
            self.__drawPointCoupleLine(self.dimPntPair)
            
            dis = self.dimPntPair.distance()
            dis = dis * self.scale
            self.dimensions.append(dis)
            index = self.counter // 2
            
            ac = self.canvas.create_text(x+10, y+10,fill='red', font=("Purisa", 12), text = str(index))
            self.stack.append(ac)
            
            self.list_collected.insert(END, 'dim {}: {}'.format(index, dis))
            
            self.__showStatus('dimension {}, value: {}'.format(index, dis))
        self.counter += 1
            
            
    def __measureReferenceObject(self, x, y):
        if not self.calibrationPair.isP1Full():
            self.calibrationPair.p1_x = x
            self.calibrationPair.p1_y = y
            self.canvas.create_oval(x-circle_radius, y-circle_radius, x + circle_radius, y+circle_radius, fill='red')
            return
        if not self.calibrationPair.isP2Full():
            self.calibrationPair.p2_x = x
            self.calibrationPair.p2_y = y
            self.canvas.create_oval(x-circle_radius, y-circle_radius, x + circle_radius, y+circle_radius, fill='red')
            self.__drawPointCoupleLine(self.calibrationPair)
            
            #compute scale
            self.scale = self.real_object_length / self.calibrationPair.distance()
            self.__showStatus('Reference calibraetd! The scale is {}.'.format(self.scale))
            
            if self.calibrationPair.isFull():
                self.current_state = self.workState.CALIBRATED
            return
                
    def __drawPointCoupleLine(self, pc = PointCouple()):
        # draw the line between the point couple
        ac = self.canvas.create_line(pc.p1_x, pc.p1_y, pc.p2_x, pc.p2_y)
        self.stack.append(ac)
    
    def __loadImagePath(self):
        self.image_path = askopenfilename(parent=self.master, title='choose hand image!')
        self.text_path.set(self.image_path)
        self.__showStatus('Load image: {}'.format(self.image_path))
    
    def __loadImage(self):
        image = ImageTk.PhotoImage(Image.open(self.image_path))
        self.canvas.image = image
        img_w = image.width()
        img_h = image.height()
        
        # limit the window
        if img_w >= 960:
            img_w = 960
        if img_h >= 540:
            img_h = 540
                
        self.canvas.create_image(0, 0, image=image, anchor='nw')
        self.canvas.config(scrollregion=self.canvas.bbox(ALL), width = img_w, height = img_h)
        self.canvas.update()
    
    def __calibrate(self):
        self.label_status.configure(text='Select 2 points of a line that known its real distance.')
        self.button_calibrate.config(state=DISABLED)
        self.current_state = self.workState.CALIBRATING
    
    def __setReferenceLength(self):
        data = self.entry_ref_length.get()
        if data:
            self.real_object_length = float(data)
            self.__showStatus('real reference object length: {}'.format(data))
        else:
            self.__showStatus('Enter one value please!')
    
    def __startMeasure(self):
        if self.current_state == self.workState.CALIBRATED:
            self.current_state = self.workState.MEASURE
            self.label_status.configure(text='Start measuring distance! State: Measure')
        
    
    def __exportResult(self):
        self.label_status.configure(text='Export the result!')
        
        pass
    
    def __undo(self):
        self.label_status.configure(text='Undo last step!')
        ac = self.stack.pop()
        self.canvas.delete(ac)
    
        
    def run(self):
        self.master.mainloop()




