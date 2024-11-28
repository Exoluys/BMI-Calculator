import os
from PyQt6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox,
                             QWidget, QGridLayout, QDialog, QTableWidget, QTableWidgetItem)
from PyQt6.QtGui import QIntValidator, QIcon, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


class DatabaseConnection:
    """
    Handles MySQL database connections and table creation for storing BMI records.
    """

    def __init__(self, host="localhost", user=os.getenv("user"), password=os.getenv("password"), database="bmi_calc"):
        """
        Initializes the database connection parameters using environment variables for security.
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database

    def connect(self):
        """
        Establishes and returns a connection to the database.
        """
        connection = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.database)
        return connection

    def create_table(self, username):
        """
        Creates a user-specific table for storing BMI records if it doesn't already exist.
        """
        try:
            connection = self.connect()
            cursor = connection.cursor()

            # Dynamically create a table for the given username
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS bmi_records_{username} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) NOT NULL,
                    height_cm FLOAT NOT NULL,
                    weight_kg FLOAT NOT NULL,
                    bmi FLOAT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    record_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()
        except pymysql.MySQLError as e:
            print(f"Database Error: {e}")
        finally:
            if 'connection' in locals() and connection.open:
                cursor.close()
                connection.close()


class MainWindow(QMainWindow):
    """
    Main application window for the BMI Calculator, providing user interaction with input fields,
    BMI calculation, and database storage.
    """

    def __init__(self):
        """
        Initializes the main window and sets up the user interface.
        """
        super().__init__()
        self.setWindowTitle("BMI Calculator")
        self.setWindowIcon(QIcon("icon.png"))
        self.setMinimumSize(380, 200)

        # Create central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QGridLayout()
        layout.setHorizontalSpacing(20)

        # Name input field
        name_label = QLabel("Enter your name:")
        self.name_edit = QLineEdit()
        self.name_edit.setValidator(QRegularExpressionValidator(QRegularExpression(r"^[A-Za-z\s]*$")))
        layout.addWidget(name_label, 0, 0)
        layout.addWidget(self.name_edit, 0, 1)

        # Height input field
        height_label = QLabel("Enter your height in cm:")
        self.height_edit = QLineEdit()
        self.height_edit.setValidator(QIntValidator(0, 300))
        layout.addWidget(height_label, 1, 0)
        layout.addWidget(self.height_edit, 1, 1)

        # Weight input field
        weight_label = QLabel("Enter your weight in kg:")
        self.weight_edit = QLineEdit()
        self.weight_edit.setValidator(QIntValidator(0, 300))
        layout.addWidget(weight_label, 2, 0)
        layout.addWidget(self.weight_edit, 2, 1)

        # Calculate button
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculator)
        layout.addWidget(calculate_button, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)

        # History button
        self.history_button = QPushButton("History")
        self.history_button.clicked.connect(self.history)
        layout.addWidget(self.history_button, 3, 1, 1, 2, Qt.AlignmentFlag.AlignCenter)

        # Save button (initially hidden)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_to_database)
        layout.addWidget(self.save_button, 4, 1, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.save_button.setVisible(False)

        # Label to display BMI results
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 12px; font-weight: bold")
        layout.addWidget(self.result_label, 4, 0, 1, 1)

        central_widget.setLayout(layout)

        # Initialize database connection
        self.database = DatabaseConnection()

    def calculator(self):
        """
        Calculates the BMI based on user inputs for height and weight.
        Displays the result and allows saving to the database.
        """
        try:
            self.username = self.name_edit.text().strip()
            height = float(self.height_edit.text())
            weight = float(self.weight_edit.text())

            # Ensure name is not empty
            if not self.username:
                QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
                return

            # Calculate BMI and determine status
            cal = BMICalculator(height, weight)
            self.bmi = cal.calculate()
            self.status = self.get_status(self.bmi)
            self.display(self.bmi)

            # Show save button after calculation
            self.save_button.setVisible(True)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for height and weight.")

    def display(self, bmi):
        """
        Displays the BMI value and category in the result label.
        """
        self.result_label.setText(f"{self.status} \nYour BMI is {bmi:.1f} kg/m\u00B2")

    def get_status(self, bmi):
        """
        Determines the BMI category based on the calculated BMI value.
        """
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 24.9:
            return "Normal weight"
        elif 24.9 <= bmi < 29.9:
            return "Overweight"
        else:
            return "Obese"

    def save_to_database(self):
        """
        Saves the calculated BMI record to the database under a user-specific table.
        """
        try:
            if not hasattr(self, "bmi") or not hasattr(self, "status"):
                QMessageBox.warning(self, "Error", "Please calculate BMI before saving.")
                return

            if not self.username:
                QMessageBox.warning(self, "Error", "Name cannot be empty.")
                return

            # Sanitize username to make it a valid table name
            table_name = self.username.replace(" ", "_").lower()
            if not table_name.isalnum():
                QMessageBox.warning(self, "Error", "Name contains invalid characters.")
                return

            # Create the user-specific table
            self.database.create_table(table_name)

            connection = self.database.connect()
            cursor = connection.cursor()

            # Insert data into the user's table
            cursor.execute(f"""
                INSERT INTO bmi_records_{table_name} (username, height_cm, weight_kg, bmi, category)
                VALUES (%s, %s, %s, %s, %s)
            """, (self.username, float(self.height_edit.text()), float(self.weight_edit.text()), self.bmi, self.status))

            connection.commit()
            connection.close()

            QMessageBox.information(self, "Success", "Record saved to database successfully!")
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Unexpected Error", f"An error occurred: {e}")

    def history(self):
        """
        Opens a dialog to display the user's BMI history from the database.
        """
        username = self.name_edit.text().lower().strip()
        if not username:
            QMessageBox.warning(self, "Input Error", "Name cannot be empty.")
            return

        dialog = HistoryDialog(username, self.database)
        dialog.exec()


class BMICalculator:
    """
    Utility class for calculating BMI based on height and weight.
    """

    def __init__(self, height, weight):
        self.height = height
        self.weight = weight

    def calculate(self):
        """
        Calculates and returns the BMI value.
        """
        height_in_meters = self.height / 100
        result = self.weight / (height_in_meters ** 2)
        return round(result, 2)


class HistoryDialog(QDialog):
    """
    Dialog to display the user's BMI history in a table format.
    """

    def __init__(self, username, database):
        super().__init__()
        self.setWindowTitle("History")
        self.setWindowIcon(QIcon("icon.png"))
        self.setFixedSize(540, 300)

        # Set up layout and table widget
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        try:
            # Fetch and display user records from the database
            connection = database.connect()
            cursor = connection.cursor()

            cursor.execute(f"SELECT record_time, height_cm, weight_kg, bmi, category FROM bmi_records_{username}")
            records = cursor.fetchall()

            if records:
                self.table_widget.setRowCount(len(records))
                self.table_widget.setColumnCount(5)
                self.table_widget.setHorizontalHeaderLabels(
                    ["Record Time", "Height (cm)", "Weight (kg)", "BMI", "Category"])

                for row_index, record in enumerate(records):
                    for col_index, value in enumerate(record):
                        self.table_widget.setItem(row_index, col_index, QTableWidgetItem(str(value)))

        except pymysql.MySQLError as e:
            layout.addWidget(QMessageBox.warning(self,  "Error", f"An error occurred: {e}"))

        finally:
            if connection.open:
                cursor.close()
                connection.close()


if __name__ == "__main__":
    # Main application entry point
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
