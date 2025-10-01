#!/usr/bin/env python3
"""Product model definition."""

from datetime import datetime
from typing import Optional

class Product:
    """Product model class."""
    
    def __init__(self, name: str, price: float, product_id: Optional[int] = None):
        """Initialize product."""
        self.product_id = product_id
        self.name = name
        self.price = price
        self.created_at = datetime.now()
        self.in_stock = True
    
    def to_dict(self) -> dict:
        """Convert product to dictionary."""
        return {
            'product_id': self.product_id,
            'name': self.name,
            'price': self.price,
            'created_at': self.created_at.isoformat(),
            'in_stock': self.in_stock
        }
    
    def __str__(self) -> str:
        """String representation of product."""
        return f"Product(id={self.product_id}, name={self.name}, price=${self.price})"