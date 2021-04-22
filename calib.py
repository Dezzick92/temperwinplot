"""
Calibration for plot.py
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
        self.interval = 1

    def sample_handler(self,data):
        temp = (data)
        # firmware version is TemperX3.3, so divisor of 100
        temp = int(temp[3])*2.56 + int(temp[4])/100.0
        if data[2] == 128:
            temperature = round(temp,2)
            self.temp_int = temperature
        else:
            temperature = round(temp,2)
            self.temp_ext = temperature

    
    def reading(self, duration, interval):
        
        all_hids = hid.find_all_hid_devices()

        for i in all_hids:
            if i.vendor_id == self.vendor_id and i.product_id == self.product_id: self.devices.append(i)

        if self.devices:
            device = self.devices[0]
            print("success")

            try:
                device.open()
                device.set_raw_data_handler(self.sample_handler)

                print("Reading, Time, Internal Temp, Probe Temp")

                # main loop - break when unplugged
                r = 0

                temps = []

                while device.is_plugged() and r < duration:
                # keep device open and rx new requests
                    report = device.find_output_reports()[0]
                    report[ 0xff000001 ].value = 0x01,0x80,0x33,0x01,0x00,0x00,0x00,0x00
                    report.send()

                    time.sleep(self.interval)
                    r+= interval
                    
                    self.time = datetime.datetime.now().strftime('%H-%M-%S')
                    temps = temps + [self.temp_ext]

                    print(str(r)+", "+str(self.time)+", "+str(self.temp_int)+", "+str(self.temp_ext))
                if device.is_plugged():
                    print("Reading done!")
                    return temps
                else:
                    print("TEMPer2 unplugged")
                    quit()
            finally:
                device.close()

        else:
            print("Couldn't find TEMPer2")

    def main(self):
        print("Please immerse TEMPer2 probe in FREEZING water")
        myinput = "not enter!"
        while myinput != "":
            myinput = input("Press Enter")
        temps = self.reading(15,1)
        lowtemp = min(temps)
        print("")
        print("Lowest temp detected: " + str(lowtemp)+ "°C")

        print("Please immerse TEMPer2 probe in BOILING water")
        myinput = "not enter!"
        while myinput != "":
            myinput = input("Press Enter")
        temps = self.reading(15,1)
        hightemp = max(temps)
        print("")
        print("Highest temp detected: " + str(hightemp)+ "°C")

        
        scale = 100 / (hightemp - lowtemp)
        offset = 0 -( scale * lowtemp)
        print("Offset: " + str(offset))
        print("Scale: " + str(scale))

        with open("calib.txt","w") as calibfile:
            calibfile.write(str(offset)+","+str(scale))
            calibfile.close()

if __name__ == "__main__":
    tempwin = TempWin(1)
    tempwin.main()
    quit()