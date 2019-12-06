# Python Unity Images

# Image Data set of articulated cuboids
This tool can create many images with articulated cuboids in different scenes.
These images are labeled and can be reused and manipulated at specific features as for example the articulatioon or the apperence which can be changed individualy without changing other aspects of the image.
The framework and the rendering are achieved through the game engine Unity 3D which communicates with the python scripts via a TCP Socket connnection.
Unity receives parameters from the script to build up a specific scene and sends the rendered image back to python.

This repository was created in a project at the research group Computer Vision at the Heidelberg Collaboratory for Image processing.   

## Documentation
The documentation of the python code can be found here: <https://python-unity-images.readthedocs.io/en/latest/>. 
Additionaly a detailed report as pdf can be found in this repository at the root directory: "Documentation.pdf"

## Example
The following code represents a simple example how to use this project.
This code creates and plots 10 randomly generated images. 
```python
import dataset
data = dataset.dataset_cuboids()
data.set_config(total_cuboids=[3,4],same_theta=True,same_material=True)
dictionaries = []
for i in range(10):
    dictionaries.append(data.get_example(save_para=True, save_image=True))
data.exit()
data.plot_images(dictionaries, images_per_row=5, save_fig=True)
```

* In the first line the file dataset.py is imported.
* The first thing you want to do is to initialize an object of the class ``dataset_cuboids()``.
    * This starts Unity and connects to it with code from ``client.py``. 
* After this you can use it as you want. 
* In this exampel we create random images with the function ``get_example()``, but first we want to personalize our boundaries for the randomly generated images.
* The intervals, which define in what range a parameter can be generated are saved in the config of the instance of the class ``dataset_cubiods()``.
* Every instance has a default config initialized wich can be change with the function ``set_config()``.
    * In our example we choose with the argument ``total_cuboids`` that only three or four cuboids are created in every scene.
    * with ``same_theta`` 
* 
    * This returns an dictionnary with the keys "index", "parameters" and "image".
    * The argumets ``save_para`` and ``save_image`` are ``True``. This means that the parameters of the created scene are saved at ``data/parameters`` as well as the image at ``data/images``.
    * This is done ten times and every returned dictionary is save in a list.
* If we are done with requesting images you should always close and exit the Unity application and the connection with ``exit()``.
* At last we want to have a look at the created images with the function ``plot_images()``.
    * The argument ``images_per_row = 5`` means that the images will be plotted in the shape: 5 Images horizontal and 2 rows vertically images.
    ``save_fig = True`` which means that the resulting figure is saved at ``data/figures``.
