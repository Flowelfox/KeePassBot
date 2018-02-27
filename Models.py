from peewee import CharField, DateTimeField, BlobField, Model, SqliteDatabase, DoesNotExist, BooleanField, IntegerField
from playhouse.migrate import migrate, SqliteMigrator

from settings import DATABASE

database = SqliteDatabase(DATABASE)

# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.
class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    chat_id = IntegerField(default=0, unique=True)
    username = CharField(unique=True, null=True)
    join_date = DateTimeField()
    file = BlobField(null=True)
    is_opened = BooleanField(default=False)
    interface_message_id = IntegerField(default=0)
    key_file_needed = BooleanField(default=False)
    password_needed = BooleanField(default=True)
    create_state = BooleanField(default=False)
    notification = BooleanField(default=True)


    class Meta:
        order_by = ('username',)

    @classmethod
    def get_or_none(cls, **kwargs):
        try:
            return User.get(**kwargs)
        except DoesNotExist:
            return None



def create_tables():
    database.connect()
    database.create_tables([User])

def create_custom_columns():
    database.connect()
    migrator = SqliteMigrator(database)

    new_column = BooleanField(default=True)
    chat_id = IntegerField(default=0)

    migrate(
        #migrator.add_column('user', 'notification', new_column),
        migrator.add_column('user', 'chat_id', chat_id),
    )

if __name__ == "__main__":
    pass
    #create_tables()
    #create_custom_columns()