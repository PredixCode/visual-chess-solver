import customtkinter as ctk

class GUI:
    # Removed restart_cmd, we only need start and stop now!
    def __init__(self, config, start_cmd=None, stop_cmd=None) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.app = ctk.CTk()
        self.app.title("Chess Solver - Live Configuration")
        self.app.geometry("500x750")
        
        self.config = config
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        
        self._build_ui()

    def _build_ui(self):
        title_label = ctk.CTkLabel(self.app, text="Bot Configuration", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(20, 10))

        # --- Bot Control Panel (START / STOP) ---
        control_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        control_frame.pack(pady=(0, 10))

        self.start_btn = ctk.CTkButton(control_frame, text="▶ Start Bot", fg_color="#2B8C52", hover_color="#206B3E", command=self.start_bot)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(control_frame, text="⏹ Stop Bot", fg_color="#C62828", hover_color="#8E0000", command=self.stop_bot)
        self.stop_btn.pack(side="left", padx=10)

        # --- Active Bot Selector ---
        bot_mode_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        bot_mode_frame.pack(padx=20, pady=10, fill="x")
        ctk.CTkLabel(bot_mode_frame, text="Active Bot:").pack(side="left", padx=(10, 20))
        
        self.bot_mode_var = ctk.StringVar(value=self.config.mode)
        self.bot_type_selector = ctk.CTkSegmentedButton(
            bot_mode_frame, values=["Desktop", "Remote Phone"], 
            variable=self.bot_mode_var,
            command=self.on_mode_change 
        )
        self.bot_type_selector.pack(side="left", fill="x", expand=True)

        # --- Vision Mode Selector ---
        vision_mode_frame = ctk.CTkFrame(self.app, fg_color="transparent")
        vision_mode_frame.pack(padx=20, pady=(0, 10), fill="x")
        ctk.CTkLabel(vision_mode_frame, text="Vision Mode:").pack(side="left", padx=(10, 20))
        
        self.vision_mode_var = ctk.StringVar(value=self.config.vision_mode)
        self.vision_type_selector = ctk.CTkSegmentedButton(
            vision_mode_frame, values=["2D", "3D"], 
            variable=self.vision_mode_var,
            command=self.on_mode_change 
        )
        self.vision_type_selector.pack(side="left", fill="x", expand=True)

        # --- Bot Settings Frame ---
        bot_frame = ctk.CTkFrame(self.app)
        bot_frame.pack(padx=20, pady=10, fill="x")
        
        self.move_pieces_var = ctk.BooleanVar(value=self.config.move_pieces)
        self.move_pieces_switch = ctk.CTkSwitch(
            bot_frame, text="Move Pieces", 
            variable=self.move_pieces_var, 
            command=self.update_visibility 
        )
        self.move_pieces_switch.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        self.play_human_var = ctk.BooleanVar(value=self.config.play_like_human)
        self.play_human_switch = ctk.CTkSwitch(bot_frame, text="Play Like Human", variable=self.play_human_var)
        self.play_human_switch.grid(row=2, column=0, padx=20, pady=10, sticky="w")

        self.stream_url_label = ctk.CTkLabel(bot_frame, text="Phone Stream URL:")
        self.stream_url_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.stream_url_entry = ctk.CTkEntry(bot_frame, width=300)
        self.stream_url_entry.insert(0, self.config.phone_stream_url)
        self.stream_url_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="w")

        # --- Stockfish Settings Frame ---
        sf_frame = ctk.CTkFrame(self.app)
        sf_frame.pack(padx=20, pady=10, fill="x")

        def add_sf_entry(row, label_text, val):
            ctk.CTkLabel(sf_frame, text=label_text).grid(row=row, column=0, padx=20, pady=5, sticky="w")
            entry = ctk.CTkEntry(sf_frame, width=150)
            if val is not None:
                entry.insert(0, str(val))
            entry.grid(row=row, column=1, padx=20, pady=5, sticky="e")
            return entry

        self.sf_path_entry = add_sf_entry(1, "Relative Stockfish Path:", self.config.stockfish_config.get("path", ""))
        self.sf_threads_entry = add_sf_entry(2, "Threads (empty=max):", self.config.stockfish_config.get("threads"))
        self.sf_elo_entry = add_sf_entry(3, "ELO (empty=max):", self.config.elo)
        self.sf_time_entry = add_sf_entry(4, "Thinking Time (ms, empty=max):", self.config.think_time)
        self.sf_depth_entry = add_sf_entry(5, "Depth (empty=max):", self.config.depth)

        # --- Save Config Button ---
        self.save_btn = ctk.CTkButton(self.app, text="Save Config", command=self.save_and_reload)
        self.save_btn.pack(pady=20)

        # Trigger initial UI state on load
        self.update_visibility()

    # --- Dynamic UI Logic ---
    def update_visibility(self, *args):
        mode = self.bot_mode_var.get()
        move_pieces = self.move_pieces_var.get()

        if mode == "Remote Phone":
            self.move_pieces_switch.grid_remove()
            self.play_human_switch.grid_remove()
            
            self.stream_url_label.grid()
            self.stream_url_entry.grid()
        else:
            self.stream_url_label.grid_remove()
            self.stream_url_entry.grid_remove()
            
            self.move_pieces_switch.grid()
            if move_pieces:
                self.play_human_switch.grid()
            else:
                self.play_human_switch.grid_remove()

    def on_mode_change(self, selected_value=None):
        self.update_visibility()
        self.save_and_reload()

    # --- Control Methods ---
    def start_bot(self):
        if self.start_cmd:
            self.start_cmd()

    def stop_bot(self):
        if self.stop_cmd:
            self.stop_cmd()

    def _get_int_or_null(self, value: str):
        value = value.strip()
        return int(value) if value.isdigit() else None

    def save_and_reload(self):
        new_mode = self.bot_mode_var.get()
        old_mode = self.config.mode
        
        new_vision = self.vision_mode_var.get()
        old_vision = self.config.vision_mode

        self.config.file_data["bot"]["mode"] = new_mode
        self.config.file_data["bot"]["vision_mode"] = new_vision
        self.config.file_data["bot"]["move_pieces"] = self.move_pieces_var.get()
        self.config.file_data["bot"]["play_like_human"] = self.play_human_var.get()
        self.config.file_data["bot"]["phone"]["stream_url"] = self.stream_url_entry.get()

        self.config.file_data["stockfish"]["path"] = self.sf_path_entry.get()
        self.config.file_data["stockfish"]["threads"] = self._get_int_or_null(self.sf_threads_entry.get())
        self.config.file_data["stockfish"]["elo"] = self._get_int_or_null(self.sf_elo_entry.get())
        self.config.file_data["stockfish"]["thinking_time_in_ms"] = self._get_int_or_null(self.sf_time_entry.get()) or 1000
        self.config.file_data["stockfish"]["depth"] = self._get_int_or_null(self.sf_depth_entry.get())

        self.config.persist()
        print(f"Config saved! Bot Mode: {new_mode} | Vision Mode: {new_vision}")

        # If a core mode changed, gracefully stop the bot and wait for the user to press start.
        if (old_mode != new_mode or old_vision != new_vision) and self.stop_cmd:
            print("Core mode changed! Stopping active bot. Please click 'Start Bot' when ready.")
            self.stop_cmd()

    def run(self):
        self.app.mainloop()