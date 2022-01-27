from PyQt5.QtGui import QPaintEvent, QPainter, QPalette, QBrush, QMouseEvent
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget,  QPushButton, QLabel, QComboBox, QListWidget
from PyQt5.QtWidgets import QGridLayout, QStyleOptionSlider, QSlider, QSizePolicy, QStyle, QApplication, QLineEdit, \
    QCheckBox
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QRect, QSize
from smlm_main import *
import napari


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
        self.Brenderoptions.addItems(["variable gaussian", "fixed gaussian"])
        self.Brenderoptions.currentIndexChanged.connect(self.render_options_changed)
        layout.addWidget(self.Brenderoptions, 3, 1)

        self.Lsigma = QLabel()
        self.Lsigma.setText("PSF FWHM in XY [nm]:")
        layout.addWidget(self.Lsigma, 4, 0)

        self.Lsigma2 = QLabel()
        self.Lsigma2.setText("PSF FWHM in Z [nm]:")
        layout.addWidget(self.Lsigma2, 5, 0)

        self.Esigma = QLineEdit()
        self.Esigma.setText("300")
        self.Esigma.textChanged.connect(lambda: self.start_typing_timer(self.typing_timer_sigma))
        layout.addWidget(self.Esigma, 4, 1)
        self.typing_timer_sigma = QtCore.QTimer()
        self.typing_timer_sigma.setSingleShot(True)
        self.typing_timer_sigma.timeout.connect(lambda: update_layers(self))

        self.Esigma2 = QLineEdit()
        self.Esigma2.setText("700")
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


        layout.setColumnStretch(0, 2)
        self.setLayout(layout)

        self.Sz.hide()
        self.Lrangez.hide()
        self.Lresetview.hide()
        self.Baxis.hide()
        self.L3d.hide()
        self.C3d.hide()

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
        print("Dataset removal not implemented yet...", item)


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return SMLMQW









