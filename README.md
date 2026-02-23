# About
**ImgToPoints**: A simple, local tool to digitize images into points

ImgToPoints is a lightweight, local-only Python desktop application designed to quickly and easily convert raster (pixel-based) image files of graphical data (such as those found in scientific publications, reports, or historical documents) into usable CSV data for analysis. See also https://github.com/MasterAI-EAM/GraphMaster for the logic used to (attempting to) get the x/y min/max automatically. Built with assistance from Gemini.

## Purpose
Extracting raw data points from published charts is a common necessity in research and engineering. The goal of this tool is to provide a fast, user-friendly, and stable way to "digitize" these graphs. By running entirely locally on your machine, it ensures your sensitive or proprietary data remains private, while avoiding the instability and latency of cloud-based APIs. 

It strikes a balance between automation and manual control by using pixel-logic algorithms to automatically detect chart axes, while leaving the critical task of accurate data point placement to the user.

## Key Features
* **100% Local Processing:** No cloud APIs, no internet connection required, and no data privacy risks.
* **Automated Axis Detection:** Automatically attempts to locate the pixel boundaries of the X and Y axes upon loading an image.
* **Flexible Scaling:** Supports Linear, Log10, and Natural Log (Ln) scales for both X and Y axes independently.
* **Real-Time Data Interpolation:** As you click to mark points on the graph, the corresponding numerical values are instantly calculated and sorted into a visible data table.
* **Easy Corrections:** Simple left-click to add a data point, right-click to remove a misplaced point.
* **CSV Export:** One-click export of your digitized, sorted data points to a standard `x, y` CSV file.
* **Responsive UI:** Resizable window with a dynamic image canvas and a draggable pane to view your data table side-by-side with the graph.

## Requirements

This application requires Python 3.x and the following libraries:

* `opencv-python` (cv2) - For image processing and automated axis detection.
* `numpy` - For mathematical operations during image processing.
* `Pillow` (PIL) - For handling and scaling images within the Tkinter GUI.
* `tkinter` - Standard Python GUI library (usually included with Python installations).

**Installation:**
Clone the repository and install the required external dependencies using pip:

    ```bash
    git clone https://github.com/jasparagus/ImgToPoints.git
    python -m pip install -r requirements.txt
    ```

Or 

    ```
    pip install opencv-python numpy pillow
    ```


## How to Use



1. **Launch the App:** Run the Python script (`python app.py`).
2. **Load an Image:** Click "Load Image" and select the graph you wish to digitize (supports PNG, JPG, BMP).
3. **Configure Axes:** * The app will attempt to automatically find the graph's bounding box (indicated by a green dashed box).
* If the automatic detection is slightly off, click "Set X Min", "Set Y Max", etc., and click on the image to manually correct the pixel locations of the axes.
* Enter the actual numerical values for your X and Y minimums and maximums in the text boxes.
* Select the appropriate scale (Linear, Log10, Ln) for each axis.


4. **Digitize Points:** Click the "Mark Datapoints" button.
* **Left-Click** on the image to place a data point.
* **Right-Click** (or 2-finger click on Mac) near an existing point to remove it.


5. **Export:** Once you have marked all necessary points, review the sorted table on the right, and click "Export to CSV" to save your data.
