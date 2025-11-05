from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
from io import BytesIO
import aiohttp, asyncio

class RewindExportProfil:
    def __init__(self, player_name: str, champion_played: str, games_played: int, kd: float, lvl: int, story: str):
        self.name = player_name
        self.champion_played = champion_played
        self.games_played = games_played
        self.kd = kd
        self.lvl = lvl
        self.story = story

class RewindGeneration:
    def __init__(self, profil: RewindExportProfil):
        self.profil = profil
        self.image = None
        self.overlay = None
        self.draw = None
        self.width = None
        self.height = None
        self.fonts = {}
    
    async def get_champion_images(self) -> dict[str, str]:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ddragon.leagueoflegends.com/api/versions.json") as resp:
                versions = await resp.json()
                latest_version = versions[0]

            async with session.get(f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json") as resp:
                data = await resp.json()
                champions = data["data"]

            splash_urls = {
                champ_info["id"]: f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{champ_info['id']}_0.jpg"
                for champ_info in champions.values()
            }

        return splash_urls

    def create_image(self, width: int = 1920, height: int = 1080, background_color=(0, 0, 0, 0)):
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
    
    def add_gradient_overlay(self, opacity_start=80, opacity_end=160, side='left'):
        gradient = Image.new('RGBA', (self.width, self.height))
        draw = ImageDraw.Draw(gradient)
        
        if side == 'left':
            for x in range(self.width):
                ratio = x / self.width
                opacity = int(opacity_start * (1 - ratio) + opacity_end * ratio)
                draw.line([(x, 0), (x, self.height)], fill=(5, 10, 25, opacity))
        else:
            for y in range(self.height):
                ratio = y / self.height
                opacity = int(opacity_start * (1 - ratio) + opacity_end * ratio)
                draw.line([(0, y), (self.width, y)], fill=(5, 10, 25, opacity))
        
        self.image = Image.alpha_composite(self.image, gradient)
        return self
    
    def add_vignette(self, strength=100):
        vignette = Image.new('RGBA', (self.width, self.height))
        draw = ImageDraw.Draw(vignette)
        
        center_x, center_y = self.width // 2, self.height // 2
        max_dist = ((center_x ** 2 + center_y ** 2) ** 0.5)
        
        for y in range(self.height):
            for x in range(0, self.width, 5):
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                ratio = min(dist / max_dist, 1.0)
                opacity = int(ratio * strength)
                draw.line([(x, y), (x + 5, y)], fill=(0, 0, 0, opacity))
        
        self.image = Image.alpha_composite(self.image, vignette)
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
        self.load_font('mega', 160)
        self.load_font('title', 110)
        self.load_font('large', 85)
        self.load_font('normal', 70)
        self.load_font('small', 55)
        self.load_font('tiny', 42)
        return self
    
    def draw_text(self, text: str, x: int, y: int, font_name: str = 'normal', 
                  color=(255, 255, 255, 255), align='left', anchor=None, stroke_width=0, stroke_fill=None):
        if not self.is_drawable():
            raise ValueError("Image not init. Call create_image() first")
        font = self.fonts.get(font_name)
        if not font:
            raise ValueError(f"Font '{font_name}' not load. Call load_font() first.")
        
        if align == 'center' or x == 'center':
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = (self.width - text_width) // 2
        elif align == 'right':
            bbox = self.draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x = x - text_width

        self.draw.text((x, y), text, fill=color, font=font, anchor=anchor, 
                      stroke_width=stroke_width, stroke_fill=stroke_fill)
        return self
    
    def draw_centered_text(self, text: str, y: int, font_name: str = 'normal', 
                          color=(255, 255, 255, 255), stroke_width=0, stroke_fill=None):
        return self.draw_text(text, 0, y, font_name, color, align='center', 
                            stroke_width=stroke_width, stroke_fill=stroke_fill)
    
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
    
    def draw_stat_card(self, x: int, y: int, width: int, height: int, 
                      label: str, value: str, accent_color=(255, 215, 0)):
        self.draw_rounded_rectangle(x, y, x + width, y + height, radius=25, 
                                    fill=(10, 15, 30, 200))
        
        self.draw_rounded_rectangle(x, y, x + width, y + 10, radius=25, 
                                    fill=(*accent_color, 255))
        
        self.draw_text(label, x + 30, y + 40, 'small', (180, 180, 180, 255))
        
        self.draw_text(value, x + 30, y + 100, 'large', accent_color + (255,), 
                      stroke_width=2, stroke_fill=(0, 0, 0, 255))
        
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
    
    async def image_creation_async(self) -> bool:
        try:
            champion_images = await self.get_champion_images()
            champion_url = champion_images.get(self.profil.champion_played)
            
            self.create_image(1920, 1080)
            
            if champion_url:
                self.load_background(champion_url)
                self.add_gradient_overlay(opacity_start=120, opacity_end=30, side='left')
                self.add_vignette(strength=80)
            else:
                self.load_background((15, 25, 40))
            
            self.load_fonts_preset()
            
            self.draw_text("YOUR 2025", 70, 50, 'large', (255, 215, 0, 255), 
                          stroke_width=4, stroke_fill=(0, 0, 0, 255))
            self.draw_text("LOL REWIND", 70, 150, 'mega', (255, 215, 0, 255),
                          stroke_width=5, stroke_fill=(0, 0, 0, 255))
            
            self.draw_rounded_rectangle(60, 330, 700, 460, radius=30, fill=(10, 15, 30, 220))
            self.draw_text(f"{self.profil.name}", 90, 360, 'title', (255, 255, 255, 255),
                          stroke_width=3, stroke_fill=(0, 0, 0, 200))
            
            champ_y = 490
            self.draw_rounded_rectangle(60, champ_y, 700, champ_y + 140, radius=30, fill=(30, 20, 50, 220))
            self.draw_text("FAVORITE CHAMPION", 90, champ_y + 25, 'small', (255, 215, 0, 255))
            self.draw_text(f"{self.profil.champion_played}", 90, champ_y + 75, 'title', (255, 255, 255, 255),
                          stroke_width=3, stroke_fill=(0, 0, 0, 200))
            
            stats_y = 670
            card_width = 260
            card_height = 200
            spacing = 50
            start_x = 60
            
            self.draw_stat_card(start_x, stats_y, card_width, card_height, 
                              "GAMES PLAYED", f"{self.profil.games_played}", (100, 200, 255))
            
            self.draw_stat_card(start_x + card_width + spacing, stats_y, card_width, card_height,
                              "K/D RATIO", f"{self.profil.kd}", (150, 255, 150))
            
            self.draw_stat_card(start_x + (card_width + spacing) * 2, stats_y, card_width, card_height,
                              "LEVEL", f"{self.profil.lvl}", (255, 150, 150))
            
            story_y = 910
            self.draw_rounded_rectangle(60, story_y, 900, story_y + 130, radius=30, fill=(10, 15, 30, 220))
            self.draw_text("YOUR STORY", 90, story_y + 25, 'small', (255, 215, 0, 255))
            self.draw_text(self.profil.story, 90, story_y + 75, 'tiny', (230, 230, 230, 255))
            
            self.draw_text("League of Legends © Riot Games", self.width - 450, self.height - 50, 
                          'tiny', (150, 150, 150, 180))
            
            self.save(f"{self.profil.name}_rewind_2025.png")
            print(f"Image created: {self.profil.name}_rewind_2025.png (1920x1080)")
            return True

        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def image_creation(self) -> bool:
        return asyncio.run(self.image_creation_async())

def main():
    print("Generating LOL Rewind ...")
    profil = RewindExportProfil(
        player_name="Faker", 
        champion_played="Ahri", 
        games_played=342,
        kd=4.2, 
        lvl=287, 
        story="The legend continues with style and precision."
    )
    rewind = RewindGeneration(profil)
    rewind.image_creation()

if __name__=="__main__":
    main()
