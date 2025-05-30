import os
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

# Constants
DEFAULT_TAG_FOLDER = Path.home() / "Documents" / "Tagged Files"
TAG_CONFIG_FILE = Path.home() / ".file_organizer_tags.json"

# App State
file_list = []
tag_map = {}  # filename -> tag
tag_to_folder = {}  # tag -> folder path

# Load saved tag-folder mappings if exists
if TAG_CONFIG_FILE.exists():
    with open(TAG_CONFIG_FILE, "r") as f:
        tag_to_folder = {k: Path(v) for k, v in json.load(f).items()}

def save_tag_config():
    with open(TAG_CONFIG_FILE, "w") as f:
        json.dump({k: str(v) for k, v in tag_to_folder.items()}, f)

def scan_directory():
    downloads = Path.home() / "Downloads"
    documents = Path.home() / "Documents"
    extensions = (".csv", ".xls", ".xlsx", ".doc", ".docx", ".txt")

    file_list.clear()
    for folder in [downloads, documents]:
        for file in folder.glob("*"):
            if file.suffix.lower() in extensions and file.is_file():
                file_list.append(file)

    refresh_file_list()

def refresh_file_list(sort_key=None, reverse=False):
    for item in tree.get_children():
        tree.delete(item)

    if sort_key:
        file_list.sort(key=sort_key, reverse=reverse)

    for file in file_list:
        tag = tag_map.get(file.name, "")
        mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        tree.insert("", "end", values=(file.name, tag, file.suffix, mod_time))

def assign_tag():
    selected = tree.selection()
    tag = tag_combo.get().strip()

    if not selected:
        messagebox.showinfo("Info", "Select a file to tag.")
        return
    if not tag:
        messagebox.showinfo("Info", "Enter or select a tag name.")
        return

    if tag not in tag_combo["values"]:
        tag_combo["values"] = (*tag_combo["values"], tag)

    for sel in selected:
        filename = tree.item(sel, "values")[0]
        tag_map[filename] = tag

    refresh_file_list()

def choose_folder_for_tag():
    tag = tag_combo.get().strip()
    if not tag:
        messagebox.showinfo("Info", "Enter or select a tag first.")
        return

    folder_path = filedialog.askdirectory()
    if folder_path:
        tag_to_folder[tag] = Path(folder_path)
        save_tag_config()
        messagebox.showinfo("Success", f"Tag '{tag}' assigned to folder:\n{folder_path}")

def run_cleanup():
    moved = 0
    for file in file_list:
        tag = tag_map.get(file.name)
        if tag:
            dest_folder = tag_to_folder.get(tag, DEFAULT_TAG_FOLDER / tag)
            dest_folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(file), dest_folder / file.name)
                moved += 1
            except Exception as e:
                print(f"Failed to move {file.name}: {e}")

    messagebox.showinfo("Cleanup", f"{moved} files moved successfully.")
    scan_directory()

def on_treeview_heading_click(col):
    reverse = tree_sort_state.get(col, False)
    if col == "Type":
        refresh_file_list(sort_key=lambda f: f.suffix, reverse=reverse)
    elif col == "Modified":
        refresh_file_list(sort_key=lambda f: f.stat().st_mtime, reverse=reverse)
    elif col == "Filename":
        refresh_file_list(sort_key=lambda f: f.name.lower(), reverse=reverse)
    elif col == "Tag":
        refresh_file_list(sort_key=lambda f: tag_map.get(f.name, "").lower(), reverse=reverse)
    tree_sort_state[col] = not reverse

# --- GUI Setup ---
root = tk.Tk()
root.title("File Organizer")
root.geometry("800x540")

top_frame = ttk.Frame(root)
top_frame.pack(padx=10, pady=10, fill="x")

scan_btn = ttk.Button(top_frame, text="Scan Files", command=scan_directory)
scan_btn.pack(side="left", padx=5)

ttk.Label(top_frame, text="Tag:").pack(side="left", padx=5)
tag_combo = ttk.Combobox(top_frame, width=20)
tag_combo.pack(side="left", padx=5)

tag_btn = ttk.Button(top_frame, text="Assign Tag", command=assign_tag)
tag_btn.pack(side="left", padx=5)

folder_btn = ttk.Button(top_frame, text="Set Folder for Tag", command=choose_folder_for_tag)
folder_btn.pack(side="left", padx=5)

# Treeview with Scrollbar
tree_frame = ttk.Frame(root)
tree_frame.pack(padx=10, pady=10, fill="both", expand=True)

tree_scroll = ttk.Scrollbar(tree_frame)
tree_scroll.pack(side="right", fill="y")

tree = ttk.Treeview(tree_frame, columns=("Filename", "Tag", "Type", "Modified"), show="headings", selectmode="extended", yscrollcommand=tree_scroll.set)
tree.heading("Filename", text="Filename", command=lambda: on_treeview_heading_click("Filename"))
tree.heading("Tag", text="Tag", command=lambda: on_treeview_heading_click("Tag"))
tree.heading("Type", text="Type", command=lambda: on_treeview_heading_click("Type"))
tree.heading("Modified", text="Modified", command=lambda: on_treeview_heading_click("Modified"))

tree.column("Filename", width=300)
tree.column("Tag", width=120)
tree.column("Type", width=80)
tree.column("Modified", width=150)

tree.pack(fill="both", expand=True)
tree_scroll.config(command=tree.yview)

bottom_frame = ttk.Frame(root)
bottom_frame.pack(pady=10)

cleanup_btn = ttk.Button(bottom_frame, text="Run Cleanup", command=run_cleanup)
cleanup_btn.pack()

# Sort state
tree_sort_state = {}

# Load saved tags to combobox
tag_combo["values"] = list(tag_to_folder.keys())

scan_directory()
root.mainloop()
