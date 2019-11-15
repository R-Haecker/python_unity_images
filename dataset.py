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

class DataSetCrane(DatasetMixin):
    def __init__(self, config = None, use_unity_build = True, combine_logs = True, log_level = logging.INFO):
        self.uc = client.Client_Communicator_to_Unity(use_unity_build=use_unity_build, log_level = log_level, relative_unity_build_path = "/build/image.x86_64")
        
        # Create logger
        self.log_path = "log/dataset.log"
        self.logger = logging.getLogger('dataset_log')
        self.logger.setLevel(logging.DEBUG)
        # Create the same console handler as the client
        self.ch = self.uc.ch
        # Create a file handler 
        self.fh = logging.FileHandler(self.log_path)
        self.fh.setLevel(logging.DEBUG)
        # Use the same format as the client
        self.fh.setFormatter(self.uc.formatter_fh)
        self.ch.setFormatter(self.uc.formatter_ch)
        # Add the fh and the ch to the logger
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.ch)        
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

    def writeConfig(self,same_scale=None, scale=[0.5,4], totalSegments=[2,12], phi=[0,360], enable_many_arms=[1,3],same_theta=None, theta=None, same_material=None, r=[0,1], g=[0,1], b=[0,1], a=[0.5,1], metallic=[0,1], smoothness=[0,1],
    totalPointLights=None, PointLightsRadius=[5,20], PointLightsPhi=[0,360], PointLightsTheta=[0,90], PointLightsIntensity=[7,17], PointLightsRange=[5,25], samePointLightColor=None, PointLightsColor_r=[0,1], PointLightsColor_g=[0,1], PointLightsColor_b=[0,1], PointLightsColor_a=[0.5,1],
    totalSpotLights=None, SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotLightsAngle=[5,120], sameSpotLightColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
    DirectionalLightTheta = [0,90], DirectionalLightIntensity = [0.1,1.8]):
        ### retruns a config dictionary which determines the interval for all random parameters created in the function create_random_parameters  
        config = {}
        # Create intervals for general properties
        assert len(totalSegments) == 2, "totalSegments[0] is minimal limit and totalSegments[1] is maximal limit for random generation of totalSegments"
        config["totalSegments"]=totalSegments
        config["same_theta"]=same_theta
        if theta!=None:
            assert len(theta) == 2, "theta != None is true; theta[0] is minimal limit and theta[1] is maximal limit for random generation theta"
        config["theta"]=theta
        assert len(phi) == 2, "phi[0] is minimal limit and phi[1] is maximal limit for random generation of phi."
        config["phi"]=phi
        if same_scale!=None:
            assert type(same_scale)==bool, "Has to be bool or None; same_scale sets the bool of same_scale in getRandomJsonData. If it is None bool is set randomly." 
        config["same_scale"]=same_scale
        assert len(scale) == 2, "scale[0] is minimal limit and scale[1] is maximal limit for random generation of the scale of the cubiods."
        config["scale"]=scale    
        if enable_many_arms!=None:
            assert len(enable_many_arms) == 2, "Has to be list of length 2 or type None; enable_many_arms defines boundaries for how many arms could be created in getRandomJsonData. This means that there is a chance that the crane splits up in the given range. If it is None then there will be only one arm." 
            assert enable_many_arms[0] > 0, "enable_many_arms has to be 1 or greater to even create one Arm."
            assert enable_many_arms[1] > 0, "enable_many_arms has to be 1 or greater to even create one Arm."
        config["enable_many_arms"] = enable_many_arms

        
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
        
    def create_random_parameters(self ,Seed=None):
        dictionary={}
        np.random.seed(Seed)
        dictionary["seed"] = np.random.get_state()
        TotalSegments = np.random.randint(self.config["totalSegments"][0],self.config["totalSegments"][1])

        DirectionalLightTheta = np.random.uniform(self.config["DirectionalLightTheta"][0], self.config["DirectionalLightTheta"][1])
        DirectionalLightIntensity = np.random.uniform(self.config["DirectionalLightIntensity"][0], self.config["DirectionalLightIntensity"][1])

        PointLightRadius = []
        PointLightPhi = []
        PointLightTheta = []
        PointLightIntensity=[]
        PointLightRange = []
        P_R=[]
        P_G=[]
        P_B=[]
        P_A=[]
        if self.config["totalPointLights"] == None:
            TotalPointLights = 0
        else:        
            TotalPointLights = np.random.randint(self.config["totalPointLights"][0],self.config["totalPointLights"][1])
            if(self.config["samePointLightColor"]==None):
                Same_PLcolor = bool(np.random.randint(2,dtype=int))
            else:
                Same_PLcolor = self.config["samePointLightColor"]

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
            PointLightRadius=np.random.uniform(self.config["PointLightsRadius"][0],self.config["PointLightsRadius"][1],TotalPointLights).tolist()
            PointLightRange=np.random.uniform(self.config["PointLightsRange"][0],self.config["PointLightsRange"][1],TotalPointLights).tolist()
            PointLightPhi=np.random.uniform(self.config["PointLightsPhi"][0],self.config["PointLightsPhi"][1],TotalPointLights).tolist()
            PointLightTheta=np.random.uniform(self.config["PointLightsTheta"][0],self.config["PointLightsTheta"][1],TotalPointLights).tolist()
            PointLightIntensity=np.random.uniform(self.config["PointLightsIntensity"][0],self.config["PointLightsIntensity"][1],TotalPointLights).tolist()
                
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
        if self.config["totalPointLights"] == None:
            TotalSpotLights = 0
        else:        
            TotalSpotLights = np.random.randint(self.config["totalSpotLights"][0],self.config["totalSpotLights"][1])
            if(self.config["sameSpotLightColor"]==None):
                Same_SLcolor = bool(np.random.randint(2))
            else:
                Same_SLcolor = self.config["sameSpotLightColor"]
                
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
            SpotLightRadius=np.random.uniform(self.config["SpotLightsRadius"][0],self.config["SpotLightsRadius"][1],TotalSpotLights).tolist()
            SpotLightRange=np.random.uniform(self.config["SpotLightsRange"][0],self.config["SpotLightsRange"][1],TotalSpotLights).tolist()
            SpotLightPhi=np.random.uniform(self.config["SpotLightsPhi"][0],self.config["SpotLightsPhi"][1],TotalSpotLights).tolist()
            SpotLightTheta=np.random.uniform(self.config["SpotLightsTheta"][0],self.config["SpotLightsTheta"][1],TotalSpotLights).tolist()
            SpotLightIntensity=np.random.uniform(self.config["SpotLightsIntensity"][0],self.config["SpotLightsIntensity"][1],TotalSpotLights).tolist()
            SpotLightsAngle=np.random.uniform(self.config["SpotLightsAngle"][0],self.config["SpotLightsAngle"][1],TotalSpotLights).tolist()
        
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

        if(self.config["same_theta"]==None):
            Same_Theta = bool(np.random.randint(2))
        else:
            Same_Theta = self.config["same_theta"]

        Theta = []
        if(Same_Theta):
            if self.config["theta"]==None:
                Theta.append(np.random.uniform(0,360/TotalSegments))
        else:
            if self.config["theta"]==None:
                Theta=np.random.uniform(0,360/TotalSegments,TotalSegments-1).tolist()
            else:
                Theta=np.random.uniform(self.config["theta"][0],self.config["theta"][1],TotalSegments-1).tolist()
                    
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
        
        if(self.config["same_scale"]==None):
            Same_Scale = bool(np.random.randint(2))
        else:
            Same_Scale = self.config["same_scale"]
        if(Same_Scale):
            Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1])
        else:
            Scale = np.random.uniform(self.config["scale"][0],self.config["scale"][1],TotalSegments).tolist()
        Phi=np.random.uniform(self.config["phi"][0],self.config["phi"][1])
        
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
        
    def get_json_string_from_parameters(self, dictionary):
        return self.uc.writeJsonCrane(totalSegments=dictionary["totalSegments"], same_scale=dictionary["same_scale"], scale=dictionary["scale"], same_theta=dictionary["same_theta"], theta=dictionary["theta"], phi=dictionary["phi"], totalArms_Segment=dictionary["totalArms_Segment"], same_material=dictionary["same_material"], metallic=dictionary["metallic"], smoothness=dictionary["smoothness"], r=dictionary["r"], g=dictionary["g"], b=dictionary["b"], a=dictionary["a"], CameraRes_width=520, CameraRes_height=520, Camera_FieldofView=80, CameraRadius=13, CameraTheta=90, CameraPhi=0, CameraVerticalOffset=0, 
            totalPointLights=dictionary["totalPointLights"], same_PointLightsColor=dictionary["same_PointLightsColor"], PointLightsColor_r=dictionary["PointLightsColor_r"], PointLightsColor_g=dictionary["PointLightsColor_g"], PointLightsColor_b=dictionary["PointLightsColor_b"], PointLightsColor_a=dictionary["PointLightsColor_a"], PointLightsRadius=dictionary["PointLightsRadius"], PointLightsTheta=dictionary["PointLightsTheta"], PointLightsPhi=dictionary["PointLightsPhi"], PointLightsIntensity=dictionary["PointLightsIntensity"], PointLightsRange=dictionary["PointLightsRange"], 
            totalSpotLights=dictionary["totalSpotLights"], same_SpotLightsColor=dictionary["same_SpotLightsColor"], SpotLightsColor_r=dictionary["SpotLightsColor_r"], SpotLightsColor_g=dictionary["SpotLightsColor_g"], SpotLightsColor_b=dictionary["SpotLightsColor_b"], SpotLightsColor_a=dictionary["SpotLightsColor_a"], SpotLightsRadius=dictionary["SpotLightsRadius"], SpotLightsTheta=dictionary["SpotLightsTheta"], SpotLightsPhi=dictionary["SpotLightsPhi"], SpotLightsIntensity=dictionary["SpotLightsIntensity"], SpotLightsRange=dictionary["SpotLightsRange"],SpotAngle=dictionary["SpotAngle"],
            DirectionalLightTheta=dictionary["DirectionalLightTheta"], DirectionalLightIntensity=dictionary["DirectionalLightIntensity"])

    def parameter_apperence1_articluation2(self, param1, param2):
        param1["same_theta"] = param2["same_theta"]
        param1["same_scale"] = param1["same_scale"]
        param1["scale"]=param2["scale"]
        param1["phi"]=param2["phi"]
        param1["totalArmsSegment"]=param2["totalArmsSegment"]
        if param1["totalSegments"]>param2["totalSegments"]:
            param1["theta"]=param2["theta"]
        else:
            for i in range(param1["totalSegments"]):
                param1["segments"][i]["scale"]=param2["segments"][i]["scale"]
                param1["segments"][i]["theta_deg"]=param2["segments"][i]["theta_deg"]
            for i in range(param1["totalSegments"], param2["totalSegments"]):
                param1["segments"].append({"theta_deg":param2["segments"][i]["theta_deg"],"scale":param2["segments"][i]["scale"],"material":param2["segments"][param1["totalSegments"]-1]["material"]})                   
        param1["totalSegments"]=param2["totalSegments"]
        return param1

    def CombinationOfJsonData_apperence1_articluation2(self,jsondata,jsondata2):
        jsondata1 = jsondata
        jsondata1["same_theta"]=jsondata2["same_theta"]
        jsondata1["phi"]=jsondata2["phi"]
        jsondata1["totalArmsSegment"]=jsondata2["totalArmsSegment"]
        if jsondata1["totalSegments"]>jsondata2["totalSegments"]:
            for i in range(jsondata2["totalSegments"]):
                jsondata1["segments"][i]["scale"]=jsondata2["segments"][i]["scale"]
                jsondata1["segments"][i]["theta_deg"]=jsondata2["segments"][i]["theta_deg"]

        else:
            for i in range(jsondata1["totalSegments"]):
                jsondata1["segments"][i]["scale"]=jsondata2["segments"][i]["scale"]
                jsondata1["segments"][i]["theta_deg"]=jsondata2["segments"][i]["theta_deg"]
            for i in range(jsondata1["totalSegments"], jsondata2["totalSegments"]):
                jsondata1["segments"].append({"theta_deg":jsondata2["segments"][i]["theta_deg"],"scale":jsondata2["segments"][i]["scale"],"material":jsondata1["segments"][jsondata1["totalSegments"]-1]["material"]})                   
        jsondata1["totalSegments"]=jsondata2["totalSegments"]
        return jsondata1

    #get 3 images with two of them different random parameters and one with articulation of img1 and apperence of img2 
    def getPlot_of_3Images_withCombination_of_twoParameters(self):
        dict1 = self.get_example(1)
        
        dict2 = self.get_example(2)
        jsondata3 = data.CombinationOfJsonData_apperence1_articluation2(dict1["jsondata"],dict2["jsondata"])
        jsonstring3 = json.dumps(jsondata3)
        with open('datajson_combi.json', 'w') as f:
            f.write(jsonstring3)

        dict3 = data.get_crane(jsonstring3)
        #plot the three images
        matplotlib.use('TkAgg')
        fig, (pic1, pic3, pic2) = plt.subplots(3,1)
        fig.suptitle('combination of apperence and articulation')
        plt.subplots_adjust(hspace=0.2)

        pic1.set_title('app. 1 and artic. 1')
        pic1.imshow(dict1["image"])
        pic1.axis("off")

        pic2.set_title('app. 2 and artic. 2')
        pic2.imshow(dict2["image"])
        pic2.axis("off")

        pic3.set_title('combination of app. 1 and artic. 2')
        pic3.imshow(dict3["image"])
        pic3.axis("off")
        fig.savefig("figures/disentangle/fig_"+str(np.round(jsondata3["phi"]*1000))+".png")
    
    def get_random_CameraAngle(self,jsondata):
        #use gaussian distribution for theta around 90 degrees
        jsondata["camera"]["theta_deg"] = np.random.randint(self.config["theta"][0],self.config["theta"][1],float)
        jsondata["camera"]["phi_deg"] = np.random.randint(self.config["phi"][0],self.config["phi"][1],float)
        return jsondata
    #fix theta position
    def change_articulation_theta(self, parameters, start_value, end_value, amount_of_pics, theta_pos = None):
        new_theta = np.linspace(start_value, end_value, amount_of_pics)
        newDict = []
        parameters["CameraRadius"] = 15
        if(theta_pos==None):
            for i in range(amount_of_pics):
                New_Theta = []                
                for j in range(parameters["totalSegments"]-1):
                    New_Theta.append(new_theta[i])
                parameters["theta"] = New_Theta
                json_string = self.get_json_string_from_parameters(parameters)
                img = self.uc.reciveImage(json_string)
                newDict.append({"parameters":parameters, "jsondata":json_string,"image":img})
    
        else:    
            assert type(theta_pos) == int , "Dataset in change_articulation_theta: wrong input theta_pos has to be an integer or None; integer chooses position of manipulated theta, if None all theta are going to change the same."
            assert theta_pos < parameters["totalSegments"] , "Dataset in change_articulation_theta: wrong input theta_pos has to be smaller than the amount of segments."
            New_Theta = []
            if parameters["same_theta"]==True:
                for i in range(parameters["totalSegments"]):
                    New_Theta.append(parameters["theta"][0]) 
                    parameters["same_theta"]==False
                print("INFO: changing only one theta while same_theta is true")
            else:
                New_Theta = parameters["theta"]
            for i in range(amount_of_pics):
                print("i: " + str(i) + " new_theta: " + str(new_theta) + " theta_pos: " + str(theta_pos) + " New_Theta: " + str(New_Theta) )
                New_Theta[theta_pos] = new_theta[i]
                parameters["theta"] = New_Theta          
    
                json_string = self.get_json_string_from_parameters(parameters)
                img = self.uc.reciveImage(json_string)
                newDict.append({"parameters":parameters, "jsondata":json_string,"image":img})
        return newDict

    def plot_2Images_inSubplots(self,dict1,dict2):
        matplotlib.use('TkAgg')
        fig, (pic1, pic2) = plt.subplots(1,2)
        
        pic1.imshow(dict1["image"])
        pic1.axis("off")
        
        pic2.imshow(dict2["image"])
        pic2.axis("off")
        #plt.savefig("figures/differentAngle/fig_"+str(np.round(dict1["jsondata"]["phi"]*100))+".png")
        plt.show()

    def plot_Images_inSubplots(self,dicts):
        matplotlib.use('TkAgg')
        number = int(len(dicts))
        if(number%2==0):
            if(number==2):
                fig, ax = plt.subplots(1,number))

                for i in range(number):    
                    ax[i].imshow(dicts[i]["image"])
                    ax[i].axis("off")
            else:
                fig, ax = plt.subplots(2,math.ceil(number/2))  
                for j in range(2):
                    for i in range(math.ceil(number/2)):
                        if(i+j*int(number/2)<int(number)):
                            ax[j,i].imshow(dicts[i+j*int(number/2)]["image"])
                            ax[j,i].axis("off")
        else:
            if(number>5):    
                fig, ax = plt.subplots(3,math.ceil(number/3))
                for j in range(3):
                    for i in range(math.ceil(number/3)):
                        if(i+j*int(number/2)<int(number)):
                            ax[j,i].imshow(dicts[i+j*int(number/3)]["image"])
                            ax[j,i].axis("off")
            else:
                if(number==1):
                    plt.imshow(dicts[0]["image"])
                    plt.axis("off")
                else:
                    fig, ax = plt.subplots(1,int(number))
                    for i in range(number):    
                        ax[i].imshow(dicts[i]["image"])
                        ax[i].axis("off")
        plt.show()

    def plot_combined_Images(self,dicts):
        numb = len(dicts)
        if (numb%2):
            while numb > 5:
                numb_y += 1
                numb -= 5
            

    def get_example(self,idx=None):
        random_parameters = self.create_random_parameters()
        #with open('Parameter/random_parameters'+str(idx) + '.json', 'w') as f:
        #    f.write(para_string)
        jsonstring = self.get_json_string_from_parameters(random_parameters)
        img = self.uc.reciveImage(jsonstring)
        if idx==None:
            idx=np.random.randint(0,200)
        newDict = {"label":idx,"parameters":random_parameters, "jsondata":jsonstring,"image":img}
        return newDict
        
    def get_crane(self,jsonstring):
        img = self.uc.reciveImage(jsonstring)
        jsondata = json.loads(jsonstring)
        newDict = {"jsondata":jsondata,"image":img}
        return newDict
    
    def exit(self):
        ### sends end request to Unity, closes TCP connection. Called when used in with statement"""
        self.uc.exit()
        print("Exit socket connection to unity.")


        
#for i in range(3):    
#    dict1 = data[2*i+0]
#    dict2 = data[2*i+1]
#    data.plot_2Images_inSubplots(dict1,dict2)
'''
dicts = []
for i in range(1):
    print("Image number: "+str(i))
    dicts.append(data.get_example())
print(len(dicts))
'''

data = DataSetCrane(use_unity_build=False)
dicts = []
for i in range(2):
    dicts.append(data.get_example())
#dicts = data.change_articulation_theta(parameter, start_value = 0,end_value = 25,amount_of_pics = 20)#, theta_pos=2 )#parameter["totalSegments"]-2)
data.exit()
#data.plot_Images_inSubplots(dicts)
#data.plot_2Images_inSubplots(dict1,dict2)
img1 = dicts[0]["image"]
img2 = dicts[1]["image"]

plt.imshow(img)
plt.show()