import sqlalchemy

import database

__metadata = sqlalchemy.MetaData(schema="authorization")

__fk_options = {"onupdate": "CASCADE", "ondelete": "CASCADE"}

roles = sqlalchemy.Table(
    "roles",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.String(length=255), unique=True),
    sqlalchemy.Column("description", sqlalchemy.Text),
)

scopes = sqlalchemy.Table(
    "scopes",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("name", sqlalchemy.Text, unique=True),
    sqlalchemy.Column("description", sqlalchemy.Text),
    sqlalchemy.Column("value", sqlalchemy.String(length=255), unique=True),
)

access_token = sqlalchemy.Table(
    "accessTokens",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("value", sqlalchemy.String(length=56)),
    sqlalchemy.Column("active", sqlalchemy.Boolean, default=True),
    sqlalchemy.Column("expires", sqlalchemy.TIMESTAMP(timezone=True)),
    sqlalchemy.Column("created", sqlalchemy.TIMESTAMP(timezone=True)),
    sqlalchemy.Column("accountID", None, sqlalchemy.ForeignKey("accounts.id", **__fk_options)),
)

refresh_token = sqlalchemy.Table(
    "refreshTokens",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("value", sqlalchemy.String(length=56)),
    sqlalchemy.Column("active", sqlalchemy.Boolean, default=True),
    sqlalchemy.Column("expires", sqlalchemy.TIMESTAMP(timezone=True)),
    sqlalchemy.Column("accountID", None, sqlalchemy.ForeignKey("accounts.id", **__fk_options)),
)

accounts = sqlalchemy.Table(
    "accounts",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("firstName", sqlalchemy.String(length=255), nullable=False),
    sqlalchemy.Column("lastName", sqlalchemy.String(length=255), nullable=False),
    sqlalchemy.Column("username", sqlalchemy.String(length=255), nullable=False, unique=True),
    sqlalchemy.Column("password", sqlalchemy.Text, nullable=False),
    sqlalchemy.Column("active", sqlalchemy.Boolean, default=True, nullable=False),
)

role_scopes = sqlalchemy.Table(
    "roleScopes",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("roleID", None, sqlalchemy.ForeignKey("roles.id", **__fk_options)),
    sqlalchemy.Column("scopeID", None, sqlalchemy.ForeignKey("scopes.id", **__fk_options)),
)

access_token_scopes = sqlalchemy.Table(
    "accessTokenScopes",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "tokenID", sqlalchemy.Integer, sqlalchemy.ForeignKey("accessTokens.id", **__fk_options)
    ),
    sqlalchemy.Column(
        "scopeID", sqlalchemy.Integer, sqlalchemy.ForeignKey("scopes.id", **__fk_options)
    ),
)

refresh_token_scopes = sqlalchemy.Table(
    "refreshTokenScopes",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "tokenID", sqlalchemy.Integer, sqlalchemy.ForeignKey("accessTokens.id", **__fk_options)
    ),
    sqlalchemy.Column(
        "scopeID", sqlalchemy.Integer, sqlalchemy.ForeignKey("scopes.id", **__fk_options)
    ),
)

account_scopes = sqlalchemy.Table(
    "accountScopes",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "accountID", sqlalchemy.Integer, sqlalchemy.ForeignKey("accounts.id", **__fk_options)
    ),
    sqlalchemy.Column(
        "scopeID", sqlalchemy.Integer, sqlalchemy.ForeignKey("scopes.id", **__fk_options)
    ),
)

account_roles = sqlalchemy.Table(
    "accountRoles",
    __metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column(
        "accountID", sqlalchemy.Integer, sqlalchemy.ForeignKey("accounts.id", **__fk_options)
    ),
    sqlalchemy.Column(
        "scopeID", sqlalchemy.Integer, sqlalchemy.ForeignKey("roles.id", **__fk_options)
    ),
)


def initialize() -> None:
    """
    Initialize the tables used by the service
    """
    __metadata.create_all(bind=database.engine)
