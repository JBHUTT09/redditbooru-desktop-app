__author__ = 'John Huttlinger'

import sys
from PyQt4 import QtGui
import manage_gui


def main():
    app = QtGui.QApplication(sys.argv)
    image_path = None
    if len(sys.argv) > 1:
        image_path = ""
        for arg in sys.argv[1:]:
            image_path += arg + " "
        image_path = image_path.rstrip()
    gui = manage_gui.CheckerWidget(image_path)
    app.setActiveWindow(gui)
    gui.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()