import threading
import queue
import win32pipe
import win32file


class PipeTransmitter:
    def __init__(self, pipe_name, close_pipes=False):
        self.pipe_name = r'\\.\pipe'+'\\'+pipe_name
        self.close_pipes = close_pipes
        self.send_queue = queue.Queue()

        # Start threads for sending and receiving data
        self.send_thread = threading.Thread(target=self.send_data_thread)
        self.send_thread.start()

    def send_data_thread(self):
        pipe_handle = win32pipe.CreateNamedPipe(
            self.pipe_name,
            win32pipe.PIPE_ACCESS_OUTBOUND,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
            1,  # Max instances
            65536,  # Out buffer size
            65536,  # In buffer size
            0,  # Timeout
            None  # Security attributes
        )
        win32pipe.ConnectNamedPipe(pipe_handle, None)

        while True:
            data = self.send_queue.get()
            win32file.WriteFile(pipe_handle, data.encode())

        if self.close_pipes:
            win32file.CloseHandle(pipe_handle)

    def send_data(self, data):
        self.send_queue.put(data)


class PipeReceiver:
    def __init__(self, pipe_name):
        self.pipe_name = r'\\.\pipe'+'\\'+pipe_name
        self.receive_queue = queue.Queue()
        self.callback_function = None

        # Start threads for sending and receiving data
        self.receive_thread = threading.Thread(target=self.receive_data_thread)
        self.receive_thread.start()

    def receive_data_thread(self):
        pipe_handle = win32file.CreateFile(
            self.pipe_name,
            win32file.GENERIC_READ,
            0,
            None,
            win32file.OPEN_EXISTING,
            0,
            None
        )

        while True:
            data = win32file.ReadFile(pipe_handle, 4096)[1].decode()
            self.receive_queue.put(data)
            if self.callback_function:
                self.callback_function(data)

        if self.close_pipes:
            win32file.CloseHandle(pipe_handle)

    def receive_data(self):
        return self.receive_queue.get()

    def register_callback(self, callback_function):
        self.callback_function = callback_function
