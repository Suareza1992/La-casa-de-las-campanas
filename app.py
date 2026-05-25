from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from utils.pdf_processing import extract_images_from_pdf
from models import SessionLocal, ProductItem

app = Flask(__name__)
UPLOAD_FOLDER = 'static/output'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Main site routes ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/legales')
def legales():
    return render_template('legales.html')


# --- Product API ---

@app.route('/api/products')
def api_products():
    db = SessionLocal()
    items = db.query(ProductItem).all()
    db.close()
    products = []
    for item in items:
        products.append({
            'id': str(item.id),
            'name': item.name or item.image_name,
            'description': item.caption or '',
            'price': item.price or '0.00',
            'image': f'/static/output/{item.image_name}',
            'category': item.category or 'otros',
        })
    return jsonify(products)


# --- Admin routes ---

@app.route('/admin/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'pdf_file' not in request.files:
            return redirect(request.url)

        file = request.files['pdf_file']
        folder_name = request.form.get('folder_name', '').strip()

        if not file or not allowed_file(file.filename):
            return redirect(request.url)

        if not folder_name:
            folder_name = secure_filename(file.filename).rsplit('.', 1)[0]

        output_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        pdf_path = os.path.join(output_folder, secure_filename(file.filename))
        os.makedirs(output_folder, exist_ok=True)
        file.save(pdf_path)

        count = extract_images_from_pdf(pdf_path, output_folder)

        # Build items list for the results review page
        items = []
        for i in range(1, count + 1):
            caption_path = os.path.join(output_folder, f"Caption{i}.txt")
            caption = ""
            if os.path.exists(caption_path):
                with open(caption_path, encoding="utf-8") as f:
                    caption = f.read()

            # Find the actual image extension
            image_name = None
            for ext in ('png', 'jpeg', 'jpg', 'webp'):
                candidate = f"{folder_name}/Image{i}.{ext}"
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], candidate)):
                    image_name = candidate
                    break
            if not image_name:
                image_name = f"{folder_name}/Image{i}.png"

            items.append({'id': i, 'image': image_name, 'caption': caption})

        return render_template('admin/results.html', items=items, folder=folder_name)

    return render_template('admin/upload.html')


@app.route('/save_captions', methods=['POST'])
def save_captions():
    data = request.form
    folder = data.get("folder")
    if not folder:
        return jsonify({"status": "error", "message": "No folder provided"}), 400

    output_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    captions_json = {}
    db = SessionLocal()

    for key in data:
        if key.startswith("caption_"):
            img_id = key.split("_", 1)[1]
            caption = data[key].strip()
            name = data.get(f"name_{img_id}", "").strip()
            price = data.get(f"price_{img_id}", "").strip()
            category = data.get(f"category_{img_id}", "otros").strip()

            # Find actual image file
            image_name = None
            for ext in ('png', 'jpeg', 'jpg', 'webp'):
                candidate = f"{folder}/Image{img_id}.{ext}"
                if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], candidate)):
                    image_name = candidate
                    break
            if not image_name:
                image_name = f"{folder}/Image{img_id}.png"

            # Save caption .txt
            caption_path = os.path.join(output_folder, f"Caption{img_id}.txt")
            with open(caption_path, "w", encoding="utf-8") as f:
                f.write(caption)

            # Upsert in DB
            item = db.query(ProductItem).filter_by(image_name=image_name).first()
            if item:
                item.caption = caption
                item.name = name or item.name
                item.price = price or item.price
                item.category = category or item.category
            else:
                item = ProductItem(
                    image_name=image_name,
                    caption=caption,
                    name=name,
                    price=price,
                    category=category,
                )
                db.add(item)

            captions_json[image_name] = caption

    db.commit()
    db.close()

    json_path = os.path.join(output_folder, "captions.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(captions_json, jf, indent=2)

    return jsonify({"status": "success", "message": "¡Productos guardados exitosamente!"})


@app.route('/admin/items')
def view_items():
    db = SessionLocal()
    items = db.query(ProductItem).all()
    db.close()
    return render_template('admin/items.html', items=items)


@app.route('/admin/items/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    db = SessionLocal()
    item = db.query(ProductItem).filter_by(id=item_id).first()
    if item:
        db.delete(item)
        db.commit()
    db.close()
    return redirect(url_for('view_items'))


if __name__ == '__main__':
    app.run(debug=True)
