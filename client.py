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

class client_communicator_to_unity:

    def __init__(self,use_unity_build = True, log_level = logging.INFO):
        """Creates a socket and a logger for the console and saves a log file at: ``log/python_client.log``.
        Starts Unity if ``use_unity_build == True`` and waits until Unity is fully started to then call the function ``connect_to_server()``.
        
        :param use_unity_build: defaults to ``True``, \n
                                If this is set true the Unity build will start. Otherwise you should already set the Unity editor to play., 
        :type use_unity_build: bool, optional
        :param log_level: defaults to ``logging.INFO``, \n 
                            This variable sets the logging level of the console handler for the class which means how much information is displayed to your console. 
                            For debugging set it to: logging.DEBUG
        :type log_level: `int`, optional
        :raises IOError: Raises IOError if Unity build can not be found. 
        """   
        # Set up Data Paths
        self.relative_path_TCPsocket_config = "data/python/client_tcp_config.json"
        self.use_unity_build = use_unity_build
        self.file_directory = os.path.dirname(os.path.realpath("client.py")) #sys.argv[0] #sys.path[0] # # os.path.split(os.path.abspath(__file__))
        # Create logger
        self.log_path = self.file_directory + "/log/python_client.log"
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
                self.logger.fatal("Unity build can not be found; build has been moved. Check: python client: client_communicator_to_unity in init(...,relative_unity_build_path,...)")
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
    
    def connect_to_server(self):
        '''
        Establish tcp socket connection to Unity server.\n
        Load client tcp config from ``data/python/client_tcp_config.json``.\n
        Try to connect to the Unity server.\n
        If connection is established save the tcp config to ``data/python/client_tcp_config.json``.
        '''

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
            self.logger.error("Check: python client: client_communicator_to_unity in init(): self.relative_path_TCPsocket_config; tcpconfig.json should be found in the same folder as client.py")
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
    
    def exit(self):
        '''Close tcp connection and send end request to Unity which quits the build application.'''

        if(self.use_unity_build):
            self.logger.info("Exit-message is sent. Unity build and socket now closing.\n")
        else:
            self.logger.info("Exit-message is sent. Unity editor can now exit play mode and socket is now closing.\n")
        self.send_to_unity("",exit=True)
        self.socket.close()
    
    def send_to_unity(self, json_string, exit = False):    
        """Send data to Unity server.
        
        :param json_string: This string will be sent to Unity. Has to be readable by Unity.
        :type json_string: `string`
        :param exit: defaults to ``False``,\n 
                    If this is True the Unity build will close.
        :type exit: bool, optional
        """
        
        if exit:
            self.logger.debug("Exit request sent.\n")
            self.socket.sendall((json_string+"END.eod.").encode())
        else:
            self.logger.debug("Json string sent.\n")
            self.socket.sendall((json_string + "eod.").encode())
            
    def receive_data_as_bytes(self):
        """Receive image data from Unity trough socket. Ends by timeout, returns bytearray
        
        :return: From Unity recived bytearray. 
        :rtype: ``bytearray``
        """        

        data_complete = bytearray([0])
        while 1:
            # receive data from socket connection
            try:
                data = self.socket.recv(1024)
            except socket.timeout:
                self.logger.debug("Timeout -> exit _receiveData()")
                self.logger.debug("data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
            data_complete = data_complete + data
            if not data:
                self.logger.debug("No data anymore exit member function.")
                self.logger.debug("data_complete: type: %s, data_complete len: %s, data_complete [:10]: %s" %(type(data_complete),len(data_complete),data_complete[:10]))
                break
        return data_complete

    def receive_image(self, json_string):
        """Send string to Unity server and receive corresponding image.
        
        :param json_string: This ``string`` has to be comprehensible for Unity which are strings returned by :meth:`~client.client_communicator_to_unity.write_json_crane`
        :type json_string: string
        :return: Image corresponding to the input string.
        :rtype: `PngImageFile-array`
        """        
        
        while(self.connected==False):
            # Socket must be connnected at this point
            self.logger.critical("Socket is still not connected. Waiting...\n")
            time.sleep(1)
        # Send unity the json_string with the formatted information to create the image 
        self.send_to_unity(json_string)
        self.logger.debug("Json string sent.\n")
        
        unity_resp_bytes = bytes()
        while True:
            # receive data from Unity until the whole image is transferred
            unity_resp_bytes = self.receive_data_as_bytes()
            self.logger.debug("Trying to receive data.")
            if unity_resp_bytes[-8:] == bytearray([125, 99,255,255,255,255,255,255]):
                # Check if the data contains the whole image by looking for the end tag
                self.logger.info("Data from Unity received.")
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
    
    def write_json_crane(self, total_cuboids=3, same_scale = True, scale=2.0, same_theta = True, theta=40.0, phi=0.0, total_branches=None,
    same_material = True, metallic=0.5, smoothness=0.5, r=1.0,g=1.0,b=1.0,a = 1.0,
    CameraRes_width = 256, CameraRes_height = 256, Camera_FieldofView = 60.0, CameraRadius = 12.0, CameraTheta = 90.0, CameraPhi=0.0, CameraVerticalOffset = 0.0,
    DirectionalLightTheta = 30.0, DirectionalLightIntensity = 0.8,
    totalPointLights=1, same_PointLightsColor = True, PointLightsColor_r = 1.0, PointLightsColor_g = 1.0, PointLightsColor_b = 1.0, PointLightsColor_a = 1.0, PointLightsRadius=[7.0], PointLightsTheta=[20.0], PointLightsPhi=[0.0], PointLightsIntensity=[1.0], PointLightsRange=[10.0], 
    totalSpotLights=1, same_SpotLightsColor = True, SpotLightsColor_r = 1.0, SpotLightsColor_g = 1.0, SpotLightsColor_b = 1.0, SpotLightsColor_a = 1.0, SpotLightsRadius=[10.0], SpotLightsTheta=[0.0], SpotLightsPhi=[0.0], SpotLightsIntensity=[1.0], SpotLightsRange=[10.0], SpotAngle=[30.0]):
        """
        Returns string according to input parameter which can be interpreted by the Unity server. Should be used in function :meth:`~client.client_communicator_to_unity.receive_image` to create an image.
        
        :param total_cuboids:  The total amount of cubiods which will be "stacked" along one branch. Has to be bigger than zero, defaults to 3
        :type total_cuboids: int, optional
        :param same_scale: If the vertical scale of the cuboids should all be the same, defaults to True
        :type same_scale: bool, optional
        :param scale: The cuboids size vary only along the vertical dimension others are set to one. It is either a float if ``same_scale == True``  or a list of floats with the lenght of ``total_cuboids``, defaults to 2.0
        :type scale: 'float' or 'list', optional
        :param same_theta: If the angle between two stacked cuboids should be the same for every cuboid, defaults to True
        :type same_theta: bool, optional
        :param theta: The angle between two stacked cuboids in degrees. If it is zero the cuboids will be vertically allinged. If ``same_theta == True`` it has to be a float, else it has to be list of float with the length of ``total_cuboids - 1``, defaults to 40.0
        :type theta: float, optional
        :param phi: The rotation in degrees around the origin on the vertical axis for all cuboids i.e. the whole crane, defaults to 0.0
        :type phi: float, optional
        :param total_branches: If this is ``None`` there will be a Crane with one arm without any branches. If it is not ``None`` it has to be a ``list`` of integers with the length of ``total_cubiods-1``. 
                                The integers define how many branches are created at the cubiod corresponding to the index of the element in the list, defaults to None
        :type total_branches: None or list, optional
        :param same_material: If all cuboids should have the same material properties, defaults to True
        :type same_material: bool, optional
        :param metallic: The metallic property of the material of a cuboid should be in the range of zero and one. For more details have a look at the unity documentation. If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 0.5
        :type metallic: float or list, optional
        :param smoothness: 
            The smoothness property of the material of a cuboid should be in the range of zero and one.
            If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 0.5
        :type smoothness: float, optional
        :param r: The **red color** property of the material of a cuboid should be in the range of zero and one.
            If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 1.0
        :type r: float or list, optional
        :param g: The **green color** property of the material of a cuboid should be in the range of zero and one.
            If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 1.0
        :type g: float or list, optional
        :param b: The **blue color** property of the material of a cuboid should be in the range of zero and one.
            If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 1.0
        :type b: float or list, optional
        :param a: The **alpha channel/transparency** of the material of a cuboid should be in the range of zero and one with zero beeing fully transparent. For more details have a look at the unity documentation.
            If ``same_material == True`` it has to be a float, else it has to be a list of floats with the length of ``total_cuboids``, defaults to 1.0
        :type a: float or list, optional
        :param CameraRes_width: The **width resolution** of the receiving Image, defaults to 256
        :type CameraRes_width: int, optional
        :param CameraRes_height: The **height resolution** of the receiving Image, defaults to 256
        :type CameraRes_height: int, optional
        :param Camera_FieldofView: The **field of view** of the camera in degrees, defaults to 60.0
        :type Camera_FieldofView: float, optional
        :param CameraRadius: Position of the camera in spherical coordinates. The camera always faces the origin of the spherical coordinates, defaults to 12.0
        :type CameraRadius: float, optional
        :param CameraTheta: In degree the position of the camera in spherical coordinates. The camera always faces the origin of the spherical coordinates, defaults to 90.0
        :type CameraTheta: float, optional
        :param CameraPhi: In degree the position of the camera in spherical coordinates. The camera always faces the origin of the spherical coordinates, defaults to 0.0
        :type CameraPhi: float, optional
        :param CameraVerticalOffset: This parameter offstets the origin of the spherical coordinate system only for the camera in the vertical i.e y-axis direction. The camera always faces the origin of its spherical coordinates, defaults to 0.0
        :type CameraVerticalOffset: float, optional
        :param DirectionalLightTheta: The angle in degrees of the directional light i.e. the sun. *For more details have a look at the unity documentation*. If zero it is at the zenith i.e. directly above the origin, at 90 degrees the light comes from the horizon, defaults to 30.0
        :type DirectionalLightTheta: float, optional
        :param DirectionalLightIntensity: The intesity of the light should be between zero and one but can be set higher, defaults to 0.8
        :type DirectionalLightIntensity: float, optional
        :param totalPointLights: The total amount of Pointlights in the scene. *For more details about Pointlights have a look at the unity documentation*, defaults to 1
        :type totalPointLights: int, optional
        :param same_PointLightsColor: If all Pointlights should have the same color, defaults to True
        :type same_PointLightsColor: bool, optional
        :param PointLightsColor_r: The **red color** property of the light should be in the range of zero and one. If ``same_PointLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalPointLights``, defaults to 1.0
        :type PointLightsColor_r: float or list, optional
        :param PointLightsColor_g: The **green color** property of the light should be in the range of zero and one. If ``same_PointLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalPointLights``, defaults to 1.0
        :type PointLightsColor_g: float or list, optional
        :param PointLightsColor_b: The **blue color** property of the light should be in the range of zero and one. If ``same_PointLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalPointLights``, defaults to 1.0
        :type PointLightsColor_b: float or list, optional
        :param PointLightsColor_a: The **alpha channel/ transparency** of the color of the light should be in the range of zero and one. If ``same_PointLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalPointLights``, defaults to 1.0
        :type PointLightsColor_a: float or list, optional
        :param PointLightsRadius: The positions of all Pointlights in spherical coordinates. Has to be a list of floats with the length of ``totalPointLights``, defaults to [7.0]
        :type PointLightsRadius: list, optional
        :param PointLightsTheta: The positions of all Pointlights in spherical coordinates. Has to be a list of floats with the length of ``totalPointLights``, defaults to [20.0]
        :type PointLightsTheta: list, optional
        :param PointLightsPhi: The positions of all Pointlights in spherical coordinates. Has to be a list of floats with the length of ``totalPointLights``, defaults to [0.0]
        :type PointLightsPhi: list, optional
        :param PointLightsIntensity: The intensities of all Pointlights should be in the range of zero and one. Has to be a list of floats with the length of ``totalPointLights``, defaults to [1.0]
        :type PointLightsIntensity: list, optional
        :param PointLightsRange: The range of the emitted light from the Pointlights. Should be adjusted depending on the position of the lights to "reach" the cuboids. Has to be a list of floats with the length of ``totalPointLights``, defaults to [10.0]
        :type PointLightsRange: list, optional
        :param totalSpotLights: The total amount of Spotlights in the scene. *For more details about Spotlights have a look at the unity documentation*, defaults to 1
        :type totalSpotLights: int, optional
        :param same_SpotLightsColor: If all Spotlights should have the same color, defaults to True
        :type same_SpotLightsColor: bool, optional
        :param SpotLightsColor_r: The **red color** property of the light should be in the range of zero and one. If ``same_SpotLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalSpotLights``, defaults to 1.0
        :type SpotLightsColor_r: float or list, optional
        :param SpotLightsColor_g: The **green color** property of the light should be in the range of zero and one. If ``same_SpotLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalSpotLights``, defaults to 1.0
        :type SpotLightsColor_g: float or list, optional
        :param SpotLightsColor_b: The **blue color** property of the light should be in the range of zero and one. If ``same_SpotLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalSpotLights``, defaults to 1.0
        :type SpotLightsColor_b: float or list, optional
        :param SpotLightsColor_a: The **alpha channel/ transparency** of the color of the light should be in the range of zero and one. If ``same_SpotLightsColor == True`` it has to be a float, else it has to be a list of floats with the length of ``totalSpotLights``, defaults to 1.0
        :type SpotLightsColor_a: float or list, optional
        :param SpotLightsRadius: The positions of all Spotlights in spherical coordinates. Spotlights always face the origin. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [10.0]
        :type SpotLightsRadius: list, optional
        :param SpotLightsTheta: The positions of all Spotlights in spherical coordinates. Spotlights always face the origin. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [0.0]
        :type SpotLightsTheta: list, optional
        :param SpotLightsPhi: The positions of all Spotlights in spherical coordinates. Spotlights always face the origin. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [0.0]
        :type SpotLightsPhi: list, optional
        :param SpotLightsIntensity: The intensities of all Spotlights should be in the range of zero and one. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [1.0], defaults to [1.0]
        :type SpotLightsIntensity: list, optional
        :param SpotLightsRange: The range of the emitted light from the Spotlights. Should be adjusted depending on the position of the lights to "reach" the cuboids. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [10.0]
        :type SpotLightsRange: list, optional
        :param SpotAngle: In degree this describes the angle created by the cone of the Spotlight. Has to be a list of floats with the length of ``totalSpotLights``, defaults to [30.0]
        :type SpotAngle: list, optional
        :return: Returns a string with all given parameters for unity to interpret. Can be used in function :meth:`~client.client_communicator_to_unity.receive_image` to create an image.
        :rtype: string
        """        
        # Create a Dictionary with all the given information which can be read by the Unity script
        data = {}
        data['total_cuboids'] = total_cuboids
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
                    for i in range(0,total_cuboids):
                        newScale.append(scale[0])
            else:
                    for i in range(0,total_cuboids):
                        newScale.append(scale)
        else:
            # Use for every cuboid the given scale 
            assert len(scale) == total_cuboids, " wrong json input Parameter; same_scale: " + str(same_scale) + "; The list scale has to be the size of total_cuboids: " + str(total_cuboids) + "; len(scale): " + str(len(scale))
            for i in range(0,total_cuboids):
                    newScale.append(scale[i])

        # Get all the angels: Theta between two cubiods in an array
        newTheta = []
        if(same_theta):
            # Use the same angle for every Theta 
            if(isinstance(theta, list)):    
                    for i in range(0,total_cuboids):
                        newTheta.append(theta[0])
            else:
                    for i in range(0,total_cuboids):
                        newTheta.append(theta)
        else:
            # Use for every angle the given Theta 
            assert len(theta) == total_cuboids-1, " wrong json input Parameter; sameTheta: " + str(same_theta) + "; The list theta has to be the size total_cuboids-1: " + str(total_cuboids-1) + "; len(theta): " + str(len(theta))
            for i in range(0,total_cuboids):
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
            for i in range(0,total_cuboids):
                color = {}
                color['x'] = r
                color['y'] = g
                color['z'] = b
                color['w'] = a
                newMaterial.append({"color":color,"metallic":metallic,"smoothness":smoothness})
        else:
            # Use for every material of a cuboid the specified information 
            assert len(metallic) == total_cuboids, "len(metallic) has to be equal to total_cuboids"
            assert len(r) == total_cuboids, "len(r) has to be equal to total_cuboids"
            assert len(g) == total_cuboids, "len(g) has to be equal to total_cuboids"
            assert len(b) == total_cuboids, "len(b) has to be equal to total_cuboids"
            if(len(a)!=total_cuboids):
                for i in range(0,total_cuboids):
                    a[i]=a[0]
            for i in range(0,total_cuboids):
                color = {}
                color['x'] = r[i]
                color['y'] = g[i]
                color['z'] = b[i]
                color['w'] = a[i]
                newMaterial.append({"color":color,"metallic":metallic[i],"smoothness":smoothness[i]})
        # Add all the data of the cubiods to the dictionary
        data['cuboids'] = []
        for i in range(0,total_cuboids):
            data['cuboids'].append({"theta_deg":newTheta[i],"scale":newScale[i],"material":newMaterial[i]})
        
        # Specify if there should be created many cubiods branches
        if(total_branches==None):
            # If None there will be no branches created
            total_branches = []
            for i in range(0,total_cuboids-1):
                total_branches.append(1)    
        else:
            # Use the given information
            assert type(total_branches)==list, "total_branches not a list" 
            assert len(total_branches)== total_cuboids-1, "len(total_branches): " +  str(len(total_branches)) + " has to be equal to total_cuboids-1: " + str(total_cuboids-1) 
        # Add the information to the dictionary
        data['total_branches']=total_branches
        # Add the vertical offset of the coordinates of the camera  
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