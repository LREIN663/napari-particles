from PyQt5.QtGui import QPaintEvent, QPainter, QPalette, QBrush, QMouseEvent
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QPushButton, QLabel, QComboBox, QListWidget, QWidget
from PyQt5.QtWidgets import QGridLayout, QStyleOptionSlider, QSlider, QSizePolicy, QStyle, QApplication, QLineEdit, \
    QCheckBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QRect, QSize
import easygui
import napari

class MouseControlls(QWidget):
    def __init__(self):
        super().__init__()
        print("Hello")
        self.viewer = napari.current_viewer()
        self.mouse_down = False
        self.mode = None
        self.active = False

    def _handle_moveL(self, x, y):

        #self.viewer.camera.zoom *= 1.0025
        delta_x = x - self.start_x
        delta_y = y - self.start_y
        alpha, beta, gamma = self.viewer.camera.angles
        relative_x = delta_x / self.viewer.window.qt_viewer.width() * 50
        relative_y = delta_y / self.viewer.window.qt_viewer.height() * 15
        gamma -= relative_y
        beta -= relative_x
        if beta <-90:
            print(beta)
        z, y, x = self.viewer.camera.center
        y += np.cos(2 * 3.14145 * gamma / 360) * self.viewer.window.qt_viewer.height() * 0.05
        x -= np.sin(2 * 3.14145 * beta / 360) * self.viewer.window.qt_viewer.width() * 0.05
        self.viewer.camera.center = (z, y, x)
        self.viewer.camera.angles = (alpha, beta, gamma)

    def _handle_moveR(self, x, y):
        #self.viewer.camera.zoom *= 0.9975
        delta_x = x - self.start_x
        delta_y = y - self.start_y
        alpha, beta, gamma = self.viewer.camera.angles
        relative_x = delta_x / self.viewer.window.qt_viewer.width() * 7.5
        relative_y = delta_y / self.viewer.window.qt_viewer.height() * 7.5
        gamma -= relative_y
        beta -= relative_x
        z, y, x = self.viewer.camera.center
        y -= np.cos(2 * 3.14145 * gamma / 360) * self.viewer.window.qt_viewer.height() * 0.05
        x += np.sin(2 * 3.14145 * beta / 360) * self.viewer.window.qt_viewer.width() * 0.05
        self.viewer.camera.center = (z, y, x)
        # print(alpha,beta,gamma)
        self.viewer.camera.angles = (alpha, beta, gamma)
        # print(self.viewer.camera.center)

    def _activate(self):
            print("Custom controlls active")

            self.copy_on_mouse_press = self.viewer.window.qt_viewer.on_mouse_press
            self.copy_on_mouse_move = self.viewer.window.qt_viewer.on_mouse_move
            self.copy_on_mouse_release = self.viewer.window.qt_viewer.on_mouse_release
            self.copy_on_key_press = self.viewer.window.qt_viewer.keyPressEvent

            def our_key_press(event=None): # not used atm
                print("Hello")
                z,y,x = self.viewer.camera.center
                alpha,beta,gamma= self.viewer.camera.angles
                print(event.key())
                if event.key()==87: #W
                    self.viewer.camera.zoom *= 1.1
                elif event.key()==83: #S
                    self.viewer.camera.zoom *= 0.9
                elif  event.key()==65: #A
                    alpha+=2.5
                elif event.key()==68:
                    alpha-=2.5
                self.viewer.camera.center=(z,y,x)
                self.viewer.camera.angles=(alpha,beta,gamma)



            def our_mouse_wheel(event=None):
                #print(event.delta)
                if event.delta[-1]>0:
                    self.viewer.camera.zoom *= 1.1
                else:
                    self.viewer.camera.zoom *= 0.9
                #print(self.viewer.camera.zoom)

            def our_mouse_press(event=None):
                #print("mouse press", event.native.x(), event.native.y(), event.native.button())
                self.mouse_down = True
                self.start_x = event.native.x()
                self.start_y = event.native.y()

                self.current_step = list(self.viewer.dims.current_step)
                #print("CURRENT step", self.current_step)

                self._start_zoom = self.viewer.camera.zoom

            def our_mouse_move(event=None):
                if event.button == Qt.MouseButton.RightButton:
                    if not self.mouse_down:
                        return
                    #print("mouse move", event.native.x(), event.native.y(), event.native.button())
                    self._handle_moveR(event.native.x(), event.native.y())
                else:
                    if not self.mouse_down:
                        return
                    #print("mouse move", event.native.x(), event.native.y(), event.native.button())
                    self._handle_moveL(event.native.x(), event.native.y())

            def our_mouse_release(event=None):
                if event.button == Qt.MouseButton.RightButton:
                    if not self.mouse_down:
                        return
                    #print("mouse release", event.native.x(), event.native.y(), event.native.button())
                    self._handle_moveR(event.native.x(), event.native.y())
                    self.mouse_down = False
                else:
                    if not self.mouse_down:
                        return
                    #print("mouse release", event.native.x(), event.native.y(), event.native.button())
                    self._handle_moveL(event.native.x(), event.native.y())
                    self.mouse_down = False



            self.viewer.window.qt_viewer.on_mouse_wheel = our_mouse_wheel
            self.viewer.window.qt_viewer.on_mouse_press = our_mouse_press
            self.viewer.window.qt_viewer.on_mouse_move = our_mouse_move
            self.viewer.window.qt_viewer.on_mouse_release = our_mouse_release
            #self.viewer.window.qt_viewer.keyPressEvent = our_key_press
            self.viewer.camera.interactive = False
            self.active = True

    def _deactivate(self):
        if not self.active:
            return
        self.viewer.window.qt_viewer.on_mouse_press = self.copy_on_mouse_press
        self.viewer.window.qt_viewer.on_mouse_move = self.copy_on_mouse_move
        self.viewer.window.qt_viewer.on_mouse_release = self.copy_on_mouse_release
        #self.viewer.window.qt_viewer.keyPressEvent = self.copy_on_key_press
        self.viewer.camera.interactive = True
        self.active = False

class RangeSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.first_position = 1
        self.second_position = 99

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
                self.scalebar_layer = v.add_shapes(xsb, shape_type='polygon', face_color='white', name='scalebar',
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
    try:
        locs.z
        zdim = True
        self.C3d.setChecked(True)
    except:
        zdim=False
    self.list_of_datasets.append(dataset(locs=locs, parent=self, zdim=zdim, pixelsize=pixelsize, name=filename))

    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)


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
        zdim = False
    num_channel = max(data['CHANNEL']) + 1
    for i in range(num_channel):
        locs_in_ch=locs[data['CHANNEL']==i]
        self.list_of_datasets.append(dataset(locs=locs_in_ch, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename+f" Channel {i+1}"))
        create_new_layer(self=self, aas=0.1,  layer_name=filename+f" Channel {i+1}", idx=-1)

def load_mfx_json(self,file_path): # 3D not implemented yet
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    filename = file_path.split('/')[-1]
    with open(file_path) as f:
        raw_data=json.load(f)
    f.close()
    locsx=[]
    locsy=[]
    try:
        zdim = True
        self.C3d.setChecked(True)
    except:
        zdim = False
    if zdim:
        locsz = []
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data[i]['itr'][-1]['loc'][0]) * 1E9)
                locsy.append((raw_data[i]['itr'][-1]['loc'][1]) * 1E9)
                locsz.append((raw_data[i]['itr'][-1]['loc'][2]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, locsz, photons),
            dtype=LOCS_DTYPE_3D, )
    else:
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data[i]['itr'][-1]['loc'][0]) * 1E9)
                locsy.append((raw_data[i]['itr'][-1]['loc'][1]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, photons),
            dtype=LOCS_DTYPE_2D, )
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1, layer_name=filename, idx=-1)



def load_mfx_npy(self,file_path):
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    filename = file_path.split('/')[-1]
    raw_data=np.load(file_path)
    locsx=[]
    locsy=[]
    minx= min(raw_data['itr']['loc'][:,-1,0])
    miny=min(raw_data['itr']['loc'][:,-1,1])
    try:
        minz=min(raw_data['itr']['loc'][:,-1,2])
        zdim=True
        self.C3d.setChecked(True)
    except:
        zdim=False
    if zdim:
        locsz=[]
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data['itr']['loc'][i, -1, 0]) * 1E9)
                locsy.append((raw_data['itr']['loc'][i, -1, 1]) * 1E9)
                locsz.append((raw_data['itr']['loc'][i, -1, 2]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, locsz, photons),
            dtype=LOCS_DTYPE_3D, )
    else:
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data['itr']['loc'][i, -1, 0]-minx)*1E9)
                locsy.append((raw_data['itr']['loc'][i, -1, 1]-miny)*1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, photons),
            dtype=LOCS_DTYPE_2D, )
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1, layer_name=filename, idx=-1)


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
    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)


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
    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)

##### Lowest Order functions
