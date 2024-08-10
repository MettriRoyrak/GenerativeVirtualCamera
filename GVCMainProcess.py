import cv2
import numpy as np
import math as m

try :
    cv2.ocl.setUseOpenCL(True)
except :
    pass

class MultiGridPrespective() :
    def __init__(self) :
        """
        Main Process for software.
        """
        pass
    
    def quadratic_curve(self, position_order, curve_step) :
        """
        Create list of Position of each point from start to end using Quadratic Curve Equation.

        position_order is the list of each position (x, y) the order of the Quadratic Curve Equation is upon range of the list

        for example :
        
        position_order = [
            [0, 0], 
            [0, 100], 
            [100, 400],
            [500, 400]
        ]
        """
        n = len(position_order) - 1
        if n < 1 :
            e = "Position Order cannot be least than 2"
            raise Exception(e)
        line_position = []
        for lenge_step in range(curve_step + 1) :
            t = lenge_step / curve_step
            i = 0
            for p in position_order :
                if i == 0 :
                    n_x = m.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) * p[0]
                    n_y = m.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) * p[1]
                else :
                    n_x += m.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) * p[0]
                    n_y += m.comb(n, i) * (t ** i) * ((1 - t) ** (n - i)) * p[1]
                i += 1
            line_position.append([n_x, n_y])
        return line_position
    
    def quadratic_grid(self, position_order_list, step, order) :
        """
        Create 2D list of grid position of element from 4 corner position with 4*order focus point.

        position_order_list data tag must use keyword {TOP, BOTTOM, LEFT, RIGHT} Dict to set infomation. 
        Which is one keyword must contain position list (x, y) for Quadratic Curve Equation (position list must be more than 1 and each line are must be the same range. but can be more as you like.)

        for example :
        
        position_order_list = {
        
            "TOP" : [[0, 0], [100, 0], [200, 100]],

            "BOTTOM" : [[0, 300], [100, 300], [200, 400]],

            "LEFT" : [[0, 0], [0, 100], [0, 300]],

            "RIGHT" : [[200, 100], [200, 250], [200, 400]]

        }

        """
        tpo = position_order_list["TOP"][0:order+1] + [position_order_list["TOP"][-1]]              # Top Position Order list
        bpo = position_order_list["BOTTOM"][0:order+1] + [position_order_list["BOTTOM"][-1]]        # Bottom Position Order list
        lpo = position_order_list["LEFT"][0:order+1] + [position_order_list["LEFT"][-1]]            # Left Position Order list
        rpo = position_order_list["RIGHT"][0:order+1] + [position_order_list["RIGHT"][-1]]          # Right Position Order list
        step_x = step[0]
        step_y = step[1]

        grid = []
        c_list = []

        plane_l = self.quadratic_curve(lpo, step_y)
        plane_r = self.quadratic_curve(rpo, step_y)
        for i in range(len(plane_l)) :
            for j in range(order) :
                c_adj = [(bpo[j+1][0] - tpo[j+1][0]) * (i / (len(plane_l) - 1)) + (tpo[j+1][0]), (bpo[j+1][1] - tpo[j+1][1]) * (i / (len(plane_l) - 1)) + (tpo[j+1][1])]
                c_list.append(c_adj)
            pos_line = self.quadratic_curve([plane_l[i]] + c_list + [plane_r[i]], step_x)
            if i != 0 :
                for j in range(len(pos_line) - 1) :
                    grid.append([old_line[j], old_line[j+1], pos_line[j],  pos_line[j+1]])
            old_line = pos_line
            c_list = []
        return grid
    
    def grid_merge(self, img, grid, output_size, step) :
        """
        take image to warp perspective with 2D grid position list of each area and reconstruction all image of each area.
        """
        scr_size = [img.shape[1], img.shape[0]]

        sp_x = int(output_size[0] / step[0])
        sp_y = int(output_size[1] / step[1])

        # create warped image and contain in list.
        dst_raw = []
        for i in range(len(grid)) :
            pts1 = np.float32([[int(grid[i][0][0]*scr_size[0]), int(grid[i][0][1]*scr_size[1])], [int(grid[i][1][0]*scr_size[0]), int(grid[i][1][1]*scr_size[1])], [int(grid[i][2][0]*scr_size[0]), int(grid[i][2][1]*scr_size[1])],[int(grid[i][3][0]*scr_size[0]), int(grid[i][3][1]*scr_size[1])]])
            pts2 = np.float32([[0, 0], [sp_x, 0], [0, sp_y], [sp_x, sp_y]])
            M_t = cv2.getPerspectiveTransform(pts1, pts2)
            dst_raw.append(cv2.warpPerspective(img, M_t, (int(sp_x), int(sp_y))))
            
        # reconstruction image.
        i = 0
        for row in range(int(step[1])) :
            for col in range(int(step[0])) :
                if col == 0 :
                    dst_row = dst_raw[i].copy()
                else :
                    dst_row = np.concatenate((dst_row, dst_raw[i]), axis=1)
                i += 1
            if row == 0 :
                dst_col = dst_row.copy()
            else :
                dst_col = np.concatenate((dst_col, dst_row), axis=0)
        return dst_col
    
    # def EXP_grid_merge(self, img, grid, output_size, grid_size) :
    #     """
    #     EXPERIMENTAL USING SINGLE SPACE IMAGE TO MERGE IN SINGLE IMAGE.
    #     RESULT : SLOWER PROCESSING TIME.
    #     """
    #     sp_x = int(output_size[0] / grid_size[0])
    #     sp_y = int(output_size[1] / grid_size[1])
    #     space = np.zeros((output_size[0],output_size[1],3), np.uint8)

    #     # create warped image and construction image at the same time.
    #     i = 0
    #     for row in range(int(grid_size[1])) :
    #         for col in range(int(grid_size[0])) :
    #             pts1 = np.float32(grid[i])
    #             pts2 = np.float32([[int(col*sp_x), int(row*sp_y)], [int(col*sp_x) + sp_x, int(row*sp_y)], [int(col*sp_x), int(row*sp_y) + sp_y], [int(col*sp_x) + sp_x, int(row*sp_y) + sp_y]])
    #             M_t = cv2.getPerspectiveTransform(pts1, pts2)
    #             i += 1
    #             space = cv2.warpPerspective(img, M_t, (output_size[0], output_size[1]))
    #     return space
    
def multi_filter(img, alpha, beta, d_k, t_k, m_k) :
    if cv2.ocl.useOpenCL :
        img = cv2.UMat(img)
    fil = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
    fil = cv2.bilateralFilter(fil, d_k, 10, 10)
    fil = cv2.medianBlur(fil, (t_k + (t_k + 1)%2))
    mean_kernel = np.ones((m_k, m_k),np.uint8) / (m_k ** 2)
    fil = cv2.filter2D(fil, -2, mean_kernel)
    return fil.get() if cv2.ocl.useOpenCL else fil

def camera_list_ports(test_range) :
    """
    Test the ports and returns a tuple with the available camera ports and the ones that are working.
    """
    non_working_ports = []
    dev_port = 0
    working_ports = []
    available_ports = []
    while len(non_working_ports) < test_range: # if there are more than 5 non working ports stop the testing. 
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            non_working_ports.append(dev_port)
            print("Port %s is not working." %dev_port)
        else:
            is_reading, img = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print("Port %s is working and reads images (%s x %s)" %(dev_port,h,w))
                available_ports.append(dev_port)
            else:
                print("Port %s for camera ( %s x %s) is present but does not reads." %(dev_port,h,w))
                working_ports.append(dev_port)
        dev_port +=1
    return available_ports, working_ports, non_working_ports