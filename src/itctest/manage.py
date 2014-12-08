# coding: utf-8

from flask import current_app
from flask.ext.script import Server, Manager
from flask.ext.script.commands import Clean, ShowUrls
from flask.ext.assets import ManageAssets
from flask.ext.alembic import ManageMigrations

from brpr.blueprints.language.manage import MakeMessage, CompileMessage

from itctest.init import app, collect, db


manager = Manager(app)
manager.add_command('clean', Clean())
manager.add_command('routes', ShowUrls())
manager.add_command('makemessages', MakeMessage('itctest'))
manager.add_command('compilemessages', CompileMessage('itctest'))
manager.add_command('runserver', Server())
manager.add_command('migrate', ManageMigrations())
manager.add_command('assets', ManageAssets())
collect.init_script(manager)


def drop_all():
    from sqlalchemy.engine import reflection
    from sqlalchemy.schema import (
        MetaData,
        Table,
        DropTable,
        ForeignKeyConstraint,
        DropConstraint
    )

    inspector = reflection.Inspector.from_engine(db.engine)
    metadata = MetaData()

    tbs = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(
                ForeignKeyConstraint((), (), name=fk['name'])
            )
        t = Table(table_name, metadata, *fks)
        tbs.append(t)
        all_fks.extend(fks)

    for fkc in all_fks:
        db.engine.execute(DropConstraint(fkc))

    for table in tbs:
        db.engine.execute(DropTable(table))


@manager.command
def syncdb(console=True):
    from admin.models import User

    user_defaults = {
        'login': 'admin',
        'password': 'admin'
    }
    input_msg = 'Enter {0} [{1}]: '

    if console:
        for k, v in user_defaults.iteritems():
            user_defaults[k] = raw_input(input_msg.format(k, v)) or v

    user = User(**user_defaults)
    user.activity = True

    drop_all()

    db.create_all()

    db.session.add(user)
    db.session.flush()

    db.session.commit()


def main():
    manager.run()
