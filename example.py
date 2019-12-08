import dataset
data = dataset.dataset_cuboids(dataset_name="example", unique_data_folder=True)
data.set_config(total_cuboids=[3,4],same_theta=True,same_material=True)
dicts = []
for i in range(10):
    dicts.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dicts, images_per_row=5, save_fig=True)
