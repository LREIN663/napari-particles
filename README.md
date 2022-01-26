# napari-particles (WIP)

A particle layer for napari (super rough draft)

----------------------------------

Extension of Napari Particles that provides a dock widget within Napari into which .hdf5 (Picasso), .smlm, .csv (Thunderstorm) and .h5 files can be imported and rendered via drag and drop. 

## Installation

For the time being, the easiest way to install is as follows: 

create an enviroment, e.g. using anaconda terminal with 

```
conda create --name napari-particles
activate napari-particles
```

clone this repository using and install it using 

```
git clone https://github.com/LREIN663/napari-particles
cd napari-particles
pip install -r requirements.txt
```

## Usage

active the created enviroment in the anaconda terminal and start napari

```
activate napari-particles
napari
```

Now under plugins click napari-particles: SMLMQW and the dock widget should open. Now you can either use the import button or simply drag the file you are trying to open onto the list.


## Usage (Original Repo)


```python
import numpy as np
import napari
from napari_particles.particles import Particles
from napari_particles.filters import ShaderFilter

coords = np.random.uniform(0,100,(10000,3))
coords[:,0] *=.1
size   = np.random.uniform(.4, 1, len(coords))
values = np.random.uniform(0.2,1, len(coords))

layer = Particles(coords,
                size=size,
                values=values,
                colormap='Spectral',
                filter = ShaderFilter('gaussian'))

layer.contrast_limits=(0,1)
v = napari.Viewer()
layer.add_to_viewer(v)
v.dims.ndisplay=3
v.camera.perspective=80.0
napari.run()

```





## Examples Scripts

in `./examples`

### Basic 

```
python test_particles.py
```


### SMLM

If you have a localization csv file in the following format (with "\t" as separator)

```
"frame" "x [nm]"        "y [nm]"        "z [nm]"        "uncertainty_xy [nm]"   "uncertainty_z [nm]"
2       23556.7 2045    -97     2.5     5
2       5871.4  2853.1  -306    2.2     4.5
2       24767.5 3298    -267    1.7     3.5
2       22070.8 3502.8  -334    1       2
....
```


you can render it like so:

```
python test_smlm.py -i data.csv
```
