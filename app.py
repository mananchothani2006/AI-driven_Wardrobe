import customtkinter as ctk
from PIL import Image
import os
import pathlib
from tkinter import filedialog
import threading
import markdown
from tkinterweb import HtmlFrame

# ── Backend ──────────────────────────────────────────────────────────────────
from main import (
    clothes, save_clothes, Clothing,
    search_clothes, add_cloth, update_wear, delete_cloth, get_outfit_prompt,mark_clean
)

# ── Theme ─────────────────────────────────────────────────────────────────────
ACCENT  = "#6C63FF"
BG      = "#1A1A2E"
SURFACE = "#16213E"
CARD    = "#0F3460"
TEXT    = "#E0E0E0"
MUTED   = "#888"
SUCCESS = "#28a745"
DANGER  = "#dc3545"

ctk.set_appearance_mode("dark")

WARDROBE_DIR = pathlib.Path("wardrobe")
WARDROBE_DIR.mkdir(exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_ctk_image(image_path, size=(160, 160)):
    full_path = WARDROBE_DIR / image_path
    try:
        img = Image.open(full_path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except Exception:
        return None


# ── App ───────────────────────────────────────────────────────────────────────
class DrobeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Drobe")
        self.geometry("1100x700")
        self.configure(fg_color=BG)
        self.selected_image_path = None
        self._last_outfit = None
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()

        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.show_wardrobe()

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=200, fg_color=SURFACE, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            sb, text="Drobe",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=ACCENT
        ).grid(row=0, column=0, padx=20, pady=(32, 40))

        nav_items = [
            ("👕  My Wardrobe", self.show_wardrobe),
            ("➕  Add Item",    self.show_add_item),
            ("📋  Log Wear",    self.show_log_wear),
            ("✨  Get Outfit",  self.show_get_outfit),
        ]
        for i, (label, cmd) in enumerate(nav_items, start=1):
            ctk.CTkButton(
                sb, text=label, command=cmd,
                fg_color="transparent", text_color=TEXT,
                hover_color=CARD, anchor="w", height=44,
                font=ctk.CTkFont(size=15)
            ).grid(row=i, column=0, padx=12, pady=4, sticky="ew")

    # ── Shared helpers ────────────────────────────────────────────────────────
    def _clear(self):
        for w in self.main.winfo_children():
            w.destroy()
        for i in range(10):
            self.main.grid_rowconfigure(i, weight=0)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

    def _title(self, text):
        ctk.CTkLabel(
            self.main, text=text,
            font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))

    # ── Screen 1 — My Wardrobe ────────────────────────────────────────────────
    def show_wardrobe(self):
        self._clear()
        self._title("My Wardrobe")

        if not clothes:
            ctk.CTkLabel(
                self.main, text="Your wardrobe is empty — add your first item!",
                text_color=MUTED, font=ctk.CTkFont(size=16)
            ).grid(row=1, column=0)
            return

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        for i in range(4):
            scroll.grid_columnconfigure(i, weight=1)

        for idx, cloth in enumerate(clothes):
            self._cloth_card(scroll, cloth, idx // 4, idx % 4)

    def _cloth_card(self, parent, cloth, row, col):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=14)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk_img = load_ctk_image(cloth["image_path"], size=(160, 160))
        if ctk_img:
            ctk.CTkLabel(card, image=ctk_img, text="").grid(row=0, column=0, pady=(14, 8))
        else:
            ctk.CTkLabel(
                card, text="No Image", width=160, height=160,
                fg_color=SURFACE, text_color=MUTED
            ).grid(row=0, column=0, pady=(14, 8))

        ctk.CTkLabel(
            card, text=cloth["desc"].title(),
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=145, text_color=TEXT
        ).grid(row=1, column=0, padx=10)

        colour = SUCCESS if cloth["available"] else DANGER
        label  = "Available" if cloth["available"] else "Needs Wash"
        ctk.CTkLabel(card, text=label, text_color=colour, font=ctk.CTkFont(size=12)).grid(row=2, column=0, pady=2)

        ctk.CTkLabel(
            card, text=f"Worn {cloth['wear_count']}/{cloth['max_wears']}×",
            text_color=MUTED, font=ctk.CTkFont(size=11)
        ).grid(row=3, column=0, pady=(0, 8))

        ctk.CTkButton(
            card, text="Remove", fg_color=DANGER, hover_color="#a71d2a",
            width=110, height=28,
            command=lambda cid=cloth["cloth_id"]: self._delete(cid)
        ).grid(row=4, column=0, pady=(0, 14))

    def _delete(self, cloth_id):
        delete_cloth(clothes, cloth_id)
        self.show_wardrobe()

    # ── Screen 2 — Add Item ───────────────────────────────────────────────────
    def show_add_item(self):
        self._clear()
        self._title("Add New Item")
        self.selected_image_path = None

        form = ctk.CTkFrame(self.main, fg_color="transparent")
        form.grid(row=1, column=0, sticky="nw")

        self._img_btn = ctk.CTkButton(
            form, text="+ Click to pick image",
            width=200, height=200, fg_color=CARD,
            hover_color=SURFACE, border_width=2, border_color=MUTED,
            command=self._pick_image
        )
        self._img_btn.grid(row=0, column=0, rowspan=5, padx=(0, 32), pady=4)

        for r, (lbl, attr, ph, default) in enumerate([
            ("Description",           "_desc_entry", "e.g. white linen shirt", ""),
            ("Max wears before wash", "_maxw_entry", "Default: 1",             "1"),
        ]):
            ctk.CTkLabel(form, text=lbl, text_color=MUTED).grid(row=r*2, column=1, sticky="w", pady=(10, 0))
            e = ctk.CTkEntry(form, width=260, placeholder_text=ph)
            if default:
                e.insert(0, default)
            e.grid(row=r*2+1, column=1, sticky="w", pady=(4, 12))
            setattr(self, attr, e)

        self._add_msg = ctk.CTkLabel(form, text="", text_color=SUCCESS)
        self._add_msg.grid(row=4, column=1, sticky="w")

        ctk.CTkButton(
            form, text="Add to Wardrobe",
            fg_color=ACCENT, hover_color="#5a52d5",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_item
        ).grid(row=5, column=1, sticky="w", pady=16)

    def _pick_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.bmp")]
        )
        if not path:
            return
        self.selected_image_path = path
        img = Image.open(path)
        img.thumbnail((180, 180))
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._img_btn.configure(image=ctk_img, text="")

    def _save_item(self):
        desc = self._desc_entry.get().strip().lower()
        max_wears_raw = self._maxw_entry.get().strip() or "1"

        if not desc:
            self._add_msg.configure(text="Please enter a description.", text_color=DANGER)
            return
        if not self.selected_image_path:
            self._add_msg.configure(text="Please select an image.", text_color=DANGER)
            return
        try:
            max_wears = int(max_wears_raw)
        except ValueError:
            self._add_msg.configure(text="Max wears must be a number.", text_color=DANGER)
            return

        add_cloth(clothes, self.selected_image_path, desc, max_wears, wardrobe_dir=str(WARDROBE_DIR))

        self._add_msg.configure(text=f"'{desc}' added!", text_color=SUCCESS)
        self.selected_image_path = None
        self._img_btn.configure(image=None, text="+ Click to pick image")
        self._desc_entry.delete(0, "end")
        self._maxw_entry.delete(0, "end")
        self._maxw_entry.insert(0, "1")

    # ── Screen 3 — Log Wear ───────────────────────────────────────────────────
    def show_log_wear(self):
        self._clear()
        self._title("Log Wear")

        top = ctk.CTkFrame(self.main, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top, text="Log Wear",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=TEXT
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self._search_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            top, textvariable=self._search_var,
            width=420, placeholder_text="Describe the item you wore today..."
        )
        entry.grid(row=1, column=0, sticky="w", padx=(0, 12))
        entry.bind("<Return>", lambda e: self._run_search())

        ctk.CTkButton(
            top, text="Search", fg_color=ACCENT,
            command=self._run_search, width=100
        ).grid(row=1, column=1, sticky="w")

        self._log_scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self._log_scroll.grid(row=1, column=0, sticky="nsew")
        for i in range(4):
            self._log_scroll.grid_columnconfigure(i, weight=1)

        self._log_msg = ctk.CTkLabel(self.main, text="", text_color=SUCCESS, font=ctk.CTkFont(size=14))
        self._log_msg.grid(row=2, column=0, pady=8)

        self._render_log_cards([c for c in clothes if c["available"]])

    def _run_search(self):
        query = self._search_var.get().strip().lower()
        if not query:
            self._render_log_cards([c for c in clothes if c["available"]])
            return
        keywords = query.split()
        hits     = search_clothes(clothes, keywords)
        hit_ids  = {h[0] for h in hits}
        filtered = [c for c in clothes if c["cloth_id"] in hit_ids]
        self._render_log_cards([c for c in filtered if c["available"]])

    def _render_log_cards(self, items):
        for w in self._log_scroll.winfo_children():
            w.destroy()

        if not items:
            ctk.CTkLabel(self._log_scroll, text="No items found.", text_color=MUTED).grid(row=0, column=0, columnspan=4, pady=20)
            return

        for idx, cloth in enumerate(items):
            card = ctk.CTkFrame(self._log_scroll, fg_color=CARD, corner_radius=12)
            card.grid(row=idx // 4, column=idx % 4, padx=10, pady=10, sticky="nsew")

            ctk_img = load_ctk_image(cloth["image_path"], size=(120, 120))
            if ctk_img:
                ctk.CTkLabel(card, image=ctk_img, text="").pack(pady=(12, 4))

            ctk.CTkLabel(card, text=cloth["desc"].title(), font=ctk.CTkFont(weight="bold"), text_color=TEXT).pack(pady=4)

        
            ctk.CTkButton(
                card, text="I Wore This", fg_color=ACCENT,
                command=lambda cid=cloth["cloth_id"]: self._log_wear(cid)
            ).pack(pady=(0, 14), padx=14)
        

    def _log_wear(self, cloth_id):
        msg = update_wear(clothes, cloth_id)
        self._log_msg.configure(text=msg)
        self._run_search()

    # ── Screen 4 — Get Outfit ─────────────────────────────────────────────────
    def show_get_outfit(self):
        self._clear()
        self._title("Get Outfit Suggestion")

        ctk.CTkLabel(
            self.main, text="Describe your vibe, event, or mood:",
            text_color=MUTED, font=ctk.CTkFont(size=15)
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        self._vibe_entry = ctk.CTkEntry(
            self.main, width=520,
            placeholder_text="e.g. smart casual coffee date, relaxed sunday at home..."
        )
        self._vibe_entry.grid(row=2, column=0, sticky="w", pady=(0, 14))
        self._vibe_entry.bind("<Return>", lambda e: self._fetch_outfit())

        self._outfit_btn = ctk.CTkButton(
            self.main, text="Get Outfit",
            fg_color=ACCENT, hover_color="#5a52d5",
            font=ctk.CTkFont(weight="bold"),
            command=self._fetch_outfit
        )
        self._outfit_btn.grid(row=3, column=0, sticky="w", pady=(0, 20))
        self._outfit_box = HtmlFrame(self.main, width=700, height=340)
        self._outfit_box.grid(row=4, column=0, sticky="w")
        if self._last_outfit:
            self._outfit_box.load_html(markdown.markdown(self._last_outfit))
        else:
            self._outfit_box.load_html("<p style='color:gray'>Your suggestion will appear here...</p>")

    def _fetch_outfit(self):
        vibe = self._vibe_entry.get().strip()
        if not vibe:
            self._write_outfit("Please describe a vibe or event first.")
            return

        self._write_outfit("Consulting Gemini... please wait ✨")
        self._outfit_btn.configure(state="disabled")
        threading.Thread(target=self._call_gemini, args=(vibe,), daemon=True).start()

    def _call_gemini(self, vibe):
        try:
            result = get_outfit_prompt(clothes, vibe)
            self.after(0, lambda: self._write_outfit(result))
        except Exception as e:
            self.after(0, lambda: self._write_outfit(f"Error: {e}"))
        finally:
            self.after(0, lambda: self._outfit_btn.configure(state="normal"))

    def _write_outfit(self, text):
        html = markdown.markdown(text)
        self._last_outfit = text
        self._outfit_box.load_html(html)


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = DrobeApp()
    app.mainloop()