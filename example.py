import dataset
data = dataset.dataset_cuboids(dataset_name = "non", unique_data_folder = False, from_home_dataset_directory="/Documents/data_set/", 
                                use_unity_build=True, debug_log=False)
dictionaries = []
#data.reset_index()
#data.load_config(file_name="here.json")#file_name="2020-02-22_19:13:47_config(1).json")

#data.set_config(total_cuboids=2, branches = None, same_theta = True, CameraRadius=5, request_pose=False, theta=45,)

data.set_config(save_config = True, request_pose = False, request_three = False, same_scale=True, scale=[1,2.5], total_cuboids=[2,4], phi=[0,360], specify_branches=False, branches=None, same_theta=None, theta=None, 
    same_material=True, specify_material=False, r=[0,1], g=[0,1], b=[0,1], a=1, metallic=[0.4,1], smoothness=[0,0.6], CameraRes_width= 512, CameraRes_height=512, Camera_FieldofView=90, CameraRadius = None, CameraTheta = 90, CameraPhi = 0, CameraVerticalOffset = None, Camera_solid_background = False,
    totalPointLights=[0,4], PointLightsRadius=[5,20], PointLightsPhi=[0,360], PointLightsTheta=[0,90], PointLightsIntensity=[7,17], PointLightsRange=[5,25], same_PointLightsColor=None, PointLightsColor_r=[0,1], PointLightsColor_g=[0,1], PointLightsColor_b=[0,1], PointLightsColor_a=[0.5,1],
    totalSpotLights=[0,4], SpotLightsRadius=[5,20], SpotLightsPhi=[0,360], SpotLightsTheta=[0,90], SpotLightsIntensity=[5,15], SpotLightsRange=[5,25], SpotAngle=[5,120], same_SpotLightsColor=None, SpotLightsColor_r=[0,1], SpotLightsColor_g=[0,1], SpotLightsColor_b=[0,1], SpotLightsColor_a=[0.5,1],
    DirectionalLightTheta = [0,90], DirectionalLightIntensity = [0.5,1.5], specify_scale=False, specify_theta=False)

for i in range(100):
    dictionaries.append(data.get_example(save_image = True, save_para = True, return_dict = True))

data.plot_images(dictionaries,images_per_row=10,show_index=False)
data.exit()


'''
data.set_config(same_scale=True, scale=3, total_cuboids=3, phi=[0,360], branches=None, same_theta = True, theta=90, 
specify_material=True, same_material=True, r=0.1,g=0,b=1,a=1,metallic=1,smoothness=0.5,Camera_FieldofView=90,CameraRadius=5,CameraTheta=90,CameraPhi=0, Camera_solid_background=True,
totalPointLights=[1,15],same_PointLightsColor=True,PointLightsIntensity=[15,20],PointLightsColor_r=[0.9,1],PointLightsColor_g=[0.9,1],PointLightsColor_b=[0.9,1], totalSpotLights=None, 
DirectionalLightTheta=70, DirectionalLightIntensity=3.5)
for i in range(10):
    dictionaries.append(data.get_example(save_image=True))

data.load_config(index_config=1)
for i in range(10):
    dictionaries.append(data.get_example(save_image=True))

data.load_config(index_config=0)
for i in range(10):
    dictionaries.append(data.get_example(save_image=True))
'''
#import matplotlib.pyplot as plt
'''
plt.imshow(dictionaries[0]["pose"])
plt.show()
plt.imshow(dictionaries[0]["image"])
plt.show()'''
#data.plot_images(dictionaries, images_per_row=5, save_fig=True, show_index=True)

# /export/scratch/rhaecker/datasets/
