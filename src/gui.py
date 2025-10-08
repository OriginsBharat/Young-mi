# src/gui.py
# This module contains the code for the tkinter-based text chat window.

import tkinter as tk
from tkinter import scrolledtext, Entry, Button
import threading
import queue

class ChatWindow(threading.Thread):
    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.daemon = True
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.root = None

    def _send_message(self, event=None):
        """Sends the message from the input box to the main app."""
        message = self.entry_box.get()
        if message:
            self.input_queue.put(message)
            self.entry_box.delete(0, tk.END)
            # Display the user's own message in the chat history
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.insert(tk.END, f"You: {message}\n")
            self.chat_history.config(state=tk.DISABLED)
            self.chat_history.see(tk.END)

    def _check_for_new_messages(self):
        """Checks the output queue for new messages from the AI and displays them."""
        while not self.output_queue.empty():
            try:
                message = self.output_queue.get_nowait()
                self.chat_history.config(state=tk.NORMAL)
                self.chat_history.insert(tk.END, f"Kim Young-mi: {message}\n")
                self.chat_history.config(state=tk.DISABLED)
                self.chat_history.see(tk.END)
            except queue.Empty:
                pass
        # Schedule the next check
        self.root.after(100, self._check_for_new_messages)

    def run(self):
        """Creates and runs the tkinter GUI."""
        self.root = tk.Tk()
        self.root.title("Chat with Kim Young-mi")
        self.root.geometry("400x500")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Chat history display
        self.chat_history = scrolledtext.ScrolledText(self.root, state=tk.DISABLED, wrap=tk.WORD, bg="#2b2b2b", fg="white")
        self.chat_history.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Message entry box
        self.entry_box = Entry(self.root, bg="#404040", fg="white", insertbackground="white")
        self.entry_box.grid(row=1, column=0, sticky="ew", padx=(5, 0), pady=5)
        self.entry_box.bind("<Return>", self._send_message)

        # Send button
        self.send_button = Button(self.root, text="Send", command=self._send_message, bg="#505050", fg="white", activebackground="#606060")
        self.send_button.grid(row=1, column=1, sticky="ew", padx=(0, 5), pady=5)

        # Start checking for messages from the main thread
        self.root.after(100, self._check_for_new_messages)

        # Start the GUI event loop
        self.root.mainloop()

if __name__ == '__main__':
    # This is for testing the GUI module directly
    # It simulates the main application loop.

    def dummy_main_thread(input_q, output_q):
        print("Dummy main thread started.")
        while True:
            try:
                message = input_q.get(timeout=2)
                print(f"Main thread received: {message}")
                response = f"I received your message: '{message}'. This is a dummy response."
                output_q.put(response)
            except queue.Empty:
                pass

    in_q = queue.Queue()
    out_q = queue.Queue()

    # Start the dummy main thread
    main_thread_sim = threading.Thread(target=dummy_main_thread, args=(in_q, out_q))
    main_thread_sim.daemon = True
    main_thread_sim.start()

    # Start the GUI
    chat_gui = ChatWindow(in_q, out_q)
    chat_gui.run() # Run in the main thread for this test