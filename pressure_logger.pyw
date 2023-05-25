import threading
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno
import csv
from datetime import datetime
import signal
import serial
import os
import sys
from pathlib import Path
from tkinter import StringVar

DEFAULT_LOG_NAME = ''

def write_to_csv(data, datetime, log_name):
    if log_name == DEFAULT_LOG_NAME:
        return
    
    with open(f'{log_name}.csv', 'a+', newline='') as csvfile:
        r = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        r.writerow([datetime.strftime('%m/%d/%Y %H:%M:%S:%f')[:-3], data])

def readserial(comport, baudrate, running, current_pressure, file_name_entry):
    log_file_name = file_name_entry.get()
    if log_file_name == '':
        log_file_name = DEFAULT_LOG_NAME

    ser = serial.Serial(comport, baudrate, timeout=0.5)
    while running[0]:
        
        data = ser.readline().decode().strip()
        d = datetime.now()
        timestamp = d.strftime('%H:%M:%S:%f')[:-3]

        if len(data) != 0:
            print(f'{timestamp} > {data}')
            current_pressure.configure(text=f'Current pressure: {data} Pa')
            write_to_csv(data, d, log_file_name)

def main():
    running = [False]
    thread = [None]

    # user interface
    root = tk.Tk()
    root.title("Pressure Logger")
    root.geometry('250x260')  # Specify the initial size of the window

    icon_path = Path(sys._MEIPASS, 'icon.ico') if hasattr(sys, '_MEIPASS') else 'icon.ico'
    root.iconbitmap(icon_path)

    def handler(signum, frame, running):
        '''Handler for Ctrl-C. Makes the readserial thread stop running.'''
        print("Ctrl-c was pressed. Shutting down and saving data.")
        running[0] = False
        root.destroy()

    # Create frame to hold widgets
    mainframe = ttk.Frame(root, padding="10")
    mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

    # Create widgets
    title = ttk.Label(mainframe, text="Pressure Logger", font=("Arial", 16))
    title.grid(column=0, row=0, columnspan=2)

    logging_status = ttk.Label(mainframe, text="Logging status: Inactive", padding="2")
    logging_status.grid(column=0, row=1, columnspan=2)

    current_pressure = ttk.Label(mainframe, text="No Pressure Readings", padding="2")
    current_pressure.grid(column=0, row=2, columnspan=2)

    file_name_label = ttk.Label(mainframe, text="Log Name:")
    file_name_label.grid(column=0, row=5, columnspan=2)

    open_latest_button = ttk.Button(mainframe, text="Open Current Log")
    open_latest_button.grid(column=0, row=4, sticky=(tk.W, tk.E), pady=5)

    def start_serial():
        '''Starts the serial log.'''
        if not running[0]:
            # if the program isn't already running, start it.
            running[0] = True
            logging_status.configure(text="Logging status: Active")
            open_latest_button.configure(state='disabled')
            # start reading the serial port in a new thread so the GUI doesn't lock up.
            # daemon=True means the thread will exit when the main thread exits.
            thread[0] = threading.Thread(target=readserial, args=('COM9', 9600, running, current_pressure, file_name_entry), daemon=True)
            # start the thread
            thread[0].start()

    def stop_serial():
        '''Stops the serial log.'''
        # if the program is running, stop it.
        if running[0]:
            # set the running flag to False so the readserial thread will exit.
            running[0] = False
            logging_status.configure(text="Logging status: Inactive")
            current_pressure.configure(text="No Pressure Readings")
            open_latest_button.configure(state='normal')
            # if the running thread doesn't exit in a reasonable amount of time, kill it.
            if thread[0] is not None:
                thread[0].join()  # Wait for the thread to finish if it hasn't already.
                thread[0] = None # delete it
    
    def open_latest_log(file_name):
        '''Opens the latest log file.'''
        # open pressure.csv using os
        os.startfile(f'{file_name}.csv')
    
    def open_log_folder():
        '''Opens the folder where the log files are stored.'''
        # open the folder where the log files are stored
        os.startfile(os.getcwd())

    # handle control c so that the serial loop doesn't keep running as a ghost process.
    signal.signal(signal.SIGINT, lambda signum, frame: handler(signum, frame, running))

    start_button = ttk.Button(mainframe, text="Start Logging", command=start_serial, state='disabled')
    start_button.grid(column=0, row=3, sticky=(tk.W, tk.E), pady=5)

    stop_button = ttk.Button(mainframe, text="Stop Logging", command=stop_serial)
    stop_button.grid(column=1, row=3, sticky=(tk.W, tk.E), pady=5)

    open_folder_button = ttk.Button(mainframe, text="Open Logs Folder", command=open_log_folder)
    open_folder_button.grid(column=1, row=4, sticky=(tk.W, tk.E), pady=5)

    def log_name_modified_handler(var):
        '''Handler for when the log name is modified.'''
        if var.get() == '':
            start_button.configure(state='disabled')
        else:
            start_button.configure(state='normal')

    log_name_var = StringVar()
    log_name_var.trace("w", lambda name, index, mode, var=log_name_var: log_name_modified_handler(var))

    file_name_entry = ttk.Entry(mainframe, textvariable=log_name_var)
    file_name_entry.grid(column=0, row=6, columnspan=2)
    file_name_entry.focus_set()

    open_latest_button.configure(command=lambda: open_latest_log(file_name_entry.get()))

    def handle_close():
        if running[0]:
            answer = askyesno(title='Quit Logging', message="Logging is active! Are you sure you want to exit the program?")
            if answer:
                root.destroy()
        else:
            root.destroy()

    root.protocol('WM_DELETE_WINDOW', handle_close)  # root is your root window

    # Make sure the widgets resize nicely
    for child in mainframe.winfo_children():
        child.grid_configure(padx=5, pady=5)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.mainloop()

    # If we get here, it means the Tkinter window has been closed.
    # Set the running flag to False so the readserial thread will exit.
    running[0] = False

if __name__ == "__main__":
    main()
