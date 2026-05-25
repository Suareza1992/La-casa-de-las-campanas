from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from functools import wraps
import os, json
from werkzeug.utils import secure_filename
from utils.pdf_processing import extract_images_from_pdf
from models import SessionLocal, ProductItem, User, Order, OrderItem
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicie sesión para acceder.'

mail = Mail(app)

UPLOAD_FOLDER = 'static/output'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.query(User).get(int(user_id))
    db.close()
    return user


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Acceso restringido al administrador.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Email helpers ─────────────────────────────────────────────────────────────

def send_order_email(order, items_data, client):
    try:
        items_text = "\n".join(
            f"  - {i['name']} x{i['quantity']}  (${i['price']})" for i in items_data
        )
        mail.send(Message(
            subject=f"Nueva cotización — Pedido #{order.id}",
            recipients=[app.config['ADMIN_EMAIL']],
            body=(
                f"Cliente: {client.username} <{client.email}>\n"
                f"Pedido #: {order.id}\n"
                f"Fecha: {order.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Productos:\n{items_text}\n\n"
                f"Notas: {order.notes or 'Ninguna'}\n"
            ),
        ))
        mail.send(Message(
            subject="Recibimos tu solicitud — La casa de las campanas",
            recipients=[client.email],
            body=(
                f"Hola {client.username},\n\n"
                f"Hemos recibido tu solicitud de cotización:\n\n"
                f"{items_text}\n\n"
                f"Nos pondremos en contacto contigo a la brevedad.\n\n"
                f"La casa de las campanas\n"
                f"casacampanaspr@gmail.com | +1 (787) 470-3443"
            ),
        ))
    except Exception as e:
        app.logger.warning(f"Email not sent: {e}")


def send_contact_email(name, email, subject, message):
    try:
        mail.send(Message(
            subject=f"Contacto: {subject}",
            recipients=[app.config['ADMIN_EMAIL']],
            reply_to=email,
            body=f"Nombre: {name}\nEmail: {email}\nAsunto: {subject}\n\n{message}",
        ))
    except Exception as e:
        app.logger.warning(f"Email not sent: {e}")


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard') if current_user.role == 'admin' else url_for('catalog'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = SessionLocal()
        user = db.query(User).filter_by(email=email).first()
        db.close()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('admin_dashboard') if user.role == 'admin' else url_for('catalog'))
        flash('Email o contraseña incorrectos.')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('catalog'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = SessionLocal()
        if db.query(User).filter_by(email=email).first():
            flash('Ya existe una cuenta con ese email.')
            db.close()
            return render_template('auth/register.html')
        user = User(username=username, email=email, role='client')
        user.set_password(password)
        db.add(user)
        db.commit()
        db.close()
        flash('Cuenta creada. Por favor inicia sesión.')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ── Public routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/legales')
def legales():
    return render_template('legales.html')


@app.route('/contact', methods=['POST'])
def contact():
    send_contact_email(
        request.form.get('name', ''),
        request.form.get('email', ''),
        request.form.get('subject', ''),
        request.form.get('message', ''),
    )
    return jsonify({'status': 'success', 'message': '¡Tu mensaje fue enviado correctamente!'})


# ── Client routes ─────────────────────────────────────────────────────────────

@app.route('/catalog')
@login_required
def catalog():
    return render_template('client/catalog.html')


@app.route('/api/products')
def api_products():
    db = SessionLocal()
    items = db.query(ProductItem).all()
    db.close()
    return jsonify([{
        'id': str(item.id),
        'name': item.name or item.image_name,
        'description': item.caption or '',
        'price': item.price or '0.00',
        'image': f'/static/output/{item.image_name}',
        'category': item.category or 'otros',
    } for item in items])


@app.route('/order/submit', methods=['POST'])
@login_required
def submit_order():
    data = request.get_json()
    cart = data.get('cart', [])
    notes = data.get('notes', '')

    if not cart:
        return jsonify({'status': 'error', 'message': 'El carrito está vacío.'}), 400

    db = SessionLocal()
    order = Order(user_id=current_user.id, notes=notes, status='pending')
    db.add(order)
    db.flush()

    items_data = []
    for cart_item in cart:
        product = db.query(ProductItem).get(int(cart_item['id']))
        if product:
            db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=cart_item.get('quantity', 1)))
            items_data.append({
                'name': product.name or product.image_name,
                'price': product.price or '0.00',
                'quantity': cart_item.get('quantity', 1),
            })

    db.commit()
    user = db.query(User).get(current_user.id)
    order_obj = db.query(Order).get(order.id)
    send_order_email(order_obj, items_data, user)
    db.close()

    return jsonify({'status': 'success', 'message': f'Solicitud #{order.id} enviada.', 'order_id': order.id})


# ── Admin routes ──────────────────────────────────────────────────────────────

@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = SessionLocal()
    product_count = db.query(ProductItem).count()
    pending_orders = db.query(Order).filter_by(status='pending').count()
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    db.close()
    return render_template('admin/dashboard.html',
                           product_count=product_count,
                           pending_orders=pending_orders,
                           recent_orders=recent_orders)


@app.route('/admin/orders')
@admin_required
def admin_orders():
    db = SessionLocal()
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    db.close()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    db = SessionLocal()
    order = db.query(Order).get(order_id)
    if order:
        order.status = request.form.get('status', order.status)
        db.commit()
    db.close()
    return redirect(url_for('admin_orders'))


@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
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
        items = []
        for i in range(1, count + 1):
            caption_path = os.path.join(output_folder, f"Caption{i}.txt")
            caption = open(caption_path, encoding='utf-8').read() if os.path.exists(caption_path) else ''
            image_name = next(
                (f"{folder_name}/Image{i}.{ext}"
                 for ext in ('png', 'jpeg', 'jpg', 'webp')
                 if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f"{folder_name}/Image{i}.{ext}"))),
                f"{folder_name}/Image{i}.png"
            )
            items.append({'id': i, 'image': image_name, 'caption': caption})
        return render_template('admin/results.html', items=items, folder=folder_name)
    return render_template('admin/upload.html')


@app.route('/save_captions', methods=['POST'])
@admin_required
def save_captions():
    data = request.form
    folder = data.get('folder')
    if not folder:
        return jsonify({'status': 'error', 'message': 'No folder provided'}), 400
    output_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    captions_json = {}
    db = SessionLocal()
    for key in data:
        if not key.startswith('caption_'):
            continue
        img_id = key.split('_', 1)[1]
        caption = data[key].strip()
        name = data.get(f'name_{img_id}', '').strip()
        price = data.get(f'price_{img_id}', '').strip()
        category = data.get(f'category_{img_id}', 'otros').strip()
        image_name = next(
            (f"{folder}/Image{img_id}.{ext}"
             for ext in ('png', 'jpeg', 'jpg', 'webp')
             if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f"{folder}/Image{img_id}.{ext}"))),
            f"{folder}/Image{img_id}.png"
        )
        with open(os.path.join(output_folder, f"Caption{img_id}.txt"), 'w', encoding='utf-8') as f:
            f.write(caption)
        item = db.query(ProductItem).filter_by(image_name=image_name).first()
        if item:
            item.caption = caption
            if name: item.name = name
            if price: item.price = price
            if category: item.category = category
        else:
            db.add(ProductItem(image_name=image_name, caption=caption, name=name, price=price, category=category))
        captions_json[image_name] = caption
    db.commit()
    db.close()
    with open(os.path.join(output_folder, 'captions.json'), 'w', encoding='utf-8') as jf:
        json.dump(captions_json, jf, indent=2)
    return jsonify({'status': 'success', 'message': '¡Productos guardados exitosamente!'})


@app.route('/admin/items')
@admin_required
def view_items():
    db = SessionLocal()
    items = db.query(ProductItem).all()
    db.close()
    return render_template('admin/items.html', items=items)


@app.route('/admin/items/<int:item_id>/delete', methods=['POST'])
@admin_required
def delete_item(item_id):
    db = SessionLocal()
    item = db.query(ProductItem).filter_by(id=item_id).first()
    if item:
        db.delete(item)
        db.commit()
    db.close()
    return redirect(url_for('view_items'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
