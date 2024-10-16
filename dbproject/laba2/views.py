# views.py
import os
import re
import sqlite3
from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.apps import apps
from django.templatetags.static import static
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, PickupPoint, Client, Order, DiscountCard, Supplier
from django.http import HttpResponse
from django.templatetags.static import static
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt  # Імпортуємо для обходу CSRF
from django.shortcuts import redirect
from decimal import Decimal

def all_records_view(request):
    # Отримуємо всі моделі, які починаються з "laba2_"
    app_models = apps.get_app_config('laba2').get_models()
    
    # Словник для зберігання даних
    tables_data = {}

    for model in app_models:
        if model._meta.db_table.startswith('laba2_'):
            # Отримуємо назву таблиці без префіксу
            table_name = model._meta.db_table[len('laba2'):]

            # Отримуємо всі записи з моделі
            records = model.objects.all()

            # Додаємо назву таблиці та записи до словника
            tables_data[table_name] = records

    # Генеруємо HTML-контент
    html_content = """
    <html>
        <head>
            <meta charset="UTF-8">
            <title>All tables</title>
            <link rel="stylesheet" type="text/css" href="{css_url}">
        </head>
        <body>
    """.format(css_url=static('laba2/styles.css'))  # Підключаємо CSS

    for table_name, records in tables_data.items():
        # Замінюємо "_" на " " і робимо перші букви великими
        formatted_table_name = table_name.replace('_', ' ').title()
        html_content += f"<h2>Table: {formatted_table_name}</h2>"
        html_content += "<table border='1'><tr>"

        # Отримуємо заголовки стовпців
        columns = [field.name for field in records.model._meta.fields]
        for column in columns:
            formatted_column_name = column.replace('_', ' ').title()  # Форматуємо назву стовпця
            html_content += f"<th>{formatted_column_name}</th>"
        html_content += "</tr>"

        # Виводимо записи
        for record in records:
            html_content += "<tr>"
            for column in columns:
                value = getattr(record, column, 'N/A')  # Отримуємо значення або 'N/A'
                html_content += f"<td>{value}</td>"
            html_content += "</tr>"
        html_content += "</table>"

    html_content += """
        </body>
    </html>
    """
    return HttpResponse(html_content, content_type='text/html')

def upload_sql_file_view(request):
    if request.method == 'POST':
        sql_file = request.FILES.get('sql_file')

        if sql_file:
            # Зберігаємо файл у тимчасовому місці
            temp_file_path = os.path.join(settings.MEDIA_ROOT, sql_file.name)

            # Переконайтесь, що директорія існує
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

            with open(temp_file_path, 'wb+') as destination:
                for chunk in sql_file.chunks():
                    destination.write(chunk)

            # Виконуємо SQL запити
            connection = sqlite3.connect(settings.DATABASES['default']['NAME'])  # Ваша база даних
            cursor = connection.cursor()

            with open(temp_file_path, 'r') as f:
                sql_script = f.read()

                # Додаємо префікс laba2_ до назв таблиць
                sql_script = re.sub(r'\b(DiscountCard|Director|Client|Employee|Warehouse|Supplier|Product|Store|DeliveryService|PickupPoint|Manufacturer|Order)\b', r'laba2_\1', sql_script)

                # Розділяємо запити та обробляємо їх
                for statement in sql_script.split(';'):
                    statement = statement.strip()
                    if statement:  # Перевірка на пусті рядки
                        try:
                            # Замінюємо записи у таблицях
                            if statement.startswith('INSERT INTO'):
                                # Отримуємо назву таблиці
                                table_name = re.search(r'INSERT INTO (.+?) ', statement).group(1).strip()
                                table_name = f"{table_name}"

                                # Видаляємо всі записи з таблиці
                                cursor.execute(f'DELETE FROM {table_name};')

                            cursor.execute(statement)  # Виконуємо запит
                        except sqlite3.OperationalError as e:
                            print(f'Error executing statement: {statement} - {str(e)}')  # Виводимо помилку
                            continue  # Продовжуємо до наступного запиту
                        except sqlite3.IntegrityError as e:
                            print(f'Error executing statement: {statement} - {str(e)}')  # Виводимо помилку при конфлікті

                connection.commit()

            # Видаляємо тимчасовий файл
            os.remove(temp_file_path)
            return HttpResponse('SQL file processed successfully.')

    return render(request, 'laba2/upload_sql.html')

def home_view(request):
    return render(request, 'laba2/home.html')

def all_products_view(request):
    # Отримуємо всі продукти
    products = Product.objects.all()

    # Генеруємо HTML-контент
    html_content = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <title>Store</title>
            <link rel="stylesheet" type="text/css" href="{static('laba2/styles.css')}">
        </head>
        <body>
            <h1>Store</h1>
            <div class="product-container">
    """

    for product in products:
        # Динамічно додаємо інформацію про кожен продукт у форматі HTML
        html_content += f"""
            <div class="product">
                <div class="image-placeholder">Image Placeholder</div>
                <h2 class="name">{product.name}</h2>
                <p class="supplier">Supplier: {product.supplier}</p>
                <p class="price">Price: ${product.price}</p>
                <p class="description">{product.description}</p>
                <a href="/place-order/?article={product.article}" class="buy-button">Buy Now</a>
            </div>
        """

    html_content += """
            </div>
        </body>
    </html>
    """
    
    return HttpResponse(html_content, content_type='text/html')


def place_order(request):
    article = request.GET.get('article', None)

    if article:
        try:
            product = Product.objects.get(article=article)
            pickup_points = PickupPoint.objects.all()

            html_content = f"""
            <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Деталі Продукту</title>
                    <link rel="stylesheet" type="text/css" href="{static('laba2/styles.css')}">
                    <style>
                        .product-order {{
                            max-width: 777px;
                            border: 1px solid #ccc;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            display: flex;
                            flex-wrap: wrap; /* Додаємо цю властивість для переносу елементів вниз */
                            padding: 20px;
                        }}
                        .product {{
                            flex: 1;
                            max-width: 250px; /* Встановлюємо максимальну ширину */
                            margin-right: 20px; /* Відстань між продуктом і інформацією про замовлення */
                        }}
                        .order-info {{
                            flex: 1;
                        }}
                        .header {{
                            display: flex;
                            flex-direction: column; /* Розміщуємо заголовки вертикально */
                            align-items: flex-start; /* Вирівнюємо заголовки зліва */
                            margin-bottom: 20px; /* Відступ під заголовками */
                        }}
                    </style>
                </head>
                <body>
                    <h1>Product details</h1>
                    <h2>Your order</h2>
                    <div class="product-order">
                        <div class="product">
                            <div class="image-placeholder">Image Placeholder</div>
                            <h2 class="name">{product.name}</h2>
                            <p class="supplier">Supplier: {product.supplier}</p>
                            <p class="price">Price: ${product.price}</p>
                            <p class="description">{product.description}</p>
                        </div>
                        <div class="order-info">
                            <form action="/confirm-order/{product.article}/" method="post">
                                <input type="hidden" name="article" value="{product.article}">
                                <div>
                                    <label for="client-name">Client:</label>
                                    <input type="text" id="client-name" name="client_name" required>
                                </div>
                                <div>
                                    <label for="phone_number">Phone:</label>
                                    <input type="text" id="phone_number" name="phone_number">
                                </div>
                                <div>
                                    <label for="email">Email:</label>
                                    <input type="email" id="email" name="email">
                                </div>
                                <div>
                                    <label for="email">Delivery method:</label>
                                    <input type="text" id="delivery_method" name="delivery_method">
                                </div>
                                <div>
                                    <label for="payment-method">Payment Method:</label>
                                    <select id="payment-method" name="payment_method" required>
                                        <option value="Cash">Cash</option>
                                        <option value="Credit Card">Credit Card</option>
                                        <option value="PayPal">PayPal</option>
                                    </select>
                                </div>
                                <div>
                                    <label for="pickup-checkbox">Pickup?</label>
                                    <input type="checkbox" id="pickup-checkbox" name="pickup_checkbox">
                                </div>
                                <div>
                                    <label for="pickup-point">Pickup Point:</label>
                                    <select id="pickup-point" name="pickup_point">
                                        <option value="">Select a pickup point</option>
            """
            for point in pickup_points:
                html_content += f'<option value="{point.pickup_point_id}">{point.address}</option>'

            html_content += f"""
                                    </select>
                                </div>
                                <button type="submit" class="buy-button">Confirm order</button>
                            </form>
                        </div>
                    </div>
                </body>
            </html>
            """
            return HttpResponse(html_content, content_type='text/html')

        except Product.DoesNotExist:
            return HttpResponse("Товар не знайдено", status=404)
    else:
        return HttpResponse("Не вказано article", status=400)

@csrf_exempt  # Для тестування без CSRF токена
def confirm_order(request, article):
    if request.method == "POST":
        try:
            product = Product.objects.get(article=article)
        except Product.DoesNotExist:
            return HttpResponse("Товар не знайдено", status=404)

        client_name = request.POST.get('client_name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        payment_method = request.POST.get('payment_method')
        delivery_method = request.POST.get('delivery_method')
        pickup_checkbox = request.POST.get('pickup_checkbox')
        pickup_point = request.POST.get('pickup_point')

        # Знайти або створити клієнта за ім'ям
        client, created = Client.objects.get_or_create(
            full_name=client_name,
            defaults={
                'phone_number': phone_number,
                'email': email
            }
        )

        # Застосування знижки з картки
        discount = 0
        if client.discount_card_number:  # Якщо у клієнта є картка зі знижкою
            discount = client.discount_card_number.discount_amount

        # Логіка доставки
        if pickup_checkbox and pickup_point:
            delivery_method = "Pickup"
        elif not pickup_checkbox and not delivery_method:
            return HttpResponse("It is necessary to specify the method of delivery", status=400)

        # Розрахунок фінальної ціни з урахуванням знижки
        final_price = product.price * (Decimal(1) - discount / Decimal(100))

        # Генеруємо замовлення
        order = Order(
            order_date=timezone.now(),
            order_amount=final_price,  # Ціна продукту з урахуванням знижки
            payment_method=payment_method,
            client=client,
            delivery_method=delivery_method,
            responsible_employee_id=1,
            product=product
        )
        order.save()

        return redirect('order_confirmation', order_id=order.order_id)

    return HttpResponse("The method is not supported", status=405)

def order_confirmation(request, order_id):
    order = Order.objects.get(order_id=order_id)
    return HttpResponse(f"Thank you for your order! Your order ID: {order.order_id}")

def list_and_delete_suppliers(request):
    suppliers = Supplier.objects.all()

    if request.method == "POST":
        supplier_id = request.POST.get('supplier_id')
        if supplier_id:
            supplier = get_object_or_404(Supplier, supplier_id=supplier_id)
            supplier.delete()  # Видалення постачальника
            return redirect('list_and_delete_suppliers')  # Перенаправлення на ту ж сторінку

    return render(request, 'laba2/supplier_list.html', {'suppliers': suppliers})
