import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

def fetch_page(url):
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": UA})
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        return f"__ERROR__::{e}"

def extract_fields(html):
    # If error bubbled up
    if html.startswith("__ERROR__::"):
        return {"error": html.split("::", 1)[1]}

    soup = BeautifulSoup(html, "html.parser")

    # Title
    title = soup.title.string.strip() if soup.title and soup.title.string else "Not Found"

    # Meta Description (try name=description, then og:description)
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        description = desc_tag.get("content").strip()
    else:
        og_desc = soup.find("meta", attrs={"property": "og:description"})
        description = og_desc.get("content").strip() if og_desc and og_desc.get("content") else "Not Found"

    # First H1 only (as per your format)
    h1_tag = soup.find("h1")
    h1_text = h1_tag.get_text(strip=True) if h1_tag else "Not Found"

    return {"title": title, "description": description, "h1": h1_text}

def run_extraction():
    urls_text = url_input.get("1.0", tk.END).strip()
    if not urls_text:
        messagebox.showwarning("Input missing", "কমপক্ষে একটি URL লিখুন (লাইন বাই লাইন)।")
        return

    options = []
    if var_title.get():
        options.append("title")
    if var_desc.get():
        options.append("description")
    if var_h1.get():
        options.append("h1")

    if not options:
        messagebox.showwarning("Select fields", "কমপক্ষে একটি অপশন সিলেক্ট করুন: Title / Description / H1")
        return

    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]

    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)

    for idx, url in enumerate(urls, start=1):
        html = fetch_page(url)
        data = extract_fields(html)

        output_lines = [f"{idx}."]
        if "error" in data:
            output_lines.append(f"Error: {data['error']}")
        else:
            if "title" in options:
                output_lines.append(f"Title: {data['title']}")
            if "description" in options:
                output_lines.append(f"Meta Description: {data['description']}")
            if "h1" in options:
                output_lines.append(f"H1: {data['h1']}")

        output_box.insert(tk.END, "\n".join(output_lines) + "\n\n")

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

# ---- UI ----
root = tk.Tk()
root.title("Meta Extractor (Title / Description / H1)")

# Top instructions
tk.Label(root, text="URLs দিন (এক লাইন = এক URL)।\nনীচে যেগুলো টিক দেবেন শুধু সেগুলোই স্ক্র্যাপ হবে:",
         font=("Segoe UI", 10)).grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 4))

# URL input box
url_input = scrolledtext.ScrolledText(root, width=80, height=10, font=("Consolas", 10))
url_input.grid(row=1, column=0, columnspan=3, padx=10, pady=4)

# Checkboxes
var_title = tk.BooleanVar(value=True)
var_desc = tk.BooleanVar(value=True)
var_h1 = tk.BooleanVar(value=True)

chk_title = tk.Checkbutton(root, text="Title", variable=var_title)
chk_desc  = tk.Checkbutton(root, text="Meta Description", variable=var_desc)
chk_h1    = tk.Checkbutton(root, text="H1", variable=var_h1)

chk_title.grid(row=2, column=0, sticky="w", padx=10, pady=4)
chk_desc.grid(row=2, column=1, sticky="w", padx=10, pady=4)
chk_h1.grid(row=2, column=2, sticky="w", padx=10, pady=4)

# Action buttons
btn_extract = tk.Button(root, text="Extract", command=run_extraction, width=12)
btn_copy    = tk.Button(root, text="Copy Output", command=copy_output, width=12)
btn_clear   = tk.Button(root, text="Clear", command=clear_all, width=12)

btn_extract.grid(row=3, column=0, padx=10, pady=6, sticky="w")
btn_copy.grid(row=3, column=1, padx=10, pady=6, sticky="w")
btn_clear.grid(row=3, column=2, padx=10, pady=6, sticky="w")

# Output box
tk.Label(root, text="Output:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 4))
output_box = scrolledtext.ScrolledText(root, width=80, height=14, font=("Consolas", 10), state="disabled")
output_box.grid(row=5, column=0, columnspan=3, padx=10, pady=(0, 10))

root.mainloop()
