from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import matplotlib.pyplot as plt


class QLabelCanvas(QLabel):
    table_refresh_signal = pyqtSignal()

    def __init__(self):
        super(QLabel, self).__init__()
        self.setMouseTracking(True)
        self.draw_lines = False
        self.draw_lines_action_started = False
        self.canvas_orig = None
        self.canvas_zoom = None # Store image after zoom (by Ricky)

        # Basic information
        self.canvas_array = None  # Scale it and get the pixmap directly
        self.canvas_orig_size = None  # (Width, Height)
        self.canvas_display_size = None  # (Width, Height)
        self.canvas_scaling = None  # Orig / Display
        self.canvas_orig_anchor = (0, 0)  # (X, Y)

        # Free drawing (segmentation)
        self.free_drawing_start_point = None
        self.free_drawing_absolute_start_point = None
        self.temp_area = []

        # Bounding box
        self.draw_b_box = False
        self.draw_b_box_action_started = False
        self.b_box_start_corner = False
        self.canvas_last_frame = None
        self.marking_info = [] # [TYPE, LABEL, [CORNERS/POINTS], NUMBER VISABILITY, VISABILITY]

        # Zoom in/out
        self.zoom = False
        self.zoom_started = False
        self.zoom_start_corner = False
        self.zoom_corner1 = None
        self.zoom_corner2 = None

    ##########################################################################
    ## Canvas Update Function ################################################
    ##########################################################################
    def initiate_canvas_and_set_pixmap(self, qpixmap):
        self.canvas = qpixmap
        self.set_and_update_pixmap()
        self.painter = QPainter(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        self.painter.end()
        self.text_painter = QPainter(self.canvas)
        self.text_painter.setPen(QPen(Qt.black))
        font = QFont()
        font.setFamily('Times')
        font.setBold(True)
        font.setPointSize(24)
        self.text_painter.setFont(font)
        self.text_painter.end()


    def set_and_update_pixmap(self):
        self.setPixmap(self.canvas)
        self.update()

    # Show selected function
    def refresh_pixmap_acc_to_vis(self):
        if self.zoom:
            self.canvas = self.canvas_zoom.copy()
            self.set_and_update_pixmap()
            self.zoom_to_vis()
        else:
            self.canvas = self.canvas_orig.copy()
            self.set_and_update_pixmap()
            for i in range(0, len(self.marking_info)):
                if self.marking_info[i][0] == "Contour" and self.marking_info[i][3] and self.marking_info[i][-1]:
                    self.draw_contour(self.marking_info[i][2], dynamic=False, number=i+1)
                elif self.marking_info[i][0] == "Bounding Box" and self.marking_info[i][3] and self.marking_info[i][-1]:
                    self.draw_bounding_box(self.marking_info[i][2], dynamic=False, number=i+1)
                elif self.marking_info[i][0] == "Contour" and self.marking_info[i][-1]:
                    self.draw_contour(self.marking_info[i][2], dynamic=False)
                elif self.marking_info[i][0] == "Bounding Box" and self.marking_info[i][-1]:
                    self.draw_bounding_box(self.marking_info[i][2], dynamic=False)
                else:
                    pass

    # Clear markings
    def clear_all_markings(self):
        self.marking_info = []
        self.canvas_last_frame = None
        self.table_refresh_signal.emit()
        self.replace_canvas_with_zoom(self.zoom_corner1, self.zoom_corner2)

    # Clear selected markings
    def clear_selected_markings(self, selected_list):
        self.marking_info = [self.marking_info[i] for i in range(len(self.marking_info)) if not selected_list[i]]
        if len(self.marking_info) == 0:
            self.clear_all_markings()
        else:
            self.replace_canvas_with_zoom(self.zoom_corner1, self.zoom_corner2)
            self.canvas_last_frame = self.canvas.copy()
            self.table_refresh_signal.emit()

    def replace_canvas_origin(self):
        self.replace_canvas_with_zoom(QPoint(0, 0), QPoint(self.canvas_array.shape[1], self.canvas_array.shape[0]))

    def replace_canvas_with_zoom(self, corner1, corner2):
        self.zoom_corner1 = corner1
        self.zoom_corner2 = corner2
        x_max = max(corner1.x(), corner2.x())
        y_max = max(corner1.y(), corner2.y())
        x_min = min(corner1.x(), corner2.x())
        y_min = min(corner1.y(), corner2.y())
        if (x_max-x_min)>(y_max-y_min):
            y_max = y_min + (x_max-x_min)
        elif (x_max-x_min)<(y_max-y_min):
            x_max = x_min + (y_max-y_min)
        zoomed_array = self.canvas_array[y_min:y_max, x_min:x_max, :].astype('uint8')
        qimage = QImage(zoomed_array, zoomed_array.shape[1], zoomed_array.shape[0], 3 * zoomed_array.shape[1], QImage.Format_RGB888)
        qpixmap = QPixmap.fromImage(qimage)
        qpixmap = qpixmap.scaled(self.canvas_display_size[0], self.canvas_display_size[1], Qt.KeepAspectRatio)
        self.canvas = qpixmap.copy()
        self.set_and_update_pixmap()
        self.canvas_zoom = qpixmap.copy()
        self.canvas_orig_size = (zoomed_array.shape[1], zoomed_array.shape[0])
        self.canvas_scaling = self.canvas_orig_size[0] / self.canvas_display_size[0]
        self.canvas_orig_anchor = (x_min, y_min)
        # Draw markings
        self.zoom_to_vis()
        self.canvas_last_frame = self.canvas.copy()
    
    def zoom_to_vis(self):
        for i in range(0, len(self.marking_info)):
            if self.marking_info[i][0] == "Contour" and self.marking_info[i][3] and self.marking_info[i][-1]:
                self.draw_contour(self.marking_info[i][2], dynamic=False, anchor=self.canvas_orig_anchor, number=i+1)
            elif self.marking_info[i][0] == "Bounding Box" and self.marking_info[i][3] and self.marking_info[i][-1]:
                self.draw_bounding_box(self.marking_info[i][2], dynamic=False, anchor=self.canvas_orig_anchor, number=i+1)
            elif self.marking_info[i][0] == "Contour" and self.marking_info[i][-1]:
                self.draw_contour(self.marking_info[i][2], dynamic=False, anchor=self.canvas_orig_anchor)
            elif self.marking_info[i][0] == "Bounding Box" and self.marking_info[i][3] and self.marking_info[i][-1]:
                self.draw_bounding_box(self.marking_info[i][2], dynamic=False, anchor=self.canvas_orig_anchor)
            else:
                pass

    ##########################################################################
    ## Event Filter for Drawing Function #####################################
    ##########################################################################
    def eventFilter(self, obj, event):
        # Free drawing
        if self.draw_lines:
            # Start
            if not self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # All QPoint in real scale
                self.free_drawing_start_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.free_drawing_absolute_start_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_lines_action_started = True
                self.temp_area = []
                self.temp_area.append(self.free_drawing_absolute_start_point)
                self.canvas_last_frame = self.canvas.copy()
            # Finish
            if self.draw_lines_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                # All QPoint in real scale
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.temp_area.append(curr_point)
                #self.draw_contour([self.free_drawing_start_point, curr_point], dynamic=True, anchor=self.canvas_orig_anchor)
                #self.draw_contour([curr_point, self.free_drawing_absolute_start_point], dynamic=True, anchor=self.canvas_orig_anchor)
                self.canvas = self.canvas_last_frame.copy()
                self.draw_contour(self.temp_area, dynamic=False, anchor=self.canvas_orig_anchor, number=len(self.marking_info)+1)
                self.canvas_last_frame = self.canvas.copy()
                self.draw_lines_action_started = False
                self.marking_info.append(["Contour", "NO LABEL", self.temp_area, True, True])
                self.temp_area = []
                self.table_refresh_signal.emit()
            # Moving
            if self.draw_lines_action_started and event.type() == QEvent.MouseMove:
                # All QPoint in real scale
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_contour([self.free_drawing_start_point, curr_point], dynamic=True, anchor=self.canvas_orig_anchor)
                self.free_drawing_start_point = curr_point
                self.temp_area.append(curr_point)
        # Bounding box
        elif self.draw_b_box:
            # Start
            if not self.draw_b_box_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # All QPoint in real scale
                self.b_box_start_corner = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_b_box_action_started = True
            # Finish
            if self.draw_b_box_action_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                # All QPoint in real scale
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_bounding_box([self.b_box_start_corner, curr_point], dynamic=True, anchor=self.canvas_orig_anchor, number=len(self.marking_info)+1)
                self.canvas_last_frame = self.canvas.copy()
                self.draw_b_box_action_started = False
                self.marking_info.append(["Bounding Box", "NO LABEL", [self.b_box_start_corner, curr_point], True, True])
                self.table_refresh_signal.emit()
            # Moving
            if self.draw_b_box_action_started and event.type() == QEvent.MouseMove:
                # All QPoint in real scale
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_bounding_box([self.b_box_start_corner, curr_point], dynamic=True, anchor=self.canvas_orig_anchor)
        # Zoom
        elif self.zoom:
            # Start
            if not self.zoom_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                self.zoom_start_corner = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.zoom_started = True
            # Finish
            if self.zoom_started and event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.zoom_started = False
                self.replace_canvas_with_zoom(self.zoom_start_corner, curr_point)
            # Moving
            if self.zoom_started and event.type() == QEvent.MouseMove:
                curr_point = self.scale_points([QPoint(event.pos().x(), event.pos().y())], to_display=False, anchor=self.canvas_orig_anchor)[0]
                self.draw_bounding_box([self.zoom_start_corner, curr_point], dynamic=True, anchor=self.canvas_orig_anchor)

        return super(QLabelCanvas, self).eventFilter(obj, event)

    ##########################################################################
    ## Drawing Function ######################################################
    ##########################################################################
    def scale_points(self, points, to_display=True, anchor=(0, 0)):
        # Input: points = [QPoint, QPoint, ...]
        # Input: to_real: Define whether changing the points from display scale to real scale, or inverse
        # Real X = Display X * Scaling + Anchor X
        # Display X = (Real X - Anchor X) / Scaling
        # QPoints in real scale (relative to image original size)
        scaled_points = []
        for i in range(0, len(points)):
            if to_display:
                scaled_single_point = QPoint(int((points[i].x() - anchor[0]) / self.canvas_scaling),
                                             int((points[i].y() - anchor[1]) / self.canvas_scaling))
            else:
                scaled_single_point = QPoint(int(points[i].x() * self.canvas_scaling + anchor[0]),
                                             int(points[i].y() * self.canvas_scaling + anchor[1]))
            scaled_points.append(scaled_single_point)
        return scaled_points

    def draw_bounding_box(self, corners, dynamic=False, anchor=(0, 0), number=None):
        # Input: corners = [QPoint, QPoint]
        # Corners in real scale (relative to image original size)
        corners = self.scale_points(corners, to_display=True, anchor=anchor)
        corner1 = corners[0]
        corner2 = corners[1]
        corner1_x = corner1.x()
        corner1_y = corner1.y()
        corner2_x = corner2.x()
        corner2_y = corner2.y()
        corner3 = QPoint(corner2_x, corner1_y)
        corner4 = QPoint(corner1_x, corner2_y)
        if dynamic:
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
        if number is not None:
            self.text_painter.begin(self.canvas)
            text_x, text_y = int((corner1_x + corner2_x) / 2), int((corner1_y + corner2_y) / 2)
            self.text_painter.drawText(text_x, text_y, str(number))
            self.text_painter.end()
        else:
            pass
        self.set_and_update_pixmap()

    def draw_contour(self, points, dynamic=False, anchor=(0, 0), number=None):
        def find_central_point(points):
            # Input (points): [QPoint, QPoint, ...]
            x, y = [], []
            for i in range(0, len(points)):
                x.append(int(points[i].x()))
                y.append(int(points[i].y()))
            return int((max(x) + min(x)) / 2), int((max(y) + min(y)) / 2)
        # Input: points = [[QPoint(), QPoint[]]]
        points = self.scale_points(points, to_display=True, anchor=anchor)
        self.painter.begin(self.canvas)
        self.painter.setPen(QPen(Qt.black))
        if dynamic:
            self.painter.drawLine(points[0], points[1])
            self.painter.end()
        else:
            for i in range(0, len(points) - 1):
                self.painter.drawLine(points[i], points[i + 1])
            self.painter.drawLine(points[-1], points[0])
            self.painter.end()
            # Add number
            if number is not None:
                self.text_painter.begin(self.canvas)
                text_x, text_y = find_central_point(points)
                self.text_painter.drawText(text_x, text_y, str(number))
                self.text_painter.end()
            else:
                pass
        self.set_and_update_pixmap()
