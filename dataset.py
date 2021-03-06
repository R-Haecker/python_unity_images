from PIL import Image
import client
#from edflow.data.dataset import DatasetMixin
import numpy as np
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import tkinter
import json
import math
import logging
import copy
import time
import os
from os.path import expanduser

class dataset_cuboids():
    def __init__(self, dataset_name = None, unique_data_folder = True, debug_log = False, use_unity_build = True,  dataset_directory=None, absolute_path=False, port_range = [49990,50050]):
        """Sets up logging, the config, necessary paths and a client instance form :class:`~client.client_communicator_to_unity`.
        
        :param dataset_name: If this is not default the created images and parameters are saved into a folder nested in ``data/dataset/`` containing the dataset_name, defaults to None
        :type dataset_name: string or None, optional
        :param unique_data_folder: If ``True`` the name of the folder for your dataset will start with a time stamp. If ``False`` the name of the folder will only contain the name of the dataset and can be used across many instances of this class, defaults to True
        :type unique_data_folder: bool, optional
        :param use_unity_build: If this is set to true image generation will work automatically with the Unity build. Otherwise you have to manually set the Unity editor to play, defaults to True
        :type use_unity_build: bool, optional
        :param debug_log: If there should be more information displayed in the console for debugging, defaults to False
        :type debug_log: bool, optional
        """        
        #  Set up log level
        if debug_log:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        # Set up a client and start unity 
        print("before client")
        self.uc = client.client_communicator_to_unity(use_unity_build=use_unity_build, log_level = log_level, port_range = port_range)
        print("after client")
        self.file_directory =  os.path.dirname(os.path.realpath(__file__)) #os.path.split(os.path.abspath(__file__)) 
        # Use already existing logger from pthon for dataset as well
        self.log_path = self.file_directory + "/log/python_dataset_and_client.log"
        self.logger = self.uc.logger
        # Create file handler
        self.fh = logging.FileHandler(self.log_path)
        self.fh.setLevel(logging.DEBUG)
        # Add formatter
        self.formatter_fh = logging.Formatter('%(asctime)s; %(filename)s - line: %(lineno)d -%(levelname)s: %(message)s')
        self.fh.setFormatter(self.formatter_fh)
        # Different formatter for different log_level
        # Add fh to logger
        self.logger.addHandler(self.fh)
        # Clear log at startup
        with open(self.log_path, 'w'):
            pass
        
        if dataset_name != None:
            assert type(dataset_name) == str , "In dataset.py, __init__() function: dataset_name has to be a string." 
            assert ' ' not in dataset_name,  "In dataset.py, __init__() function: dataset_name does contain white spaces, leads to problems in saving and loading data."
        
        self.init_time = time.strftime("%Y-%m-%d_%H:%M", time.gmtime())
        #self.init_index = self.read_index()

        # Create unique name for the folder where the dataset is saved
        if dataset_name != None:
            if unique_data_folder:
                full_folder_name = self.init_time + "__" + dataset_name 
            else:
                full_folder_name = dataset_name 
    
        if dataset_directory==None:
            directory = "data/dataset/" + full_folder_name
        else:
            assert dataset_directory[-1] == "/" , "dataset_directory is string for a directory, has to end with '/'."
            if absolute_path:
                assert dataset_directory[0] == "/" , "dataset_directory is string for a directory, absolute_path is true --> has to start with '/'."
                directory = dataset_directory + full_folder_name
            else:
                home = expanduser("~")
                self.logger.debug("home directory: " + str(home))
                directory = home + dataset_directory + full_folder_name
        self.data_directory = directory
        self.logger.debug("Dataset directory:" + directory)
        self.logger.debug("Create config.")
        # Create dataset config for random parameter creation and set the default intervalls for all random generated parameters
        self.set_config()
        
        self.logger.debug("Dataset initialised.\n")     

    def set_config(self, save_config = True, request_pose = False, request_three = False, same_scale=None, scale=[0.5,4], total_cuboids=[2,5], phi=[0,360], specify_branches=False, branches=[1,3], same_theta=None, theta=None, 
    same_material=None, specify_material=False, r=[0,1], g=[0,1], b=[0,1], a=1, metallic=[0,1], smoothness=[0,1], CameraRes_width= 1024, CameraRes_height=1024, Camera_FieldofView=90, CameraRadius = None, CameraTheta = [60,100], CameraPhi = [0,360], CameraVerticalOffset = None, Camera_solid_background = False,
    totalPointLights=[5,12], PointLightsRadius=[5,20], PointLightsPhi=[0,360], PointLightsTheta=[0,90], PointLightsIntensity=[7,17], PointLightsRange=[5,25], same_PointLightsColor=None, PointLightsColor_r=[0,1], PointLightsColor_g=[0,1], PointLightsColor_b=[0,1], PointLightsColor_a=[0.5,1],
    totalSpotLights=[3,7], SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotAngle=[5,120], same_SpotLightsColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
    DirectionalLightTheta = [0,90], DirectionalLightIntensity = [1.0,5.0], specify_scale=False, specify_theta=False):
        """Sets a config for this class instace which determines the interval for all random parameters created in the function :meth:`~dataset.dataset_cuboids.create_random_parameters`. The meaning of all the parameters are explained in this function: :meth:`~client.client_communicator_to_unity.write_json_crane`. 
        Here are only those parameters mentioned which deviate from the ``standard_parameter``. You can also specify and set parameters which should not be generated randomly.
        
        :param "save_config": This flag indicates if the config should be saved. It should be kept at the default: ``True``. 
        :type "save_config": bool, optional
        :param "request_pose": This flag indicates if a groundtruth of the pose in form of an image has to be created. 
        :type "request_pose": bool, optional
        :param "standard_parameter": Has to be a list with two floats. The first element describes the lower boundary and second element describes the upper boundary for the function :meth:`~dataset.dataset_cuboids.create_random_parameters` in which the variable is set randomly, defaults is a predefined list
        :type "standard parameter": list, optional
        :param same_scale: If ``None`` the boolean will be set randomly in :meth:`~dataset.dataset_cuboids.create_random_parameters`. Otherwise it will be set to the given boolean, defaults to None
        :type same_scale: None or bool, optional
        :param specify_branches: Mainly leave it at the default: False, but if you wish to set the parameter ``branches`` not randomly you can set it to ``True`` and specify them. 
        :type specify_branches: bool, optional
        :param branches: If ``None`` there will be no branches which means one main branch. Else has to be a list with two integers. The amount of branches created in :meth:`~dataset.dataset_cuboids.create_random_parameters` at every cuboid will be chosen from a normal distribution where the second element of this list is interpreted als three sigma deviation, there is also a thrid option to set this parameter to a fixed value: you can use ``specyfy_branches = True`` and input a list with your desired values with a length of ``total_cuboids - 1``, defaults to [1,3]
        :type branches: None or list, optional
        :param same_theta: If ``None`` the boolean will be set randomly in :meth:`~dataset.dataset_cuboids.create_random_parameters`. Otherwise it will be set to the given boolean, defaults to None
        :type same_theta: None or bool, optional
        :param theta: If ``None`` the values for theta is set randomly between zero and ``360/total_cuboids``. Otherwise it has to be a list of length 2. If you want fixed values you can input a float or an int if ``same_theta = True``, if you want fixed values with ``same_theta = False`` you have to set ``specify_theta = True``, defaults to None
        :type theta: None, list, float or int, optional
        :param same_material: If ``None`` the boolean will be set randomly in :meth:`~dataset.dataset_cuboids.create_random_parameters`. Otherwise it will be set to the given boolean, defaults to None
        :type same_material: None or bool, optional
        :param CameraRes_width: The width Resolution of your image, default to 1024
        :type CameraRes_width: int, optional
        :param CameraRes_height: The height Resolution of your image, default to 1024
        :type CameraRes_height: int, optional
        :param Camera_FieldofView: The Fiel of View of the camera, default to 80
        :type Camera_FieldofView: float or int, optional
        :param CameraRadius: If a ``float`` or ``int`` is entered then the value in :meth:`~dataset.dataset_cuboids.create_random_parameters` will not be random, instead set to the given value. If it is a list it has to be a list of length two. If it is set to `None`it will be calculated to fit the enire crane in the picture, defaults to 10.0
        :type CameraRadius: float, int, None or list, optional
        :param CameraTheta:  If ``float`` or ``int`` then the value in :meth:`~dataset.dataset_cuboids.create_random_parameters` will not be random, instead set to the given value. If it is a list it has to be a list of length two, defaults to [30,100]
        :type CameraTheta: float, int or list, optional
        :param CameraPhi:  If input is ``float`` or ``int`` then the value in :meth:`~dataset.dataset_cuboids.create_random_parameters` will not be random, instead set to the given value. If it is a list it has to be a list of length two, defaults to [0,360]
        :type CameraPhi: float, int or list, optional
        :param CameraVerticalOffset: If ``None`` it is set to zero. If input is ``float`` or ``int`` then the value in :meth:`~dataset.dataset_cuboids.create_random_parameters` will not be random, instead set to the given ``float``. If it is a list it has to be a list of length two, defaults to None
        :type CameraVerticalOffset: None, float, int or list, optional
        :param totalPointLights: If ``None`` there will be no Pointlights created in :meth:`~dataset.dataset_cuboids.create_random_parameters`. Else it has to be a list of integers with the length two, defaults to [5,12]
        :type totalPointLights: None or list, optional
        :param same_PointLightsColor: If ``None`` the boolean will be chosen randomly, else the given boolean is used, defaults to None
        :type same_PointLightsColor: None or bool, optional
        :param totalSpotLights:  If ``None`` there will be no Spotlights created in :meth:`~dataset.dataset_cuboids.create_random_parameters`. Else it has to be a list of integers with the length two, defaults to None
        :type totalSpotLights: None or list, optional
        :param same_SpotLightsColor: If ``None`` the boolean will be chosen randomly, else the given boolean is used, defaults to None
        :type same_SpotLightsColor: None or bool, optional
        :param DirectionalLightTheta: If ``None`` the ``DirectionalLightIntensity`` will be set to zero, elif has to be a list of floats with the length two, for a fixed value enter a ``float`` or ``int``, defaults to [0,90]
        :type DirectionalLightTheta: None, float, int or list, optional
        :param DirectionalLightIntensity: If ``None`` the ``DirectionalLightIntensity`` will be set to zero, elif has to be a list of floats with the length two, for a fixed value enter a ``float`` or ``int``, defaults to [0.1,1.8]
        :type DirectionalLightIntensity: None, float, int or list, optional
        :param specify_scale: If this is set ``True`` you can enter the fixed values for ``scale`` even if ``same_scale = False``, defaults to False
        :type specify_scale: bool, optional
        :param specify_theta: If this is set ``True`` you can enter the fixed values for ``theta`` even if ``same_theta = False``, defaults to False
        :type specify_theta: bool, optional
        """        
        
        config = {}
        # Create intervals for general properties
        if type(total_cuboids)==int:
            config["total_cuboids"]=total_cuboids
        else:    
            assert len(total_cuboids) == 2, "total_cuboids either int or total_cuboids[0] is minimal limit and total_cuboids[1] is maximal limit for random generation of total_cuboids"
            config["total_cuboids"]=total_cuboids
        # Use the same_theta for every angle between two cubiods
        if same_theta!=None:
            assert type(same_theta)==bool, "Has to be bool or none. same_theta sets the bool of same_theta in getRandomJsonData. If it is None bool is set randomly." 
        config["same_theta"]=same_theta
        
        if specify_theta:
            assert same_theta != None, "You can not specify theta if same_theta is not specified"    
            if same_theta:
                assert type(theta)in [float, int], "specify_theta and same_theta is true, theta has to be a float"
            else:
                assert len(theta) == total_cuboids-1, "specify_theta is true and same_theta is false, theta has to be a list of length total_cuboids-1."
        #else:
        #    if same_theta == False:
                #assert type(theta)==list, "If same_theta is None i.e. randomly choosen, theta can not be specified exactly, has to be choosen randomly as well. This means theta has to be a list of length 2 with theta[0] is minimal limit and theta[1] is maximal limit for random generation theta."
                #assert len(theta)==2, "If same_theta is None i.e. randomly choosen, theta can not be specified exactly, has to be choosen randomly as well. This means theta has to be a list of length 2 with theta[0] is minimal limit and theta[1] is maximal limit for random generation theta."
        config["specify_theta"]=specify_theta
        config["theta"]=theta
        
        # Phi describes by how much the crane is rotated
        if type(phi)==list:
            assert len(phi)==2, "Phi is a list, has to be of langth two. Or a float for not random generation."
        else:
            assert type(phi)in [float, int], "Phi is not a list then it hast to be a float."
        config["phi"]=phi
        
        # Use the same scale for every cubiod
        if same_scale==None:
            assert specify_scale==False, "You can not specify the scale if you do not specify same_scale."
            assert type(scale)==list, "If same_scale = None i.e. randomly generated then scale hast to be also randomly generated.Which means scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods or a float not a list."
            assert len(scale) == 2, "If same_scale = None i.e. randomly generated then scale hast to be also randomly generated.Which means scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods or a float not a list."
        else:
            assert type(same_scale)==bool, "Has to be bool or None; same_scale sets the bool of same_scale in getRandomJsonData. If it is None bool is set randomly." 
        config["same_scale"]=same_scale
        
        # Vertical Scale of the cubiods
        if specify_scale:
            if same_scale:
                assert type(scale)in [float, int], "specify_scale and same_scale is true; scale has to be a float."
            else:
                assert len(scale) == total_cuboids, "specify_scale is true and same_scale is flase; if you want to specify the scale is has to be length total_cuboids"
        else:    
            if same_scale in [False,None]:
                assert type(scale)==list, "If same_scale = None i.e. randomly generated then scale hast to be also randomly generated.Which means scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods or a float not a list."
                assert len(scale) == 2, "If same_scale = None i.e. randomly generated then scale hast to be also randomly generated.Which means scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods or a float not a list."     
        config["specify_scale"]=specify_scale    
        config["scale"]=scale    
        
        # The upper limit for the arms is dicribing the three sigma variance of the guassion normal distribution for random generation of total_branches
        if specify_branches:
            if branches!=None:
                assert len(branches)==total_cuboids-1, "Has to be list of length 2 or length total_cuboids-1 or type None; branches defines boundaries for how many arms could be created in getRandomJsonData. This means that there is a chance that the crane splits up in the given range. If it is None then there will be only one arm." 
        else:
            if branches!=None:
                assert type(branches) == list, "Has to be list of length 2 or length total_cuboids-1 or type None; branches defines boundaries for how many arms could be created in getRandomJsonData. This means that there is a chance that the crane splits up in the given range. If it is None then there will be only one arm." 
                assert len(branches) == 2, "Has to be list of length 2 or length total_cuboids-1 or type None; branches defines boundaries for how many arms could be created in getRandomJsonData. This means that there is a chance that the crane splits up in the given range. If it is None then there will be only one arm." 
                assert branches[0] > 0, "branches has to be 1 or greater to even create one Arm."
                assert branches[1] > 0, "branches has to be 1 or greater to even create one Arm."
        config["specify_branches"] = specify_branches
        config["branches"] = branches
        
        # Create intervals or fixed values for camera position
        config["CameraRes_height"] = CameraRes_height
        config["CameraRes_width"] = CameraRes_width
        config["Camera_FieldofView"] = Camera_FieldofView
        if type(CameraRadius)== list:
            assert len(CameraRadius) == 2, "CameraRadius has to be a list len()==2 or a float for a fixed value."
        elif CameraRadius == None:
            CameraRadius = -1
        else:
            assert type(CameraRadius)in [float, int],"CameraRadius has to be a list len()==2 or a float for a fixed value."
        config["CameraRadius"] = CameraRadius 
        if type(CameraTheta)== list:
            assert len(CameraTheta) == 2, "CameraTheta has to be a list len()==2 or a float for a fixed value."
        else:
            assert type(CameraTheta)in [float, int], "CameraTheta has to be a list len()==2 or a float for a fixed value."
        config["CameraTheta"] = CameraTheta 
        if type(CameraPhi)== list:
            assert len(CameraPhi) == 2, "CameraPhi has to be a list len()==2 or a float for a fixed value."
        else:
            type(CameraPhi)in [float, int], "CameraPhi has to be a list len()==2 or a float for a fixed value."
        config["CameraPhi"] = CameraPhi 
        if CameraVerticalOffset==None:
            config["CameraVerticalOffset"] = 0    
        else:
            if type(CameraVerticalOffset)== list:
                assert len(CameraVerticalOffset) == 2, "CameraVerticalOffset has to be a list len()==2 or a float for a fixed value."
            else:
                assert type(CameraVerticalOffset)in [float, int], "CameraVerticalOffset has to be a list len()==2 or a float for a fixed value."
            config["CameraVerticalOffset"] = CameraVerticalOffset 
        config["Camera_solid_background"] = Camera_solid_background

        # Create intervals for Material properties 
        if same_material!=None:
            assert type(same_material)==bool, "Has to be bool or None. same_material sets the bool of same_material in getRandomJsonData. If it is None bool is set randomly." 
            if specify_material:
                if same_material:
                    assert type(r)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                    assert type(g)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                    assert type(b)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                    assert type(a)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                    assert type(metallic)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                    assert type(smoothness)in [float, int], "specify_material and same_material is true, material prpoertie has to be a float."
                else:
                    assert type(r)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(r)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert type(g)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(g)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert type(b)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(b)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert type(a)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(a)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert type(metallic)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(metallic)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert type(smoothness)==list, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
                    assert len(smoothness)==total_cuboids, "specify_material is true and same_material is false: material properie hast to be a list of lenght total_cuboids."
        else:
            assert specify_material==False, "you can not specify the material when same_material is None." 
            assert len(r) == 2, "r[0] is minimal limit and r[1] is maximal limit for random generation of the cuboidscolor r (red)"
            assert len(g) == 2, "g[0] is minimal limit and g[1] is maximal limit for random generation of the cuboidscolor g"
            assert len(b) == 2, "b[0] is minimal limit and b[1] is maximal limit for random generation of the cuboidscolor b"
            #assert len(a) == 2, "a[0] is minimal limit and a[1] is maximal limit for random generation of the cuboidscolor a (alpha/transparency)"
            assert len(metallic) == 2, "metallic[0] is minimal limit and metallic[1] is maximal limit for random generation of the cuboidsmaterial property metallic"
            assert len(smoothness) == 2, "smoothness[0] is minimal limit and smoothness[1] is maximal limit for random generation of the cuboidsmaterial property smoothness"

        config["specify_material"] = specify_material
        config["r"]=r
        config["g"]=g
        config["b"]=b
        config["a"]=a
        config["metallic"]=metallic
        config["smoothness"]=smoothness
        config["same_material"] = same_material

        # Create intervals for DirectionalLight
        if DirectionalLightTheta==None or DirectionalLightIntensity==None:
            config["DirectionalLightTheta"] = None
            config["DirectionalLightIntensity"] = None
        else:
            if type(DirectionalLightTheta)==list:
                assert len(DirectionalLightTheta) == 2, "DirectionalLightTheta has to be a float or a list with DirectionalLightTheta[0] is minimal limit and DirectionalLightTheta[1] is maximal limit for random generation of DirectionalLightTheta."
            else:
                assert type(DirectionalLightTheta)in [float, int], "DirectionalLightTheta has to be a float or a list with DirectionalLightTheta[0] is minimal limit and DirectionalLightTheta[1] is maximal limit for random generation of DirectionalLightTheta."
            config["DirectionalLightTheta"] = DirectionalLightTheta
            if type(DirectionalLightIntensity)==list:
                assert len(DirectionalLightIntensity) == 2, "DirectionalLightIntensity has to be a float or a list with DirectionalLightIntensity[0] is minimal limit and DirectionalLightIntensity[1] is maximal limit for random generation of DirectionalLightIntensity."
            else:
                assert type(DirectionalLightIntensity)in [float, int], "DirectionalLightIntensity has to be a float or a list with DirectionalLightIntensity[0] is minimal limit and DirectionalLightIntensity[1] is maximal limit for random generation of DirectionalLightIntensity."
            config["DirectionalLightIntensity"] = DirectionalLightIntensity

        # Create intervals for PointLights
        if totalPointLights == None:
            config["totalPointLights"]=totalPointLights
        else:
            assert len(totalPointLights) == 2, "totalPointLights is not None which would mean no PointLights. totalPointLights[0] is minimal limit and totalPointLights[1] is maximal limit for random generation of totalPointLights."
            config["totalPointLights"]=totalPointLights
            assert len(PointLightsRadius) == 2, "PointLightsRadius[0] is minimal limit and PointLightsRadius[1] is maximal limit for random generation of PointLightsRadius."
            config["PointLightsRadius"]=PointLightsRadius
            assert len(PointLightsPhi) == 2, "PointLightsPhi[0] is minimal limit and PointLightsPhi[1] is maximal limit for random generation of PointLightsPhi."
            config["PointLightsPhi"]=PointLightsPhi
            assert len(PointLightsTheta) == 2, "PointLightsTheta[0] is minimal limit and PointLightsTheta[1] is maximal limit for random generation of PointLightsTheta."
            config["PointLightsTheta"]=PointLightsTheta
            assert len(PointLightsIntensity) == 2, "PointLightsIntensity[0] is minimal limit and PointLightsIntensity[1] is maximal limit for random generation of PointLightsIntensity."
            config["PointLightsIntensity"]=PointLightsIntensity
            assert len(PointLightsRange) == 2, "PointLightsRange[0] is minimal limit and PointLightsRange[1] is maximal limit for random generation of PointLightsRange."
            config["PointLightsRange"]=PointLightsRange
            if same_PointLightsColor!=None:
                assert type(same_PointLightsColor)==bool, "Has to be bool or none. same_PointLightsColor sets the bool of same_PointLightsColor in getRandomJsonData. If its None bool is set randomly." 
            config["same_PointLightsColor"]=same_PointLightsColor
            assert len(PointLightsColor_r) == 2, "PointLightsColor_r[0] is minimal limit and PointLightsColor_r[1] is maximal limit for random generation of PointLightsColor_r."
            config["PointLightsColor_r"]=PointLightsColor_r
            assert len(PointLightsColor_g) == 2, "PointLightsColor_g[0] is minimal limit and PointLightsColor_g[1] is maximal limit for random generation of PointLightsColor_g."
            config["PointLightsColor_g"]=PointLightsColor_g
            assert len(PointLightsColor_b) == 2, "PointLightsColor_b[0] is minimal limit and PointLightsColor_b[1] is maximal limit for random generation of PointLightsColor_b."
            config["PointLightsColor_b"]=PointLightsColor_b
            assert len(PointLightsColor_a) == 2, "PointLightsColor_a[0] is minimal limit and PointLightsColor_a[1] is maximal limit for random generation of PointLightsColor_a."
            config["PointLightsColor_a"]=PointLightsColor_a
            
        # Create intervals for SpotLights
        if totalSpotLights == None:
            config["totalSpotLights"]=totalSpotLights
        else:
            assert len(totalSpotLights) == 2, "totalSpotLights is not None which would mean no SpotLights. totalSpotLights[0] is minimal limit and totalSpotLights[1] is maximal limit for random generation of totalSpotLights."
            config["totalSpotLights"]=totalSpotLights
            assert len(SpotLightsRadius) == 2, "SpotLightsRadius[0] is minimal limit and SpotLightsRadius[1] is maximal limit for random generation of SpotLightsRadius."
            config["SpotLightsRadius"]=SpotLightsRadius
            assert len(SpotLightsPhi) == 2, "SpotLightsPhi[0] is minimal limit and SpotLightsPhi[1] is maximal limit for random generation of SpotLightsPhi."
            config["SpotLightsPhi"]=SpotLightsPhi
            assert len(SpotLightsTheta) == 2, "SpotLightsTheta[0] is minimal limit and SpotLightsTheta[1] is maximal limit for random generation of SpotLightsTheta."
            config["SpotLightsTheta"]=SpotLightsTheta
            assert len(SpotLightsIntensity) == 2, "SpotLightsIntensity[0] is minimal limit and SpotLightsIntensity[1] is maximal limit for random generation of SpotLightsIntensity."
            config["SpotLightsIntensity"]=SpotLightsIntensity
            assert len(SpotLightsRange) == 2, "SpotLightsRange[0] is minimal limit and SpotLightsRange[1] is maximal limit for random generation of SpotLightsRange."
            config["SpotLightsRange"]=SpotLightsRange
            assert len(SpotAngle) == 2, "SpotAngle[0] is minimal limit and SpotAngle[1] is maximal limit for random generation of SpotAngle."
            config["SpotAngle"]=SpotAngle
            if same_SpotLightsColor!=None:
                assert type(same_SpotLightsColor)==bool, "Has to be bool or None. same_SpotLightsColor sets the bool of same_SpotLightsColor in getRandomJsonData. If its None bool is set randomly." 
            config["same_SpotLightsColor"]=same_SpotLightsColor
            assert len(SpotLightsColor_r) == 2, "SpotLightsColor_r[0] is minimal limit and SpotLightsColor_r[1] is maximal limit for random generation of SpotLightsColor_r."
            config["SpotLightsColor_r"]=SpotLightsColor_r
            assert len(SpotLightsColor_g) == 2, "SpotLightsColor_g[0] is minimal limit and SpotLightsColor_g[1] is maximal limit for random generation of SpotLightsColor_g."
            config["SpotLightsColor_g"]=SpotLightsColor_g
            assert len(SpotLightsColor_b) == 2, "SpotLightsColor_b[0] is minimal limit and SpotLightsColor_b[1] is maximal limit for random generation of SpotLightsColor_b."
            config["SpotLightsColor_b"]=SpotLightsColor_b
            assert len(SpotLightsColor_a) == 2, "SpotLightsColor_a[0] is minimal limit and SpotLightsColor_a[1] is maximal limit for random generation of SpotLightsColor_a."
            config["SpotLightsColor_a"]=SpotLightsColor_a
        if request_three == True and request_pose == True:
            assert 1==0, "request_three and request_pose can currently not be true at the same time." 
        config["request_pose"] = request_pose
        config["request_three"] = request_three

        config["seed"] = np.random.randint(np.iinfo(np.int32).max)
        np.random.seed(config["seed"])
        self.logger.debug("Config Seed: " + str(config["seed"]))
        self.config = config
        
        # Save the config for a dataset
        if save_config:
            if not os.path.exists(self.data_directory + "/config"):
                os.makedirs(self.data_directory + "/config")
            conf_path = self.data_directory + "/config/" + str(time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())) + '_config.json'
            i=0
            while os.path.exists(conf_path):
                i+=1
                conf_path = self.data_directory + "/config/" + str(time.strftime("%Y-%m-%d_%H:%M:%S", time.gmtime())) + '_config(' + str(i) + ').json'
            with open(conf_path, 'w') as f:
                json.dump(config,f)
                f.close()

    def load_config(self, index_config=0, file_name=None):
        """This enables you to load an old config to replicate a dataset.
        
        :param index_config: This will give you the latest config if set to zero, if set to one it will set the the second latest config and so on, defaults to ``0``
        :type index_config: int, optional
        :param file_name: This specifies the file name. If this is not default the specified file will be loaded, defaults to ``None``
        :type file_name: string or None, optional
        """        
        if file_name!=None:
            assert type(file_name)==str , "The file_name of the loading config has to be a string"
            if file_name[-5:] != ".json":
                file_name += ".json"
            try:
                with open(self.data_directory + "/config/" + file_name) as f:    
                    self.config = json.load(f)
                    f.close()
            except FileNotFoundError:
                self.logger.debug("this config could not be loaded:" + self.data_directory + "/config/" + file_name + ";  check for spelling mistakes for file_name: " + file_name + ", or if the file is in the right directory: " + self.data_directory + "/config/")
        else:
            files = os.listdir(self.data_directory + "/config/")
            paths = [os.path.join(self.data_directory + "/config/", basename) for basename in files]
            for i in range(1+index_config):
                final = max(paths, key=os.path.getctime)
                paths.remove(final)
            try:
                with open(final) as f:    
                    self.config = json.load(f)
                    f.close()
            except FileNotFoundError:
                self.logger.debug("config could not be loaded:" + final + ";  check that index_config is smaller than the amount of all config files -1; or if the file is in the right directory: " + self.data_directory + "/config/")
        
        np.random.seed(self.config["seed"])
    
    def create_random_parameters(self):
        """Creates random input parameters depending on your config which defines the interval for the generated parameters, the camera parameters are not set randomly
    
        :param CameraRes_width: Image resolution width, defaults to 520
        :type CameraRes_width: int, optional
        :param CameraRes_height: Image resolution height, defaults to 520
        :type CameraRes_height: int, optional
        :return: A dictionary to use as input for function :meth:`~dataset.dataset_cuboids.create_json_string_from_parameters`.
        :rtype: dictionary
        """
        dictionary={}

        # not random set variables for the Camera
        dictionary["CameraRes_width"] = self.config["CameraRes_width"] 
        dictionary["CameraRes_height"] = self.config["CameraRes_height"] 
        dictionary["Camera_FieldofView"] = self.config["Camera_FieldofView"]
        
        dictionary["request_pose"] = self.config["request_pose"]
        # Create all parameters randomly 
        
        # Camera position
        if type(self.config["CameraRadius"]) in [float, int]:
            dictionary["CameraRadius"] = self.config["CameraRadius"]
        else:
            dictionary["CameraRadius"] = np.random.uniform(self.config["CameraRadius"][0],self.config["CameraRadius"][1])
        if type(self.config["CameraTheta"]) in [float, int]:
            dictionary["CameraTheta"] = self.config["CameraTheta"]
        else:
            dictionary["CameraTheta"] = np.random.uniform(self.config["CameraTheta"][0],self.config["CameraTheta"][1])
        
        if type(self.config["CameraPhi"]) in [float, int]:
            dictionary["CameraPhi"] = self.config["CameraPhi"] 
        else:
            dictionary["CameraPhi"] = np.random.uniform(self.config["CameraPhi"][0],self.config["CameraPhi"][1])
        if type(self.config["CameraVerticalOffset"]) in [float, int]:
            dictionary["CameraVerticalOffset"] = self.config["CameraVerticalOffset"] 
        else:
            dictionary["CameraVerticalOffset"] = np.random.uniform(self.config["CameraVerticalOffset"][0],self.config["CameraVerticalOffset"][1])
        dictionary["Camera_solid_background"] = self.config["Camera_solid_background"]
        
        # Create how many Cubiods are in one branch.
        if type(self.config["total_cuboids"])==int:
            total_cuboids = self.config["total_cuboids"]
        else:
            total_cuboids = np.random.randint(self.config["total_cuboids"][0],self.config["total_cuboids"][1])
        # Create the angle and the intsaveensity of the directional light
        if self.config["DirectionalLightIntensity"] == None:
            DirectionalLightIntensity = 0   
            DirectionalLightTheta = 0
        else:
            if type(self.config["DirectionalLightIntensity"])==list:        
                DirectionalLightIntensity = np.random.uniform(self.config["DirectionalLightIntensity"][0], self.config["DirectionalLightIntensity"][1])
            else:
                DirectionalLightIntensity = self.config["DirectionalLightIntensity"]
            if type(self.config["DirectionalLightTheta"]) ==list:
                DirectionalLightTheta = np.random.uniform(self.config["DirectionalLightTheta"][0], self.config["DirectionalLightTheta"][1])
            else:
                DirectionalLightTheta = self.config["DirectionalLightTheta"]
            
        # Create all properties of the point lights
        PointLightRadius = []
        PointLightPhi = []
        PointLightTheta = []
        PointLightIntensity=[]
        PointLightRange = []
        P_R=[]
        P_G=[]
        P_B=[]
        P_A=[]
        # Amount of Pointlights
        if self.config["totalPointLights"] == None:
            TotalPointLights = 0
        else:        
            TotalPointLights = np.random.randint(self.config["totalPointLights"][0],self.config["totalPointLights"][1])
            # If all Pointlights should have the same color
            if(self.config["same_PointLightsColor"]==None):
                Same_PLcolor = bool(np.random.randint(2,dtype=int))
            else:
                Same_PLcolor = self.config["same_PointLightsColor"]
            # Create color for Pointlights
            if(Same_PLcolor):
                    pr=np.random.uniform(self.config["PointLightsColor_r"][0],self.config["PointLightsColor_r"][1])
                    pg=np.random.uniform(self.config["PointLightsColor_g"][0],self.config["PointLightsColor_g"][1])
                    pb=np.random.uniform(self.config["PointLightsColor_b"][0],self.config["PointLightsColor_b"][1])
                    pa=np.random.uniform(self.config["PointLightsColor_a"][0],self.config["PointLightsColor_a"][1])
                    for i in range(TotalPointLights):
                        P_R.append(pr)
                        P_G.append(pg)
                        P_B.append(pb)
                        P_A.append(pa)

            else:
                P_R=np.random.uniform(self.config["PointLightsColor_r"][0],self.config["PointLightsColor_r"][1],TotalPointLights).tolist()
                P_G=np.random.uniform(self.config["PointLightsColor_g"][0],self.config["PointLightsColor_g"][1],TotalPointLights).tolist()
                P_B=np.random.uniform(self.config["PointLightsColor_b"][0],self.config["PointLightsColor_b"][1],TotalPointLights).tolist()
                P_A=np.random.uniform(self.config["PointLightsColor_a"][0],self.config["PointLightsColor_a"][1],TotalPointLights).tolist()
            # Create spherical coordinate position for all Pointlights
            PointLightRadius=np.random.uniform(self.config["PointLightsRadius"][0],self.config["PointLightsRadius"][1],TotalPointLights).tolist()
            PointLightRange=np.random.uniform(self.config["PointLightsRange"][0],self.config["PointLightsRange"][1],TotalPointLights).tolist()
            PointLightPhi=np.random.uniform(self.config["PointLightsPhi"][0],self.config["PointLightsPhi"][1],TotalPointLights).tolist()
            PointLightTheta=np.random.uniform(self.config["PointLightsTheta"][0],self.config["PointLightsTheta"][1],TotalPointLights).tolist()
            PointLightIntensity=np.random.uniform(self.config["PointLightsIntensity"][0],self.config["PointLightsIntensity"][1],TotalPointLights).tolist()
        
        # Create all properties of the Spotlights        
        SpotLightRadius = []
        SpotLightPhi = []
        SpotLightTheta = []
        SpotLightIntensity=[]
        SpotLightRange = []
        SpotAngle = []
        S_R=[]
        S_G=[]
        S_B=[]
        S_A=[]
        # Amount of Spotlights
        if self.config["totalSpotLights"] == None:
            TotalSpotLights = 0
        else:        
            TotalSpotLights = np.random.randint(self.config["totalSpotLights"][0],self.config["totalSpotLights"][1])
            # If all Spotlights should have the same color
            if(self.config["same_SpotLightsColor"]==None):
                Same_SLcolor = bool(np.random.randint(2))
            else:
                Same_SLcolor = self.config["same_SpotLightsColor"]
            # Create color for Spotlights
            if(Same_SLcolor):
                sr=np.random.uniform(self.config["SpotLightsColor_r"][0],self.config["SpotLightsColor_r"][1])
                sg=np.random.uniform(self.config["SpotLightsColor_g"][0],self.config["SpotLightsColor_g"][1])
                sb=np.random.uniform(self.config["SpotLightsColor_b"][0],self.config["SpotLightsColor_b"][1])
                sa=np.random.uniform(self.config["SpotLightsColor_a"][0],self.config["SpotLightsColor_a"][1])
                for i in range(TotalSpotLights):
                    S_R.append(sr)
                    S_G.append(sg)
                    S_B.append(sb)
                    S_A.append(sa)
            else:
                S_R= np.random.uniform(self.config["SpotLightsColor_r"][0],self.config["SpotLightsColor_r"][1],TotalSpotLights).tolist()
                S_G=np.random.uniform(self.config["SpotLightsColor_g"][0],self.config["SpotLightsColor_g"][1],TotalSpotLights).tolist()
                S_B=np.random.uniform(self.config["SpotLightsColor_b"][0],self.config["SpotLightsColor_b"][1],TotalSpotLights).tolist()
                S_A=np.random.uniform(self.config["SpotLightsColor_a"][0],self.config["SpotLightsColor_a"][1],TotalSpotLights).tolist()
            # Create the positition of Spotlights
            SpotLightRadius=np.random.uniform(self.config["SpotLightsRadius"][0],self.config["SpotLightsRadius"][1],TotalSpotLights).tolist()
            SpotLightPhi=np.random.uniform(self.config["SpotLightsPhi"][0],self.config["SpotLightsPhi"][1],TotalSpotLights).tolist()
            SpotLightTheta=np.random.uniform(self.config["SpotLightsTheta"][0],self.config["SpotLightsTheta"][1],TotalSpotLights).tolist()
            # Create specific properties of the Spotlights 
            SpotLightIntensity=np.random.uniform(self.config["SpotLightsIntensity"][0],self.config["SpotLightsIntensity"][1],TotalSpotLights).tolist()
            SpotLightRange=np.random.uniform(self.config["SpotLightsRange"][0],self.config["SpotLightsRange"][1],TotalSpotLights).tolist()
            # The Angle specifies the "spread" of the lightcone created by the Spotlight
            SpotAngle=np.random.uniform(self.config["SpotAngle"][0],self.config["SpotAngle"][1],TotalSpotLights).tolist()
        
        # Amount of branches (Arms) and at which cubiod to branch. The first element of the list total_branchess counts the amount of branches at the first cubiod and and so on...
        # if total_branches = [1,1,1,1,1] then there is only one "main" Branch and no splits  
        total_branches = []
        if self.config["branches"]==None:
            total_branches = None
        else:
            if self.config["specify_branches"]:
                total_branches = self.config["branches"] 
            else:
                if self.config["branches"][0] > 1:
                    self.logger.info("config['branches'][0] is bigger than 1. This means you create at every segment new arms. Change the dataset config if you do not want this.")
                # the upper limit for the arms is dicribing the three sigma variance of the guassion normal distribution
                arms = np.random.normal(0,(self.config["branches"][1] - self.config["branches"][0])/3, total_cuboids-1)  
                arms = np.absolute(arms) + self.config["branches"][0] 
                for i in range(total_cuboids-1):
                    if arms[i]<=1 :
                        total_branches.append(1)
                    else:
                        total_branches.append(int(arms[i]))
            self.logger.debug("total_branches: "+str(total_branches)) 
        
        # Decide if there should be only one theta angle for cubiods
        if(self.config["same_theta"]==None):
            Same_Theta = bool(np.random.randint(2))
        else:
            Same_Theta = self.config["same_theta"]
        
        # Theta describes the angel between two cubiods next to each other
        Theta = []
        if(Same_Theta):
            if self.config["theta"]==None:
                Theta.append(np.random.uniform(0,360/total_cuboids))
            elif type(self.config["theta"])==list:
                assert len(self.config["theta"]) == 2, "self.config['theta'] is a list and Same_theta = True which means it has to be of length two or a float."
                Theta.append(np.random.uniform(self.config["theta"][0],self.config["theta"][1]))
            elif type(self.config["theta"])in [float, int]:
                Theta.append(self.config["theta"])
            else:
                self.logger.error("Bad input parameters in self.config['theta'] in combination with self.config['same_theta'].") 

        else:
            if self.config["theta"]==None:
                Theta=np.random.uniform(0,360/total_cuboids,total_cuboids-1).tolist()
            elif type(self.config["theta"])==list:
                if self.config["specify_theta"]:
                    Theta = self.config["theta"]
                else:
                    Theta=np.random.uniform(self.config["theta"][0],self.config["theta"][1],total_cuboids-1).tolist()    
            else:
                self.logger.error("Bad input parameters in self.config['theta'] in combination with self.config['same_theta'].") 
        
        # Decide if all cubiods use the same Material
        if(self.config["same_material"]==None):
            Same_Material = bool(np.random.randint(2))
        else:
            Same_Material = self.config["same_material"]
        R=[]
        G=[]
        B=[]
        A=[]
        Metallic=[]
        Smoothness=[]
        # Create the colors of the cubiods and the material property smoothness and metallic 
        if self.config["specify_material"]:
            R=self.config["r"]
            G=self.config["g"]
            B=self.config["b"]
            A=self.config["a"]
            Metallic=self.config["metallic"]
            Smoothness=self.config["smoothness"]
        else:   
            if(Same_Material):
                R=np.random.uniform(self.config["r"][0],self.config["r"][1])
                G=np.random.uniform(self.config["g"][0],self.config["g"][1])
                B=np.random.uniform(self.config["b"][0],self.config["b"][1])
                if type(self.config["a"]) in [int,float]:
                    A=self.config["a"]
                else:
                    A=np.random.uniform(self.config["a"][0],self.config["a"][1])
                Metallic=np.random.uniform(self.config["metallic"][0],self.config["metallic"][1])
                Smoothness=np.random.uniform(self.config["smoothness"][0],self.config["smoothness"][1])
                
            else:
                R=np.random.uniform(self.config["r"][0],self.config["r"][1],total_cuboids).tolist()
                G=np.random.uniform(self.config["g"][0],self.config["g"][1],total_cuboids).tolist()
                B=np.random.uniform(self.config["b"][0],self.config["b"][1],total_cuboids).tolist()
                if type(self.config["a"]) in [int,float]:
                    for i in range(total_cuboids):
                        A.append(self.config["a"])
                else:
                    A=np.random.uniform(self.config["a"][0],self.config["a"][1],total_cuboids).tolist()
                Metallic=np.random.uniform(self.config["metallic"][0],self.config["metallic"][1],total_cuboids).tolist()
                Smoothness=np.random.uniform(self.config["smoothness"][0],self.config["smoothness"][1],total_cuboids).tolist()
        # Decide if all cubiods should have the same vertical scale
        if(self.config["same_scale"]==None):
            Same_Scale = bool(np.random.randint(2))
        else:
            Same_Scale = self.config["same_scale"]
        # Create Scale
        if(Same_Scale):
            if type(self.config["scale"])==list:
                Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1])
            else:
                Scale = self.config["scale"] 
        else:
            if self.config["specify_scale"]:
                Scale = self.config["scale"]
            else:
                Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1],total_cuboids).tolist()

        # Create Phi the rotation of the crane
        if type(self.config["phi"])in [float, int]:
            Phi = self.config["phi"]
        else:
            Phi=np.random.uniform(self.config["phi"][0],self.config["phi"][1])
        
        # Add all parameters to a dictionary
        dictionary["total_cuboids"] = total_cuboids
        dictionary["scale"] = Scale
        dictionary["same_scale"] = Same_Scale
        dictionary["total_branches"] = total_branches
        dictionary["same_theta"] = Same_Theta
        dictionary["theta"] = Theta
        dictionary["phi"] = Phi
        dictionary["same_material"] = Same_Material
        dictionary["r"] = R
        dictionary["g"] = G
        dictionary["b"] = B
        dictionary["a"] = A
        dictionary["metallic"] = Metallic
        dictionary["smoothness"] = Smoothness
        
        dictionary["DirectionalLightTheta"] = DirectionalLightTheta
        dictionary["DirectionalLightIntensity"] = DirectionalLightIntensity

        if TotalPointLights == 0:
            dictionary["totalPointLights"] = TotalPointLights 
            dictionary["PointLightsRadius"] = None
            dictionary["PointLightsPhi"] = None
            dictionary["PointLightsTheta"] = None
            dictionary["PointLightsIntensity"] = None
            dictionary["PointLightsRange"] = None
            dictionary["PointLightsColor_r"] = None
            dictionary["PointLightsColor_g"] = None
            dictionary["PointLightsColor_b"] = None
            dictionary["PointLightsColor_a"] = None
            dictionary["same_PointLightsColor"] = None
        else:
            dictionary["totalPointLights"] = TotalPointLights    
            dictionary["PointLightsRadius"] = PointLightRadius
            dictionary["PointLightsPhi"] = PointLightPhi
            dictionary["PointLightsTheta"] = PointLightTheta
            dictionary["PointLightsIntensity"] = PointLightIntensity
            dictionary["PointLightsRange"] = PointLightRange
            dictionary["PointLightsColor_r"] = P_R
            dictionary["PointLightsColor_g"] = P_G
            dictionary["PointLightsColor_b"] = P_B
            dictionary["PointLightsColor_a"] = P_A
            dictionary["same_PointLightsColor"] = Same_PLcolor
        
        if TotalSpotLights == 0:    
            dictionary["totalSpotLights"] = TotalSpotLights
            dictionary["SpotLightsRadius"] = None
            dictionary["SpotLightsPhi"] = None
            dictionary["SpotLightsTheta"] = None
            dictionary["SpotLightsIntensity"] = None
            dictionary["SpotLightsRange"] = None
            dictionary["SpotLightsColor_r"] = None
            dictionary["SpotLightsColor_g"] = None
            dictionary["SpotLightsColor_b"] = None
            dictionary["SpotLightsColor_a"] = None
            dictionary["same_SpotLightsColor"] = None
            dictionary["SpotLightsRange"] = None
            dictionary["SpotAngle"] = None
        else:
            dictionary["totalSpotLights"] = TotalSpotLights
            dictionary["SpotLightsRadius"] = SpotLightRadius
            dictionary["SpotLightsPhi"] = SpotLightPhi
            dictionary["SpotLightsTheta"] = SpotLightTheta
            dictionary["SpotLightsIntensity"] = SpotLightIntensity
            dictionary["SpotLightsRange"] = SpotLightRange
            dictionary["SpotLightsColor_r"] = S_R
            dictionary["SpotLightsColor_g"] = S_G
            dictionary["SpotLightsColor_b"] = S_B
            dictionary["SpotLightsColor_a"] = S_A
            dictionary["same_SpotLightsColor"] = Same_SLcolor
            dictionary["SpotLightsRange"] = SpotLightRange
            dictionary["SpotAngle"] = SpotAngle
        
        return dictionary
    
    def create_parameters(self, same_scale=True, scale=2, total_cuboids=5, phi=90, total_branches=[1,2,1,4], same_theta=True, theta=20, 
    same_material=True, r=1, g=0.1, b=0.2, a=1, metallic=1, smoothness=0.5, CameraRes_width= 1024, CameraRes_height=1024, Camera_FieldofView=100, CameraRadius = 10.0, CameraTheta = 90, CameraPhi = 0, CameraVerticalOffset = 0, Camera_solid_background = False,
    totalPointLights=2, PointLightsRadius=[5,6], PointLightsPhi=[0,95], PointLightsTheta=[45,60], PointLightsIntensity=[10,12], PointLightsRange=[10,10], same_PointLightsColor=True, PointLightsColor_r=1, PointLightsColor_g=1, PointLightsColor_b=1, PointLightsColor_a=1,
    totalSpotLights=None, SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotAngle=[5,120], same_SpotLightsColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
    DirectionalLightTheta = 60, DirectionalLightIntensity = 3):
        dictionary = {}
        dictionary["total_cuboids"] =total_cuboids 
        dictionary["same_scale"] = same_scale
        dictionary["scale"] = scale
        dictionary["same_theta"] = same_theta
        dictionary["theta"] = theta
        dictionary["phi"] = phi
        dictionary["total_branches"] = total_branches
        dictionary["same_material"] = same_material
        dictionary["metallic"] = metallic
        dictionary["smoothness"] = smoothness
        dictionary["r"] = r
        dictionary["g"] = g
        dictionary["b"] = b
        dictionary["a"] = a
        dictionary["CameraRes_width"] = CameraRes_width
        dictionary["CameraRes_height"] = CameraRes_height
        dictionary["Camera_FieldofView"] = Camera_FieldofView
        dictionary["CameraRadius"] = CameraRadius
        dictionary["CameraTheta"] = CameraTheta
        dictionary["CameraPhi"] = CameraPhi
        dictionary["CameraVerticalOffset"] = CameraVerticalOffset 
        dictionary["Camera_solid_background"] = Camera_solid_background
        if totalPointLights in [0,None]:
            dictionary["totalPointLights"] = 0 
            dictionary["PointLightsRadius"] = None
            dictionary["PointLightsPhi"] = None
            dictionary["PointLightsTheta"] = None
            dictionary["PointLightsIntensity"] = None
            dictionary["PointLightsRange"] = None
            dictionary["PointLightsColor_r"] = None
            dictionary["PointLightsColor_g"] = None
            dictionary["PointLightsColor_b"] = None
            dictionary["PointLightsColor_a"] = None
            dictionary["same_PointLightsColor"] = None
        else:
            dictionary["totalPointLights"] = totalPointLights
            dictionary["same_PointLightsColor"] = same_PointLightsColor
            dictionary["PointLightsColor_r"] = PointLightsColor_r
            dictionary["PointLightsColor_g"] = PointLightsColor_g
            dictionary["PointLightsColor_b"] = PointLightsColor_b
            dictionary["PointLightsColor_a"] = PointLightsColor_a
            dictionary["PointLightsRadius"] = PointLightsRadius
            dictionary["PointLightsTheta"] = PointLightsTheta
            dictionary["PointLightsPhi"] = PointLightsPhi
            dictionary["PointLightsIntensity"] = PointLightsIntensity
            dictionary["PointLightsRange"] = PointLightsRange
        if totalSpotLights in [0,None]:    
            dictionary["totalSpotLights"] = 0
            dictionary["SpotLightsRadius"] = None
            dictionary["SpotLightsPhi"] = None
            dictionary["SpotLightsTheta"] = None
            dictionary["SpotLightsIntensity"] = None
            dictionary["SpotLightsRange"] = None
            dictionary["SpotLightsColor_r"] = None
            dictionary["SpotLightsColor_g"] = None
            dictionary["SpotLightsColor_b"] = None
            dictionary["SpotLightsColor_a"] = None
            dictionary["same_SpotLightsColor"] = None
            dictionary["SpotLightsRange"] = None
            dictionary["SpotAngle"] = None
        else:
            dictionary["totalSpotLights"] = totalSpotLights
            dictionary["same_SpotLightsColor"] = same_SpotLightsColor
            dictionary["SpotLightsColor_r"] = SpotLightsColor_r
            dictionary["SpotLightsColor_g"] = SpotLightsColor_g
            dictionary["SpotLightsColor_b"] = SpotLightsColor_b
            dictionary["SpotLightsColor_a"] = SpotLightsColor_a
            dictionary["SpotLightsRadius"] = SpotLightsRadius
            dictionary["SpotLightsTheta"] = SpotLightsTheta 
            dictionary["SpotLightsPhi"] = SpotLightsPhi
            dictionary["SpotLightsIntensity"] = SpotLightsIntensity
            dictionary["SpotLightsRange"] = SpotLightsRange
            dictionary["SpotAngle"] = SpotAngle
            
        dictionary["DirectionalLightTheta"] = DirectionalLightTheta 
        dictionary["DirectionalLightIntensity"] = DirectionalLightIntensity

        return dictionary 

    def create_json_string_from_parameters(self, dictionary):
        """
        Inputs the parameters/dictionary into the function :meth:`~client.client_communicator_to_unity.write_json_crane`.

        :param dictionary: A dictionary similar to one from :meth:`~dataset.dataset_cuboids.create_random_parameters` with all input parameters for the function :meth:`~client.client_communicator_to_unity.write_json_crane`.
        :type dictionary: dictionary
        :return: A string depending on your input parameters wich can be interpreted afterwards by the Unity script. 
        :rtype: string
        """

        return self.uc.write_json_crane(request_pose = dictionary["request_pose"], total_cuboids=dictionary["total_cuboids"], same_scale=dictionary["same_scale"], scale=dictionary["scale"], same_theta=dictionary["same_theta"], theta=dictionary["theta"], phi=dictionary["phi"], total_branches=dictionary["total_branches"], same_material=dictionary["same_material"], metallic=dictionary["metallic"], smoothness=dictionary["smoothness"], r=dictionary["r"], g=dictionary["g"], b=dictionary["b"], a=dictionary["a"], 
            CameraRes_width=dictionary["CameraRes_width"], CameraRes_height=dictionary["CameraRes_height"], Camera_FieldofView=dictionary["Camera_FieldofView"], CameraRadius=dictionary["CameraRadius"], CameraTheta=dictionary["CameraTheta"], CameraPhi=dictionary["CameraPhi"], CameraVerticalOffset=dictionary["CameraVerticalOffset"], Camera_solid_background=dictionary["Camera_solid_background"], 
            totalPointLights=dictionary["totalPointLights"], same_PointLightsColor=dictionary["same_PointLightsColor"], PointLightsColor_r=dictionary["PointLightsColor_r"], PointLightsColor_g=dictionary["PointLightsColor_g"], PointLightsColor_b=dictionary["PointLightsColor_b"], PointLightsColor_a=dictionary["PointLightsColor_a"], PointLightsRadius=dictionary["PointLightsRadius"], PointLightsTheta=dictionary["PointLightsTheta"], PointLightsPhi=dictionary["PointLightsPhi"], PointLightsIntensity=dictionary["PointLightsIntensity"], PointLightsRange=dictionary["PointLightsRange"], 
            totalSpotLights=dictionary["totalSpotLights"], same_SpotLightsColor=dictionary["same_SpotLightsColor"], SpotLightsColor_r=dictionary["SpotLightsColor_r"], SpotLightsColor_g=dictionary["SpotLightsColor_g"], SpotLightsColor_b=dictionary["SpotLightsColor_b"], SpotLightsColor_a=dictionary["SpotLightsColor_a"], SpotLightsRadius=dictionary["SpotLightsRadius"], SpotLightsTheta=dictionary["SpotLightsTheta"], SpotLightsPhi=dictionary["SpotLightsPhi"], SpotLightsIntensity=dictionary["SpotLightsIntensity"], SpotLightsRange=dictionary["SpotLightsRange"],SpotAngle=dictionary["SpotAngle"],
            DirectionalLightTheta=dictionary["DirectionalLightTheta"], DirectionalLightIntensity=dictionary["DirectionalLightIntensity"])

    def save(self, dictionary, save_image = False, save_para = None):
        """Save parameter data or/and an image of a dictionary in the ``data/parameters`` folder or the ``data/images`` folder. The saved parameters can be loaded with :meth:`~dataset.dataset_cuboids.load_parameters` and then manipulated to create an altered image.
        
        :param dictionary: A dictionary with keys as "index", "parameters" and if needed "image". For example a returned dictionary from :meth:`~dataset.dataset_cuboids.parameters_to_finished_data`.
        :type dictionary: dictionary
        :param save_para: If the parameters should be saved to ``data/parameters`` labeled with the index if available, if ``None`` and there is no seed save in the config, defaults to ``None``
        :type save_para: bool, optional
        :param save_image: If the image should be saved to ``data/images`` labeled with the index if available, defaults to ``False``
        :type save_image: bool, optional
        """ 
        # Save parameters.
        if save_para==None:
            if "seed" in self.config:
                self.logger.debug("key: 'seed' is found in config")
                save_para=False
            else:
                save_para=True
                self.logger.debug("key: 'seed' is not found in config")
        if save_para:
            # Check and if necessary create directory
            directory_para = self.data_directory + "/parameters"
            if not os.path.exists(directory_para):
                os.makedirs(directory_para)
            # Check if the parameters and the index is in the dictionary.
            if "parameters" in dictionary:
                if "index" in dictionary:
                    if "request_three" in self.config and self.config["request_three"]:
                        for i in range(3):
                            with open(directory_para + "/parameters_index_" + str(dictionary["index"]) + "_" + str(i) + '.json', 'w') as f:
                                json.dump(dictionary["parameters"][i],f)
                                f.close()
                    else:
                        with open(directory_para + "/parameters_index_" + str(dictionary["index"]) + '.json', 'w') as f:
                            json.dump(dictionary["parameters"],f)
                            f.close()
                else:
                    assert 1==0, "no index in dictionary"
                    '''
                    # Change the name of the json file if there is no index given.
                    fake_index = np.random.randint(0,1000)
                    with open(directory_para + "/parameters_NO_index_" + str(fake_index) + '.json', 'w') as f:
                        json.dump(dictionary["parameters"],f)
                        f.close()
                    '''
            else:
                self.logger.error("Image parameters could not be saved. No parameters found in dictionary.")
                assert 1==0, "no parameters in dictionary"
        # Save the image as png.
        if save_image:
            if "pose" in dictionary:   
                # Check and if necessary create directory
                directory_images = self.data_directory + "/images"
                directory_images_poses = self.data_directory + "/images_poses"
                if not os.path.exists(directory_images):
                    os.makedirs(directory_images)
                if not os.path.exists(directory_images_poses):
                    os.makedirs(directory_images_poses)
                # Check if the image and the index is in the dictionary.
                if "image" in dictionary:
                    if "index" in dictionary:
                        if "request_three" in self.config and self.config["request_three"]:
                            assert 1==0, "Pose images are not permitted with request_three images."
                        else:
                            Image.fromarray(dictionary["image"]).save(directory_images + "/image_index_" + str(dictionary["index"]) + '.png')
                            Image.fromarray(dictionary["pose"]).save(directory_images_poses + "/image_index_" + str(dictionary["index"]) + '.png')
                    else:
                        assert 1==0, "No index in dictionary."
                        '''
                        # Change the name of the image if there is no index given.
                        fake_index = np.random.randint(0,1000)
                        Image.fromarray(dictionary["image"]).save(directory_images + "/image_NO_index_" + str(fake_index) + '.png')
                        Image.fromarray(dictionary["pose"]).save(directory_images_poses + "/image_NO_index_" + str(fake_index) + '.png')
                        '''    
                else:
                    self.logger.error("Image could not be saved. No image data not found in dictionary.")
                    assert 1==0, "No index in dictionary."
            else:    
                # Check and if necessary create directory
                directory_images = self.data_directory + "/images"
                if not os.path.exists(directory_images):
                    os.makedirs(directory_images)
                # Check if the image and the index is in the dictionary.
                if "image" in dictionary:
                    if "index" in dictionary:
                        if "request_three" in self.config and self.config["request_three"]:
                            for i in range(3):
                                Image.fromarray(dictionary["image"][i]).save(directory_images + "/image_index_" + str(dictionary["index"]) + "_" + str(i) + '.png')
                        else:
                            Image.fromarray(dictionary["image"]).save(directory_images + "/image_index_" + str(dictionary["index"]) + '.png')
                    else:
                        assert 1==0, "No index in dictionary."
                        '''
                        # Change the name of the image if there is no index given.
                        fake_index = np.random.randint(0,1000)
                        Image.fromarray(dictionary["image"]).save(directory_images + "/image_NO_index_" + str(fake_index) + '.png')
                        '''
                else:
                    self.logger.error("Image could not be saved. No image data not found in dictionary.")
                    assert 1==0, "No image in dictionary."

    def load_parameters(self,index = [-1], amount = 1):
        """Load and return a given amount of parameters as dictionaries in a list. If index is not specified the index will be chosen randomly.
        
        :param index: If index is default it will be generated randomly else it has to be a list of integers the length of ``amount``, defaults to [-1]
        :type index: list, optional
        :param amount: The amount of dictionaries in the returned list, defaults to 1
        :type amount: int, optional
        :return: A list of parameters as dictionaries is returned except the amount is one or default the dictionary itself will be returned.
        :rtype: list or dictionary
        """        
        if index[0]==-1:
            index = np.random.randint(0,self.read_index(),amount)
        else:
            assert len(index)==amount, "Specified Index has to be len(Index):" + str(len(index)) + " equal to amount:" + str(amount)
        parameter_list = []
        # Load the amount of parameters and append them to the parameter_list
        for i in range(amount):
            while 1:
                try:
                    f = open(self.data_directory + "/parameters/parameters_index_" + str(index[i]) + ".json")
                    parameter_list.append(json.load(f))
                    f.close()
                    break
                except FileNotFoundError:
                    self.logger.debug("File with index" + str(index[i]) + "does not exist.")
                    index[i] +=1
        # If the amount is 1 then return the parameters directly 
        if amount==1:
            return parameter_list[0]
        # otherwise return the list of the parameters
        else:
            return parameter_list    
   
    def parameters_to_finished_data(self, parameters, save_image = True, save_para = None, return_dict = True):
        """Input parameters and get an corresponding image. 
        
        :param parameters: Parameters to use for :meth:`~dataset.dataset_cuboids.create_json_string_from_parameters`.
        :type parameters: dictionary
        :param save_para: If the parameters should be saved at ``data/parameters``, if ``None`` they will not be created if a seed is available in the config, defaults to None
        :type save_para: bool or None, optional
        :param save_image: If the image should be saved at ``data/images``, defaults to True
        :type save_image: bool, optional
        :return: A dictionary with all relevant data in keys as "index","parameters" and "image". 
        :rtype: dictionary
        """        
        # Format the parameters to a jsonstring that can be sent and interpreted by Unity.
        jsonstring = self.create_json_string_from_parameters(parameters)
        # Send unity the data to create the crane
        self.uc.send_to_unity(jsonstring)
        del jsonstring
        # receive an image depending on your parameters.
        img = self.uc.receive_image()
        # Load and increment the extern saved index.
        index = self.increment_index()
        # Put data in an dictionary.
        if self.config["request_pose"]:
            img_pose = self.uc.receive_image()    
            newDict = {"index":index,"parameters":parameters,"image":img,"pose":img_pose}
        else:
            newDict = {"index":index,"parameters":parameters,"image":img}
        self.logger.debug("data completed: Image index: " + str(index))
        # Save parameters for later recreating and manipulating the image.
        self.save(newDict, save_para = save_para, save_image = save_image)
        if return_dict:
            return newDict  
        else:
            newDict.clear()

    def three_parameters_to_finished_data(self, parameter_list, save_image = True, save_para = None, return_dict = True):
        """Input parameters and get an corresponding image. 
        
        :param parameters: Parameters to use for :meth:`~dataset.dataset_cuboids.create_json_string_from_parameters`.
        :type parameters: dictionary
        :param save_para: If the parameters should be saved at ``data/parameters``, if ``None`` they will not be created if a seed is available in the config, defaults to None
        :type save_para: bool or None, optional
        :param save_image: If the image should be saved at ``data/images``, defaults to True
        :type save_image: bool, optional
        :return: A dictionary with all relevant data in keys as "index","parameters" and "image". 
        :rtype: dictionary
        """
        img_list = []  
        img_pose_list = []      
        for i in range(3):
            # Format the parameters to a jsonstring that can be sent and interpreted by Unity.
            jsonstring = self.create_json_string_from_parameters(parameter_list[i])
            # Send unity the data to create the crane
            self.uc.send_to_unity(jsonstring)
            del jsonstring
            # receive an image depending on your parameters.
            img_list.append(self.uc.receive_image())

        # Load and increment the extern saved index.
        index = self.increment_index()
        # Put data in an dictionary.
        newDict = {"index":index,"parameters":parameter_list,"image":img_list}
        self.logger.info("data completed: Image index: " + str(index))
        # Save parameters for later recreating and manipulating the image.
        self.save(newDict, save_para = save_para, save_image = save_image)
        if return_dict:
            return newDict  
        else:
            newDict.clear()

    def get_example(self, save_image = False, save_para = None, return_dict = True, index = None):
        """Create an example of the dataset.
        
        :param save_para: If the parameters should be saved at ``data/parameters``, if set to ``None`` they will not be created if a seed is available in the config, defaults to None
        :type save_para: bool or None, optional
        :param save_image: If the image should be saved at ``data/images``, defaults to False
        :type save_image: bool, optional
        :param index: Shoukd be default. If specified the the new data will overwrite the old data at the given index if available, defaults to None
        :type index: None or int, optional
        :return: A dictionary with all relevant data in the keys "index", "parameter" and "image".
        :rtype: dictionary
        """        
        # Create random parameters depending o your config.  
        random_parameters = self.create_random_parameters()
        if "request_three" in self.config and self.config["request_three"]:
            random_parameters_1 = self.create_random_parameters()
            random_parameters_2 = self.change_app1_art2(random_parameters, random_parameters_1)
            if return_dict:
                newDict = self.three_parameters_to_finished_data(parameter_list = [random_parameters, random_parameters_1, random_parameters_2], save_para = save_para, save_image = save_image, return_dict = return_dict)
                random_parameters.clear()
                random_parameters_1.clear()
                random_parameters_2.clear()
                return newDict
            else:
                self.three_parameters_to_finished_data(parameter_list = [random_parameters, random_parameters_1, random_parameters_2], save_para = save_para, save_image = save_image, return_dict = return_dict)
                random_parameters.clear()
                random_parameters_1.clear()
                random_parameters_2.clear()
        else:
            # Get data with image in dictionary.
            if return_dict:
                newDict = self.parameters_to_finished_data(random_parameters, save_para = save_para, save_image = save_image, return_dict = return_dict)
                random_parameters.clear()
                return newDict
            else:
                self.parameters_to_finished_data(random_parameters, save_para = save_para, save_image = save_image, return_dict = return_dict)
                random_parameters.clear()

    def plot_images(self, dicts, images_per_row = 4, save_fig = True, show_index = True):
        """Plot and show all images contained in the list dicts of dictionaries and label them with their corresponding index.
        
        :param dicts: Has to be a list with dictionaries in which there is the key "image" and if wanted "index" as returned from :meth:`~dataset.dataset_cuboids.parameters_to_finished_data`
        :type dicts: list
        :param images_per_row: How many images are plotted in one row, defaults to 4
        :type images_per_row: int, optional
        :param save_fig: If the created plot of all images should be saved to ``data/figures``, defaults to True
        :type save_fig: bool, optional
        :param show_index: If the corresponding index of every image is shown in the plot, defaults to True
        :type show_index: bool, optional
        """
        # How many images are there
        numb = len(dicts)
        pose_av = all( "pose" in dicts[i] for i in range(numb))
        self.logger.debug("Pose image is available is " + str(pose_av))

        if numb < images_per_row:
            images_per_row = numb
        numb_y = 0
        numb_x = images_per_row
        # numb_y and numb_x determine the size of the grid of images
        while numb > numb_x:
            numb_y += 1
            numb -= images_per_row
        numb_y += 1
        
        if "request_three" in self.config and self.config["request_three"]:
            numb_x = len(dicts)
            numb_y = 3
            final_img = []
            for j in range(numb_x):
                v_img = []
                for i in range(numb_y):
                    v_img.append(dicts[j]["image"][i])
                final_img.append(np.vstack(v_img))
            final_img = np.flip(np.hstack(final_img),0)
        # Stack all images in one row together with np.hstack() for all numb_y
        elif pose_av:
            self.logger.debug("Pose gt is available and will be plotted.")
            h_stacked = np.zeros((numb_y*2, dicts[0]["image"].shape[0], (images_per_row*dicts[0]["image"].shape[1]), dicts[0]["image"].shape[2]), dtype=int)
            for i in range(numb_y):
                img_hstack = np.zeros((numb_x, dicts[0]["image"].shape[0], dicts[0]["image"].shape[1], dicts[0]["image"].shape[2]), dtype=int)
                pose_img_hstack = np.ones((numb_x, dicts[0]["image"].shape[0], dicts[0]["image"].shape[1], dicts[0]["image"].shape[2]), dtype=int)
                self.logger.debug("h_stacked.shape: " + str(h_stacked.shape))
                if i == numb_y-1:
                    for j in range(numb):
                        img_hstack[j] = dicts[i*numb_x+j]["image"]
                        pose_img_hstack[j] = dicts[i*numb_x+j]["pose"]
                else:    
                    for j in range(numb_x):
                        img_hstack[j] = dicts[i*numb_x+j]["image"]
                        pose_img_hstack[j] = dicts[i*numb_x+j]["pose"]
                h_stacked[i*2] = np.hstack((img_hstack))
                h_stacked[i*2+1] = np.hstack((pose_img_hstack))
            final_img = np.flip(np.vstack((h_stacked)),0)
        else: 
            self.logger.debug("numb_y: " + str(numb_y))
            self.logger.debug("dicts[0]['image'].shape[0]: " + str(dicts[0]["image"].shape[0]))
            self.logger.debug("(images_per_row*dicts[0][image].shape[1]: " + str((images_per_row*dicts[0]["image"].shape[1])))
            self.logger.debug("dicts[0][image].shape[2]: " + str(dicts[0]["image"].shape[2]))
            h_stacked = np.ones((numb_y, dicts[0]["image"].shape[0], (images_per_row*dicts[0]["image"].shape[1]), dicts[0]["image"].shape[2]), dtype=int)
            self.logger.debug("h_stacked.shape: " + str(h_stacked.shape))
            for i in range(numb_y):
                img_hstack = np.ones((numb_x, dicts[0]["image"].shape[0], dicts[0]["image"].shape[1], dicts[0]["image"].shape[2]), dtype=int)
                if i == numb_y-1:
                    for j in range(numb):
                        img_hstack[j] = dicts[i*numb_x+j]["image"]
                else:    
                    for j in range(numb_x):
                        img_hstack[j] = dicts[i*numb_x+j]["image"]
                h_stacked[i] = np.hstack((img_hstack))
            final_img = np.flip(np.vstack((h_stacked)),0)
        # Stack all rows vertically together
        matplotlib.use('TkAgg')
        self.logger.debug("final_img.shape: " + str(final_img.shape))
        plt.figure(figsize=(numb_x*2, numb_y*2))
        plt.imshow(final_img)
        if "request_three" in self.config and self.config["request_three"]:
            x_lab_pos = np.arange(dicts[0]["image"][0].shape[1]/2, dicts[0]["image"][0].shape[1]*numb_x, dicts[0]["image"][0].shape[1])
            x_lab = []
            y_lab_pos = np.arange(dicts[0]["image"][0].shape[1]/2, dicts[0]["image"][0].shape[1]*3, dicts[0]["image"][0].shape[1])
            y_lab = [r"$(\alpha_1, \pi_2)$",r"$(\alpha_2, \pi_2)$",r"$(\alpha_1, \pi_1)$"]
            for i in range(numb_x):
                x_lab.append(dicts[i]["index"])
            plt.xticks(x_lab_pos,x_lab)
            plt.yticks(y_lab_pos,y_lab)
            plt.xlabel("index of example")
            plt.xlim(0, dicts[0]["image"][0].shape[1]*numb_x)
            plt.ylim(0,dicts[0]["image"][0].shape[1]*3)
            for i in range(3):
                plt.axhline(y = dicts[0]["image"][0].shape[0]*i, color="k")
            for i in range(numb_x):
                plt.axvline(x = dicts[0]["image"][0].shape[0]*i, lw=2.5, color="k")
        else:
            plt.axis('off')
            # Plot lines between images to better see the borders of the images
            for i in range(1,numb_y):
                plt.axhline(y = dicts[0]["image"].shape[0]*i, color="k")
            for i in range(1,numb_x):
                plt.axvline(x = dicts[0]["image"].shape[1]*i, color="k")
            # Plot the index of the images onto the images
            if show_index:
                if pose_av:
                    j = numb_y+1
                    for i in range(0,len(dicts)):
                        l = 0
                        if "index" in dicts[i]:
                            if i%(numb_x)==0:
                                l += 1
                                j -= 1
                            plt.text(dicts[0]["image"].shape[1]*((i%numb_x) + 0.03), dicts[0]["image"].shape[0]*(j*2 - 0.15), "idx: " + str(dicts[i]["index"]))
                            plt.text(dicts[0]["image"].shape[1]*((i%numb_x) + 0.03), dicts[0]["image"].shape[0]*(j*2-1 - 0.15), "idx: " + str(dicts[i]["index"]))
                        else:
                            self.logger.error("dicts[" + str(i) + "] has no index.")
                else:
                    j = numb_y+1
                    for i in range(0,len(dicts)):
                        if "index" in dicts[i]:
                            if i%(numb_x)==0:
                                j -= 1
                            plt.text(dicts[0]["image"].shape[1]*((i%numb_x) + 0.03), dicts[0]["image"].shape[0]*(j - 0.1), "idx: " + str(dicts[i]["index"]) )
                        else:
                            self.logger.error("dicts[" + str(i) + "] has no index.")
            plt.xlim(0, (images_per_row)*dicts[0]["image"].shape[1])
            if pose_av:
                plt.ylim(0, (numb_y)*2*dicts[0]["image"].shape[0])
            else:
                plt.ylim(0, (numb_y)*dicts[0]["image"].shape[0])
        # Save figure if wanted.
        if save_fig:
            if not os.path.exists(self.data_directory + "/figures/"):
                os.makedirs(self.data_directory + "/figures/")
            plt.savefig(self.data_directory + "/figures/fig_from_index_" + str(dicts[0]["index"]) + "_to_index_" + str(dicts[len(dicts)-1]["index"]) + ".png", bbox_inches='tight')#, dpi= max([50 * numb_y, 50 * numb_x]))
        plt.show()

    def change_app1_art2(self, para1, para2):
        """Combines the appearence and the articulation of two different parameters.  
        
        :param para1: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type para1: dictionary
        :param para2: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type para2: dictionary
        :return: Parameters which combine the appearence of para1 and articulation of para2.
        :rtype: dictionary
        """        
        # Deepcopy para1
        param1 = para1.copy()
        param2 = para2
        param1["same_theta"] = param2["same_theta"]
        param1["same_scale"] = param2["same_scale"]
        param1["phi"]=param2["phi"]
        if param1["same_material"]:
            # If same material is true we can easily copy all parameters2
            self.logger.debug("param1['same_material']: " + str(param1["same_material"]))
            param1["theta"]=param2["theta"]
            param1["scale"]=param2["scale"]
            param1["total_cuboids"] = param2["total_cuboids"]
            param1["total_branches"]=param2["total_branches"]
        else:
            self.logger.debug("param1['same_material']: " + str(param1["same_material"]))
            self.logger.debug("param1['theta']: " + str(param1["theta"]))
            self.logger.debug("param2['theta']: " + str(param2["theta"]))
            if param1["total_cuboids"] > param2["total_cuboids"]:
                # If same material is false and para1 has more cuboids than para2 we have to crop out all apperence data for the cuboids which can't be shown with the articulation from para2 
                self.logger.debug('param1["total_cuboids"] > param2["total_cuboids"] == True')
                param1["total_cuboids"] = param2["total_cuboids"]
                param1["metallic"] = param1["metallic"][:param1["total_cuboids"]]
                param1["smoothness"] = param1["smoothness"][:param1["total_cuboids"]]
                param1["r"] = param1["r"][:param1["total_cuboids"]]
                param1["g"] = param1["g"][:param1["total_cuboids"]]
                param1["b"] = param1["b"][:param1["total_cuboids"]]
                param1["a"] = param1["a"][:param1["total_cuboids"]]
                param1["total_branches"]=param2["total_branches"]
                param1["theta"]=param2["theta"]
                param1["scale"]=param2["scale"]
            else:
                # If para2 has more cuboids, we can not fully display the articulation of para2 beacause we don't have the apperence data for the cuboids at the top
                # this means we can only show the articulation of para2 until the cubiod number: param1["total_cuboids"] 
                self.logger.debug('param1["total_cuboids"] > param2["total_cuboids"] == false')
                param1["total_branches"] = param2["total_branches"][:param1["total_cuboids"]-1]
                param1["theta"] = param2["theta"][:param1["total_cuboids"]-1]
                self.logger.debug("param2['same_scale']: " + str(param2["same_scale"]))
                if param2["same_scale"]:
                    param1["scale"] = param2["scale"]
                else:
                    param1["scale"] = param2["scale"][:param1["total_cuboids"]]
        return param1

    def change_apperence_camera_phi_relative(self, parameters, delta_phi = 20):
        """Input parameters and get parameters with the Camera position Phi shifted by ``delta_phi``.
        
        :param parameters: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type parameters: dictionary
        :param delta_phi: The amount of the added angle to Phi in degrees, defaults to 20
        :type delta_phi: float, optional
        :return: Parameters with Camera position Phi shifted by ``delta_phi``.
        :rtype: dictionary
        """        
        parameters["CameraPhi"] += delta_phi 
        return parameters

    def change_apperence_camera_phi(self, parameters, start_value, end_value, numb_of_changes):
        """Create many parameters in a list with the only difference in the Camera Phi value between ``start_value`` and the ``end_value``. 
        
        :param parameters: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type parameters: dictionary
        :param start_value: The value of phi of the camera in the first parameters in degree.
        :type start_value: float
        :param end_value: The value of phi of the camera in the last parameters in degree. 
        :type end_value: float
        :param numb_of_changes: How many parameters are going to be added to the returned list.
        :type numb_of_changes: int
        :return: List with the length: ``numb_of_changes`` of parameters in wich Camera position Phi is linearly extrapolated between the ``start_value`` and the ``end_value``.
        :rtype: list
        """        
        parameters_list = []
        para = parameters.copy()
        new_phi = np.linspace(start_value, end_value, numb_of_changes)
        for i in range(numb_of_changes):
            para["CameraPhi"] = new_phi[i]
            parameters_list.append(para) 
        return para

    def change_apperence_camera_theta_relative(self, parameters, delta_theta = 20):
        """Input parameters and get parameters with the Camera position theta shifted by ``delta_theta``.
        
        :param parameters: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type parameters: dictionary
        :param delta_theta: The amount of the added angle to Theta in degrees, defaults to 20
        :type delta_theta: float, optional
        :return: Parameters with Camera position Theta shifted by ``delta_theta``.
        :rtype: dictionary
        """        
        parameters["CameraTheta"] += delta_theta 
        return parameters

    def change_apperence_camera_theta(self, parameters, start_value, end_value, numb_of_changes):
        """Create many parameters in a list with the only difference in the Camera theta value between ``start_value`` and the ``end_value``. 
        
        :param parameters: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type parameters: dictionary
        :param start_value: The value of theta of the camera in the first parameters in degree.
        :type start_value: float
        :param end_value: The value of theta of the camera in the last parameters in degree. 
        :type end_value: float
        :param numb_of_changes: How many parameters are going to be added to the returned list.
        :type numb_of_changes: int
        :return: List with the length: ``numb_of_changes`` of parameters in wich Camera position theta is linearly extrapolated between the ``start_value`` and the ``end_value``.
        :rtype: dictionary
        """        
        parameters_list = []
        para = parameters.copy()
        new_theta = np.linspace(start_value, end_value, numb_of_changes)
        for i in range(numb_of_changes):
            para["CameraTheta"] = new_theta[i]
            parameters_list.append(para) 
        return para

    def change_articulation_theta(self, parameters, start_value, end_value, numb_of_changes, theta_pos = None):
        """Get a list of the input parameters with a changed crane articulation at the cuboid ``theta_pos`` between ``start_value`` and ``end_value``.
        If ``theta_pos`` is default then all theta of the crane are changing.
        
        :param parameters: Loaded or created parameters as from :meth:`~dataset.dataset_cuboids.create_random_parameters`.
        :type parameters: dictionary
        :param start_value: The theta angel in degrees for the first parameters in the list. 
        :type start_value: float
        :param end_value:  The theta angel in degrees for the last parameters in the list. 
        :type end_value: float
        :param numb_of_changes: How many parameters are going to be added to the returned list.
        :type numb_of_changes: int
        :param theta_pos: Defines at which cuboid theta is going to change. Has to be smaller than ``parameters["total_cuboids"]`` if not, set to ``parameters["total_cuboids"]-1``. If it is default: `None` all thetas are changing, defaults to None
        :type theta_pos: int, optional
        :return: A list with ``numb_of_changes`` parameters with changed theta from ``start_value`` to ``end_value`` at the cubiod ``theta_pos``.
        :rtype: `list`
        """        
        new_theta = np.linspace(start_value, end_value, numb_of_changes)
        parameters_list = []
        if(theta_pos==None):
            # If theta_pos is None then all thetas are going to change
            for i in range(numb_of_changes):
                New_Theta = []                
                for j in range(parameters["total_cuboids"]-1):
                    New_Theta.append(new_theta[i])
                parameters["theta"] = New_Theta
                parameters_list.append(parameters)
    
        else:    
            assert type(theta_pos) == int , "Dataset in change_articulation_theta: wrong input theta_pos has to be an integer or None; integer chooses position of manipulated theta, if None all theta are going to change the same."
            if theta_pos >= parameters["total_cuboids"]:
                theta_pos = parameters["total_cuboids"]-1
                self.logger.error("theta_pos is bigger or equal to parameters['total_cuboids']. Now set to the last cubiod.")
            New_Theta = []
            if parameters["same_theta"]==True:
                for i in range(parameters["total_cuboids"]):
                    New_Theta.append(parameters["theta"][0]) 
                    parameters["same_theta"]==False
                self.logger.info("Changing only one theta while same_theta is true")
            else:
                New_Theta = parameters["theta"]
            for i in range(numb_of_changes):
                self.logger.debug("i: " + str(i) + " new_theta: " + str(new_theta) + " theta_pos: " + str(theta_pos) + " New_Theta: " + str(New_Theta) )
                New_Theta[theta_pos] = new_theta[i]
                parameters["theta"] = New_Theta          
                parameters_list.append(parameters)
        return parameters_list
    
    def increment_index(self):
        """Load, increment and return the new external saved index.
        
        :raises FileNotFoundError: If the file ``data/python/index.txt`` is not found.
        :return: An integer which represents the next index.
        :rtype: int
        """        
        index = self.read_index()
        self.logger.debug("index: " + str(index))
        index = index + 1
        self.logger.debug("index: " + str(index))
        try:
            with open(self.data_directory + "/config/index.txt","w") as f:
                f.write(str(index))
                f.close()
        except FileNotFoundError as e:
                self.logger.error("Indexfile not found.")
                raise e
        return index

    def read_index(self):
        """Load and return the old external saved index.
        
        :raises FileNotFoundError: If the file ``data/python/index.txt`` is not found.
        :return: An integer which represents the last used index.
        :rtype: int
        """        
        try:
            with open(self.data_directory + "/config/index.txt","r") as f:
                index = f.read()
                f.close()
        except FileNotFoundError as e:
            self.logger.error("Indexfile not found. Initialising index.")
            self.reset_index()
            index = self.read_index()
        return int(index)

    def reset_index(self, set_index = -1):
        """Reset the external saved index to ``set_index`` to save storage and overwrite old parameters and images.
        
        :param set_index: The index to which it will be set, defaults to 0
        :type set_index: int, optional
        """        
        # Use this function if your data folder takes up too much space 
        with open(self.data_directory + "/config/index.txt","w") as f:
            f.write(str(set_index))
            f.close()

    def exit(self):
        """Closes TCP connection. Send end request to Unity and with that quit the application.
        """        
        self.uc.exit()
        self.logger.debug("Exit socket connection to unity.")
    
    def create_image_sequnces(self, key_list, num_list, alpha_parameter = None, return_dict = False, save_para = True, save_image = True):
        # one alpha tree which will be manipulated
        alpha_parameter = self.create_random_parameters() if alpha_parameter==None else alpha_parameter
        #TODO if total cuboids should change change the alpha crane total_cuboid

        # the range of a sequence parameter is specified in the config
        def amount_of_images(num_list):
            number = num_list[0]
            for i in range(1,len(num_list)):
                number = number * num_list[i]
            return number
        # calculate the amount of images that will be created
        amount_sequence_img = amount_of_images(num_list)
        # specify the amount of values for a sequnce paramter
        sequence_parameters = self.set_sequence_length(key_list = key_list, num_list = num_list)
        # create parameter set for all possibilities
        def recursive_parameter_creation(sequence_parameters, key_list, k = 0, current_para = {}, parameter_list = []):
            key = key_list[k]
            for i in range(len(sequence_parameters[key])):
                current_para[key] = sequence_parameters[key][i]
                if k < (len(sequence_parameters)-1):
                    recursive_parameter_creation(sequence_parameters, key_list, k = k + 1, current_para = current_para, parameter_list = parameter_list)
                else:
                    save_para = current_para.copy()
                    parameter_list.append(save_para)
                    save_para = {}
            if k == 0:
                return parameter_list

        all_parameters = recursive_parameter_creation(sequence_parameters, key_list)
        
        assert len(all_parameters) == amount_sequence_img
        self.logger.info("length of sequence data set will be: " + str(amount_sequence_img))

        # manipulate alpha paramters acording to sequences
        def change_parameters(alpha, changes):
            new_para = alpha.copy()
            mat_key = ["r", "g", "b", "a", "metallic", "smoothness"]    
            scal_key = ["theta", "scale"]
            for key in changes:
                if key in scal_key:
                    s_k = "same_" + key
                    assert alpha[s_k] == True
                elif key in mat_key:
                    assert alpha["same_scale"] == True
                new_para[key] = changes[key] 
            
            return new_para
        
        dict_list = []
        for i in range(len(all_parameters)):
            changes = all_parameters[i]
            self.printProgressBar(i, len(all_parameters)-1, prefix = '  Index ' + str(i) + " ", suffix = 'Complete', length = 200)
            current_para = change_parameters(alpha_parameter,changes)
            if return_dict:
                newDict = self.parameters_to_finished_data(current_para, save_para = save_para, save_image = save_image, return_dict = return_dict)
                current_para.clear()
                dict_list.append(newDict)
            else:
                self.parameters_to_finished_data(current_para, save_para = save_para, save_image = save_image, return_dict = return_dict)
                current_para.clear()
            
        if return_dict: return dict_list


        #TODO saving and loading parameters and images correctly        
    
    def create_dataset(self, dataset_size, test = True, continue_=False, images_per_row = 10, show_index = False):
        if test:
            dictionaries = []
            for i in range(dataset_size):
                self.printProgressBar(i, dataset_size-1, prefix = '  Index ' + str(i) + " ", suffix = 'Complete', length = 200)
                dictionaries.append(self.get_example(save_image = True, save_para = True, return_dict = True))
            self.plot_images(dictionaries, images_per_row=images_per_row, show_index=show_index)
        else:
            if continue_:
                self.load_config()
                cr_idx = self.read_index()
                cr_idx = cr_idx - 1 
                self.reset_index(cr_idx)                
            else:
                self.reset_index()
                cr_idx = 0
            for i in range(cr_idx, dataset_size):
                self.printProgressBar(i, dataset_size-1, prefix = '  Index ' + str(i) + " ", suffix = 'Complete', length = 200)
                self.get_example(save_image = True, save_para = True, return_dict = False)
        self.exit()



    def printProgressBar (self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print()


    def set_sequence_length(self, key_list, num_list):
        assert len(key_list) == len(num_list)
        all_parameters = ["total_cuboids","scale","phi","theta",
                        "r", "g", "b", "a", "metallic", "smoothness",
                        "Camera_FieldofView", "CameraRadius", "CameraTheta", "CameraPhi", "CameraVerticalOffset",
                        "totalPointLights", "PointLightsRadius", "PointLightsPhi", "PointLightsTheta", "PointLightsIntensity", "PointLightsRange", "PointLightsColor_r", "PointLightsColor_g", "PointLightsColor_b", "PointLightsColor_a",
                        "totalSpotLights", "SpotLightsRadius", "SpotLightsPhi", "SpotLightsTheta", "SpotLightsIntensity", "SpotLightsRange", "SpotAngle", "SpotLightsColor_r", "SpotLightsColor_g", "SpotLightsColor_b", "SpotLightsColor_a",
                        "DirectionalLightTheta", "DirectionalLightIntensity" 
                        ]
        mat_key = ["r", "g", "b", "a", "metallic", "smoothness"]    
        scal_key = ["theta", "scale"]
        # not sure if config has to be asserted
        for key in key_list:
            if key in all_parameters:
                if key in scal_key:
                    s_k = "same_" + key
                    assert self.config[s_k] == True
                elif key in mat_key:
                    assert self.config["same_material"] == True
                elif key == "total_cuboids":
                    assert self.config["same_scale"] == True
                    assert self.config["same_theta"] == True
                    assert self.config["same_material"] == True
            else:
                key_list.remove(key)
                self.logger.indo(key + " is not a sequence parameter key. Check spelling. The key is removed")      

        def linear_interpolation(key, num, dtype):
            assert type(key) == str, "Key has to be a string."
            assert type(self.config[key]) == list and len(self.config[key]) == 2, "linear interpolaltion of " + key + ", self.config[" + key + "] has to be a list with the length two. self.config[" + key + "] = " + str(self.config[key])
            return np.linspace(start = self.config[key][0], stop= self.config[key][1], num = num, dtype=dtype).tolist()

        int_keys = ["total_cuboids", "totalPointLights", "totalSpotLights"]
        sequence_parameters = {}
        for i in range(len(key_list)):
            key = key_list[i]
            d_type = int if key in int_keys else float
            sequence_parameters[key] = linear_interpolation(key, num_list[i], d_type)
            
        return sequence_parameters
        

        

        
        # possible sequence parameters
    '''
        scale=[0.5,4], 
            same_scale=None,
            specify_scale=False,
        total_cuboids=[2,5], 
        phi=[0,360],  
        theta=None, 
            same_theta=None,
             specify_theta=False,
        r=[0,1], g=[0,1], b=[0,1], a=1, metallic=[0,1], smoothness=[0,1],
            same_material=None, specify_material=False,  
        Camera_FieldofView=90, CameraRadius = None, CameraTheta = [60,100], CameraPhi = [0,360], CameraVerticalOffset = None, 
        totalPointLights=[5,12], PointLightsRadius=[5,20], PointLightsPhi=[0,360], PointLightsTheta=[0,90], PointLightsIntensity=[7,17], PointLightsRange=[5,25], 
            same_PointLightsColor=None, PointLightsColor_r=[0,1], PointLightsColor_g=[0,1], PointLightsColor_b=[0,1], PointLightsColor_a=[0.5,1],
        totalSpotLights=[3,7], SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotAngle=[5,120],
            same_SpotLightsColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
        DirectionalLightTheta = [0,90], DirectionalLightIntensity = [1.0,6.0],
        '''    