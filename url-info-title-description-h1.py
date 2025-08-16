import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from threading import Thread
import time
from bs4 import BeautifulSoup

# Install undetected_chromedriver via: pip install undetected-chromedriver
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException, WebDriverException

MAX_RETRIES = 3
LOAD_TIMEOUT = 30
WAIT_AFTER_LOAD = 8  # wait for Cloudflare/interstitial

# ---------------------------
# Functions
# ---------------------------
def fetch_page(url, headless_mode):
    for attempt in range(1, MAX_RETRIES+1):
        try:
            options = uc.ChromeOptions()
            options.headless = headless_mode
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(LOAD_TIMEOUT)
            driver.get(url)
            time.sleep(WAIT_AFTER_LOAD)
            html = driver.page_source
            driver.quit()
            return html
        except (WebDriverException, TimeoutException) as e:
            if attempt == MAX_RETRIES:
                return f"__ERROR__::{str(e)}"
            time.sleep(2)

def extract_fields(html):
    if html.startswith("__ERROR__::"):
        return {"error": html.split("::",1)[1]}
    
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else "Not Found"

    desc_tag = soup.find("meta", attrs={"name":"description"})
    if desc_tag and desc_tag.get("content"):
        description = desc_tag.get("content").strip()
    else:
        og_desc = soup.find("meta", attrs={"property":"og:description"})
        description = og_desc.get("content").strip() if og_desc and og_desc.get("content") else "Not Found"

    h1_tags = soup.find_all("h1")
    h1_text = " | ".join([h.get_text(strip=True) for h in h1_tags]) if h1_tags else "Not Found"

    return {"title": title, "description": description, "h1": h1_text}

def start_thread():
    thread = Thread(target=run_extraction)
    thread.start()

def run_extraction():
    urls_text = url_input.get("1.0", tk.END).strip()
    if not urls_text:
        messagebox.showwarning("Input missing", "কমপক্ষে একটি URL লিখুন (লাইন বাই লাইন)।")
        return

    options_list = []
    if var_title.get(): options_list.append("title")
    if var_desc.get(): options_list.append("description")
    if var_h1.get(): options_list.append("h1")
    if not options_list:
        messagebox.showwarning("Select fields", "কমপক্ষে একটি অপশন সিলেক্ট করুন: Title / Description / H1")
        return

    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    total = len(urls)

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    progress_bar['maximum'] = total
    progress_bar['value'] = 0

    headless_mode = var_headless.get()

    for idx, url in enumerate(urls, start=1):
        status_label.config(text=f"Processing URL {idx}/{total} ...")
        root.update_idletasks()

        html = fetch_page(url, headless_mode)
        data = extract_fields(html)

        output_lines = [f"{idx}."]
        if "error" in data:
            output_lines.append(f"Error: {data['error']}")
        else:
            if "title" in options_list: output_lines.append(f"Title: {data['title']}")
            if "description" in options_list: output_lines.append(f"Meta Description: {data['description']}")
            if "h1" in options_list: output_lines.append(f"H1: {data['h1']}")

        output_box.insert(tk.END, "\n".join(output_lines) + "\n\n")
        progress_bar['value'] = idx
        root.update_idletasks()

    status_label.config(text="Done!")
    output_box.config(state="disabled")

def copy_output():
    text = output_box.get("1.0", tk.END)
    root.clipboard_clear()
    root.clipboard_append(text)
    messagebox.showinfo("Copied", "আউটপুট কপি করা হয়েছে!")

def clear_all():
    url_input.delete("1.0", tk.END)
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.config(state="disabled")
    var_title.set(True)
    var_desc.set(True)
    var_h1.set(True)
    var_headless.set(True)
    progress_bar['value'] = 0
    status_label.config(text="")

# ---------------------------
# GUI
# ---------------------------
root = tk.Tk()
root.title("Advanced Meta Extractor (Undetected Chrome)")

tk.Label(root, text="URLs দিন (এক লাইন = এক URL)।\nযেগুলো mark করবেন শুধু সেগুলো scrape হবে:",
         font=("Segoe UI",10)).grid(row=0,column=0,columnspan=3, sticky="w", padx=10, pady=(10,4))

url_input = scrolledtext.ScrolledText(root, width=80, height=10, font=("Consolas",10))
url_input.grid(row=1,column=0,columnspan=3,padx=10,pady=4)

var_title = tk.BooleanVar(value=True)
var_desc = tk.BooleanVar(value=True)
var_h1 = tk.BooleanVar(value=True)
var_headless = tk.BooleanVar(value=True)

tk.Checkbutton(root,text="Title",variable=var_title).grid(row=2,column=0, sticky="w", padx=10, pady=4)
tk.Checkbutton(root,text="Meta Description",variable=var_desc).grid(row=2,column=1, sticky="w", padx=10, pady=4)
tk.Checkbutton(root,text="H1",variable=var_h1).grid(row=2,column=2, sticky="w", padx=10, pady=4)
tk.Checkbutton(root,text="Run Headless (Background)",variable=var_headless).grid(row=3,column=0, sticky="w", padx=10, pady=4)

tk.Button(root,text="Extract",command=start_thread,width=12).grid(row=3,column=1, padx=10,pady=6, sticky="w")
tk.Button(root,text="Copy Output",command=copy_output,width=12).grid(row=3,column=2, padx=10,pady=6, sticky="w")
tk.Button(root,text="Clear",command=clear_all,width=12).grid(row=3,column=2, padx=10,pady=6, sticky="e")

progress_bar = ttk.Progressbar(root,length=500,mode='determinate')
progress_bar.grid(row=4,column=0,columnspan=3, padx=10,pady=(10,2))

status_label = tk.Label(root,text="", font=("Segoe UI",9,"italic"))
status_label.grid(row=5,column=0,columnspan=3, sticky="w", padx=10,pady=(0,4))

tk.Label(root,text="Output:", font=("Segoe UI",10,"bold")).grid(row=6,column=0,columnspan=3, sticky="w", padx=10,pady=(4,4))
output_box = scrolledtext.ScrolledText(root, width=80, height=14, font=("Consolas",10), state="disabled")
output_box.grid(row=7,column=0,columnspan=3, padx=10,pady=(0,10))

root.mainloop()
