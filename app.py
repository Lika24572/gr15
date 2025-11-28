from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from datetime import datetime, timedelta
from database import Database, Service, Review, Booking, Order

app = Flask(__name__)
CORS(app)
db = Database()

# Вспомогательные функции
def row_to_service(row):
    return Service(
        id=row[0],
        name=row[1],
        description=row[2],
        price=row[3],
        category=row[4],
        duration=row[5],
        popular=bool(row[6])
    ).to_dict()

def row_to_review(row):
    return Review(
        id=row[0],
        author_name=row[1],
        author_avatar=row[2],
        rating=row[3],
        review_text=row[4],
        service_name=row[5],
        pet_type=row[6],
        approved=bool(row[7]),
        created_at=row[8]
    ).to_dict()

def row_to_booking(row):
    return Booking(
        id=row[0],
        customer_name=row[1],
        customer_phone=row[2],
        pet_name=row[5],
        pet_breed=row[6],
        service_name=row[7],
        service_price=row[8],
        booking_date=row[9],
        booking_time=row[10],
        status=row[11],
        notes=row[12],
        created_at=row[13]
    ).to_dict()

def row_to_order(row):
    return Order(
        id=row[0],
        customer_name=row[1],
        customer_phone=row[2],
        total_amount=row[3],
        status=row[4],
        items_json=row[5],
        created_at=row[6]
    ).to_dict()

# Роуты для услуг
@app.route('/api/services', methods=['GET'])
def get_services():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        category = request.args.get('category')
        popular = request.args.get('popular')
        
        query = "SELECT * FROM services WHERE active = TRUE"
        params = []
        
        if category and category != 'all':
            query += " AND category = ?"
            params.append(category)
        
        if popular == 'true':
            query += " AND popular = TRUE"
        
        query += " ORDER BY popular DESC, name ASC"
        
        cursor.execute(query, params)
        services = [row_to_service(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({'success': True, 'data': services})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM services WHERE id = ? AND active = TRUE", (service_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'success': False, 'error': 'Service not found'}), 404
        
        service = row_to_service(row)
        conn.close()
        return jsonify({'success': True, 'data': service})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для отзывов
@app.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        rating = request.args.get('rating')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 6))
        offset = (page - 1) * per_page
        
        query = "SELECT * FROM reviews WHERE approved = TRUE"
        params = []
        
        if rating and rating != 'all':
            query += " AND rating = ?"
            params.append(int(rating))
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        reviews = [row_to_review(row) for row in cursor.fetchall()]
        
        # Получаем общее количество для пагинации
        count_query = "SELECT COUNT(*) FROM reviews WHERE approved = TRUE"
        if rating and rating != 'all':
            count_query += " AND rating = ?"
            cursor.execute(count_query, (int(rating),))
        else:
            cursor.execute(count_query)
        
        total_count = cursor.fetchone()[0]
        
        # Статистика по рейтингам
        cursor.execute('''
            SELECT rating, COUNT(*) as count 
            FROM reviews 
            WHERE approved = TRUE 
            GROUP BY rating 
            ORDER BY rating DESC
        ''')
        rating_stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Средний рейтинг
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE approved = TRUE")
        avg_rating = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True, 
            'data': reviews,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            },
            'stats': {
                'average_rating': round(float(avg_rating), 1),
                'rating_counts': rating_stats,
                'total_reviews': total_count
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reviews', methods=['POST'])
def create_review():
    try:
        data = request.get_json()
        
        required_fields = ['author_name', 'rating', 'review_text']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (author_name, author_avatar, rating, review_text, service_name, pet_type, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['author_name'],
            data.get('author_avatar', ''),
            data['rating'],
            data['review_text'],
            data.get('service_name', ''),
            data.get('pet_type', ''),
            False  # Новые отзывы требуют модерации
        ))
        
        conn.commit()
        review_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Review submitted for moderation', 'id': review_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для записей
@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        date = request.args.get('date')
        status = request.args.get('status')
        
        query = "SELECT * FROM bookings WHERE 1=1"
        params = []
        
        if date:
            query += " AND booking_date = ?"
            params.append(date)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY booking_date, booking_time"
        
        cursor.execute(query, params)
        bookings = [row_to_booking(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({'success': True, 'data': bookings})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        
        required_fields = ['customer_name', 'customer_phone', 'pet_name', 'pet_breed', 'service_name', 'service_price', 'booking_date', 'booking_time']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Проверяем доступность времени
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE booking_date = ? AND booking_time = ? AND status IN ('pending', 'confirmed')
        ''', (data['booking_date'], data['booking_time']))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': 'This time slot is already booked'}), 400
        
        cursor.execute('''
            INSERT INTO bookings (customer_name, customer_phone, customer_email, pet_name, pet_breed, service_name, service_price, booking_date, booking_time, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['customer_name'],
            data['customer_phone'],
            data.get('customer_email', ''),
            data['pet_name'],
            data['pet_breed'],
            data['service_name'],
            data['service_price'],
            data['booking_date'],
            data['booking_time'],
            data.get('notes', '')
        ))
        
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Booking created successfully', 'id': booking_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bookings/<int:booking_id>', methods=['PUT'])
def update_booking(booking_id):
    try:
        data = request.get_json()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Проверяем существование записи
        cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        
        allowed_fields = ['status', 'notes']
        update_fields = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = ?")
                params.append(data[field])
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        params.append(booking_id)
        cursor.execute(f"UPDATE bookings SET {', '.join(update_fields)} WHERE id = ?", params)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Booking updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для заказов (корзина)
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        required_fields = ['customer_name', 'customer_phone', 'total_amount', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (customer_name, customer_phone, total_amount, items_json)
            VALUES (?, ?, ?, ?)
        ''', (
            data['customer_name'],
            data['customer_phone'],
            data['total_amount'],
            json.dumps(data['items'])
        ))
        
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Order created successfully', 'id': order_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        order = row_to_order(row)
        conn.close()
        return jsonify({'success': True, 'data': order})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для блога
@app.route('/api/blog', methods=['GET'])
def get_blog_posts():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        category = request.args.get('category', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 6))
        offset = (page - 1) * per_page
        
        query = "SELECT * FROM blog_posts WHERE published = TRUE"
        params = []
        
        if category != 'all':
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor.execute(query, params)
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row[0],
                'title': row[1],
                'excerpt': row[2],
                'content': row[3],
                'category': row[4],
                'author': row[5],
                'read_time': row[6],
                'image_url': row[7],
                'views': row[9],
                'created_at': row[10]
            })
        
        # Общее количество
        count_query = "SELECT COUNT(*) FROM blog_posts WHERE published = TRUE"
        if category != 'all':
            count_query += " AND category = ?"
            cursor.execute(count_query, (category,))
        else:
            cursor.execute(count_query)
        
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': posts,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blog/<int:post_id>', methods=['GET'])
def get_blog_post(post_id):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Увеличиваем счетчик просмотров
        cursor.execute("UPDATE blog_posts SET views = views + 1 WHERE id = ?", (post_id,))
        
        cursor.execute("SELECT * FROM blog_posts WHERE id = ? AND published = TRUE", (post_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Post not found'}), 404
        
        post = {
            'id': row[0],
            'title': row[1],
            'excerpt': row[2],
            'content': row[3],
            'category': row[4],
            'author': row[5],
            'read_time': row[6],
            'image_url': row[7],
            'views': row[9],
            'created_at': row[10]
        }
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'data': post})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для галереи
@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        category = request.args.get('category', 'all')
        
        query = "SELECT * FROM gallery WHERE active = TRUE"
        params = []
        
        if category != 'all':
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY featured DESC, created_at DESC"
        
        cursor.execute(query, params)
        gallery_items = []
        for row in cursor.fetchall():
            gallery_items.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'category': row[3],
                'image_url': row[4],
                'featured': bool(row[5]),
                'created_at': row[7]
            })
        
        conn.close()
        return jsonify({'success': True, 'data': gallery_items})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Роуты для контактов
@app.route('/api/contacts', methods=['POST'])
def create_contact():
    try:
        data = request.get_json()
        
        required_fields = ['name', 'email', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO contacts (name, email, phone, message)
            VALUES (?, ?, ?, ?)
        ''', (
            data['name'],
            data['email'],
            data.get('phone', ''),
            data['message']
        ))
        
        conn.commit()
        contact_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'message': 'Message sent successfully', 'id': contact_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Статистика
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM services WHERE active = TRUE")
        services_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE approved = TRUE")
        reviews_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = 'completed'")
        completed_bookings = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(rating) FROM reviews WHERE approved = TRUE")
        avg_rating = cursor.fetchone()[0] or 0
        
        # Статистика по услугам
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM services 
            WHERE active = TRUE 
            GROUP BY category
        ''')
        services_by_category = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'services_count': services_count,
                'reviews_count': reviews_count,
                'completed_bookings': completed_bookings,
                'average_rating': round(float(avg_rating), 1),
                'services_by_category': services_by_category
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)