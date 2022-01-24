"""
This module is an example of a barebones QWidget plugin for napari

It implements the ``napari_experimental_provide_dock_widget`` hook specification.
see: https://napari.org/docs/dev/plugins/hook_specifications.html

Replace code below according to your needs.
"""
from PyQt5.QtGui import QPaintEvent, QPainter, QPalette, QBrush, QMouseEvent
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QComboBox, QListWidget
from magicgui import magic_factory
from PyQt5.QtWidgets import QGridLayout, QStyleOptionSlider, QSlider, QSizePolicy, QStyle, QApplication, QLineEdit, \
    QCheckBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QUrl, QRect, QSize
import csv
import easygui


class RangeSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.first_position = 0
        self.second_position = 100

        self.opt = QStyleOptionSlider()
        self.opt.minimum = 0
        self.opt.maximum = 100

        self.setTickPosition(QSlider.TicksAbove)
        self.setTickInterval(1)

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed, QSizePolicy.Slider)
        )

    def setRangeLimit(self, minimum: int, maximum: int):
        self.opt.minimum = minimum
        self.opt.maximum = maximum

    def setRange(self, start: int, end: int):
        self.first_position = start
        self.second_position = end

    def getRange(self):
        return (self.first_position, self.second_position)

    def setTickPosition(self, position: QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: int):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QPaintEvent):

        painter = QPainter(self)

        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks

        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        #  Draw INTERVAL

        color = self.palette().color(QPalette.Highlight)
        color.setAlpha(160)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)

        self.opt.sliderPosition = self.first_position
        x_left_handle = (
            self.style()
                .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
                .right()
        )

        self.opt.sliderPosition = self.second_position
        x_right_handle = (
            self.style()
                .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
                .left()
        )

        groove_rect = self.style().subControlRect(
            QStyle.CC_Slider, self.opt, QStyle.SC_SliderGroove
        )

        selection = QRect(
            x_left_handle,
            groove_rect.y(),
            x_right_handle - x_left_handle,
            groove_rect.height(),
        ).adjusted(-1, 1, 1, -1)

        painter.drawRect(selection)

        # Draw first handle

        self.opt.subControls = QStyle.SC_SliderHandle
        self.opt.sliderPosition = self.first_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        # Draw second handle
        self.opt.sliderPosition = self.second_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

    def mousePressEvent(self, event: QMouseEvent):

        self.opt.sliderPosition = self.first_position
        self._first_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

        self.opt.sliderPosition = self.second_position
        self._second_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        for i in range(len(self.parent.list_of_datasets)):
            update_layers(self.parent)

    def mouseMoveEvent(self, event: QMouseEvent):

        distance = self.opt.maximum - self.opt.minimum

        pos = self.style().sliderValueFromPosition(
            0, distance, event.pos().x(), self.rect().width()
        )

        if self._first_sc == QStyle.SC_SliderHandle:
            if pos <= self.second_position:
                self.first_position = pos
                self.update()
                return

        if self._second_sc == QStyle.SC_SliderHandle:
            if pos >= self.first_position:
                self.second_position = pos
                self.update()

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.opt, self)

        if (
                self.opt.tickPosition & QSlider.TicksAbove
                or self.opt.tickPosition & QSlider.TicksBelow
        ):
            h += TickSpace

        return (
            self.style()
                .sizeFromContents(QStyle.CT_Slider, self.opt, QSize(w, h), self)
                .expandedTo(QApplication.globalStrut())
        )


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
        print("yes", item)


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
        self.camera_angle = None
        self.colormap = None

    def calc_sigmas(self):
        if self.parent.Brenderoptions.currentText() == "individual gaussian":
            sigma = float(self.parent.Esigma.text()) / np.sqrt(self.locs.photons) / 2.354
            sigmaz = float(self.parent.Esigma2.text()) / np.sqrt(self.locs.photons) / 2.354
            self.sigma = np.swapaxes([sigmaz, sigma, sigma], 0, 1)
        else:
            self.sigma= float(self.parent.Esigma.text()) / 2.354


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
        self.Brenderoptions.addItems(["individual gaussian", "fixed gaussian"])
        self.Brenderoptions.currentIndexChanged.connect(self.render_options_changed)
        layout.addWidget(self.Brenderoptions, 3, 1)

        self.Lsigma = QLabel()
        self.Lsigma.setText("FWHM(PSF) in XY [nm]:")
        layout.addWidget(self.Lsigma, 4, 0)

        self.Lsigma2 = QLabel()
        self.Lsigma2.setText("FWHM(PSF) in Z [nm]:")
        layout.addWidget(self.Lsigma2, 5, 0)

        self.Esigma = QLineEdit()
        self.Esigma.setText("10")
        self.Esigma.textChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sigma))
        layout.addWidget(self.Esigma, 4, 1)
        self.typing_timer_sigma = QtCore.QTimer()
        self.typing_timer_sigma.setSingleShot(True)
        self.typing_timer_sigma.timeout.connect(lambda: update_layers(self))

        self.Esigma2 = QLineEdit()
        self.Esigma2.setText("15")
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

        layout.setColumnStretch(0, 2)
        self.setLayout(layout)

        self.Sz.hide()
        self.Lrangez.hide()
        self.Lresetview.hide()
        self.Baxis.hide()

    def scalebar(self):
        v = napari.current_viewer()
        if self.Cscalebar.isChecked() and not not all(self.list_of_datasets[-1].locs):
            l = int(self.Esbsize.text())
            xsb = [[0, 0], [+0.1 * l, 0], [+0.1 * l, l], [0, l]]
            if self.scalebar_exists:
                v.layers.remove('scalebar')
                self.scalebar_layer = v.add_shapes(xsb, shape_type='polygon', face_color='white', name='scalebar',
                                                   edge_color='red', edge_width=0.05 * l)
            else:
                self.scalebar_layer = v.add_shapes(xsb, shape_type='polygon', face_color='white', name='scalebar',
                                                   edge_color='red', edge_width=0.05 * l)
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
        timer.start(2000)

    def change_camera(self):
        v = napari.current_viewer()
        if self.Baxis.currentText() == "XY":
            v.camera.set_view_direction((1, 0, 0))
        elif self.Baxis.currentText() == "XZ":
            v.camera.set_view_direction((0, -1, 0))
            # print(v.camera.view_direction)
        else:
            v.camera.set_view_direction((0.001, -0.001, -1))
            # print(v.camera.view_direction)

    def render_options_changed(self):
        if self.Brenderoptions.currentText() == "individual gaussian":
            self.Lsigma2.show()
            self.Esigma2.show()
            self.Lsigma.setText("FWHM(PSF) in XY [nm]")
        else:
            self.Lsigma2.hide()
            self.Esigma2.hide()
            self.Lsigma.setText("FWHM [nm]")
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
    if not self.list_of_datasets:
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
    else:
        raise TypeError("unknown File extension for STORM Data files...")


def create_new_layer(self, aas=0.1, pixelsize=130, particle_size=130, layer_name="SMLM Data", idx=-1):
    coords = get_coords_from_locs(self, pixelsize, idx)
    values = np.ones_like(coords[:, 0])
    size = values * particle_size
    values = values * 100
    v = napari.current_viewer()  # Just to get the sigmas
    self.list_of_datasets[idx].layer = Particles(coords, size=size,
                                                 values=values,
                                                 antialias=aas,
                                                 colormap='Spectral',
                                                 sigmas=self.list_of_datasets[idx].sigma / particle_size,
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


def update_layers(self, aas=0.1, pixelsize=130, particle_size=130, layer_name="SMLM Data"):
    v = napari.current_viewer()
    cache_camera = [v.camera.view_direction, v.camera.zoom]
    for i in range(len(self.list_of_datasets)):
        print(i)
        self.list_of_datasets[i].calc_sigmas()
        self.list_of_datasets[i].update_locs()
        cache_colormap = self.list_of_datasets[i].layer.colormap
        v.layers.remove(self.list_of_datasets[i].name)
        coords = get_coords_from_locs(self, pixelsize, i)
        values = np.ones_like(coords[:, 0])
        size = values * particle_size
        values = values * 100
        self.list_of_datasets[i].layer = Particles(coords, size=size,
                                                   values=values,
                                                   antialias=aas,
                                                   colormap=cache_colormap,
                                                   sigmas=self.list_of_datasets[i].sigma / particle_size,
                                                   filter=None,
                                                   name=self.list_of_datasets[i].name,
                                                   )
        self.list_of_datasets[i].layer.add_to_viewer(v)
        self.list_of_datasets[i].layer.contrast_limits = (0, 1)
        self.list_of_datasets[i].layer.shading = 'gaussian'
    v.camera.set_view_direction(cache_camera[0])
    v.camera.zoom = cache_camera[1]


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
                                                     f"Imagewidth: {np.round((max(self.list_of_datasets[idx].locs.x) - min(self.list_of_datasets[idx].locs.x)) * self.list_of_datasets[idx].pixelsize / 1000)} µm\n" +
            f"Imageheigth: {np.round((max(self.list_of_datasets[idx].locs.y) - min(self.list_of_datasets[idx].locs.y)) * self.list_of_datasets[idx].pixelsize / 1000)} µm\n" +
            f"Imagedepth: {np.round((max(self.list_of_datasets[idx].locs.z) - min(self.list_of_datasets[idx].locs.z)) * self.list_of_datasets[idx].pixelsize / 1000)} µm\n" +
            f"Intensity per localisation\nmean: {np.round(np.mean(self.list_of_datasets[idx].locs.photons))}\nmax: " + f"{np.round(max(self.list_of_datasets[idx].locs.photons))}\nmin:" +
            f" {np.round(min(self.list_of_datasets[idx].locs.photons))}\n")
    else:
        self.Lnumberoflocs.addItem(
            "Statistics\n" + f"File: {filename}\n" + f"Number of locs: {len(self.list_of_datasets[idx].locs.x)}\n"
                                                     f"Imagewidth: {np.round((max(self.list_of_datasets[idx].locs.x) - min(self.list_of_datasets[idx].locs.x)) * self.list_of_datasets[idx].pixelsize / 1000)} µm\n" +
            f"Imageheigth: {np.round((max(self.list_of_datasets[idx].locs.y) - min(self.list_of_datasets[idx].locs.y)) * self.list_of_datasets[idx].pixelsize / 1000)} µm\n" +
            f"Intensity per localisation\nmean: {np.round(np.mean(self.list_of_datasets[idx].locs.photons))}\nmax: " + f"{np.round(max(self.list_of_datasets[idx].locs.photons))}\nmin:" +
            f" {np.round(min(self.list_of_datasets[idx].locs.photons))}\n")


def load_info(path):
    path_base, path_extension = _ospath.splitext(path)
    filename = path_base + ".yaml"
    try:
        with open(filename, "r") as info_file:
            info = list(_yaml.load_all(info_file, Loader=_yaml.FullLoader))
    except FileNotFoundError as e:
        print(
            "\nAn error occured. Could not find metadata file:\n{}".format(
                filename
            )
        )
    return info


def load_locs(path):
    with h5py.File(path, "r") as locs_file:
        locs = locs_file["locs"][...]
    locs = np.rec.array(
        locs, dtype=locs.dtype
    )  # Convert to rec array with fields as attributes
    info = load_info(path)
    return locs, info


def load_hdf5(self, file_path):
    filename = file_path.split('/')[-1]
    locs, info = load_locs(file_path)
    try:
        pixelsize = locs.pixelsize
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    self.pixelsize = pixelsize
    self.list_of_datasets.append(dataset(locs=locs, parent=self, pixelsize=pixelsize, name=filename))
    try:
        self.list_of_datasets[-1].locs.z
        self.list_of_datasets[-1].zdim = True
        self.C3d.setChecked(True)
    except:
        pass
    create_new_layer(self=self, aas=0.1, pixelsize=pixelsize, particle_size=130, layer_name=filename, idx=-1)


def load_h5(self, file_path):
    filename = file_path.split('/')[-1]
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    with h5py.File(file_path, "r") as locs_file:
        data = locs_file['molecule_set_data']['datatable'][...]
        pixelsize = locs_file['molecule_set_data']['xy_pixel_size_um'][...] * 1E3  # to µm to nm
    try:
        locs = np.rec.array((data['FRAME_NUMBER'], data['X_POS_PIXELS'], data['Y_POS_PIXELS'], data['Z_POS_PIXELS'],
                             data['PHOTONS']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array((data['FRAME_NUMBER'], data['X_POS_PIXELS'], data['Y_POS_PIXELS'],
                             data['PHOTONS']), dtype=LOCS_DTYPE_2D)
    num_channel = max(data['CHANNEL']) + 1
    for i in range(num_channel):
        locs_in_ch=locs[data['CHANNEL']==i]
        self.list_of_datasets.append(dataset(locs=locs_in_ch, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename+f" Channel {i+1}"))
        create_new_layer(self=self, aas=0.1, pixelsize=pixelsize, particle_size=130, layer_name=filename+f" Channel {i+1}", idx=-1)


def load_csv(self, file_path):
    filename = file_path.split('/')[-1]
    data = {}
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    with open(file_path, mode='r') as infile:
        header = infile.readline()
        header = header.replace('\n', '')
        header = header.split(',')
        data_list = np.loadtxt(file_path, delimiter=',', skiprows=1, dtype=float)
    for i in range(len(header)):
        data[header[i]] = data_list[:, i]
    try:
        pixelsize = data['"pixelsize"']
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    try:
        locs = np.rec.array(
            (data['"frame"'], data['"x [nm]"'] / pixelsize, data['"y [nm]"'] / pixelsize, data['"z [nm]"'] / pixelsize,
             data['"intensity [photon]"']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array(
            (data['"frame"'], data['"x [nm]"'] / pixelsize, data['"y [nm]"'] / pixelsize, data['"intensity [photon]"']),
            dtype=LOCS_DTYPE_2D, )
        zdim = False
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1, pixelsize=pixelsize, particle_size=130, layer_name=filename, idx=-1)


## load_SMLM adapted from Marting Weigerts readSmlmFile
import zipfile
import json
import struct
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
dtype2struct = {'uint8': 'B', 'uint32': 'I', 'float64': 'd', 'float32': 'f'}
dtype2length = {'uint8': 1, 'uint32': 4, 'float64': 8, 'float32': 4}


def load_SMLM(self, file_path):
    filename = file_path.split('.')[-1]
    zf = zipfile.ZipFile(file_path, 'r')
    file_names = zf.namelist()
    if "manifest.json" in file_names:
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest['format_version'] == '0.2'
        for file_info in manifest['files']:
            if file_info['type'] == "table":
                logger.info('loading table...')
                format_key = file_info['format']
                file_format = manifest['formats'][format_key]
                if file_format['mode'] == 'binary':
                    try:
                        table_file = zf.read(file_info['name'])
                        logger.info(file_info['name'])
                    except KeyError:
                        logger.error('ERROR: Did not find %s in zip file', file_info['name'])
                        continue
                    else:
                        logger.info('loading table file: %s bytes', len(table_file))
                        logger.info('headers: %s', file_format['headers'])
                        headers = file_format['headers']
                        dtype = file_format['dtype']
                        shape = file_format['shape']
                        cols = len(headers)
                        rows = file_info['rows']
                        logger.info('rows: %s, columns: %s', rows, cols)
                        assert len(headers) == len(dtype) == len(shape)
                        rowLen = 0
                        for i, h in enumerate(file_format['headers']):
                            rowLen += dtype2length[dtype[i]]

                        tableDict = {}
                        byteOffset = 0
                        try:
                            import numpy as np
                            for i, h in enumerate(file_format['headers']):
                                tableDict[h] = np.ndarray((rows,), buffer=table_file, dtype=dtype[i], offset=byteOffset,
                                                          order='C', strides=(rowLen,))
                                byteOffset += dtype2length[dtype[i]]
                        except ImportError:
                            logger.warning(
                                'Failed to import numpy, performance will drop dramatically. Please install numpy for the best performance.')
                            st = ''
                            for i, h in enumerate(file_format['headers']):
                                st += (str(shape[i]) + dtype2struct[dtype[i]])

                            unpack = struct.Struct(st).unpack
                            tableDict = {h: [] for h in headers}
                            for i in range(0, len(table_file), rowLen):
                                unpacked_data = unpack(table_file[i:i + rowLen])
                                for j, h in enumerate(headers):
                                    tableDict[h].append(unpacked_data[j])
                            tableDict = {h: np.array(tableDict[h]) for i, h in enumerate(headers)}
                        data = {}
                        data['min'] = [tableDict[h].min() for h in headers]
                        data['max'] = [tableDict[h].max() for h in headers]
                        data['avg'] = [tableDict[h].mean() for h in headers]
                        data['tableDict'] = tableDict
                        file_info['data'] = data
                        logger.info('table file loaded: %s', file_info['name'])
                else:
                    raise Exception('format mode {} not supported yet'.format(file_format['mode']))
            elif file_info['type'] == "image":
                if file_format['mode'] == 'binary':
                    try:
                        image_file = zf.read(file_info['name'])
                        logger.info('image file loaded: %s', file_info['name'])
                    except KeyError:
                        logger.error('ERROR: Did not find %s in zip file', file_info['name'])
                        continue
                    else:
                        from PIL import Image
                        image = Image.open(io.BytesIO(image_file))
                        data = {}
                        data['image'] = image
                        file_info['data'] = data
                        logger.info('image file loaded: %s', file_info['name'])

            else:
                logger.info('ignore file with type: %s', file_info['type'])
    else:
        raise Exception('invalid file: no manifest.json found in the smlm file')
    prop = manifest['files'][-1]['data']['tableDict']
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    try:
        pixelsize = prop['pixelsize']
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    if not 'intensity_photon_' in prop.keys():  # If the photons are not given, set them to 1k
        prop['intensity_photon_'] = 1000 * np.ones(len(prop['x']))
    try:
        locs = np.rec.array(
            (prop['frame'], prop['x'] / pixelsize, prop['y'] / pixelsize, prop['z'] / pixelsize,
             prop['intensity_photon_']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array(
            (prop['frame'], prop['x'] / pixelsize, prop['y'] / pixelsize,
             prop['intensity_photon_']), dtype=LOCS_DTYPE_2D)
        zdim = False
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    plt.scatter(locs.x, locs.y)  # until gpu and ram are updated... to show that it works in principle
    plt.show()
    # create_new_layer(self=self, aas=0.1, pixelsize=pixelsize, particle_size=130, layer_name=filename, idx=-1)

##### Lowest Order functions