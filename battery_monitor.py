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
from typing import List, Dict, Any, Optional

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
    # Label Prefixes
    STATUS_PREFIX = "Status: "
    TEMP_PREFIX = "CPU Temperature: "
    FAN_PREFIX = "Fan Speed: "
    BATTERY_PREFIX = "Battery: "
    TIME_REMAINING_PREFIX = "Time: "

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
    time_remaining_label: QLabel
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
        self.status_label = QLabel(self.STATUS_PREFIX + "Idle")
        top_layout.addWidget(self.status_label)

        # Temperature display
        self.temp_label = QLabel(self.TEMP_PREFIX + "N/A")
        top_layout.addWidget(self.temp_label)

        # Fan speed display
        self.fan_label = QLabel(self.FAN_PREFIX + "N/A")
        top_layout.addWidget(self.fan_label)

        # Battery percentage display
        self.battery_label = QLabel(self.BATTERY_PREFIX + "N/A")
        top_layout.addWidget(self.battery_label)

        # Time remaining display
        self.time_remaining_label = QLabel(self.TIME_REMAINING_PREFIX + "N/A")
        top_layout.addWidget(self.time_remaining_label)

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
            self.status_label.setText(self.STATUS_PREFIX + "Loading CPU...")

        else:
            self.cpu_loader.stop()
            self.start_button.setText("Start Load")
            self.cores_spinbox.setEnabled(True)
            self.status_label.setText(self.STATUS_PREFIX + "Idle")

    def update_data(self) -> None:
        # Update temperature
        temps: Optional[Dict[str, List[Any]]] = psutil.sensors_temperatures()
        if temps:
            # This might need adjustment based on your system
            # Using Any for sensor details as structure can vary
            first_sensor_list: List[Any] = next(iter(temps.values()))
            if first_sensor_list:
                first_temp: float = first_sensor_list[0].current
                self.temp_label.setText(f"{self.TEMP_PREFIX}{first_temp:.1f}°C")
            else:
                 self.temp_label.setText(self.TEMP_PREFIX + "N/A") # Ensure N/A is set if no data
        else:
            self.temp_label.setText(self.TEMP_PREFIX + "N/A") # Ensure N/A is set if psutil fails

        # Update fan speed
        fans: Optional[Dict[str, List[Any]]] = psutil.sensors_fans()
        if fans:
            try:
                # Display the first detected fan speed
                first_fan_list: List[Any] = next(iter(fans.values()))
                if first_fan_list:
                    fan_speed: int = first_fan_list[0].current
                    self.fan_label.setText(f"{self.FAN_PREFIX}{fan_speed} RPM")
                else:
                    self.fan_label.setText(self.FAN_PREFIX + "N/A")
            except (StopIteration, IndexError, AttributeError):
                 self.fan_label.setText(self.FAN_PREFIX + "N/A")
        else:
            self.fan_label.setText(self.FAN_PREFIX + "N/A")

        # Update battery
        battery: Optional[psutil._common.sbattery] = psutil.sensors_battery()
        if battery:
            percent: float = battery.percent
            self.battery_label.setText(f"{self.BATTERY_PREFIX}{percent:.1f}%")

            # Update time remaining
            secsleft: int = battery.secsleft
            if battery.power_plugged:
                time_remaining_str = "Charging"
            elif secsleft == psutil.POWER_TIME_UNLIMITED:
                time_remaining_str = "Unlimited"
            elif secsleft == psutil.POWER_TIME_UNKNOWN:
                time_remaining_str = "Calculating..."
            else:
                # Format seconds into H:MM
                mm, ss = divmod(secsleft, 60)
                hh, mm = divmod(mm, 60)
                time_remaining_str = f"{hh}:{mm:02d} remaining"
            self.time_remaining_label.setText(self.TIME_REMAINING_PREFIX + time_remaining_str)

            current_time: str = datetime.now().strftime('%H:%M:%S')
            self.times.append(current_time)
            self.battery_levels.append(percent)

            # Update graph
            self.ax.clear()
            self.ax.plot(self.times, self.battery_levels)
            self.ax.set_title("Battery Level Over Time")
            self.ax.set_xlabel("Time")
            self.ax.set_ylabel("Battery %")
            self.ax.set_ylim(0, 100)  # Set fixed Y-axis limits
            self.ax.xaxis.set_major_locator(MaxNLocator(nbins=10, prune='both'))

            # Remove top and right spines
            self.ax.spines['top'].set_visible(False)
            self.ax.spines['right'].set_visible(False)

            # Add faint horizontal grid lines every 10%
            self.ax.grid(True, axis='y', linestyle=':', color='gray', alpha=0.7)

            plt.setp(self.ax.get_xticklabels(), rotation=45, ha="right")
            self.figure.tight_layout()
            self.canvas.draw()
        else:
            # If no battery info, set labels to N/A
            self.battery_label.setText(self.BATTERY_PREFIX + "N/A")
            self.time_remaining_label.setText(self.TIME_REMAINING_PREFIX + "N/A")

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
