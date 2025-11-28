import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path='grooming_salon.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица услуг
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price INTEGER NOT NULL,
                category TEXT NOT NULL,
                duration INTEGER DEFAULT 60,
                popular BOOLEAN DEFAULT FALSE,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица отзывов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_name TEXT NOT NULL,
                author_avatar TEXT,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                review_text TEXT NOT NULL,
                service_name TEXT,
                pet_type TEXT,
                approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица записей на услуги
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_email TEXT,
                pet_name TEXT NOT NULL,
                pet_breed TEXT NOT NULL,
                service_name TEXT NOT NULL,
                service_price INTEGER NOT NULL,
                booking_date DATE NOT NULL,
                booking_time TEXT NOT NULL,
                status TEXT DEFAULT 'pending', -- pending, confirmed, completed, cancelled
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица заказов (корзина)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                total_amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending', -- pending, paid, completed, cancelled
                items_json TEXT NOT NULL, -- JSON с товарами
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица статей блога
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT NOT NULL,
                author TEXT NOT NULL,
                read_time TEXT NOT NULL,
                image_url TEXT,
                published BOOLEAN DEFAULT TRUE,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица галереи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gallery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                image_url TEXT,
                featured BOOLEAN DEFAULT FALSE,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица контактов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                message TEXT NOT NULL,
                responded BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Вставляем начальные данные
        self.insert_initial_data(cursor)
        
        conn.commit()
        conn.close()
    
    def insert_initial_data(self, cursor):
        """Вставка начальных данных в базу"""
        
        # Проверяем, есть ли уже услуги
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            services = [
                ('Комплексный груминг', 'Полный комплекс услуг по уходу за шерстью, кожей и когтями вашего питомца', 1500, 'grooming', 120, True),
                ('Стрижка и укладка', 'Профессиональная стрижка по породе или индивидуальному запросу с последующей укладкой', 1200, 'grooming', 90, True),
                ('Гигиенический уход', 'Стрижка когтей, чистка ушей и глаз, уход за кожей', 800, 'hygiene', 60, False),
                ('Чистка зубов', 'Профессиональная чистка зубов и уход за полостью рта', 700, 'hygiene', 30, False),
                ('SPA-процедуры', 'Массаж, маски, ароматерапия для вашего питомца', 1000, 'spa', 90, True),
                ('Обработка от паразитов', 'Защита от блох и клещей безопасными средствами', 600, 'health', 30, False),
                ('Тримминг', 'Выщипывание отмершей шерсти для жесткошерстных пород', 900, 'grooming', 75, False),
                ('Экспресс-линька', 'Ускоренное выведение шерсти в период линьки', 1100, 'grooming', 60, False),
                ('Уход за лапами', 'Стрижка когтей, уход за подушечками лап', 500, 'hygiene', 30, False),
                ('Уход за глазами', 'Очистка, удаление слезных дорожек', 400, 'hygiene', 20, False),
                ('Уход за ушами', 'Чистка ушных раковин, удаление шерсти', 450, 'hygiene', 25, False),
                ('Аромарасчесывание', 'Расчесывание с аромамаслами для блеска шерсти', 650, 'spa', 45, False)
            ]
            
            cursor.executemany(
                "INSERT INTO services (name, description, price, category, duration, popular) VALUES (?, ?, ?, ?, ?, ?)",
                services
            )
        
        # Начальные отзывы
        cursor.execute("SELECT COUNT(*) FROM reviews")
        if cursor.fetchone()[0] == 0:
            reviews = [
                ('Анна К.', 'АК', 5, 'Очень довольна услугами салона! Моего пуделя стригут просто идеально. Персонал внимательный и заботливый.', 'Стрижка и укладка', 'собака'),
                ('Игорь П.', 'ИП', 5, 'Привожу своего кота уже больше года. Всегда отличный результат! Спасибо за профессионализм.', 'Комплексный груминг', 'кот'),
                ('Марина С.', 'МС', 5, 'Лучший груминг-салон в городе! Цены адекватные, качество на высоте. Мой шпиц всегда выглядит ухоженным.', 'Комплексный груминг', 'собака'),
                ('Дмитрий В.', 'ДВ', 4, 'Хороший салон, качественные услуги. Единственное, пришлось немного подождать в очереди.', 'Гигиенический уход', 'собака'),
                ('Ольга М.', 'ОМ', 5, 'Впервые привела свою собаку на груминг и осталась очень довольна. Специалисты знают свое дело.', 'Комплексный груминг', 'собака')
            ]
            
            cursor.executemany(
                "INSERT INTO reviews (author_name, author_avatar, rating, review_text, service_name, pet_type, approved) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(r[0], r[1], r[2], r[3], r[4], r[5], True) for r in reviews]
            )
        
        # Начальные статьи блога
        cursor.execute("SELECT COUNT(*) FROM blog_posts")
        if cursor.fetchone()[0] == 0:
            blog_posts = [
                (
                    'Как правильно ухаживать за шерстью собаки в домашних условиях',
                    'Полное руководство по уходу за шерстью вашего питомца с профессиональными советами от наших грумеров.',
                    'Правильный уход за шерстью собаки - это не только вопрос эстетики, но и важная составляющая здоровья вашего питомца...',
                    'care',
                    'Мария Иванова',
                    '8 мин'
                ),
                (
                    'Топ-5 ошибок в питании собак, которые допускают владельцы',
                    'Узнайте, какие распространенные ошибки в кормлении могут навредить здоровью вашего питомца.',
                    'Правильное питание - основа здоровья и долголетия вашего питомца. К сожалению, многие владельцы допускают серьезные ошибки...',
                    'nutrition',
                    'Алексей Петров',
                    '6 мин'
                ),
                (
                    'Как подготовить питомца к зиме: советы грумеров',
                    'Сезонные рекомендации по уходу за шерстью, лапами и кожей вашего питомца в холодное время года.',
                    'Зима - особое время года, которое требует дополнительного ухода за вашим питомцем...',
                    'care',
                    'Ольга Сидорова',
                    '5 мин'
                )
            ]
            
            cursor.executemany(
                "INSERT INTO blog_posts (title, excerpt, content, category, author, read_time) VALUES (?, ?, ?, ?, ?, ?)",
                blog_posts
            )
        
        # Начальные данные галереи
        cursor.execute("SELECT COUNT(*) FROM gallery")
        if cursor.fetchone()[0] == 0:
            gallery_items = [
                ('Стрижка пуделя', 'Профессиональная стрижка пуделя в стиле "Лев"', 'dogs'),
                ('Груминг шпица', 'Комплексный уход за шерстью шпица', 'dogs'),
                ('Стрижка кота', 'Аккуратная стрижка персидского кота', 'cats'),
                ('SPA для собаки', 'Расслабляющие SPA-процедуры с аромамаслами', 'spa'),
                ('Гигиенический уход', 'Комплекс гигиенических процедур', 'grooming')
            ]
            
            cursor.executemany(
                "INSERT INTO gallery (title, description, category) VALUES (?, ?, ?)",
                gallery_items
            )

# Модели данных
class Service:
    def __init__(self, id, name, description, price, category, duration=60, popular=False):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.category = category
        self.duration = duration
        self.popular = popular
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'duration': self.duration,
            'popular': bool(self.popular)
        }

class Review:
    def __init__(self, id, author_name, author_avatar, rating, review_text, service_name, pet_type, approved=False, created_at=None):
        self.id = id
        self.author_name = author_name
        self.author_avatar = author_avatar
        self.rating = rating
        self.review_text = review_text
        self.service_name = service_name
        self.pet_type = pet_type
        self.approved = approved
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'author_name': self.author_name,
            'author_avatar': self.author_avatar,
            'rating': self.rating,
            'review_text': self.review_text,
            'service_name': self.service_name,
            'pet_type': self.pet_type,
            'approved': bool(self.approved),
            'created_at': self.created_at
        }

class Booking:
    def __init__(self, id, customer_name, customer_phone, pet_name, pet_breed, service_name, service_price, booking_date, booking_time, status='pending', notes=None, created_at=None):
        self.id = id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.pet_name = pet_name
        self.pet_breed = pet_breed
        self.service_name = service_name
        self.service_price = service_price
        self.booking_date = booking_date
        self.booking_time = booking_time
        self.status = status
        self.notes = notes
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'pet_name': self.pet_name,
            'pet_breed': self.pet_breed,
            'service_name': self.service_name,
            'service_price': self.service_price,
            'booking_date': self.booking_date,
            'booking_time': self.booking_time,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at
        }

class Order:
    def __init__(self, id, customer_name, customer_phone, total_amount, status='pending', items_json='', created_at=None):
        self.id = id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.total_amount = total_amount
        self.status = status
        self.items_json = items_json
        self.created_at = created_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'total_amount': self.total_amount,
            'status': self.status,
            'items': json.loads(self.items_json) if self.items_json else [],
            'created_at': self.created_at
        }