import socket
import sys
import json
import os
import io
from PIL import Image
import numpy as np
import time
import subprocess
from inspect import currentframe
import logging


class Client_Communicator_to_Unity:

    def __init__(self,use_unity_build = True, relative_unity_build_path = "/build/image.x86_64", log_level = logging.INFO):
        
        # Create logger
        log_path = "log/python_client.log"
        self.logger = logging.getLogger('python_client_log')
        self.logger.setLevel(logging.DEBUG)
        # Create console handler
        self.ch = logging.StreamHandler()
        self.ch.setLevel(log_level)
        # Create file handler
        self.fh = logging.FileHandler(log_path)
        self.fh.setLevel(logging.DEBUG)
        # Add formatter
        self.formatter_fh = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        self.fh.setFormatter(self.formatter_fh)
        self.formatter_ch = logging.Formatter('%(levelname)s : %(message)s')
        self.ch.setFormatter(self.formatter_ch)
        # Add fh and ch to logger
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)

        #Clear log at startup
        with open(log_path, 'w'):
            pass

        self.logger.debug("__init__(): starting python client.")

        self.relative_path_TCPsocket_config = "tcp_config.json"
        self.use_unity_build = use_unity_build
        self.file_directory = os.path.dirname(os.path.realpath("client.py"))
        self.unity_build_path = self.file_directory + relative_unity_build_path
        
        self.port = 50000
        self.host = "127.0.0.1"
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.1)
                

        if use_unity_build == True:
            ### For execution with BUILD
            # Start unity build
            try:
                self.logger.info("Starting Unity...")
                self.logger.debug("__init__(): starting: " + self.unity_build_path)
                #TODO maybe if you want: do not let subprocess.popen print found path 
                subprocess.Popen([self.unity_build_path])
                seconds = 4
                self.logger.info("Waiting " + str(seconds) + " seconds.")
                for i in range(seconds):
                    if seconds-i ==1:
                        self.logger.debug("__init__(): 1 \n")
                    else:
                        self.logger.debug("__init__(): " + str(seconds-i))
                    time.sleep(1) 
                               
            #except FileNotFoundError as e:    
            except IOError as e:    
                self.logger.fatal(e)
                self.logger.fatal('__init__(): Unity build can not be found; build has been moved. Check: python client: Client_Communicator_to_Unity in init(...,relative_unity_build_path,...')
                raise e
        else:
            self.logger.info("Use with unity editor, editor should now be running.\n")
            ### For execution with unity engine
        self.connect_to_server()

    def __enter__(self):
        return self
    
    #def __exit__(self, type, value, traceback):
    #    """sends end request to Unity, closes TCP connection. Called when used in with statement"""
    #    self.send_to_unity("",change_request=None)
    #    self.socket.close()
    
    def exit(self):
        """sends end request to Unity, closes TCP connection. Called when used in with statement"""
        if(self.use_unity_build):
            self.send_to_unity("True",change_request=None)
            self.logger.info("Exit-message is sent. Unity build and socket now closing.\n")
            self.logger.debug("exit(): Exit-message is sent. Unity build and socket now closing.\n")
        else:
            self.send_to_unity("False",change_request=None)
            self.logger.info("Exit-message is sent. Unity editor can now exit play mode and socket is now closing.\n")
            self.logger.debug("exit(): Exit-message is sent. Unity editor can now exit play mode and socket is now closing.\n")
        self.socket.close()
    
    def connect_to_server(self):
        self.logger.info("Client now connecting to server.")  
        self.logger.debug("connect_to_server(): Client now connecting to server.")  
        try:
            with open(self.relative_path_TCPsocket_config, 'r') as f:
                config = json.load(f)
                f.close()
                self.host = config["host"]
                self.port = config["port"]
            self.logger.info("Config data for TCP socket found.")
            self.logger.debug("connect_to_server(): config data for TCP socket: host: " + self.host + "; port: " + str(self.port)) 
        except IOError as e:
            self.logger.error("connect_to_server(): tcpconfig.json can not be found. Now using default: host: " + self.host + "; port: " + str(self.port))
            self.logger.error("connect_to_server(): Check: python client: Client_Communicator_to_Unity in init(): self.relative_path_TCPsocket_config; tcpconfig.json should be found in the same folder as client.py")
            pass
        # Connect the socket to the port where the server is listening
        while 1:
            try:
                self.socket.connect((self.host, self.port))
                self.logger.info("Socket connected.")
                self.logger.debug("connect_to_server(): Socket connected. Saving TCP config to self.relative_path_TCPsocket_config.\n")
                #if bytearray([99, 19, 99, 19, 99, 19, 99, 19, 99, 19, 99, 19, 99]) == self._receiveDataAsBytes():
                break
            except socket.error as e:
                self.logger.debug("connect_to_server(): socket can not connect: " + str(e))
                self.logger.debug("connect_to_server(): Make sure that the tcp_server from unity is already running.")
                # If port is in use, try next port
                if self.port >= 50050:
                    self.port = 49990
                else:
                    self.port += 1
                self.logger.debug("connect_to_server(): try next port: %s" %self.port)
            except socket.timeout:
                self.logger.debug("connect_to_server(): Socket.Timeout: socket can not connect")
                self.logger.debug("connect_to_server(): Make sure that the tcp_server from unity is already running. You could modify the TCPsocket_config.")
                # If port is in use, try next port
                if self.port >= 50050:
                    self.port = 49990
                else:
                    self.port += 0
                self.logger.debug("connect_to_server(): try next port: %s" %self.port)
        new_config = {} 
        new_config["host"] = self.host
        new_config["port"] = self.port
        self.connected = True
        with open(self.relative_path_TCPsocket_config, 'w') as f:
            json.dump(new_config, f)
            f.close()
    
    def send_to_unity(self, json_string, change_request):    
        # Send data
        if change_request:
            self.logger.debug("send_to_unity(): json_string with change_req. sent.\n")
            self.socket.sendall((json_string+"change."+"eod.").encode())
        elif change_request==False:        
            self.logger.debug("In send_to_unity(): json_string without change_req. sent.\n")
            self.socket.sendall((json_string+"eod.").encode())
        else:
            self.logger.debug("In send_to_unity(): exit request sent.\n")
            self.socket.sendall((json_string+"END.eod.").encode())
            
    def _receiveDataAsBytes(self):
        """receives data at the classes socket. ends by timeout, returns string object"""
        self.logger.debug("_receiveDataAsBytes(): entered.")
        
        data_complete = bytearray([0])
        while 1:
            try:
                data = self.socket.recv(1024)
            except socket.timeout:
                self.logger.debug("_receiveDataAsBytes(): timeout -> exit _receiveData()")
                self.logger.debug("_receiveDataAsBytes(): data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
            #TODO better format data_complete
            data_complete = data_complete + data
            if not data:
                self.logger.debug("_receiveDataAsBytes(): no data anymore exit member function.")
                self.logger.debug("_receiveDataAsBytes(): data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
        return data_complete

    def reciveImage(self, json_string, change_request=True):
        while(self.connected==False):
            self.logger.critical("reciveImage(): socket is still not connected. Waiting...\n")
            time.sleep(1)
        self.send_to_unity(json_string, change_request)
        self.logger.debug("reciveImage(): json_string sent.\n")
        
        unity_resp_bytes = bytes()
        while True:
            unity_resp_bytes = self._receiveDataAsBytes()
            self.logger.debug("reciveImage(): trying to recive data")
            if unity_resp_bytes[-8:] == bytearray([125, 99,255,255,255,255,255,255]):
                    self.logger.info("Data from Unity recived.")
                    self.logger.debug("reciveImage(): End_tag detected, unity_resp_bytes[0:30]: " + str(unity_resp_bytes[0:30]))
                    break
        
        img_bytes = unity_resp_bytes[1:-8]
        self.logger.debug("reciveImage(): img_bytes type: %s, img_bytes len: %s, img_bytes[:10]: %s" %(type(img_bytes),len(img_bytes),img_bytes[:10]))
        iobytes = io.BytesIO(img_bytes)
        pilImg = Image.open(iobytes)
        self.logger.debug("reciveImage(): pilImg: type: %s \n" %type(pilImg))
        img = np.array(pilImg)
        return img
    
    def writeJsonCrane(self, totalSegments=3, same_scale = True, scale=2, same_theta = True, theta=40, phi=0, totalArms_Segment=None,
    same_material = True, metallic=0.5, smoothness=0.5, r=1,g=1,b=1,a = 1,
    CameraRes_width = 256, CameraRes_height = 256, Camera_FieldofView = 60, CameraRadius = None, CameraTheta = 90, CameraPhi=0, CameraVerticalOffset = 0,
    totalPointLights=1, same_PointLightsColor = True, PointLightsColor_r = 1, PointLightsColor_g = 1, PointLightsColor_b = 1, PointLightsColor_a = 1, PointLightsRadius=[7], PointLightsTheta=[20], PointLightsPhi=[0], PointLightsIntensity=[1], PointLightsRange=[10], 
    totalSpotLights=1, same_SpotLightsColor = True, SpotLightsColor_r = 1, SpotLightsColor_g = 1, SpotLightsColor_b = 1, SpotLightsColor_a = 1, SpotLightsRadius=[10], SpotLightsTheta=[0], SpotLightsPhi=[0], SpotLightsIntensity=[1], SpotLightsRange=[10], SpotAngle=[30]):
        newScale = []
        #TODO have better logging in this function for assert errors are currently not logged.
        if(same_scale):
            if(isinstance(scale, list)):    
                    for i in range(0,totalSegments):
                        newScale.append(scale[0])
            else:
                    for i in range(0,totalSegments):
                        newScale.append(scale)
        else:
            assert len(scale) == totalSegments, " wrong json input Parameter; same_scale: " + str(same_scale) + "; The list scale has to be the size: " + str(totalSegments) + "; len(scale): " + str(len(scale))
            for i in range(0,totalSegments):
                    newScale.append(scale[i])
        
        newTheta = []
        if(same_theta):
            if(isinstance(theta, list)):    
                    for i in range(0,totalSegments):
                        newTheta.append(theta[0])
            else:
                    for i in range(0,totalSegments):
                        newTheta.append(theta)
        else:
            assert len(theta) == totalSegments-1, " wrong json input Parameter; sameTheta: " + str(same_theta) + "; The list theta has to be the size: " + str(totalSegments-1) + "; len(theta): " + str(len(theta))
            for i in range(0,totalSegments):
                if(i==0):
                    newTheta.append(0)
                else:
                    newTheta.append(theta[i-1])
    
        newMaterial = []
        if(same_material==True):
            for i in range(0,totalSegments):
                color = {}
                color['x'] = r
                color['y'] = g
                color['z'] = b
                color['w'] = a
                newMaterial.append({"color":color,"metallic":metallic,"smoothness":smoothness})
        else:
            assert len(metallic) == totalSegments, "len(metallic) has to be equal to totalSegments"
            assert len(r) == totalSegments, "len(r) has to be equal to totalSegments"
            assert len(g) == totalSegments, "len(g) has to be equal to totalSegments"
            assert len(b) == totalSegments, "len(b) has to be equal to totalSegments"
            if(len(a)!=totalSegments):
                for i in range(0,totalSegments):
                    a[i]=a[0]
            for i in range(0,totalSegments):
                color = {}
                color['x'] = r[i]
                color['y'] = g[i]
                color['z'] = b[i]
                color['w'] = a[i]
                newMaterial.append({"color":color,"metallic":metallic[i],"smoothness":smoothness[i]})
        
        data = {}
        data['totalSegments'] = totalSegments
        data['same_scale'] = same_scale
        data['same_theta'] = same_theta
        data['same_material'] = same_material
        data['phi'] = phi
        data['resolution_width'] = CameraRes_width
        data['resolution_height'] = CameraRes_height
        if(totalArms_Segment==None):
            totalArms_Segment = []
            for i in range(0,totalSegments-1):
                totalArms_Segment.append(1)
            data['totalArmsSegment']=totalArms_Segment
        else:
            assert type(totalArms_Segment)==list, "totalArmsSegment not a list" 
            assert len(totalArms_Segment)== totalSegments-1, "len(totalArmsSegment) has to be totalSegments-1" 
            data['totalArmsSegment']=totalArms_Segment

        if(CameraVerticalOffset==None):
            self.logger.info("CameraVerticalOffset is None, the origin of the spherical coordinates of the camera will be vertically offset depending on the crane height.\n") 
            self.logger.debug("writeJsonCrane(): CameraVerticalOffset is None, the origin of the spherical coordinates of the camera will be vertically offset depending on the crane height.\n") 
        if(CameraVerticalOffset!=0):
            self.logger.info("CameraVerticalOffset is not zero anymore, the origin of the spherical coordinates of the camera is now vertically offset.\n") 
            self.logger.debug("writeJsonCrane(): CameraVerticalOffset is not zero anymore, the origin of the spherical coordinates of the camera is now vertically offset.\n") 
        data['camera'] = {"radius":CameraRadius,"theta_deg":CameraTheta,"phi_deg":CameraPhi,"y_offset":CameraVerticalOffset,'resolution_width':CameraRes_width,'resolution_height':CameraRes_height,"FOV":Camera_FieldofView}
        #if CameraRadius is 0 then a fitting Radius is calculated in Unity
        #set up color of PointLights
        PointsColor = []
        if(same_PointLightsColor):    
            PointColor = {}
            PointColor['x'] = PointLightsColor_r
            PointColor['y'] = PointLightsColor_b
            PointColor['z'] = PointLightsColor_g
            PointColor['w'] = PointLightsColor_a
            for i in range(totalPointLights):    
                PointsColor.append(PointColor)
        else:
            assert type(PointLightsColor_r) == list, "PointLightsColor_r type has to be a list; type(PointLightsColor_r):"+str(type(PointLightsColor_r))
            assert len(PointLightsColor_r) == totalPointLights," wrong length of json input Parameter; The list PointLightsColor_r has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsColor_r): " + str(len(PointLightsColor_r))
            assert type(PointLightsColor_g) == list, "PointLightsColor_g type has to be a list; type(PointLightsColor_g):"+str(type(PointLightsColor_g))
            assert len(PointLightsColor_g) == totalPointLights," wrong length of json input Parameter; The list PointLightsColor_g has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsColor_g): " + str(len(PointLightsColor_r))
            assert type(PointLightsColor_b) == list, "PointLightsColor_b type has to be a list; type(PointLightsColor_b):"+str(type(PointLightsColor_b))
            assert len(PointLightsColor_b) == totalPointLights," wrong length of json input Parameter; The list PointLightsColor_b has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsColor_b): " + str(len(PointLightsColor_r))
            assert type(PointLightsColor_a) == list, "PointLightsColor_a type has to be a list; type(PointLightsColor_a):"+str(type(PointLightsColor_a))
            assert len(PointLightsColor_a) == totalPointLights," wrong length of json input Parameter; The list PointLightsColor_a has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsColor_a): " + str(len(PointLightsColor_r))
            for i in range(totalPointLights):
                PointColor = {}
                PointColor['x'] = PointLightsColor_r[i]
                PointColor['y'] = PointLightsColor_b[i]
                PointColor['z'] = PointLightsColor_g[i]
                PointColor['w'] = PointLightsColor_a[i]
                PointsColor.append(PointColor)
                        
        data['totalPointLights'] = totalPointLights
        if(totalPointLights!=0):
            data['point_lights'] = []
            assert type(PointLightsRadius) == list, "PointLightsRadius type has to be a list; type(PointLightsRadius):"+str(type(PointLightsRadius))
            assert type(PointLightsPhi) == list, "PointLightsPhi type has to be a list; type(PointLightsPhi):"+str(type(PointLightsPhi))
            assert type(PointLightsTheta) == list, "PointLightsTheta type has to be a list; type(PointLightsTheta):"+str(type(PointLightsTheta))
            assert len(PointLightsPhi) == totalPointLights," wrong length of json input Parameter; The list PointLightsPhi has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsPhi): " + str(len(PointLightsPhi))
            assert len(PointLightsTheta) == totalPointLights, " wrong length of json input Parameter; The list PointLightsTheta has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsTheta): " + str(len(PointLightsTheta))
            assert len(PointLightsRadius) == totalPointLights, " wrong length of json input Parameter; The list PointLightsRadius has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsRadius): " + str(len(PointLightsRadius))
            for i in range(0,totalPointLights):
                data['point_lights'].append({"radius":PointLightsRadius[i],"theta_deg":PointLightsTheta[i],"phi_deg":PointLightsPhi[i],"color":PointsColor[i],"intensity":PointLightsIntensity[i],"range":PointLightsRange[i]})
       
        #set up color of SpotLights
        SpotsColor = []
        if(same_SpotLightsColor):    
            Color = {}
            Color['x'] = SpotLightsColor_r
            Color['y'] = SpotLightsColor_b
            Color['z'] = SpotLightsColor_g
            Color['w'] = SpotLightsColor_a
            for i in range(totalSpotLights):    
                SpotsColor.append(Color)
        else:
            assert type(SpotLightsColor_r) == list, "SpotLightsColor_r type has to be a list; type(SpotLightsColor_r):"+str(type(SpotLightsColor_r))
            assert len(SpotLightsColor_r) == totalSpotLights," wrong length of json input Parameter; The list SpotLightsColor_r has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsColor_r): " + str(len(SpotLightsColor_r))
            assert type(SpotLightsColor_g) == list, "SpotLightsColor_g type has to be a list; type(SpotLightsColor_g):"+str(type(SpotLightsColor_g))
            assert len(SpotLightsColor_g) == totalSpotLights," wrong length of json input Parameter; The list SpotLightsColor_g has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsColor_g): " + str(len(SpotLightsColor_r))
            assert type(SpotLightsColor_b) == list, "SpotLightsColor_b type has to be a list; type(SpotLightsColor_b):"+str(type(SpotLightsColor_b))
            assert len(SpotLightsColor_b) == totalSpotLights," wrong length of json input Parameter; The list SpotLightsColor_b has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsColor_b): " + str(len(SpotLightsColor_r))
            assert type(SpotLightsColor_a) == list, "SpotLightsColor_a type has to be a list; type(SpotLightsColor_a):"+str(type(SpotLightsColor_a))
            assert len(SpotLightsColor_a) == totalSpotLights," wrong length of json input Parameter; The list SpotLightsColor_a has to be the size of totalSpotLSpotights: " + str(totalSpotLights) + "; len(SpotLightsColor_a): " + str(len(SpotLightsColor_r))
            for i in range(totalSpotLights):
                Color = {}
                Color['x'] = SpotLightsColor_r[i]
                Color['y'] = SpotLightsColor_b[i]
                Color['z'] = SpotLightsColor_g[i]
                Color['w'] = SpotLightsColor_a[i]
                SpotsColor.append(Color)

        data['totalSpotLights'] = totalSpotLights
        if(totalSpotLights!=0):
            data['spot_lights'] = []
            assert type(SpotLightsPhi) == list, "SpotLightsPhi type has to be a list; type(SpotLightsPhi):"+str(type(SpotLightsPhi))
            assert type(SpotLightsTheta) == list, "SpotLightsTheta type has to be a list; type(SpotLightsTheta):"+str(type(SpotLightsTheta))
            assert type(SpotLightsRadius) == list, "SpotLightsRadius type has to be a list; type(SpotLightsRadius):"+str(type(SpotLightsRadius))
            assert type(SpotLightsRange) == list, "SpotLightsRange type has to be a list; type(SpotLightsRange):"+str(type(SpotLightsRange))
            assert type(SpotAngle) == list, "SpotAngle type has to be a list; type(SpotAngle):"+str(type(SpotLightsRadius))
            assert len(SpotLightsPhi) == totalSpotLights," wrong length of json input Parameter; The list SpotLightsPhi has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsPhi): " + str(len(SpotLightsPhi))
            assert len(SpotLightsTheta) == totalSpotLights, " wrong length of json input Parameter; The list SpotLightsTheta has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsTheta): " + str(len(SpotLightsTheta))
            assert len(SpotLightsRadius) == totalSpotLights, " wrong length of json input Parameter; The list SpotLightsRadius has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsRadius): " + str(len(SpotLightsRadius))
            assert len(SpotLightsRange) == totalSpotLights, " wrong length of json input Parameter; The list SpotLightsRange has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotLightsRange): " + str(len(SpotLightsRange))
            assert len(SpotAngle) == totalSpotLights, " wrong length of json input Parameter; The list SpotAngle has to be the size of totalSpotLights: " + str(totalSpotLights) + "; len(SpotAngle): " + str(len(SpotAngle))
            
            for i in range(0,totalSpotLights):
                data['spot_lights'].append({"radius":SpotLightsRadius[i],"theta_deg":SpotLightsTheta[i],"phi_deg":SpotLightsPhi[i], "color":SpotsColor[i], "intensity":SpotLightsIntensity[i],"range":SpotLightsRange[i],"spot_angle":SpotAngle[i]})

        data['segments'] = []
        for i in range(0,totalSegments):
            data['segments'].append({"theta_deg":newTheta[i],"scale":newScale[i],"material":newMaterial[i]})
            json_string = json.dumps(data)        
        return json_string

        

'''
comm = Client_Communicator_to_Unity(use_unity_build=True)
jsonString = comm.writeJsonCrane(totalSegments = 3, totalArms_Segment=[1,1], phi = 90,scale= [2], theta= 20,
same_material= True, metallic=[0.5], smoothness=[0.5], r=[1],g=[0.3],b=[0],a=[1], 
CameraRadius=10, CameraTheta = 90, CameraPhi = 0, CameraRes_width=256, CameraRes_height=256, Camera_FieldofView=60,#CameraVerticalOffset=0,
totalPointLights = 1, PointLightsRadius=[25], PointLightsRange=[50], PointLightsIntensity=[25], PointLightsColor_r=0, SpotLightsColor_b=1.0, SpotLightsColor_g=1.0, SpotLightsColor_r=1.0, SpotLightsRadius = [30,17,28], SpotLightsTheta = [50,-90,140], SpotLightsPhi=[0,90,0], SpotLightsIntensity=[100,50,90],SpotLightsRange=[20,15,20],
totalSpotLights=3, SpotAngle=[90,50,60],same_theta=True)
print("PYTHON CLIENT: befor recive Image")
imge = comm.reciveImage(jsonString)
print("PYTHON CLIENT: after reciveImage; imge:")
print(type(imge), imge)
imgPIL = Image.fromarray(imge)
imgPIL.save("img1.png","PNG")
print("PYTHON CLIENT: imPIL: ")
print(imgPIL)
imgPIL.show()
comm.exit()
jsonString2 = comm.writeJsonCrane(totalSegments = 4, totalArms_Segment=[1,2,1], phi = 45,scale= [2], theta= 20,
same_material= True, metallic=[0.5], smoothness=[0.5], r=[1],g=[0.1],b=[0],a=[1], 
CameraRadius=10, CameraTheta = 90, CameraPhi = 0, CameraRes_width=720, CameraRes_height=480, Camera_FieldofView=60,#CameraVerticalOffset=0,
totalPointLights = 1, PointLightsRadius=[25], PointLightsRange=[50], PointLightsIntensity=[25], PointLightsColor_r=0, SpotLightsColor_b=1.0, SpotLightsColor_g=1.0, SpotLightsColor_r=1.0, SpotLightsRadius = [30,17,28], SpotLightsTheta = [50,-90,140], SpotLightsPhi=[0,90,0], SpotLightsIntensity=[100,50,90],SpotLightsRange=[20,15,20],
totalSpotLights=3, SpotAngle=[90,50,60],same_theta=True)
print("befor recive Image2")
imge2 = comm.reciveImage(jsonString2)
print("closing Socket")
comm.socket.close()
print("after reciveImage; imge2:")
print(type(imge2))
imgPIL2 = Image.fromarray(imge2)
imgPIL2.show()
'''