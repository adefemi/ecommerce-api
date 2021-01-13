import graphene
from .models import User, ImageUpload, UserProfile, UserAddress
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


class ImageUploadType(DjangoObjectType):
    image = graphene.String()

    class Meta:
        model = ImageUpload

    def resolve_image(self, info):
        if self.image:
            return "{}{}{}".format(settings.S3_BUCKET_URL, settings.MEDIA_URL, self.image)
        return None


class UserProfileType(DjangoObjectType):

    class Meta:
        model = UserProfile


class UserAddressType(DjangoObjectType):

    class Meta:
        model = UserAddress


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
    profile_picture = graphene.String()
    country_code = graphene.String()


class CreateUserProfile(graphene.Mutation):
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput()
        dob = graphene.Date(required=True)
        phone = graphene.Int(required=True)

    @is_authenticated
    def mutate(self, info, profile_data, **kwargs):
        user_profile = UserProfile.objects.create(
            user_id = info.context.user.id,
            **profile_data, **kwargs
        )

        return CreateUserProfile(
            user_profile=user_profile
        )


class UpdateUserProfile(graphene.Mutation):
    user_profile = graphene.Field(UserProfileType)

    class Arguments:
        profile_data = UserProfileInput()
        dob = graphene.Date()
        phone = graphene.Int()

    @is_authenticated
    def mutate(self, info, profile_data, **kwargs):
        try:
            info.context.user.user_profile
        except Exception:
            raise Exception("You don't have a profile to update")

        UserProfile.objects.filter(user_id=info.context.user.id).update(**profile_data, **kwargs)

        return UpdateUserProfile(
            user_profile = info.context.user.user_profile
        )


class AddressInput(graphene.InputObjectType):
    street = graphene.String()
    city = graphene.String()
    state = graphene.String()
    country = graphene.String()


class CreateUserAddress(graphene.Mutation):
    address = graphene.Field(UserAddressType)

    class Arguments:
        address_data = AddressInput(required=True)
        is_default = graphene.Boolean()

    @is_authenticated
    def mutate(self, info, address_data, is_default=False):
        try:
            user_profile_id = info.context.user.user_profile.id
        except Exception:
            raise Exception("You need a profile to create an address")

        existing_addresses = UserAddress.objects.filter(user_profile_id=user_profile_id)

        if is_default:
            existing_addresses.update(is_default=False)

        address = UserAddress.objects.create(
            user_profile_id=user_profile_id,
            is_default=is_default,
            **address_data
        )

        return CreateUserAddress(
            address=address
        )

        
class UpdateUserAddress(graphene.Mutation):
    address = graphene.Field(UserAddressType)

    class Arguments:
        address_data = AddressInput()
        is_default = graphene.Boolean()
        address_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, address_data, address_id, is_default=False):
        profile_id = info.context.user.user_profile.id

        UserAddress.objects.filter(
            user_profile_id = profile_id,
            id=address_id
        ).update(is_default=is_default, **address_data)

        if is_default:
            UserAddress.objects.filter(
                user_profile_id=profile_id).exclude(id=address_id).update(is_default=False)

        return UpdateUserAddress(
            address = UserAddress.objects.get(id=address_id)
        )


class DeleteUserAddress(graphene.Mutation):
    status = graphene.Boolean()

    class Arguments:
        address_id = graphene.ID(required=True)

    @is_authenticated
    def mutate(self, info, address_id):
        UserAddress.objects.filter(
            user_profile_id = profile_id,
            id=address_id
        ).delete()

        return DeleteUserAddress(
            status=True
        )


class Query(graphene.ObjectType):
    users = graphene.Field(paginate(UserType), page=graphene.Int())
    image_uploads = graphene.Field(paginate(ImageUploadType), page=graphene.Int())
    me = graphene.Field(UserType)

    def resolve_users(self, info, **kwargs):
        return User.objects.filter(**kwargs)

    def resolve_image_uploads(self, info, **kwargs):
        return ImageUpload.objects.filter(**kwargs)

    @is_authenticated
    def resolve_me(self, info):
        return info.context.user


class Mutation(graphene.ObjectType):
    register_user = RegisterUser.Field()
    login_user = LoginUser.Field()
    get_access = GetAccess.Field()
    image_upload = ImageUploadMain.Field()
    create_user_profile = CreateUserProfile.Field()
    update_user_profile = UpdateUserProfile.Field()
    create_user_address = CreateUserAddress.Field()
    update_user_address = UpdateUserAddress.Field()
    delete_user_address = DeleteUserAddress.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
