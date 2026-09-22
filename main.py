import pathlib
import json
import shutil
import os
from operator import itemgetter
from dotenv import load_dotenv
from google import genai
import datetime

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Clothing Class ────────────────────────────────────────────────────────────
class Clothing:
    def __init__(self, cloth_id, image_path, ironed=0, location="Home", desc="", max_wears=1):
        self.cloth_id = cloth_id
        self.available = True
        self.desc = desc
        self.wear_count = 0
        self.image_path = image_path
        self.max_wears = max_wears
        self.ironed = ironed
        self.location = location

    def to_class_object(self, dictionary):
        for key, value in dictionary.items():
            setattr(self, key, value)
        return self


# ── Pure Logic Functions (no input/print) ─────────────────────────────────────

def save_clothes(clothes):
    pathlib.Path('clothes.json').write_text(json.dumps(clothes))

def mark_clean(clothes, cloth_id):
    """Reset wear count and mark item as available again."""
    for cloth in clothes:
        if cloth["cloth_id"] == cloth_id:
            cloth["wear_count"] = 0
            cloth["available"] = True
            break
    save_clothes(clothes)

def add_cloth(clothes, image_src_path, desc, max_wears=1, wardrobe_dir="wardrobe"):
    """Add a single clothing item. Copies image, creates Clothing object, saves."""
    pathlib.Path(wardrobe_dir).mkdir(exist_ok=True)
    ext = pathlib.Path(image_src_path).suffix
    filename = desc.replace(' ', '_') + ext

    # Handle duplicate filenames
    dest = pathlib.Path(wardrobe_dir) / filename
    stem, n = pathlib.Path(filename).stem, 1
    while dest.exists():
        filename = f"{stem}_{n}{ext}"
        dest = pathlib.Path(wardrobe_dir) / filename
        n += 1

    shutil.copyfile(image_src_path, dest)

    new_id = max((c["cloth_id"] for c in clothes), default=0) + 1
    cloth = Clothing(cloth_id=new_id, image_path=filename, desc=desc.lower(), max_wears=max_wears).__dict__
    clothes.append(cloth)
    save_clothes(clothes)
    return cloth

def log_to_history(cloth):
    history_file = pathlib.Path('history.json')
    if history_file.exists():
        history = json.loads(history_file.read_text())
    else:
        history = []
    
    entry = {
        "cloth_id": cloth["cloth_id"],
        "desc": cloth["desc"],
        "date": datetime.date.today().strftime("%d %b %Y")
    }
    history.append(entry)
    history_file.write_text(json.dumps(history))


def search_clothes(clothes, keywords):
    """Returns sorted list of (cloth_id, score, desc) tuples. No printing."""
    results = []
    for cloth in clothes:
        score = sum(1 for k in keywords if k in cloth["desc"])
        if score > 0:
            results.append((cloth["cloth_id"], score, cloth["desc"]))
    return sorted(results, key=itemgetter(1), reverse=True)


def update_wear(clothes, cloth_id):
    """Increment wear count for a cloth, flip available if needed. Returns status message."""
    for cloth in clothes:
        if cloth["cloth_id"] == cloth_id:
            cloth["wear_count"] += 1
            log_to_history(cloth)
            if cloth["wear_count"] >= cloth["max_wears"]:
                cloth["available"] = False
                msg = f"'{cloth['desc']}' marked as needs wash."
            else:
                remaining = cloth["max_wears"] - cloth["wear_count"]
                msg = f"Logged! {remaining} wear(s) remaining before washing."
            save_clothes(clothes)
            return msg
    return "Item not found."


def delete_cloth(clothes, cloth_id):
    """Remove a clothing item by ID and save."""
    clothes[:] = [c for c in clothes if c["cloth_id"] != cloth_id]
    save_clothes(clothes)


def get_outfit_prompt(clothes, vibe):
    """Build prompt and call Gemini. Returns response text."""
    available = [
        {"cloth_id": c["cloth_id"], "description": c["desc"]}
        for c in clothes if c["available"]
    ]
    if not available:
        return "No available clothes right now. Mark some items as clean first!"

    prompt = (
        f"This is my wardrobe (available items only): {available}.\n"
        f"Help me pick an outfit for the following vibe/event: {vibe}.\n"
        "Be specific about which items to combine and why. Reference items by their description."
    )
    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(model="gemini-3.6-flash", input=prompt)
    return interaction.output_text


# ── Load Wardrobe ─────────────────────────────────────────────────────────────
file = pathlib.Path('clothes.json')
if file.exists():
    clothes = json.loads(file.read_text())
else:
    clothes = []


# ── Terminal Interface (only runs if executed directly) ───────────────────────
def _terminal_add(clothes):
    from tkinter import Tk, filedialog
    from rich.markdown import Markdown
    from rich import print as rprint
    while True:
        Tk().withdraw()
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif *.webp")]
        )
        desc = input("Description of item: ").lower()
        max_wears = input("Max wears before washing (press Enter for 1): ") or "1"
        add_cloth(clothes, path, desc, int(max_wears))
        again = input("Add another? (y/n): ").strip().lower()
        if again != "y":
            print("Saved!")
            break


def _terminal_search(clothes):
    keywords = input("Search: ").lower().split()
    results = search_clothes(clothes, keywords)
    print("\n--- Search Results ---")
    for cloth_id, score, desc in results:
        print(f"  ID {cloth_id}: {desc}  (matched {score} keyword(s))")
    print("----------------------\n")
    return results


def _terminal_log_wear(clothes):
    results = _terminal_search(clothes)
    if not results:
        print("No matching items found.")
        return
    choice = int(input("Enter the cloth ID you wore: "))
    print(update_wear(clothes, choice))


def _terminal_remove(clothes):
    for cloth in clothes:
        status = "available" if cloth["available"] else "needs wash"
        print(f"  ID {cloth['cloth_id']}: {cloth['desc']}  [{status}]")
    removal = int(input("Enter the ID to remove: "))
    delete_cloth(clothes, removal)
    print("Item removed.")


def _terminal_print(clothes):
    if not clothes:
        print("Your wardrobe is empty.")
        return
    print("\n--- Your Wardrobe ---")
    for cloth in clothes:
        status = "✓ available" if cloth["available"] else "✗ needs wash"
        print(f"  ID {cloth['cloth_id']:>3} | {cloth['desc']:<30} | wears: {cloth['wear_count']}/{cloth['max_wears']} | {status}")
    print("---------------------\n")


def main():
    from rich.markdown import Markdown
    from rich import print as rprint

    print(f"Wardrobe loaded: {len(clothes)} item(s).\n")
    if not clothes:
        print("No wardrobe found. Let's add your first items!\n")
        _terminal_add(clothes)

    MENU = """
What would you like to do?
  1) Add items
  2) Remove an item
  3) View wardrobe
  4) Log a wear
  5) Get suggestion
  6) Exit
Choice: """

    while True:
        choice = input(MENU).strip()
        if choice == "1":
            _terminal_add(clothes)
        elif choice == "2":
            _terminal_remove(clothes)
        elif choice == "3":
            _terminal_print(clothes)
        elif choice == "4":
            _terminal_log_wear(clothes)
        elif choice == "5":
            vibe = input("Describe your vibe/event: ")
            rprint(Markdown(get_outfit_prompt(clothes, vibe)))
        elif choice == "6":
            print("See you later!")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()