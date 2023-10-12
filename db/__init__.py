from pymongo import MongoClient, IndexModel

from helpers.env import EnvVars
from db.models import (
    __models__,
    DraftLessons,
    PublishedLessons,
    ArchiveLessons,
    LessonsReviews,
    Categories,
    Users,
    Accounts,
    Roles,
    SiteHelp,
    SiteHelpCategories,
)


mongo_client = MongoClient(EnvVars.DB_CONNECTION_STRING)
db = mongo_client[EnvVars.DB_NAME]


USER_COLLECTION = db[Users.__get_collection_name__()]
ACCOUNT_COLLECTION = db[Accounts.__get_collection_name__()]
DRAFT_LESSONS_COLLECTION = db[DraftLessons.__get_collection_name__()]
PUBLISHED_LESSONS_COLLECTION = db[PublishedLessons.__get_collection_name__()]
ARCHIVE_LESSONS_COLLECTION = db[ArchiveLessons.__get_collection_name__()]
LESSONS_REVIEWS_COLLECTION = db[LessonsReviews.__get_collection_name__()]
CATEGORIES_COLLECTION = db[Categories.__get_collection_name__()]
ROLES_COLLECTION = db[Roles.__get_collection_name__()]
SITE_HELP_COLLECTION = db[SiteHelp.__get_collection_name__()]
SITE_HELP_CATEGORIES_COLLECTION = db[SiteHelpCategories.__get_collection_name__()]


def create_all_indexes():

    for model in __models__:

        c_name = model.__get_collection_name__()

        current_indexes_names = list(db[c_name].index_information().keys())

        updated_indexes_names = []

        indexes = []

        for index in model.get_indexes():

            indexes.append(
                IndexModel(
                    index.fields,
                    name=index.name,
                    unique=index.unique,
                    collation=index.collation,
                )
            )

            updated_indexes_names.append(index.name)

        indexes_to_drop = []

        for index_name in current_indexes_names:
            if index_name not in updated_indexes_names and not index_name == "_id_":
                indexes_to_drop.append(index_name)

        for index_name in indexes_to_drop:
            print(f"dropping index {index_name} from {c_name}")
            db[c_name].drop_index(index_name)

        # its ok to create indexes even if they already exist
        # mongo will just ignore them
        if indexes:
            print(f"creating indexes for {c_name}")
            db[c_name].create_indexes(indexes)
