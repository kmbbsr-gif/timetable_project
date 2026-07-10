# PySide6 desktop entry point – minimal placeholder
import sys
from PySide6.QtWidgets import QApplication, QLabel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    label = QLabel("Timetable Desktop App (Coming Soon)")
    label.show()
    sys.exit(app.exec())