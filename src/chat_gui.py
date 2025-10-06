import tkinter as tk
from tkinter import scrolledtext
import queue
import threading

class ChatGUI(threading.Thread):
    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = True

        self.window = None
        self.txt_display = None
        self.txt_input = None

    def run(self):
        """This method runs in a separate thread and creates the GUI."""
        self.window = tk.Tk()
        self.window.title("Kim Young-mi")
        self.window.geometry("400x500")

        # --- Display Area ---
        self.txt_display = scrolledtext.ScrolledText(self.window, wrap=tk.WORD, state='disabled')
        self.txt_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Configure tags for styling messages
        self.txt_display.tag_config('user', foreground='blue', justify='right')
        self.txt_display.tag_config('assistant', foreground='green')

        # --- Input Area ---
        input_frame = tk.Frame(self.window)
        input_frame.pack(padx=10, pady=10, fill=tk.X)

        self.txt_input = tk.Entry(input_frame)
        self.txt_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.txt_input.bind("<Return>", self.send_message)

        btn_send = tk.Button(input_frame, text="Send", command=self.send_message)
        btn_send.pack(side=tk.RIGHT)

        # Start a periodic check for new messages from the main app
        self.window.after(100, self.check_for_new_messages)

        # Start the GUI event loop
        self.window.mainloop()

    def send_message(self, event=None):
        """Sends the message from the input box to the main application."""
        message = self.txt_input.get()
        if message:
            self.input_queue.put(message)
            self.txt_input.delete(0, tk.END)

    def add_message_to_display(self, message, tag):
        """Adds a message to the display area with the appropriate styling."""
        if self.txt_display:
            self.txt_display.config(state='normal')
            self.txt_display.insert(tk.END, message + '\n', tag)
            self.txt_display.config(state='disabled')
            self.txt_display.see(tk.END) # Auto-scroll to the bottom

    def check_for_new_messages(self):
        """Periodically checks the output queue for messages from the main app."""
        try:
            while True:
                message, tag = self.output_queue.get_nowait()
                self.add_message_to_display(message, tag)
        except queue.Empty:
            pass # No new messages

        # Reschedule the check
        if self.window:
            self.window.after(100, self.check_for_new_messages)

# This function will be called from main.py to start the GUI
def start_gui_thread(input_queue, output_queue):
    gui = ChatGUI(input_queue, output_queue)
    gui.start()
    return gui

if __name__ == '__main__':
    # This is for testing the GUI directly
    print("--- Testing chat_gui.py ---")
    # Create dummy queues for testing
    q_in = queue.Queue()
    q_out = queue.Queue()

    # Function to simulate the main app receiving and responding
    def dummy_responder():
        while True:
            try:
                msg = q_in.get(timeout=1)
                q_out.put((f"You: {msg}", 'user'))
                q_out.put(("AI: I received your message.", 'assistant'))
            except queue.Empty:
                pass

    responder_thread = threading.Thread(target=dummy_responder, daemon=True)
    responder_thread.start()

    start_gui_thread(q_in, q_out)

    # Keep the main thread alive for the test
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping test.")