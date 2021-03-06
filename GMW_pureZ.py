
#********************** 2017/01/30 Version ********************#
# Note: Threading added in the measureMethod()
# Note: The listbox will now always show the latest measured data
# Note: Threading can avoid non-responsive problem, but will also cause
#       the intereference by clicking other buttons during measurement.
# Note: Keithley current option added.
# Note: All output will be shut down by clicking quit
# Note: Create the K2400 current stepping function

#********************** 2017/03/30 Version ********************#
# Note: Modification on data plots (dots and lines)
# Note: Saving files with date and time

#********************** 2017/06/15 Version ********************#
# Note: Saving files with measured channel resistance

#********************** 2018/01/11 Version ********************#
# Note: Added comments for clarity
# Note: Cleaned up code for easier reading
# Note: Unnecessary variables removed
# Note: Amplifier protect added.
# Note: Save function updated to include sample name
# Note: Read me added
# Note: Data value changed to match multimeasure for Keithley

#********************** 2018/01/26 Version ********************#
# Note: Loop made to run from low to high
# Note: Added delay to minimize initial noise

#********************** 2018/05/18 Version ********************#
# Note: Title added
# Note: Print statements made to display in Listbox
# Note: Save function variables rounded to 2 decimals, listbox variables to 4 decimals
# Note: Updated Hx loop to allow for a negative to positive Hx values

#********************** 2020/04/23 Version ********************#
# Note: GMW VectorMagnet replace the lock-in
# Note: Consider the mixed Hx + Hz is produced by adding the voltage 
#       of each output channel linearly
# Note: readtask() results & wigit are not yet finished

#********************** 2020/05/22 Version ********************#
# Note: Remove all the lock-in amp terms
# Note: New function about measuring field has been added
#       including every method and write the data into csv
# Note: Further calibration of conversion constant is required
#       output and input calibration values have different unit
# Note: No yet tested

from tkinter import *
from tkinter import ttk
import tkinter
from tkinter import filedialog
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pylab
from pylab import *
import os
import math
import numpy
#from LockinAmp import lockinAmp
import nidaqmx
from keithley2400_I import Keithley2400
from keithley import Keithley
import time
import multiprocessing
import threading
from datetime import datetime

root = Tk()
root.title("GMW pure Hz")

def main():

    global result, average, directory, dot_size, dot_edge, xchan, ychan, zchan

    directory = os.getcwd()


    xchan=0 #Set a default iutput x channel for field measurement
    ychan=1
    zchan=2

    read_me = 'This program sweeps Hz over a range of currents supplied by Keithley2400.\
    Voltage measurements are taken by Keithley2000. The loop runs from low field strength to high'

    print(read_me)

    dot_size=10 #Set a default data dot size
    dot_edge=0.5 #Set a default data dot edge width

    result=['']
    values_y=[]
    values_x=[]

    createWidgit()

    root.protocol('WM_DELETE_WINDOW', quit)
    root.mainloop()

#************************Main End Here***************************#


# Measures Voltage over series of Hz field strengths for set current and Hx field.
def measureMethod(_interval, _number, _output, _average, _current, _step, _sample, _intervalfield):

    # _current: max and min values of current sweep, current supplied by Keithley2400
    # _sense: sensitvity value for Lock-in Amp
    # _sample: sample name for save file
    i=float(_interval) # Z field V/Oe conversion value (for GMW)
    n=int(_number) # number of points measured in Hz field range
    average=int(_average) # number of measurements averaged by Keithley2000
    ifield=float(_intervalfield) # Measured field Oe/V conversion value (for GMW sensor)



    def event():

        keith=Keithley2400(f) #Initiate K2400
        keith2000=Keithley(f) #Initiate K2000

        writetask = nidaqmx.Task() #Initiate GMW write & read channels
        readtask = nidaqmx.Task()

        Va_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao0")
        Vb_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao1")
        Vc_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao2")

        Field_X = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai0")
        Field_Y = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai1")
        Field_Z = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai2")
        #readtask.read() will give [V_ai0, V_ai1, V_ai2]

        current_start=float(_current)
        current_end=float(_current)*(-1)
        current_step=float(_step)

        while current_start>=current_end:
            ax.clear()
            ax.grid(True)
            ax.set_title("Realtime Resistance vs H Plot")
            ax.set_xlabel("Applied Z Field (Oe)")
            ax.set_ylabel("Hall Resistance (Ohm)")

            listbox_l.insert('end',"Now measuring with Idc = %f (mA) " %(current_start))
            listbox_l.see(END)

            #Prepare data entries
            global values_x, values_y, result, canvas

            values_y=[]
            values_x=[]
            result=[]

            #Setup K2400 for current output and resistance measurement
            keith.fourWireOff()
            keith.setCurrent(current_start)
            keith.outputOn()

            index=1
            data=[]
            m_time = []
            m_xfield = []
            m_yfield = []
            m_zfield = []

            while index<=5: #Average of five measurements
                data=data+keith.measureOnce()
                index+=1

            listbox_l.insert('end',"Measured current: %f mA" %(1000*data[2]))
            listbox_l.insert('end',"Measured voltage: %f V" %data[1])
            listbox_l.insert('end',"Measured resistance: %f Ohm" %(data[1]/data[2]))
            listbox_l.see(END)

            resistance = data[1]/data[2]

            #Setup lock-in for dac (Hz field) output
            t=0
            a=(float(_output)/i) * (-1)
            step = (double(_output)/i)/n

            writetask.write([a,a,a])#initial application of field to avoid outliers

            while t < 2*n :

                writetask.write([a,a,a])
                #sleep at start to avoid outliers
                if t < 5:
                    time.sleep(.5)
                start = time.time()
                data=keith2000.measureMulti(average)
                fdata=[0,0,0] # origin measured field is in unit V, ifield is conversion value with unit Oe/V
                findex=1
                while findex<=5: #Average of five measurements
                    fdata=[fdata[i]+readtask.read()[i] for i in range(0,3)]
                    findex+=1
                fielddata=[x*ifield/5 for x in fdata] #while loop is for averaging 5 measurements
                print(fielddata)
                m_zfield.append(fielddata[zchan])
                m_xfield.append(fielddata[xchan])
                m_yfield.append(fielddata[ychan])
                tmp=double(1000*data/current_start) # Voltage from K2000 / Current from K2400 (Hall resistance)
                result.append(tmp)
                values_y.append(tmp)
                values_x.append(a*i)
                #ax.scatter(values_x[-1], values_y[-1], s=50, alpha=0.5)
                mid = time.time()
                ax.plot(values_x, values_y,'b-o', ms=dot_size, mew=dot_edge, alpha=0.5)
                canvas.draw()
                listbox_l.insert('end', "Hall Resistance:" + str(round(tmp,4)) + " Applied Field:" + str(round(a*i,4)) + " Measured Field:" + str(round(fielddata[zchan],4)))
                t+=1
                a+=step
                listbox_l.see(END)
                fin = time.time()
                m_time.append(fin-start)
                print('Total Time: ', (fin-start), '\n Plot time: ', (fin-mid))

            while t <= 4*n :

                start = time.time()
                writetask.write([a,a,a])
                data=keith2000.measureMulti(average)
                fdata=[0,0,0] # origin measured field is in unit V, ifield is conversion value with unit Oe/V
                findex=1
                while findex<=5: #Average of five measurements
                    fdata=[fdata[i]+readtask.read()[i] for i in range(0,3)]
                    findex+=1
                fielddata=[x*ifield/5 for x in fdata] #while loop is for averaging 5 measurements
                m_zfield.append(fielddata[zchan])
                m_xfield.append(fielddata[xchan])
                m_yfield.append(fielddata[ychan])
                tmp=double(1000*data/current_start) # Voltage from K2000 / Current from K2400
                result.append(tmp)
                values_y.append(tmp)
                values_x.append(a*i)
                mid = time.time()
                #ax.scatter(values_x[-1], values_y[-1], s=50, alpha=0.5)
                ax.plot(values_x, values_y,'b-o', ms=dot_size, mew=dot_edge, alpha=0.5)
                canvas.draw()
                listbox_l.insert('end', "Hall Resistance:" + str(round(tmp,4)) + " Applied Field:" + str(round(a*i,4)) + " Measured Field:" + str(round(fielddata[zchan],4)))
                t+=1
                a-=step
                listbox_l.see(END)
                fin = time.time()
                m_time.append(fin-start)
                print('Total Time: ', (fin-start), '\n Plot time: ', (fin-mid))

            #Setup timestamp
            stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
            listbox_l.insert('end', str(stamp))

            file = open(str(directory)+"/"+str(_sample)+"_GMW_pureZ_"+str(round(resistance,2))+"Ohm_"+str(round(current_start,2))+"mA_"+str(stamp), "w")
            file.write("Sample name: "+str(_sample)+"\n")
            file.write("Applied current: "+str(current_start)+"(mA)\n\n")
            file.write("Number"+" "+"Applied Field(Oe)"+" "+"Resistance(Ohm)"+" "+"Measure_time"+" "+"Measured XField(Oe)"+" "+"Measured YField(Oe)"+" "+"Measured ZField(Oe)"+"\n")

            cnt=1
            #output all data
            for a in range(len(values_y)):

                file.write(str(cnt)+" "+str(values_x[a])+" "+str(values_y[a])+" "+str(m_time[a])+" "+str(m_xfield[a])+" "+str(m_yfield[a])+" "+str(m_zfield[a])+"\n")
                cnt +=1

            file.closed

            listbox_l.insert('end', "The Measurement data is saved.")
            listbox_l.see(END)

            #keith.outputOff()
            current_start=current_start-current_step

            time.sleep(1) #Sleep between each scan
        
        #amp.dacOutput(0, DACx)
        #amp.dacOutput(0, DAC)
        writetask.write([0, 0, 0])
        writetask.close()
        readtask.close()

        keith.fourWireOff()
        keith.outputOn()

        listbox_l.insert('end',"Measurement finished")
        listbox_l.see(END)

    if (double(_output)/i)< 20:

        th = threading.Thread(target=event)
        th.start()

    else:

        listbox_l.insert('end',"Your output field is TOO LARGE!")
        listbox_l.see(END)
        print("Your output field is TOO LARGE!")


# DAC: Which DAC output channel for Hz (Out-of-plane field)

def xchanMethod(val):

    global xchan

    xchan = val

    listbox_l.insert('end', "x channel for measured H: "+ str(xchan))
    listbox_l.insert('end', "Don't forget to check the calibration factor H(Oe)/AOchan(V)")
    listbox_l.see(END)


def ychanMethod(val):

    global ychan

    ychan = val

    listbox_l.insert('end', "y channel for measured H: "+str(ychan))
    listbox_l.insert('end', "Don't forget to check the calibration factor H(Oe)/AOchan(V)")
    listbox_l.see(END)


def zchanMethod(val):

    global zchan

    zchan = val

    listbox_l.insert('end', "z channel for measured H "+str(zchan))
    listbox_l.insert('end', "Don't forget to check the calibration factor H(Oe)/AOchan(V)")
    listbox_l.see(END)


def dirMethod():

    global directory

    directory = filedialog.askdirectory()

    listbox_l.insert('end', directory)
    listbox_l.see(END)


def outputMethod(_interval, _output, _intervalfield):

    i=float(_interval)
    ifield=float(_intervalfield)

    writetask = nidaqmx.Task() #Initiate GMW write & read channels
    readtask = nidaqmx.Task()
    Va_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao0")
    Vb_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao1")
    Vc_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao2")
    Field_X = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai0")
    Field_Y = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai1")
    Field_Z = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai2")


    if _output.replace('.','').replace('-','').isdigit() :
        #print(entry_output.get())
        #amp.dacOutput((double(_output)/i), DAC)
        V = double(_output)/i
        writetask.write([V, V, V])
        fdata=[0,0,0] # origin measured field is in unit V, ifield is conversion value with unit Oe/V
        findex=1
        while findex<=5: #Average of five measurements
            fdata=[fdata[i]+readtask.read()[i] for i in range(0,3)]
            findex+=1
        fielddata=[x*ifield/5 for x in fdata]

        listbox_l.insert('end', "Single output field: "+str(_output)+" Oe.\nMeasured field: z = "+str(fielddata[zchan])+", x = "+str(fielddata[xchan])+", y = "+str(fielddata[ychan]))
        listbox_l.see(END)

        writetask.write([0, 0, 0])
    else:
        listbox_l.insert('end', "\""+str(_output)+"\" is not a valid ouput value.")
        listbox_l.see(END)

    writetask.close()
    readtask.close()

def clearMethod():

    ax.clear()
    ax.grid(True)
    ax.set_title("Realtime Resistance vs H Plot")
    ax.set_xlabel("Applied Z Field (Oe)")
    ax.set_ylabel("Hall Resistance (Ohm)")
    ax.axis([-1, 1, -1, 1])

    canvas.draw()
    listbox_l.delete(0, END)

    print("clear all")

def quitMethod():

    writetask = nidaqmx.Task() #Initiate GMW write & read channels
    readtask = nidaqmx.Task()
    Va_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao0")
    Vb_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao1")
    Vc_applied = writetask.ao_channels.add_ao_voltage_chan("VectorMagnet/ao2")
    Field_X = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai0")
    Field_Y = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai1")
    Field_Z = readtask.ai_channels.add_ai_voltage_chan("VectorMagnet/ai2")

    writetask.write([0, 0, 0])
    fdata=[0,0,0] # origin measured field is in unit V, ifield is conversion value with unit Oe/V
    findex=1
    while findex<=5: #Average of five measurements
        fdata=[fdata[i]+readtask.read()[i] for i in range(0,3)]
        findex+=1
    fielddata=[x*ifield/5 for x in fdata]

    listbox_l.insert('end', "All fields set to zero.\nMeasured field is "+str([readtask.read()]))
    listbox_l.see(END)
    writetask.close()
    readtask.close()
    time.sleep(1)

    global root

    root.quit()

def createWidgit():

    global ax, canvas, listbox_l, result, func, frame, sense

    fig = pylab.figure(1)

    ax = fig.add_subplot(111)
    ax.grid(True)
    ax.set_title("Realtime Resistance vs H Plot")
    ax.set_xlabel("Applied Z Field (Oe)")
    ax.set_ylabel("Hall Resistance (Ohm)")
    ax.axis([-1, 1, -1, 1])


    content = ttk.Frame(root, padding=(3,3,12,12))

    #plotting area
    frame = ttk.Frame(content, borderwidth=0, relief="sunken",padding=(3,3,12,12))
    frame_setting = ttk.Frame(content)
    frame_information = ttk.Frame(content, padding = (3,3,12,12))
    frame_buttomArea = ttk.Frame(content)

    #Save Variables
    entry_sample = ttk.Entry(frame_information); entry_sample.insert(0, "sample_name")

    #Function Variables
    entry_number = ttk.Entry(frame_setting); entry_number.insert(0,"40") # point per scan
    entry_interval = ttk.Entry(frame_setting);entry_interval.insert(0,"1") # Hz convertion value (V/Oe)
    entry_output = ttk.Entry(frame_setting); entry_output.insert(0,"5") # Hz field
    entry_average = ttk.Entry(frame_setting); entry_average.insert(0,"1") # measure time for Keithley
    entry_current = ttk.Entry(frame_setting); entry_current.insert(0,"0.1") # applied current
    entry_step = ttk.Entry(frame_setting); entry_step.insert(0,"0.4") # current step
    entry_intervalfield = ttk.Entry(frame_setting);entry_intervalfield.insert(0,"1") # measured field conversion value (Oe/V)

    value3 = tkinter.IntVar()
    value4 = tkinter.IntVar()
    value5 = tkinter.IntVar() #AI channel


    xchan = [0,0,1,2]
    ychan = [1,0,1,2]
    zchan = [2,0,1,2]

    option_xchan = ttk.OptionMenu(frame_setting, value3, *xchan, command = xchanMethod)
    option_ychan = ttk.OptionMenu(frame_setting, value4, *ychan, command = ychanMethod)
    option_zchan = ttk.OptionMenu(frame_setting, value5, *zchan, command = zchanMethod)

    listbox_l = Listbox(frame_information,height=5)
    scrollbar_s = ttk.Scrollbar(frame_information, orient=VERTICAL, command=listbox_l.yview)

    #Save Labels
    label_sample = ttk.Label(frame_information, text = "Sample Name")

    #Function Labels
    label_interval = ttk.Label(frame_setting, text="AOchan(V)/Applied Hz(Oe):") #calibration factor
    label_number = ttk.Label(frame_setting, text="Points per scan:")
    label_output = ttk.Label(frame_setting, text="Hz field (Oe):")
    label_average = ttk.Label(frame_setting, text="Averages:")
    label_xchan = ttk.Label(frame_setting, text="X Channel:")
    label_ychan = ttk.Label(frame_setting, text="Y Channel:")
    label_zchan = ttk.Label(frame_setting, text="Z Channel:")
    label_current = ttk.Label(frame_setting, text="Current (mA):")
    label_step = ttk.Label(frame_setting, text="Current step (mA):")
    label_intervalfield = ttk.Label(frame_setting, text="Measured H(Oe)/AIchan(V):")
    label_empty = ttk.Label(frame_setting, text="")


    button_measure = ttk.Button(frame_buttomArea, text ="Measure", \
        command = lambda : measureMethod(entry_interval.get(),entry_number.get(),\
            entry_output.get(),entry_average.get(),entry_current.get(),\
            entry_step.get(),entry_sample.get(),entry_intervalfield.get()))

    button_dir  = ttk.Button(frame_buttomArea, text="Change directory", command = dirMethod)
    button_quit = ttk.Button(frame_buttomArea, text="Quit", command = quitMethod)
    button_output = ttk.Button(frame_buttomArea, text="Output", \
        command = lambda : outputMethod(entry_interval.get(),entry_output.get(),entry_intervalfield.get()))
    button_clear = ttk.Button(frame_buttomArea, text="Clear", command = clearMethod)

    #Attatch Plot
    canvas = FigureCanvasTkAgg(fig, frame)
    canvas.get_tk_widget().grid(row=0, column =0, pady =0, padx =0,sticky='nsew')
    content.grid(column=0, row=0, sticky=(N, S, E, W))
    frame.grid(column=0, row=0, columnspan=3, rowspan=30, sticky=(N, S, E, W))


    frame_setting.grid(column=3, row=0, columnspan=2, rowspan=30, sticky=(N, S, E, W))

    #Frame setting grid

    label_interval.grid(column=0, row=1, columnspan=2, sticky=(N, W), padx=5)
    entry_interval.grid(column=0, row=2, columnspan=2, sticky=(N, W), padx=5)
    label_number.grid(column=0, row=3, columnspan=2, sticky=(N, W), padx=5)
    entry_number.grid(column=0, row=4, columnspan=2, sticky=(N, W), padx=5)
    label_output.grid(column=0, row=5, columnspan=2, sticky=(N, W), padx=5)
    entry_output.grid(column=0, row=6, columnspan=2, sticky=(N, W), padx=5)
    label_average.grid(column=0, row=7, columnspan=2, sticky=(N, W), padx=5)
    entry_average.grid(column=0, row=8, columnspan=2, sticky=(N, W), padx=5)
    label_xchan.grid(column=0, row=9, columnspan=2, sticky=(N, W), padx=5)
    option_xchan.grid(column=0, row=10, columnspan=2, sticky=(N, W), padx=5)
    label_ychan.grid(column=0, row=11, columnspan=2, sticky=(N, W), padx=5)
    option_ychan.grid(column=0, row=12, columnspan=2, sticky=(N, W), padx=5)
    label_zchan.grid(column=0, row=13, columnspan=2, sticky=(N, W), padx=5)
    option_zchan.grid(column=0, row=14, columnspan=2, sticky=(N, W), padx=5)
    label_current.grid(column=0, row=15, columnspan=2, sticky=(N, W), padx=5)
    entry_current.grid(column=0, row=16, columnspan=2, sticky=(N, W), padx=5)
    label_step.grid(column=0, row=17, columnspan=2, sticky=(N, W), padx=5)
    entry_step.grid(column=0, row=18, columnspan=2, sticky=(N, W), padx=5)
    label_intervalfield.grid(column=0, row=19, columnspan=2, sticky=(N, W), padx=5)
    entry_intervalfield.grid(column=0, row=20, columnspan=2, sticky=(N, W), padx=5)


    label_empty.grid(column=0, row=23, columnspan=2, sticky=(N, W), padx=5)


    frame_information.grid(column=0, row=31,columnspan=3,sticky=(N,W,E,S))

    listbox_l.grid(column=0, row=0,columnspan=3,sticky=(N,W,E,S))
    scrollbar_s.grid(column=1, row=0, sticky=(N,S))

    listbox_l['yscrollcommand'] = scrollbar_s.set

    label_sample.grid(column=0, row=2, columnspan=1, sticky=(N,W,E,S), padx=5)
    entry_sample.grid(column=0, row=3, columnspan=1, sticky=(N,W,E,S), padx=5)

    frame_information.grid_columnconfigure(0, weight=1)
    frame_information.grid_rowconfigure(0, weight=1)


    frame_buttomArea.grid(column =3, row=31,columnspan=2,sticky=(N, S, E, W))

    button_output.grid(column=0, row=0,columnspan = 2,sticky=(N, S, E, W))
    button_measure.grid(column =0, row=1, columnspan = 2,sticky=(N, S, E, W))
    button_clear.grid(column = 0, row = 3, columnspan = 1, sticky=(N, S, E, W))
    button_dir.grid(column=0, row=2,columnspan = 2,sticky=(N, S, E, W))
    button_quit.grid(column=1, row=3,columnspan = 1,sticky=(N, S, E, W))


    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    content.columnconfigure(0, weight=3)
    content.columnconfigure(1, weight=3)
    content.columnconfigure(2, weight=3)
    content.columnconfigure(3, weight=1)
    content.columnconfigure(4, weight=1)
    content.rowconfigure(1, weight=1)



if __name__ == '__main__':
    main()
