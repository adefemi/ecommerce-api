from .permissions import resolve_paginated


class CustomAuthMiddleware(object):
    def resolve(self, next, root, info, **kwargs):
        info.context.user = self.authorize_user(info)
        return next(root, info, **kwargs)

    @staticmethod
    def authorize_user(info):
        from .authentication import Authentication
        auth = Authentication(info.context)
        return auth.authenticate()


class CustomPaginationMiddleware(object):
    def resolve(self, next, root, info, **kwargs):
        try:
            is_paginated = info.return_type.name[-9:]
            is_paginated = is_paginated == "Paginated"
        except Exception:
            is_paginated = False

        if is_paginated:
            page = kwargs.pop("page", 1)
            return resolve_paginated(next(root, info, **kwargs).value, info, page)

        return next(root, info, **kwargs)
