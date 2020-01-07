import dataset
data = dataset.dataset_cuboids(dataset_name = "first_ae", unique_data_folder = True, from_home_dataset_folder="/Documents/auto_encoder/data", use_unity_build=True, debug_log=True)
dictionaries = []
data.reset_index()
#data.set_config(total_cuboids=[2,12],branches=[1,6], same_material=False,CameraRadius=12, Camera_FieldofView = 100)
data.set_config(same_scale=True, scale=2, total_cuboids=2, phi=[0,360], branches=None, same_theta = True, theta=90, 
specify_material=True, same_material=True, r=0.1,g=0,b=1,a=1,metallic=1,smoothness=0.5,Camera_FieldofView=90,CameraRadius=5,CameraTheta=90,CameraPhi=0, Camera_solid_background=True,
totalPointLights=[10,15],same_PointLightsColor=True,PointLightsIntensity=[15,20],PointLightsColor_r=[0.9,1],PointLightsColor_g=[0.9,1],PointLightsColor_b=[0.9,1], totalSpotLights=None, 
DirectionalLightTheta=70, DirectionalLightIntensity=3.5)
for i in range(10):
    dictionaries.append(data.get_example(save_image=True))
    #parameters_to_finished_data(parameters = data.create_parameters(DirectionalLightTheta=80),save_image=True))#theta=10,scale=2,phi=45)))
    #data.set_config(same_scale=True, specify_scale=True,scale=2,total_cuboids=2, phi=45, branches=None, same_theta=True, theta=20,specify_theta=True,specify_material=True, same_material=True, r=0.3,g=0,b=1,a=1,metallic=0.5,smoothness=0.5,CameraRadius=5,CameraTheta=90,CameraPhi=10*i, totalPointLights=None, totalSpotLights=None, DirectionalLightTheta=80)
    #dictionaries.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dictionaries, images_per_row=10, save_fig=True, show_index=False)
