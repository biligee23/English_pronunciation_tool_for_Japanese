import tkinter as tk
from tkinter import font
import queue
from eng_to_ipa import convert as english_to_ipa

class KatakanaOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.configure(bg="black")
        self.root.geometry(self._calculate_position())
        self.root.attributes("-transparentcolor", "black")

        # Create a queue for thread-safe updates
        self.text_queue = queue.Queue()

        # Create two frames - input at bottom, display above
        self.display_frame = tk.Frame(self.root, bg="black", height=100)
        self.display_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.input_frame = tk.Frame(self.root, bg="black", height=50)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Fonts
        self.display_font = font.Font(family="Arial", size=24, weight="bold")
        self.input_font = font.Font(family="Arial", size=18)

        # Display Label with shadow
        self.display_label_shadow = tk.Label(
            self.display_frame,
            text="",
            font=self.display_font,
            fg="black",
            bg="black",
            wraplength=780,
            justify="center"
        )
        self.display_label_shadow.place(relx=0.5, rely=0.5, anchor="center", x=2, y=2)

        self.display_label = tk.Label(
            self.display_frame,
            text="",
            font=self.display_font,
            fg="white",
            bg="black",
            wraplength=780,
            justify="center"
        )
        self.display_label.place(relx=0.5, rely=0.5, anchor="center")

        # Input Entry - more visible and selectable
        self.input_entry = tk.Entry(
            self.input_frame,
            font=self.input_font,
            bg="white",  # Lighter background for contrast
            fg="black",  # Black text for visibility
            insertbackground="black",  # Change cursor to black
            borderwidth=2,  # Thicker border
            highlightthickness=2,  # Visible highlight when focused
            highlightbackground="blue",  # Blue border when focused
            relief="solid",  # Solid border
        )
        self.input_entry.pack(pady=10, padx=20, fill=tk.X)
        self.input_entry.focus_set()

        # Start update loop
        self.root.after(100, self.update_overlay)

        # Bind mouse click event to allow focus back on the input
        self.input_entry.bind("<FocusIn>", self.focus_input)

    def _calculate_position(self):
        """Position window at bottom of screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 800
        window_height = 150
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 50
        return f"{window_width}x{window_height}+{x}+{y}"

    def update_overlay(self):
        """Update display from queue"""
        try:
            while not self.text_queue.empty():
                text = self.text_queue.get_nowait()
                self.display_label.config(text=text)
                self.display_label_shadow.config(text=text)
        except queue.Empty:
            pass
        # Keep updating the display at regular intervals
        self.root.after(100, self.update_overlay)

    def focus_input(self, event):
        """Ensure the input entry can be focused again after clicking"""
        self.input_entry.focus_set()

    def start(self):
        self.root.mainloop()

class KatakanaEngine:
    def __init__(self):
        self.IPA_RULES = {
            # Vowels
            "i": "イ", "ɪ": "イ", 
            "e": "エ", "ɛ": "エ",
            "æ": "ア", 
            "ɒ": "オ", "ɔ": "オ",
            "ʊ": "ウ", "u": "ウ",
            "ʌ": "ア", "ə": "ア",
            "ɝ": "アー",
            
            # Diphthongs
            "eɪ": "エイ", "aɪ": "アイ", 
            "ɔɪ": "オイ", "əʊ": "オウ",
            "aʊ": "アウ", "ɪə": "イア",
            "ɛə": "エア", "ʊə": "ウア",
            
            # Consonants
            "p": "プ", "b": "ブ",
            "t": "ト", "d": "ド",
            "k": "ク", "g": "グ",
            "m": "ム", "n": "ン",
            "ŋ": "ング", "f": "フ",
            "v": "ヴ", "θ": "シ", 
            "ð": "ズ", "s": "ス",
            "z": "ズ", "ʃ": "シャ",
            "ʒ": "ジャ", "h": "ハ",
            "ʧ": "チャ", "ʤ": "ジャ",
            "l": "ル", "r": "ラ",
            "j": "ヤ", "w": "ワ",
            
            # Special combinations
            "tʃ": "チャ", "dʒ": "ジャ",
            "ts": "ツ", "dz": "ズ",
        }
        
        # Contextual rules
        self.CONTEXT_RULES = {
            # æ after k -> キャ
            "kæ": "キャ",
            # final schwa -> アー
            "ə$": "アー",
            # gemination patterns
            "([bcdfghjklmnpqrstvwxyz])\\1": "ッ",
            # ti/di -> ティ/ディ
            "ti": "ティ", "di": "ディ",
            # tu/du -> トゥ/ドゥ
            "tu": "トゥ", "du": "ドゥ",
        }

    def transliterate(self, text):
        ipa_text = english_to_ipa(text).replace("ˈ", "").replace("ˌ", "")
        katakana = []
        i = 0
        
        while i < len(ipa_text):
            # Apply contextual rules first
            if i > 0 and ipa_text[i-1] == 'k' and ipa_text[i] == 'æ':
                katakana[-1] = "キャ"
                i += 1
                continue
                
            # Check for 2-3 character sequences
            if i+2 < len(ipa_text) and ipa_text[i:i+3] in self.IPA_RULES:
                katakana.append(self.IPA_RULES[ipa_text[i:i+3]])
                i += 3
            elif i+1 < len(ipa_text) and ipa_text[i:i+2] in self.IPA_RULES:
                # Handle special consonant clusters
                if ipa_text[i:i+2] == "dz":
                    katakana.append("ッズ")
                    i += 2
                    continue
                katakana.append(self.IPA_RULES[ipa_text[i:i+2]])
                i += 2
            else:
                # Handle single characters
                char = ipa_text[i]
                # Check gemination
                if i > 0 and char == ipa_text[i-1] and char in "bcdfghjklmnpqrstvwxyz":
                    katakana.append("ッ")
                # Apply normal rules
                if char in self.IPA_RULES:
                    katakana.append(self.IPA_RULES[char])
                else:
                    katakana.append("・")
                i += 1
        
        # Final processing
        result = "".join(katakana)
        # Handle final schwa
        if result.endswith("ア"):
            result = result[:-1] + "アー"
        return result

# Connect everything together (same as before)
if __name__ == "__main__":
    overlay = KatakanaOverlay()
    engine = KatakanaEngine()
    
    def on_input_change(event):
        text = event.widget.get()
        katakana = engine.transliterate(text)
        overlay.text_queue.put(katakana)
    
    overlay.input_entry.bind("<KeyRelease>", on_input_change)
    overlay.start()