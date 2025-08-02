import tkinter as tk
import threading

class StateIndicator:
    _TRANSPARENT_COLOR = "#FF00FF" # Pure magenta, used for click-through on Windows
    _DEFAULT_SIZE = (20, 20) # Default width and height tuple

    def __init__(self, colour=(255, 0, 0), opacity=0.8, corner='topright', offset=(10, 10), size=_DEFAULT_SIZE):
        self._colour = colour
        self._opacity = opacity
        self._corner = corner
        self._offset = offset
        self._size = size

        self._root = None
        self._tk_ready_event = threading.Event()

        # Start Tkinter event loop and GUI setup in a daemon thread
        self._tk_thread = threading.Thread(target=self._run_gui_thread, daemon=True)
        self._tk_thread.start()

        # Wait for the Tkinter thread to initialize the _root object
        self._tk_ready_event.wait(timeout=5)

    def _run_gui_thread(self):
        self._root = tk.Tk()
        self._root.withdraw()

        # Configure window for borderless, always-on-top, click-through, no focus
        self._root.overrideredirect(True)
        self._root.attributes('-topmost', True)
        self._root.attributes('-toolwindow', True)
        self._root.attributes('-transparentcolor', self._TRANSPARENT_COLOR)
        self._root.config(bg=self._TRANSPARENT_COLOR)

        # Create canvas for the colored box, using transparent color as background
        self._canvas = tk.Canvas(self._root, width=self._size[0], height=self._size[1],
                                 highlightthickness=0, bg=self._TRANSPARENT_COLOR)
        self._canvas.pack()

        # Draw the rectangle on the canvas
        self._rect_id = self._canvas.create_rectangle(
            0, 0, self._size[0], self._size[1],
            fill=self._to_hex(self._colour), outline="")

        # Apply initial geometry and opacity
        self._update_geometry_internal()
        self._update_opacity_internal()
        self._root.deiconify()

        self._tk_ready_event.set()

        self._root.mainloop()

    def _to_hex(self, color_value):
        # If the value is a string, assume it's a valid Tkinter color name (e.g., 'red', 'blue')
        # or a hex string already, and return it directly.
        if isinstance(color_value, str):
            return color_value
        # If it's a tuple, assume it's an RGB tuple and convert to a hex string.
        elif isinstance(color_value, tuple) and len(color_value) == 3:
            return f"#{color_value[0]:02x}{color_value[1]:02x}{color_value[2]:02x}"
        # For any other unsupported type, you might want to raise an error or return a default.
        # Following the existing pattern, it implicitly expects either a string or 3-tuple.
        return "#000000" # Fallback to black for unexpected types

    def _update_geometry_internal(self):
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()

        x_off, y_off = self._offset
        box_w, box_h = self._size

        x_pos, y_pos = 0, 0
        if self._corner == 'topleft': x_pos, y_pos = x_off, y_off
        elif self._corner == 'topright': x_pos, y_pos = screen_w - box_w - x_off, y_off
        elif self._corner == 'bottomleft': x_pos, y_pos = x_off, screen_h - box_h - y_off
        elif self._corner == 'bottomright': x_pos, y_pos = screen_w - box_w - x_off, screen_h - box_h - y_off

        self._root.geometry(f"{box_w}x{box_h}+{x_pos}+{y_pos}")

    def _update_opacity_internal(self):
        self._root.attributes('-alpha', self._opacity)

    def _update_colour_internal(self):
        self._canvas.itemconfig(self._rect_id, fill=self._to_hex(self._colour))

    def _update_size_internal(self):
        w, h = self._size
        self._canvas.config(width=w, height=h)
        self._canvas.coords(self._rect_id, 0, 0, w, h)
        self._update_geometry_internal()

    # Public methods, thread-safe by scheduling operations on the Tkinter thread
    def colour(self, rgb_tuple): # Renamed `rgb_tuple` argument to `color_value` in thoughts, but kept for strict adherence
        self._colour = rgb_tuple # This now accepts RGB tuples or color strings like 'red'
        if self._root and self._root.winfo_exists(): self._root.after(0, self._update_colour_internal)

    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, value))
        if self._root and self._root.winfo_exists(): self._root.after(0, self._update_opacity_internal)

    def corner(self, corner_str):
        if corner_str in {'topleft', 'topright', 'bottomleft', 'bottomright'}:
            self._corner = corner_str
            if self._root and self._root.winfo_exists(): self._root.after(0, self._update_geometry_internal)

    def offset(self, xy_tuple):
        if isinstance(xy_tuple, tuple) and len(xy_tuple) == 2:
            self._offset = xy_tuple
            if self._root and self._root.winfo_exists(): self._root.after(0, self._update_geometry_internal)

    def size(self, xy_tuple):
        if isinstance(xy_tuple, tuple) and len(xy_tuple) == 2 and all(isinstance(n, (int, float)) and n > 0 for n in xy_tuple):
            self._size = xy_tuple
            if self._root and self._root.winfo_exists(): self._root.after(0, self._update_size_internal)