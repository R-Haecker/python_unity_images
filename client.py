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

    def __init__(self,use_unity_build = True, log_level = logging.INFO):
        
        # Create logger
        self.log_path = "log/python_client.log"
        self.logger = logging.getLogger("python_client_log")
        self.logger.setLevel(logging.DEBUG)
        # Create console handler
        self.ch = logging.StreamHandler()
        self.ch.setLevel(log_level)
        # Create file handler
        self.fh = logging.FileHandler(self.log_path)
        self.fh.setLevel(logging.DEBUG)
        # Add formatter
        self.formatter_fh = logging.Formatter('%(asctime)s; %(filename)s - line: %(lineno)d -%(levelname)s: %(message)s')
        self.fh.setFormatter(self.formatter_fh)
        # Different formatter for different log_level
        if log_level==logging.DEBUG:
            self.formatter_ch = logging.Formatter('%(filename)s -line:%(lineno)d -%(levelname)s: %(message)s')
        else:
            self.formatter_ch = logging.Formatter('%(filename)s: %(message)s')
        self.ch.setFormatter(self.formatter_ch)
        # Add fh and ch to logger
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)
        # Clear log at startup
        with open(self.log_path, 'w'):
            pass

        self.logger.debug("Starting python client.")
        # Set up Data Paths
        self.relative_path_TCPsocket_config = "data/python/client_tcp_config.json"
        self.use_unity_build = use_unity_build
        self.file_directory = os.path.dirname(os.path.realpath("client.py"))

        # Determine OS for the right build to start
        osdata = os.uname()
        if osdata[0] == "Linux":
            relative_unity_build_path = "/build_linux/unity_server_rendering_images.x86_64"
        if osdata[0] == "Windows":
            relative_unity_build_path = "/build_windows/unity_server_rendering_images.exe"
        
        self.unity_build_path = self.file_directory + relative_unity_build_path
        # Set up Default properties 
        self.port = 50000
        self.host = "127.0.0.1"
        self.connected = False
        # Set up Socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.1)
                
        if use_unity_build == True:
        # For execution with BUILD: start Unity build
            self.logger.info("Starting Unity...")
            self.logger.debug("path to unity: " + self.unity_build_path)
            # Befor strarting unity set value in stated.txt to zero
            with open(self.file_directory + "/data/unity/started.txt","w") as f:
                f.write("0")
                f.close()
            try:
                # Start Unity and set log path of unity
                subprocess.Popen(self.unity_build_path + " -logFile ./log/unity.log" , shell=True)
            except IOError as e:    
                self.logger.fatal(e)
                self.logger.fatal("Unity build can not be found; build has been moved. Check: python client: Client_Communicator_to_Unity in init(...,relative_unity_build_path,...)")
                raise e
            # Wait until Unity is fully set up. unity writes a one in startet.txt if it is ready 
            self.logger.info("Waiting for unity...")
            zero_or_one = 0
            max_waiting = 100*2
            for i in range(max_waiting):
                try:
                    with open(self.file_directory + "/data/unity/started.txt","r") as f:
                        zero_or_one = f.read()
                        f.close()
                except FileNotFoundError as e:
                    self.logger.debug("started.txt not found.")
                if zero_or_one == "1":
                    break
                time.sleep(0.5)
        else:
        # For execution with unity engine
            self.logger.info("Use with unity editor, editor should now be running.\n")
        # Connect to Unity server 
        self.connect_to_server()
    
    def exit(self):
        ### Send end request to Unity, close TCP connection and application
        if(self.use_unity_build):
            self.logger.info("Exit-message is sent. Unity build and socket now closing.\n")
        else:
            self.logger.info("Exit-message is sent. Unity editor can now exit play mode and socket is now closing.\n")
        self.send_to_unity("",exit=True)
        self.socket.close()
    
    def connect_to_server(self):
        ### Establish socket connection to Unity server
        self.logger.info("Client now connecting to server.")  
        try:
            # Load TCP config: ip and port 
            with open(self.relative_path_TCPsocket_config, 'r') as f:
                config = json.load(f)
                f.close()
                self.host = config["host"]
                self.port = config["port"]
            self.logger.debug("Config data for TCP socket: host: " + self.host + "; port: " + str(self.port)) 
        except IOError as e:
            self.logger.error("tcpconfig.json can not be found. Now using default: host: " + self.host + "; port: " + str(self.port))
            self.logger.error("Check: python client: Client_Communicator_to_Unity in init(): self.relative_path_TCPsocket_config; tcpconfig.json should be found in the same folder as client.py")
            pass
        while 1:
            # Connect the socket to the listening server
            try:
                self.socket.connect((self.host, self.port))
                self.logger.info("Socket connected.")
                self.logger.debug("Saving TCP config to self.relative_path_TCPsocket_config.\n")
                break
            except socket.error as e:
                self.logger.debug("Socket can not connect. Make sure that the tcp_server from unity is already running.")
                self.logger.debug(e)
                #sleep for 0.05 secounds
                time.sleep(0.05)
                # If port is in use or not working, try next port
                if self.port >= 50050:
                    self.port = 49990
                else:
                    self.port += 1
                self.logger.debug("Try next port: %s" %self.port)
            except socket.timeout:
                # If port is in use, try next port
                self.logger.debug("Socket.Timeout: socket can not connect")
                self.logger.debug("Make sure that the tcp_server from unity is already running. You could modify the TCPsocket_config.")
                if self.port >= 50050:
                    self.port = 49990
                else:
                    self.port += 0
                self.logger.debug("Try next port: %s" %self.port)
        # Save that the connnection is established
        self.connected = True
        # Save the working ip and host to the socket config
        new_config = {} 
        new_config["host"] = self.host
        new_config["port"] = self.port
        with open(self.relative_path_TCPsocket_config, 'w') as f:
            json.dump(new_config, f)
            f.close()
    
    def send_to_unity(self, json_string, exit = False):    
        ### Send Data to Unity server
        if exit:
            self.logger.debug("Exit request sent.\n")
            self.socket.sendall((json_string+"END.eod.").encode())
        else:
            self.logger.debug("Json string sent.\n")
            self.socket.sendall((json_string + "eod.").encode())
            
    def _receiveDataAsBytes(self):
        ### Receive image data from Unity trough socket. Ends by timeout, returns bytearray
        data_complete = bytearray([0])
        while 1:
            # Recive data from socket connection
            try:
                data = self.socket.recv(1024)
            except socket.timeout:
                self.logger.debug("Timeout -> exit _receiveData()")
                self.logger.debug("data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
            #TODO better format data_complete
            data_complete = data_complete + data
            if not data:
                self.logger.debug("No data anymore exit member function.")
                self.logger.debug("data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
        return data_complete

    def reciveImage(self, json_string):
        ### Send json_string to Unity server and returns image in PngImageFile-array 
        while(self.connected==False):
            # Socket must be connnected at this point
            self.logger.critical("Socket is still not connected. Waiting...\n")
            time.sleep(1)
        # Send unity the json_string with the formatted information to create the image 
        self.send_to_unity(json_string)
        self.logger.debug("Json string sent.\n")
        
        unity_resp_bytes = bytes()
        while True:
            # Recive data from Unity until the whole image is transferred
            unity_resp_bytes = self._receiveDataAsBytes()
            self.logger.debug("Trying to recive data.")
            if unity_resp_bytes[-8:] == bytearray([125, 99,255,255,255,255,255,255]):
                # Check if the data contains the whole image by looking for the end tag
                self.logger.info("Data from Unity recived.")
                self.logger.debug("End_tag detected, unity_resp_bytes[0:10]: " + str(unity_resp_bytes[0:10]))
                break
        # Cut out bytes which are not pixels of the image and format bytes
        img_bytes = unity_resp_bytes[1:-8]
        self.logger.debug("img_bytes type: %s, img_bytes len: %s, img_bytes[:10]: %s" %(type(img_bytes),len(img_bytes),img_bytes[:10]))
        iobytes = io.BytesIO(img_bytes)
        pilImg = Image.open(iobytes)
        self.logger.debug("PIL Img: type: %s " %type(pilImg))
        img = np.array(pilImg)
        self.logger.debug("Returning img: type: %s \n" %type(img))
        return img
    
    def writeJsonCrane(self, totalSegments=3, same_scale = True, scale=2, same_theta = True, theta=40, phi=0, totalArms_Segment=None,
    same_material = True, metallic=0.5, smoothness=0.5, r=1,g=1,b=1,a = 1,
    CameraRes_width = 256, CameraRes_height = 256, Camera_FieldofView = 60, CameraRadius = None, CameraTheta = 90, CameraPhi=0, CameraVerticalOffset = 0,
    totalPointLights=1, same_PointLightsColor = True, PointLightsColor_r = 1, PointLightsColor_g = 1, PointLightsColor_b = 1, PointLightsColor_a = 1, PointLightsRadius=[7], PointLightsTheta=[20], PointLightsPhi=[0], PointLightsIntensity=[1], PointLightsRange=[10], 
    totalSpotLights=1, same_SpotLightsColor = True, SpotLightsColor_r = 1, SpotLightsColor_g = 1, SpotLightsColor_b = 1, SpotLightsColor_a = 1, SpotLightsRadius=[10], SpotLightsTheta=[0], SpotLightsPhi=[0], SpotLightsIntensity=[1], SpotLightsRange=[10], SpotAngle=[30],
    DirectionalLightTheta = 30, DirectionalLightIntensity = 0.8):
        ### Returns json data according to input parameter which can be interpreted by the Unity server
        
        # Create a Dictionary with all the given information which can be read by the Unity script
        data = {}
        data['totalSegments'] = totalSegments
        data['same_scale'] = same_scale
        data['same_theta'] = same_theta
        data['same_material'] = same_material
        data['phi'] = phi
        data['resolution_width'] = CameraRes_width
        data['resolution_height'] = CameraRes_height

        # Get all cubiod scale values in an array
        newScale = []
        if(same_scale):
            # Use the same scale for every cuboid
            if(isinstance(scale, list)):    
                    for i in range(0,totalSegments):
                        newScale.append(scale[0])
            else:
                    for i in range(0,totalSegments):
                        newScale.append(scale)
        else:
            # Use for every cuboid the given scale 
            assert len(scale) == totalSegments, " wrong json input Parameter; same_scale: " + str(same_scale) + "; The list scale has to be the size of totalSegments: " + str(totalSegments) + "; len(scale): " + str(len(scale))
            for i in range(0,totalSegments):
                    newScale.append(scale[i])

        # Get all the angels: Theta between two cubiods in an array
        newTheta = []
        if(same_theta):
            # Use the same angle for every Theta 
            if(isinstance(theta, list)):    
                    for i in range(0,totalSegments):
                        newTheta.append(theta[0])
            else:
                    for i in range(0,totalSegments):
                        newTheta.append(theta)
        else:
            # Use for every angle the given Theta 
            assert len(theta) == totalSegments-1, " wrong json input Parameter; sameTheta: " + str(same_theta) + "; The list theta has to be the size totalSegments-1: " + str(totalSegments-1) + "; len(theta): " + str(len(theta))
            for i in range(0,totalSegments):
                # Every cuboid has the information Theta for the angle between the cuboid which was placed before it and itself 
                if(i==0):
                    # By definition the first cuboid can not have an angle
                    newTheta.append(0)
                else:
                    newTheta.append(theta[i-1])

        # Get the information about the materials
        # The color is determined by RGBA, r is red, g is green, b is blue and a is alpha/transperency
        # The material is also dependent of the metallic- and smoothness value, for further informations look into the unity documentation
        newMaterial = []
        if(same_material==True):
            # Use the same material for every cubiod
            for i in range(0,totalSegments):
                color = {}
                color['x'] = r
                color['y'] = g
                color['z'] = b
                color['w'] = a
                newMaterial.append({"color":color,"metallic":metallic,"smoothness":smoothness})
        else:
            # Use for every material of a cuboid the specified information 
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
        # Add all the data of the cubiods to the dictionary
        data['segments'] = []
        for i in range(0,totalSegments):
            data['segments'].append({"theta_deg":newTheta[i],"scale":newScale[i],"material":newMaterial[i]})
        
        # Specify if there should be created many cubiods branches
        if(totalArms_Segment==None):
            # If None there will be no branches created
            totalArms_Segment = []
            for i in range(0,totalSegments-1):
                totalArms_Segment.append(1)    
        else:
            # Use the given information
            assert type(totalArms_Segment)==list, "totalArmsSegment not a list" 
            assert len(totalArms_Segment)== totalSegments-1, "len(totalArmsSegment): " +  str(len(totalArms_Segment)) + " has to be equal to totalSegments-1: " + str(totalSegments-1) 
        # Add the information to the dictionary
        data['totalArmsSegment']=totalArms_Segment
        # Add the vertical offset of the coordinates of the camera  
        #TODO not sure if this is still true 
        if(CameraVerticalOffset==None):
            self.logger.info("CameraVerticalOffset is None, the origin of the spherical coordinates of the camera will be vertically offset depending on the crane height.\n") 
        if(CameraVerticalOffset!=0):
            self.logger.info("CameraVerticalOffset is not zero anymore, the origin of the spherical coordinates of the camera is now vertically offset.\n") 
        # Add all the information for the Camera into the dictonary
        data['camera'] = {"radius":CameraRadius,"theta_deg":CameraTheta,"phi_deg":CameraPhi,"y_offset":CameraVerticalOffset,'resolution_width':CameraRes_width,'resolution_height':CameraRes_height,"FOV":Camera_FieldofView}
        
        data["DirectionalLight"] = {"theta_deg":DirectionalLightTheta, "intensity":DirectionalLightIntensity}

        # Add the information of the PointLights
        data['totalPointLights'] = totalPointLights
        if(totalPointLights!=0):
            PointsColor = []
            if(same_PointLightsColor):    
                # Use the same color for ever Pointlight
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
            # Add the information to the dictionary
            data['point_lights'] = []
            assert type(PointLightsRadius) == list, "PointLightsRadius type has to be a list; type(PointLightsRadius):"+str(type(PointLightsRadius))
            assert type(PointLightsPhi) == list, "PointLightsPhi type has to be a list; type(PointLightsPhi):"+str(type(PointLightsPhi))
            assert type(PointLightsTheta) == list, "PointLightsTheta type has to be a list; type(PointLightsTheta):"+str(type(PointLightsTheta))
            assert len(PointLightsPhi) == totalPointLights," wrong length of json input Parameter; The list PointLightsPhi has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsPhi): " + str(len(PointLightsPhi))
            assert len(PointLightsTheta) == totalPointLights, " wrong length of json input Parameter; The list PointLightsTheta has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsTheta): " + str(len(PointLightsTheta))
            assert len(PointLightsRadius) == totalPointLights, " wrong length of json input Parameter; The list PointLightsRadius has to be the size of totalPointLights: " + str(totalPointLights) + "; len(PointLightsRadius): " + str(len(PointLightsRadius))
            for i in range(0,totalPointLights):
                data['point_lights'].append({"radius":PointLightsRadius[i],"theta_deg":PointLightsTheta[i],"phi_deg":PointLightsPhi[i],"color":PointsColor[i],"intensity":PointLightsIntensity[i],"range":PointLightsRange[i]})
        
        data['totalSpotLights'] = totalSpotLights
        if(totalSpotLights!=0):
            # Set up color of SpotLights
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
            # Add the Information of the Spotlights to the dictonary
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
        
        # Format the dictionary with all the data to a string and return it
        json_string = json.dumps(data)        
        return json_string
