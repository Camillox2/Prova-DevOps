from flask import Flask, jsonify
import redis
import requests
import mysql.connector
import os

app = Flask(__name__)
cache = redis.Redis(host=os.environ.get('REDIS_HOST', 'redis'), port=6379)

@app.route('/order')
def create_order():
    cached_product_data = cache.get('selected_product')
    product_to_order = None

    if cached_product_data:
        product_to_order = eval(cached_product_data)
    else:
        products_api_url = f"http://{os.environ.get('PRODUCTS_API_HOST', 'products')}:3001/products"
        response = requests.get(products_api_url)
        products_data = response.json()['products']
        if len(products_data) > 1:
            product_to_order = products_data[1]
        elif len(products_data) == 1:
            product_to_order = products_data[0]
        else:
            return jsonify({"error": "No products available"}), 500
        
        cache.set('selected_product', str(product_to_order))

    db_connection = None
    order_id = None
    quantity_ordered = 3
    total_order_price = product_to_order['price'] * quantity_ordered

    try:
        db_connection = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'db'),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', 'pass'),
            database=os.environ.get('MYSQL_DATABASE', 'ecommerce')
        )
        cursor = db_connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY, 
                product_id INT, 
                product_name VARCHAR(255),
                quantity INT, 
                total_price DECIMAL(10, 2)
            )
        """)
        
        sql_insert_query = "INSERT INTO orders (product_id, product_name, quantity, total_price) VALUES (%s, %s, %s, %s)"
        insert_tuple = (product_to_order['id'], product_to_order['name'], quantity_ordered, total_order_price)
        
        cursor.execute(sql_insert_query, insert_tuple)
        db_connection.commit()
        order_id = cursor.lastrowid
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()

    if order_id is None:
        return jsonify({"error": "Failed to create order"}), 500

    return jsonify({
        "order_id": order_id,
        "product_id": product_to_order['id'],
        "product_name": product_to_order['name'],
        "quantity": quantity_ordered,
        "total_price": total_order_price
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)