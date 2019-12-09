# Python Unity Images

# Image Data set of articulated cuboids
This tool can create many images with articulated cuboids in different scenes.
These images are labeled and can be reused and manipulated at specific features as for example the articulatioon or the apperence which can be changed individualy without changing other aspects of the image.
The framework and the rendering are achieved through the game engine Unity 3D which communicates with the python scripts via a TCP Socket connnection.
Unity receives parameters from the script to build up a specific scene and sends the rendered image back to python.

This repository was created in a project at the research group Computer Vision at the Heidelberg Collaboratory for Image processing.   

<img src="https://github.com/R-Haecker/python_unity_images/raw/master/data/dataset/2019-12-09_00:04__simple_example/images/image_index_3.png" height="210" width="210">
<img src="https://github.com/R-Haecker/python_unity_images/raw/master/data/dataset/advanced_example/images/image_index_1.png" height="210" width="210">
<img src="https://github.com/R-Haecker/python_unity_images/raw/master/data/dataset/advanced_example/images/image_index_9.png" height="210" width="210">

## Documentation
The documentation of the python code can be found here: <https://python-unity-images.readthedocs.io/en/latest/>. 
Additionaly a detailed report as pdf can be found in this repository at the root directory: "Documentation.pdf"

## Examples
### 1) Simple Example 
The following code represents a simple example how to use this project.
This code creates and plots eight randomly generated images. 
```python
import dataset
data = dataset.dataset_cuboids(dataset_name = "simple_example")
dictionaries = []
for i in range(8):
    dictionaries.append(data.get_example(save_para = True, save_image = True))
data.exit()
data.plot_images(dictionaries, save_fig = True)
```

* In the first line the file dataset.py is imported.
* The first thing you want to do is to initialize an object of the class ``dataset_cuboids()``.
    * This starts Unity and connects to it with code from ``client.py``. 
    * make sure that the string ``dataset_name`` does not contain any white spaces.
* After that you can use it as you desire. 
* In this exampel we create random images with the function ``get_example()``.
    * This function returns an dictionnary with the keys: ``index``, ``parameters`` and ``image``.
    * The argumets ``save_para`` and ``save_image`` are ``True``. This means that the parameters of the created scene are saved inside a unique folder for your dataset. This folder can be found in ``data/dataset/``, it is named with a time stamp and the name of your dataset specified in ``dataset_name``.
    The parameters and and images are saved separately. You can have a look at the saved data of the example above.
    * This is done eight times and every returned dictionary is save in a list.
* If we are done with requesting images you should always close and exit the Unity application and the connection with ``exit()``.
* At last we want to have a look at the created images with the function ``plot_images()``.
    * ``save_fig = True`` means that the resulting figure is saved at ``data/figures``.

That is it we have successfully created and saved images with a ground truth. 


Here is the figure of the plotted images:

![alt text](https://github.com/R-Haecker/python_unity_images/raw/master/data/figures/fig_simple_example__from_index_0_to_index_7.png)


### 2) Advanced Example

```python
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
```

* The first block of code is pretty similar to the simple example
* The initialization differs by one additional argument.
    * ``unique_data_folder = True`` means that if you later save images or parameters your personal dataset folder will not include a time stamp. This enables another instance as ``data2`` with the same ``dataset_name`` to use the same dataset folder to store more and different images and parameters.
    * The folder in ``data/dataset/`` will now just be named:  ``advanced_example``.
* Since the simple example was executed befor this example the index is currently at nine. It is stored externally in ``data/python/index.txt``.
* With the function ``reset_index()`` we now set it back to zero. Keep in mind that if you choose to set ``unique_data_folder = True`` and reset the index you can overwrite your old data.
* In the function ``plot_images()`` we specified the shape of the figure.
    * Since we created 10 images and ``images_per_row = 5``, we now plot 2 rows of each 5 images next to each other.

* Now we create another ``dataset_cuboids`` instance and save into the same dataset folder. This block of code can also be executed in a different python file. 
* We will also use the function ``get_example()``, but first we want to personalize our boundaries and settings for the randomly generated images to create different images.
* The intervals, which define in what range a parameter can be generated are saved in the config of the instance of the class ``dataset_cubiods()``.
* Every instance has a default config initialized wich can be changed with the function ``set_config()``. You should habe a look into the [Documentation](https://python-unity-images.readthedocs.io/en/latest/) at the function ``set_config`` and to learn what the specific parameters mean, you should go to the function ``write_json_crane()`` in the ``client_communicator_to_unity`` class.  
    * In our example we choose with the argument ``total_cuboids = [2,3]`` that only two or three cuboids are created on the main "branch".
    * with ``same_theta = False`` we specified that all angels between cuboids should be different.
    * with ``totalPointLights=None`` there will not be any Pointlights. 
    * with ``totalSpotLights=None`` there will not be any Spotlights as well.
    * with ``DirectionalLightTheta=[80,90]`` we specify that the only light the "Sun" will have the polar angle theta between 80 and 90 degrees which means there will be dawn. Note that the common spherical coordinates are implemented as seen [here](https://en.wikipedia.org/wiki/Spherical_coordinate_system).  
* This time when using the function ``plot_images()`` we set ``show_index = False`` to not show the index displayed on top of the images.

We now created a dataset with two different configs in the same dataset folder.

Here is the figure of images with the default config:

![alt text](https://github.com/R-Haecker/python_unity_images/raw/master/data/figures/fig_advanced_example__from_index_0_to_index_9.png "Plot of images with default config.")


Here is the figure of images with the modified config:

![alt text](https://github.com/R-Haecker/python_unity_images/raw/master/data/figures/fig_advanced_example__from_index_10_to_index_19.png "Plot of images with personal config")
