from PIL import Image, ImageDraw, ImageFont
from urllib.request import urlopen
from io import BytesIO
import aiohttp, asyncio

class RewindExportProfil:
    def __init__(self, player_name: str, champion_played: str, games_played: int, kd: float, lvl: int, rank: str, title: str, story: str):
        self.name = player_name
        self.champion_played = champion_played
        self.games_played = games_played
        self.kd = kd
        self.lvl = lvl
        self.rank = rank
        self.title = title
        self.story = story

class RewindCardGeneration:
    def __init__(self, profil: RewindExportProfil):
        self.profil = profil
        self.image = None
        self.draw = None
        self.width = 356
        self.height = 591
        self.fonts = {}
        self.base_url = "https://raw.communitydragon.org/15.22/game/assets/characters"
    
    async def get_champion_splash(self, champion_name: str) -> str:
        champion_lower = champion_name.lower()
        base_path = f"{self.base_url}/{champion_lower}/skins/base"
        
        possible_patterns = [
            f"{champion_lower}_loadscreen.png",
            f"{champion_lower}_loadscreen_0.png",
            f"{champion_lower}_loadscreen_1.png",
            f"{champion_lower}_loadscreen_2.png",
            "loadscreen.png",
            "loadscreen_0.png",
            "loadscreen_1.png",
        ]
        
        async with aiohttp.ClientSession() as session:
            for pattern in possible_patterns:
                try:
                    url = f"{base_path}/{pattern}"
                    async with session.head(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            return url
                except Exception as e:
                    continue
            
            try:
                async with session.get(base_path, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        import re
                        loadscreen_files = re.findall(r'([\w_-]*loadscreen[\w_-]*\.png)', content, re.IGNORECASE)
                        if loadscreen_files:
                            first_file = loadscreen_files[0]
                            return f"{base_path}/{first_file}"
            except:
                pass
        return f"{base_path}/{champion_lower}_loadscreen.png"
    
    def get_rank_image_url(self, rank: str) -> str:
        rank_mapping = {
            "Iron": "https://static.wikia.nocookie.net/leagueoflegends/images/f/fe/Season_2022_-_Iron.png",
            "Bronze": "https://static.wikia.nocookie.net/leagueoflegends/images/e/e9/Season_2022_-_Bronze.png",
            "Silver": "https://static.wikia.nocookie.net/leagueoflegends/images/4/44/Season_2022_-_Silver.png",
            "Gold": "https://static.wikia.nocookie.net/leagueoflegends/images/8/8d/Season_2022_-_Gold.png",
            "Platinum": "https://static.wikia.nocookie.net/leagueoflegends/images/3/3b/Season_2022_-_Platinum.png",
            "Emerald": "https://static.wikia.nocookie.net/leagueoflegends/images/d/d4/Season_2023_-_Emerald.png",
            "Diamond": "https://static.wikia.nocookie.net/leagueoflegends/images/e/ee/Season_2022_-_Diamond.png",
            "Master": "https://static.wikia.nocookie.net/leagueoflegends/images/e/eb/Season_2022_-_Master.png",
            "Grandmaster": "https://static.wikia.nocookie.net/leagueoflegends/images/f/fc/Season_2022_-_Grandmaster.png",
            "Challenger": "https://static.wikia.nocookie.net/leagueoflegends/images/0/02/Season_2022_-_Challenger.png"
        }
        
        for rank_key, url in rank_mapping.items():
            if rank_key.lower() in rank.lower():
                return url
        
        return rank_mapping["Silver"]
    
    def create_base_card(self):
        self.image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
        self.draw = ImageDraw.Draw(self.image)
        return self
    
    def load_fonts(self):
        try:
            self.fonts['title'] = ImageFont.truetype("arial.ttf", 16)
            self.fonts['name'] = ImageFont.truetype("arial.ttf", 24)
            self.fonts['subtitle'] = ImageFont.truetype("arial.ttf", 14)
            self.fonts['story'] = ImageFont.truetype("arial.ttf", 11)
            self.fonts['circle'] = ImageFont.truetype("arial.ttf", 20)
            self.fonts['circle_label'] = ImageFont.truetype("arial.ttf", 10)
            self.fonts['footer'] = ImageFont.truetype("arial.ttf", 9)
        except:
            default_font = ImageFont.load_default()
            self.fonts['title'] = default_font
            self.fonts['name'] = default_font
            self.fonts['subtitle'] = default_font
            self.fonts['story'] = default_font
            self.fonts['circle'] = default_font
            self.fonts['circle_label'] = default_font
            self.fonts['footer'] = default_font
        return self
    
    def draw_golden_border(self):
        """Dessine la bordure dorée style LoL"""
        gold = (218, 165, 32)
        dark_gold = (139, 101, 8)
        
        for i in range(5):
            self.draw.rectangle(
                [i, i, self.width - 1 - i, self.height - 1 - i],
                outline=gold if i % 2 == 0 else dark_gold,
                width=1
            )
        
        corner_size = 15
        for x, y in [(10, 10), (self.width - 10, 10), (10, self.height - 10), (self.width - 10, self.height - 10)]:
            self.draw.rectangle([x - 3, y - 3, x + 3, y + 3], fill=gold)
        
        return self
    
    def draw_circle_stat(self, x: int, y: int, value: str, label: str, is_rank: bool = False):
        gold = (218, 165, 32)
        dark_bg = (20, 20, 30)
        
        radius = 30
        
        self.draw.ellipse([x - radius - 3, y - radius - 3, x + radius + 3, y + radius + 3], 
                         fill=gold, outline=None)
        self.draw.ellipse([x - radius, y - radius, x + radius, y + radius], 
                         fill=dark_bg, outline=None)
        
        if is_rank:
            try:
                rank_url = self.get_rank_image_url(self.profil.rank)
                response = urlopen(rank_url)
                rank_img = Image.open(BytesIO(response.read()))
                rank_size = int(radius * 1.5)
                rank_img = rank_img.resize((rank_size, rank_size), Image.Resampling.LANCZOS)
                rank_img = rank_img.convert('RGBA')
                mask = Image.new('L', (rank_size, rank_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([0, 0, rank_size, rank_size], fill=255)
                self.image.paste(rank_img, (x - rank_size // 2, y - rank_size // 2), mask)
                self.draw = ImageDraw.Draw(self.image)
            except Exception as e:
                print(f"Erreur chargement image rang: {e}")
                bbox = self.draw.textbbox((0, 0), value, font=self.fonts['circle'])
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
                self.draw.text((x - text_w // 2, y - text_h // 2), value, 
                              fill=gold, font=self.fonts['circle'])
        else:
            bbox = self.draw.textbbox((0, 0), label, font=self.fonts['circle_label'])
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            self.draw.text((x - text_w // 2, y - 12), label, 
                          fill=gold, font=self.fonts['circle_label'])
            bbox = self.draw.textbbox((0, 0), value, font=self.fonts['circle'])
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            self.draw.text((x - text_w // 2, y + 2), value, 
                          fill=gold, font=self.fonts['circle'])
        
        return self
    
    def add_champion_splash(self, champion_url: str):
        try:
            response = urlopen(champion_url)
            champ_img = Image.open(BytesIO(response.read()))
            img_width = self.width
            img_height = self.height
            
            aspect_ratio = champ_img.width / champ_img.height
            target_aspect = img_width / img_height
            
            if aspect_ratio > target_aspect:
                new_height = img_height
                new_width = int(new_height * aspect_ratio)
                champ_img = champ_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                crop_x = (new_width - img_width) // 2
                champ_img = champ_img.crop((crop_x, 0, crop_x + img_width, img_height))
            else:
                new_width = img_width
                new_height = int(new_width / aspect_ratio)
                champ_img = champ_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                crop_y = max(0, (new_height - img_height) // 4)  # Garder le haut
                champ_img = champ_img.crop((0, crop_y, img_width, crop_y + img_height))
            
            champ_img = champ_img.convert('RGBA')
            self.image.paste(champ_img, (0, 0))
            self.draw = ImageDraw.Draw(self.image)
            
        except Exception as e:
            print(f"Error: {e}")
            for y in range(self.height):
                ratio = y / self.height
                color_val = int(40 + ratio * 20)
                self.draw.line([(0, y), (self.width, y)], fill=(color_val, color_val, color_val + 20))
        
        return self
    
    def draw_info_section(self):
        gold = (218, 165, 32)
        
        info_y = self.height - 170
        info_height = 145
        padding = 15
        
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        dark_bg = (20, 25, 35, 220)
        overlay_draw.rounded_rectangle(
            [padding, info_y, self.width - padding, info_y + info_height],
            radius=15,
            fill=dark_bg
        )
        
        self.image = Image.alpha_composite(self.image, overlay)
        self.draw = ImageDraw.Draw(self.image)
        
        bbox = self.draw.textbbox((0, 0), self.profil.name, font=self.fonts['name'])
        text_w = bbox[2] - bbox[0]
        self.draw.text((self.width // 2 - text_w // 2, info_y + 20), 
                      self.profil.name, fill=(255, 255, 255), font=self.fonts['name'])
        
        bbox = self.draw.textbbox((0, 0), self.profil.title, font=self.fonts['subtitle'])
        text_w = bbox[2] - bbox[0]
        self.draw.text((self.width // 2 - text_w // 2, info_y + 52), 
                      self.profil.title, fill=gold, font=self.fonts['subtitle'])
        
        story_y = info_y + 77
        max_width = self.width - 50
        words = self.profil.story.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self.draw.textbbox((0, 0), test_line, font=self.fonts['story'])
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        lines = lines[:3]
        
        for i, line in enumerate(lines):
            bbox = self.draw.textbbox((0, 0), line, font=self.fonts['story'])
            text_w = bbox[2] - bbox[0]
            self.draw.text((self.width // 2 - text_w // 2, story_y + i * 14), 
                          line, fill=(220, 220, 220), font=self.fonts['story'])
        
        return self
    
    def draw_header_and_footer(self):
        gold = (218, 165, 32)
        hot_pink = (255, 76, 154)
        cyan = (0, 184, 217)
        white = (255, 255, 255)
        
        header_text = "2025 REWIND"
        bbox = self.draw.textbbox((0, 0), header_text, font=self.fonts['title'])
        text_w = bbox[2] - bbox[0]
        self.draw.text((self.width // 2 - text_w // 2, 15), 
                      header_text, fill=gold, font=self.fonts['title'])
        
        footer_y = self.height - 20
        
        word1 = "Jinx's"
        word2 = "Magical"
        word3 = "Rewind Machine"
        
        bbox1 = self.draw.textbbox((0, 0), word1, font=self.fonts['footer'])
        w1 = bbox1[2] - bbox1[0]
        
        bbox2 = self.draw.textbbox((0, 0), " " + word2, font=self.fonts['footer'])
        w2 = bbox2[2] - bbox2[0]
        
        bbox3 = self.draw.textbbox((0, 0), " " + word3, font=self.fonts['footer'])
        w3 = bbox3[2] - bbox3[0]
        
        total_width = w1 + w2 + w3
        start_x = (self.width - total_width) // 2
        current_x = start_x
        self.draw.text((current_x, footer_y), word1, fill=hot_pink, font=self.fonts['footer'])
        current_x += w1
        self.draw.text((current_x, footer_y), " " + word2, fill=cyan, font=self.fonts['footer'])
        current_x += w2
        self.draw.text((current_x, footer_y), " " + word3, fill=white, font=self.fonts['footer'])
        
        return self
    
    def save(self, filename: str):
        self.image.save(filename, 'PNG')
        return self
    
    async def create_card_async(self) -> bool:
        try:
            champion_url = await self.get_champion_splash(self.profil.champion_played)
            
            self.create_base_card()
            self.add_champion_splash(champion_url)
            self.load_fonts()
            self.draw_golden_border()
            self.draw_header_and_footer()
            left_circle_x = 50
            right_circle_x = self.width - 50
            circle_y = 50
            self.draw_circle_stat(left_circle_x, circle_y, str(self.profil.lvl), "LVL")
            self.draw_circle_stat(right_circle_x, circle_y, self.profil.rank, "RANK", is_rank=True)
            self.draw_info_section()
            filename = f"{self.profil.name}_rewind_card.png"
            self.save(filename)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def create_card(self) -> bool:
        return asyncio.run(self.create_card_async())


def main():
    profil = RewindExportProfil(
        player_name="Faker",
        champion_played="Ahri",
        games_played=342,
        kd=4.2,
        lvl=287,
        rank="Silver",
        title="The Unkillable Demon King",
        story="The legend continues with style and precision across the Rift"
    )
    generator = RewindCardGeneration(profil)
    generator.create_card()

if __name__ == "__main__":
    main()
