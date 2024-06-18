import sys
import PyQt5
import main_window

if __name__ == '__main__':
    app = PyQt5.QtWidgets.QApplication(sys.argv)
    window = main_window.MainWindow()
    window.installEventFilter(window)
    window.show()
    sys.exit(app.exec_())