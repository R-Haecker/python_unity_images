import dataset
data = dataset.dataset_cuboids(dataset_name = "test_gitignore", unique_data_folder = True)#,use_unity_build=False)
data.set_config(same_scale=True, scale=2,total_cuboids=2, phi=0, branches=None, same_theta = True, theta=20, specify_material=True, same_material=True, r=0.3,g=0,b=1,a=1,metallic=0.5,smoothness=0.5,CameraRadius=5,CameraTheta=90,CameraPhi=[0,180], totalPointLights=None, totalSpotLights=None, DirectionalLightTheta=80)
dictionaries = []
for i in range(10):
    #dictionaries.append(data.parameters_to_finished_data(parameters = data.create_parameters()))#theta=10,scale=2,phi=45)))
    #data.set_config(same_scale=True, specify_scale=True,scale=2,total_cuboids=2, phi=45, branches=None, same_theta=True, theta=20,specify_theta=True,specify_material=True, same_material=True, r=0.3,g=0,b=1,a=1,metallic=0.5,smoothness=0.5,CameraRadius=5,CameraTheta=90,CameraPhi=10*i, totalPointLights=None, totalSpotLights=None, DirectionalLightTheta=80)
    dictionaries.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dictionaries, images_per_row=5, save_fig=False)