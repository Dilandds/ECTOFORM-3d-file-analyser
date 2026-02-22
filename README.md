# STL 3D Viewer

A minimalistic Python desktop application for uploading and visualizing STL files with smooth 3D interaction, optimized for handling large models.

## Features

- **Minimalistic UI**: Clean, modern interface with intuitive controls
- **STL File Upload**: Easy file selection through button or file dialog
- **Interactive 3D Viewer**: Rotate, zoom, and pan your 3D models smoothly
- **Large Model Support**: Optimized rendering using PyVista/VTK for smooth performance with large STL files
- **Real-time Visualization**: Instant display of loaded STL models with proper lighting and shading

## Requirements

- Python 3.8 or higher (Python 3.11 or 3.12 recommended for macOS)
- PyQt5 (PyQt6 has compatibility issues on macOS with Python 3.13)
- PyVista
- NumPy

## Installation

1. Clone or download this repository

2. Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

**Note:** Make sure your virtual environment is activated (you should see `(venv)` in your terminal prompt) before installing dependencies and running the application.

## Usage

**Important:** Always activate the virtual environment first:

```bash
source venv/bin/activate
```

Then run the application (no environment variables required):

```bash
python main.py
```

Or use the provided run script (macOS/Linux):

```bash
./run.sh
```

To deactivate the virtual environment when you're done:
```bash
deactivate
```

### How to Use

1. Launch the application
2. Click the "Upload STL File" button on the left panel
3. Select an STL file from your computer
4. The 3D model will appear in the viewer on the right panel
5. Interact with the model:
   - **Rotate**: Click and drag
   - **Zoom**: Scroll wheel or pinch gesture
   - **Pan**: Right-click and drag (or Shift + left-click and drag)

## Technology Stack

- **PyQt5**: GUI framework for the desktop application (PyQt5 used for better macOS compatibility)
- **PyVista**: High-performance 3D visualization library built on VTK
- **VTK**: Underlying rendering engine optimized for large datasets
- **NumPy**: Numerical computing support

## macOS Compatibility Notes

This application uses PyQt5 instead of PyQt6 for better compatibility with macOS, especially with Python 3.13. If QtInteractor has issues, the application will automatically fall back to offscreen rendering mode, which provides a stable viewing experience with button-based controls for rotation and zoom.

## Performance

This application is optimized for handling large STL files smoothly:

- Uses VTK's efficient rendering pipeline
- Supports GPU acceleration when available
- Optimized mesh rendering for large datasets
- Configurable quality settings for balance between performance and visual quality

## Building the Application

### macOS - Build DMG

Run the build script to create a macOS DMG installer:

```bash
./build_mac.sh
```

This will:
- Create the `.app` bundle
- Generate a DMG installer file
- Output: `STL_Viewer-1.0.0-macOS.dmg`

**Requirements:**
- PyInstaller (installed automatically if missing)
- `create-dmg` tool (installed via Homebrew if missing)

### Windows - Get EXE via GitHub Actions

1. **Push code to GitHub** (or use GitHub Actions workflow dispatch)
2. **Wait for build to complete** (~5-10 minutes)
3. **Download artifact:**
   - Go to: `https://github.com/YOUR_USERNAME/Jewellery_new/actions`
   - Click on the latest workflow run
   - Download "STL-Viewer-Windows" artifact
   - Extract the `.exe` file

The GitHub Actions workflow automatically builds both macOS and Windows versions.

## File Structure

```
Jewellery_new/
├── main.py                 # Application entry point
├── stl_viewer.py          # Main window with UI
├── viewer_widget.py        # 3D viewer widget (PyVista)
├── requirements.txt       # Python dependencies
├── run.sh                 # Convenience script to run the app (macOS/Linux)
├── build_mac.sh           # Build script for macOS DMG
├── stl_viewer_mac.spec    # PyInstaller spec for macOS
├── stl_viewer_windows.spec # PyInstaller spec for Windows
└── README.md              # This file
```

## Troubleshooting

### Import Errors

If you encounter import errors like `ModuleNotFoundError: No module named 'PyQt6'`:

1. Make sure the virtual environment is activated:
   ```bash
   source venv/bin/activate
   ```

2. Ensure all dependencies are installed:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. Verify you're using the correct Python interpreter:
   ```bash
   which python  # Should point to venv/bin/python
   ```

### Large File Performance

For very large STL files (>10MB), the initial load may take a few seconds. The viewer is optimized for smooth interaction after loading.

### Display Issues

If the 3D viewer appears blank:
- Ensure your graphics drivers are up to date
- Check that OpenGL is properly configured on your system
- Try restarting the application

## License

This project is provided as-is for personal or commercial use.
