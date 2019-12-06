import dataset
data = dataset.dataset_cuboids(use_unity_build=True,debug_log=False)
#data.reset_index()
dicts = []
for i in range(50):
    dicts.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dicts, images_per_row=5, save_fig=True)