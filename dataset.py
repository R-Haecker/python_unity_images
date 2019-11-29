from PIL import Image
import client
from edflow.data.dataset import DatasetMixin
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import tkinter
import json
import math
import logging
import copy
import time

class DataSetCrane(DatasetMixin):
    def __init__(self, config = None, use_unity_build = True, combine_logs = True, debug_log = False):
        # Set up log level
        if debug_log:
            log_level = logging.DEBUG
        else:
            log_level = logging.INFO
        # Set up a client and start unity 
        self.uc = client.client_communicator_to_unity(use_unity_build=use_unity_build, log_level = log_level)
        
        # Use already existing logger from pthon for dataset as well
        self.log_path = "log/python_dataset_and_client.log"
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
        
        self.logger.debug("Create config.")
        # Create dataset config for random parameter creation
        if config==None:    
            # Set the default intervall for all random generated parameters
            self.config = self.writeConfig()
        else:
            # Use the given config
            self.config = config
        self.logger.debug("Dataset initialised.\n")        

    def writeConfig(self,same_scale=None, scale=[0.5,4], totalSegments=[2,12], phi=[0,360], enable_many_arms=[1,3],same_theta=None, theta=None, 
    same_material=None, r=[0,1], g=[0,1], b=[0,1], a=[0.5,1], metallic=[0,1], smoothness=[0,1], CameraRadius = 10.0, CameraTheta = [30,100], CameraPhi = [0,360], CameraVerticalOffset = None,
    totalPointLights=[5,12], PointLightsRadius=[5,20], PointLightsPhi=[0,360], PointLightsTheta=[0,90], PointLightsIntensity=[7,17], PointLightsRange=[5,25], samePointLightColor=None, PointLightsColor_r=[0,1], PointLightsColor_g=[0,1], PointLightsColor_b=[0,1], PointLightsColor_a=[0.5,1],
    totalSpotLights=None, SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotLightsAngle=[5,120], sameSpotLightColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
    DirectionalLightTheta = [0,90], DirectionalLightIntensity = [0.1,1.8]):
        ### Retruns a config as dictionary which determines the interval for all random parameters created in the function create_random_parameters  
        config = {}
        # Create intervals for general properties
        assert len(totalSegments) == 2, "totalSegments[0] is minimal limit and totalSegments[1] is maximal limit for random generation of totalSegments"
        config["totalSegments"]=totalSegments
        # Use the same_theta for every angle between two cubiods
        config["same_theta"]=same_theta
        if theta!=None:
            assert len(theta) == 2, "theta != None is true; theta[0] is minimal limit and theta[1] is maximal limit for random generation theta"
        config["theta"]=theta
        assert len(phi) == 2, "phi[0] is minimal limit and phi[1] is maximal limit for random generation of phi."
        # Phi describes by how much the crane is roteted
        config["phi"]=phi
        # Use the same scale for every cubiod
        if same_scale!=None:
            assert type(same_scale)==bool, "Has to be bool or None; same_scale sets the bool of same_scale in getRandomJsonData. If it is None bool is set randomly." 
        config["same_scale"]=same_scale
        assert len(scale) == 2, "scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods."
        # Vertical Scale of the cubiods
        config["scale"]=scale    
        # The upper limit for the arms is dicribing the three sigma variance of the guassion normal distribution for random generation of TotalArms_Segment
        if enable_many_arms!=None:
            assert len(enable_many_arms) == 2, "Has to be list of length 2 or type None; enable_many_arms defines boundaries for how many arms could be created in getRandomJsonData. This means that there is a chance that the crane splits up in the given range. If it is None then there will be only one arm." 
            assert enable_many_arms[0] > 0, "enable_many_arms has to be 1 or greater to even create one Arm."
            assert enable_many_arms[1] > 0, "enable_many_arms has to be 1 or greater to even create one Arm."
        config["enable_many_arms"] = enable_many_arms
        
        # Create intervals or fixed values for camera position
        if type(CameraRadius)== list:
            assert len(CameraRadius) == 2, "CameraRadius has to be a list len()==2 or a float for a fixed value."
        config["CameraRadius"] = CameraRadius 
        if type(CameraTheta)== list:
            assert len(CameraTheta) == 2, "CameraTheta has to be a list len()==2 or a float for a fixed value."
        config["CameraTheta"] = CameraTheta 
        if type(CameraPhi)== list:
            assert len(CameraPhi) == 2, "CameraPhi has to be a list len()==2 or a float for a fixed value."
        config["CameraPhi"] = CameraPhi 
        if CameraVerticalOffset==None:
            config["CameraVerticalOffset"] = 0    
        else:
            if type(CameraVerticalOffset)== list:
                assert len(CameraVerticalOffset) == 2, "CameraVerticalOffset has to be a list len()==2 or a float for a fixed value."
            config["CameraVerticalOffset"] = CameraVerticalOffset 
        
        # Create intervals for Material properties 
        if same_material!=None:
            assert type(same_material)==bool, "Has to be bool or None. same_material sets the bool of same_material in getRandomJsonData. If it is None bool is set randomly." 
        config["same_material"] = same_material
        assert len(r) == 2, "r[0] is minimal limit and r[1] is maximal limit for random generation of the segmentscolor r (red)"
        config["r"]=r
        assert len(g) == 2, "g[0] is minimal limit and g[1] is maximal limit for random generation of the segmentscolor g"
        config["g"]=g
        assert len(b) == 2, "b[0] is minimal limit and b[1] is maximal limit for random generation of the segmentscolor b"
        config["b"]=b
        assert len(a) == 2, "a[0] is minimal limit and a[1] is maximal limit for random generation of the segmentscolor a (alpha/transparency)"
        config["a"]=a
        assert len(metallic) == 2, "metallic[0] is minimal limit and metallic[1] is maximal limit for random generation of the segmentsmaterial property metallic"
        config["metallic"]=metallic
        assert len(smoothness) == 2, "smoothness[0] is minimal limit and smoothness[1] is maximal limit for random generation of the segmentsmaterial property smoothness"
        config["smoothness"]=smoothness
        if same_theta!=None:
            assert type(same_theta)==bool, "Has to be bool or none. same_theta sets the bool of same_theta in getRandomJsonData. If it is None bool is set randomly." 
        
        # Create intervals for DirectionalLight
        if DirectionalLightTheta==None or DirectionalLightIntensity==None:
            config["DirectionalLightTheta"] = None
            config["DirectionalLightIntensity"] = None
        else:
            assert len(DirectionalLightTheta) == 2, "DirectionalLightTheta[0] is minimal limit and DirectionalLightTheta[1] is maximal limit for random generation of DirectionalLightTheta."
            config["DirectionalLightTheta"] = DirectionalLightTheta
            assert len(DirectionalLightIntensity) == 2, "DirectionalLightIntensity[0] is minimal limit and DirectionalLightIntensity[1] is maximal limit for random generation of DirectionalLightIntensity."
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
            if samePointLightColor!=None:
                assert type(samePointLightColor)==bool, "Has to be bool or none. samePointLightColor sets the bool of samePointLightColor in getRandomJsonData. If its None bool is set randomly." 
            config["samePointLightColor"]=samePointLightColor
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
            assert len(SpotLightsAngle) == 2, "SpotLightsAngle[0] is minimal limit and SpotLightsAngle[1] is maximal limit for random generation of SpotLightsAngle."
            config["SpotLightsAngle"]=SpotLightsAngle
            if sameSpotLightColor!=None:
                assert type(sameSpotLightColor)==bool, "Has to be bool or None. sameSpotLightColor sets the bool of sameSpotLightColor in getRandomJsonData. If its None bool is set randomly." 
            config["sameSpotLightColor"]=sameSpotLightColor
            assert len(SpotLightsColor_r) == 2, "SpotLightsColor_r[0] is minimal limit and SpotLightsColor_r[1] is maximal limit for random generation of SpotLightsColor_r."
            config["SpotLightsColor_r"]=SpotLightsColor_r
            assert len(SpotLightsColor_g) == 2, "SpotLightsColor_g[0] is minimal limit and SpotLightsColor_g[1] is maximal limit for random generation of SpotLightsColor_g."
            config["SpotLightsColor_g"]=SpotLightsColor_g
            assert len(SpotLightsColor_b) == 2, "SpotLightsColor_b[0] is minimal limit and SpotLightsColor_b[1] is maximal limit for random generation of SpotLightsColor_b."
            config["SpotLightsColor_b"]=SpotLightsColor_b
            assert len(SpotLightsColor_a) == 2, "SpotLightsColor_a[0] is minimal limit and SpotLightsColor_a[1] is maximal limit for random generation of SpotLightsColor_a."
            config["SpotLightsColor_a"]=SpotLightsColor_a
            
        return config
        
    def create_random_parameters(self , CameraRes_width= 520, CameraRes_height=520,):
        ### Creates random input parameter depending on your config, the camera parameters are not random
        dictionary={}

        # not random set variables for the Camera
        dictionary["CameraRes_width"] = CameraRes_width 
        dictionary["CameraRes_height"] = CameraRes_height 
        dictionary["Camera_FieldofView"] = 80
        
        # If needed you could save the seed
        #np.random.seed(Seed)
        #dictionary["seed"] = np.random.get_state()

        # Create all parameters randomly 
        
        # Camera position
        if type(self.config["CameraRadius"]) == float:
            dictionary["CameraRadius"] = self.config["CameraRadius"]
        else:
            dictionary["CameraRadius"] = np.random.uniform(self.config["CameraRadius"][0],self.config["CameraRadius"][1])
        if type(self.config["CameraTheta"]) == float:
            dictionary["CameraTheta"] = self.config["CameraTheta"]
        else:
            dictionary["CameraTheta"] = np.random.uniform(self.config["CameraTheta"][0],self.config["CameraTheta"][1])
        if type(self.config["CameraPhi"]) == float:
            dictionary["CameraPhi"] = self.config["CameraPhi"] 
        else:
            dictionary["CameraPhi"] = np.random.uniform(self.config["CameraPhi"][0],self.config["CameraPhi"][1])
        if type(self.config["CameraVerticalOffset"]) == float or type(self.config["CameraVerticalOffset"]) == int:
            dictionary["CameraVerticalOffset"] = self.config["CameraVerticalOffset"] 
        else:
            dictionary["CameraVerticalOffset"] = np.random.uniform(self.config["CameraVerticalOffset"][0],self.config["CameraVerticalOffset"][1])
        
        # Create how many Cubiods are in one branch.
        TotalSegments = np.random.randint(self.config["totalSegments"][0],self.config["totalSegments"][1])
        # Create the angle and the intensity of the directional light
        if self.config["DirectionalLightIntensity"] == None:
            DirectionalLightIntensity = 0   
            DirectionalLightTheta = 0
        else:        
            DirectionalLightTheta = np.random.uniform(self.config["DirectionalLightTheta"][0], self.config["DirectionalLightTheta"][1])
            DirectionalLightIntensity = np.random.uniform(self.config["DirectionalLightIntensity"][0], self.config["DirectionalLightIntensity"][1])
        
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
            if(self.config["samePointLightColor"]==None):
                Same_PLcolor = bool(np.random.randint(2,dtype=int))
            else:
                Same_PLcolor = self.config["samePointLightColor"]
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
        SpotLightsAngle = []
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
            if(self.config["sameSpotLightColor"]==None):
                Same_SLcolor = bool(np.random.randint(2))
            else:
                Same_SLcolor = self.config["sameSpotLightColor"]
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
            SpotLightsAngle=np.random.uniform(self.config["SpotLightsAngle"][0],self.config["SpotLightsAngle"][1],TotalSpotLights).tolist()
        
        # Amount of branches (Arms) and at which cubiod to branch. The first element of the list TotalArms_Segments counts the amount of branches at the first cubiod and and so on...
        # if TotalArms_Segment = [1,1,1,1,1] then there is only one "main" Branch and no splits  
        TotalArms_Segment = []
        if self.config["enable_many_arms"]==None:
            TotalArms_Segment = None
        else:
            if self.config["enable_many_arms"][0] < 1:
                self.logger.info("config['enable_many_arms'][0] is bigger than 1. This means you create at every segment new arms. Change the dataset config if you do not want this.")
            # the upper limit for the arms is dicribing the three sigma variance of the guassion normal distribution
            arms = np.random.normal(0,(self.config["enable_many_arms"][1] - self.config["enable_many_arms"][0])/3, TotalSegments-1)  
            arms = np.absolute(arms) + self.config["enable_many_arms"][0] 
            for i in range(TotalSegments-1):
                if arms[i]<=1 :
                    TotalArms_Segment.append(1)
                else:
                    TotalArms_Segment.append(int(arms[i]))
            self.logger.debug("TotalArms_Segment: "+str(TotalArms_Segment)) 
        # Decide if there should be only one theta angle for cubiods
        if(self.config["same_theta"]==None):
            Same_Theta = bool(np.random.randint(2))
        else:
            Same_Theta = self.config["same_theta"]
        # Theta describes the angel between two cubiods next to each other
        Theta = []
        if(Same_Theta):
            if self.config["theta"]==None:
                Theta.append(np.random.uniform(0,360/TotalSegments))
        else:
            if self.config["theta"]==None:
                Theta=np.random.uniform(0,360/TotalSegments,TotalSegments-1).tolist()
            else:
                Theta=np.random.uniform(self.config["theta"][0],self.config["theta"][1],TotalSegments-1).tolist()
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
        if(Same_Material):
            R=np.random.uniform(self.config["r"][0],self.config["r"][1])
            G=np.random.uniform(self.config["g"][0],self.config["g"][1])
            B=np.random.uniform(self.config["b"][0],self.config["b"][1])
            A=np.random.uniform(self.config["a"][0],self.config["a"][1])
            Metallic=np.random.uniform(self.config["metallic"][0],self.config["metallic"][1])
            Smoothness=np.random.uniform(self.config["smoothness"][0],self.config["smoothness"][1])
            
        else:
            R=np.random.uniform(self.config["r"][0],self.config["r"][1],TotalSegments).tolist()
            G=np.random.uniform(self.config["g"][0],self.config["g"][1],TotalSegments).tolist()
            B=np.random.uniform(self.config["b"][0],self.config["b"][1],TotalSegments).tolist()
            A=np.random.uniform(self.config["a"][0],self.config["a"][1],TotalSegments).tolist()
            Metallic=np.random.uniform(self.config["metallic"][0],self.config["metallic"][1],TotalSegments).tolist()
            Smoothness=np.random.uniform(self.config["smoothness"][0],self.config["smoothness"][1],TotalSegments).tolist()
        # Decide if all cubiods should have the same vertical scale
        if(self.config["same_scale"]==None):
            Same_Scale = bool(np.random.randint(2))
        else:
            Same_Scale = self.config["same_scale"]
        # Create Scale
        if(Same_Scale):
            Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1])
        else:
            Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1],TotalSegments).tolist()
        # Create Phi the rotation of the crane
        Phi=np.random.uniform(self.config["phi"][0],self.config["phi"][1])
        
        # Add all parameters to a dictionary
        dictionary["totalSegments"] = TotalSegments
        dictionary["scale"] = Scale
        dictionary["same_scale"] = Same_Scale
        dictionary["totalArms_Segment"] = TotalArms_Segment
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
            dictionary["SpotAngle"] = SpotLightsAngle
        
        return dictionary
        
    def create_json_string_from_parameters(self, dictionary):
        ### Return a String depending on your input parameters wich can be interpreted afterwards by the Unity script 
        return self.uc.write_json_crane(totalSegments=dictionary["totalSegments"], same_scale=dictionary["same_scale"], scale=dictionary["scale"], same_theta=dictionary["same_theta"], theta=dictionary["theta"], phi=dictionary["phi"], totalArms_Segment=dictionary["totalArms_Segment"], same_material=dictionary["same_material"], metallic=dictionary["metallic"], smoothness=dictionary["smoothness"], r=dictionary["r"], g=dictionary["g"], b=dictionary["b"], a=dictionary["a"], CameraRes_width=dictionary["CameraRes_width"], CameraRes_height=dictionary["CameraRes_height"], Camera_FieldofView=dictionary["Camera_FieldofView"], CameraRadius=dictionary["CameraRadius"], CameraTheta=dictionary["CameraTheta"], CameraPhi=dictionary["CameraPhi"], CameraVerticalOffset=dictionary["CameraVerticalOffset"], 
            totalPointLights=dictionary["totalPointLights"], same_PointLightsColor=dictionary["same_PointLightsColor"], PointLightsColor_r=dictionary["PointLightsColor_r"], PointLightsColor_g=dictionary["PointLightsColor_g"], PointLightsColor_b=dictionary["PointLightsColor_b"], PointLightsColor_a=dictionary["PointLightsColor_a"], PointLightsRadius=dictionary["PointLightsRadius"], PointLightsTheta=dictionary["PointLightsTheta"], PointLightsPhi=dictionary["PointLightsPhi"], PointLightsIntensity=dictionary["PointLightsIntensity"], PointLightsRange=dictionary["PointLightsRange"], 
            totalSpotLights=dictionary["totalSpotLights"], same_SpotLightsColor=dictionary["same_SpotLightsColor"], SpotLightsColor_r=dictionary["SpotLightsColor_r"], SpotLightsColor_g=dictionary["SpotLightsColor_g"], SpotLightsColor_b=dictionary["SpotLightsColor_b"], SpotLightsColor_a=dictionary["SpotLightsColor_a"], SpotLightsRadius=dictionary["SpotLightsRadius"], SpotLightsTheta=dictionary["SpotLightsTheta"], SpotLightsPhi=dictionary["SpotLightsPhi"], SpotLightsIntensity=dictionary["SpotLightsIntensity"], SpotLightsRange=dictionary["SpotLightsRange"],SpotAngle=dictionary["SpotAngle"],
            DirectionalLightTheta=dictionary["DirectionalLightTheta"], DirectionalLightIntensity=dictionary["DirectionalLightIntensity"])

    def save(self, dictionary, save_para = True, save_image = False):
        ### Save parameter data or an image of a dictionary in the data/parameters folder or the data/images folder.
        # Save parameters.
        if save_para:
            # Check if the parameters and the index is in the dictionary.
            if "parameters" in dictionary:
                if "index" in dictionary:
                    with open("data/parameters/parameters_index_" + str(dictionary["index"]) + '.json', 'w') as f:
                        json.dump(dictionary["parameters"],f)
                        f.close()
                else:
                    # Change the name of the json file if there is no index given.
                    fake_index = np.random.randint(0,1000)
                    with open("data/parameters/parameters_NO_index_" + str(fake_index) + '.json', 'w') as f:
                        json.dump(dictionary["parameters"],f)
                        f.close()
            else:
                self.logger.error("Image parameters could not be saved. No parameters found in dictionary.")
        # Save the image as png.
        if save_image:
            # Check if the image and the index is in the dictionary.
            if "image" in dictionary:
                if "index" in dictionary:
                    Image.fromarray(dictionary["image"]).save("data/images/image_index_" + str(dictionary["index"]) + '.png')
                else:
                    # Change the name of the image if there is no index given.
                    fake_index = np.random.randint(0,1000)
                    Image.fromarray(dictionary["image"]).save("data/images/image_NO_index_" + str(fake_index) + '.png')
            else:
                self.logger.error("Image could not be saved. No image data not found in dictionary.")

    def load_parameters(self,index = [-1], amount = 1):
        ### Load and return a given aoumt of parameters. If index is not specified the index will be chooden randomly.  
        if index[0]==-1:
            index = np.random.randint(0,self.load_index(),amount)
        else:
            assert len(index)==amount, "Specified Index has to be len(Index):" + str(len(index)) + " equal to amount:" + str(amount)
        parameter_list = []
        # Load the amount of parameters and append them to the parameter_list
        for i in range(amount):
            while 1:
                try:
                    f = open("data/parameters/parameters_index_" + str(index[i]) + ".json")
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
   
    def parameters_to_finished_data(self, parameters, save_para = True, save_image = False):
        ### Return dictionary with all relevant data. Input parameters and get an corresponding image. 
        # Format the parameters to a jsonstring that can be sent and interpreted by Unity.
        jsonstring = self.create_json_string_from_parameters(parameters)
        # Recive an image depending on your parameters.
        img = self.uc.recive_image(jsonstring)
        # Load and increment the extern saved index.
        index = self.increment_index()
        # Put data in an dictionary.
        newDict = {"index":index,"parameters":parameters,"image":img}
        # Save parameters for later recreating and manipulating the image.
        self.save(newDict,save_para = save_para, save_image = save_image)
        return newDict  

    def get_example(self,index = None, save_para = True, save_image = False):
        ### Returns a dictionary with all relevant data and the image. Create an exampel image from random parameters.
        # Create random parameters depending o your config.  
        random_parameters = self.create_random_parameters()
        # Get data with image in dictionary.
        newDict = data.parameters_to_finished_data(random_parameters, save_para = save_para, save_image = save_image)
        return newDict

    def plot_images(self, dicts, images_in_one_row = 4, save_fig = True, show_index = True):
        ### Plot and show all images contained in the list of dictionaries and label them with their corresponding index. 
        # How many images are there
        numb = len(dicts)
        if numb < images_in_one_row:
            images_in_one_row = numb
        numb_y = 0
        numb_x = images_in_one_row
        # numb_y and numb_x determine the size of the grid of images
        while numb > numb_x:
            numb_y += 1
            numb -= images_in_one_row
        numb_y += 1
        self.logger.debug("numb_y: " + str(numb_y))
        self.logger.debug("dicts[0]['image'].shape[0]: " + str(dicts[0]["image"].shape[0]))
        self.logger.debug("(images_in_one_row*dicts[0][image].shape[1]: " + str((images_in_one_row*dicts[0]["image"].shape[1])))
        self.logger.debug("dicts[0][image].shape[2]: " + str(dicts[0]["image"].shape[2]))
        h_stacked = np.ones((numb_y, dicts[0]["image"].shape[0], (images_in_one_row*dicts[0]["image"].shape[1]), dicts[0]["image"].shape[2]), dtype=int)
        self.logger.debug("h_stacked.shape: " + str(h_stacked.shape))
        # Stack all images in one row together with np.hstack() for all numb_y
        for i in range(numb_y):
            img_hstack = np.ones((numb_x, dicts[0]["image"].shape[0], dicts[0]["image"].shape[1], dicts[0]["image"].shape[2]), dtype=int)
            if i == numb_y-1:
                for j in range(numb):
                    img_hstack[j] = dicts[i*numb_x+j]["image"]
            else:    
                for j in range(numb_x):
                    img_hstack[j] = dicts[i*numb_x+j]["image"]
            h_stacked[i] = np.hstack((img_hstack))
        # Stack all rows vertically together
        final_img = np.vstack((h_stacked))
        self.logger.debug("final_img.shape: " + str(final_img.shape))
        matplotlib.use('TkAgg')
        plt.imshow(final_img)
        # Plot lines between images to better see the borders of the images
        for i in range(1,numb_y):
            plt.axhline(y = dicts[0]["image"].shape[0]*i, color="k")
        for i in range(1,numb_x):
            plt.axvline(x = dicts[0]["image"].shape[1]*i, color="k")
        # Plot the index of the images onto the images
        if show_index:
            j = 0
            for i in range(0,len(dicts)):
                if "index" in dicts[i]:
                    if i%numb_x==0:
                        j += 1
                    plt.text(dicts[0]["image"].shape[1]*((i%numb_x) + 0.05), dicts[0]["image"].shape[0]*(j - 0.05), "idx: " + str(dicts[i]["index"]) )
                else:
                    self.logger.error("dicts[" + str(i) + "] has no index.")
        plt.axis('off')
        # Save figure if wanted.
        if save_fig:
            plt.savefig("data/figures/fig_from_index_" + str(dicts[0]["index"]) + "_to_index_" + str(dicts[len(dicts)-1]["index"]) + ".png")
        plt.show()

    def change_app1_art2(self, para1, para2):
        # Returns parameters in a dictionary which combine the apperence of para1 and articulation of para2 
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
            param1["totalSegments"] = param2["totalSegments"]
            param1["totalArms_Segment"]=param2["totalArms_Segment"]
        else:
            self.logger.debug("param1['same_material']: " + str(param1["same_material"]))
            self.logger.debug("param1['theta']: " + str(param1["theta"]))
            self.logger.debug("param2['theta']: " + str(param2["theta"]))
            if param1["totalSegments"] > param2["totalSegments"]:
                # If same material is false and para1 has more cuboids than para2 we have to crop out all apperence data for the segments which can't be shown with the articulation from para2 
                self.logger.debug('param1["totalSegments"] > param2["totalSegments"] == True')
                param1["totalSegments"] = param2["totalSegments"]
                param1["metallic"] = param1["metallic"][:param1["totalSegments"]]
                param1["smoothness"] = param1["smoothness"][:param1["totalSegments"]]
                param1["r"] = param1["r"][:param1["totalSegments"]]
                param1["g"] = param1["g"][:param1["totalSegments"]]
                param1["b"] = param1["b"][:param1["totalSegments"]]
                param1["a"] = param1["a"][:param1["totalSegments"]]
                param1["totalArms_Segment"]=param2["totalArms_Segment"]
                param1["theta"]=param2["theta"]
                param1["scale"]=param2["scale"]
            else:
                # If para2 has more cuboids, we can not fully display the articulation of para2 beacause we don't have the apperence data for the cuboids at the top
                # this means we can only show the articulation of para2 until the cubiod number: param1["totalSegments"] 
                self.logger.debug('param1["totalSegments"] > param2["totalSegments"] == false')
                param1["totalArms_Segment"] = param2["totalArms_Segment"][:param1["totalSegments"]-1]
                param1["theta"] = param2["theta"][:param1["totalSegments"]-1]
                self.logger.debug("param2['same_scale']: " + str(param2["same_scale"]))
                if param2["same_scale"]:
                    param1["scale"] = param2["scale"]
                else:
                    param1["scale"] = param2["scale"][:param1["totalSegments"]]
        return param1

    def change_apperence_camera_phi_relative(self, parameters, delta_phi = 20):
        ### Return parameters with Camera position Phi shifted by delta_phi   
        parameters["CameraPhi"] += delta_phi 
        return parameters

    def change_apperence_camera_phi(self, parameters, start_value, end_value, amount_of_pics):
        ### Return list with amount_of_pics of parameters in wich Camera position Phi is between the start_value and the end_value    
        parameters_list = []
        para = parameters.copy()
        new_phi = np.linspace(start_value, end_value, amount_of_pics)
        for i in range(amount_of_pics):
            para["CameraPhi"] = new_phi[i]
            parameters_list.append(para) 
        return para

    def change_apperence_camera_theta_relative(self, parameters, delta_theta = 20):
        ### Return parameters with Camera position Theta shifted by delta_phi   
        parameters["CameraTheta"] += delta_theta 
        return parameters

    def change_apperence_camera_theta(self, parameters, start_value, end_value, amount_of_pics):
        ### Return list with amount_of_pics of parameters in wich Camera position Theta is between the start_value and the end_value    
        parameters_list = []
        para = parameters.copy()
        new_theta = np.linspace(start_value, end_value, amount_of_pics)
        for i in range(amount_of_pics):
            para["CameraTheta"] = new_theta[i]
            parameters_list.append(para) 
        return para

    def change_articulation_theta(self, parameters, start_value, end_value, amount_of_pics, theta_pos = None):
        ### Return a list with amount_of_pics parameters with changed theta from start_value to end_value at the cubiod theta_pos 
        new_theta = np.linspace(start_value, end_value, amount_of_pics)
        parameters_list = []
        if(theta_pos==None):
            # If theta_pos is None then all thetas are going to change
            for i in range(amount_of_pics):
                New_Theta = []                
                for j in range(parameters["totalSegments"]-1):
                    New_Theta.append(new_theta[i])
                parameters["theta"] = New_Theta
                parameters_list.append(parameters)
    
        else:    
            assert type(theta_pos) == int , "Dataset in change_articulation_theta: wrong input theta_pos has to be an integer or None; integer chooses position of manipulated theta, if None all theta are going to change the same."
            if theta_pos >= parameters["totalSegments"]:
                theta_pos = parameters["totalSegments"]-1
                self.logger.error("theta_pos is bigger or equal to parameters['totalSegments']. Now set to the last cubiod.")
            New_Theta = []
            if parameters["same_theta"]==True:
                for i in range(parameters["totalSegments"]):
                    New_Theta.append(parameters["theta"][0]) 
                    parameters["same_theta"]==False
                self.logger.info("Changing only one theta while same_theta is true")
            else:
                New_Theta = parameters["theta"]
            for i in range(amount_of_pics):
                self.logger.debug("i: " + str(i) + " new_theta: " + str(new_theta) + " theta_pos: " + str(theta_pos) + " New_Theta: " + str(New_Theta) )
                New_Theta[theta_pos] = new_theta[i]
                parameters["theta"] = New_Theta          
                parameters_list.append(parameters)
        return parameters_list
    
    def increment_index(self):
        ### Load, increment and return the externaly saved index.
        index = self.load_index()
        self.logger.debug("index: " + str(index))
        index = index + 1
        self.logger.debug("index: " + str(index))
        try:
            with open("data/python/index.txt","w") as f:
                f.write(str(index))
                f.close()
        except FileNotFoundError as e:
                self.logger.error("Indexfile not found.")
                raise e
        return index

    def load_index(self):
        ### Load and return the externaly saved index.
        try:
            with open("data/python/index.txt","r") as f:
                index = f.read()
                f.close()
        except FileNotFoundError as e:
            self.logger.error("Indexfile not found.")
            raise e
        return int(index)

    def reset_index(self, set_index = 0):
        ### Reset the externaly saved index to set_index
        # Use this function if your data folder takes up too much space 
        with open("data/index.txt","w") as f:
            f.write(str(set_index))
            f.close()

    def exit(self):
        ### Close TCP connection. Send end request to Unity and with that quit the application.  
        self.uc.exit()
        self.logger.debug("Exit socket connection to unity.")


data = DataSetCrane(use_unity_build = True,debug_log=False)

dicts = []
for i in range(1):
    dicts.append(data[0])
'''
for i in range(5):
    para = data.create_random_parameters()
    para1 = data.create_random_parameters()
    para2 = data.change_app1_art2(para, para1)

    dicts.append(data.parameters_to_finished_data(para))
    dicts.append(data.parameters_to_finished_data(para1))
    dicts.append(data.parameters_to_finished_data(para2))
'''
data.exit()

data.plot_images(dicts, images_in_one_row=5)

