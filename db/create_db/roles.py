import db
from db.models import (
    Roles,
    RolesInternalNames,
    Categories,
    Users,
    PublishedLessons,
    Accounts,
    # LessonsReviews,
    ArchiveLessons,
    DraftLessons,
)
from db.models.roles import (
    Permissions,
    Resources,
    ResourcesFilter,
    ResourcesFilterOperators,
    Actions,
    DynamicSources,
)
from db.models.lessons.common import LessonEdit
from bson import ObjectId


def create_all_roles():
    db.ROLES_COLLECTION.delete_many({})
    create_admin_role()
    viewer_role = create_viewer_role()
    editor_role = create_editor_role()
    create_institution_manager_role([viewer_role, editor_role])
    create_guest_role()


def create_guest_role():

    # There is not a real use for this resource filters
    # I need to think of a way to limit the categories for only categories that the current user
    # have lessons that he can see
    # In the meantime we will filter base on role name
    categories_permissions = Permissions(
        resource=Resources.CATEGORIES,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                field=Categories.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Categories that the user is allowed to see",
            ),
            ResourcesFilter(
                field=Categories.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Categories that the user is allowed to see from his role",
            ),
        ],
    )

    published_lessons_permissions = Permissions(
        resource=Resources.PUBLISHED_LESSONS,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                field=PublishedLessons.Fields.public,
                operator=ResourcesFilterOperators.EQUAL,
                value=True,
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that are public",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_lessons],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his own allowed lessons",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his own allowed categories",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his role allowed categories",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.lessons],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his role allowed lessons",
            ),
        ],
    )

    reviews_permissions = Permissions(
        resource=Resources.REVIEWS,
        actions=[Actions.READ, Actions.READ_MANY],
        # since only after viewing a lesson the user can review it,
        # and the token for viewing a lesson is only given to the user if he is allowed to view it
        # we can assume that the user is allowed to review the lesson
        # so we don't need to add any filters
        # TODO maybe add filter for reading reviews
        filters=[],
    )

    role = Roles(
        id=ObjectId("6425685d86bd12f19c2dec6c"),
        name="אורח",
        internal_name=RolesInternalNames.GUEST,
        permissions=[
            categories_permissions,
            published_lessons_permissions,
            reviews_permissions,
        ],
        managed_roles=[],
        require_account=False,
        rank=10000,
    )

    return db.ROLES_COLLECTION.insert_one(role.dict(to_db=True))


def create_admin_role():

    all_actions = [action for action in Actions]
    all_resources = [resource for resource in Resources]

    role = Roles(
        id=ObjectId("6374ba0c3e2f7c3c01811e92"),
        name="מנהל מערכת",
        internal_name=RolesInternalNames.ADMIN,
        permissions=[
            Permissions(resource=resource, actions=all_actions, filters=[])
            for resource in all_resources
        ],
        managed_roles="*",
        require_account=False,
        rank=0,
    )

    return db.ROLES_COLLECTION.insert_one(role.dict(to_db=True))


def create_viewer_role():

    # There is not a real use for this resource filters
    # I need to think of a way to limit the categories for only categories that the current user
    # have lessons that he can see
    # In the meantime we will filter base on role name
    categories_permissions = Permissions(
        resource=Resources.CATEGORIES,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[],
    )

    published_lessons_permissions = Permissions(
        resource=Resources.PUBLISHED_LESSONS,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                field=PublishedLessons.Fields.public,
                operator=ResourcesFilterOperators.EQUAL,
                value=True,
                is_or=True,
                description="Published lessons that are public",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_lessons],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his own allowed lessons",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his own allowed categories",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.account, Accounts.Fields.allowed_lessons],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his account allowed lessons",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[
                    Users.Fields.account,
                    Accounts.Fields.allowed_categories,
                ],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his account allowed categories",
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                description="Published lessons that the user is allowed to see from his role allowed categories",
            ),
        ],
    )

    reviews_permissions = Permissions(
        resource=Resources.REVIEWS,
        actions=[Actions.READ, Actions.CREATE, Actions.READ_MANY],
        # since only after viewing a lesson the user can review it,
        # and the token for viewing a lesson is only given to the user if he is allowed to view it
        # we can assume that the user is allowed to review the lesson
        # so we don't need to add any filters
        # TODO maybe add filter for reading reviews
        filters=[],
    )

    role = Roles(
        id=ObjectId("6374ba0d3e2f7c3c01811e94"),
        name="צופה",
        internal_name=RolesInternalNames.VIEWER,
        permissions=[
            categories_permissions,
            published_lessons_permissions,
            reviews_permissions,
        ],
        managed_roles=[],
        rank=1000,
    )

    res = db.ROLES_COLLECTION.insert_one(role.dict(to_db=True))

    role.id = res.inserted_id

    return role


def create_institution_manager_role(roles: list[Roles]):

    roles_permissions = Permissions(
        resource=Resources.ROLES,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                field=Roles.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.managed_roles],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ, Actions.READ_MANY],
                description="To allow to read only the roles that the user is allowed to manage",
            )
        ],
    )

    users_permissions = Permissions(
        resource=Resources.USERS,
        actions=[
            Actions.READ,
            Actions.UPDATE,
            Actions.DELETE,
            Actions.CREATE,
            Actions.READ_MANY,
        ],
        filters=[
            ResourcesFilter(
                field=Users.Fields.account,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.account, Accounts.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                description="To allow actions on users only from the same account",
            ),
            ResourcesFilter(
                field=Users.Fields.role,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.managed_roles],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.UPDATE, Actions.CREATE, Actions.UPDATE_LIMITES],
                description="Only allowed to update users with roles that are managed by the current user",
            ),
            ResourcesFilter(
                field=Users.Fields.allowed_categories,
                operator=ResourcesFilterOperators.EQUAL,
                value="*",
                apply_to=[Actions.UPDATE_LIMITES],
                description="To prevent updating the allowed categories of the user",
            ),
            ResourcesFilter(
                field=Users.Fields.allowed_lessons,
                operator=ResourcesFilterOperators.EQUAL,
                value="*",
                apply_to=[Actions.UPDATE_LIMITES],
                description="To prevent updating the allowed lessons of the user",
            ),
            ResourcesFilter(
                field=Users.Fields.allowed_categories,
                operator=ResourcesFilterOperators.EQUAL,
                value=[],
                apply_to=[Actions.CREATE_LIMITES],
                description="To prevent creating users with allowed categories, and since the default value is [], the provided value must be []",
            ),
            ResourcesFilter(
                field=Users.Fields.allowed_lessons,
                operator=ResourcesFilterOperators.EQUAL,
                value=[],
                apply_to=[Actions.CREATE_LIMITES],
                description="To prevent creating users with allowed lessons, and since the default value is [], the provided value must be []",
            ),
        ],
    )

    accounts_permissions = Permissions(
        resource=Resources.ACCOUNTS,
        actions=[Actions.READ, Actions.UPDATE],
        filters=[
            ResourcesFilter(
                field=Accounts.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.account, Accounts.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                description="To allow actions on accounts only from the same account",
            ),
            ResourcesFilter(
                field=Accounts.Fields.allowed_categories,
                operator=ResourcesFilterOperators.EQUAL,
                value="*",
                apply_to=[Actions.UPDATE_LIMITES],
                description="To prevent updating the allowed categories of the account",
            ),
            ResourcesFilter(
                field=Accounts.Fields.allowed_lessons,
                operator=ResourcesFilterOperators.EQUAL,
                value="*",
                apply_to=[Actions.UPDATE_LIMITES],
                description="To prevent updating the allowed lessons of the account",
            ),
            ResourcesFilter(
                field=Accounts.Fields.allowed_users,
                operator=ResourcesFilterOperators.EQUAL,
                value="*",
                apply_to=[Actions.UPDATE_LIMITES],
                description="To prevent updating the allowed users of the account",
            ),
        ],
    )

    draft_lesson_permissions = Permissions(
        resource=Resources.DRAFT_LESSONS,
        actions=[Actions.READ, Actions.UPDATE, Actions.DELETE, Actions.CREATE],
        filters=[
            ResourcesFilter(
                field=DraftLessons.Fields.creator,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                description="To allow actions on draft lessons only from the same account",
            )
        ],
    )

    published_lesson_permissions = Permissions(
        resource=Resources.PUBLISHED_LESSONS,
        actions=[
            Actions.READ,
            Actions.UPDATE,
            Actions.DELETE,
            Actions.CREATE,
            Actions.DUPPLICATE,
            Actions.READ_MANY,
        ],
        filters=[
            # all the below filters are for reading and duplicating
            ResourcesFilter(
                field=PublishedLessons.Fields.public,
                operator=ResourcesFilterOperators.EQUAL,
                value=True,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_categories],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.account, Accounts.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[
                    Users.Fields.account,
                    Accounts.Fields.allowed_categories,
                ],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
                description="Published lessons that the user is allowed to see from his role allowed categories",
            ),
            # all the below filters are for deleting and updating
            ResourcesFilter(
                field=PublishedLessons.Fields.creator,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.DELETE, Actions.UPDATE],
                is_and=True,
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.account, Accounts.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.DELETE, Actions.UPDATE],
                is_and=True,
            ),
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.UPDATE],
                is_and=True,
            ),
            # all the below filters are for reading update data aka edit data
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ_UPDATE_LIMITES],
                is_or=True,
            ),
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ_UPDATE_LIMITES],
                is_or=True,
            ),
        ],
    )

    archived_lesson_permissions = Permissions(
        resource=Resources.ARCHIVED_LESSONS,
        actions=[Actions.READ, Actions.UPDATE, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                # If the user archived the lesson, he can see it
                # and also restore it
                field=ArchiveLessons.Fields.archive_by,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
            )
        ],
    )

    categories_permissions = Permissions(
        resource=Resources.CATEGORIES,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[],
    )

    reviews_permissions = Permissions(
        resource=Resources.REVIEWS,
        actions=[Actions.READ, Actions.CREATE, Actions.READ_MANY],
        # since only after viewing a lesson the user can review it,
        # and the token for viewing a lesson is only given to the user if he is allowed to view it
        # we can assume that the user is allowed to review the lesson
        # so we don't need to add any filters
        # TODO maybe add filter for reading reviews
        filters=[],
    )

    role = Roles(
        id=ObjectId("642985e7bbb066a75d4b2a1d"),
        name="מנהל מוסד",
        internal_name=RolesInternalNames.INSTATUTION_MANAGER,
        permissions=[
            roles_permissions,
            users_permissions,
            accounts_permissions,
            draft_lesson_permissions,
            published_lesson_permissions,
            archived_lesson_permissions,
            categories_permissions,
            reviews_permissions,
        ],
        managed_roles=[r.id for r in roles],
        rank=10,
    )

    db.ROLES_COLLECTION.insert_one(role.dict(to_db=True))


def create_editor_role():

    draft_lesson_permissions = Permissions(
        resource=Resources.DRAFT_LESSONS,
        actions=[Actions.READ, Actions.UPDATE, Actions.DELETE, Actions.CREATE],
        filters=[
            ResourcesFilter(
                field=DraftLessons.Fields.creator,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
            )
        ],
    )

    # The editor and instation manager have the same permissions for published lessons
    published_lesson_permissions = Permissions(
        resource=Resources.PUBLISHED_LESSONS,
        actions=[
            Actions.READ,
            Actions.UPDATE,
            Actions.DELETE,
            Actions.CREATE,
            Actions.DUPPLICATE,
            Actions.READ_MANY,
        ],
        filters=[
            # all the below filters are for reading and duplicating
            ResourcesFilter(
                field=PublishedLessons.Fields.public,
                operator=ResourcesFilterOperators.EQUAL,
                value=True,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.allowed_categories],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.account, Accounts.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[
                    Users.Fields.account,
                    Accounts.Fields.allowed_categories,
                ],
                dynamic_source=DynamicSources.CURRENT_USER,
                is_or=True,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.categories,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.role, Roles.Fields.categories],
                is_or=True,
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ, Actions.DUPPLICATE, Actions.READ_MANY],
                description="Published lessons that the user is allowed to see from his role allowed categories",
            ),
            # all the below filters are for deleting and updating
            ResourcesFilter(
                field=PublishedLessons.Fields.creator,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.DELETE, Actions.UPDATE],
                is_and=True,
            ),
            ResourcesFilter(
                field=PublishedLessons.Fields.id,
                dynamic=True,
                operator=ResourcesFilterOperators.IN,
                dynamic_field=[Users.Fields.account, Accounts.Fields.allowed_lessons],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.DELETE, Actions.UPDATE],
                is_and=True,
            ),
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.UPDATE],
                is_and=True,
            ),
            # all the below are for reading update data, aka edit data
            # editor can read update data if he is the current editor or the initial editor
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ_UPDATE_LIMITES],
                is_or=True,
            ),
            ResourcesFilter(
                field=f"{PublishedLessons.Fields.edit_data}.{LessonEdit.Fields.current_editor}",
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
                apply_to=[Actions.READ_UPDATE_LIMITES],
                is_or=True,
            ),
        ],
    )

    archived_lesson_permissions = Permissions(
        resource=Resources.ARCHIVED_LESSONS,
        actions=[Actions.READ, Actions.UPDATE, Actions.READ_MANY],
        filters=[
            ResourcesFilter(
                # If the user archived the lesson, he can see it
                # and also restore it
                field=ArchiveLessons.Fields.archive_by,
                dynamic=True,
                operator=ResourcesFilterOperators.EQUAL,
                dynamic_field=[Users.Fields.id],
                dynamic_source=DynamicSources.CURRENT_USER,
            )
        ],
    )

    categories_permissions = Permissions(
        resource=Resources.CATEGORIES,
        actions=[Actions.READ, Actions.READ_MANY],
        filters=[],
    )

    # maybe dont allow to create a review for a lesson that the user created
    reviews_permissions = Permissions(
        resource=Resources.REVIEWS,
        actions=[Actions.READ, Actions.CREATE, Actions.READ_MANY],
        # since only after viewing a lesson the user can review it,
        # and the token for viewing a lesson is only given to the user if he is allowed to view it
        # we can assume that the user is allowed to review the lesson
        # so we don't need to add any filters
        # TODO maybe add filter for reading reviews
        filters=[],
    )

    role = Roles(
        id=ObjectId("6374ba0d3e2f7c3c01811e93"),
        name="עורך",
        internal_name=RolesInternalNames.EDITOR,
        permissions=[
            draft_lesson_permissions,
            published_lesson_permissions,
            archived_lesson_permissions,
            categories_permissions,
            reviews_permissions,
        ],
        rank=100,
    )

    db.ROLES_COLLECTION.insert_one(role.dict(to_db=True))

    return role
