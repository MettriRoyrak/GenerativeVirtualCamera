import numpy as np
import ctypes
import shutil
from pyueye import ueye

class IDSCamera() :
    def __init__(self, id_cam = 0, size = [1600, 1200], col_mode = "BAYER") :
        """
        Simple Fuction for support IDS Camera.
        
        col_mode = Y8/MONOCHROME/CBYCRY/BAYER
        """
        try :
            uEyeDll = ctypes.cdll.LoadLibrary("ueye_api_64.dll")
            ueye.get_dll_file = uEyeDll
        except :
            shutil.copy2("./ueye_api_64.dll", "C:/Windows/System32")
            uEyeDll = ctypes.cdll.LoadLibrary("ueye_api_64.dll")
            ueye.get_dll_file = uEyeDll
        self.size = size
        self.hCam = ueye.HIDS(id_cam)
        self.sInfo = ueye.SENSORINFO()
        self.cInfo = ueye.CAMINFO()
        self.pcImageMemory = ueye.c_mem_p()
        self.MemID = ueye.int()
        self.rectAOI = ueye.IS_RECT()
        self.pitch = ueye.INT()
        self.nBitsPerPixel = ueye.INT()
        self.channels = 3
        self.m_nColorMode = ueye.INT()
        self.bytes_per_pixel = int(self.nBitsPerPixel / 8)

        self.nRet = ueye.is_InitCamera(self.hCam, None)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_InitCamera ERROR: Cannot Connect and initialize the Camera."
            raise Exception(e)

        self.nRet = ueye.is_GetCameraInfo(self.hCam, self.cInfo)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_GetCameraInfo ERROR: Cannot Get Camera Infomation."
            raise Exception(e)

        self.nRet = ueye.is_GetSensorInfo(self.hCam, self.sInfo)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_GetSensorInfo ERROR: Cannot Get Camera Sensor Infomation."
            raise Exception(e)

        self.nRet = ueye.is_ResetToDefault(self.hCam)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_ResetToDefault ERROR: Cannot reset value of the camera."
            raise Exception(e)

        self.nRet = ueye.is_SetDisplayMode(self.hCam, ueye.IS_SET_DM_DIB)

        if col_mode == "BAYER" :
            ueye.is_GetColorDepth(self.hCam, self.nBitsPerPixel, self.m_nColorMode)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_BAYER: ", )
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        elif col_mode == "CBYCRY" :
            self.m_nColorMode = ueye.IS_CM_BGRA8_PACKED
            self.nBitsPerPixel = ueye.INT(32)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_CBYCRY: ", )
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        elif col_mode == "MONOCHROME" :
            self.m_nColorMode = ueye.IS_CM_MONO8
            self.nBitsPerPixel = ueye.INT(8)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_MONOCHROME: ", )
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        elif col_mode == "Y8" :
            self.m_nColorMode = ueye.IS_CM_MONO8
            self.nBitsPerPixel = ueye.INT(8)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_Y8: ", )
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        self.nRet = ueye.is_AOI(self.hCam, ueye.IS_AOI_IMAGE_GET_AOI, self.rectAOI, ueye.sizeof(self.rectAOI))
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_AOI ERROR: Cannot setup camera Area of Interest."
            raise Exception(e)
            
        self.width = self.rectAOI.s32Width
        self.height = self.rectAOI.s32Height

        self.siler = [int((self.width.value - self.size[0]) / 2), int((self.height.value - self.size[1]) / 2)]

        print("Camera model:\t\t", self.sInfo.strSensorName.decode('utf-8'))
        print("Camera serial no.:\t", self.cInfo.SerNo.decode('utf-8'))
        print("Maximum image width:\t", self.width)
        print("Maximum image height:\t", self.height)
        print()

        self.nRet = ueye.is_AllocImageMem(self.hCam, self.width, self.height, self.nBitsPerPixel, self.pcImageMemory, self.MemID)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_AllocImageMem ERROR: Cannot allocate Image Memory size."
            raise Exception(e)
        else:
            self.nRet = ueye.is_SetImageMem(self.hCam, self.pcImageMemory, self.MemID)
            if self.nRet != ueye.IS_SUCCESS:
                e = "is_SetImageMem ERROR: Cannot Set Image Memory."
                raise Exception(e)
            else:
                self.nRet = ueye.is_SetColorMode(self.hCam, self.m_nColorMode)

        self.nRet = ueye.is_CaptureVideo(self.hCam, ueye.IS_DONT_WAIT)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_CaptureVideo ERROR: Cannot get image from camera."
            raise Exception(e)

        self.nRet = ueye.is_InquireImageMem(self.hCam, self.pcImageMemory, self.MemID, self.width, self.height, self.nBitsPerPixel, self.pitch)
        if self.nRet != ueye.IS_SUCCESS:
            e = "is_InquireImageMem ERROR: Cannot Inquire image memory."
            raise Exception(e)

    def read(self) :
        try :
            array = ueye.get_data(self.pcImageMemory, self.width, self.height, self.nBitsPerPixel, self.pitch, copy=False)
            img = np.reshape(array,(self.height.value, self.width.value, self.bytes_per_pixel))
            img = img[self.siler[1]:self.siler[1]+self.size[1], self.siler[0]:self.siler[0]+self.size[0]]
            ret = True
        except :
            ret = False
        return ret, img
    
    def release(self) :
        ueye.is_FreeImageMem(self.hCam, self.pcImageMemory, self. MemID)
        ueye.is_ExitCamera(self.hCam)