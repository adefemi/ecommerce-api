import graphene
from .models import User, ImageUpload, UserProfile, AddressList
from graphene_django import DjangoObjectType
from django.contrib.auth import authenticate
from datetime import datetime
from ecommerce_api.authentication import TokenManager
from ecommerce_api.permissions import is_authenticated, paginate
from graphene_file_upload.scalars import Upload
from django.conf import settings


class UserType(DjangoObjectType):

    class Meta:
        model = User


class UserProfileType(DjangoObjectType):

    class Meta:
        model = UserProfile


class AddressListType(DjangoObjectType):

    class Meta:
        model = AddressList


class ImageUploadType(DjangoObjectType):
    image = graphene.String()

    class Meta:
        model = ImageUpload

    def resolve_image(self, info):
        if self.image:
            return "{}{}{}".format(settings.S3_BUCKET_URL, settings.MEDIA_URL, self.image)
        return None


class RegisterUser(graphene.Mutation):
    status = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)

    def mutate(self, info, email, password, **kwargs):
        User.objects.create_user(email, password, **kwargs)

        return RegisterUser(
            status=True,
            message="User created successfully"
        )


class LoginUser(graphene.Mutation):
    access = graphene.String()
    refresh = graphene.String()
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, email, password):
        user = authenticate(username=email, password=password)

        if not user:
            raise Exception("invalid credentials")

        user.last_login = datetime.now()
        user.save()

        access = TokenManager.get_access({"user_id": user.id})
        refresh = TokenManager.get_refresh({"user_id": user.id})

        return LoginUser(
            access=access,
            refresh=refresh,
            user=user
        )


class GetAccess(graphene.Mutation):
    access = graphene.String()

    class Arguments:
        refresh = graphene.String(required=True)

    def mutate(self, info, refresh):
        token = TokenManager.decode_token(refresh)

        if not token or token["type"] != "refresh":
            raise Exception("Invalid token or has expired")

        access = TokenManager.get_access({"user_id": token["user_id"]})

        return GetAccess(
            access=access
        )


class ImageUploadMain(graphene.Mutation):
    image = graphene.Field(ImageUploadType)

    class Arguments:
        image = Upload(required=True)

    def mutate(self, info, image):
        image = ImageUpload.objects.create(image=image)

        return ImageUploadMain(
            image=image
        )


class UserProfileInput(graphene.InputObjectType):
    profile_picture = graphene.ID()
    dob = graphene.Date()
    phone = graphene.Int()
    country_code = graphene.String()


class AddressInput(graphene.InputObjectType):
    street = graphene.String()
    city = graphene.String()
    state = graphene.String()
    country = graphene.String()
    is_default = graphene.Boolean()


class CreateAddress(graphene.Mutation):
    address = graphene.Field(AddressListType)

    class Arguments:
        address_data = AddressInput(required=True)

    @is_authenticated
    def mutate(self, info, address_data):
        try:
            user_profile_id = info.context.user.user_profile.id
        except Exception:
            raise Exception("User does not have a profile yet")

        address = AddressList.objects.filter(user_profile_id=user_profile_id)
        if not address:
            address_data["is_default"] = True
        
        if address and address_data["is_default"] is True:
            address.update(is_default=False)
        
        address = AddressList.objects.create(user_profile_id=user_profile_id, **address_data)

        return CreateAddress(
            address=address
        )


class UpdateAddress(graphene.Mutation):
    address = graphene.Field(AddressListType)

    class Arguments:
        address_data = AddressInput()
        address_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, address_data, address_id):
        address = AddressList.objects.filter(
            id=address_id, 
            user_profile_id=info.context.user.user_profile.id
            )

        if address_data["is_default"] is True:
            address.update(is_default=False)

        address.update(**address_data)

        return UpdateAddress(
            address=AddressList.objects.get(id=address_id)
        )


class CreateUserProfile(graphene.Mutation):
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput(required=True)

    @is_authenticated
    def mutate(self, info, profile_data):
        user_profile = UserProfile.objects.create(user_id=info.context.user.id, **profile_data)

        return CreateUserProfile(
            user_profile=user_profile
        )


class UpdateUserProfile(graphene.Mutation):
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput()

    @is_authenticated
    def mutate(self, info, profile_data):
        user_profile = UserProfile.objects.filter(user_id=info.context.user.id).update(**profile_data)

        return CreateUserProfile(
            user_profile=info.context.user.user_profile
        )
    


class Query(graphene.ObjectType):
    users = graphene.Field(paginate(UserType), page=graphene.Int())
    images = graphene.Field(paginate(ImageUploadType), page=graphene.Int())
    me = graphene.Field(UserType)
    user_profiles = graphene.Field(paginate(UserProfileType), page=graphene.Int())
    address_lists = graphene.Field(paginate(AddressListType), page=graphene.Int())

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(**kwargs)

    def resolve_images(self, info, **kwargs):
        return ImageUpload.objects.filter(**kwargs)

    @is_authenticated
    def resolve_me(self, info, **kwargs):
        return info.context.user

    def resolve_user_profiles(self, info, **kwargs):
        return UserProfile.objects.select_relate("user").filter(**kwargs)

    def resolve_address_lists(self, info, **kwargs):
        return AddressList.objects.select_relate("user_profile").filter(**kwargs)


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    login_user = LoginUser.Field()
    get_access = GetAccess.Field()
    image_upload = ImageUploadMain.Field()
    create_user_profile = CreateUserProfile.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_address = CreateAddress.Field()
    update_address = UpdateAddress.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
