import tkinter as tk
from tkinter import simpledialog, ttk
import multiprocessing
import subprocess

from cod_sursa import create_database, insert_initial_urls, bfs_process

def start_scraping(urls, depth):
    create_database()
    insert_initial_urls(urls, depth)
    bfs_process()

def submit_action():
    urls = url_text.get("1.0", "end-1c").split()  # Modified to get text from Text widget
    depth = int(depth_spinbox.get())
    if urls and depth:
        # Start the scraping process
        proc = multiprocessing.Process(target=start_scraping, args=(urls, depth))
        proc.start()
        status_label.config(text=f"Started scraping {len(urls)} URLs with depth {depth}.")
        # Launch UIDB.py as a new process
        subprocess.Popen(["python", "UIDB.py"])
    else:
        status_label.config(text="Please enter valid URLs and depth.")

def main():
    global app, url_text, depth_spinbox, status_label
    app = tk.Tk()
    app.title("URL Scraper Interface")
    app.configure(bg='light blue')

    tk.Label(app, text="Enter URLs (space-separated):", bg='light blue', fg='black').pack(pady=10, anchor='w')
    url_text = tk.Text(app, height=2, width=50, font=('Arial', 12))
    url_text.pack(padx=10, pady=10, fill='both', expand=True)

    tk.Label(app, text="Enter Depth:", bg='light blue', fg='black').pack(pady=10, anchor='w')
    depth_spinbox = tk.Spinbox(app, from_=0, to=10, width=5, font=('Arial', 12))
    depth_spinbox.pack(pady=10)

    submit_button = tk.Button(app, text="Start Scraping", command=submit_action, bg='green', fg='white', font=('Arial', 12), padx=10)
    submit_button.pack(pady=20)

    status_label = tk.Label(app, text="", bg='light blue', fg='black', font=('Arial', 12))
    status_label.pack(pady=10)

    app.mainloop()

if __name__ == '__main__':
    main()