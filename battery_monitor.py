# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "matplotlib",
#     "psutil",
#     "PySide6",
# ]
# ///

import sys
import csv
from datetime import datetime
from pathlib import Path
import multiprocessing
from typing import List, Dict, Tuple, Any, Optional

import psutil
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QSpinBox)
from PySide6.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.ticker import MaxNLocator

class CPULoader:
    def __init__(self) -> None:
        self.running: bool = False
        self.processes: List[multiprocessing.Process] = []

    def cpu_load(self) -> None:
        while True:
            if not self.running:
                break
            pass  # Infinite loop to load CPU

    def start(self, num_cores: int) -> None:
        self.running = True
        for _ in range(num_cores):
            p = multiprocessing.Process(target=self.cpu_load)
            p.start()
            self.processes.append(p)

    def stop(self) -> None:
        self.running = False
        for p in self.processes:
            p.terminate()
        self.processes.clear()

class BatteryMonitor(QMainWindow):
    cpu_loader: CPULoader
    times: List[str]
    battery_levels: List[float]
    update_timer: QTimer
    log_timer: QTimer
    csv_file: Path
    cores_spinbox: QSpinBox
    start_button: QPushButton
    temp_label: QLabel
    battery_label: QLabel
    fan_label: QLabel
    status_label: QLabel
    figure: Figure
    canvas: FigureCanvasQTAgg
    ax: Axes

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Battery Life Tester")
        self.setMinimumSize(800, 600)

        # Initialize CPU loader
        self.cpu_loader = CPULoader()

        # Data storage
        self.times = []
        self.battery_levels = []

        # Setup UI
        self.setup_ui()

        # Setup timers
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(1000)  # Update every second

        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.log_data)
        self.log_timer.start(15000)  # Log every 15 seconds

        # Setup CSV logging
        self.csv_file = Path("battery_log.csv")
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', 'Battery Percentage'])

    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top Fixed Section --- 
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0,0,0,0) # Remove margins if needed

        # Controls
        controls_layout = QHBoxLayout()
        self.cores_spinbox = QSpinBox()
        self.cores_spinbox.setRange(1, multiprocessing.cpu_count())
        self.cores_spinbox.setValue(1)
        controls_layout.addWidget(QLabel("Number of cores:"))
        controls_layout.addWidget(self.cores_spinbox)

        self.start_button = QPushButton("Start Load")
        self.start_button.clicked.connect(self.toggle_load)
        controls_layout.addWidget(self.start_button)
        top_layout.addLayout(controls_layout)

        # Status display
        self.status_label = QLabel("Status: Idle")
        top_layout.addWidget(self.status_label)

        # Temperature display
        self.temp_label = QLabel("CPU Temperature: N/A")
        top_layout.addWidget(self.temp_label)

        # Fan speed display
        self.fan_label = QLabel("Fan Speed: N/A")
        top_layout.addWidget(self.fan_label)

        # Battery percentage display
        self.battery_label = QLabel("Battery: N/A")
        top_layout.addWidget(self.battery_label)

        top_widget.setMaximumHeight(top_widget.sizeHint().height()) # Fix the height
        main_layout.addWidget(top_widget)

        # --- Resizable Graph Section --- 
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasQTAgg(self.figure)
        main_layout.addWidget(self.canvas) # Add canvas directly to main layout
        self.ax = self.figure.add_subplot(111)
        self.ax.set_title("Battery Level Over Time")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Battery %")

    def toggle_load(self) -> None:
        if self.start_button.text() == "Start Load":
            self.cpu_loader.start(self.cores_spinbox.value())
            self.start_button.setText("Stop Load")
            self.cores_spinbox.setEnabled(False)
            self.status_label.setText("Status: Loading CPU...")

        else:
            self.cpu_loader.stop()
            self.start_button.setText("Start Load")
            self.cores_spinbox.setEnabled(True)
            self.status_label.setText("Status: Idle")

    def update_data(self) -> None:
        # Update temperature
        temps: Optional[Dict[str, List[Any]]] = psutil.sensors_temperatures()
        if temps:
            # This might need adjustment based on your system
            # Using Any for sensor details as structure can vary
            first_sensor_list: List[Any] = next(iter(temps.values()))
            if first_sensor_list:
                first_temp: float = first_sensor_list[0].current
                self.temp_label.setText(f"CPU Temperature: {first_temp:.1f}°C")

        # Update fan speed
        fans: Optional[Dict[str, List[Any]]] = psutil.sensors_fans()
        if fans:
            try:
                # Display the first detected fan speed
                first_fan_list: List[Any] = next(iter(fans.values()))
                if first_fan_list:
                    fan_speed: int = first_fan_list[0].current
                    self.fan_label.setText(f"Fan Speed: {fan_speed} RPM")
                else:
                    self.fan_label.setText("Fan Speed: N/A")
            except (StopIteration, IndexError, AttributeError):
                 self.fan_label.setText("Fan Speed: N/A")
        else:
            self.fan_label.setText("Fan Speed: N/A")

        # Update battery
        battery: Optional[psutil._common.sbattery] = psutil.sensors_battery()
        if battery:
            percent: float = battery.percent
            self.battery_label.setText(f"Battery: {percent:.1f}%")

            current_time: str = datetime.now().strftime('%H:%M:%S')
            self.times.append(current_time)
            self.battery_levels.append(percent)

            # Update graph
            self.ax.clear()
            self.ax.plot(self.times, self.battery_levels)
            self.ax.set_title("Battery Level Over Time")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Battery %")
            self.ax.xaxis.set_major_locator(MaxNLocator(nbins=10, prune='both'))
            plt.setp(self.ax.get_xticklabels(), rotation=45, ha="right")
            self.figure.tight_layout()
            self.canvas.draw()

    def log_data(self) -> None:
        battery: Optional[psutil._common.sbattery] = psutil.sensors_battery()
        if battery:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%H:%M:%S'),
                    battery.percent
                ])

def main() -> None:
    app = QApplication(sys.argv)
    window = BatteryMonitor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
