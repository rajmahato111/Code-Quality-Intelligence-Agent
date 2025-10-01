#!/usr/bin/env python3
"""Product service layer."""

from typing import List, Optional
from models.product import Product
from utils.database import DatabaseManager

class ProductService:
    """Product business logic service."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize product service."""
        self.db = db_manager
    
    def add_product(self, product: Product) -> int:
        """Add a new product."""
        query = """
        INSERT INTO products (name, price, created_at, in_stock)
        VALUES (?, ?, ?, ?)
        """
        params = (
            product.name,
            product.price,
            product.created_at.isoformat(),
            product.in_stock
        )
        
        return self.db.execute_update(query, params)
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        query = "SELECT * FROM products WHERE product_id = ?"
        products = self.db.execute_query(query, (product_id,))
        
        if products:
            product_data = products[0]
            return Product(
                name=product_data['name'],
                price=product_data['price'],
                product_id=product_data['product_id']
            )
        
        return None
    
    def get_all_products(self) -> List[Product]:
        """Get all products in stock."""
        query = "SELECT * FROM products WHERE in_stock = 1"
        products_data = self.db.execute_query(query)
        
        products = []
        for product_data in products_data:
            product = Product(
                name=product_data['name'],
                price=product_data['price'],
                product_id=product_data['product_id']
            )
            products.append(product)
        
        return products
    
    def update_product(self, product: Product) -> bool:
        """Update product information."""
        query = """
        UPDATE products 
        SET name = ?, price = ?, in_stock = ?
        WHERE product_id = ?
        """
        params = (product.name, product.price, product.in_stock, product.product_id)
        
        rows_affected = self.db.execute_update(query, params)
        return rows_affected > 0
    
    def search_products(self, search_term: str) -> List[Product]:
        """Search products by name."""
        query = "SELECT * FROM products WHERE name LIKE ? AND in_stock = 1"
        products_data = self.db.execute_query(query, (f"%{search_term}%",))
        
        products = []
        for product_data in products_data:
            product = Product(
                name=product_data['name'],
                price=product_data['price'],
                product_id=product_data['product_id']
            )
            products.append(product)
        
        return products