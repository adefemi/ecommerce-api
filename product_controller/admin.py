from django.contrib import admin
from .models import (
    Category, Business, Product, ProductComment, 
    ProductImage, Wish, Cart, RequestCart
) 


admin.site.register((
    Category, Business, Product, ProductComment, 
    ProductImage, Wish, Cart, RequestCart,
))
