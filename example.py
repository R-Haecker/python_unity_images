import dataset
data = dataset.dataset_cuboids(use_unity_build=True,debug_log=False)
dicts = []
for i in range(3):
    dicts.append(data[i])
data.exit()
data.plot_images(dicts)