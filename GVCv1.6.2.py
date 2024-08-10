import cv2
import fileInteraction as fi
import GVCMainProcess
import GVCAdj
from time import sleep
import tkinter as tk
import tkinter.font as tkFont
from tkinter.ttk import Progressbar
from tkinter import messagebox as ms
from PIL.Image import open as imopen
from pystray import Icon, Menu, MenuItem
import os
import sys
import pyvirtualcam
from threading import Thread

try :
    cv2.ocl.setUseOpenCL(True)
except :
    pass

class startup_ui() :
    def __init__(self, root) :
        self.root = root
        self.root.title(f"Starting Up....")
        self.root.resizable(width=False, height=False)
        self.root.geometry("250x100")
        self.root.iconbitmap(default = config['icon'])
        self.root.after(1, lambda: self.root.focus_force())
        ft = tkFont.Font(family='Arial Narrow', size=10)
        self.root.attributes('-topmost', 1)

        self.text = tk.Label(self.root, anchor="nw")
        self.text["font"] = ft
        self.text["fg"] = "#333333"
        self.text["justify"] = "left"
        self.text["text"] = "N/N"
        self.text.place(x=10, y=10, width=230, height=20)

        self.p = Progressbar(self.root)
        self.p["orient"] = tk.HORIZONTAL
        self.p["length"] = 230
        self.p["mode"] = "determinate"
        self.p["takefocus"] = True
        self.p["maximum"] = 100
        self.p.place(x=10, y=50, width=230, height=20)

    def update(self, text, progress) :
        self.text["text"] = text
        self.p.step(progress)
        
class info_ui() :
    def __init__(self, root) :
        self.root = root
        self.root.title(f"Information")
        self.root.resizable(width=False, height=False)
        self.root.geometry("310x125")
        self.root.iconbitmap(default = config['icon'])
        self.root.after(1, lambda: self.root.focus_force())
        ft = tkFont.Font(family='Arial Narrow', size=10)
        
        text_list = [
            ["Acquisition Camera Type", ":", f"{cam_type}"], 
            ["Virtual Camera Backend", ":", f"{gvccam.backend}"], 
            ["Image Processing Backend", ":", "GPU" if cv2.ocl.useOpenCL else "CPU"], 
            ["Image Input Size*", ":", f"{cam_resolution[0]}x{cam_resolution[1]}"], 
            ["Image Output Size", ":", f"{output_size[0]}x{output_size[1]}"]
            ]
        
        for i in range(len(text_list)) :
            for j in range(len(text_list[i])) :
                self.text = tk.Label(self.root)
                self.text["font"] = ft
                self.text["fg"] = "#333333"
                self.text["text"] = text_list[i][j]
                self.text.grid(row=i, pady=1 ,column=j, padx=5, sticky="W")

def call_startup_ui() :
    global sta_ui
    root = tk.Tk()
    sta_ui = startup_ui(root)
    root.mainloop()
    
def tray_manu_enable(l1 = True, l2 = True, l3 = True, l4 = True) :
    tray.menu = Menu(MenuItem("Setting Output Image", image_setting, enabled=l1), 
                     MenuItem("Set Camera Acquisition", cam_setting, enabled=l2), 
                     MenuItem("Information", call_info_ui, enabled=l3), 
                     MenuItem("Exit Software", call_stop, enabled=l4))
    tray.update_menu()
    
def call_info_ui() :
    tray_manu_enable(l1=False, l2=False, l3=False)
    root = tk.Tk()
    info_ui(root)
    root.mainloop()
    tray_manu_enable()

def image_setting() :
    global vid
    tray_manu_enable(l1=False, l2=False, l3=False)
    GVCAdj.adj_ui(vid)
    sleep(1)
    restart()

def cam_setting() :
    try :
        tray_manu_enable(l1=False, l2=False, l3=False)
        tray.update_menu()
    except :
        pass
    GVCAdj.select_cam()
    restart()

def restart() :
    os.execl(sys.executable, sys.executable, *sys.argv)

def call_stop(_) :
    global stop
    try :
        tray.stop()
    except :
        pass
    stop = True
    sleep(0.5)
    os._exit(0)

config = fi.read_json("./data/gvc_config.json")
software_version = config["software_version"]
cam_type = config["cam_type"]
cam_index = config["cam_index"]
cam_resolution = [config["image_width"], config["image_height"]]
output_size = [config["output_width"], config["output_height"]]
grid = config["grid"]
stop = False
pause = False

multi_grid = GVCMainProcess.MultiGridPrespective()

Thread(target = call_startup_ui).start()

sleep(0.1)

sta_ui.update("Starting up Software...", 0)

try :
    sta_ui.update("Check Camera...", 10)
    if cam_type == "Webcam Camera (CAM)" :
        sta_ui.update("Opening Webcam Camera...", 60)
        vid = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not vid.isOpened() :
            error = "Devices ERROR: Device Not Found!"
            raise Exception(error)
        vid.set(3, cam_resolution[0])
        vid.set(4, cam_resolution[1])
        ret, img = vid.read()
        if not ret :
            error = "Devices ERROR: Cannot Open Device!"
            raise Exception(error)
    elif cam_type == "IDS Industry Camera (IDS)" :
        from IDSCameraCol import IDSCamera
        sta_ui.update("Opening IDS Industry Camera...", 60)
        vid = IDSCamera(cam_index, cam_resolution, "BAYER")
    elif cam_type == "HIK Industry Camera (HIK)" :
        from HIKCameraCol import HIKCamera
        sta_ui.update("Opening HIK Industry Camera...", 60)
        vid = HIKCamera(cam_index, cam_resolution)
    else :
        sta_ui.update("Unknow Camera!!!", 60)
        error = f"CameraType ERROR: System are not support {cam_type}\n\nThis may cause by Illegal edit on JSON File."
        raise Exception(error)
except Exception as error :
    sta_ui.update("ERROR Occurs!!", 30)
    ms.showerror("Image Acquisition Error", f"Cannot Read {cam_type} on Index {cam_index} due System raise :\n\n{error}")
    sure = ms.askyesno("Setting?", f"Would you like to setting the software?\nif no, the software will automatically close due error.")
    pause = True
    sta_ui.root.after(1, sta_ui.root.destroy)
    sleep(0.1)
    if sure :
        cam_setting()
    else :
        call_stop(0)
    
sta_ui.update("Setting up Virtual Camera...", 10)

sleep(0.1)
    
try :
    gvccam = pyvirtualcam.Camera(width=output_size[0], height=output_size[1], fps=120, fmt=pyvirtualcam.PixelFormat.BGR)
except Exception as error :
    sta_ui.update("ERROR Occurs!!", 20)
    ms.showerror("Virtual Camera Error", f"Cannot setup Virtual Camera due System raise :\n\n{error}")
    sure = ms.askyesno("Setting?", f"Would you like to setting the software?\nif no, the software will automatically close due error.")
    pause = True
    sta_ui.root.after(1, sta_ui.root.destroy)
    sleep(0.1)
    if sure :
        cam_setting()
    else :
        call_stop(0)

sta_ui.update("Tray Setting up...", 10)

image = imopen(config["icon"])
tray = Icon(f"Generative Virtual Camera v{software_version}", 
            image, 
            menu = Menu(MenuItem("Setting Output Image", image_setting, enabled=True), 
                        MenuItem("Set Camera Acquisition", cam_setting, enabled=True), 
                        MenuItem("Information", call_info_ui, enabled=True),
                        MenuItem("Exit Software", call_stop, enabled=True)), 
            title = f"Generative Virtual Camera v{software_version}")
tray.run_detached()

sta_ui.update("Complete!", 9.99)
sta_ui.root.after(500, sta_ui.root.destroy)
    
while not stop :
    while not pause or not stop :
        ret, img = vid.read()
        if config["gray"] == 1 :
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        try :
            img = multi_grid.grid_merge(img, grid, output_size, [config["grid_div_x"], config["grid_div_y"]])
        except :
            pass
        fil = GVCMainProcess.multi_filter(img, config["alpha"], config["beta"], config["d_kernal_size"], config["t_kernal_size"], config["m_kernal_size"])
        re_fil = cv2.resize(fil, output_size)
        if len(fil.shape) <= 2 :
            re_fil = cv2.cvtColor(re_fil, cv2.COLOR_GRAY2RGB)
        gvccam.send(re_fil)
        tray.title = f"Generative Virtual Camera v{software_version}\nFPS : {round(gvccam.current_fps)}"
        gvccam.sleep_until_next_frame()
    sleep(2)
gvccam.close()