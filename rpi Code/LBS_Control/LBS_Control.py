#! /usr/bin/env python

        #XXX add something here later about open source stuff

#Shawn Wright
#Linear book Scanner Code

import pygtk
pygtk.require('2.0')
import gtk
import shelve

import glib
import pexpect
import spidev
import RPi.GPIO as GPIO
import time


# Interfacing with the Micro: FIrst pull the reset pin down to gmd
# to reset it (when the pi boots shomehow it puts the micro into an
# unknown state that I'm not sure whats going on yet)

#Then when the micro's enable pin is high it will try to move the motor
# To the given position at the given velocity.  

# With the enable pin low you can either set the position or send a position
# for it to go to, with a velocity percent (100% should be 500 rpm)


GPIO.setmode(GPIO.BCM)


GPIO.setup(18, GPIO.OUT)
GPIO.output(18, GPIO.HIGH) #Pull low to reset

GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW) #Pull low to reset


#These will be for the limit switches some day
#GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)


spi = spidev.SpiDev()

spi.open(0,0)
spi.max_speed_hz = 500000  #XXX Make faster?


class LBS_Number_Setting:
    def new_value(self, new_value):
        
        try:
            new_value = float(new_value)
            if( (new_value > self.min) and (new_value < self.max) ):
                self.current_value = new_value
                self.old_value = current_value;
        except: 
            pass
        

    def get_current_value(self):
        return self.current_value
        
            
    def old_value(self):
        return self.old_value


    def load_variable(self):
        try:
            with open(self.filename) as file:
                pass
        except IOError as e:
            return 
        
        my_shelf = shelve.open(self.filename)
        
        #load current value if it exists
        try:
            self.current_value =  my_shelf[self.key+'_current_value']
        except:
            pass


        #load old value if it exists
        try:
            self.old_value =  my_shelf[self.key+'_old_value']
        except:
            self.old_value = 0;
       
        my_shelf.close()



    def save_variable(self):
        my_shelf = shelve.open(self.filename)

        my_shelf[self.key+'_current_value'] = self.current_value
        my_shelf[self.key+'_old_value'] = self.old_value
        
        my_shelf.close()


    def update_variable(self, widget):
        self.old_value = self.current_value
        
        try:
            self.current_value = float(self.textbox.get_text())
        except:
            return
        
        if( self.current_value > self.max):
            self.current_value = self.max  
        
        if( self.current_value < self.min):
            self.current_value = self.min  
        
       
        self.label_current.set_text(str(self.current_value))
        self.label_old.set_text(str(self.old_value)) 
        
        self.save_variable()


    def textbox_on_changed(self, widget):
        text = self.textbox.get_text().strip()
        self.textbox.set_text(''.join([i for i in text if i in '0123456789.']))



    def __init__(self, description, unit, current_value, min, max, key, filename) :
        
        self.description = str(description)
        self.unit = str(unit)
        self.current_value = current_value
        self.old_value = 0
        self.min = min
        self.max = max
        self.key = key
        self.filename = filename

        self.load_variable()
        self.save_variable()
        

        self.label_description = gtk.Label(str(self.description))
        self.label_unit = gtk.Label(str(self.unit))
        self.label_current = gtk.Label(str(self.current_value))
        self.label_old = gtk.Label(str(self.old_value)) 
        self.label_min = gtk.Label(str(self.min))
        self.label_max = gtk.Label(str(self.max))
       
        self.label_description.set_width_chars(30)
        self.label_unit.set_width_chars(5)
        self.label_current.set_width_chars(5)
        self.label_old.set_width_chars(5) 
        self.label_min.set_width_chars(5)
        self.label_max.set_width_chars(5)
      
        self.label_description.set_alignment(xalign=0,yalign=0.5)
        self.label_unit.set_alignment(xalign=0.5,yalign=0.5)
        self.label_current.set_alignment(xalign=.5,yalign=0.5)
        self.label_old.set_alignment(xalign=.5,yalign=0.5) 
        self.label_min.set_alignment(xalign=.5,yalign=0.5) 
        self.label_max.set_alignment(xalign=.5,yalign=0.5) 
        
        
        #Apply Button and button box to get right border
        self.textbox = gtk.Entry()
        self.textbox.set_width_chars(10)
        self.textbox.connect('changed', self.textbox_on_changed)

       
        
        self.apply_button = gtk.Button("Apply")
        self.apply_button.connect('clicked', self.update_variable)
        self.apply_button_box = gtk.HButtonBox()
        self.apply_button_box.set_layout('start')
        self.apply_button_box.set_border_width(10)
        self.apply_button_box.set_child_size(60,10)
        self.apply_button_box.add(self.apply_button)
       

        #pack it all in a box
        self.hbox = gtk.HBox()
        self.hbox.pack_start(self.label_description)
        self.hbox.pack_start(self.label_unit)
        self.hbox.pack_start(self.label_current)
        self.hbox.pack_start(self.textbox)
        self.hbox.pack_start(self.label_old)
        self.hbox.pack_start(self.label_min)
        self.hbox.pack_start(self.label_max)
        self.hbox.pack_start(self.apply_button_box) 
        


class LBS_Control:
    
    FILENAME='LBS_Settings.db'
    LBS_IMAGE_FILE = 'LBS_Main_Image.jpg'

###############################
#  List of Flags
#    ENABLE_PIN (1 and the stepper moves if not at commanded position)
#    MOVING (0 if at commanded position)
#    INITIALIZED (set to 1 when the system is initialzed)
#
#
#  NEW List of Pins
# GPIO 18 - Micro Reset Pin (PC6)
# GPIO 17 - Micro Enable Pin (PB0)
# 
# SCK - Micro SCK (PB5)
# MISO - Micro MISO (PB4)
# MOSI - Micro MOSI (PB3)



# Stlll need to relocate these pins
#  GPIO 14 - Green Light
#  GPIO 15 - Yellow Light
#  GPIO 18 - Red Light
#  GPIO 23 - Green Button
#  GPIO 24 - Yellow Button
#  GPIO 25 - Red Button
#  GPIO 8 - Blue Tube LED
#  GPIO 22 - Home Limit Switch
#  GPIO 4 - End Lmit Switch
###############################



    #These funcitons are for the GPIO pins
    def micro_reset(self):
        #Make pin high, turn BJT on, make reset pin go down, wait a little, turn off
        GPIO.output(18, GPIO.LOW)
        time.sleep(0.01) #sleep 10ms
        GPIO.output(18,GPIO.HIGH)

    
    def enable_pin(self,enable):
    	if enable:
            GPIO.output(17,GPIO.HIGH)
            self.ENABLE_PIN = 1
        else:
            GPIO.output(17,GPIO.LOW)
            self.ENABLE_PIN = 0


#    def green_light(self, enable):
#   	if enable:
#            GPIO.output(14,GPIO.HIGH)
#        else:
#            GPIO.output(14,GPIO.LOW)

#    def yellow_light(self, enable):
#    	if enable:
#            GPIO.output(15,GPIO.HIGH)
#        else:
#            GPIO.output(15,GPIO.LOW)

#    def red_light(self, enable):
#    	if enable:
#            GPIO.output(18,GPIO.HIGH)
#        else:
#            GPIO.output(18,GPIO.LOW)

#    def blue_light(self, enable):
#    	if enable:
#            GPIO.output(8,GPIO.HIGH)
#        else:
#            GPIO.output(8,GPIO.LOW)


#    def home_limit_switch(self):
#        if GPIO.input(22):#XXX
#            return False
#        else:
#            print "At home limit switch"
#            return True


#    def end_limit_switch(self):
#        if GPIO.input(4): #XXX
#            return False
#        else:
#            print "At home limit switch"
#            return True 

#    def green_push_button(self):
#        if GPIO.input(23): #XXX
#            return False
#        else:
#            print "Green Push Button Pressed"
#            return True 
    
    
#    def yellow_push_button(self):
#        if GPIO.input(24): #XXX
#            return False
#        else:
#            print "Yellow Push Button Pressed"
#            return True 
    
#    def red_push_button(self):
#        if GPIO.input(25): #XXX
#            return False
#        else:
#            print "Red Push Button Pressed"
#            return True 

###############################
###############################



    #This closes everything    
    def destroy(self, widget, data=None):
        gtk.main_quit()
        GPIO.cleanup()


    #This makes textboxes only input numbers and -
    def number_textbox_on_changed(self, widget):
        text = widget.get_text()
        widget.set_text(''.join([i for i in text if i in '-0123456789']))


    #How a button calles send position
    def send_position_clicked(self,widget):
        position =  int(self.manual_control_position_textbox.get_text())
        velocity = int(self.manual_control_velocity_textbox.get_text())
        self.send_position(position, velocity)
        self.INITIALIZED = False #moved it manually, no longer initialized

    def send_position_1_clicked(self,widget):
        position = 32000
        velocity = 40
        self.send_position(position, velocity)

    def send_position_2_clicked(self,widget):
        position = 20000
        velocity = 150
        self.send_position(position, velocity)

    def send_position_3_clicked(self,widget):
        position = -20000
        velocity = 150
        self.send_position(position, velocity)

    def send_position_4_clicked(self,widget):
        position = -32000
        velocity = 150
        self.send_position(position, velocity)









    #Sends the position to the microcontroller        
    def send_position(self,position, velocity):
        #self.micro_reset()
        #time.sleep(.1)
        
        self.enable_pin(0)


        temp1 = int(position)>>8
        temp2 = int(position) & 0xFF

    	print "Sending Position:"
        print spi.xfer([240])
    	print spi.xfer([temp1])
    	print spi.xfer([temp2])
    	print spi.xfer([velocity])

        self.enable_pin(1)
        self.MOVING = 1 #XXX is this needed wihth a single cycle?
    
    
    #How a button calls set position
    def set_position_clicked(self,widget):
        position =  int(self.manual_control_position_textbox.get_text())
        self.set_position(position)
        self.INITIALIZED = False #moved it manually, no longer initialized


    #Sets the current position in the steppers micro
    def set_position(self, position):
        print "Setting Current  Position"
	
        self.enable_pin(0)
	
        temp1 = int(position)>>8
        temp2 = int(position) & 0xFF
       
    	print spi.xfer([241])
    	print spi.xfer([temp1])
    	print spi.xfer([temp2])
    	print spi.xfer([0]) #This byte doesn't do anything

        self.enable_pin(1)



    def initialize(self, widget):
        
        #set initialize flag
        self.CURRENT_COMMAND = "Initialize_0"

   
    #Automatic page start button to start a cycle and disable buttons  
    def start(self, widget):

        if(widget.get_label() == "Start"):
            widget.set_label("Stop")
            self.automatic_button_select_folder.set_sensitive(False)
            self.automatic_button_initialize.set_sensitive(False)
            self.show_automatic_control_button.set_sensitive(False)
            self.show_manual_control_button.set_sensitive(False)
            self.show_settings_button.set_sensitive(False)
            self.variable_1.apply_button.set_sensitive(False) 
            self.variable_2.apply_button.set_sensitive(False) 
            self.variable_3.apply_button.set_sensitive(False) 
            self.variable_4.apply_button.set_sensitive(False) 
            self.variable_5.apply_button.set_sensitive(False) 
            self.variable_6.apply_button.set_sensitive(False) 
            self.CURRENT_COMMAND = "Scan_Cycle_0"
        
        
        elif(widget.get_label() == "Stop"):
            widget.set_label("Start")
            self.automatic_button_select_folder.set_sensitive(True)
            self.automatic_button_initialize.set_sensitive(True)
            self.show_automatic_control_button.set_sensitive(True)
            self.show_manual_control_button.set_sensitive(True)
            self.show_settings_button.set_sensitive(True)
            self.variable_1.apply_button.set_sensitive(True) 
            self.variable_2.apply_button.set_sensitive(True) 
            self.variable_3.apply_button.set_sensitive(True) 
            self.variable_4.apply_button.set_sensitive(True) 
            self.variable_5.apply_button.set_sensitive(True) 
            self.variable_6.apply_button.set_sensitive(True) 
            self.CURRENT_COMMAND = "Stop"




    def main_loop(self):

        self.update_current_position()
        

        if self.CURRENT_COMMAND == "Stop":
            self.micro_reset()
            self.CURRENT_COMMAND = "Idel"


        #In idel state check for button push
        if self.CURRENT_COMMAND == "Idel":
            pass


        if self.CURRENT_COMMAND == "Initialize_0":
            self.set_position(0)

            self.send_position(-1000,
                                    int(self.variable_6.get_current_value()))
            self.CURRENT_COMMAND = "Initialize_1"
       
        
        if ((self.CURRENT_COMMAND == "Initialize_1") and (self.MOVING == 0)):
            self.set_position(-32000)
            self.CURRENT_COMMAND = "Idel"
            






        # variable_1 - Steps per inch
        # Variable_2 - Distance to end of scan
        # Variable_3 - Scan Velocity Percent
        # Variable_4 - Distacne to End Stop
        # Variable_5 - Post Scan Velocity Percent
        # Variable_6 - Reverse Velocity Percent

        #moves throught the scan


        if self.CURRENT_COMMAND == "Scan_Cycle_0":
            print "cycle 0"
            self.send_position(-32000+int(self.variable_1.get_current_value() *
                                     int(self.variable_2.get_current_value())),
                                     int(self.variable_3.get_current_value()))

            self.CURRENT_COMMAND = "Scan_Cycle_1"
            

        
        #moves to the end
        if ((self.CURRENT_COMMAND == "Scan_Cycle_1") and (self.MOVING == 0)):
            print "cycle 1"
            self.send_position(-32000+int(self.variable_1.get_current_value() *
                                    int(self.variable_4.get_current_value())),
                                    int(self.variable_5.get_current_value()))
           
            self.CURRENT_COMMAND = "Scan_Cycle_2"


        #moves to the home
        if ((self.CURRENT_COMMAND == "Scan_Cycle_2") and (self.MOVING == 0)):
            print "cycle 2"
            self.send_position(-32000,
                                    int(self.variable_6.get_current_value()))
           
            #Turn stop to start button since we are done
            self.automatic_button_start.set_label("Start")
            self.automatic_button_select_folder.set_sensitive(True)
            self.automatic_button_initialize.set_sensitive(True)
            self.show_automatic_control_button.set_sensitive(True)
            self.show_manual_control_button.set_sensitive(True)
            self.show_settings_button.set_sensitive(True)
            self.variable_1.apply_button.set_sensitive(True) 
            self.variable_2.apply_button.set_sensitive(True) 
            self.variable_3.apply_button.set_sensitive(True) 
            self.variable_4.apply_button.set_sensitive(True) 
            self.variable_5.apply_button.set_sensitive(True) 
            self.variable_6.apply_button.set_sensitive(True) 
            
            self.CURRENT_COMMAND = "Idel"
        
           
        glib.timeout_add(100, self.main_loop)


    def create_navigation_window(self):
        #Set the window parameters
        self.navigation_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.navigation_window.set_position(gtk.WIN_POS_CENTER)
        self.navigation_window.set_size_request(300, 50)
        self.navigation_window.set_title("LBS Navigation")


        #Configure buttonss
        self.show_automatic_control_button = gtk.Button("Automatic")
        self.show_automatic_control_button.connect('clicked', self.show_automatic_control_window) 
       
        self.show_manual_control_button = gtk.Button("Manual")
        self.show_manual_control_button.connect('clicked', self.show_manual_control_window)
        
        self.show_settings_button = gtk.Button("Settings")
        self.show_settings_button.connect('clicked', self.show_settings_window)
       
        
        #Pack buttons into boxess
        self.navigation_box = gtk.HButtonBox()
        self.navigation_box.set_layout('spread')
        self.navigation_box.set_spacing(5)
        self.navigation_box.set_child_size(60,10)
        self.navigation_box.add(self.show_automatic_control_button)
        self.navigation_box.add(self.show_manual_control_button)
        self.navigation_box.add(self.show_settings_button)

       
        #Load the window
        self.navigation_window.add(self.navigation_box)
        self.navigation_window.connect('destroy', self.destroy)
    

    def show_navigation_window(self):
        self.navigation_window.show_all()
       

    def create_automatic_control_window(self):
        #Set the window parameters
        self.automatic_control_window = gtk.Window()
        self.automatic_control_window.set_size_request(500, 400)
        self.automatic_control_window.set_title("LBS Automatic Control")

        self.LBS_image = gtk.Image()
        pixbuf = gtk.gdk.pixbuf_new_from_file(self.LBS_IMAGE_FILE)
        scaled_pixbuf = pixbuf.scale_simple(300,150,gtk.gdk.INTERP_BILINEAR)
        self.LBS_image.set_from_pixbuf(scaled_pixbuf)


        self.automatic_button_select_folder = gtk.Button("Select Folder")
        self.automatic_button_select_folder.connect('clicked', self.select_folder)
        
        self.automatic_button_initialize = gtk.Button("Initialize")
        self.automatic_button_initialize.connect('clicked', self.initialize)
        
        self.automatic_button_start = gtk.Button("Start")
        self.automatic_button_start.connect('clicked', self.start)
        
        self.save_directory_label = gtk.Label("NA")
        
        self.automatic_jobname_label = gtk.Label('Jobname:')
        self.automatic_jobname_textbox = gtk.Entry()
        self.automatic_jobname_hbox = gtk.HBox()
        self.automatic_jobname_hbox.pack_start(self.automatic_jobname_label,
                                                 expand=False, padding=14)
        self.automatic_jobname_hbox.pack_start(self.automatic_jobname_textbox,
                                                 expand=False, padding=0)
        
                
        

        settings_label_col_max = gtk.Label("Max")
        

        self.automatic_h_button_box = gtk.HButtonBox()
        self.automatic_h_button_box.set_layout('center')
        self.automatic_h_button_box.set_border_width(10)
        self.automatic_h_button_box.set_child_size(60,15)
        self.automatic_h_button_box.add(self.automatic_button_select_folder)
        self.automatic_h_button_box.add(self.automatic_button_initialize)
        self.automatic_h_button_box.add(self.automatic_button_start)
         

        self.automatic_vbox = gtk.VBox()
        self.automatic_vbox.pack_start(self.LBS_image)
        self.automatic_vbox.pack_start(self.automatic_h_button_box)
        self.automatic_vbox.pack_start(self.save_directory_label)
        self.automatic_vbox.pack_start(self.automatic_jobname_hbox)


        #put the main box into the window
        self.automatic_control_window.add(self.automatic_vbox)

        self.automatic_control_window.connect("delete-event",self.hide_automatic_control_window) 
        
       
    
               
        
    def select_folder(self, widget, data=None):
        self.filechooser_window = gtk.Window()
        self.filechooser = gtk.FileChooserDialog('Select Directory', self.filechooser_window, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, ('Cancel', 1, 'Open', 2))

        ans = self.filechooser.run()
        
        if ans == 2:
            self.save_directory = self.filechooser.get_filename()
            self.save_directory_label.set_text(self.save_directory)
            self.filechooser.destroy()
        else:
            self.filechooser.destroy()

        

    def show_automatic_control_window(self, widget):
        self.automatic_control_window.show_all()


    def hide_automatic_control_window(self, widget, event):
        self.automatic_control_window.hide_all()
        return True




    def create_manual_control_window(self):
        #Set the window parameters
        self.manual_control_window = gtk.Window()
        self.manual_control_window.set_size_request(400, 200)
        self.manual_control_window.set_title("LBS Manual Control")
        self.manual_control_window.set_tooltip_text("Use this utility to manually move the stepper.") 


        
        self.manual_control_window.connect("delete-event",self.hide_manual_control_window) 
              
        self.send_position_button = gtk.Button("Send Position")
        self.send_position_button.connect('clicked', self.send_position_clicked)
        
        self.set_position_button = gtk.Button("Set Position")
        self.set_position_button.connect('clicked', self.set_position_clicked)


#XXX Weird Shit

        self.send_position_1_button = gtk.Button("First")
        self.send_position_1_button.connect('clicked', self.send_position_1_clicked)

        self.send_position_2_button = gtk.Button("Second")
        self.send_position_2_button.connect('clicked', self.send_position_2_clicked)

        self.send_position_3_button = gtk.Button("Third")
        self.send_position_3_button.connect('clicked', self.send_position_3_clicked)

        self.send_position_4_button = gtk.Button("Fourth")
        self.send_position_4_button.connect('clicked', self.send_position_4_clicked)


        self.manual_control_box_grr = gtk.HBox()
        self.manual_control_box_grr.pack_start(self.send_position_1_button)
        self.manual_control_box_grr.pack_start(self.send_position_2_button)
        self.manual_control_box_grr.pack_start(self.send_position_3_button)
        self.manual_control_box_grr.pack_start(self.send_position_4_button)





        self.manual_control_label_1 = gtk.Label("Position: ")
        self.manual_control_label_2 = gtk.Label("Velocity %: ")
        self.manual_control_label_3 = gtk.Label("The Current Position is: ")
        self.manual_control_label_4 = gtk.Label("N/A")
       
        self.manual_control_position_textbox = gtk.Entry()
        self.manual_control_position_textbox.connect('changed', self.number_textbox_on_changed)
       
        self.manual_control_velocity_textbox = gtk.Entry()
        self.manual_control_velocity_textbox.connect('changed', self.number_textbox_on_changed)
 
      # self.textbox_2.connect('changed', self.new_text)
       

        self.manual_control_box_1 = gtk.HBox()
        self.manual_control_box_1.pack_start(self.manual_control_label_1)
        self.manual_control_box_1.pack_start(self.manual_control_position_textbox)
        
       
        self.manual_control_box_2 = gtk.HBox()
        self.manual_control_box_2.pack_start(self.manual_control_label_2)
        self.manual_control_box_2.pack_start(self.manual_control_velocity_textbox)
       
        self.manual_control_box_3 = gtk.HBox()
        self.manual_control_box_3.pack_start(self.send_position_button)
        self.manual_control_box_3.pack_start(self.set_position_button)
      
        self.manual_control_box_4 = gtk.HBox()
        self.manual_control_box_4.pack_start(self.manual_control_label_3)
        self.manual_control_box_4.pack_start(self.manual_control_label_4)
      
        self.manual_control_box_5 = gtk.VBox()
        self.manual_control_box_5.pack_start(self.manual_control_box_1)
        self.manual_control_box_5.pack_start(self.manual_control_box_2)
        self.manual_control_box_5.pack_start(self.manual_control_box_3)
        self.manual_control_box_5.pack_start(self.manual_control_box_4)
        self.manual_control_box_5.pack_start(self.manual_control_box_grr)
  
        self.manual_control_window.add(self.manual_control_box_5)
        
        self.manual_control_window.connect("delete-event",self.hide_manual_control_window) 



    def show_manual_control_window(self, widget):
        self.manual_control_window.show_all()
        

    def hide_manual_control_window(self, widget, event):
        self.manual_control_window.hide_all()
        return True




    def create_settings_window(self):
        #Set the window parameters
        self.settings_window = gtk.Window()
        self.settings_window.set_size_request(750, 350)
        self.settings_window.set_title("LBS Settings")

        #These are text for colum headings
        self.settings_label_col_description = gtk.Label("Setting Description")
        self.settings_label_col_unit = gtk.Label("Unit")
        self.settings_label_col_current = gtk.Label("Current")
        self.settings_label_col_entry = gtk.Label("New")
        self.settings_label_col_old = gtk.Label("Old")
        self.settings_label_col_min = gtk.Label("Min")
        self.settings_label_col_max = gtk.Label("Max")
        self.settings_label_col_apply = gtk.Label("     ")
       
       
        self.settings_label_col_description.set_width_chars(30)
        self.settings_label_col_unit.set_width_chars(5)
        self.settings_label_col_current.set_width_chars(5)
        self.settings_label_col_entry.set_width_chars(10) 
        self.settings_label_col_old.set_width_chars(5)
        self.settings_label_col_min.set_width_chars(5)
        self.settings_label_col_max.set_width_chars(5)
        self.settings_label_col_apply.set_width_chars(9)
        
        self.settings_label_col_description.set_alignment(xalign=0.5,yalign=0.5)
        self.settings_label_col_unit.set_alignment(xalign=0.2,yalign=0.5)
        self.settings_label_col_current.set_alignment(xalign=0,yalign=0.5)
        self.settings_label_col_old.set_alignment(xalign=0.4,yalign=0.5) 
        self.settings_label_col_min.set_alignment(xalign=0.4,yalign=0.5) 
        self.settings_label_col_max.set_alignment(xalign=0.4,yalign=0.5) 
        self.settings_label_col_apply.set_alignment(xalign=0,yalign=0.5) 
        
        
      
        
        self.settings_box_col_description = gtk.HBox() 
        self.settings_box_col_description.pack_start(self.settings_label_col_description)
        self.settings_box_col_description.pack_start(self.settings_label_col_unit)
        self.settings_box_col_description.pack_start(self.settings_label_col_current)
        self.settings_box_col_description.pack_start(self.settings_label_col_entry)
        self.settings_box_col_description.pack_start(self.settings_label_col_old)
        self.settings_box_col_description.pack_start(self.settings_label_col_min)
        self.settings_box_col_description.pack_start(self.settings_label_col_max)
        self.settings_box_col_description.pack_start(self.settings_label_col_apply)



        # variable_1 - Steps per inch
        # Variable_2 - Distance to end of scan
        # Variable_3 - Scan Velocity Percent
        # Variable_4 - Distacne to End Stop
        # Variable_5 - Post Scan Velocity Percent
        # Variable_6 - Reverse Velocity Percent

        self.variable_1 = LBS_Number_Setting('Steps per inch:', 
                                           '(steps/in)', 1600, 100, 4000, 'var_1', self.FILENAME)
         
        self.variable_2 = LBS_Number_Setting('Distance to end of scan:', 
                                                '(in)', 10, 5, 16, 'var_2', self.FILENAME)
                                                
        self.variable_3 = LBS_Number_Setting('Scan velocity percent:', 
                                                '(%)', 20, 5, 50, 'var_3', self.FILENAME)
        
        self.variable_4 = LBS_Number_Setting('Distance to end stop:', 
                                                '(in)', 20, 16, 40, 'var_4', self.FILENAME)
    
        self.variable_5 = LBS_Number_Setting('Post scan velocity percent:', 
                                                '(%)', 60, 25, 255, 'var_5', self.FILENAME)
        
        self.variable_6 = LBS_Number_Setting('Reverse velocity percent:', 
                                                '(%)', 60, 25, 255, 'var_6', self.FILENAME)
        
    

        #Stick it all in the main box
        self.settings_vbox_variables_and_titles = gtk.VBox()
        self.settings_vbox_variables_and_titles.set_border_width(10)
        self.settings_vbox_variables_and_titles.pack_start(self.settings_box_col_description)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_1.hbox)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_2.hbox)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_3.hbox)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_4.hbox)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_5.hbox)
        self.settings_vbox_variables_and_titles.pack_start(self.variable_6.hbox)
        

       # print self.variable_one.get_current_value() 
        
        #put the main box into the window
        self.settings_window.add(self.settings_vbox_variables_and_titles)
        self.settings_window.connect("delete-event",self.hide_settings_window) 
     
     
    def show_settings_window(self, widget):
        self.settings_window.show_all()


    def hide_settings_window(self, widget, event):
        self.settings_window.hide_all()
        return True


        
    def update_current_position(self):
        if(self.ENABLE_PIN == 0):
            return
            
        temp1 = spi.xfer([0])
        temp2 = spi.xfer([0])
        temp3 = spi.xfer([0])
    	
        temp2 = temp2[0]
        temp3 = temp3[0]

        negative = 1
        if(temp2 & 0b10000000):
            temp2 = (~temp2 & 0xFF)
            temp3 = (~temp3 & 0xFF) + 1
            negative = -1


        self.MOVING = temp1[0]
        current_pos = temp2*256 + temp3
        current_pos = current_pos * negative

        self.manual_control_label_4.set_text(str(current_pos) + " MOVING: " + str(self.MOVING))



    def __init__(self):
        self.CURRENT_COMMAND = "Idel"
        self.enable_pin(0)
        self.micro_reset()
        
        self.create_navigation_window()
        self.create_automatic_control_window()
        self.create_manual_control_window()
        self.create_settings_window()
    
        self.show_navigation_window()
       
        settings = shelve.open('LBS_Settings.db')
     
        self.CURRENT_COMMAND = "Idel"
        self.main_loop() 

    def main(self):
        gtk.main()



#Start the windows!
if __name__ == "__main__":
    LBS = LBS_Control()
    LBS.main()
        
