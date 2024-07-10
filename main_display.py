import sys
import copy
import cv2
import json
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QWidget, QFileDialog, QLabel, QGroupBox, QStatusBar, QTableWidget, QTableWidgetItem, QCheckBox, QLineEdit, QMenuBar, QMenu, QAction


class QLabelCanvas(QLabel):
    table_refresh_signal = pyqtSignal()

    def __init__(self):
        super(QLabel, self).__init__()
        self.setMouseTracking(True)
        self.draw_lines = False
        self.draw_lines_action_started = False
        self.canvas_orig = None

        # Free drawing (segmentation)
        self.free_drawing_start_point = None
        self.free_drawing_absolute_start_point = None
        self.temp_area = []

        # Bounding box
        self.draw_b_box = False
        self.draw_b_box_action_started = False
        self.b_box_start_corner = False
        self.canvas_last_frame = None
        self.marking_info = [] # [TYPE, LABEL, [CORNERS/POINTS], VISABILITY]

    def eventFilter(self, obj, event):
        # Free drawing
        if self.draw_lines:
            # Start
            if not self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.free_drawing_start_point = QPoint(event.pos().x(), event.pos().y())
                self.free_drawing_absolute_start_point = QPoint(event.pos().x(), event.pos().y())
                self.draw_lines_action_started = True

                self.temp_area = []
                self.temp_area.append(self.free_drawing_absolute_start_point)
            # Finish
            if self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_line_on_canvas_and_set_pixmap(self.free_drawing_start_point, curr_point)
                self.add_line_on_canvas_and_set_pixmap(curr_point, self.free_drawing_absolute_start_point)
                self.canvas_last_frame = self.canvas.copy()
                self.temp_area.append(curr_point)
                self.draw_lines_action_started = False
                self.marking_info.append(["Contour", "NO LABEL", self.temp_area, True])
                self.temp_area = []
                self.table_refresh_signal.emit()
            # Moving
            if self.draw_lines_action_started and event.type() == QEvent.MouseMove:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_line_on_canvas_and_set_pixmap(self.free_drawing_start_point, curr_point)
                self.free_drawing_start_point = curr_point
                self.temp_area.append(curr_point)

        # Bounding box
        elif self.draw_b_box:
            # Start
            if not self.draw_b_box_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.b_box_start_corner = QPoint(event.pos().x(), event.pos().y())
                self.draw_b_box_action_started = True
            # Finish
            if self.draw_b_box_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_bounding_box_on_canvas_and_set_pixmap(self.b_box_start_corner, curr_point)
                self.canvas_last_frame = self.canvas.copy()
                self.draw_b_box_action_started = False
                self.marking_info.append(["Bounding Box", "NO LABEL", [self.b_box_start_corner, curr_point], True])
                self.table_refresh_signal.emit()
            # Moving
            if self.draw_b_box_action_started and event.type() == QEvent.MouseMove:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_bounding_box_on_canvas_and_set_pixmap(self.b_box_start_corner, curr_point)

        return super(QLabelCanvas, self).eventFilter(obj, event)

    def add_bounding_box_on_canvas_and_set_pixmap(self, corner1, corner2):
        corner1_x = corner1.x()
        corner1_y = corner1.y()
        corner2_x = corner2.x()
        corner2_y = corner2.y()
        corner3 = QPoint(corner2_x, corner1_y)
        corner4 = QPoint(corner1_x, corner2_y)

        if self.canvas_last_frame is None:
            self.canvas = self.canvas_orig.copy()
        else:
            self.canvas = self.canvas_last_frame.copy()
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        self.painter.drawLine(corner1, corner3)
        self.painter.drawLine(corner3, corner2)
        self.painter.drawLine(corner2, corner4)
        self.painter.drawLine(corner4, corner1)
        self.painter.end()
        self.setPixmap(self.canvas)
        self.update()

    def initiate_canvas_and_set_pixmap(self, qpixmap):
        self.canvas = qpixmap
        self.set_and_update_pixmap()
        self.painter = QPainter(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        self.painter.end()

    def add_line_on_canvas_and_set_pixmap(self, start, end):
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        self.painter.drawLine(start, end)
        self.painter.end()
        self.setPixmap(self.canvas)
        self.update()

    def set_and_update_pixmap(self):
        self.setPixmap(self.canvas)
        self.update()

    def draw_bounding_box_on_pixmap_based_on_corners(self, corners):
        corner1 = corners[0]
        corner2 = corners[1]
        corner1_x = corner1.x()
        corner1_y = corner1.y()
        corner2_x = corner2.x()
        corner2_y = corner2.y()
        corner3 = QPoint(corner2_x, corner1_y)
        corner4 = QPoint(corner1_x, corner2_y)
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        self.painter.drawLine(corner1, corner3)
        self.painter.drawLine(corner3, corner2)
        self.painter.drawLine(corner2, corner4)
        self.painter.drawLine(corner4, corner1)
        self.painter.end()
        self.set_and_update_pixmap()

    def draw_areas_on_pixmap_based_on_points(self, points):
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        for i in range(0, len(points) - 1):
            self.painter.drawLine(points[i], points[i+1])
        self.painter.drawLine(points[-1], points[0])
        self.painter.end()
        self.set_and_update_pixmap()

    def refresh_pixmap_acc_to_vis(self):
        print("Refresh pixmap according to visualization")
        print(self.marking_info)
        self.canvas = self.canvas_orig.copy()
        self.set_and_update_pixmap()
        for i in range(0, len(self.marking_info)):
            if self.marking_info[i][0] == "Contour" and self.marking_info[i][-1]:
                self.draw_areas_on_pixmap_based_on_points(self.marking_info[i][2])
            elif self.marking_info[i][0] == "Bounding Box" and self.marking_info[i][-1]:
                self.draw_bounding_box_on_pixmap_based_on_corners(self.marking_info[i][2])
            else:
                pass

    def clear_all_markings(self):
        self.setPixmap(self.canvas_orig)
        self.update()
        self.canvas = self.canvas_orig.copy()
        self.marking_info = []
        self.canvas_last_frame = None
        self.table_refresh_signal.emit()

    def clear_selected_markings(self, selected_list):
        print("Clear selected markings")
        print("Selected list", selected_list)
        self.marking_info = [self.marking_info[i] for i in range(len(self.marking_info)) if not selected_list[i]]
        if len(self.marking_info) == 0:
            self.clear_all_markings()
        else:
            self.canvas = self.canvas_orig.copy()
            for i in range(0, len(self.marking_info)):
                if self.marking_info[i][0] == "Contour":
                    self.draw_areas_on_pixmap_based_on_points(self.marking_info[i][2])
                elif self.marking_info[i][0] == "Bounding Box":
                    self.draw_bounding_box_on_pixmap_based_on_corners(self.marking_info[i][2])
                else:
                    pass
            self.canvas_last_frame = self.canvas.copy()
            self.table_refresh_signal.emit()
