from PyQt5.QtGui import QPaintEvent, QPainter, QPalette, QBrush, QMouseEvent
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QPushButton, QLabel, QComboBox, QListWidget, QWidget
from PyQt5.QtWidgets import QGridLayout, QStyleOptionSlider, QSlider, QSizePolicy, QStyle, QApplication, QLineEdit, \
    QCheckBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QRect, QSize
import easygui
from .Exp_Controlls import *
import napari






class TestListView(QListWidget):
    def __init__(self, type, parent=None):
        super(TestListView, self).__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(72, 72))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
            links = []
            u = event.mimeData().urls()
            file = u[0].toString()[8:]
            open_STORM_data(self.parent, file_path=file)
        else:
            event.ignore()

    def remove_dataset(self, item):
        print("Dataset removal not implemented yet...", item)


class dataset():
    def __init__(self, locs=None, zdim=False, parent=None, name=None, pixelsize=130):
        self.zdim = zdim
        if zdim:
            locs.z -= min(locs.z)
        locs.y -= min(locs.y) # No negative Values, b/c napari doesn't like them
        locs.x -= min(locs.x)
        self.locs = locs
        self.locs_backup = locs  # Needed if dataset is cut with sliders and then you want the data back
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


class SMLMQW(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()

        self.list_of_datasets = []
        self.pixelsize = []
        self.layer = []
        self.layer_names = []
        self.scalebar_layer = []
        self.scalebar_exists = False
        self.sigma = []
        self.zdim = False

        self.viewer = napari_viewer
        layout = QGridLayout()

        self.Bopen = QPushButton()
        self.Bopen.clicked.connect(lambda: open_STORM_data(self))
        self.Bopen.setStyleSheet(
            "background-image : url(Bilder/Import_Button.png)")
        layout.addWidget(self.Bopen, 0, 1)

        self.Limport = QLabel()
        self.Limport.setText("Import \nSMLM Data")
        layout.addWidget(self.Limport, 0, 0)

        self.Lnumberoflocs = TestListView(self, parent=self)
        self.Lnumberoflocs.addItem("STATISTICS \nWaiting for Data... \nImport or drag file here")
        self.Lnumberoflocs.itemDoubleClicked.connect(self.Lnumberoflocs.remove_dataset)
        layout.addWidget(self.Lnumberoflocs, 1, 0, 1, 2)

        self.Lresetview = QLabel()
        self.Lresetview.setText("Reset view:")
        layout.addWidget(self.Lresetview, 2, 0)

        self.Baxis = QComboBox()
        self.Baxis.addItems(["XY", "XZ", "YZ"])
        self.Baxis.currentIndexChanged.connect(self.change_camera)
        layout.addWidget(self.Baxis, 2, 1)

        self.Lrenderoptions = QLabel()
        self.Lrenderoptions.setText("Rendering options:")
        layout.addWidget(self.Lrenderoptions, 3, 0)

        self.Brenderoptions = QComboBox()
        self.Brenderoptions.addItems(["fixed gaussian", "variable gaussian"])
        self.Brenderoptions.currentIndexChanged.connect(self.render_options_changed)
        layout.addWidget(self.Brenderoptions, 3, 1)

        self.Lsigma = QLabel()
        self.Lsigma.setText("PSF FWHM in XY [nm]:")
        layout.addWidget(self.Lsigma, 4, 0)

        self.Lsigma2 = QLabel()
        self.Lsigma2.setText("PSF FWHM in Z [nm]:")
        layout.addWidget(self.Lsigma2, 5, 0)

        self.Esigma = QLineEdit()
        self.Esigma.setText("10")
        self.Esigma.textChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sigma))
        layout.addWidget(self.Esigma, 4, 1)
        self.typing_timer_sigma = QtCore.QTimer()
        self.typing_timer_sigma.setSingleShot(True)
        self.typing_timer_sigma.timeout.connect(lambda: update_layers(self))

        self.Esigma2 = QLineEdit()
        self.Esigma2.setText("750")
        self.Esigma2.textChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sigma))
        layout.addWidget(self.Esigma2, 5, 1)

        self.Lrangex = QLabel()
        self.Lrangex.setText("X-range")
        layout.addWidget(self.Lrangex, 6, 0)

        self.Lrangey = QLabel()
        self.Lrangey.setText("Y-range")
        layout.addWidget(self.Lrangey, 7, 0)

        self.Lrangez = QLabel()
        self.Lrangez.setText("Z-range")
        layout.addWidget(self.Lrangez, 8, 0)

        from .Range_slider import RangeSlider
        self.Sx = RangeSlider(parent=self)
        # self.Sx.mouseReleaseEvent.connect()
        layout.addWidget(self.Sx, 6, 1)

        self.Sy = RangeSlider(parent=self)
        layout.addWidget(self.Sy, 7, 1)

        self.Sz = RangeSlider(parent=self)
        layout.addWidget(self.Sz, 8, 1)

        self.Lscalebar = QLabel()
        self.Lscalebar.setText("Scalebar?")
        layout.addWidget(self.Lscalebar, 9, 0)

        self.Cscalebar = QCheckBox()
        self.Cscalebar.stateChanged.connect(self.scalebar)
        layout.addWidget(self.Cscalebar, 9, 1)

        self.Lscalebarsize = QLabel()
        self.Lscalebarsize.setText("Size of Scalebar [nm]:")
        layout.addWidget(self.Lscalebarsize, 10, 0)

        self.Esbsize = QLineEdit()
        self.Esbsize.setText("1000")
        self.Esbsize.textChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sbscale))
        layout.addWidget(self.Esbsize, 10, 1)
        self.typing_timer_sbscale = QtCore.QTimer()
        self.typing_timer_sbscale.setSingleShot(True)
        self.typing_timer_sbscale.timeout.connect(self.scalebar)

        self.L3d = QLabel()
        self.L3d.setText("3D?")
        layout.addWidget(self.L3d, 11, 0)

        self.C3d = QCheckBox()
        self.C3d.stateChanged.connect(self.threed)
        layout.addWidget(self.C3d, 11, 1)

        self.Lperformance = QLabel()
        self.Lperformance.setText("Performance - Image Quality")
        layout.addWidget(self.Lperformance,12,0)

        self.Sperformance = QSlider(Qt.Horizontal)
        self.Sperformance.setMinimum(5)
        self.Sperformance.setMaximum(105)
        self.Sperformance.setSingleStep(10)
        self.Sperformance.setValue(35)
        self.Sperformance.valueChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sigma))
        layout.addWidget(self.Sperformance,12,1)

        self.Baltpan = QCheckBox()
        self.Baltpan.setText("activate experimental fly through mode")
        self.Baltpan.stateChanged.connect(self.alt_controlls)
        layout.addWidget(self.Baltpan,13,0)

        self.custom_controlls = MouseControlls()


        layout.setColumnStretch(0, 2)
        self.setLayout(layout)

        self.Lsigma2.hide()
        self.Esigma2.hide()
        self.Sz.hide()
        self.Lrangez.hide()
        self.Lresetview.hide()
        self.Baxis.hide()
        self.L3d.hide()
        self.C3d.hide()

        # Custom Keys : w and s for zoom
        # q and e to switch trough axis
        # a and d to rotate view
        v = napari.current_viewer()
        @v.bind_key('w')
        def fly_ahead(v):
            v.camera.zoom *= 1.1
        @v.bind_key('s')
        def fly_back(v):
            self.viewer.camera.zoom *= 0.9
        @v.bind_key('a')
        def fly_rotate_l(v):
            alpha,beta,gamma=v.camera.angles
            print(alpha)
            alpha += 30
            if alpha >180:
                alpha -= 360
            self.viewer.camera.angles = (alpha, beta, gamma)
        @v.bind_key('d')
        def fly_rotate_d(v):
            alpha, beta, gamma = v.camera.angles
            print(alpha)
            alpha -= 30
            if alpha < -180:
                alpha += 360
            self.viewer.camera.angles = (alpha, beta, gamma)
        @v.bind_key('q')
        def fly_rotate_l(v):
            alpha, beta, gamma = v.camera.angles
            print(beta)
            beta += 30
            if beta > 90:
                beta -= 180
                gamma -=90
            self.viewer.camera.angles = (alpha, beta, gamma)
        @v.bind_key('e')
        def fly_rotate_d(v):
            alpha, beta, gamma = v.camera.angles
            print(beta)
            beta -= 30
            if beta < -90:
                beta += 180
                gamma += 90
            self.viewer.camera.angles = (alpha, beta, gamma)
        @v.bind_key('r')
        def fly_reset(v):
            v.camera.angles=(0,0,90)
            v.camera.center = self.list_of_datasets[-1].camera_center[0]
            v.camera.zoom = self.list_of_datasets[-1].camera_center[1]


    def alt_controlls(self):
        print("swichting controlls")
        if not self.Baltpan.isChecked():
            self.custom_controlls._deactivate()
        else:
            self.custom_controlls._activate()

    def scalebar(self):
        v = napari.current_viewer()
        cpos=v.window.qt_viewer.camera.center
        l = int(self.Esbsize.text())
        center=[cpos[2]-l/2,cpos[1]]
        if self.Cscalebar.isChecked() and not not all(self.list_of_datasets[-1].locs):
            xsb = [[center[1], center[0]], [center[1]+0.1 * l, center[0]], [center[1]+0.1 * l,center[0]+l ], [center[1],center[0]+l ]]
            if self.scalebar_exists:
                v.layers.remove('scalebar')
                self.scalebar_layer = v.view_surface(xsb, shape_type='polygon', face_color='white', name='scalebar',
                                                   edge_color='red', edge_width=0)
            else:
                self.scalebar_layer = v.add_shapes(xsb, shape_type='polygon', face_color='white', name='scalebar',
                                                   edge_color='red', edge_width=0)
                self.scalebar_exists = True
        else:
            if self.scalebar_exists:
                v.layers.remove('scalebar')
                self.scalebar_exists = False

    def threed(self):
        v = napari.current_viewer()
        # print(v.camera.view_direction)
        if self.C3d.isChecked():
            self.Lrangez.show()
            self.Sz.show()
            self.Baxis.show()
            self.Lresetview.show()
            v.dims.ndisplay = 3
        else:
            self.Lrangez.hide()
            self.Sz.hide()
            v.dims.ndisplay = 2

    def start_typing_timer(self, timer):
        timer.start(500)

    def change_camera(self):
        v = napari.current_viewer()
        values= {}
        if self.Baxis.currentText() == "XY":
            v.camera.angles=(0,0,90)
        elif self.Baxis.currentText() == "XZ":
            v.camera.angles=(0,0,180)
        else:
            v.camera.angles=(-90,-90,-90)
        v.camera.center = self.list_of_datasets[-1].camera_center[0]
        v.camera.zoom =self.list_of_datasets[-1].camera_center[1]
        v.camera.update(values)

    def render_options_changed(self):
        if self.Brenderoptions.currentText() == "variable gaussian":
            self.Lsigma2.show()
            self.Esigma2.show()
            self.Lsigma.setText("PSF FWHM in XY [nm]")
            self.Esigma.setText("300")
        else:
            self.Lsigma2.hide()
            self.Esigma2.hide()
            self.Lsigma.setText("FWHM in XY [nm]")
            self.Esigma.setText("10")
        update_layers(self)


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return SMLMQW


import h5py
import numpy as np
import yaml as _yaml
import os.path as _ospath
from tkinter import filedialog as fd
from tkinter import Tk
import napari
import matplotlib.pyplot as plt
from napari_particles.particles import Particles


##### Highest Order Function


def open_STORM_data(self, file_path=None):
    from .importer import load_hdf5,load_csv,load_SMLM,load_h5,load_mfx_json,load_mfx_npy
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
    self.list_of_datasets[idx].camera_center=[v.camera.center,v.camera.zoom, v.camera.angles]

def update_layers(self, aas=0.1,  layer_name="SMLM Data"):
    v = napari.current_viewer()
    self.list_of_datasets[-1].camera = [v.camera.zoom, v.camera.center, v.camera.angles]

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
    v.camera.angles = self.list_of_datasets[-1].camera[2]
    v.camera.zoom = self.list_of_datasets[-1].camera[0]
    v.camera.center = self.list_of_datasets[-1].camera[1]
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


