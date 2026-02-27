import flet as ft
import json
import random
import os
import re
import html

DB_FILE = "master_trivia_database.json"
GAME_FILE = "game.json"
SKIP_OPTION = "-- SKIP / DO NOT IMPORT --"

class TriviaEngineApp:
    def __init__(self):
        self.db = {"databaseTitle": "Ultimate Master Anime Trivia Database", "categories": []}
        self.pending_clues = []
        self.category_mappings = {}
        self.load_db()

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
            except Exception as e:
                print(f"Error loading DB: {e}")

    def save_db(self):
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2)
            self.refresh_all_dropdowns()
        except Exception as e:
            self.show_message("Error", f"Failed to save database: {e}")

    def main(self, page: ft.Page):
        self.page = page
        page.title = "Anime Trivia Engine"
        page.theme_mode = ft.ThemeMode.DARK
        
        page.window.width = 750
        page.window.height = 900
        page.scroll = ft.ScrollMode.AUTO

       # --- Helper for Alerts ---
        self.alert_dialog = ft.AlertDialog(title=ft.Text(""), content=ft.Text(""))

        # --- Helper for Alerts ---
        def show_msg(title, text):
            def close_dlg(e):
                dlg.open = False
                page.update()

            dlg = ft.AlertDialog(
                title=ft.Text(title, weight="bold", color=ft.Colors.BLUE_400),
                content=ft.Text(text),
                actions=[ft.Button(content=ft.Text("OK"), on_click=close_dlg)]
            )
            
            # Flet requires dialogs to be explicitly added to the visual overlay tree
            page.overlay.append(dlg)
            dlg.open = True
            page.update()
            
        self.show_message = show_msg

        # ==========================================
        # TAB 1: ADD QUESTION
        # ==========================================
        self.add_cat_dropdown = ft.Dropdown(label="Select Existing Category", width=275)
        self.add_cat_textfield = ft.TextField(label="...Or Type New Category", width=275)
        
        self.add_diff_dropdown = ft.Dropdown(label="Difficulty", options=[ft.dropdown.Option(str(i)) for i in [100, 200, 300, 400, 500, 800, 1000]], value="100", width=150)
        self.add_type_dropdown = ft.Dropdown(label="Media Type", options=[ft.dropdown.Option(t) for t in ["text", "image", "youtube", "spotify"]], value="text", width=150)
        self.add_url_field = ft.TextField(label="Media URL (Optional)", width=560)
        self.add_prompt_field = ft.TextField(label="Prompt (Question)", multiline=True, min_lines=3, max_lines=5, width=560)
        self.add_response_field = ft.TextField(label="Correct Response", multiline=True, min_lines=2, max_lines=4, width=560)
        self.add_notes_field = ft.TextField(label="Host Notes (Optional)", multiline=True, min_lines=2, max_lines=4, width=560)

        add_tab_content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Manual Question Entry", size=20, weight="bold", color=ft.Colors.BLUE_400),
                ft.Row([self.add_cat_dropdown, self.add_cat_textfield]),
                ft.Row([self.add_diff_dropdown, self.add_type_dropdown]),
                self.add_url_field,
                self.add_prompt_field,
                self.add_response_field,
                self.add_notes_field,
                # THE FIX: Uses ft.Button and the 'content' kwarg instead of 'text'
                ft.Button(content="Save Question to Database", on_click=self.add_question, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
            ])
        )

        # ==========================================
        # TAB 2: IMPORT DATA
        # ==========================================
        self.import_file_path = ft.TextField(label="Selected File", read_only=True, expand=True)
        self.mapping_column = ft.Column(spacing=10)
        self.normalize_checkbox = ft.Checkbox(label="Standardize point values to 100-500 scale (Recommended)", value=True)
        self.commit_btn = ft.Button(content="Confirm & Import to Database", on_click=self.commit_import, disabled=True, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)

        async def pick_file_and_analyze(e):
            files = await ft.FilePicker().pick_files(allowed_extensions=["html", "json"])
            if files and len(files) > 0:
                self.import_file_path.value = files[0].path
                self.analyze_file()
                page.update()

        import_tab_content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Smart Batch Import (HTML / JSON)", size=20, weight="bold", color=ft.Colors.BLUE_400),
                ft.Text("Step 1: Select a JeopardyLabs HTML or exported JSON file."),
                ft.Row([
                    self.import_file_path,
                    ft.Button(content="Browse & Analyze", on_click=pick_file_and_analyze)
                ]),
                ft.Divider(height=30, color=ft.Colors.GREY_800),
                ft.Text("Step 2: Map Categories", size=18, weight="bold"),
                self.mapping_column,
                ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
                self.normalize_checkbox,
                self.commit_btn
            ], scroll=ft.ScrollMode.AUTO)
        )

        # ==========================================
        # TAB 3: MANAGE CATEGORIES
        # ==========================================
        self.man_src_dropdown = ft.Dropdown(label="Source Category (Will be deleted)", width=500)
        self.man_dest_dropdown = ft.Dropdown(label="Select Existing Destination", width=245)
        self.man_dest_textfield = ft.TextField(label="...Or Type New Category", width=245)

        manage_tab_content = ft.Container(
            padding=20,
            content=ft.Column([
                ft.Text("Transfer & Merge Categories", size=20, weight="bold", color=ft.Colors.BLUE_400),
                ft.Text("All questions from the Source Category will be moved to the Destination Category. The Source will then be deleted."),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                self.man_src_dropdown,
                ft.Row([self.man_dest_dropdown, self.man_dest_textfield]),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Button(content="Transfer Questions & Delete Source", on_click=self.transfer_category, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)
            ])
        )

        # ==========================================
        # TAB 4: GENERATE GAME
        # ==========================================
        gen_tab_content = ft.Container(
            padding=40,
            content=ft.Column([
                ft.Text("Game Board Generator", size=24, weight="bold", color=ft.Colors.BLUE_400),
                ft.Text("This will scan your master database and find all categories that contain at least one question for every point value (100-500).", text_align=ft.TextAlign.CENTER),
                ft.Text("It will randomly select 5 valid categories and create a fresh game.json file.", text_align=ft.TextAlign.CENTER),
                ft.Divider(height=40, color=ft.Colors.TRANSPARENT),
                ft.Button(content="Generate Random Game Board", on_click=self.generate_game, scale=1.2, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # --- THE FIX: NEW FLET 0.80.0+ TAB ARCHITECTURE ---
        tabs = ft.Tabs(
            selected_index=0,
            length=4,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Add Question"),
                            ft.Tab(label="Import Data"),
                            ft.Tab(label="Manage Categories"),
                            ft.Tab(label="Generate Game"),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            add_tab_content,
                            import_tab_content,
                            manage_tab_content,
                            gen_tab_content,
                        ]
                    )
                ]
            )
        )

        page.add(tabs)
        self.refresh_all_dropdowns()

    # ==========================================
    # LOGIC FUNCTIONS
    # ==========================================
    def refresh_all_dropdowns(self):
        categories = sorted([cat["name"] for cat in self.db.get("categories", [])])
        options = [ft.dropdown.Option(c) for c in categories]
        
        self.add_cat_dropdown.options = options
        self.man_src_dropdown.options = options
        self.man_dest_dropdown.options = options
        
        if hasattr(self, 'page'):
            self.page.update()

    def add_question(self, e):
        cat_name = self.add_cat_textfield.value.strip() if self.add_cat_textfield.value else self.add_cat_dropdown.value
        
        prompt = self.add_prompt_field.value.strip()
        response = self.add_response_field.value.strip()

        if not cat_name or not prompt or not response:
            self.show_message("Incomplete", "Category, Prompt, and Response are required.")
            return

        new_clue = {
            "difficulty": int(self.add_diff_dropdown.value),
            "type": self.add_type_dropdown.value,
            "prompt": prompt,
            "response": response
        }
        if self.add_url_field.value: new_clue["url"] = self.add_url_field.value.strip()
        if self.add_notes_field.value: new_clue["hostNotes"] = self.add_notes_field.value.strip()

        target_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == cat_name.lower()), None)
        if target_cat:
            target_cat["clues"].append(new_clue)
        else:
            self.db["categories"].append({"name": cat_name, "clues": [new_clue]})

        self.save_db()
        self.show_message("Success", f"Question added to '{cat_name}'!")
        
        self.add_cat_textfield.value = ""
        self.add_prompt_field.value = ""
        self.add_response_field.value = ""
        self.add_url_field.value = ""
        self.add_notes_field.value = ""
        self.page.update()

    def analyze_file(self):
        file_path = self.import_file_path.value
        if not file_path: return
            
        self.pending_clues = []
        self.category_mappings = {}
        unique_file_categories = set()

        try:
            if file_path.lower().endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for cat in data.get("categories", []):
                    cat_name = cat.get("name", "Unknown Category").strip()
                    unique_file_categories.add(cat_name)

                    for clue in cat.get("clues", []):
                        prompt = clue.get("prompt", "").strip()
                        response = clue.get("response", "").strip()
                        if not prompt or not response: continue
                        
                        difficulty = clue.get("difficulty") or clue.get("points") or 100
                        self.pending_clues.append({
                            "original_category": cat_name,
                            "difficulty": int(difficulty),
                            "type": clue.get("type", "text"),
                            "prompt": prompt,
                            "response": response,
                            "url": clue.get("url", "")
                        })

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
                    
                    media_type, media_url = "text", ""
                    yt_match = re.search(r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)', front_html, re.IGNORECASE)
                    img_match = re.search(r'<img[^>]+src="([^"]+)"', front_html, re.IGNORECASE)
                    spotify_match = re.search(r'(https?://open\.spotify\.com/track/[\w-]+)', front_html, re.IGNORECASE)

                    if yt_match: media_type, media_url = "youtube", yt_match.group(1)
                    elif spotify_match: media_type, media_url = "spotify", spotify_match.group(1)
                    elif img_match: media_type, media_url = "image", img_match.group(1)

                    def clean_text(text):
                        text = re.sub(r'<[^>]+>', ' ', text)
                        return re.sub(r'\s+', ' ', html.unescape(text)).strip()

                    prompt, response = clean_text(front_html), clean_text(back_html)
                    if prompt and response:
                        self.pending_clues.append({
                            "original_category": html_cat, "difficulty": int(points),
                            "type": media_type, "prompt": prompt, "response": response, "url": media_url
                        })

            self.mapping_column.controls.clear()
            db_categories = [SKIP_OPTION] + sorted([cat["name"] for cat in self.db.get("categories", [])])

            for cat_name in sorted(unique_file_categories):
                local_opts = list(db_categories)
                if cat_name not in local_opts:
                    local_opts.append(cat_name)
                    
                options = [ft.dropdown.Option(c) for c in local_opts]
                
                dd = ft.Dropdown(options=options, value=cat_name, width=350)
                self.category_mappings[cat_name] = dd
                
                self.mapping_column.controls.append(
                    ft.Row([ft.Text(f"• {cat_name}", width=200), dd])
                )

            self.commit_btn.disabled = False
            self.page.update()
            self.show_message("Analysis Complete", f"Found {len(self.pending_clues)} questions. Please map them below.")

        except Exception as e:
            self.show_message("Error", str(e))

    def commit_import(self, e):
        filtered_clues = []
        for clue in self.pending_clues:
            mapped_cat_name = self.category_mappings[clue["original_category"]].value
            if mapped_cat_name == SKIP_OPTION: continue
            filtered_clues.append(clue)

        if self.normalize_checkbox.value and filtered_clues:
            cat_points = {}
            for clue in filtered_clues:
                c = clue["original_category"]
                if c not in cat_points: cat_points[c] = set()
                cat_points[c].add(clue["difficulty"])
                
            point_maps = {}
            for c, pts in cat_points.items():
                sorted_pts = sorted(list(pts))
                point_maps[c] = {p: min((i + 1) * 100, 500) for i, p in enumerate(sorted_pts)}
                    
            for clue in filtered_clues:
                clue["difficulty"] = point_maps[clue["original_category"]][clue["difficulty"]]

        for clue in filtered_clues:
            mapped_cat_name = self.category_mappings[clue["original_category"]].value
            new_clue = {"difficulty": clue["difficulty"], "type": clue["type"], "prompt": clue["prompt"], "response": clue["response"]}
            if clue["url"]: new_clue["url"] = clue["url"]

            target_cat = next((cat for cat in self.db["categories"] if cat["name"].lower() == mapped_cat_name.lower()), None)
            if target_cat: target_cat["clues"].append(new_clue)
            else: self.db["categories"].append({"name": mapped_cat_name, "clues": [new_clue]})

        self.save_db()
        self.show_message("Success", f"Imported {len(filtered_clues)} questions into the database!")
        
        self.import_file_path.value = ""
        self.mapping_column.controls.clear()
        self.commit_btn.disabled = True
        self.page.update()

    def transfer_category(self, e):
        src = self.man_src_dropdown.value
        dest = self.man_dest_textfield.value.strip() if self.man_dest_textfield.value else self.man_dest_dropdown.value

        if not src or not dest or src == dest:
            self.show_message("Error", "Please select different Source and Destination categories.")
            return

        source_cat = next((cat for cat in self.db["categories"] if cat["name"] == src), None)
        if not source_cat: return

        dest_cat = next((cat for cat in self.db["categories"] if cat["name"] == dest), None)
        if dest_cat: dest_cat["clues"].extend(source_cat["clues"])
        else: self.db["categories"].append({"name": dest, "clues": source_cat["clues"]})

        self.db["categories"].remove(source_cat)
        self.save_db()
        self.show_message("Success", f"Transferred questions and deleted '{src}'.")
        
        self.man_src_dropdown.value = None
        self.man_dest_dropdown.value = None
        self.man_dest_textfield.value = ""
        self.page.update()

    def generate_game(self, e):
        valid_cats = [cat for cat in self.db.get("categories", []) if {100, 200, 300, 400, 500}.issubset({clue["difficulty"] for clue in cat["clues"]})]
                
        if len(valid_cats) < 5:
            self.show_message("Error", f"Not enough valid categories (Needs 5, found {len(valid_cats)}). Ensure categories have 100-500 point spread.")
            return

        selected_cats = random.sample(valid_cats, 5)
        game_data = {"gameTitle": "Anime Jeopardy - Random Generation", "categories": []}

        for cat in selected_cats:
            board_category = {"name": cat["name"], "clues": []}
            for points in [100, 200, 300, 400, 500]:
                matching = [c for c in cat["clues"] if c["difficulty"] == points]
                chosen = random.choice(matching).copy()
                chosen["points"] = chosen.pop("difficulty")
                board_category["clues"].append(chosen)
            game_data["categories"].append(board_category)

        try:
            with open(GAME_FILE, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=2)
            self.show_message("Success", f"Game generated! Saved as {GAME_FILE}.")
        except Exception as ex:
            self.show_message("Error", str(ex))

if __name__ == "__main__":
    app = TriviaEngineApp()
    ft.run(app.main)