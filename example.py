import dataset
data = dataset.dataset_cuboids(dataset_name = "test_gitignore", unique_data_folder = True)
dictionaries = []
for i in range(10):
    dictionaries.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dictionaries, images_per_row=5, save_fig=True)