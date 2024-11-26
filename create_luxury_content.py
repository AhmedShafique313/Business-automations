import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from io import BytesIO
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx

# Unsplash API access
UNSPLASH_ACCESS_KEY = "YOUR_ACCESS_KEY"  # You'll need to provide your Unsplash API key
LUXURY_QUERIES = [
    "luxury living room staging",
    "modern luxury interior",
    "luxury home kitchen staged",
    "luxury master bedroom staged"
]

def download_luxury_images():
    """Download high-quality luxury home images from Unsplash"""
    images = []
    headers = {'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'}
    
    for query in LUXURY_QUERIES:
        url = f'https://api.unsplash.com/search/photos?query={query}&orientation=landscape&per_page=1'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                img_url = data['results'][0]['urls']['regular']
                img_response = requests.get(img_url)
                if img_response.status_code == 200:
                    img = Image.open(BytesIO(img_response.content))
                    images.append(img)
    
    return images

def create_luxury_text_overlay(text, size=(1920, 1080), font_size=80):
    """Create professional looking text overlay with shadow effect"""
    # Create transparent background
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try to use a luxury font, fallback to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position for center alignment
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (size[0] - text_width) // 2
    y = size[1] - text_height - 100  # Position text near bottom
    
    # Draw text shadow
    shadow_offset = 3
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    return overlay

def create_luxury_reel():
    """Create a professional luxury home staging reel"""
    os.makedirs('content/luxury_images', exist_ok=True)
    os.makedirs('content/luxury_reels', exist_ok=True)
    
    # Download luxury images
    print("Downloading luxury home images...")
    images = download_luxury_images()
    
    if not images:
        print("Error: Could not download luxury images. Please check your API key and internet connection.")
        return
    
    # Save images with text overlays
    clips = []
    captions = [
        "LUXURY HOME STAGING",
        "TRANSFORM YOUR SPACE",
        "ELEVATE YOUR LISTING",
        "DESIGN GAGA"
    ]
    
    print("Creating video sequences...")
    for idx, (img, caption) in enumerate(zip(images, captions)):
        # Resize image to 1920x1080 while maintaining aspect ratio
        img = img.convert('RGB')
        img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
        
        # Create new 1920x1080 image with black background
        background = Image.new('RGB', (1920, 1080), 'black')
        offset = ((1920 - img.width) // 2, (1080 - img.height) // 2)
        background.paste(img, offset)
        
        # Save base image
        base_path = f'content/luxury_images/luxury_{idx}.jpg'
        background.save(base_path, quality=95)
        
        # Create text overlay
        text_overlay = create_luxury_text_overlay(caption)
        text_path = f'content/luxury_images/text_{idx}.png'
        text_overlay.save(text_path)
        
        # Create video clip
        clip = ImageClip(base_path).set_duration(4)
        text_clip = ImageClip(text_path).set_duration(4)
        
        # Add effects
        clip = clip.resize(lambda t: 1 + 0.05*t)  # Slow zoom
        clip = clip.crossfadein(0.5)  # Fade in
        
        # Combine image and text
        final_clip = CompositeVideoClip([clip, text_clip])
        clips.append(final_clip)
    
    # Create final video
    print("Rendering final video...")
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.fadeout(1.0)
    
    # Add cinematic black bars
    def add_black_bars(frame):
        h, w = frame.shape[:2]
        bar_height = int(h * 0.1)  # 10% of height for each bar
        frame[:bar_height] = 0  # Top bar
        frame[-bar_height:] = 0  # Bottom bar
        return frame
    
    final_video = final_video.fl_image(add_black_bars)
    
    # Write video with high quality
    output_path = 'content/luxury_reels/design_gaga_luxury_showcase.mp4'
    final_video.write_videofile(output_path, fps=30, codec='libx264', bitrate='8000k')
    print(f"Luxury reel generated successfully at {output_path}")

if __name__ == "__main__":
    create_luxury_reel()
