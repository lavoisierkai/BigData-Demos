"""
Sample Data Generator for Data Lake Demo
========================================

Generates realistic sample data for testing the data lake architecture:
1. E-commerce transaction data
2. IoT sensor data
3. User activity logs
4. Customer demographics

Author: Data Architecture Demo
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import uuid
import random
from faker import Faker
import boto3
from typing import Dict, List
import argparse

fake = Faker()

def generate_ecommerce_data(num_records: int = 10000) -> pd.DataFrame:
    """Generate realistic e-commerce transaction data"""
    
    # Product categories and names
    categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Beauty']
    products = {
        'Electronics': ['Smartphone', 'Laptop', 'Headphones', 'Tablet', 'Smart Watch'],
        'Clothing': ['T-Shirt', 'Jeans', 'Dress', 'Shoes', 'Jacket'],
        'Books': ['Fiction Novel', 'Programming Book', 'Biography', 'Cookbook', 'Travel Guide'],
        'Home & Garden': ['Coffee Machine', 'Plant Pot', 'Bed Sheets', 'Kitchen Knife', 'Lamp'],
        'Sports': ['Running Shoes', 'Yoga Mat', 'Basketball', 'Protein Powder', 'Water Bottle'],
        'Beauty': ['Face Cream', 'Lipstick', 'Shampoo', 'Perfume', 'Nail Polish']
    }
    
    data = []
    customer_ids = [str(uuid.uuid4()) for _ in range(2000)]  # 2000 unique customers
    
    for _ in range(num_records):
        category = random.choice(categories)
        product_name = random.choice(products[category])
        
        record = {
            'transaction_id': str(uuid.uuid4()),
            'customer_id': random.choice(customer_ids),
            'customer_email': fake.email(),
            'product_id': str(uuid.uuid4()),
            'product_name': product_name,
            'product_category': category,
            'amount': round(random.uniform(10, 500), 2),
            'quantity': random.randint(1, 5),
            'timestamp': fake.date_time_between(start_date='-90d', end_date='now'),
            'customer_location': fake.city(),
            'payment_method': random.choice(['Credit Card', 'Debit Card', 'PayPal', 'Bank Transfer'])
        }
        data.append(record)
    
    return pd.DataFrame(data)

def generate_iot_sensor_data(num_records: int = 50000) -> List[Dict]:
    """Generate IoT sensor data in JSON format"""
    
    locations = ['Factory Floor A', 'Warehouse B', 'Office Building C', 'Retail Store D']
    device_types = ['Temperature Sensor', 'Humidity Sensor', 'Pressure Sensor', 'Multi Sensor']
    
    data = []
    sensor_ids = [f"SENSOR_{i:04d}" for i in range(100)]  # 100 unique sensors
    
    for _ in range(num_records):
        record = {
            'sensor_id': random.choice(sensor_ids),
            'device_type': random.choice(device_types),
            'timestamp': (datetime.now() - timedelta(
                hours=random.randint(0, 72)
            )).isoformat(),
            'temperature': round(random.uniform(18, 35), 2),
            'humidity': round(random.uniform(30, 80), 2),
            'pressure': round(random.uniform(980, 1020), 2),
            'location': random.choice(locations),
            'battery_level': round(random.uniform(10, 100), 1)
        }
        data.append(record)
    
    return data

def generate_user_activity_data(num_records: int = 25000) -> List[Dict]:
    """Generate user web activity data"""
    
    pages = ['/home', '/products', '/product/123', '/cart', '/checkout', '/profile', '/search']
    devices = ['Desktop', 'Mobile', 'Tablet']
    event_types = ['page_view', 'click', 'scroll', 'form_submit', 'search']
    
    data = []
    user_ids = [str(uuid.uuid4()) for _ in range(1000)]  # 1000 unique users
    
    for _ in range(num_records):
        record = {
            'user_id': random.choice(user_ids),
            'session_id': str(uuid.uuid4()),
            'event_type': random.choice(event_types),
            'timestamp': (datetime.now() - timedelta(
                hours=random.randint(0, 168)
            )).isoformat(),
            'page_url': random.choice(pages),
            'duration_seconds': random.randint(5, 300),
            'device_info': random.choice(devices),
            'location': fake.city()
        }
        data.append(record)
    
    return data

def save_to_local(data, filename: str, format_type: str = 'csv'):
    """Save data to local files"""
    if format_type == 'csv' and isinstance(data, pd.DataFrame):
        data.to_csv(filename, index=False)
    elif format_type == 'json':
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    print(f"Saved {filename}")

def upload_to_s3(data, bucket_name: str, key: str, format_type: str = 'csv'):
    """Upload data to S3"""
    s3_client = boto3.client('s3')
    
    if format_type == 'csv' and isinstance(data, pd.DataFrame):
        csv_buffer = data.to_csv(index=False)
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=csv_buffer)
    elif format_type == 'json':
        json_string = json.dumps(data, indent=2, default=str)
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=json_string)
    
    print(f"Uploaded to s3://{bucket_name}/{key}")

def main():
    parser = argparse.ArgumentParser(description='Generate sample data for data lake demo')
    parser.add_argument('--ecommerce-records', type=int, default=10000, 
                       help='Number of e-commerce records to generate')
    parser.add_argument('--iot-records', type=int, default=50000,
                       help='Number of IoT sensor records to generate')
    parser.add_argument('--activity-records', type=int, default=25000,
                       help='Number of user activity records to generate')
    parser.add_argument('--output-dir', default='./sample-data',
                       help='Output directory for local files')
    parser.add_argument('--s3-bucket', help='S3 bucket name for upload')
    parser.add_argument('--upload-to-s3', action='store_true',
                       help='Upload generated data to S3')
    
    args = parser.parse_args()
    
    print("Generating sample data...")
    
    # Generate e-commerce data
    print(f"Generating {args.ecommerce_records} e-commerce records...")
    ecommerce_data = generate_ecommerce_data(args.ecommerce_records)
    
    # Generate IoT sensor data
    print(f"Generating {args.iot_records} IoT sensor records...")
    iot_data = generate_iot_sensor_data(args.iot_records)
    
    # Generate user activity data
    print(f"Generating {args.activity_records} user activity records...")
    activity_data = generate_user_activity_data(args.activity_records)
    
    # Save locally
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    save_to_local(ecommerce_data, f"{args.output_dir}/ecommerce_transactions.csv", 'csv')
    save_to_local(iot_data, f"{args.output_dir}/iot_sensor_data.json", 'json')
    save_to_local(activity_data, f"{args.output_dir}/user_activity_data.json", 'json')
    
    # Upload to S3 if requested
    if args.upload_to_s3 and args.s3_bucket:
        print(f"Uploading to S3 bucket: {args.s3_bucket}")
        
        upload_to_s3(ecommerce_data, args.s3_bucket, 
                     'ecommerce/transactions/ecommerce_transactions.csv', 'csv')
        upload_to_s3(iot_data, args.s3_bucket,
                     'iot-data/sensor_readings.json', 'json')
        upload_to_s3(activity_data, args.s3_bucket,
                     'user-activity/activity_logs.json', 'json')
    
    print("Sample data generation completed!")
    print(f"Generated files in: {args.output_dir}")
    
    # Data summary
    print("\nData Summary:")
    print(f"E-commerce transactions: {len(ecommerce_data)} records")
    print(f"IoT sensor readings: {len(iot_data)} records")  
    print(f"User activity events: {len(activity_data)} records")
    print(f"Total records: {len(ecommerce_data) + len(iot_data) + len(activity_data)}")

if __name__ == "__main__":
    main()