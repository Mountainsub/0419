
import pandas as pd
import numpy as np
import time 
import sys
import os
import ctypes
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


import datetime

from lib.ddeclient import DDEClient
from price_logger import ClientHolder 
from price_logger import LastNPerfTime
from init import keisan

class plot_time:
    def __init__(self):
        self.hdffilename = "./data/sum.hdf5"
        self.store = pd.HDFStore(self.hdffilename)
        self.key_name = "testcase" 
        self.key_name2 = "timecase"

    def hozon(self, data_dict):
        #print("OK")
        self.store.append(self.key_name, data_dict)

    def hozon2(self, data_dict):
        #print("OK")
        self.store.append(self.key_name2, data_dict)
      
class up_or_down:
    def __init__(self, calc, topix):
        
        
        self.RED = '\033[31m'
        self.BLUE = '\033[34m'
        self.END = '\033[0m'
        self.switch = "N"
        #self.switch = switch 
        dif = calc - float(topix)
        self.store_x = pd.HDFStore("./data/sum.hdf5")
        if dif > 10 or dif < -10:
            self.Boolean = "repair"
            return
        
        elif  dif >= 0.001:
            self.Boolean = "up"
        elif dif <= -0.001:
            self.Boolean = "down"
        else:
            self.Boolean = "None"
        self.calc = calc
        

    def judge(self):
        t = self.Boolean
        RED = self.RED
        BLUE = self.BLUE
        END = self.END
        switch = self.switch
        store = self.store_x
        if t == "up":
            string = RED +"計算した値が、実際のTOPIXより高いです。"+END
            if switch == ("down" or "N"):
                t = datetime.datetime.now()
                switch = "up"
                store.append("boundary",pd.DataFrame({"t":[t], "switch":["v"]} ,index=False))
        elif t == "down":
            string = BLUE+"計算した値が、実際のTOPIXより低いです。"+END
            if switch == ("up" or "N"):
                t = datetime.datetime.now()
                switch = "down"
                store.append("boundary",pd.DataFrame({"t":[t], "switch":["^"]},index=False))
        elif t == "repair":
            string = "差が大きすぎる"
        else:
            string = "変化が小さいので手を加えない方がよいでしょう。"
        return string

    def lever(self):
        return self.switch
    
def stop_execute():
	now = datetime.datetime.now()
	currently = np.datetime64(now)
	year = now.year
	month = now.month
	day = now.day

	hour = now.hour
	minute = now.minute
	if  hour >= 15:
		print("今日は閉場です。")
		sys.exit()
	if (hour == 11 and minute > 30 ) or (hour==12 and minute <30):
		print("お昼休みです。")
		temp = pd.datetime(year, month, day, 12, 30)		
		temp = np.datetime64(temp)
		sleep_num = temp-currently
		tim = sleep_num / 10 ** 6
		t = str(tim)
		print(t)
		#直前ではなく指定時刻の60秒前から開始する
		time.sleep(float(t)-60)
	elif hour < 9:
		temp = pd.datetime(year, month, day, 9, 0)		
		temp = np.datetime64(temp)
		sleep_num = float(temp.astype("float64")-currently.astype("float64"))
		tim = sleep_num / 10 ** 6
		t = int(tim)
		print(t)
		#直前ではなく指定時刻の60秒前から開始する
		time.sleep(float(t - 60))
	else:
		pass

if __name__ == "__main__":
    ENABLE_PROCESSED_OUTPUT = 0x0001
    ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002
    ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
    MODE = ENABLE_PROCESSED_OUTPUT + ENABLE_WRAP_AT_EOL_OUTPUT + ENABLE_VIRTUAL_TERMINAL_PROCESSING
    
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)
    kernel32.SetConsoleMode(handle, MODE)

    t1 = time.time()
    calc = 0
    timer = LastNPerfTime(2**20)
    object_pass = "value"
    dde = DDEClient("rss", "TOPX")
    store_x = pd.HDFStore("./data/sum2.hdf5")
    topix = dde.request("現在値").decode("sjis")
    topix = float(topix)
    try:
        temp  = store_x.get("consequence")
    except Exception:
        topix_init = 426.69626906238113
        pass
    else:
        calc = float(temp["calc"].tail(1))
        print(calc, topix)
        if calc == 0:
            topix_init = 426.69626906238113
        else:
            topix_init = 100 * calc / float(topix)
    
    """
    TOPIX
    （calc:8000 / 初期値）× 100
    初期値
    (calc / TOPIX ) kakeru 100
    
    """
    
    #4/8 8222.883552900003
    
             
    switch = "neutral"
    
    while True:
        
        
        holder = plot_time()
        
        timer.start()
        calc = 0
        x = 1
        
        for i in range(18):
            idx = i *126
            filename = "./data/" + str(idx).zfill(3)+ ".hdf5"
             
            try:
                with pd.HDFStore(filename) as store:
                    temp =store.get(object_pass)
            except:
                pass
            else:
                end = temp.tail(1)
                v = float(end["0"])
                if v==0:
                    now = datetime.datetime.now()
                    print(i, "attention", now)
                    """
                    with pd.HDFStore("./data/caution.hdf5") as store:
                        store.append("zero",pd.DataFrame({"caution":[now], "id": [i]})) 
                    """
                    #x += 1
                    #v = float(temp.iat[-1* x,0])
                else:
                    v2 = int(v *(10**3)) / 10**3
                    print(i, v2)
                    x = 1
                calc += v
            
        
        dict = {"total": [calc]}
        timer.end()
                
        series = pd.DataFrame(dict)

        #保存
        holder.hozon(series)
        
        temp = timer.get_sum_time()    
        dict = {"time": [temp]}
        df = pd.DataFrame(dict)
        
        holder.hozon2(df)   
        timer.count_one()
        
        
        now = datetime.datetime.now()
        print(calc)
        calc /= topix_init 
        calc *= 100
        try:
            topix = dde.request("現在値").decode("sjis")
        except Exception:
            pass
        else:
            instance = up_or_down(calc, topix)
            string = instance.judge()
            print("取得時刻:"+str(now),"計算値:" + str(calc), string)
        finally:
            data_dict = {"time":[now], "calc":[calc], "topix":[topix]}
            #print(data_dict)
            store_x.append("consequence",pd.DataFrame(data_dict), index=False)
        #pre_calc = calc
        #pre_topix = topix
        #switch = instance.lever()
        
        
        if string =="差が大きすぎる":
            topix_init = float(topix_init)* float(calc) / float(topix)
            print("トピックス初期値："+str(topix_init))
            #1882.4188190928678