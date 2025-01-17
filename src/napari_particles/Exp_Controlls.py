from qtpy.QtWidgets import QWidget, QPushButton, QLabel, QComboBox, QListWidget, QWidget
import napari
import numpy as np
from PyQt5.QtCore import Qt

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