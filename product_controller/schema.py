import graphene
from graphene_django import DjangoObjectType
from ecommerce_api.permissions import paginate, is_authenticated, get_query
from django.db.models import Q

from .models import (
    Category, Business, Product, ProductComment, 
    ProductImage, Wish, Cart, RequestCart
) 


class CategoryType(DjangoObjectType):
    count = graphene.Int()

    class Meta:
        model = Category

    def resolve_count(self, info):
        return self.product_categories.count()



class BusinessType(DjangoObjectType):
    
    class Meta:
        model = Business


class ProductType(DjangoObjectType):
    
    class Meta:
        model = Product


class ProductCommentType(DjangoObjectType):
    
    class Meta:
        model = ProductComment


class ProductImageType(DjangoObjectType):
    
    class Meta:
        model = ProductImage


class WishType(DjangoObjectType):
    
    class Meta:
        model = Wish


class CartType(DjangoObjectType):
    
    class Meta:
        model = Cart


class RequestCartType(DjangoObjectType):
    
    class Meta:
        model = RequestCart


class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType, name=graphene.String())
    products = graphene.Field(paginate(ProductType), search=graphene.String(),
     min_price=graphene.Float(), max_price=graphene.Float(), category=graphene.String(),
     business=graphene.String(), sort_by=graphene.String(), is_asc=graphene.Boolean(), mine=graphene.Boolean())
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    carts = graphene.List(CartType, name=graphene.String())
    request_carts = graphene.List(RequestCartType, name=graphene.String())

    def resolve_categories(self, info, name=False):
        query = Category.objects.prefetch_related("product_categories")

        if name:
            query = query.filter(Q(name__icontains=name) | Q(name__iexact=name)).distinct()

        return query

    @is_authenticated
    def resolve_carts(self, info, name=False):
        query = Cart.objects.select_related("user", "product").filter(user_id=info.context.user.id)

        if name:
            query = query.filter(Q(product__name__icontains=name) | Q(product__name__iexact=name)).distinct()

        return query

    @is_authenticated
    def resolve_request_carts(self, info, name=False):
        query = RequestCart.objects.select_related(
            "user", "product", "business").filter(business__user_id=info.context.user.id)

        if name:
            query = query.filter(Q(product__name__icontains=name) | Q(product__name__iexact=name)).distinct()

        return query

    def resolve_products(self, info, **kwargs):

        mine = kwargs.get("mine", False)
        if mine and not info.context.user:
            raise Exception("User auth required")


        query = Product.objects.select_related("category", "business").prefetch_related(
            "product_images", "product_comments", "products_wished", "product_carts", "product_requests"
        )

        if mine:
            query = query.filter(business__user_id=info.context.user.id)

        if kwargs.get("search", None):
            qs = kwargs["search"]
            search_fields = (
                "name", "description", "category__name"
            )

            search_data = get_query(qs, search_fields)
            query = query.filter(search_data)

        if kwargs.get("min_price", None):
            qs = kwargs["min_price"]

            query = query.filter(Q(price__gt=qs) | Q(price=qs)).distinct()

        if kwargs.get("max_price", None):
            qs = kwargs["max_price"]

            query = query.filter(Q(price__lt=qs) | Q(price=qs)).distinct()

        if kwargs.get("category", None):
            qs = kwargs["category"]

            query = query.filter(Q(category__name__icontains=qs) 
            | Q(category__name__iexact=qs)).distinct()

        if kwargs.get("business", None):
            qs = kwargs["business"]

            query = query.filter(Q(business__name__icontains=qs) 
            | Q(business__name__iexact=qs)).distinct()

        if kwargs.get("sort_by", None):
            qs = kwargs["sort_by"]
            is_asc = kwargs.get("is_asc", False)
            if not is_asc:
                qs = f"-{qs}"
            query = query.order_by(qs)

        return query

    def resolve_product(self, info, id):
        query = Product.objects.select_related("category", "business").prefetch_related(
            "product_images", "product_comments", "products_wished", "product_carts", "product_requests"
        ).get(id=id)

        return query


class CreateBusiness(graphene.Mutation):
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        buss = Business.objects.create(name=name, user_id=info.context.user.id)

        return CreateBusiness(
            business=buss
        )


class UpdateBusiness(graphene.Mutation):
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        try:
            instance = info.context.user.user_business
        except Exception:
            raise Exception("You does not have a business to update")

        instance.name = name
        instance.save()

        return UpdateBusiness(
            business=instance
        )


class DeleteBusiness(graphene.Mutation):
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        Business.objects.filter(user_id=info.context.user.id).delete()

        return DeleteBusiness(
            status=True
        )


class ProductInput(graphene.InputObjectType):
    name = graphene.String()
    price = graphene.Float()
    description = graphene.String()
    category_id = graphene.ID()

class ProductImageInput(graphene.InputObjectType):
    image_id = graphene.ID(required=True)
    is_cover = graphene.Boolean()


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput(required=True)
        total_count = graphene.Int(required=True)
        images = graphene.List(ProductImageInput)

    @is_authenticated
    def mutate(self, info, total_count, product_data, images, **kwargs):
        try:
            buss_id = info.context.user.user_business.id
        except Exception:
            raise Exception("You do not have a business")

        have_product = Product.objects.filter(business_id=buss_id, name=product_data["name"])
        if have_product:
            raise Exception("You already have a product with this name")

        product_data["total_available"] = total_count
        product_data["total_count"] = total_count
        product_data["business_id"] = buss_id

        product = Product.objects.create(**product_data, **kwargs)

        ProductImage.objects.bulk_create([
            ProductImage(product_id=product.id, **image_data) for image_data in images
        ])

        return CreateProduct(
            product=product
        )


class UpdateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput()
        total_available = graphene.Int()
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_data, product_id, **kwargs):
        try:
            buss_id = info.context.user.user_business.id
        except Exception:
            raise Exception("You do not have a business")

        if product_data.get("name", None):
            have_product = Product.objects.filter(business_id=buss_id, name=product_data["name"])
            if have_product:
                raise Exception("You already have a product with this name")

        Product.objects.filter(id=product_id, business_id=buss_id).update(**product_data, **kwargs)

        return UpdateProduct(
            product=Product.objects.get(id=product_id)
        )


class DeleteProduct(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_id):
        Product.objects.filter(id=product_id, business_id=info.context.user.user_business.id).delete()

        return DeleteProduct(
            status=True
        )


class UpdateProductImage(graphene.Mutation):
    image = graphene.Field(ProductImageType)

    class Arguments:
        image_data = ProductImageInput()
        id = graphene.ID(required=True)
    
    @is_authenticated
    def mutate(self, info, image_data, id):
        try:
            buss_id = info.context.user.user_business.id
        except Exception:
            raise Exception("You do not have a business, access denied.")

        my_image = ProductImage.objects.filter(product__business_id=buss_id, id=id)
        if not my_image:
            raise Exception("You do not own this product")

        my_image.update(**image_data)
        if image_data.get("is_cover", False):
            ProductImage.objects.filter(product__business_id=buss_id).exclude(id=id).update(is_cover=False)

        return UpdateProductImage(
            image = ProductImage.objects.get(id=id)
        )


class CreateProductComment(graphene.Mutation):
    product_comment = graphene.Field(ProductCommentType)

    class Arguments:
        product_id = graphene.ID(required=True)
        comment = graphene.String(required=True)
        rate = graphene.Int()

    @is_authenticated
    def mutate(self, info, product_id, **kwargs):
        user_buss_id = None
        try:
            user_buss_id = info.context.user.user_business.id
        except Exception:
            pass

        if user_buss_id:
            own_product = Product.objects.filter(business_id=user_buss_id, id=product_id)
            if own_product:
                raise Exception("You cannot comment on you product")

        ProductComment.objects.filter(user=info.context.user.id, product_id=product_id).delete()

        pc = ProductComment.objects.create(product_id=product_id, **kwargs)

        return CreateProduct(
            product_comment = pc
        )


class HandleWishList(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)
        is_check = graphene.Boolean()

    @is_authenticated
    def mutate(self, info, product_id, is_check=False):
        try:
            product = Product.objects.get(id=product_id)
        except Exception:
            raise Exception("Product with product_id does not exist")

        try:
            user_wish = info.context.user.user_wish
        except Exception:
            user_wish = Wish.objects.create(user_id=info.context.user.id)

        has_product = user_wish.products.filter(id=product_id)

        if has_product:
            if is_check:
                return HandleWishList(status=True)
            user_wish.products.remove(product)
        else:
            if is_check:
                return HandleWishList(status=False)
            user_wish.products.add(product)

        return HandleWishList(status=True)


class CreateCartItem(graphene.Mutation):
    cart_item = graphene.Field(CartType)

    class Arguments:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int()

    @is_authenticated
    def mutate(self, info, product_id, **kwargs):
        Cart.objects.filter(product_id=product_id, user_id=info.context.user.id).delete()

        cart_item = Cart.objects.create(product_id=product_id, user_id=info.context.user.id, **kwargs)

        return CreateCartItem(
            cart_item=cart_item
        )


class UpdateCartItem(graphene.Mutation):
    cart_item = graphene.Field(CartType)

    class Arguments:
        cart_id = graphene.ID(required=True)
        quantity = graphene.Int(required=True)

    @is_authenticated
    def mutate(self, info, cart_id, **kwargs):
        Cart.objects.filter(id=cart_id, user_id=info.context.user.id).update(**kwargs)

        return UpdateCartItem(
            cart_item = Cart.objects.get(id=cart_id)
        )


class DeleteCartItem(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        cart_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, cart_id):
        Cart.objects.filter(id=cart_id, user_id=info.context.user.id).delete()

        return DeleteCartItem(
            status = True
        )


class CompletePayment(graphene.Mutation):
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        user_carts = Cart.objects.filter(user_id=info.context.user.id)

        RequestCart.objects.bulk_create([
            RequestCart(
                user_id=info.context.user.id,
                business_id=cart_item.product.business.id,
                product_id=cart_item.product.id,
                quantity=cart_item.quantity,
                price=cart_item.quantity * cart_item.product.price
            ) for cart_item in user_carts
        ])

        user_carts.delete()

        return CompletePayment(
            status=True
        )



class Mutation(graphene.ObjectType):
    create_business = CreateBusiness.Field()
    update_business = UpdateBusiness.Field()
    delete_business = DeleteBusiness.Field()
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    update_product_image = UpdateProductImage.Field()
    create_product_comment = CreateProductComment.Field()
    handle_wish_list = HandleWishList.Field()
    create_cart_item = CreateCartItem.Field()
    update_cart_item = UpdateCartItem.Field()
    delete_cart_item = DeleteCartItem.Field()
    complete_payment = CompletePayment.Field()



schema = graphene.Schema(query=Query, mutation=Mutation)