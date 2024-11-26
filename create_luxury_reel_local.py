import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx
from moviepy.audio.AudioClip import AudioArrayClip
import requests
from io import BytesIO

def create_luxury_background(width=1920, height=1080, color=(20, 20, 20)):
    """Create a luxury dark background with gradient"""
    background = np.zeros((height, width, 3), np.uint8)
    for i in range(height):
        factor = 1 - (i / height) * 0.5
        background[i] = [int(c * factor) for c in color]
    return background

def create_luxury_text_image(text, size=(1920, 1080)):
    """Create professional looking text with effects"""
    # Create gradient background
    img = create_luxury_background()
    
    # Convert to PIL for text
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)
    
    # Try to use a professional font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    except:
        font = ImageFont.load_default()
    
    # Calculate text size for centering
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Position text in center
    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2
    
    # Add shadow effect
    shadow_offset = 4
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(30, 30, 30))
    draw.text((x, y), text, font=font, fill=(240, 240, 240))
    
    return np.array(img_pil)

def create_luxury_transition(width=1920, height=1080):
    """Create a luxury wipe transition"""
    transition = np.zeros((height, width, 3), np.uint8)
    for i in range(width):
        factor = i / width
        transition[:, i] = [int(255 * factor)] * 3
    return transition

def create_staged_room_simulation(width=1920, height=1080, style="modern"):
    """Create a luxury room simulation"""
    img = create_luxury_background(width, height, color=(40, 35, 30))
    
    if style == "modern":
        # Add floor
        cv2.rectangle(img, (0, height//2), (width, height), (60, 50, 40), -1)
        
        # Add large window
        cv2.rectangle(img, (width//4, height//8), (3*width//4, height//2), (150, 150, 150), -1)
        
        # Add luxury sofa
        cv2.rectangle(img, (width//3, 2*height//3), (2*width//3, 5*height//6), (80, 70, 60), -1)
        
        # Add designer coffee table
        cv2.rectangle(img, (width//2-100, 3*height//4), (width//2+100, 4*height//5), (90, 85, 80), -1)
        
        # Add art piece
        cv2.rectangle(img, (3*width//4, height//3), (7*width//8, height//2), (120, 110, 100), -1)
        
    return img

def create_luxury_reel():
    """Create a professional luxury home staging reel"""
    os.makedirs('content/luxury_reels', exist_ok=True)
    
    # Create clips
    clips = []
    
    # Opening title
    title_text = create_luxury_text_image("DESIGN GAGA")
    title_clip = ImageClip(title_text).set_duration(3).crossfadein(1)
    clips.append(title_clip)
    
    # Luxury rooms
    styles = ["modern", "classic", "contemporary"]
    captions = [
        "LUXURY STAGING",
        "TRANSFORM YOUR SPACE",
        "ELEVATE YOUR LISTING"
    ]
    
    for style, caption in zip(styles, captions):
        # Create room
        room = create_staged_room_simulation(style=style)
        room_clip = ImageClip(room).set_duration(4)
        
        # Add text overlay
        text = create_luxury_text_image(caption)
        text_clip = ImageClip(text).set_duration(4).set_opacity(0.8)
        
        # Combine with transition
        combined = CompositeVideoClip([
            room_clip.resize(lambda t: 1 + 0.05*t),  # Slow zoom
            text_clip.set_position('center')
        ]).crossfadein(0.5)
        
        clips.append(combined)
    
    # Create final video with transitions
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Add cinematic black bars
    def add_black_bars(frame):
        h, w = frame.shape[:2]
        bar_height = int(h * 0.1)
        frame[:bar_height] = 0  # Top bar
        frame[-bar_height:] = 0  # Bottom bar
        return frame
    
    final_video = final_video.fl_image(add_black_bars)
    
    # Add fade out
    final_video = final_video.fadeout(1.0)
    
    # Write high quality video
    output_path = 'content/luxury_reels/design_gaga_showcase.mp4'
    final_video.write_videofile(output_path, fps=30, codec='libx264', bitrate='8000k')
    print(f"Luxury reel generated successfully at {output_path}")

if __name__ == "__main__":
    create_luxury_reel()
