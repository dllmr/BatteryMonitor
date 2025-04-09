# Battery Monitor

A simple Python application to monitor battery life while optionally putting the CPU under load.

## Features

*   Displays current battery percentage.
*   Displays CPU temperature (if available).
*   Displays fan speed (if available).
*   Plots battery percentage over time.
*   Logs battery percentage to a `battery_log.csv` file every 15 seconds.
*   Optionally puts a configurable number of CPU cores under load to simulate usage.

## Requirements

*   Python 3.12 or higher
*   See `requirements.txt` for Python package dependencies.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd BatteryMonitor
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script directly:

```bash
python battery_monitor.py
```

*   The application window will open, showing the current status and battery graph.
*   Use the spin box to select the number of CPU cores to load.
*   Click "Start Load" to begin stressing the CPU.
*   Click "Stop Load" to stop the CPU stress.
*   Data is logged to `battery_log.csv` in the same directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (You'll need to create this file). 