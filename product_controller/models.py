from django.db import models
from user_controller.models import User, ImageUpload


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Business(models.Model):
    user = models.OneToOneField(User, related_name="user_business", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.name}"

    class Meta:
        ordering = ("-created_at",)


class Product(models.Model):
    business = models.ForeignKey(Business, related_name="business_products", on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name="product_categories", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    total_count = models.PositiveIntegerField()
    total_available = models.PositiveIntegerField()
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} - {self.name}"

    class Meta:
        ordering = ("-created_at",)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="product_images", on_delete=models.CASCADE)
    image = models.ForeignKey(ImageUpload, related_name="image_products", on_delete=models.CASCADE)
    is_cover = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.is_cover}"

    class Meta:
        ordering = ("-created_at",)


class ProductComment(models.Model):
    product = models.ForeignKey(Product, related_name="product_comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_comments", on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"

    class Meta:
        ordering = ("-created_at",)


class Wish(models.Model):
    product = models.ManyToManyField(Product, related_name="product_wishes")
    user = models.OneToOneField(User, related_name="user_wishes", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"


class Cart(models.Model):
    product = models.ForeignKey(Product, related_name="product_carts", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_carts", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.user.email}"

    class Meta:
        ordering = ("-created_at",)


class RequestCart(models.Model):
    product = models.ForeignKey(Product, related_name="product_requests", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="user_requests", on_delete=models.CASCADE)
    business = models.ForeignKey(Business, related_name="business_requests", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)




