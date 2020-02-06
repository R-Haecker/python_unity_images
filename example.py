import dataset
data = dataset.dataset_cuboids(dataset_name = "datase_vae_max_random", unique_data_folder = False, from_home_dataset_directory="/Desktop/data_set/", 
                                use_unity_build=False, debug_log=True)
dictionaries = []
#data.reset_index()
data.set_config(CameraRadius=10, request_pose=True)

'''data.set_config(same_scale=True, scale=2, total_cuboids=5, phi=[0,360], branches=[1,5], same_theta = True, theta=90,
specify_material=True, same_material=True, r=0.1,g=0,b=1,a=1,metallic=1,smoothness=0.5,Camera_FieldofView=90,CameraRadius=15,CameraTheta=90,CameraPhi=0, Camera_solid_background=True,
totalPointLights=[2,15],same_PointLightsColor=True,PointLightsIntensity=[15,20],PointLightsColor_r=[0.9,1],PointLightsColor_g=[0.9,1],PointLightsColor_b=[0.9,1], totalSpotLights=None, 
DirectionalLightTheta=70, DirectionalLightIntensity=3.5)
'''
for i in range(10):
    dictionaries.append(data.get_example(save_image=True))
    #parameters_to_finished_data(parameters = data.create_parameters(DirectionalLightTheta=80),save_image=True))#theta=10,scale=2,phi=45)))
    #data.set_config(same_scale=True, specify_scale=True,scale=2,total_cuboids=2, phi=45, branches=None, same_theta=True, theta=20,specify_theta=True,specify_material=True, same_material=True, r=0.3,g=0,b=1,a=1,metallic=0.5,smoothness=0.5,CameraRadius=5,CameraTheta=90,CameraPhi=10*i, totalPointLights=None, totalSpotLights=None, DirectionalLightTheta=80)
    #dictionaries.append(data.get_example(save_para=True, save_image=True))
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
import matplotlib.pyplot as plt
'''
plt.imshow(dictionaries[0]["pose"])
plt.show()
plt.imshow(dictionaries[0]["image"])
plt.show()'''
data.plot_images(dictionaries, images_per_row=5, save_fig=True, show_index=False)

data.exit()
