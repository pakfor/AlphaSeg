# -*- coding: utf-8 -*-
"""
Created on Sun Mar 10 15:29:00 2024

@author: NGPF
"""

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
                #print(curr_point)
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

    def draw_areas_on_pixmap_based_on_points(self, points):
        print("draw_areas_on_pixmap_based_on_points")
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        for i in range(0, len(points) - 1):
            self.painter.drawLine(points[i], points[i+1])
        self.painter.drawLine(points[-1], points[0])
        self.painter.end()
        self.set_and_update_pixmap()

    def refresh_pixmap_acc_to_check_box(self, points, areas_visualization_list):
        print("refresh_pixmap_acc_to_check_box")
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
        print("Remove: Length of self.areas", len(self.areas))
        if len(self.areas) == 0:
            self.clear_all_markings()
        else:
            self.canvas = self.canvas_orig.copy()
            for points in self.areas:
                self.draw_areas_on_pixmap_based_on_points(points)
            self.table_refresh_signal.emit()

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
        self.setFixedSize(QSize(1300, 900))

        # Menu Bar
        self.menu_bar = QMenuBar(self)
        self.file_menu = QMenu("&File", self)
        self.edit_menu = QMenu("&Edit", self)
        self.help_menu = QMenu("&Help", self)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.edit_menu)
        self.menu_bar.addMenu(self.help_menu)
        self.setMenuBar(self.menu_bar)
        self.open_action = QAction("&Open", self)
        self.open_action.triggered.connect(self.browse_image)
        self.file_menu.addAction(self.open_action)
        # Export
        self.export_mask_action = QAction("&Export Masks", self)
        self.export_mask_action.triggered.connect(self.export_mask)
        self.file_menu.addAction(self.export_mask_action)
        self.export_points_action = QAction("&Export Points", self)
        self.export_points_action.triggered.connect(self.export_points)
        self.file_menu.addAction(self.export_points_action)
        self.export_vis_action = QAction("&Export Visualizations", self)
        self.export_vis_action.triggered.connect(self.export_vis)
        self.file_menu.addAction(self.export_vis_action)
        # Import
        self.import_action = QAction("&Import", self)
        self.file_menu.addAction(self.import_action)
        self.pref_action = QAction("&Preferences", self)
        #self.pref_action.triggered.connect(self.open_pref_window)
        self.edit_menu.addAction(self.pref_action)

        # Status bar
        self.base_status_bar = QStatusBar()
        self.setStatusBar(self.base_status_bar)
        status_base_info = QLabel()
        status_base_info.setText(f"Version: {self.VERSION}    Release Date: {self.RELEASE_DATE}    Composer: {self.COMPOSER}")
        self.base_status_bar.addPermanentWidget(status_base_info)

        base_widget = QWidget(self)
        self.setCentralWidget(base_widget)

        main_h_layout = QHBoxLayout()

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
        seg_label_list_group.setMaximumWidth(400)
        seg_label_list_v_layout = QVBoxLayout()

        self.seg_label_list_table = QTableWidget()
        self.seg_label_list_table.setColumnCount(4)
        self.seg_label_list_table.setHorizontalHeaderLabels(["Select", "Show", "Label", "No. of Points"])
        self.seg_label_list_table.setWordWrap(True)
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)
        #self.seg_label_list_table.itemClicked.connect(self.refresh_pixmap_with_visualization_option)

        seg_label_list_function_h_layout = QHBoxLayout()
        self.remove_mask_button = QPushButton("Remove Selected")
        self.remove_mask_button.clicked.connect(self.remove_selected)
        seg_label_list_function_h_layout.addWidget(self.remove_mask_button)

        seg_label_list_function_h_layout_2 = QHBoxLayout()
        self.remove_all_mask_button = QPushButton("Remove All")
        self.remove_all_mask_button.clicked.connect(self.old_image_pixmap.clear_all_markings)
        seg_label_list_function_h_layout_2.addWidget(self.remove_all_mask_button)

        seg_label_list_v_layout.addWidget(self.seg_label_list_table)
        seg_label_list_v_layout.addLayout(seg_label_list_function_h_layout)
        seg_label_list_v_layout.addLayout(seg_label_list_function_h_layout_2)
        seg_label_list_group.setLayout(seg_label_list_v_layout)

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
        self.image_width_orig = image_arr.shape[1]
        self.image_height_orig = image_arr.shape[0]
        self.qpixmap = QPixmap.fromImage(qimage)
        self.qpixmap = self.qpixmap.scaled(700, 700, Qt.KeepAspectRatio)
        self.qpixmap_orig = self.qpixmap.copy()
        print(self.qpixmap.rect())
        self.image_width_scaled = self.qpixmap_orig.rect().width()
        self.image_height_scaled = self.qpixmap_orig.rect().height()
        self.old_image_pixmap.canvas_orig = self.qpixmap_orig
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
        tif_image = (normalize_image(np.stack((tif_red, tif_green, tif_blue), axis=2)) * 255.0).astype('uint8')
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
        self.area_visible = self.old_image_pixmap.area_visible
        self.seg_label_list_table.clearContents()
        self.seg_label_list_table.setRowCount(0)

        for i in range(0, len(self.areas)):
            self.seg_label_list_table.insertRow(self.seg_label_list_table.rowCount())

            # Check box for selection
            table_select_check_box = QCheckBox()
            table_select_check_box.setCheckState(False)

            # Check box for visualization option
            table_show_check_box = QCheckBox()
            table_show_check_box.setCheckState(self.area_visible[i])
            table_show_check_box.clicked.connect(self.refresh_pixmap_with_visualization_option)

            # Labels for marked areas
            #table_area_label_label = QLabel(str(self.area_labels[i]))
            table_area_label_text = QLineEdit()
            table_area_label_text.setText(str(self.area_labels[i]))
            table_area_label_text.textChanged.connect(self.refresh_area_labels)

            # Labels for number of marked points that define the areas
            table_number_of_area_points = QLabel(str(len(self.areas[i])))

            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 0, table_select_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 1, table_show_check_box)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 2, table_area_label_text)
            self.seg_label_list_table.setCellWidget(self.seg_label_list_table.rowCount() - 1, 3, table_number_of_area_points)

            #self.seg_label_list_table.setItem(self.seg_label_list_table.rowCount() - 1, 2, QTableWidgetItem(str(self.area_labels[i])))
            #self.seg_label_list_table.setItem(self.seg_label_list_table.rowCount() - 1, 3, QTableWidgetItem(str(len(self.areas[i]))))

    def refresh_pixmap_with_visualization_option(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            checked_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                print(self.seg_label_list_table.cellWidget(i, 1))
                if self.seg_label_list_table.cellWidget(i, 1).isChecked():
                    checked_list.append(True)
                else:
                    checked_list.append(False)
            self.old_image_pixmap.area_visible = checked_list
            self.old_image_pixmap.refresh_pixmap_acc_to_check_box(self.areas, checked_list)

    def refresh_area_labels(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            area_label_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                area_label_list.append(self.seg_label_list_table.cellWidget(i, 2).text())
            self.old_image_pixmap.area_labels = area_label_list

    def reset_pixmap(self):
        self.old_image_pixmap.setPixmap(self.qpixmap_orig)
        self.old_image_pixmap.update()

    def export_mask(self):
        self.export_areas(None, "mask", None)

    def export_points(self):
        self.export_areas(None, "points", None)

    def export_vis(self):
        self.export_areas(None, "vis", None)

    def export_areas(self, areas, mode, save_dir):
        if mode == "mask":
            save_file_as_npy_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;NPY (*.npy)")[0]
            # Assumed the image is scaled with the same ratio along its width and height
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            #print("Image scaled ratio", image_scaled_ratio)
            area_labels_set = list(set(self.old_image_pixmap.area_labels))
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            number_of_classes = len(area_labels_set)
            mask_npy = np.zeros((int(self.image_height_orig), int(self.image_width_orig), number_of_classes))
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                points_ready = np.array(points_ready)
                point_specific_label = area_labels[i]
                index = area_labels_set.index(point_specific_label)
                mask_temp = mask_npy[:, :, index]
                cv2.fillPoly(mask_temp, [points_ready], (1))
                plt.imshow(mask_temp)
                plt.show()
                mask_npy[:, :, index] = mask_temp
            np.save(save_file_as_npy_dir, mask_npy)
        elif mode == "points":
            save_file_as_json_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;JSON (*.json)")[0]
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            point_label_pair_dict = {}
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                point_specific_label = area_labels[i]
                if point_specific_label not in point_label_pair_dict.keys():
                    point_label_pair_dict[point_specific_label] = [points_ready]
                else:
                    point_label_pair_dict[point_specific_label].append(points_ready)
            #point_label_pair_json = json.dumps(point_label_pair_dict, indent = 4)
            save_as_json = open(save_file_as_json_dir, "w")
            json.dump(point_label_pair_dict, save_as_json, indent=4)
            save_as_json.close()
        elif mode == "vis":
            save_file_as_vis_dir = QFileDialog.getSaveFileName(self, "Save File", "", "All Files (*);;PNG (*.png)")[0]
            # Assumed the image is scaled with the same ratio along its width and height
            image_scaled_ratio = int(self.image_height_orig) / int(self.image_height_scaled)
            #print("Image scaled ratio", image_scaled_ratio)
            area_labels_set = list(set(self.old_image_pixmap.area_labels))
            area_labels = self.old_image_pixmap.area_labels
            points = self.old_image_pixmap.areas
            number_of_classes = len(area_labels_set)
            mask_npy = np.zeros((int(self.image_height_orig), int(self.image_width_orig), number_of_classes))
            for i in range(0, len(points)):
                points_ready = []
                for j in range(0, len(points[i])):
                    points_ready.append([min([int(points[i][j].x() * image_scaled_ratio), int(self.image_width_orig) - 1]),
                                         min([int(points[i][j].y() * image_scaled_ratio), int(self.image_height_orig) - 1])])
                points_ready = np.array(points_ready)
                point_specific_label = area_labels[i]
                index = area_labels_set.index(point_specific_label)
                mask_temp = mask_npy[:, :, index]
                cv2.fillPoly(mask_temp, [points_ready], (1))
                #plt.imshow(mask_temp)
                #plt.show()
                mask_npy[:, :, index] = mask_temp
            for i in range(0, len(area_labels_set)):
                label_mask = mask_npy[:, :, i]
                label_specific_save_dir = save_file_as_vis_dir.replace("." + save_file_as_vis_dir.split(".")[-1], "_" + area_labels_set[i] + "." + save_file_as_vis_dir.split(".")[-1])
                plt.imsave(label_specific_save_dir, self.image_mask_overlay(self.orig_image, label_mask), vmin=0.0, vmax=255.0)
        else:
            pass

    # Remove Markings ########################################################
    def remove_selected(self):
        if self.seg_label_list_table.rowCount() == 0:
            pass
        else:
            checked_list = []
            for i in range(0, self.seg_label_list_table.rowCount()):
                if self.seg_label_list_table.cellWidget(i, 0).isChecked():
                    checked_list.append(True)
                else:
                    checked_list.append(False)
            print("Remove: Checked list", checked_list)
            self.old_image_pixmap.clear_selected_markings(checked_list)

    # Visualization ##########################################################
    def image_mask_overlay(self, image_orig, mask):
        print(np.max(image_orig), np.min(image_orig))
        image_orig[:, :, 0][mask!=0] = 240
        return image_orig

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.installEventFilter(window)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
