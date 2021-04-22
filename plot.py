"""
This was made building on the following resources
Resources: http://guyfromhe.blogspot.com/2017/02/rding-temper-in-python-on-windows.html
https://github.com/urwen/temper
"""
import atexit
import time
import datetime
import ctypes
import pywinusb.hid as hid
from matplotlib import pyplot as plt


# Clear console
print("\033[H\033[J") 

class TempWin:
    def __init__(self, interval):
        self.vendor_id = 0x413d
        self.product_id = 0x2107
        self.devices = []
        self.temp_int = 0
        self.temp_ext = 0
        self.time = 0
        self.times = []
        self.interval = 1
        self.offset = 0
        self.scale = 1
        self.line = [67]

    def sample_handler(self,data):
        temp = (data)
        # firmware version is TemperX3.3, so divisor of 100
        temp = int(temp[3])*2.56 + int(temp[4])/100.0
        if data[2] == 128:
            temperature = round(temp,2)
            self.temp_int = temperature
        else:
            temperature = round((self.scale*temp)+self.offset,2)
            self.temp_ext = temperature

    
    

    def main(self):

        all_hids = hid.find_all_hid_devices()
        filename = str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

        #file handling to attempt to read from calibration file
        try:
            print("Attempting to open calib.txt")
            calibfile = open("calib.txt", "rt")
        except:
            print("calib.txt not found - run calib.py")
        else:
            print("calib.txt found")
            try:
                print("Reading calibration file")
                calibstr = calibfile.read()
                calibstr = calibstr.split(",")
                calibstr[0] = float(calibstr[0])
                calibstr[1] = float(calibstr[1])
                if calibstr[0] > -10 and calibstr[0] < 10:
                    self.offset = calibstr[0]
                    print("successfully read offset")
                else:
                    self.offset = calibstr[0]
                    print("succesfully read offset")
                    print("something's wrong though")
                if calibstr[1] > 0.8 and calibstr[1] < 1.2:
                    self.scale = calibstr[1]
                    print("successfully read scale")
                else:
                    self.scale = calibstr[1]
                    print("succesfully read scale")
                    print("something's wrong though")

            except:
                print("Couldn't read calib.txt - run calib.py")
                print("offset & scale set to (0,1)")
                self.offset= 0
                self.scale = 1
            calibfile.close()


        print("--------")
        print("offset: " + str(self.offset))
        print("scale: " + str(self.scale))
        for i in all_hids:
            if i.vendor_id == self.vendor_id and i.product_id == self.product_id: self.devices.append(i)

        if self.devices:
            device = self.devices[0]
            print("success")

            try:
                device.open()
                device.set_raw_data_handler(self.sample_handler)

                with open(str(filename) + ".csv", 'w') as savefile:
                    savefile.write("Reading,Time,Internal Temp,Probe Temp\n")

                    print("Reading, Time, Internal Temp, Probe Temp")

                    # main loop - break when unplugged
                    r = 0

                    #plt.axis([0,300,0,100])
                    plt.ion()
                    fig = plt.figure()
                    ax = plt.subplot(1,1,1)
                    ax.set_ylabel("Probe Temperature °C")
                    ax.set_ylim(0,100)
                    ax.set_xlabel("Time (s)")
                    ax.set_xlim(0,300)
                    times = []
                    temps = []
                    ax.plot(times,temps, color='blue',marker='o',linestyle='none')
                    ax.hlines(self.line,0,3600,color='red',linestyle='dashed')
                    fig.show()


                    while device.is_plugged():
                    # keep device open and rx new requests
                        report = device.find_output_reports()[0]
                        report[ 0xff000001 ].value = 0x01,0x80,0x33,0x01,0x00,0x00,0x00,0x00
                        report.send()

                        time.sleep(self.interval)
                        r+= 1
                        
                        self.time = datetime.datetime.now().strftime('%H-%M-%S')
                        times = times + [r]
                        temps = temps + [self.temp_ext]
                        ax.lines[0].set_data(times,temps)
                        if len(times) > 300:
                            ax.set_xlim(times[len(times)-301],times[len(times)-1])
                        fig.canvas.flush_events()
                        #plt.draw()
                        #plt.pause(0.001)

                        print(str(r)+", "+str(self.time)+", "+str(self.temp_int)+", "+str(self.temp_ext))
                        savefile.write(str(r)+","+str(self.time)+","+str(self.temp_int)+","+str(self.temp_ext)+"\n")
                    print("TEMPer2 unplugged")

            finally:
                
                device.close()
                savefile.close()

        else:
            print("Couldn't find TEMPer2")

                

if __name__ == "__main__":
    tempwin = TempWin(1)
    tempwin.main()
    quit()