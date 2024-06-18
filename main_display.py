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
        self.areas = []
        self.area_labels = []
        self.area_visible = []

    def eventFilter(self, obj, event):
        if self.draw_lines:
            if not self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.free_drawing_start_point = QPoint(event.pos().x(), event.pos().y())
                self.free_drawing_absolute_start_point = QPoint(event.pos().x(), event.pos().y())
                self.draw_lines_action_started = True

                self.temp_area = []
                self.temp_area.append(self.free_drawing_absolute_start_point)

            if self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_line_on_canvas_and_set_pixmap(self.free_drawing_start_point, curr_point)
                self.add_line_on_canvas_and_set_pixmap(curr_point, self.free_drawing_absolute_start_point)
                self.temp_area.append(curr_point)
                self.draw_lines_action_started = False

                self.areas.append(self.temp_area)
                self.area_labels.append("NO LABEL")
                self.area_visible.append(True)
                self.temp_area = []
                self.table_refresh_signal.emit()

            if self.draw_lines_action_started and event.type() == QEvent.MouseMove:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                self.add_line_on_canvas_and_set_pixmap(self.free_drawing_start_point, curr_point)
                self.free_drawing_start_point = curr_point
                self.temp_area.append(curr_point)

        return super(QLabelCanvas, self).eventFilter(obj, event)

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

    def draw_areas_on_pixmap_based_on_points(self, points):
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        for i in range(0, len(points) - 1):
            self.painter.drawLine(points[i], points[i+1])
        self.painter.drawLine(points[-1], points[0])
        self.painter.end()
        self.set_and_update_pixmap()

    def refresh_pixmap_acc_to_check_box(self, points, areas_visualization_list):
        self.canvas = self.canvas_orig.copy()
        self.set_and_update_pixmap()
        for i in range(0, len(areas_visualization_list)):
            if areas_visualization_list[i]:
                self.draw_areas_on_pixmap_based_on_points(points[i])
            else:
                pass

    def clear_all_markings(self):
        self.setPixmap(self.canvas_orig)
        self.update()
        self.canvas = self.canvas_orig.copy()
        self.areas = []
        self.area_labels = []
        self.table_refresh_signal.emit()

    def clear_selected_markings(self, selected_list):
        self.areas = [self.areas[i] for i in range(len(self.areas)) if not selected_list[i]]
        self.area_labels = [self.area_labels[i] for i in range(len(self.area_labels)) if not selected_list[i]]
        if len(self.areas) == 0:
            self.clear_all_markings()
        else:
            self.canvas = self.canvas_orig.copy()
            for points in self.areas:
                self.draw_areas_on_pixmap_based_on_points(points)
            self.table_refresh_signal.emit()