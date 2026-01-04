import threading
import sys

# Windows-specific imports
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        import win32gui
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
        print("Warning: Windows modules not available - GUI functionality disabled")
else:
    WIN32_AVAILABLE = False


class StateIndicator:
    _TRANSPARENT_COLOR = "#cfbbb7"  # Pure magenta, used for transparency on Windows
    _DEFAULT_SIZE = (64, 64)  # Default width and height tuple

    # Windows API constants
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    WS_EX_TRANSPARENT = 0x20

    def __init__(self, colour=(255, 0, 0), opacity=0.8, corner='topright', offset=(10, 10), size=_DEFAULT_SIZE):
        import tkinter as tk
        self.tk = tk
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
        self._root = self.tk.Tk()
        self._root.withdraw()

        # Configure window for borderless, always-on-top, no focus
        self._root.overrideredirect(True)
        self._root.attributes('-topmost', True)
        self._root.attributes('-toolwindow', True)
        self._root.attributes('-transparentcolor', self._TRANSPARENT_COLOR)
        self._root.config(bg=self._TRANSPARENT_COLOR)

        # Create canvas for the colored box, using transparent color as background
        self._canvas = self.tk.Canvas(self._root, width=self._size[0], height=self._size[1],
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

        # Apply click-through after the window is visible
        self._root.after(100, self._make_click_through)

        self._tk_ready_event.set()
        self._root.mainloop()

    def _make_click_through(self):
        """Make the window click-through using Windows API"""
        if not WIN32_AVAILABLE:
            print("Click-through only supported on Windows")
            return
            
        try:
            # Get the window handle
            hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
            if hwnd == 0:
                hwnd = self._root.winfo_id()

            # Get current extended style
            extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, self.GWL_EXSTYLE)

            # Add layered and transparent flags
            new_style = extended_style | self.WS_EX_LAYERED | self.WS_EX_TRANSPARENT

            # Apply the new extended style
            ctypes.windll.user32.SetWindowLongW(hwnd, self.GWL_EXSTYLE, new_style)

            # Set layered window attributes for transparency
            ctypes.windll.user32.SetLayeredWindowAttributes(
                hwnd,
                ctypes.wintypes.COLORREF(0xFF00FF),  # Transparent color (magenta)
                int(255 * self._opacity),  # Alpha value
                0x00000001 | 0x00000002  # LWA_COLORKEY | LWA_ALPHA
            )

        except Exception as e:
            print(f"Warning: Could not enable click-through: {e}")

    def _to_hex(self, color_value):
        # If the value is a string, assume it's a valid Tkinter color name or hex string
        if isinstance(color_value, str):
            return color_value
        # If it's a tuple, assume it's an RGB tuple and convert to a hex string
        elif isinstance(color_value, tuple) and len(color_value) == 3:
            return f"#{color_value[0]:02x}{color_value[1]:02x}{color_value[2]:02x}"
        return "#000000"  # Fallback to black for unexpected types

    def _update_geometry_internal(self):
        screen_w = self._root.winfo_screenwidth()
        screen_h = self._root.winfo_screenheight()

        x_off, y_off = self._offset
        box_w, box_h = self._size

        x_pos, y_pos = 0, 0
        if self._corner == 'topleft':
            x_pos, y_pos = x_off, y_off
        elif self._corner == 'topright':
            x_pos, y_pos = screen_w - box_w - x_off, y_off
        elif self._corner == 'bottomleft':
            x_pos, y_pos = x_off, screen_h - box_h - y_off
        elif self._corner == 'bottomright':
            x_pos, y_pos = screen_w - box_w - x_off, screen_h - box_h - y_off

        self._root.geometry(f"{box_w}x{box_h}+{x_pos}+{y_pos}")

    def _update_opacity_internal(self):
        self._root.attributes('-alpha', self._opacity)
        # Also update the layered window attributes if click-through is enabled
        self._root.after_idle(self._update_layered_attributes)

    def _update_layered_attributes(self):
        """Update the layered window attributes for proper transparency with click-through"""
        if not WIN32_AVAILABLE:
            return
            
        try:
            hwnd = ctypes.windll.user32.GetParent(self._root.winfo_id())
            if hwnd == 0:
                hwnd = self._root.winfo_id()

            # Update the alpha value for the layered window
            ctypes.windll.user32.SetLayeredWindowAttributes(
                hwnd,
                ctypes.wintypes.COLORREF(0xFF00FF),  # Transparent color (magenta)
                int(255 * self._opacity),  # Alpha value
                0x00000001 | 0x00000002  # LWA_COLORKEY | LWA_ALPHA
            )
        except Exception:
            pass  # Silently fail if we can't update

    def _update_colour_internal(self):
        self._canvas.itemconfig(self._rect_id, fill=self._to_hex(self._colour))

    def _update_size_internal(self):
        w, h = self._size
        self._canvas.config(width=w, height=h)
        self._canvas.coords(self._rect_id, 0, 0, w, h)
        self._update_geometry_internal()

    # Public methods, thread-safe by scheduling operations on the Tkinter thread
    def colour(self, rgb_tuple):
        self._colour = rgb_tuple
        if self._root and self._root.winfo_exists():
            self._root.after(0, self._update_colour_internal)

    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, value))
        if self._root and self._root.winfo_exists():
            self._root.after(0, self._update_opacity_internal)

    def corner(self, corner_str):
        if corner_str in {'topleft', 'topright', 'bottomleft', 'bottomright'}:
            self._corner = corner_str
            if self._root and self._root.winfo_exists():
                self._root.after(0, self._update_geometry_internal)

    def offset(self, xy_tuple):
        if isinstance(xy_tuple, tuple) and len(xy_tuple) == 2:
            self._offset = xy_tuple
            if self._root and self._root.winfo_exists():
                self._root.after(0, self._update_geometry_internal)

    def size(self, xy_tuple):
        if isinstance(xy_tuple, tuple) and len(xy_tuple) == 2 and all(isinstance(n, (int, float)) and n > 0 for n in xy_tuple):
            self._size = xy_tuple
            if self._root and self._root.winfo_exists():
                self._root.after(0, self._update_size_internal)

if WIN32_AVAILABLE:
    user32 = ctypes.windll.user32

    def get_focused_window():
        """Return the window that currently has the keyboard focus."""
        return user32.GetForegroundWindow()

    def get_window_rect(hwnd):
        """Return the bounding rectangle of a window."""
        HWND = wintypes.HWND
        RECT = wintypes.RECT
        rect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect

    def set_window_pos(hwnd, x: int, y: int, w: int, h: int):
        """Move (and optionally resize) a window."""
        # 0x0040 == SWP_NOACTIVATE | 0x0020 == SWP_SHOWWINDOW
        user32.SetWindowPos(hwnd, 0, x, y, w, h, 0x0040 | 0x0020)


    def find_window_by_title_fuzzy(title_query, threshold=70):
        from fuzzywuzzy import process
        from fuzzywuzzy import fuzz
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:
                    windows.append((hwnd, window_title))
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        if not windows:
            return None

        titles = [title for hwnd, title in windows]
        best_match = process.extractOne(title_query, titles, scorer=fuzz.token_set_ratio)

        if best_match[1] >= threshold:
            matched_title = best_match[0]
            for hwnd, title in windows:
                if title == matched_title:
                    return hwnd
        return None
else:
    def get_focused_window():
        print("get_focused_window() only supports Windows! Returning None")
        return None

    def get_window_rect(hwnd):
        print("get_window_rect() only supports Windows! Returning None")
        return None

    def set_window_pos(hwnd, x: int, y: int, w: int, h: int):
        print("set_window_pos() only supports Windows! Functionality disabled")

    def find_window_by_title_fuzzy(title_query, threshold=70):
        print("find_window_by_title_fuzzy() only supports Windows! Returning None")
        return None
