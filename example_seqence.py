import dataset
import time
data = dataset.dataset_cuboids(dataset_name = "non", unique_data_folder = False, dataset_directory="/Documents/data_set/", 
                                use_unity_build=True, debug_log=False)
data.set_config(same_theta=True, same_scale=True, same_material=True, total_cuboids=2, branches = None, scale=1.5, theta = 45, phi=[0,360], CameraPhi=0,
                r=[0.1,0.11],g=[0.3,0.31],b=[0.99,1], metallic=[0.7,0.71], smoothness=[0.4,0.41], totalPointLights=None,totalSpotLights=None, 
                CameraRadius=4, DirectionalLightTheta=45, DirectionalLightIntensity=3)
dict_ = []
dict_ = data.create_image_sequnces(key_list = ["phi"], num_list = [6], alpha_parameter = None, return_dict = True, save_para = True, save_image = True)
data.exit()
data.plot_images(dicts=dict_, images_per_row=10,show_index=False) 