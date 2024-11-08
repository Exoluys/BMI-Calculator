from PyQt6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox,
                             QWidget, QGridLayout)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt
import sys
import pymysql

class DatabaseConnection:
    def __init__(self, host="localhost", user="root", password="jiya81203jai", database="bmi_calc"):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        connection = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        return connection


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BMI Calculator")
        self.setMinimumSize(350, 160)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QGridLayout()

        height_label = QLabel("Enter your height in cm: ")
        self.height_edit = QLineEdit()
        self.height_edit.setValidator(QIntValidator(0, 300))
        layout.addWidget(height_label, 0, 0)
        layout.addWidget(self.height_edit, 0, 1)

        weight_label = QLabel("Enter your weight in kg: ")
        self.weight_edit = QLineEdit()
        self.weight_edit.setValidator(QIntValidator(0, 300))
        layout.addWidget(weight_label, 1, 0)
        layout.addWidget(self.weight_edit, 1, 1)

        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculator)
        layout.addWidget(calculate_button, 2, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        self.result_label = QLabel("")
        layout.addWidget(self.result_label, 3, 0, 1, 2)

        central_widget.setLayout(layout)

    def calculator(self):
        try:
            height = float(self.height_edit.text())
            weight = float(self.weight_edit.text())

            cal = BMICalculator(height, weight)
            bmi = cal.calculate()
            self.display(bmi)

        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for height and weight.")

    def display(self, bmi):
        if bmi < 18.5:
            status = "Underweight"
        elif 18.5 <= bmi < 24.9:
            status = "Normal weight"
        elif 24.9 <= bmi < 29.9:
            status = "Overweight"
        else:
            status = "Obese"

        self.result_label.setText(f"{status} \nYour BMI is {bmi:.1f} kg/m\u00B2")


class BMICalculator:
    def __init__(self, height, weight):
        self.height = height
        self.weight = weight

    def calculate(self):
        height_in_meters = self.height / 100
        height_square = height_in_meters * height_in_meters
        BMI = self.weight/ height_square
        return BMI


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
