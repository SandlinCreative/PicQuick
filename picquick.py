from flask import Flask, render_template_string, send_from_directory, abort
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import threading

app = Flask(__name__)

# Embedded HTML templates
INDEX_TEMPLATE = """
<!doctype html>
<title>PicQuick Gallery Index</title>
<h1>Image Galleries</h1>
<ul>
    {% for folder in folders %}
    <li><a href="{{ url_for('show_gallery', folder_name=folder) }}">{{ folder }}</a></li>
    {% endfor %}
</ul>
"""

GALLERY_TEMPLATE = """
<!doctype html>
<title>PicQuick Gallery - {{ folder_name }}</title>
<h1>Gallery: {{ folder_name }}</h1>
<a href="{{ url_for('gallery_index') }}">Back to the index</a>
<div>
    {% for thumbnail in thumbnails %}
    <a href="{{ url_for('custom_static', filename=folder_name + '/' + thumbnail) }}">
        <img src="{{ url_for('custom_static_for_thumbs', filename=folder_name + '/' + thumbnail) }}" alt="{{ thumbnail }}" style="height: 500px;">
    </a>
    {% endfor %}
</div>
"""

# Image processing function
def create_thumbnail(image_path, thumbnail_path):
    with Image.open(image_path) as img:
        img.thumbnail((img.width, 500), Image.ANTIALIAS)
        root, ext = os.path.splitext(thumbnail_path)
        thumbnail_file = f"{root}.jpg"
        img.save(thumbnail_file, "JPEG")

# Watchdog event handler
class ImageEventHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            thumbnail_path = get_thumbnail_path(event.src_path)
            create_thumbnail(event.src_path, thumbnail_path)

def get_thumbnail_path(image_path):
    dir_name, file_name = os.path.split(image_path)
    thumb_dir = os.path.join('thumbs', dir_name)
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir)
    return os.path.join(thumb_dir, file_name)

# Watchdog monitoring setup
def start_monitoring(path):
    event_handler = ImageEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

# Flask view functions
@app.route('/')
def gallery_index():
    folders = [folder for folder in next(os.walk('.'))[1] if not folder.startswith('thumbs')]
    return render_template_string(INDEX_TEMPLATE, folders=folders)

@app.route('/gallery/<folder_name>')
def show_gallery(folder_name):
    try:
        thumbnails = os.listdir(f'./thumbs/{folder_name}')
        thumbnails = [thumb for thumb in thumbnails if thumb.endswith('.jpg')]
    except FileNotFoundError:
        abort(404)
    return render_template_string(GALLERY_TEMPLATE, thumbnails=thumbnails, folder_name=folder_name)

@app.route('/thumbs/<path:filename>')
def custom_static_for_thumbs(filename):
    return send_from_directory('thumbs', filename)

@app.route('/<path:filename>')
def custom_static(filename):
    return send_from_directory('.', filename)

# Function to create thumbnails for all existing images
def generate_existing_thumbnails():
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_path = os.path.join(root, file)
                thumbnail_path = get_thumbnail_path(image_path)
                if not os.path.exists(thumbnail_path):
                    create_thumbnail(image_path, thumbnail_path)

if __name__ == '__main__':
    # Generate thumbnails for existing images
    generate_existing_thumbnails()
    # Start watchdog monitoring in a new thread
    monitor_thread = threading.Thread(target=start_monitoring, args=('.',), daemon=True)
    monitor_thread.start()
    # Start Flask app
    app.run(debug=True, use_reloader=False)
