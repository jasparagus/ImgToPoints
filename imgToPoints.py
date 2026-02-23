import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import csv
import math

# ==========================================
# GraphMaster Axis Detection Logic 
# See also https://github.com/MasterAI-EAM/GraphMaster
# ==========================================
def findMaxConsecutiveOnes(nums):
    count = maxCount = 0
    for i in range(len(nums)):
        if nums[i] == 1:
            count += 1
        else:
            maxCount = max(count, maxCount)
            count = 0
    return max(count, maxCount)

def detectAxes(image_cv, threshold=10):
    height, width, _ = image_cv.shape
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    # Y-axis (left)
    maxConsecutiveOnes = [findMaxConsecutiveOnes(gray[:, idx] < 200) for idx in range(width)]
    start_idx, maxindex, maxcount = 0, 0, max(maxConsecutiveOnes)
    while start_idx < width / 2:
        if abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
            maxindex = start_idx
            start_idx += 1
            while abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
                maxindex = start_idx
                start_idx += 1
            break
        start_idx += 1
    yaxis = (maxindex, 0, maxindex, height)
    
    # Right bounding axis
    start_idx, y_right_index, maxcount = width - 1, width - 1, max(maxConsecutiveOnes)
    while start_idx > width / 2:
        if abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
            y_right_index = start_idx
            start_idx -= 1
            while abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
                y_right_index = start_idx
                start_idx -= 1
            break
        start_idx -= 1
    y_right_axis = (y_right_index, 0, y_right_index, height)
    
    # X-axis (bottom)
    maxConsecutiveOnes = [findMaxConsecutiveOnes(gray[idx, :] < 200) for idx in range(height)]
    start_idx, maxindex, maxcount = height - 1, height - 1, max(maxConsecutiveOnes)
    while start_idx > height / 2:
        if abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
            maxindex = start_idx
            start_idx -= 1
            while abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
                maxindex = start_idx
                start_idx -= 1
            break
        start_idx -= 1
    xaxis = (0, maxindex, width, maxindex)
    
    # Top bounding axis
    start_idx, x_up_index, maxcount = 0, 0, max(maxConsecutiveOnes)
    while start_idx < height / 2:
        if abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
            x_up_index = start_idx
            start_idx += 1
            while abs(maxConsecutiveOnes[start_idx] - maxcount) <= threshold:
                x_up_index = start_idx
                start_idx += 1
            break
        start_idx += 1
    x_up_axis = (0, x_up_index, width, x_up_index)
    
    return xaxis, yaxis, x_up_axis, y_right_axis

# ==========================================
# Main GUI Application
# ==========================================
class GraphDigitizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Graph Digitizer")
        self.root.geometry("1200x700")

        # Application State
        self.cv_image = None
        self.pil_image = None
        self.photo_image = None
        self.scale_factor = 1.0
        self.img_offset_x = 0
        self.img_offset_y = 0
        self.mode = "idle" # idle, set_xmin, set_xmax, set_ymin, set_ymax, mark_points
        self.points_px = [] # list of (x_px, y_px)
        
        # Axis pixel boundaries
        self.px_xmin = 0
        self.px_xmax = 100
        self.px_ymin = 100 # Note: in images, y=0 is top, so ymin (bottom of graph) has a LARGER pixel value
        self.px_ymax = 0
        
        self.setup_ui()

    def setup_ui(self):
        # Main PanedWindow (Draggable separator)
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---------------- Left Panel: Controls and Image ----------------
        self.left_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.left_frame, weight=3)

        # Controls Strip
        self.controls_frame = ttk.Frame(self.left_frame)
        self.controls_frame.pack(fill=tk.X, pady=5)

        ttk.Button(self.controls_frame, text="Load Image", command=self.load_image).grid(row=0, column=0, padx=5, pady=2)
        
        # Axis Value Entries & Set Buttons
        self.val_xmin_var = tk.StringVar(value="0")
        self.val_xmax_var = tk.StringVar(value="10")
        self.val_ymin_var = tk.StringVar(value="0")
        self.val_ymax_var = tk.StringVar(value="10")

        self.scale_x_var = tk.StringVar(value="Linear")
        self.scale_y_var = tk.StringVar(value="Linear")
        scales = ["Linear", "Log10", "Ln"]

        # X Axis Configuration
        ttk.Label(self.controls_frame, text="X Scale:").grid(row=0, column=1, padx=2)
        ttk.Combobox(self.controls_frame, textvariable=self.scale_x_var, values=scales, width=8, state="readonly").grid(row=0, column=2, padx=2)
        
        ttk.Label(self.controls_frame, text="X Min:").grid(row=0, column=3, padx=2)
        ttk.Entry(self.controls_frame, textvariable=self.val_xmin_var, width=8).grid(row=0, column=4, padx=2)
        ttk.Button(self.controls_frame, text="Set X Min", command=lambda: self.set_mode("set_xmin")).grid(row=0, column=5, padx=2)

        ttk.Label(self.controls_frame, text="X Max:").grid(row=0, column=6, padx=2)
        ttk.Entry(self.controls_frame, textvariable=self.val_xmax_var, width=8).grid(row=0, column=7, padx=2)
        ttk.Button(self.controls_frame, text="Set X Max", command=lambda: self.set_mode("set_xmax")).grid(row=0, column=8, padx=2)

        # Y Axis Configuration
        ttk.Label(self.controls_frame, text="Y Scale:").grid(row=1, column=1, padx=2)
        ttk.Combobox(self.controls_frame, textvariable=self.scale_y_var, values=scales, width=8, state="readonly").grid(row=1, column=2, padx=2)

        ttk.Label(self.controls_frame, text="Y Min:").grid(row=1, column=3, padx=2)
        ttk.Entry(self.controls_frame, textvariable=self.val_ymin_var, width=8).grid(row=1, column=4, padx=2)
        ttk.Button(self.controls_frame, text="Set Y Min", command=lambda: self.set_mode("set_ymin")).grid(row=1, column=5, padx=2)

        ttk.Label(self.controls_frame, text="Y Max:").grid(row=1, column=6, padx=2)
        ttk.Entry(self.controls_frame, textvariable=self.val_ymax_var, width=8).grid(row=1, column=7, padx=2)
        ttk.Button(self.controls_frame, text="Set Y Max", command=lambda: self.set_mode("set_ymax")).grid(row=1, column=8, padx=2)

        # Mark Points Button
        self.btn_mark = ttk.Button(self.controls_frame, text="Mark Datapoints", command=lambda: self.set_mode("mark_points"))
        self.btn_mark.grid(row=0, column=9, rowspan=2, padx=15)
        
        self.status_lbl = ttk.Label(self.controls_frame, text="Status: Idle", foreground="blue")
        self.status_lbl.grid(row=0, column=10, rowspan=2, padx=10)

        # Image Canvas
        self.canvas = tk.Canvas(self.left_frame, bg="gray", cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click) # Windows/Linux
        self.canvas.bind("<Button-2>", self.on_right_click) # Mac alternative

        # ---------------- Right Panel: Data Table ----------------
        self.right_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.right_frame, weight=1)

        ttk.Label(self.right_frame, text="Digitized Points (Sorted by X)", font=("Arial", 10, "bold")).pack(pady=5)

        # Treeview with scrollbar
        tree_frame = ttk.Frame(self.right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, columns=("X", "Y"), show="headings", yscrollcommand=scrollbar.set)
        self.tree.heading("X", text="X Value")
        self.tree.heading("Y", text="Y Value")
        self.tree.column("X", width=100, anchor=tk.CENTER)
        self.tree.column("Y", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.tree.yview)

        ttk.Button(self.right_frame, text="Export to CSV", command=self.export_csv).pack(pady=10, fill=tk.X)
        
        # Add variable traces to auto-update points if numerical inputs change
        self.val_xmin_var.trace_add("write", lambda *args: self.update_data_list())
        self.val_xmax_var.trace_add("write", lambda *args: self.update_data_list())
        self.val_ymin_var.trace_add("write", lambda *args: self.update_data_list())
        self.val_ymax_var.trace_add("write", lambda *args: self.update_data_list())
        self.scale_x_var.trace_add("write", lambda *args: self.update_data_list())
        self.scale_y_var.trace_add("write", lambda *args: self.update_data_list())

    def set_mode(self, mode):
        self.mode = mode
        modes_text = {
            "idle": "Idle",
            "set_xmin": "Click on image to set X Min pixel",
            "set_xmax": "Click on image to set X Max pixel",
            "set_ymin": "Click on image to set Y Min pixel (Bottom)",
            "set_ymax": "Click on image to set Y Max pixel (Top)",
            "mark_points": "Left-click: Add point | Right-click: Remove point"
        }
        self.status_lbl.config(text=f"Status: {modes_text.get(mode, mode)}")

    def load_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not filepath:
            return

        # Load with OpenCV for GraphMaster axis detection logic
        self.cv_image = cv2.imread(filepath)
        
        try:
            xaxis, yaxis, x_up_axis, y_right_axis = detectAxes(self.cv_image)
            self.px_xmin = yaxis[0]
            self.px_ymin = xaxis[1] 
            self.px_ymax = x_up_axis[1]
            self.px_xmax = y_right_axis[0]
        except Exception as e:
            # Fallback to image corners if detection fails
            h, w, _ = self.cv_image.shape
            self.px_xmin, self.px_xmax = 0, w
            self.px_ymin, self.px_ymax = h, 0

        # Convert to PIL for Tkinter
        self.cv_image = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2RGB)
        self.pil_image = Image.fromarray(self.cv_image)
        self.points_px = []
        self.update_data_list()
        self.draw_image()
        self.set_mode("idle")

    def draw_image(self):
        if not self.pil_image: return
        self.canvas.delete("all")

        c_width = self.canvas.winfo_width()
        c_height = self.canvas.winfo_height()
        if c_width < 10 or c_height < 10: return

        i_width, i_height = self.pil_image.size

        # Calculate scale to fit canvas while preserving aspect ratio
        scale_w = c_width / i_width
        scale_h = c_height / i_height
        self.scale_factor = min(scale_w, scale_h)

        new_w = int(i_width * self.scale_factor)
        new_h = int(i_height * self.scale_factor)
        
        resized_image = self.pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_image)

        # Center the image
        self.img_offset_x = (c_width - new_w) // 2
        self.img_offset_y = (c_height - new_h) // 2

        self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor=tk.NW, image=self.photo_image)
        
        self.draw_overlays()

    def draw_overlays(self):
        if not self.pil_image: return
        
        # Draw axis guidelines (using the calculated px bounds)
        cx_min = self.img_to_canvas_x(self.px_xmin)
        cx_max = self.img_to_canvas_x(self.px_xmax)
        cy_min = self.img_to_canvas_y(self.px_ymin) # Bottom
        cy_max = self.img_to_canvas_y(self.px_ymax) # Top

        # Draw box representing active graph area
        self.canvas.create_rectangle(cx_min, cy_max, cx_max, cy_min, outline="green", dash=(4, 4))
        self.canvas.create_text(cx_min, cy_min+10, text="Xmin, Ymin", fill="green")
        self.canvas.create_text(cx_max, cy_max-10, text="Xmax, Ymax", fill="green")

        # Draw points
        for (px, py) in self.points_px:
            cx = self.img_to_canvas_x(px)
            cy = self.img_to_canvas_y(py)
            r = 4
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="red", outline="white")

    def on_canvas_resize(self, event):
        self.draw_image()

    def canvas_to_img_coords(self, cx, cy):
        ix = (cx - self.img_offset_x) / self.scale_factor
        iy = (cy - self.img_offset_y) / self.scale_factor
        return ix, iy

    def img_to_canvas_x(self, ix):
        return ix * self.scale_factor + self.img_offset_x
        
    def img_to_canvas_y(self, iy):
        return iy * self.scale_factor + self.img_offset_y

    def on_left_click(self, event):
        if not self.pil_image: return
        ix, iy = self.canvas_to_img_coords(event.x, event.y)
        
        if self.mode == "set_xmin":
            self.px_xmin = ix
            self.set_mode("idle")
        elif self.mode == "set_xmax":
            self.px_xmax = ix
            self.set_mode("idle")
        elif self.mode == "set_ymin":
            self.px_ymin = iy
            self.set_mode("idle")
        elif self.mode == "set_ymax":
            self.px_ymax = iy
            self.set_mode("idle")
        elif self.mode == "mark_points":
            self.points_px.append((ix, iy))
            
        self.draw_image()
        self.update_data_list()

    def on_right_click(self, event):
        if not self.pil_image or self.mode != "mark_points": return
        ix, iy = self.canvas_to_img_coords(event.x, event.y)
        
        # Find closest point within a small pixel radius (e.g., 10 pixels on original image)
        threshold = 10 / self.scale_factor
        closest_idx = -1
        min_dist = float('inf')
        
        for idx, (px, py) in enumerate(self.points_px):
            dist = math.hypot(px - ix, py - iy)
            if dist < min_dist and dist < threshold:
                min_dist = dist
                closest_idx = idx
                
        if closest_idx != -1:
            self.points_px.pop(closest_idx)
            self.draw_image()
            self.update_data_list()

    def interpolate_value(self, px, px_min, px_max, val_min, val_max, scale_type):
        if px_max == px_min: return val_min # Avoid div by zero
        
        t = (px - px_min) / (px_max - px_min)
        
        try:
            if scale_type == "Linear":
                return val_min + t * (val_max - val_min)
            elif scale_type == "Log10":
                if val_min <= 0 or val_max <= 0: return float('nan')
                log_min, log_max = math.log10(val_min), math.log10(val_max)
                return 10 ** (log_min + t * (log_max - log_min))
            elif scale_type == "Ln":
                if val_min <= 0 or val_max <= 0: return float('nan')
                ln_min, ln_max = math.log(val_min), math.log(val_max)
                return math.exp(ln_min + t * (ln_max - ln_min))
        except Exception:
            return float('nan')

    def update_data_list(self):
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            val_xmin = float(self.val_xmin_var.get())
            val_xmax = float(self.val_xmax_var.get())
            val_ymin = float(self.val_ymin_var.get())
            val_ymax = float(self.val_ymax_var.get())
        except ValueError:
            return # Don't update if parsing fails

        sc_x = self.scale_x_var.get()
        sc_y = self.scale_y_var.get()

        calculated_points = []
        for (px, py) in self.points_px:
            # X interpolation
            data_x = self.interpolate_value(px, self.px_xmin, self.px_xmax, val_xmin, val_xmax, sc_x)
            
            # Y interpolation (Note: py_ymin is geometrically > py_ymax in image coordinates)
            data_y = self.interpolate_value(py, self.px_ymin, self.px_ymax, val_ymin, val_ymax, sc_y)
            
            calculated_points.append((data_x, data_y))

        # Sort by X ascending
        calculated_points.sort(key=lambda item: item[0])

        for (x, y) in calculated_points:
            self.tree.insert("", tk.END, values=(f"{x:.5f}", f"{y:.5f}"))

    def export_csv(self):
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("Warning", "No data points to export!")
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
            
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["x", "y"])
                for item in items:
                    writer.writerow(self.tree.item(item, 'values'))
            messagebox.showinfo("Success", f"Data saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphDigitizerApp(root)
    root.mainloop()