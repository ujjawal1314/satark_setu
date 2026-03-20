from PIL import Image

def process_image(input_path, output_path):
    img = Image.open(input_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    for r, g, b, a in data:
        # Detect grey checkerboard background (high brightness, low color variance)
        brightness = (r + g + b) / 3
        variance = max(r, g, b) - min(r, g, b)
        
        # If the pixel is light and largely grey, it's the checkerboard background
        if brightness > 180 and variance < 30:
            new_data.append((r, g, b, 0)) # Make transparent
        else:
            new_data.append((r, g, b, a))
            
    img.putdata(new_data)
    img.save(output_path, "PNG")
    print(f"Saved {output_path}")

process_image("logo.png", "logo_transparent.png")
