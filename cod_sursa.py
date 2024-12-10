import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import sqlite3
import re
import multiprocessing
import smtplib
import dns.resolver
import time  # Import the time module
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)




def create_database():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS urls')
        # Drop the emails table if it exists
        c.execute('DROP TABLE IF EXISTS emails')
        conn.commit()
        c.execute('''
            CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY,
                domain TEXT,
                url TEXT UNIQUE,
                subdomain TEXT,
                depth INTEGER,
                visited INTEGER DEFAULT 0
            )
        ''')
        # Create the emails table if not already present
        c.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                url_id INTEGER,
                domain TEXT,
                email TEXT UNIQUE,  
                FOREIGN KEY (url_id) REFERENCES urls (id)
            )
        ''')
        conn.commit()


def insert_initial_urls(start_urls, depth):
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        for url in start_urls:
            domain, subdomain = get_domain_subdomain(url)
            c.execute('INSERT OR IGNORE INTO urls (url, domain, subdomain, depth, visited) VALUES (?, ?, ?, ?, 0)',
                      (url, domain, subdomain, depth))
        conn.commit()


def bfs_process():
    with sqlite3.connect('email_scraper.db') as conn:
        c = conn.cursor()
        current_depth = c.execute('SELECT MAX(depth) FROM urls WHERE visited = 0').fetchone()[0]

        if current_depth == 0:
            print("Current depth is 0, ending the search")
            return  # Exit the function if depth is 0

        while current_depth is not None and current_depth >= 0:
            c.execute('SELECT url FROM urls WHERE visited = 0 AND depth = ?', (current_depth,))
            urls_to_process = [(url[0], current_depth) for url in c.fetchall()]

            remaining_urls = c.execute('SELECT COUNT(*) FROM urls WHERE visited = 0').fetchone()[0]
            print(f"Remaining URLs to process: {remaining_urls}")

            if not urls_to_process:
                current_depth -= 1
                continue

            with multiprocessing.Pool() as pool:
                pool.starmap(process_url, urls_to_process)s

            next_depth = c.execute('SELECT MAX(depth) FROM urls WHERE visited = 0').fetchone()[0]
            if next_depth is None or next_depth < current_depth:
                current_depth = next_depth
                if current_depth is None or current_depth < 0:
                    print("No more URLs left to process or all have been processed.")
                    break  # Exit loop if there are no more depths to process or if invalid depth
                print(f"Moving to depth {current_depth}")

def process_url(url, depth):
    conn = None
    try:
        conn = sqlite3.connect('email_scraper.db')
        response = safe_request(url)
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            process_content(url, response, depth, conn)
    except requests.exceptions.RequestException as e:
        print(f"Request error for {url}: {e}")
        if conn:
            conn.execute('UPDATE urls SET visited = 1 WHERE url = ?', (url,))
            conn.commit()
    finally:
        if conn:
            conn.close()

def safe_request(url, attempt=1):
    try:
        return requests.get(url, timeout=50)
    except requests.exceptions.SSLError as e:
        if attempt <= 3:  # Retry up to 3 times
            print(f"SSLError encountered with {url}. Retrying ({attempt}/3)...")
            return safe_request(url, attempt + 1)
        else:
            raise  # Reraise exception if all retries fail

def process_content(url, response, depth, conn):
    soup = BeautifulSoup(response.content, 'html.parser')
    print(f"Successfully parsed {url}")

    domain = urlparse(url).netloc
    email_pattern = r'\b[a-zA-Z0-9_.+-]+(?:@|\s*\[at\]\s*)[a-zA-Z0-9-]+\s*(?:\.|\[dot\]\s*)[a-zA-Z0-9-.]+\b'
    emails = re.findall(email_pattern, soup.get_text())
    print(f"Found {len(emails)} emails on {url}")

    for email in emails:
        print(f"Email {email} is valid and deliverable.")
        update_url_emails(url, [email], domain, conn)

    links_found = 0
    for link in soup.find_all('a', href=True):
        full_url = urljoin(url, link['href'])
        if not full_url.lower().endswith('.pdf') and not full_url.startswith('mailto:'):
            if urlparse(full_url).netloc == domain:
                insert_link(full_url, domain, "", depth - 1, conn)
                links_found += 1
    print(f"Found and inserted {links_found} links from {url}")
    conn.execute('UPDATE urls SET visited = 1 WHERE url = ?', (url,))
    conn.commit()
# def process_url(url, depth):
#     conn = None  # Initialize conn as None before the try block
#     print(f"Starting to process URL: {url} at depth {depth}")
#     try:
#         conn = sqlite3.connect('email_scraper.db')  # Open a new connection for each process
#         response = requests.get(url, timeout=50)  # Added timeout for the request
#         content_type = response.headers.get('Content-Type', '')
#         if 'text/html' in content_type:
#             soup = BeautifulSoup(response.content, 'html.parser')
#             print(f"Successfully parsed {url}")
#
#             domain = urlparse(url).netloc
#             email_pattern = r'\b[a-zA-Z0-9_.+-]+(?:@|\s*\[at\]\s*)[a-zA-Z0-9-]+\s*(?:\.|\[dot\]\s*)[a-zA-Z0-9-.]+\b'
#             emails = re.findall(email_pattern, soup.get_text())
#             print(f"Found {len(emails)} emails on {url}")
#
#             for email in emails:
#                 # if check_smtp(email):
#                     print(f"Email {email} is valid and deliverable.")
#                     update_url_emails(url, [email], domain, conn)
#                 # else:
#                 #     print(f"Email {email} is not deliverable.")
#
#             links_found = 0
#             for link in soup.find_all('a', href=True):
#                 full_url = urljoin(url, link['href'])
#                 if not full_url.lower().endswith('.pdf'):
#                     if urlparse(full_url).netloc == domain and not full_url.startswith('mailto:'):
#                         insert_link(full_url, domain, "", depth - 1, conn)
#                         links_found += 1
#             print(f"Found and inserted {links_found} links from {url}")
#             conn.execute('UPDATE urls SET visited = 1 WHERE url = ?', (url,))
#             conn.commit()
#         else:
#             print(f"Unsupported content type for URL {url}: {content_type}")
#             conn.execute('UPDATE urls SET visited = 1 WHERE url = ?', (url,))
#             conn.commit()
#     except requests.exceptions.RequestException as e:
#         print(f"Request error for {url}: {e}")
#         conn.execute('UPDATE urls SET visited = 1 WHERE url = ?', (url,))
#         conn.commit()
#     finally:
#         if conn:
#             conn.close()


def update_url_emails(url, emails, domain, conn):
    c = conn.cursor()
    url_id = None
    try:
        c.execute('SELECT id FROM urls WHERE url = ?', (url,))
        url_id = c.fetchone()[0]
        for email in emails:
            c.execute('INSERT OR IGNORE INTO emails (url_id, domain, email) VALUES (?, ?, ?)', (url_id, domain, email))
        conn.commit()
    except TypeError:
        print(f"No URL ID found for {url}. Inserting URL into database.")
        c.execute('INSERT OR IGNORE INTO urls (url, visited) VALUES (?, 1)', (url,))
        c.execute('SELECT id FROM urls WHERE url = ?', (url,))
        url_id = c.fetchone()[0]
        for email in emails:
            c.execute('INSERT OR IGNORE INTO emails (url_id, domain, email) VALUES (?, ?, ?)', (url_id, domain, email))
        conn.commit()


def insert_link(url, domain, subdomain, depth, conn):
    c = conn.cursor()
    if depth > 0:  # Only insert if the depth is non-negative
        c.execute('INSERT OR IGNORE INTO urls (url, domain, subdomain, depth, visited) VALUES (?, ?, ?, ?, 0)',
                  (url, domain, subdomain, depth))
        conn.commit()


def get_domain_subdomain(url):
    parsed_uri = urlparse(url)
    domain = parsed_uri.netloc
    if domain.startswith("www."):
        domain = domain[4:]  # Strip 'www.'
    pieces = domain.split('.')
    subdomain = '.'.join(pieces[:-2]) if len(pieces) > 2 else ''
    domain = '.'.join(pieces[-2:])
    return domain, subdomain


def check_smtp(email):
    domain = email.split('@')[-1]
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
        server = smtplib.SMTP(mx_record)
        server.set_debuglevel(0)  # Turn off debug output
        server.ehlo()
        server.mail('you@example.com')
        code, message = server.rcpt(email)
        server.quit()

        if code == 250:
            return True
        else:
            return False
    except Exception as e:
        print(f"SMTP check failed: {e}")
        return False


def safe_request(url, attempt=1):
    try:
        return requests.get(url, timeout=50, verify=False)  # Not recommended for production
    except requests.exceptions.SSLError as e:
        if attempt <= 3:
            print(f"SSLError encountered with {url}. Retrying ({attempt}/3)...")
            return safe_request(url, attempt + 1)
        else:
            raise  # Re-raise the exception if all retries fail

if __name__ == "__main__":
    start_time = time.time()  # Start time measurement
    start_urls = [

        "https://stiinte.utcluj.ro/acasa.html",


    ]
    create_database()
    insert_initial_urls(start_urls, 6)
    bfs_process()
    end_time = time.time()  # End time measurement
    print(f"Program completed in {end_time - start_time} seconds.")
