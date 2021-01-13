from django.db import models
from user_controller.models import ImageUpload, User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Business(models.Model):
    user = models.OneToOneField(User, related_name="user_business", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="product_categories", on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name="business_products", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.FloatField()
    total_available = models.PositiveIntegerField()
    total_count = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} - {self.name}"

    class Meta:
        ordering = ("-created_at",)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="product_images", on_delete=models.CASCADE)
    image = models.ForeignKey(ImageUpload, related_name="image_product", on_delete=models.CASCADE)
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.business.name} - {self.product.name} - {self.image}"


class ProductComment(models.Model):
    product = models.ForeignKey(Product, related_name="product_comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_comments", on_delete=models.CASCADE)
    comment = models.TextField()
    rate = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)


class Wish(models.Model):
    user = models.OneToOneField(User, related_name="user_wish", on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name="products_wished")
    created_at = models.DateTimeField(auto_now_add=True)


class Cart(models.Model):
    product = models.ForeignKey(Product, related_name="product_carts", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_carts", on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"

    class Meta:
        ordering = ("-created_at",)


class RequestCart(models.Model):
    user = models.ForeignKey(User, related_name="user_requests", on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name="business_requests", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="product_requests", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

