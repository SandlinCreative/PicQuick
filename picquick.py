from flask import Flask, render_template_string, url_for
from PIL import Image
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__, static_url_path='', static_folder='.')
IMAGE_FOLDER = os.path.dirname(os.path.abspath(__file__))
THUMB_FOLDER = os.path.join(IMAGE_FOLDER, 'thumbs')

if not os.path.exists(THUMB_FOLDER):
    os.makedirs(THUMB_FOLDER)

def create_thumbnail(image_path):
    with Image.open(image_path) as img:
        height = 400
        # Calculate the new width to preserve the aspect ratio
        aspect_ratio = img.width / img.height
        width = int(height * aspect_ratio)
        
        # Creating the thumbnail
        img.thumbnail((width, height))
        # Save it to the thumbs directory
        thumb_path = os.path.join(THUMB_FOLDER, os.path.basename(image_path))
        img.save(thumb_path, "JPEG")

# Function to create thumbnails for existing images
def create_thumbnails():
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(IMAGE_FOLDER, filename)
            create_thumbnail(image_path)

# Call the function to create thumbnails on startup
create_thumbnails()

# Flask route for the gallery
@app.route('/')
def gallery():
    thumbnails = [os.path.join('thumbs', file) for file in os.listdir(THUMB_FOLDER) if file.endswith(('.jpg', '.jpeg', '.png'))]
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Image Gallery</title>
            <style>
                #gallery img {
                    height: 100px; /* Displaying the thumbnails at a consistent size */
                    margin: 5px;
                    border: 1px solid #ccc;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
                }
                #gallery {
                    display: flex;
                    flex-wrap: wrap;
                }
            </style>
        </head>
        <body>
            <h1>Dynamic Image Gallery</h1>
            <div id="gallery">
                {% for thumbnail in thumbnails %}
                    <img src="{{ url_for('static', filename=thumbnail) }}" alt="Gallery Image">
                {% endfor %}
            </div>
        </body>
        </html>
    ''', thumbnails=thumbnails)

class NewImageHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Check if the event is for a new image file
        if event.src_path.endswith(('.jpg', '.jpeg', '.png')):
            create_thumbnail(event.src_path)

if __name__ == '__main__':
    # Set up watchdog observer
    event_handler = NewImageHandler()
    observer = Observer()
    observer.schedule(event_handler, path=IMAGE_FOLDER, recursive=False)
    observer.start()

    try:
        # Start the Flask app
        app.run(debug=True, use_reloader=False)
    finally:
        observer.stop()
        observer.join()
