import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import csv
from urllib.parse import urlparse

def get_url_count():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM urls')
        count = c.fetchone()[0]
        return count

def get_email_count():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM emails')
        count = c.fetchone()[0]
        return count
def fetch_urls():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM urls')
        return c.fetchall()


def fetch_emails():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM emails')
        return c.fetchall()

def populate_emails(data=None):
    for row in email_tree.get_children():
        email_tree.delete(row)
    if not data:
        data = fetch_emails()
    for row in data:
        email_tree.insert('', 'end', values=row)


def refresh_data():
    populate_urls()  # Refresh URL data
    populate_emails()  # Refresh email data
    url_count.set(f"URLs Count: {get_url_count()}")  # Update URL count
    email_count.set(f"Emails Count: {get_email_count()}")  # Update Email count
def populate_urls(data=None):
    for row in url_tree.get_children():
        url_tree.delete(row)
    if not data:
        data = fetch_urls()
    for row in data:
        url_tree.insert('', 'end', values=row)




def add_url():
    url = simpledialog.askstring("Input", "Enter URL:")
    if url:
        domain, subdomain = get_domain_subdomain(url)
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO urls (url, domain, subdomain, depth, visited) VALUES (?, ?, ?, ?, 0)',
                      (url, domain, subdomain, 0))
            conn.commit()
        populate_urls()


def delete_url():
    selected = url_tree.focus()
    if not selected:
        messagebox.showwarning("Warning", "No URL selected")
        return
    values = url_tree.item(selected, 'values')
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM urls WHERE id = ?', (values[0],))
        conn.commit()
    populate_urls()


def update_url():
    selected = url_tree.focus()
    if not selected:
        messagebox.showwarning("Warning", "No URL selected")
        return
    values = url_tree.item(selected, 'values')
    new_url = simpledialog.askstring("Input", "Enter new URL:", initialvalue=values[2])
    if new_url:
        domain, subdomain = get_domain_subdomain(new_url)
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE urls SET url = ?, domain = ?, subdomain = ? WHERE id = ?',
                      (new_url, domain, subdomain, values[0]))
            conn.commit()
        populate_urls()


def add_email():
    email = simpledialog.askstring("Input", "Enter Email:")
    if email:
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            c.execute('INSERT OR IGNORE INTO emails (url_id, domain, email) VALUES (NULL, ?, ?)',
                      ('unknown', email))
            conn.commit()
        populate_emails()


def delete_email():
    selected = email_tree.focus()
    if not selected:
        messagebox.showwarning("Warning", "No Email selected")
        return
    values = email_tree.item(selected, 'values')
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('DELETE FROM emails WHERE id = ?', (values[0],))
        conn.commit()
    populate_emails()


def update_email():
    selected = email_tree.focus()
    if not selected:
        messagebox.showwarning("Warning", "No Email selected")
        return
    values = email_tree.item(selected, 'values')
    new_email = simpledialog.askstring("Input", "Enter new Email:", initialvalue=values[3])
    if new_email:
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            c.execute('UPDATE emails SET email = ? WHERE id = ?', (new_email, values[0]))
            conn.commit()
        populate_emails()


def search_url():
    query = search_var_url.get()
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM urls WHERE url LIKE ?', ('%' + query + '%',))
        results = c.fetchall()
    populate_urls(results)


def search_email():
    query = search_var_email.get()
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM emails WHERE email LIKE ?', ('%' + query + '%',))
        results = c.fetchall()
    populate_emails(results)


def sort_urls(col_name, ascending=True):
    col_index = url_columns_dict[col_name]
    data = fetch_urls()
    data.sort(key=lambda x: x[col_index], reverse=not ascending)
    populate_urls(data)


def sort_emails(col_name, ascending=True):
    col_index = email_columns_dict[col_name]
    data = fetch_emails()
    data.sort(key=lambda x: x[col_index], reverse=not ascending)
    populate_emails(data)


def filter_urls():
    query = filter_var_url.get()
    column = filter_column_var_url.get()
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        query = f'SELECT * FROM urls WHERE {column} LIKE ?'
        c.execute(query, ('%' + query + '%',))
        results = c.fetchall()
    populate_urls(results)


def filter_emails():
    query = filter_var_email.get()
    column = filter_column_var_email.get()
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        query = f'SELECT * FROM emails WHERE {column} LIKE ?'
        c.execute(query, ('%' + query + '%',))
        results = c.fetchall()
    populate_emails(results)


def on_select_url(event):
    selected = url_tree.focus()
    if not selected:
        return
    values = url_tree.item(selected, 'values')
    if values:
        messagebox.showinfo(title='URL Selected', message=f'You selected URL: {values[2]}')


def on_select_email(event):
    selected = email_tree.focus()
    if not selected:
        return
    values = email_tree.item(selected, 'values')
    if values:
        messagebox.showinfo(title='Email Selected', message=f'You selected Email: {values[3]}')


def get_domain_subdomain(url):
    parsed_uri = urlparse(url)
    domain = parsed_uri.netloc
    if domain.startswith("www."):
        domain = domain[4:]  # Strip 'www.'
    pieces = domain.split('.')
    subdomain = '.'.join(pieces[:-2]) if len(pieces) > 2 else ''
    domain = '.'.join(pieces[-2:])
    return domain, subdomain


def export_to_db3():
    filepath = filedialog.asksaveasfilename(defaultextension=".db3", filetypes=[("SQLite Database", "*.db3")])
    if filepath:
        with sqlite3.connect('email_scraper.db') as original_db:
            with sqlite3.connect(filepath) as export_db:
                original_db.backup(export_db, pages=1, progress=None)
        messagebox.showinfo("Export", f"Database exported successfully to {filepath}")


def export_to_csv():
    filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if filepath:
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            tables = [("urls", fetch_urls), ("emails", fetch_emails)]
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.writer(csvfile)
                for table_name, fetch_function in tables:
                    csv_writer.writerow([table_name.upper()])
                    csv_writer.writerow([col[0] for col in c.execute(f"PRAGMA table_info({table_name})")])
                    for row in fetch_function():
                        csv_writer.writerow(row)
                    csv_writer.writerow([])  # Empty row between tables
        messagebox.showinfo("Export", f"Database exported successfully to {filepath}")


def import_from_db3():
    filepath = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db3")])
    if filepath:
        with sqlite3.connect('email_scraper.db') as original_db:
            with sqlite3.connect(filepath) as import_db:
                import_db.backup(original_db, pages=1, progress=None)
        populate_urls()
        populate_emails()
        messagebox.showinfo("Import", f"Database imported successfully from {filepath}")

def import_from_csv():
    filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filepath:
        with sqlite3.connect('email_scraper.db') as conn:
            c = conn.cursor()
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                csv_reader = csv.reader(csvfile)
                table_name = None
                columns = None
                for row in csv_reader:
                    if not row:
                        table_name = None
                        continue
                    if row[0].isupper():
                        table_name = row[0].lower()
                        columns = next(csv_reader)
                        continue
                    if table_name and columns:
                        placeholders = ', '.join(['?'] * len(columns))
                        c.execute(f'INSERT OR IGNORE INTO {table_name} ({", ".join(columns)}) VALUES ({placeholders})',
                                  row)
            conn.commit()
        populate_urls()
        populate_emails()
        messagebox.showinfo("Import", f"Database imported successfully from {filepath}")


def create_menu(root):
    menubar = tk.Menu(root)

    url_menu = tk.Menu(menubar, tearoff=0)
    url_menu.add_command(label="Add URL", command=add_url)
    url_menu.add_command(label="Delete URL", command=delete_url)
    url_menu.add_command(label="Update URL", command=update_url)
    menubar.add_cascade(label="URLs", menu=url_menu)

    email_menu = tk.Menu(menubar, tearoff=0)
    email_menu.add_command(label="Add Email", command=add_email)
    email_menu.add_command(label="Delete Email", command=delete_email)
    email_menu.add_command(label="Update Email", command=update_email)
    menubar.add_cascade(label="Emails", menu=email_menu)

    export_menu = tk.Menu(menubar, tearoff=0)
    export_menu.add_command(label="Export to DB3", command=export_to_db3)
    export_menu.add_command(label="Export to CSV", command=export_to_csv)
    export_menu.add_command(label="Import from DB3", command=import_from_db3)
    export_menu.add_command(label="Import from CSV", command=import_from_csv)
    menubar.add_cascade(label="Export/Import", menu=export_menu)


    root.config(menu=menubar)


# Set up the main application window
root = tk.Tk()
root.title('Email Scraper Database UI')

style = ttk.Style()
style.configure('TButton', font=('Helvetica', 12))
style.configure('TLabel', font=('Helvetica', 12))
style.configure('TEntry', font=('Helvetica', 12))
style.configure('TNotebook.Tab', font=('Helvetica', 12))
style.configure('Treeview.Heading', font=('Helvetica', 12, 'bold'))

create_menu(root)

search_var_url = tk.StringVar()
filter_var_url = tk.StringVar()
filter_column_var_url = tk.StringVar(value='url')

search_var_email = tk.StringVar()
filter_var_email = tk.StringVar()
filter_column_var_email = tk.StringVar(value='email')

tab_control = ttk.Notebook(root)
url_tab = ttk.Frame(tab_control)
email_tab = ttk.Frame(tab_control)
tab_control.add(url_tab, text='URLs')
tab_control.add(email_tab, text='Emails')
tab_control.pack(expand=1, fill='both')

url_columns = ('id', 'domain', 'url', 'subdomain', 'depth', 'visited')
email_columns = ('id', 'url_id', 'domain', 'email')
url_columns_dict = {name: idx for idx, name in enumerate(url_columns)}
email_columns_dict = {name: idx for idx, name in enumerate(email_columns)}

# URL Tab
url_frame = ttk.Frame(url_tab)
url_frame.pack(fill='x', padx=10, pady=10)
refresh_button = ttk.Button(url_frame, text="Refresh Data", command=refresh_data)
refresh_button.pack(side='right', padx=10)

ttk.Label(url_frame, text="Search URL:").pack(side='left', padx=5)
search_entry_url = ttk.Entry(url_frame, textvariable=search_var_url)
search_entry_url.pack(side='left', padx=5)
search_button_url = ttk.Button(url_frame, text='Search', command=search_url)
search_button_url.pack(side='left', padx=5)

filter_frame_url = ttk.Frame(url_tab)
filter_frame_url.pack(fill='x', padx=10, pady=10)

ttk.Label(filter_frame_url, text="Filter by:").pack(side='left', padx=5)
filter_entry_url = ttk.Entry(filter_frame_url, textvariable=filter_var_url)
filter_entry_url.pack(side='left', padx=5)
filter_column_menu_url = ttk.OptionMenu(filter_frame_url, filter_column_var_url, 'url', 'url', 'domain', 'subdomain')
filter_column_menu_url.pack(side='left', padx=5)
filter_button_url = ttk.Button(filter_frame_url, text='Filter', command=filter_urls)
filter_button_url.pack(side='left', padx=5)

sort_asc_button_url = ttk.Button(filter_frame_url, text='Sort Asc',
                                 command=lambda: sort_urls(filter_column_var_url.get(), ascending=True))
sort_asc_button_url.pack(side='left', padx=5)
sort_desc_button_url = ttk.Button(filter_frame_url, text='Sort Desc',
                                  command=lambda: sort_urls(filter_column_var_url.get(), ascending=False))
sort_desc_button_url.pack(side='left', padx=5)

add_url_button = ttk.Button(url_frame, text='Add URL', command=add_url)
add_url_button.pack(side='left', padx=5)

delete_url_button = ttk.Button(url_frame, text='Delete URL', command=delete_url)
delete_url_button.pack(side='left', padx=5)

update_url_button = ttk.Button(url_frame, text='Update URL', command=update_url)
update_url_button.pack(side='left', padx=5)

url_tree = ttk.Treeview(url_tab, columns=url_columns, show='headings')
for col in url_columns:
    url_tree.heading(col, text=col)
    url_tree.column(col, width=100)
url_tree.pack(expand=1, fill='both', padx=10, pady=10)
url_tree.bind('<<TreeviewSelect>>', on_select_url)
# Create StringVar objects for counts
url_count = tk.StringVar()
email_count = tk.StringVar()

# Initial fetch for counts
url_count.set(f"URLs Count: {get_url_count()}")
email_count.set(f"Emails Count: {get_email_count()}")

# URL Tab
url_frame = ttk.Frame(url_tab)
url_frame.pack(fill='x', padx=10, pady=10)

# Display URL count
url_count_label = ttk.Label(url_frame, textvariable=url_count)
url_count_label.pack(side='left', padx=5)



# Email Tab setup
email_frame = ttk.Frame(email_tab)
email_frame.pack(fill='x', padx=10, pady=10)

# Initialize the StringVar for email count and set its value


# Email search entry and button
ttk.Label(email_frame, text="Search Email:").pack(side='left', padx=5)
search_entry_email = ttk.Entry(email_frame, textvariable=search_var_email)
search_entry_email.pack(side='left', padx=5)
search_email_button = ttk.Button(email_frame, text='Search', command=search_email)
search_email_button.pack(side='left', padx=5)

# Email filter frame setup
filter_frame_email = ttk.Frame(email_tab)
filter_frame_email.pack(fill='x', padx=10, pady=10)

# Filter options for emails
ttk.Label(filter_frame_email, text="Filter by:").pack(side='left', padx=5)
filter_entry_email = ttk.Entry(filter_frame_email, textvariable=filter_var_email)
filter_entry_email.pack(side='left', padx=5)
filter_column_menu_email = ttk.OptionMenu(filter_frame_email, filter_column_var_email, 'email', 'email', 'domain', 'url_id')
filter_column_menu_email.pack(side='left', padx=5)
filter_button_email = ttk.Button(filter_frame_email, text='Filter', command=filter_emails)
filter_button_email.pack(side='left', padx=5)

# Sorting buttons for emails
sort_asc_button_email = ttk.Button(filter_frame_email, text='Sort Asc', command=lambda: sort_emails(filter_column_var_email.get(), True))
sort_asc_button_email.pack(side='left', padx=5)
sort_desc_button_email = ttk.Button(filter_frame_email, text='Sort Desc', command=lambda: sort_emails(filter_column_var_email.get(), False))
sort_desc_button_email.pack(side='left', padx=5)

# Buttons for adding, deleting, and updating emails
add_email_button = ttk.Button(email_frame, text='Add Email', command=add_email)
add_email_button.pack(side='left', padx=5)
delete_email_button = ttk.Button(email_frame, text='Delete Email', command=delete_email)
delete_email_button.pack(side='left', padx=5)
update_email_button = ttk.Button(email_frame, text='Update Email', command=update_email)
update_email_button.pack(side='left', padx=5)

# Email Treeview for displaying email entries
email_tree = ttk.Treeview(email_tab, columns=email_columns, show='headings')
for col in email_columns:
    email_tree.heading(col, text=col)
    email_tree.column(col, width=100)
email_tree.pack(expand=1, fill='both', padx=10, pady=10)
email_tree.bind('<<TreeviewSelect>>', on_select_email)

# Refresh button to refresh email data and count
refresh_button_email = ttk.Button(email_frame, text="Refresh Data", command=refresh_data)
refresh_button_email.pack(side='right', padx=10)
email_count = tk.StringVar()
email_count.set(f"Emails Count: {get_email_count()}")

email_frame = ttk.Frame(email_tab)
email_frame.pack(fill='x', padx=10, pady=10)
# Display the email count on the Email Tab
email_count_label = ttk.Label(email_frame, textvariable=email_count)
email_count_label.pack(side='left', padx=5)
# Function to refresh email data and update the email count


# Populate the initial email list and count
refresh_data()

# Populate the tree views with data
populate_urls()
populate_emails()

root.mainloop()
