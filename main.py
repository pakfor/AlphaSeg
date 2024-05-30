# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 15:29:00 2024

@author: NGPF
"""

import sys
import numpy as np
import copy
import cv2
from PIL import Image, ImageQt
from PyQt5.QtCore import QEvent, QSize, Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox, QWidget, QFileDialog, QLabel, QGroupBox, QStatusBar, QTableWidget, QTableWidgetItem


class QLabelCanvas(QLabel):
    table_refresh_signal = pyqtSignal()

    def __init__(self):
        super(QLabel, self).__init__()
        self.setMouseTracking(True)
        self.draw_lines = False
        self.draw_lines_action_started = False

        # Free drawing (segmentation)
        self.free_drawing_start_point = None
        self.free_drawing_absolute_start_point = None
        self.temp_area = []
        self.areas = []
        self.area_labels = []

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
                self.temp_area = []
                self.table_refresh_signal.emit()

            if self.draw_lines_action_started and event.type() == QEvent.MouseMove:
                curr_point = QPoint(event.pos().x(), event.pos().y())
                #print(f"Current Point: {curr_point}")
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


class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        # Basic software information
        self.VERSION = "0.3.0"
        self.RELEASE_DATE = "11-Mar-2024"
        self.COMPOSER = "NGPF"

        self.orig_image = None
        self.orig_image_dir = None
        self.new_image = None
        self.new_image_dir = None

        self.setWindowTitle(f"AlphaSEG - V.{self.VERSION}")
        self.setFixedSize(QSize(1600, 900))

        # Status bar
        self.base_status_bar = QStatusBar()
        self.setStatusBar(self.base_status_bar)
        status_base_info = QLabel()
        status_base_info.setText(f"Version: {self.VERSION}    Release Date: {self.RELEASE_DATE}    Composer: {self.COMPOSER}")
        self.base_status_bar.addPermanentWidget(status_base_info)

        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)

        main_h_layout = QHBoxLayout()
        function_v_widget = QWidget()
        function_v_widget.setFixedWidth(150)
        function_v_layout = QVBoxLayout()

        io_group = QGroupBox("File")
        io_v_layout = QVBoxLayout()
        import_button = QPushButton("Import")
        import_button.clicked.connect(self.browse_image)
        #export_option = QComboBox()
        #export_option.addItems(["PNG", "JPG"])
        #export_option.setCurrentText("PNG")
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.save_image)
        io_v_layout.addWidget(import_button)
        #io_v_layout.addWidget(export_option)
        io_v_layout.addWidget(export_button)
        io_group.setLayout(io_v_layout)

        function_v_layout.addWidget(io_group)
        function_v_widget.setLayout(function_v_layout)

        old_image_group = QGroupBox("VIEW")
        old_image_v_layout = QVBoxLayout()

        self.old_image_pixmap = QLabelCanvas()
        self.old_image_pixmap.installEventFilter(self.old_image_pixmap)
        self.old_image_pixmap.table_refresh_signal.connect(self.refresh_seg_label_list_table)

        self.old_image_size_label = QLabel()
        self.old_image_dir_label = QLabel()
        toolbar_h_layout = QHBoxLayout()

        self.draw_polygon_button = QPushButton("CREATE MASK")
        self.draw_polygon_button.setCheckable(True)
        self.draw_polygon_button.clicked.connect(self.enable_drawing)
        toolbar_h_layout.addWidget(self.draw_polygon_button)

        old_image_v_layout.addWidget(self.old_image_dir_label)
        old_image_v_layout.addWidget(self.old_image_size_label)
        old_image_v_layout.addWidget(self.old_image_pixmap)
        old_image_v_layout.addLayout(toolbar_h_layout)
        old_image_group.setLayout(old_image_v_layout)

        seg_label_list_group = QGroupBox("MASK AND LABEL")
        seg_label_list_group.setMaximumWidth(500)
        seg_label_list_v_layout = QVBoxLayout()

        self.seg_label_list_table = QTableWidget()
        self.seg_label_list_table.setColumnCount(3)
        self.seg_label_list_table.setHorizontalHeaderLabels(["Seg. No.", "No. of Points", "Label"])
        self.seg_label_list_table.setWordWrap(True)
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        seg_label_list_v_layout.addWidget(self.seg_label_list_table)
        seg_label_list_group.setLayout(seg_label_list_v_layout)

        main_h_layout.addWidget(function_v_widget)
        main_h_layout.addWidget(old_image_group)
        main_h_layout.addWidget(seg_label_list_group)
        base_widget.setLayout(main_h_layout)

    def enable_drawing(self):
        if self.draw_polygon_button.isChecked():
            self.old_image_pixmap.draw_lines = True
        else:
            self.old_image_pixmap.draw_lines = False

    def set_pixmap_from_array(self, image_arr):
        qimage = QImage(image_arr, image_arr.shape[1], image_arr.shape[0], QImage.Format_RGB888)
        self.qpixmap = QPixmap.fromImage(qimage)
        self.qpixmap = self.qpixmap.scaled(700, 700, Qt.KeepAspectRatio)
        self.old_image_pixmap.initiate_canvas_and_set_pixmap(self.qpixmap)

    def process_tif(self, tif_image):
        def normalize_image(image):
            imin, imax = np.min(image), np.max(image)
            irange = abs(imax - imin)
            if irange == 0:
                return image
            else:
                return (image - imin) / irange
        tif_red = tif_image[:, :, 2]
        tif_green = tif_image[:, :, 1]
        tif_blue = tif_image[:, :, 0]
        tif_image = (normalize_image(np.stack((tif_red, tif_green, tif_blue), axis=2)) * 255.0).astype('int8')
        return tif_image

    def browse_image(self):
        support_file_format = ["png", "PNG", "jpg", "JPG", "tif", "TIF", "tiff", "TIFF"]
        open_file = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;PNG (*.png;*.PNG);;JPEG (*.jpg;*.JPG);;TIFF (*.tif;*.TIF;*.tiff;*.TIFF")[0]
        if open_file[-3:] in support_file_format:
            self.orig_image_dir = open_file
            self.orig_image = self.image_loader(self.orig_image_dir)
            self.set_pixmap_from_array(self.orig_image)
            self.old_image_size_label.setText(f"Size: {self.orig_image.shape[1]} x {self.orig_image.shape[0]}")
            self.old_image_dir_label.setText(f"{self.orig_image_dir}")
        elif open_file == "":
            pass
        else:
            return

    def save_image(self):
        save_file = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;PNG (*.png;*.PNG);;JPEG (*.jpg;*.JPG)")[0]
        self.new_image_dir = save_file
        image_to_save = copy.deepcopy(self.new_image)
        image_to_save = image_to_save.astype(np.uint8)
        image_to_save_pil = Image.fromarray(image_to_save)
        image_to_save_pil.save(self.new_image_dir)

    def image_loader(self, image_dir):
        if image_dir.split(".")[-1] in ["tif", "TIF", "tiff", "TIFF"]:
            return self.process_tif(cv2.imread(image_dir, -1))
        return np.array(Image.open(image_dir))

    def refresh_seg_label_list_table(self):
        self.areas = self.old_image_pixmap.areas
        self.area_labels = self.old_image_pixmap.area_labels
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        for i in range(0, len(self.areas)):
            self.seg_label_list_table.insertRow(self.seg_label_list_table.rowCount())
            self.seg_label_list_table.setItem(self.seg_label_list_table.rowCount() - 1, 0, QTableWidgetItem(str(i + 1)))
            self.seg_label_list_table.setItem(self.seg_label_list_table.rowCount() - 1, 1, QTableWidgetItem(str(len(self.areas[i]))))
            self.seg_label_list_table.setItem(self.seg_label_list_table.rowCount() - 1, 2, QTableWidgetItem(str(self.area_labels[i])))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.installEventFilter(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
