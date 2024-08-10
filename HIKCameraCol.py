import cv2
import numpy as np
from MvCameraControl_class import *

class HIKCamera() :
    def __init__(self, id_cam = 0, size = [1600, 1200]) :
        """
        Simple Fuction for support HIK Camera.
        """
        self.size = size
        self.deviceList = MV_CC_DEVICE_INFO_LIST()
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE

        ret = MvCamera.MV_CC_EnumDevices(tlayerType, self.deviceList)
        if ret != 0:
            e = "Enum devices ERROR: enum devices fail! ret[0x%x]" % ret
            raise Exception(e)

        if self.deviceList.nDeviceNum == 0:
            e = "Devices ERROR: Devices Not Found!"
            raise Exception(e)
        else :
            print ("Find %d devices!" % self.deviceList.nDeviceNum)

        for i in range(0, self.deviceList.nDeviceNum):
            mvcc_dev_info = cast(self.deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
            if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                print ("\ngige device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    strModeName = strModeName + chr(per)
                print ("device model name: %s" % strModeName)

                nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                print ("\nu3v device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print ("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print ("user serial number: %s" % strSerialNumber)

        nConnectionNum = id_cam

        if int(nConnectionNum) >= self.deviceList.nDeviceNum:
            e = "Input ERROR: Camera index out of range!"
            raise Exception(e)

        self.cam = MvCamera()
        
        stDeviceList = cast(self.deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

        ret = self.cam.MV_CC_CreateHandle(stDeviceList)
        if ret != 0:
            e = "Handle ERROR: Create handle fail! ret[0x%x]" % ret
            raise Exception(e)

        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            print ("open device fail! ret[0x%x]" % ret)
            e = "Device ERROR: Open device fail! ret[0x%x]" % ret
            raise Exception(e)
        
        if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
            nPacketSize = self.cam.MV_CC_GetOptimalPacketSize()
            if int(nPacketSize) > 0:
                ret = self.cam.MV_CC_SetIntValue("GevSCPSPacketSize",nPacketSize)
                if ret != 0:
                    e = "Packet ERROR: Set Packet Size fail! ret[0x%x]" % ret
                    raise Exception(e)
            else:
                e = "Packet ERROR: Get Packet Size fail! ret[0x%x]" % nPacketSize
                raise Exception(e)

        stBool = c_bool(False)
        ret =self.cam.MV_CC_GetBoolValue("AcquisitionFrameRateEnable", stBool)
        if ret != 0:
            e = "Acquisition ERROR: Get AcquisitionFrameRateEnable fail! ret[0x%x]" % ret
            raise Exception(e)

        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        if ret != 0:
            e = "Trigger ERROR: Set trigger mode fail! ret[0x%x]" % ret
            raise Exception(e)

        ret = self.cam.MV_CC_StartGrabbing()
        if ret != 0:
            print ("start grabbing fail! ret[0x%x]" % ret)
            e = "Grabbing ERROR: Start grabbing fail! ret[0x%x]" % ret
            raise Exception(e)
        
        self.stOutFrame = MV_FRAME_OUT()
        self.st_frame_info = self.stOutFrame.stFrameInfo
        self.buf_cache = None
        self.img_buff = None
        
    def read(self) :
        """
        Get frame from HIK camera.
        """
        ret = self.cam.MV_CC_GetImageBuffer(self.stOutFrame, 1000)
        if None == self.buf_cache :
            self.buf_cache = (c_ubyte * self.stOutFrame.stFrameInfo.nFrameLen)()
        cdll.msvcrt.memcpy(byref(self.buf_cache), self.stOutFrame.pBufAddr, self.st_frame_info.nFrameLen)
        n_save_image_size = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3 + 2048
        if self.img_buff is None :
            self.img_buff = (c_ubyte * n_save_image_size)()

        stConvertParam = MV_CC_PIXEL_CONVERT_PARAM()
        memset(byref(stConvertParam), 0, sizeof(stConvertParam))
        stConvertParam.nWidth = self.st_frame_info.nWidth
        stConvertParam.nHeight = self.st_frame_info.nHeight
        stConvertParam.pSrcData = cast(self.buf_cache, POINTER(c_ubyte))
        stConvertParam.nSrcDataLen = self.st_frame_info.nFrameLen
        stConvertParam.enSrcPixelType = self.st_frame_info.enPixelType 

        if PixelType_Gvsp_RGB8_Packed == self.st_frame_info.enPixelType:
            numArray = self.Color_numpy(self.buf_cache, self.st_frame_info.nWidth, self.st_frame_info.nHeight)
        else:
            nConvertSize = self.st_frame_info.nWidth * self.st_frame_info.nHeight * 3
            stConvertParam.enDstPixelType = PixelType_Gvsp_RGB8_Packed
            stConvertParam.pDstBuffer = (c_ubyte * nConvertSize)()
            stConvertParam.nDstBufferSize = nConvertSize
            ret = self.cam.MV_CC_ConvertPixelType(stConvertParam)
            cdll.msvcrt.memcpy(byref(self.img_buff), stConvertParam.pDstBuffer, nConvertSize)
            numArray = self.Color_numpy(self.img_buff, self.st_frame_info.nWidth, self.st_frame_info.nHeight)

        try :
            self.siler = [int((self.st_frame_info.nWidth - self.size[0]) / 2), int((self.st_frame_info.nHeight - self.size[1]) / 2)]
            img = numArray[self.siler[1]:self.siler[1]+self.size[1], self.siler[0]:self.siler[0]+self.size[0]]
            img = cv2.resize(img, self.size)
            ret = True
            nRet = self.cam.MV_CC_FreeImageBuffer(self.stOutFrame)
        except :
            ret = False
            nRet = self.cam.MV_CC_FreeImageBuffer(self.stOutFrame)

        return ret, img

    def release(self) :
        """
        Stop record and free memory.
        """
        ret = self.cam.MV_CC_StopGrabbing()
        if ret != 0:
            e = "Grabbing ERROR: Stop grabbing fail! ret[0x%x]" % ret
            raise Exception(e)

        ret = self.cam.MV_CC_CloseDevice()
        if ret != 0:
            e = "Device ERROR: Close Device fail! ret[0x%x]" % ret
            raise Exception(e)

        ret = self.cam.MV_CC_DestroyHandle()
        if ret != 0:
            e = "Handle ERROR: Destroy handle fail! ret[0x%x]" % ret
            raise Exception(e)

    def Color_numpy(self, data, nWidth, nHeight) :
        """
        Transfer data buffer to numpy array (Color only)
        Internal Method.
        """
        data_ = np.frombuffer(data, count=int(nWidth*nHeight*3), dtype=np.uint8, offset=0)
        data_r = data_[0:nWidth*nHeight*3:3]
        data_g = data_[1:nWidth*nHeight*3:3]
        data_b = data_[2:nWidth*nHeight*3:3]

        data_r_arr = data_r.reshape(nHeight, nWidth)
        data_g_arr = data_g.reshape(nHeight, nWidth)
        data_b_arr = data_b.reshape(nHeight, nWidth)
        numArray = np.zeros([nHeight, nWidth, 3],"uint8")

        numArray[:, :, 0] = data_r_arr
        numArray[:, :, 1] = data_g_arr
        numArray[:, :, 2] = data_b_arr
        return numArray