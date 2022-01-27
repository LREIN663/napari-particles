from tkinter import filedialog as fd
from tkinter import Tk
import napari
from napari_particles.particles import Particles
from importer import *


class dataset():
    def __init__(self, locs=None, zdim=False, parent=None, name=None, pixelsize=130):
        self.locs = locs
        self.locs_backup = locs  # Needed if dataset is cut with sliders and then you want the data back
        self.zdim = zdim
        self.layer = None
        self.name = name
        self.sigma = None
        self.pixelsize = pixelsize
        self.parent = parent
        self.calc_sigmas()
        self.camera_center = None
        self.colormap = None

    def calc_sigmas(self):
        if self.parent.Brenderoptions.currentText() == "variable gaussian":
            sigma = float(self.parent.Esigma.text()) / np.sqrt(self.locs.photons/10) / 2.354 *1E-2
            sigmaz = float(self.parent.Esigma2.text()) / np.sqrt(self.locs.photons/10) / 2.354 *1E-2
            self.sigma = np.swapaxes([sigmaz, sigma, sigma], 0, 1)
            print(f"Sigma XY {sigma[0]}")
        else:
            self.sigma= float(self.parent.Esigma.text()) / 2.354 *1E-2
            print(f"Sigma XYZ {self.sigma}")

    def update_locs(self):
        LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
        LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
        self.locs = self.locs_backup
        x0, x1 = self.parent.Sy.getRange()  # x and y are swapped in napari
        y0, y1 = self.parent.Sx.getRange()
        xscale = max(self.locs.x) - min(self.locs.x)
        yscale = max(self.locs.y) - min(self.locs.y)

        x0 = x0 * xscale / 100
        x1 = x1 * xscale / 100
        y0 = y0 * yscale / 100
        y1 = y1 * yscale / 100
        filterer = np.ones(self.locs.x.shape)
        filterer[self.locs.x < x0] = np.nan
        filterer[self.locs.x > x1] = np.nan
        filterer[self.locs.y < y0] = np.nan
        filterer[self.locs.y > y1] = np.nan
        if self.zdim:
            z0, z1 = self.parent.Sz.getRange()
            zscale = max(self.locs.z) - min(self.locs.z)
            z0 = z0 * zscale / 100
            z1 = z1 * zscale / 100
            filterer[self.locs.z < z0] = np.nan
            filterer[self.locs.z > z1] = np.nan
            self.locs = np.rec.array((self.locs.frame[~ np.isnan(filterer)], self.locs.x[~ np.isnan(filterer)],
                                      self.locs.y[~ np.isnan(filterer)], self.locs.z[~ np.isnan(filterer)],
                                      self.locs.photons[~ np.isnan(filterer)]), dtype=LOCS_DTYPE_3D)
        else:
            self.locs = np.rec.array((self.locs.frame[~ np.isnan(filterer)], self.locs.x[~ np.isnan(filterer)],
                                      self.locs.y[~ np.isnan(filterer)],
                                      self.locs.photons[~ np.isnan(filterer)]), dtype=LOCS_DTYPE_2D)
        self.calc_sigmas()


##### Highest Order Function

def open_STORM_data(self, file_path=None):
    v=napari.current_viewer()
    if not self.list_of_datasets:
        self.Lnumberoflocs.clear()
    else :
        for i in range(len(self.list_of_datasets)):
            v.layers.remove(self.list_of_datasets[i].name)
        self.list_of_datasets=[]
        self.Lnumberoflocs.clear()
    Tk().withdraw()
    if not file_path:
        file_path = fd.askopenfilename()
    filetype = file_path.split(".")[-1]
    filename = file_path.split("/")[-1]
    if filetype == "hdf5":
        load_hdf5(self, file_path)
    elif filetype == "yaml":
        file_path = file_path[:-(len(filetype))] + "hdf5"
        load_hdf5(self, file_path)
    elif filetype == "csv":
        load_csv(self, file_path)
    elif filetype == "smlm":
        load_SMLM(self, file_path)
    elif filetype == "h5":
        load_h5(self, file_path)
    elif filetype == "json":
        load_mfx_json(self,file_path)
    elif filetype == "npy":
        load_mfx_npy(self,file_path)
    else:
        raise TypeError("unknown File extension for STORM Data files...")


def create_new_layer(self, aas=0.1, layer_name="SMLM Data", idx=-1):
    print(f"Pixelsize {self.list_of_datasets[idx].pixelsize}")
    coords = get_coords_from_locs(self, self.list_of_datasets[idx].pixelsize, idx)
    values = np.ones_like(coords[:, 0])
    values = values * 100
    v = napari.current_viewer()  # Just to get the sigmas
    size=self.Sperformance.value()
    self.list_of_datasets[idx].layer = Particles(coords, size=size,
                                                 values=values,
                                                 antialias=aas,
                                                 colormap='Spectral',
                                                 sigmas=self.list_of_datasets[idx].sigma,
                                                 filter=None,
                                                 name=layer_name,
                                                 )
    self.list_of_datasets[idx].name = layer_name
    self.list_of_datasets[idx].layer.add_to_viewer(v)
    # v.window.qt_viewer.layer_to_visual[self.layer[-1]].node.canvas.measure_fps()
    self.list_of_datasets[idx].layer.contrast_limits = (0, 1)
    if self.list_of_datasets[idx].zdim:
        v.dims.ndisplay = 3
    else:
        v.dims.ndisplay = 2
    v.camera.perspective = 50
    self.list_of_datasets[idx].layer.shading = 'gaussian'
    show_infos(self, layer_name, idx)
    self.list_of_datasets[idx].camera_center=[v.camera.center,v.camera.zoom]


def update_layers(self, aas=0.1,  layer_name="SMLM Data"):
    v = napari.current_viewer()
    cache_camera = [v.camera.angles, v.camera.zoom]

    for i in range(len(self.list_of_datasets)):
        self.list_of_datasets[i].update_locs()
        cache_colormap = self.list_of_datasets[i].layer.colormap
        v.layers.remove(self.list_of_datasets[i].name)
        coords = get_coords_from_locs(self, self.list_of_datasets[i].pixelsize, i)
        values = np.ones_like(coords[:, 0])
        size=self.Sperformance.value()
        values = values * 100
        self.list_of_datasets[i].layer = Particles(coords, size=size,
                                                   values=values,
                                                   antialias=aas,
                                                   colormap=cache_colormap,
                                                   sigmas=self.list_of_datasets[i].sigma,
                                                   filter=None,
                                                   name=self.list_of_datasets[i].name,
                                                   )
        self.list_of_datasets[i].layer.add_to_viewer(v)
        self.list_of_datasets[i].layer.contrast_limits = (0, 1)
        self.list_of_datasets[i].layer.shading = 'gaussian'
    v.camera.angles=cache_camera[0]
    v.camera.zoom = cache_camera[1]
    v.camera.update({})


""" Alternative to update the layers, which should be faster --> does not work yet 
def update_layers_alt(self, aas=0.1, pixelsize=130,  layer_name="SMLM Data"):
    v = napari.current_viewer()
    for i in range(len(self.list_of_datasets)):
        self.list_of_datasets[i].calc_sigmas()
        self.list_of_datasets[i].update_locs()
        self.list_of_datasets[i].layer.coords=get_coords_from_locs(self, pixelsize, i)
        print(self.list_of_datasets[i].name)
        v.layers[i]=self.list_of_datasets[i].layer
"""


def get_coords_from_locs(self, pixelsize, idx):
    if self.list_of_datasets[idx].zdim:
        num_of_locs = len(self.list_of_datasets[idx].locs.x)
        coords = np.zeros([num_of_locs, 3])
        coords[:, 0] = self.list_of_datasets[idx].locs.z * pixelsize
        coords[:, 1] = self.list_of_datasets[idx].locs.x * pixelsize
        coords[:, 2] = self.list_of_datasets[idx].locs.y * pixelsize
    else:
        num_of_locs = len(self.list_of_datasets[idx].locs.x)
        coords = np.zeros([num_of_locs, 2])
        coords[:, 0] = self.list_of_datasets[idx].locs.x * pixelsize
        coords[:, 1] = self.list_of_datasets[idx].locs.y * pixelsize
    return coords


##### Semi Order Functions
def show_infos(self, filename, idx):
    if self.list_of_datasets[idx].zdim:
        self.Lnumberoflocs.addItem(
            "Statistics\n" + f"File: {filename}\n" + f"Number of locs: {len(self.list_of_datasets[idx].locs.x)}\n"
                                                     f"Imagewidth: {np.round((max(self.list_of_datasets[idx].locs.x) - min(self.list_of_datasets[idx].locs.x)) * self.list_of_datasets[idx].pixelsize / 1000,3)} µm\n" +
            f"Imageheigth: {np.round((max(self.list_of_datasets[idx].locs.y) - min(self.list_of_datasets[idx].locs.y)) * self.list_of_datasets[idx].pixelsize / 1000,3)} µm\n" +
            f"Imagedepth: {np.round((max(self.list_of_datasets[idx].locs.z) - min(self.list_of_datasets[idx].locs.z)) * self.list_of_datasets[idx].pixelsize / 1000,3)} µm\n" +
            f"Intensity per localisation\nmean: {np.round(np.mean(self.list_of_datasets[idx].locs.photons),3)}\nmax: " + f"{np.round(max(self.list_of_datasets[idx].locs.photons),3)}\nmin:" +
            f" {np.round(min(self.list_of_datasets[idx].locs.photons),3)}\n")
    else:
        self.Lnumberoflocs.addItem(
            "Statistics\n" + f"File: {filename}\n" + f"Number of locs: {len(self.list_of_datasets[idx].locs.x)}\n"
                                                     f"Imagewidth: {np.round((max(self.list_of_datasets[idx].locs.x) - min(self.list_of_datasets[idx].locs.x)) * self.list_of_datasets[idx].pixelsize / 1000,3)} µm\n" +
            f"Imageheigth: {np.round((max(self.list_of_datasets[idx].locs.y) - min(self.list_of_datasets[idx].locs.y)) * self.list_of_datasets[idx].pixelsize / 1000,3)} µm\n" +
            f"Intensity per localisation\nmean: {np.round(np.mean(self.list_of_datasets[idx].locs.photons),3)}\nmax: " + f"{np.round(max(self.list_of_datasets[idx].locs.photons),3)}\nmin:" +
            f" {np.round(min(self.list_of_datasets[idx].locs.photons),3)}\n")