
import os
import math
from PIL import Image, ImageDraw, ImageFont

def merge_images_with_text():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the input and output directories
    input_dir = os.path.join(script_dir, 'output')
    output_path = os.path.join(script_dir, '202512.png')

    # Get a list of all .png files in the input directory and sort them
    try:
        image_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])
    except FileNotFoundError:
        print(f"Error: Input directory not found at '{input_dir}'")
        return

    if not image_files:
        print("No images found in the 'output' directory.")
        return

    # Open the first image to get dimensions
    try:
        with Image.open(os.path.join(input_dir, image_files[0])) as img:
            img_width, img_height = img.size
    except Exception as e:
        print(f"Error opening first image: {e}")
        return

    # --- Grid Calculation ---
    num_images = len(image_files)
    cols = 5 # Let's arrange in 5 columns
    rows = math.ceil(num_images / cols)
    
    # Total dimensions of the merged image
    total_width = cols * img_width
    total_height = rows * img_height

    # Create a new blank image (white background)
    merged_image = Image.new('RGB', (total_width, total_height), 'white')
    draw = ImageDraw.Draw(merged_image)

    # --- Font Selection ---
    try:
        # Try to use a common sans-serif font
        font = ImageFont.truetype("DejaVuSans.ttf", size=30)
    except IOError:
        print("DejaVuSans.ttf not found. Using default font.")
        # Use a basic default font if the preferred one isn't available
        font = ImageFont.load_default()

    text_to_add = "起点时间为9:30"
    text_position = (10, 10) # Top-left corner with a small margin
    text_color = "red"

    # --- Image Pasting and Annotation ---
    current_x, current_y = 0, 0
    for i, image_file in enumerate(image_files):
        try:
            with Image.open(os.path.join(input_dir, image_file)) as img:
                # Create a copy to draw text on, to avoid altering the original
                img_with_text = img.copy().convert("RGB") # Ensure it's RGB for color text
                draw_on_img = ImageDraw.Draw(img_with_text)
                
                # Draw the text on the individual image
                draw_on_img.text(text_position, text_to_add, font=font, fill=text_color)
                
                # Calculate the position to paste the image
                col = i % cols
                row = i // cols
                paste_x = col * img_width
                paste_y = row * img_height
                
                # Paste the image with text onto the merged canvas
                merged_image.paste(img_with_text, (paste_x, paste_y))
        except Exception as e:
            print(f"Error processing image {image_file}: {e}")
            continue # Skip to the next image

    # Save the final image
    try:
        merged_image.save(output_path)
        print(f"Successfully merged {len(image_files)} images into '{output_path}'")
    except Exception as e:
        print(f"Error saving the final image: {e}")

if __name__ == "__main__":
    merge_images_with_text()
