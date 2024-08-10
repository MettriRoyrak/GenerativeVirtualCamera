import cv2
import tkinter as tk
import tkinter.font as tkFont
from tkinter.ttk import Scale, Combobox
from threading import Thread
from tkinter import messagebox as ms
from time import sleep
import fileInteraction as fi
import GVCMainProcess

try :
    cv2.ocl.setUseOpenCL(True)
except :
    pass

class adj_ui() :
    def __init__(self, vid) :
        self.config_path = "./data/gvc_config.json"
        self.config = fi.read_json(self.config_path)
        self.command_list = {}
        self.stop = False
        self.dis_lowest = ["", 0, 1e10]
        self.holding = False
        self.change_on_text = False
        self.res = [self.config["image_width"], self.config["image_height"]]

        self.text_scale = {
            "Image Size :" : [None, None, None, None],
            'Image Output Width' : ["output_width", 1, 4096, "int"], 
            'Image Output Height' : ["output_height", 1, 4096, "int"], 
            "Image Filter :" : [None, None, None, None],
            'Mean size' : ["m_kernal_size", 1, 25, "int"], 
            'Median size' : ["t_kernal_size", 1, 25, "int"], 
            'Bilateral size' : ["d_kernal_size", 0, 25, "int"], 
            "Image Brightness and Contrast :"  : [None, None, None, None], 
            'Contrast' : ["alpha", 0, 3, "float"], 
            'Brightness' : ["beta", 0, 300, "float"],
            "Grid Adjustment :" : [None, None, None, None],
            "Horizontal Segment" : ["grid_div_x", 1, 30, "int"],
            "Vertical Segment" : ["grid_div_y", 1, 30, "int"]
            }
        
        per_order = self.config["perspective_order_list"]
        
        self.grid_pos = {
            "TOP" : per_order["TOP"][0 : self.config["grid_order"]+1] + [per_order["TOP"][-1]],
            "BOTTOM" : per_order["BOTTOM"][0 : self.config["grid_order"]+1] + [per_order["BOTTOM"][-1]],
            "LEFT" : per_order["LEFT"][0 : self.config["grid_order"]+1] + [per_order["LEFT"][-1]],
            "RIGHT" : per_order["RIGHT"][0 : self.config["grid_order"]+1] + [per_order["RIGHT"][-1]]
            }

        Thread(target = self.call_ui).start()

        self.multi_grid = GVCMainProcess.MultiGridPrespective()

        cv2.namedWindow('Source', cv2.WINDOW_NORMAL)
        cv2.namedWindow('LiveStream', cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Source", self.res[0], self.res[1])
        cv2.resizeWindow("LiveStream", self.config["output_width"], self.config["output_height"])
        cv2.setMouseCallback('Source', self.mouse_position)

        self.adjustment(vid)

    def set_stop(self) :
        decition = ms.askyesnocancel("Saving", "Do you still want to save this setting?")
        if decition == True :
            self.stop = True
            sleep(1)
            fi.write_json(self.config, self.config_path)
            sleep(0.5)
            self.root.destroy()
        elif decition == False :
            self.stop = True
            sleep(0.5)
            self.root.destroy()
        elif decition == None :
            self.root.after(1, lambda: self.root.focus_force())
            return

    def call_ui(self) :
        self.root = tk.Tk()
        self.ft = tkFont.Font(family='Arial Narrow', size=10)
        self.ui()
        self.root.attributes('-topmost', 1)
        sleep(0.01)
        self.root.attributes('-topmost', 0)
        self.root.mainloop()

    def set_text(self, entry_root, text):
        entry_root.delete(0, tk.END)
        entry_root.insert(0, text)

    def text_change(self) :
        self.change_on_text = True
        for header in list(self.text_scale.values()) :
            if header[0] == None :
                continue
            try :
                if self.command_list[header[0]][0].get() == "" :
                    val = header[1]
                    self.set_text(self.command_list[header[0]][0], str(val))
                if header[3] == "float" :
                    val = float(self.command_list[header[0]][0].get())
                else :
                    val = int(self.command_list[header[0]][0].get())
                if val < header[1] :
                    val = header[1]
                    self.set_text(self.command_list[header[0]][0], str(val))
                elif val > header[2] :
                    val = header[2]
                    self.set_text(self.command_list[header[0]][0], str(val))
                self.config[header[0]] = val
                self.command_list[header[0]][1].set(float(val))
            except KeyError :
                pass
            except TypeError :
                val = self.config[header[0]]
                self.set_text(self.command_list[header[0]][0], val)
            except ValueError :
                val = self.config[header[0]]
                self.set_text(self.command_list[header[0]][0], val)
        self.change_on_text = False 
        
    def scale_change(self, _) :
        for header in list(self.text_scale.values()) :
            if header[0] == None or self.change_on_text :
                continue
            try :
                if header[3] == "float" :
                    val = self.command_list[header[0]][1].get()
                else :
                    val = int(self.command_list[header[0]][1].get())
                self.set_text(self.command_list[header[0]][0], str(val))
                self.config[header[0]] = val
            except KeyError :
                pass
    
    def ui(self) :
        self.root.title(f"Setting")
        self.root.resizable(width=False, height=False)
        self.root.geometry("540x400")
        self.root.iconbitmap(default = self.config['icon'])
        self.root.after(1, lambda: self.root.focus_force())

        for i in range(len(self.text_scale)) :
            text = tk.Label(self.root, anchor="w")
            text["font"] = self.ft
            text["fg"] = "#333333"
            text["justify"] = "left"
            text["text"] = list(self.text_scale.keys())[i]
            if list(self.text_scale.values())[i][0] == None :
                text.grid(column=0, row=i, columnspan=3, sticky=tk.W, padx=10, pady=3)
            else :
                text.grid(column=0, row=i, columnspan=1, sticky=tk.W, padx=10, pady=3)
                text_entry = tk.Entry(self.root)
                text_entry["borderwidth"] = "1px"
                text_entry["fg"] = "#333333"
                text_entry["justify"] = "left"
                text_entry.bind("<KeyPress>", lambda _ : self.root.after(1, self.text_change))
                # text_entry.bind("<KeyRelease>", self.text_change)
                text_entry.grid(column=1, row=i, sticky=tk.W, padx=0, pady=3)
                self.set_text(text_entry, str(self.config[list(self.text_scale.values())[i][0]]))

                scale = Scale(self.root, from_=list(self.text_scale.values())[i][1], to=list(self.text_scale.values())[i][2], orient=tk.HORIZONTAL, length=260, command = self.scale_change)
                scale.set(self.config[list(self.text_scale.values())[i][0]])
                scale.grid(column=2, columnspan=1, row=i, sticky=tk.W, padx=10, pady=0)

                self.command_list[list(self.text_scale.values())[i][0]] = [text_entry, scale]

        text = tk.Label(self.root, anchor="nw")
        text["font"] = self.ft
        text["fg"] = "#333333"
        text["justify"] = "left"
        text["text"] = f"Grayscale"
        text.place(x=10, y=369, width=160, height=20)

        self.sl = tk.Scale(self.root, from_=0, to=1, showvalue=False, command=self.sl_val_change, orient=tk.HORIZONTAL)
        self.sl.place(x=70, y=370, width=60, height=20)
        self.sl.set(self.config["gray"])

        self.root.protocol("WM_DELETE_WINDOW", self.set_stop)

    def sl_val_change(self, _) :
        """
        Change val mode from BGR <-> RGB.
        """
        self.config["gray"] = self.sl.get()

    def do_releae(self, from_root) :
        from_root.destroy()
        self.root.after(1, lambda : self.root.focus_force())

    def mouse_position(self, event, x, y, flags, param) :
        if (event == cv2.EVENT_LBUTTONDOWN or self.holding) and self.dis_lowest[0] != "" :
            if x > self.res[0] :
                x = self.res[0]
            elif x < 0 :
                x = 0
            if y > self.res[1] :
                y = self.res[1]
            elif y < 0 :
                y = 0
            self.grid_pos[self.dis_lowest[0]][self.dis_lowest[1]] = [x/self.res[0], y/self.res[1]]
            self.grid_pos["RIGHT"][0] = self.grid_pos["TOP"][-1]
            self.grid_pos["LEFT"][0] = self.grid_pos["TOP"][0]
            self.grid_pos["LEFT"][-1] = self.grid_pos["BOTTOM"][0]
            self.grid_pos["RIGHT"][-1] = self.grid_pos["BOTTOM"][-1]
            self.holding = True
        if event == cv2.EVENT_LBUTTONUP :
            self.holding = False
        if event == cv2.EVENT_MOUSEMOVE and not self.holding :
            self.dis_lowest = ["", 0, 1e10]
            for key, pos in zip(self.grid_pos.keys(), self.grid_pos.values()) :
                i = 0
                for p in pos :
                    dis = (((p[0]*self.res[0] - x) ** 2) + ((p[1]*self.res[1] - y) ** 2)) ** 0.5
                    if dis < self.dis_lowest[2] and dis < (self.res[0] + self.res[1]) / 16 :
                        self.dis_lowest = [str(key), i, float(dis)]
                    i += 1

    def adjustment(self, vid) :
        while not self.stop :
            ret, img = vid.read()
            img = cv2.resize(img, self.res)
            grid_img = img.copy()
            if self.config["gray"] == 1 :
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            grid = self.multi_grid.quadratic_grid(self.grid_pos, [self.config["grid_div_x"], self.config["grid_div_y"]], self.config["grid_order"])
            for g in grid :
                cv2.line(grid_img, [int(g[0][0]*self.res[0]), int(g[0][1]*self.res[1])], [int(g[1][0]*self.res[0]), int(g[1][1]*self.res[1])], (255, 0, 255), 2)
                cv2.line(grid_img, [int(g[1][0]*self.res[0]), int(g[1][1]*self.res[1])], [int(g[3][0]*self.res[0]), int(g[3][1]*self.res[1])], (255, 0, 255), 2)
                cv2.line(grid_img, [int(g[0][0]*self.res[0]), int(g[0][1]*self.res[1])], [int(g[2][0]*self.res[0]), int(g[2][1]*self.res[1])], (255, 0, 255), 2)
                cv2.line(grid_img, [int(g[2][0]*self.res[0]), int(g[2][1]*self.res[1])], [int(g[3][0]*self.res[0]), int(g[3][1]*self.res[1])], (255, 0, 255), 2)
            for pos in self.grid_pos.values() :
                for p in pos :
                    cv2.circle(grid_img, [int(p[0]*self.res[0]), int(p[1]*self.res[1])], 5, [255, 255, 255], 2)
            if self.dis_lowest[0] != "" :
                uni_grid = self.grid_pos[self.dis_lowest[0]][self.dis_lowest[1]]
                uni_pos = [int(uni_grid[0]*self.res[0]), int(uni_grid[1]*self.res[1])]
                cv2.circle(grid_img, uni_pos, 9, [0, 255, 255], 2)
            cv2.imshow("Source", grid_img)

            try :
                dst = self.multi_grid.grid_merge(img, grid, [self.config["output_width"], self.config["output_height"]], [self.config["grid_div_x"], self.config["grid_div_y"]])
            except :
                pass
            fil = GVCMainProcess.multi_filter(dst, self.config["alpha"], self.config["beta"], self.config["d_kernal_size"], self.config["t_kernal_size"], self.config["m_kernal_size"])
            if len(fil.shape) <= 2 :
                fil = cv2.cvtColor(fil, cv2.COLOR_GRAY2RGB)

            fil = cv2.resize(fil, [self.config["output_width"], self.config["output_height"]])
            cv2.resizeWindow("LiveStream", self.config["output_width"], self.config["output_height"])
            cv2.imshow("LiveStream", fil)
            cv2.waitKey(1)
        self.config["grid"] = grid
        self.config["perspective_order_list"] = {
            "TOP" : self.grid_pos["TOP"][: (len(self.grid_pos["TOP"]) - 1)] + self.config["perspective_order_list"]["TOP"][(len(self.grid_pos["TOP"]) - 1) : (len(self.config["perspective_order_list"]["TOP"]) - 1)] + [self.grid_pos["TOP"][-1]],
            "BOTTOM" : self.grid_pos["BOTTOM"][: (len(self.grid_pos["BOTTOM"]) - 1)] + self.config["perspective_order_list"]["BOTTOM"][(len(self.grid_pos["BOTTOM"]) - 1) : (len(self.config["perspective_order_list"]["BOTTOM"]) - 1)] + [self.grid_pos["BOTTOM"][-1]],
            "LEFT" : self.grid_pos["LEFT"][: (len(self.grid_pos["LEFT"]) - 1)] + self.config["perspective_order_list"]["LEFT"][(len(self.grid_pos["LEFT"]) - 1) : (len(self.config["perspective_order_list"]["LEFT"]) - 1)] + [self.grid_pos["LEFT"][-1]],
            "RIGHT" : self.grid_pos["RIGHT"][: (len(self.grid_pos["RIGHT"]) - 1)] + self.config["perspective_order_list"]["RIGHT"][(len(self.grid_pos["RIGHT"]) - 1) : (len(self.config["perspective_order_list"]["RIGHT"]) - 1)] + [self.grid_pos["RIGHT"][-1]],
            }
        dev = 16
        self.config["output_width"] = int(dev * round(self.config["output_width"] / dev))
        self.config["output_height"] = int(dev * round(self.config["output_height"] / dev))
        if self.config["output_width"] == 0 :
            self.config["output_width"] = dev
        if self.config["output_height"] == 0 :
            self.config["output_height"] = dev
        cv2.destroyAllWindows()

class select_cam() :
    def __init__(self) :
        self.config_path = "./data/gvc_config.json"
        self.config = fi.read_json(self.config_path)
        self.img_size_lim = [120, 4096]
        self.display_cam_type = ["Webcam Camera (CAM)", "IDS Industry Camera (IDS)", "HIK Industry Camera (HIK)"]
        self.call_ui()

    def call_ui(self) :
        self.root = tk.Tk()
        self.ft = tkFont.Font(family='Arial Narrow', size=10)
        self.ui()
        self.root.attributes('-topmost', 1)
        sleep(0.01)
        self.root.attributes('-topmost', 0)
        self.root.mainloop()

    def ui(self) :
        self.root.title("Camera Type")
        self.root.resizable(width=False, height=False)
        self.root.geometry("250x175")
        self.root.iconbitmap(default= self.config['icon'])
        self.root.after(1, lambda: self.root.focus_force())

        text = tk.Label(self.root, anchor="nw")
        text["font"] = self.ft
        text["fg"] = "#333333"
        text["justify"] = "left"
        text["text"] = f"Please Select Camera Type and Index :"
        text.place(x=10, y=10, width=230, height=20)

        self.cam_select_combo = Combobox(self.root,
                                         width=27,
                                         state="readonly",
                                         textvariable=tk.IntVar())
        self.cam_select_combo['values'] = self.display_cam_type
        self.cam_select_combo.place(x=10, y=40, width=175, height=25)
        try :
            self.cam_select_combo.current(self.display_cam_type.index(self.config["cam_type"]))
        except :
            self.cam_select_combo.current(0)

        text2 = tk.Label(self.root, anchor="nw")
        text2["font"] = self.ft
        text2["fg"] = "#333333"
        text2["justify"] = "left"
        text2["text"] = f"Image Width\t     Image Height"
        text2.place(x=9, y=75, width=280, height=20)

        self.cam_index_entry = tk.Entry(self.root)
        self.cam_index_entry["borderwidth"] = "1px"
        self.cam_index_entry["fg"] = "#333333"
        self.cam_index_entry["justify"] = "left"
        self.cam_index_entry.place(x=190, y=40, width=50, height=25)
        self.cam_index_entry.bind("<KeyPress>", lambda _ : self.root.after(1, lambda : self.text_lock(self.cam_index_entry, "cam_index", lock_type=int, val_lim=[0, 254])))
        self.set_text(self.cam_index_entry, str(self.config["cam_index"]))

        self.w_entry = tk.Entry(self.root)
        self.w_entry["borderwidth"] = "1px"
        self.w_entry["fg"] = "#333333"
        self.w_entry["justify"] = "left"
        self.w_entry.place(x=10, y=100, width=100, height=25)
        self.w_entry.bind("<KeyPress>", lambda _ : self.root.after(1, lambda : self.text_lock(self.w_entry, "image_width", lock_type=int)))
        self.w_entry.bind("<FocusOut>", lambda _ : self.root.after(1, lambda : self.text_lock(self.w_entry, "image_width", lock_type=int, val_lim=self.img_size_lim)))
        self.set_text(self.w_entry, str(self.config["image_width"]))

        self.h_entry = tk.Entry(self.root)
        self.h_entry["borderwidth"] = "1px"
        self.h_entry["fg"] = "#333333"
        self.h_entry["justify"] = "left"
        self.h_entry.place(x=120, y=100, width=100, height=25)
        self.h_entry.bind("<KeyPress>", lambda _ : self.root.after(1, lambda : self.text_lock(self.h_entry, "image_height", lock_type=int)))
        self.h_entry.bind("<FocusOut>", lambda _ : self.root.after(1, lambda : self.text_lock(self.h_entry, "image_height", lock_type=int, val_lim=self.img_size_lim)))
        self.set_text(self.h_entry, str(self.config["image_height"]))

        submit_botton = tk.Button(self.root)
        submit_botton["bg"] = "#f0f0f0"
        submit_botton["font"] = self.ft
        submit_botton["fg"] = "#000000"
        submit_botton["justify"] = "center"
        submit_botton["text"] = 'Confirm'
        submit_botton["border"] = "1"
        submit_botton["command"] = lambda : self.change()
        submit_botton.place(x=10, y=140, width=230, height=25)

    def text_lock(self, entry_root, dic, lock_type = int, val_lim = [-1e10, 1e10]) :
        try :
            text = entry_root.get()
            if text == "" :
                self.config[dic] = 0
            else :
                val = lock_type(entry_root.get())
                if val < val_lim[0] :
                    self.config[dic] = val_lim[0]
                    raise
                elif val > val_lim[1] :
                    self.config[dic] = val_lim[1]
                    raise
                self.config[dic] = val
        except :
            val = str(self.config[dic])
            self.set_text(entry_root, val)

    def set_text(self, entry_root, text):
        entry_root.delete(0, tk.END)
        entry_root.insert(0, text)

    def change(self) :
        self.config["cam_type"] = str(self.cam_select_combo.get())
        if self.config["image_width"] < self.img_size_lim[0] :
            self.config["image_width"] = self.img_size_lim[0]
        elif self.config["image_width"] > self.img_size_lim[1] :
            self.config["image_width"] = self.img_size_lim[1]
        if self.config["image_height"] < self.img_size_lim[0] :
            self.config["image_height"] = self.img_size_lim[0]
        elif self.config["image_height"] > self.img_size_lim[1] :
            self.config["image_height"] = self.img_size_lim[1]
        fi.write_json(self.config, self.config_path)
        self.root.destroy()

"""
TEST AREA
"""

# vid = cv2.VideoCapture(0)
# vid.set(3, 1280)
# vid.set(4, 720)

# adjustment = adj_ui(vid)

# setting = select_cam()