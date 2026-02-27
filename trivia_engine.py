import json
import random
import os
import re
import html
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DB_FILE = "master_trivia_database.json"
GAME_FILE = "game.json"
SKIP_OPTION = "-- SKIP / DO NOT IMPORT --"

class TriviaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Anime Trivia Engine")
        self.root.geometry("720x860")
        
        self.db = {"databaseTitle": "Ultimate Master Anime Trivia Database", "categories": []}
        self.pending_clues = []
        self.category_mappings = {}
        
        self.load_db()
        self.apply_dark_theme()
        self.create_widgets()

    def apply_dark_theme(self):
        self.bg_color = "#2b2b2b"
        self.fg_color = "#e0e0e0"
        self.input_bg = "#3c3f41"
        self.accent_color = "#4b6eaf"
        self.accent_hover = "#355487"
        self.danger_color = "#a83232"
        self.danger_hover = "#8a2727"
        self.success_color = "#2e7d32"

        self.root.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use('clam') 
        
        style.configure('.', background=self.bg_color, foreground=self.fg_color, fieldbackground=self.input_bg)
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=("Helvetica", 10))
        
        style.configure('TLabelframe', background=self.bg_color, foreground=self.fg_color, bordercolor="#555555")
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.accent_color, font=("Helvetica", 11, "bold"))
        
        style.configure('TButton', background=self.accent_color, foreground="#ffffff", padding=8, font=("Helvetica", 10, "bold"), borderwidth=0)
        style.map('TButton', background=[('active', self.accent_hover)])
        
        style.configure('Danger.TButton', background=self.danger_color)
        style.map('Danger.TButton', background=[('active', self.danger_hover)])

        style.configure('Success.TButton', background=self.success_color)
        style.map('Success.TButton', background=[('active', "#1b5e20")])
        
        style.configure('TRadiobutton', background=self.bg_color, foreground=self.fg_color, font=("Helvetica", 10))
        style.map('TRadiobutton', background=[('active', self.bg_color)])
        
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color, font=("Helvetica", 10))
        style.map('TCheckbutton', background=[('active', self.bg_color)])

        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.input_bg, foreground=self.fg_color, padding=[15, 5], font=("Helvetica", 10))
        style.map('TNotebook.Tab', background=[('selected', self.accent_color)], foreground=[('selected', "#ffffff")])
        
        style.configure('TCombobox', fieldbackground=self.input_bg, background=self.bg_color, foreground="#ffffff", arrowcolor="#ffffff")
        style.map('TCombobox', fieldbackground=[('readonly', self.input_bg)])

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load database: {e}")

    def save_db(self):
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2)
            self.refresh_categories()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save database: {e}")

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=15, pady=15)

        self.add_tab = ttk.Frame(notebook)
        self.import_tab = ttk.Frame(notebook)
        self.manage_tab = ttk.Frame(notebook)
        self.gen_tab = ttk.Frame(notebook)
        
        notebook.add(self.add_tab, text="Add Question")
        notebook.add(self.import_tab, text="Import Data")  # Renamed Tab
        notebook.add(self.manage_tab, text="Manage Categories")
        notebook.add(self.gen_tab, text="Generate Game")

        self.setup_add_tab()
        self.setup_import_tab()
        self.setup_manage_tab()
        self.setup_gen_tab()
        
        self.refresh_categories()

    def get_text_widget(self, parent, height, width):
        return tk.Text(parent, height=height, width=width, bg=self.input_bg, fg="#ffffff", 
                       insertbackground="#ffffff", relief="flat", padx=5, pady=5, font=("Helvetica", 10))

    # --- TAB 1: ADD QUESTION ---
    def setup_add_tab(self):
        frame = ttk.LabelFrame(self.add_tab, text=" Manual Question Entry ", padding=15)
        frame.pack(fill='both', expand=True, padx=15, pady=15)

        ttk.Label(frame, text="Category:\n(Select existing or TYPE to create new)").grid(row=0, column=0, sticky='nw', pady=10)
        self.cat_var = tk.StringVar()
        self.cat_combo = ttk.Combobox(frame, textvariable=self.cat_var, width=42)
        self.cat_combo.grid(row=0, column=1, pady=10, sticky='w')

        ttk.Label(frame, text="Difficulty (Points):").grid(row=1, column=0, sticky='w', pady=10)
        self.diff_var = tk.StringVar(value="100")
        ttk.Combobox(frame, textvariable=self.diff_var, values=["100", "200", "300", "400", "500", "800", "1000"], state="readonly", width=10).grid(row=1, column=1, sticky='w', pady=10)

        ttk.Label(frame, text="Media Type:").grid(row=2, column=0, sticky='w', pady=10)
        self.type_var = tk.StringVar(value="text")
        ttk.Combobox(frame, textvariable=self.type_var, values=["text", "image", "youtube", "spotify"], state="readonly", width=10).grid(row=2, column=1, sticky='w', pady=10)

        ttk.Label(frame, text="Media URL (if applicable):").grid(row=3, column=0, sticky='w', pady=10)
        self.url_entry = tk.Entry(frame, width=45, bg=self.input_bg, fg="#ffffff", insertbackground="#ffffff", relief="flat")
        self.url_entry.grid(row=3, column=1, sticky='w', pady=10, ipady=3)

        ttk.Label(frame, text="Prompt (Question):").grid(row=4, column=0, sticky='nw', pady=10)
        self.prompt_text = self.get_text_widget(frame, 4, 45)
        self.prompt_text.grid(row=4, column=1, pady=10)

        ttk.Label(frame, text="Correct Response:").grid(row=5, column=0, sticky='nw', pady=10)
        self.response_text = self.get_text_widget(frame, 3, 45)
        self.response_text.grid(row=5, column=1, pady=10)

        ttk.Label(frame, text="Host Notes (Optional):").grid(row=6, column=0, sticky='nw', pady=10)
        self.notes_text = self.get_text_widget(frame, 3, 45)
        self.notes_text.grid(row=6, column=1, pady=10)

        ttk.Button(frame, text="Save Question to Database", command=self.add_question).grid(row=7, column=0, columnspan=2, pady=15)

    # --- TAB 2: IMPORT DATA (HTML & JSON) ---
    def setup_import_tab(self):
        frame = ttk.LabelFrame(self.import_tab, text=" Smart Batch Import (HTML / JSON) ", padding=20)
        frame.pack(fill='both', expand=True, padx=15, pady=15)

        ttk.Label(frame, text="Step 1: Select a JeopardyLabs HTML or exported JSON file.", justify="center").pack(pady=(0, 10))

        self.file_path_var = tk.StringVar()
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill='x', pady=5)
        
        tk.Entry(file_frame, textvariable=self.file_path_var, state='readonly', width=45, bg=self.input_bg, fg="#ffffff").pack(side='left', padx=(0, 10), ipady=5)
        # Point the button to the new unified analyze_file method
        ttk.Button(file_frame, text="Browse & Analyze", command=self.analyze_file).pack(side='left')

        self.mapping_frame = ttk.LabelFrame(frame, text=" Step 2: Map Categories ", padding=15)
        self.mapping_frame.pack(fill='both', expand=True, pady=20)
        
        self.mapping_instructions = ttk.Label(self.mapping_frame, text="No file analyzed yet.", foreground="#888888")
        self.mapping_instructions.pack(pady=20)
        
        self.mapping_container = ttk.Frame(self.mapping_frame)
        self.mapping_container.pack(fill='both', expand=True)

        self.normalize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Standardize point values to 100-500 scale (Recommended)", variable=self.normalize_var).pack(anchor='w', pady=(10, 5))

        self.commit_btn = ttk.Button(frame, text="Confirm & Import to Database", style="Success.TButton", command=self.commit_import, state="disabled")
        self.commit_btn.pack(pady=10)

    # --- TAB 3: MANAGE CATEGORIES ---
    def setup_manage_tab(self):
        frame = ttk.LabelFrame(self.manage_tab, text=" Transfer & Merge Categories ", padding=20)
        frame.pack(fill='both', expand=True, padx=15, pady=15)

        info_text = (
            "Use this tool to consolidate your database. All questions from the\n"
            "Source Category will be moved to the Destination Category.\n"
            "The Source Category will then be deleted."
        )
        ttk.Label(frame, text=info_text, justify="center").pack(pady=(0, 20))

        ttk.Label(frame, text="Source Category (Will be emptied and deleted):", font=("Helvetica", 10, "bold")).pack(anchor='w', pady=(10, 5))
        self.src_cat_var = tk.StringVar()
        self.src_cat_combo = ttk.Combobox(frame, textvariable=self.src_cat_var, width=50, state="readonly")
        self.src_cat_combo.pack(anchor='w', ipady=3)

        ttk.Label(frame, text="Destination Category (Select existing or TYPE to create new):", font=("Helvetica", 10, "bold")).pack(anchor='w', pady=(20, 5))
        self.dest_cat_var = tk.StringVar()
        self.dest_cat_combo = ttk.Combobox(frame, textvariable=self.dest_cat_var, width=50)
        self.dest_cat_combo.pack(anchor='w', ipady=3)

        ttk.Button(frame, text="Transfer Questions & Delete Source", style="Danger.TButton", command=self.transfer_category).pack(pady=40)

    # --- TAB 4: GENERATE GAME ---
    def setup_gen_tab(self):
        frame = ttk.Frame(self.gen_tab, padding=30)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Game Board Generator", font=("Helvetica", 18, "bold"), foreground=self.accent_color).pack(pady=15)
        
        info_text = (
            "This will scan your master database and find all categories\n"
            "that contain at least one question for every point value (100-500).\n\n"
            "It will then randomly select 5 valid categories, pull random questions\n"
            "for each slot, and create a fresh game.json file."
        )
        ttk.Label(frame, text=info_text, justify="center").pack(pady=20)
        
        ttk.Button(frame, text="Generate Random Game Board", command=self.generate_game).pack(pady=40)

    # --- GLOBAL LOGIC ---
    def refresh_categories(self):
        categories = sorted([cat["name"] for cat in self.db.get("categories", [])])
        
        if hasattr(self, 'cat_combo'):
            self.cat_combo['values'] = categories
        if hasattr(self, 'src_cat_combo'):
            self.src_cat_combo['values'] = categories
        if hasattr(self, 'dest_cat_combo'):
            self.dest_cat_combo['values'] = categories

    # --- IMPORT LOGIC ---
    def analyze_file(self):
        # Allow both HTML and JSON files in the browser dialogue
        file_path = filedialog.askopenfilename(filetypes=[("Trivia Files", "*.html *.json"), ("All Files", "*.*")])
        if not file_path:
            return
            
        self.file_path_var.set(file_path)
        self.pending_clues = []
        self.category_mappings = {}
        unique_file_categories = set()

        try:
            # --- JSON PARSING LOGIC ---
            if file_path.lower().endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for cat in data.get("categories", []):
                    cat_name = cat.get("name", "Unknown Category").strip()
                    unique_file_categories.add(cat_name)

                    for clue in cat.get("clues", []):
                        prompt = clue.get("prompt", "").strip()
                        response = clue.get("response", "").strip()
                        
                        if not prompt or not response:
                            continue
                        
                        # Support both "difficulty" (master format) and "points" (game format)
                        difficulty = clue.get("difficulty") or clue.get("points") or 100
                        media_type = clue.get("type", "text")
                        url = clue.get("url", "")
                        
                        self.pending_clues.append({
                            "original_category": cat_name,
                            "difficulty": int(difficulty),
                            "type": media_type,
                            "prompt": prompt,
                            "response": response,
                            "url": url
                        })

            # --- HTML PARSING LOGIC ---
            elif file_path.lower().endswith('.html'):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                cell_pattern = re.compile(
                    r'<div class="cell-inner"[^>]*data-category="([^"]*)"[^>]*>(\d+)</div>\s*'
                    r'<div class="front answer"[^>]*>(.*?)</div>\s*'
                    r'<div class="back question"[^>]*>(.*?)</div>',
                    re.DOTALL | re.IGNORECASE
                )

                matches = cell_pattern.findall(content)
                
                for html_cat, points, front_html, back_html in matches:
                    html_cat = html_cat.strip()
                    unique_file_categories.add(html_cat)
                    
                    difficulty = int(points)
                    media_type = "text"
                    media_url = ""

                    yt_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)', front_html, re.IGNORECASE)
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', front_html, re.IGNORECASE)
                    spotify_match = re.search(r'(https?://open\.spotify\.com/track/[\w-]+)', front_html, re.IGNORECASE)

                    if yt_match:
                        media_type = "youtube"
                        media_url = yt_match.group(1)
                    elif spotify_match:
                        media_type = "spotify"
                        media_url = spotify_match.group(1)
                    elif img_match:
                        media_type = "image"
                        media_url = img_match.group(1)

                    def clean_text(text):
                        text = re.sub(r'<[^>]+>', ' ', text)
                        text = html.unescape(text)
                        return re.sub(r'\s+', ' ', text).strip()

                    prompt = clean_text(front_html)
                    response = clean_text(back_html)

                    if prompt and response:
                        self.pending_clues.append({
                            "original_category": html_cat,
                            "difficulty": difficulty,
                            "type": media_type,
                            "prompt": prompt,
                            "response": response,
                            "url": media_url
                        })

            else:
                messagebox.showerror("Unsupported File", "Please select a valid .html or .json file.")
                return

            if not self.pending_clues:
                messagebox.showerror("Parse Error", "No valid questions found in this file.")
                return

            # Build the Mapping UI (Same for both HTML and JSON!)
            self.mapping_instructions.pack_forget()
            for widget in self.mapping_container.winfo_children():
                widget.destroy()

            ttk.Label(self.mapping_container, text="Found in File:", font=("Helvetica", 9, "bold")).grid(row=0, column=0, sticky='w', padx=5, pady=5)
            ttk.Label(self.mapping_container, text="Map to Database Category:", font=("Helvetica", 9, "bold")).grid(row=0, column=1, sticky='w', padx=5, pady=5)

            db_categories = [SKIP_OPTION] + sorted([cat["name"] for cat in self.db.get("categories", [])])

            for idx, cat_name in enumerate(sorted(unique_file_categories)):
                row_idx = idx + 1
                ttk.Label(self.mapping_container, text=f"• {cat_name}").grid(row=row_idx, column=0, sticky='w', padx=5, pady=8)
                
                var = tk.StringVar(value=cat_name) 
                self.category_mappings[cat_name] = var
                
                cb = ttk.Combobox(self.mapping_container, textvariable=var, values=db_categories, width=35)
                cb.grid(row=row_idx, column=1, sticky='w', padx=5, pady=8)

            self.commit_btn.config(state="normal")
            messagebox.showinfo("Analysis Complete", f"Found {len(self.pending_clues)} questions across {len(unique_file_categories)} categories.\n\nPlease map them to your database categories below, then click Confirm.")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while parsing the file:\n{e}")

    def commit_import(self):
        if not self.pending_clues:
            return

        normalize = self.normalize_var.get()
        imported_count = 0
        skipped_count = 0
        new_categories_created = set()

        filtered_clues = []
        for clue in self.pending_clues:
            mapped_cat_name = self.category_mappings[clue["original_category"]].get().strip()
            if mapped_cat_name == SKIP_OPTION:
                skipped_count += 1
                continue
            filtered_clues.append(clue)

        if normalize and filtered_clues:
            cat_points = {}
            for clue in filtered_clues:
                c = clue["original_category"]
                if c not in cat_points: cat_points[c] = set()
                cat_points[c].add(clue["difficulty"])
                
            point_maps = {}
            for c, pts in cat_points.items():
                sorted_pts = sorted(list(pts))
                point_maps[c] = {}
                for i, p in enumerate(sorted_pts):
                    point_maps[c][p] = min((i + 1) * 100, 500)
                    
            for clue in filtered_clues:
                clue["difficulty"] = point_maps[clue["original_category"]][clue["difficulty"]]

        for clue in filtered_clues:
            mapped_cat_name = self.category_mappings[clue["original_category"]].get().strip()
            
            new_clue = {
                "difficulty": clue["difficulty"], 
                "type": clue["type"], 
                "prompt": clue["prompt"], 
                "response": clue["response"]
            }
            if clue["url"]: 
                new_clue["url"] = clue["url"]

            target_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == mapped_cat_name.lower()), None)
            if target_cat:
                target_cat["clues"].append(new_clue)
            else:
                self.db["categories"].append({"name": mapped_cat_name, "clues": [new_clue]})
                new_categories_created.add(mapped_cat_name)
            
            imported_count += 1

        if imported_count > 0:
            self.save_db()
        
        msg = f"Successfully imported and mapped {imported_count} questions!"
        if skipped_count > 0:
            msg += f"\nSkipped {skipped_count} questions."
        if new_categories_created:
            msg += f"\n\nCreated {len(new_categories_created)} new categories in database:\n" + "\n".join(f"- {c}" for c in new_categories_created)
        
        messagebox.showinfo("Import Complete", msg)
        
        self.file_path_var.set("") 
        self.pending_clues = []
        self.category_mappings = {}
        for widget in self.mapping_container.winfo_children():
            widget.destroy()
        self.mapping_instructions.pack(pady=20)
        self.commit_btn.config(state="disabled")

    # --- ADD QUESTION LOGIC ---
    def add_question(self):
        category_name = self.cat_var.get().strip()
        difficulty = int(self.diff_var.get())
        media_type = self.type_var.get()
        url = self.url_entry.get().strip()
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        response = self.response_text.get("1.0", tk.END).strip()
        host_notes = self.notes_text.get("1.0", tk.END).strip()

        if not category_name or not prompt or not response:
            messagebox.showwarning("Incomplete", "Category, Prompt, and Response are required fields.")
            return

        new_clue = {"difficulty": difficulty, "type": media_type, "prompt": prompt, "response": response}
        if url: new_clue["url"] = url
        if host_notes: new_clue["hostNotes"] = host_notes

        target_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == category_name.lower()), None)
        is_new_category = False
        if target_cat:
            target_cat["clues"].append(new_clue)
        else:
            self.db["categories"].append({"name": category_name, "clues": [new_clue]})
            is_new_category = True

        self.save_db()
        
        msg = f"Question successfully added to '{category_name}'!"
        if is_new_category: msg += "\n\n(A new category was automatically created)."
        messagebox.showinfo("Success", msg)
        
        self.prompt_text.delete("1.0", tk.END)
        self.response_text.delete("1.0", tk.END)
        self.url_entry.delete(0, tk.END)
        self.notes_text.delete("1.0", tk.END)

    # --- MANAGE CATEGORY LOGIC ---
    def transfer_category(self):
        source_name = self.src_cat_var.get().strip()
        dest_name = self.dest_cat_var.get().strip()

        if not source_name or not dest_name:
            messagebox.showwarning("Incomplete", "Please select both a Source and Destination category.")
            return

        if source_name.lower() == dest_name.lower():
            messagebox.showwarning("Error", "Source and Destination categories cannot be the same.")
            return

        source_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == source_name.lower()), None)
        if not source_cat:
            messagebox.showerror("Error", f"Source category '{source_name}' not found in the database.")
            return

        clue_count = len(source_cat["clues"])
        if not messagebox.askyesno("Confirm Transfer", f"Are you sure you want to move {clue_count} questions from '{source_name}' to '{dest_name}'?\n\n'{source_name}' will be permanently deleted."):
            return

        dest_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == dest_name.lower()), None)
        
        is_new_category = False
        if dest_cat:
            dest_cat["clues"].extend(source_cat["clues"])
        else:
            self.db["categories"].append({"name": dest_name, "clues": source_cat["clues"]})
            is_new_category = True

        self.db["categories"].remove(source_cat)
        self.save_db()

        msg = f"Successfully moved {clue_count} questions to '{dest_name}'."
        if is_new_category:
            msg += "\n\n(A new category was automatically created)."
        messagebox.showinfo("Transfer Complete", msg)

        self.src_cat_var.set("")
        self.dest_cat_var.set("")

    # --- GENERATE GAME LOGIC ---
    def generate_game(self):
        valid_categories = []
        for cat in self.db.get("categories", []):
            available_diffs = {clue["difficulty"] for clue in cat["clues"]}
            if {100, 200, 300, 400, 500}.issubset(available_diffs):
                valid_categories.append(cat)
                
        if len(valid_categories) < 5:
            messagebox.showerror("Error", f"Not enough valid categories.\nYou only have {len(valid_categories)} categories with a full 100-500 point spread.\nYou need at least 5.")
            return

        selected_cats = random.sample(valid_categories, 5)
        game_data = {"gameTitle": "Anime Jeopardy - Random Generation", "categories": []}

        for cat in selected_cats:
            board_category = {"name": cat["name"], "clues": []}
            for points in [100, 200, 300, 400, 500]:
                matching_clues = [clue for clue in cat["clues"] if clue["difficulty"] == points]
                chosen_clue = random.choice(matching_clues).copy()
                chosen_clue["points"] = chosen_clue.pop("difficulty")
                board_category["clues"].append(chosen_clue)
                
            game_data["categories"].append(board_category)

        try:
            with open(GAME_FILE, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=2)
            messagebox.showinfo("Success", f"Game successfully generated!\nSaved as {GAME_FILE}.\n\nYou can now upload this file in your Moderator View.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate game: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TriviaApp(root)
    root.mainloop()