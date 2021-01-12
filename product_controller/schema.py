import graphene
from graphene_django import DjangoObjectType
from .models import Category, Product, ProductComment, ProductImage, Wish, Cart, Business, RequestCart
from ecommerce_api.permissions import is_authenticated, paginate, get_query
from django.db.models import Q

class CategoryType(DjangoObjectType):

    class Meta:
        model = Category


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


class BusinessType(DjangoObjectType):
    
    class Meta:
        model = Business


class RequestType(DjangoObjectType):

    class Meta:
        model = RequestCart


class Query(graphene.ObjectType):
    categories = graphene.List(CategoryType, name=graphene.String())
    products = graphene.Field(paginate(ProductType), category=graphene.String(), min_prize=graphene.Float(), max_prize=graphene.Float(), search=graphene.String(), sort_by=graphene.String(), is_asc=graphene.Boolean())
    product = graphene.Field(ProductType, product_id=graphene.ID(required=True))

    def resolve_categories(self, info, name):
        query = Category.objects.prefetch_related("product_categories")
        if name:
            query = query.filter(Q(name__icontains=name) | Q(name__iexact=name)).distinct()
        return query

    def resolve_products(self, info, category, min_prize, max_prize, search, sort_by, is_asc=False):
        query = Product.objects.select_related("business", "category").prefetch_related("product_images", "product_comments", "product_wishes", "product_carts")

        if category:
            query = query.filter(Q(category__name__icontains=name) | Q(category__name__iexact=name)).distinct()

        if min_prize:
            query = query.filter(Q(price__gt=min_prize) | Q(price=min_prize)).distinct()

        if max_prize:
            query = query.filter(Q(price__lt=max_prize) | Q(price=max_prize)).distinct()

        if search:
            search_fields = (
                "name", "category__name", "price", "total_available"
            )
            q = self.get_query(search, search_fields)
            query = query.filter(q)

        if sort_by:
            data = sort_by
            if is_asc is True:
                data = f"-{data}"

            query = query.order_by(data)

        return query

    def resolve_product(self, info, product_id):
        return Product.objects.get(id=product_id)


class CreateCategory(graphene.Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        name = graphene.String(required=True)

    def mutate(self, info, name):
        cat = Category.objects.create(name=name)
        return CreateCategory(
            category=cat
        )


class CreateBusiness(graphene.Mutation):
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        buss = Business.objects.create(user_id=info.context.user.id, name=name)

        return CreateBusiness(
            business=buss
        )


class UpdateBusiness(graphene.Mutation):
    business = graphene.Field(BusinessType)

    class Arguments:
        name = graphene.String(required=True)

    @is_authenticated
    def mutate(self, info, name):
        buss = Business.objects.filter(user_id=info.context.user.id).update(name=name)

        return CreateBusiness(
            business=info.context.user.user_business
        )


class DeleteBusiness(graphene.Mutation):
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        buss = Business.objects.filter(user_id=info.context.user.id).delete()

        return DeleteBusiness(
            status=True
        )


class ProductInput(graphene.InputObjectType):
    category_id = graphene.ID()
    name = graphene.String()
    price = graphene.Float()
    total_count = graphene.Int()
    description = graphene.String()


class ProductImageInput(graphene.InputObjectType):
    image_id = graphene.ID()
    is_cover = graphene.Boolean()


class CreateProduct(graphene.Mutation):
    product = graphene.Field(ProductType)

    class Arguments:
        product_data = ProductInput(required=True)
        images = graphene.List(ProductImageInput)

    @is_authenticated
    def mutate(self, info, product_data, images):
        try:
            business_id = info.context.user.user_business.id
        except Exception:
            raise Exception("User does not have a business")

        product_data["total_available"] = product_data["total_count"]

        product = Product.objects.create(business_id=business_id, **product_data)

        ProductImage.objects.bulk_create(
            [ProductImage(product_id=product.id, **image_data) for image_data in images]
            )

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
    def mutate(self, info, product_id, product_data, **kwargs):
        product = Product.objects.filter(
            id=product_id, 
            business_id=info.context.user.user_business.id
            ).update(**product_data, **kwargs)

        return UpdateProduct(
            product=Product.objects.get(id=product_id)
        )

    
class DeleteProduct(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info):
        Product.objects.filter(
            id=product_id, 
            business_id=info.context.user.user_business.id
            ).delete()

        return DeleteBusiness(
            status=True
        )


class UpdateProductImage(graphene.Mutation):
    image = graphene.Field(ProductImageType)

    class Arguments:
        product_id = graphene.ID(required=True)
        image_data = ProductImageInput()
        default_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_id, image_data):
        image = ProductImage.objects.filter(
            id=default_id,
            product_id=product_id
        )

        if image_data["is_cover"] is True:
            ProductImage.objects.filter(
                product_id=product_id
            ).update(is_cover=False)

        image.update(**image_data)

        return UpdateProductImage(
            image = ProductImage.objects.get(id=default_id)
        )


class CreateProductComment(graphene.Mutation):
    product_comment = graphene.Field(ProductCommentType)

    class Arguments:
        product_id = graphene.ID(required=True)
        comment = graphene.String(required=True)
    
    @is_authenticated
    def mutate(self, info, product_id, comment):
        user_id = info.context.user.id

        comment_exist = ProductComment.objects.filter(user_id=user_id, product_id=product_id)

        if comment_exist:
            comment_exist.update(comment=comment)
            product_comment = ProductComment.objects.filter(user_id=user_id, product_id=product_id).first()
        else:
            product_comment = ProductComment.objects.create(user_id=user_id, product_id=product_id, comment=comment)

        return CreateProductComment(product_comment=product_comment)


class ToggleWish(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_id):

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise Exception("product with ID does not exist")

        try:
            user_wishes = info.context.user.user_wishes
        except Exception:
            user_wishes = Wish.objects.create(user_id=info.context.user.id)

        has_product = user_wishes.product.filter(id=product_id)

        if has_product:
            user_wishes.product.remove(product)

        else:
            user_wishes.product.add(product)

        return ToggleWish(
            status = True
        )

    
class HasWish(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        product_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, product_id):
        status = False

        try:
            user_wishes = info.context.user.user_wishes
        except Exception:
            user_wishes = Wish.objects.create(user_id=info.context.user.id)

        has_product = user_wishes.product.filter(id=product_id)

        if has_product:
            status = True

        return HasWish(
            status=status
        )


class CreateCart(graphene.Mutation):
    cart_item = graphene.Field(CartType)

    class Arguments:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int()

    @is_authenticated
    def mutate(self, info, product_id, **kwargs):
        user_id = info.context.user.id

        cart = Cart.objects.filter(user_id=user_id, product_id=product_id)

        if cart:
            cart.update(**kwargs)
            cart = Cart.objects.filter(user_id=user_id, product_id=product_id).first()
        else:
            cart = Cart.objects.create(user_id=user_id, product_id=product_id, **kwargs)

        return CreateCart(
            cart_item = cart
        )


class DeleteCartItem(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        cart_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, cart_id):
        Cart.objects.filter(id=cart_id, user_id=info.context.user.id).delete()

        return DeleteCartItem(
            status=True
        )


class CompletePayment(graphene.Mutation):
    status = graphene.Boolean()

    @is_authenticated
    def mutate(self, info):
        cart_items = Cart.objects.filter(user_id=info.context.user.id)

        RequestCart.objects.bulk_create(
            [
                RequestCart(
                    product_id=cart_item.product.id,
                    business_id=cart_item.product.business.id,
                    user_id = info.context.user.id
                ) for cart_item in cart_items
            ]
        )

        cart_items.delete()

        return CompletePayment(status=True)


class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    create_business = CreateBusiness.Field()
    update_business = UpdateBusiness.Field()
    delete_business = DeleteBusiness.Field()
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    update_product_image = UpdateProductImage.Field()
    create_product_comment = CreateProductComment.Field()
    toggle_wish = ToggleWish.Field()
    has_wish = HasWish.Field()
    create_cart = CreateCart.Field()
    delete_cart_item = DeleteCartItem.Field()
    complete_payment = CompletePayment.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
            