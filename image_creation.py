from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
from io import BytesIO

class RewindExportProfil:
    def __init__(self, player_name: str, champion_played: str, kd: int, lvl: int, storie: str):
        self.name = player_name
        self.champion_played = champion_played
        self.kd = kd
        self.lvl = lvl
        self.storie = storie

# class RewindGeneration:
#     image = None
#     draw = None
#     width = None
#     height = None
#     font = None
#
#     def __init__(self, profil: RewindExportProfil):
#         self.profil = profil
#
#     def create_image(self, width: int, height: int):
#         self.width = width
#         self.height = height
#         self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
#         self.draw = ImageDraw.Draw(self.image)
#
#     def is_drawable(self) -> bool:
#         if self.image and self.draw:
#             return True
#         return False
#
#     def load_font(self, size: int):
#         try:
#             self.font = ImageFont.truetype("arial.ttf", size)
#         except:
#             self.font = ImageFont.load_default()
#
#     def draw_tittle(self, title: str):
#         if not self.draw or not self.font:
#             raise ValueError(
#             "Image or font not initialized. Call create_image() and load_font() first.")
#
#         bbox = self.draw.textbbox((0, 0), title, font=self.font)
#         text_width = bbox[2] - bbox[0]
#         x = (self.width - text_width) // 2
#         y = 200
#         self.draw.text((x, y), title, fill=(255, 215, 0, 255), font=self.font)
#
#     def save_image_to_png(self, filename: str):
#         if not self.image:
#             raise ValueError("No image to save.")
#         self.image.save(filename, 'PNG')
#
#     def image_creation(self) -> bool:
#         # gen image
#         self.create_image(1080, 1920)
#         if self.is_drawable():
#             self.load_font(120)
#             self.draw_tittle("My LOL rewind 2025")
#             self.save_image_to_png(f"{self.profil.name}_rewind_2025.png")
#         else:
#             print("Error: image not drawable.")
#             return False
#         return True

class RewindGeneration:
    def __init__(self, profil: RewindExportProfil):
        self.profil = profil
        self.image = None
        self.overlay = None
        self.draw = None
        self.width = None
        self.height = None
        self.fonts = {}
    
    def create_image(self, width: int = 1080, height: int = 1920, background_color=(0, 0, 0, 0)):
        self.width = width
        self.height = height
        self.image = Image.new('RGBA', (width, height), background_color)
        self.overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.overlay)
        return self
    
    def load_background(self, source):
        if isinstance(source, tuple):
            self.image = Image.new('RGB', (self.width, self.height), source)
        elif source.startswith('http'):
            response = urlopen(source)
            self.image = Image.open(BytesIO(response.read()))
        else:
            self.image = Image.open(source)
        
        self.image = self.image.resize((self.width, self.height), Image.Resampling.LANCZOS)
        self.image = self.image.convert('RGBA')
        return self
    
    def add_dark_overlay(self, opacity=128):
        dark = Image.new('RGBA', (self.width, self.height), (0, 0, 0, opacity))
        self.image = Image.alpha_composite(self.image, dark)
        return self
    
    def is_drawable(self) -> bool:
        return self.image is not None and self.draw is not None
    
    def load_font(self, name: str, size: int, font_path: str = "arial.ttf"):
        try:
            self.fonts[name] = ImageFont.truetype(font_path, size)
        except:
            self.fonts[name] = ImageFont.load_default()
        return self
    
    def load_fonts_preset(self):
        self.load_font('mega', 200)
        self.load_font('title', 170)
        self.load_font('large', 140)
        self.load_font('normal', 130)
        self.load_font('small', 100)
        self.load_font('tiny', 75)
        return self
    
    def draw_text(self, text: str, x: int, y: int, font_name: str = 'normal', 
                  color=(255, 255, 255, 255), align='left', anchor=None):
        if not self.is_drawable():
            raise ValueError("Image not init. Call create_image() first")
        font = self.fonts.get(font_name)
        if not font:
            raise ValueError(f"Font '{font_name}' not load. Call load_font() d'abord.")
        
        if align == 'center' or x == 'center':
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
        elif align == 'right':
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = x - text_width

        self.draw.text((x, y), text, fill=color, font=font, anchor=anchor)
        return self
    
    def draw_centered_text(self, text: str, y: int, font_name: str = 'normal', 
                          color=(255, 255, 255, 255)):
        return self.draw_text(text, 0, y, font_name, color, align='center')
    
    def draw_rectangle(self, x1: int, y1: int, x2: int, y2: int, 
                      fill=(0, 0, 0, 128), outline=None, width=0):
        if not self.is_drawable():
            raise ValueError("Image not init")
        self.draw.rectangle([x1, y1, x2, y2], fill=fill, outline=outline, width=width)
        return self
    
    def draw_rounded_rectangle(self, x1: int, y1: int, x2: int, y2: int, 
                              radius: int = 20, fill=(0, 0, 0, 128), outline=None, width=0):
        if not self.is_drawable():
            raise ValueError("Image not init")
        self.draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, 
                                    fill=fill, outline=outline, width=width)
        return self
    
    def add_image(self, image_source, x: int, y: int, width: int = None, height: int = None):
        if isinstance(image_source, str):
            if image_source.startswith('http'):
                response = urlopen(image_source)
                img = Image.open(BytesIO(response.read()))
            else:
                img = Image.open(image_source)
        else:
            img = image_source
        
        if width or height:
            if width and height:
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            elif width:
                ratio = width / img.width
                img = img.resize((width, int(img.height * ratio)), Image.Resampling.LANCZOS)
            else:
                ratio = height / img.height
                img = img.resize((int(img.width * ratio), height), Image.Resampling.LANCZOS)
        
        img = img.convert('RGBA')
        self.overlay.paste(img, (x, y), img)
        return self
    
    def merge_layers(self):
        if self.image and self.overlay:
            self.image = Image.alpha_composite(self.image, self.overlay)
        return self
    
    def save(self, filename: str):
        if not self.image:
            raise ValueError("No image to save")
        
        self.merge_layers()
        self.image.save(filename, 'PNG')
        return self
    
    def image_creation(self) -> bool:
        try:
            self.create_image(1080, 1920)
            
            self.load_background((15, 25, 40)) # blue
            
            # Option 2 : Img
            # self.load_background("https://example.com/lol-background.jpg")
            # self.add_dark_overlay(180)  # Assombrir pour mieux voir le texte
            
            self.load_fonts_preset()
            self.draw_centered_text("MY LOL", 120, 'mega', (255, 215, 0, 255))
            self.draw_centered_text("REWIND 2025", 320, 'title', (255, 215, 0, 255))
            self.draw_rectangle(200, 480, 880, 490, fill=(255, 215, 0, 200))
            self.draw_centered_text(f"{self.profil.name}", 580, 'title', (255, 255, 255, 255))
            y_start = 780
            spacing = 180
            self.draw_text(f"Champion plyed", 120, y_start, 'small', (150, 150, 150, 255))
            self.draw_text(f"{self.profil.champion_played}", 120, y_start + 70, 'large', (255, 200, 100, 255))
            self.draw_text(f"K/D Ratio", 120, y_start + spacing, 'small', (150, 150, 150, 255))
            self.draw_text(f"{self.profil.kd}", 120, y_start + spacing + 70, 'large', (150, 255, 150, 255))
            self.draw_text(f"Lvl reached", 120, y_start + spacing * 2, 'small', (150, 150, 150, 255))
            self.draw_text(f"{self.profil.lvl}", 120, y_start + spacing * 2 + 70, 'large', (150, 200, 255, 255))
            story_y = 1480
            self.draw_rounded_rectangle(60, story_y, 1020, story_y + 360, radius=40, fill=(0, 0, 0, 200))
            self.draw_text("You stroy ✨:", 100, story_y + 50, 'normal', (255, 215, 0, 255))
            self.draw_text(self.profil.storie, 100, story_y + 160, 'small', (230, 230, 230, 255))
            
            self.save(f"{self.profil.name}_rewind_2025.png")
            return True
            
        except Exception as e:
            print(f"Error : {e}")
            return False

def main():
    print("Try to create png image")
    profil = RewindExportProfil("titi", "idkfornow", 1, 12, "titi look's good today")
    rewind = RewindGeneration(profil)
    rewind.image_creation()

if __name__=="__main__":
    main()
