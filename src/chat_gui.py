import tkinter as tk
from tkinter import scrolledtext
import queue
import threading

# This module creates and manages the text-based chat GUI.

class ChatGUI(threading.Thread):
    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True
        self.window = None

    def run(self):
        """Creates and runs the Tkinter GUI in a separate thread."""
        self.window = tk.Tk()
        self.window.title("Kim Young-mi")
        self.window.geometry("400x500")

        # --- Display Area ---
        txt_display = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state='disabled', bg='#2b2b2b', fg='white', font=("Helvetica", 10))
        txt_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Configure tags for styling messages
        txt_display.tag_config('user', foreground='#a9d1ff', justify='right')
        txt_display.tag_config('assistant', foreground='#e6e6e6')
        txt_display.tag_config('system', foreground='#ffcc66', font=("Helvetica", 8, "italic"))

        # --- Input Area ---
        input_frame = tk.Frame(self.window, bg='#2b2b2b')
        input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        txt_input = tk.Entry(input_frame, bg='#404040', fg='white', insertbackground='white')
        txt_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        txt_input.bind("<Return>", lambda event: self.send_message(txt_input))

        btn_send = tk.Button(input_frame, text="Send", command=lambda: self.send_message(txt_input), bg='#555555', fg='white', activebackground='#666666')
        btn_send.pack(side=tk.RIGHT, padx=(5, 0))

        # Start checking for new messages from the main app
        self.window.after(100, lambda: self.check_for_new_messages(txt_display))

        # Start the GUI event loop
        self.window.mainloop()

    def send_message(self, txt_input):
        """Sends a message from the input box to the main application."""
        message = txt_input.get()
        if message:
            self.input_queue.put(message)
            txt_input.delete(0, tk.END)

    def check_for_new_messages(self, txt_display):
        """Periodically checks the output queue for messages from the main app."""
        try:
            while True:
                message, tag = self.output_queue.get_nowait()
                txt_display.config(state='normal')
                txt_display.insert(tk.END, f"{message}\n\n", tag)
                txt_display.config(state='disabled')
                txt_display.see(tk.END)
        except queue.Empty:
            pass

        if self.window:
            self.window.after(100, lambda: self.check_for_new_messages(txt_display))

def start_gui_thread(input_queue, output_queue):
    """Function to be called from main.py to start the GUI."""
    gui = ChatGUI(input_queue, output_queue)
    gui.start()
    return gui

if __name__ == '__main__':
    print("--- Testing chat_gui.py ---")
    q_in = queue.Queue()
    q_out = queue.Queue()

    def dummy_responder():
        q_out.put(("Kim Young-mi: Hello! Type a message to start.", 'assistant'))
        q_out.put(("[SYSTEM] Game awareness module loaded.", 'system'))

        while True:
            try:
                msg = q_in.get(timeout=1)
                q_out.put((f"You: {msg}", 'user'))
                time.sleep(1)
                q_out.put(("Kim Young-mi: I'm a test response!", 'assistant'))
            except queue.Empty:
                pass

    threading.Thread(target=dummy_responder, daemon=True).start()
    start_gui_thread(q_in, q_out)

    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping test.")