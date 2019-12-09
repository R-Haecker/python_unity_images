import dataset
data = dataset.dataset_cuboids(dataset_name = "advanced_example", unique_data_folder = False)
data.reset_index()
dictionaries = []
for i in range(10):
    dictionaries.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dictionaries, images_per_row=5, save_fig=True)

data2 = dataset.dataset_cuboids(dataset_name = "advanced_example", unique_data_folder = False)
data2.set_config(total_cuboids=[2,3],same_theta=False, DirectionalLightTheta=[80,90], totalPointLights=None, totalSpotLights=None)
dictionaries2 = []
for i in range(10):
    dictionaries2.append(data2.get_example(save_para=True, save_image=True))
data2.exit()
data2.plot_images(dictionaries2, images_per_row=5, save_fig=True, show_index=False)
