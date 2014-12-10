
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


class DatabaseTranslatableColumn(sa.Column):
    def __init__(self, *args, **kwargs):
        self.tsweight = kwargs.pop('tsweight', None)
        super(DatabaseTranslatableColumn, self).__init__(*args, **kwargs)


class TranslatableColumn(object):
    def __init__(self, *args, **kwargs):
        self.orm_column = args[0]
        self.tsweight = kwargs.pop('tsweight', None)
        self.name = kwargs.pop('name', None)

    def __eq__(self, other):
        return sa.sql.elements.BinaryExpression(
            left=self.translatable_column,
            right=sa.sql.expression.bindparam(other, other),
            operator='='
        )


class SearchMapperCreator(object):
    def __init__(self, translatable_mapper_creator):
        self.translatable_mapper_creator = translatable_mapper_creator

    def __construct_table(self):
        columns = []
        columns.append(sa.Column('id', sa.Integer(), primary_key=True))
        columns.append(sa.Column('search_vector', TSVECTOR))
        columns.append(sa.Column(
            self.translatable_mapper_creator.local_mapper.class_.__translatable_mapper__.local_table.name + '_id',
            sa.ForeignKey(
                self.translatable_mapper_creator.local_mapper.class_.__translatable_mapper__.local_table.columns.id
            )
        ))

        table = sa.Table(self.translatable_mapper_creator.local_mapper.local_table.name + '_search_fields',
            self.translatable_mapper_creator.local_mapper.local_table.metadata,
            *columns,
            schema=self.translatable_mapper_creator.local_mapper.local_table.schema
        )

        table.indexes.update([
            sa.Index(
                '{0}_tsvector'.format(table.name),
                table.c.search_vector,
                postgresql_using='gin'
            )
        ])

        return table

    def create_search_class(self):
        return type.__new__(
            type,
            '%sSearchable' % self.translatable_mapper_creator.local_mapper.class_.__name__,
            self.translatable_mapper_creator.local_mapper.base_mapper.class_.__bases__[1:2],
            {}
        )

    def create_search_mapper(self):
        orm_class = self.create_search_class()
        search_mapper = sa.orm.mapper(
            orm_class,
            self.__construct_table(),
            properties={
                'translatable_fields': sa.orm.relationship(
                    self.translatable_mapper_creator.local_mapper.class_.__translatable_mapper__,
                    uselist=False,
                    backref=sa.orm.backref(
                        'search_fields',
                        uselist=True,
                        lazy='joined',
                        cascade='all, delete-orphan'
                    )
                )
            }
        )

        return search_mapper


class TranslatableMapperCreator(object):
    def __init__(self, local_mapper):
        self.local_mapper = local_mapper
        self.search_mapper_creator = SearchMapperCreator(self)

    @staticmethod
    def translatable_objects(sequence):
        for obj in sequence:
            if hasattr(obj, '__translatable_mapper__'):
                yield obj

    @property
    def translatable_class(self):
        class_ = type.__new__(type, '%sTranslatable' % self.local_mapper.class_.__name__, self.local_mapper.base_mapper.class_.__bases__[1:2], {})
        return class_

    def __construct_table(self, tablename, columns, schema, extends=False):
        return sa.Table(tablename, self.local_mapper.local_table.metadata, *columns, schema=schema, extend_existing=extends)

    def create_translatable_mapper(self):
        columns = []
        columns.append(sa.Column('id', sa.Integer(), primary_key=True))
        columns.append(sa.Column('language', sa.String()))

        for attr in self.local_mapper.class_.__dict__:
            q_trans_column = self.local_mapper.class_.__dict__[attr]

            if isinstance(q_trans_column, TranslatableColumn):
                new_column = DatabaseTranslatableColumn(attr, q_trans_column.orm_column, tsweight=q_trans_column.tsweight)
                columns.append(new_column)
                q_trans_column.translatable_column = new_column

        columns.append(sa.Column(self.local_mapper.local_table.name + '_id', sa.ForeignKey(self.local_mapper.local_table.columns.id)))
        columns.append(
            sa.UniqueConstraint(
                'language', self.local_mapper.local_table.name + '_id',
                name='language_' + self.local_mapper.local_table.name + '_id_unique_constraint'
            )
        )

        table = self.__construct_table(
            self.local_mapper.local_table.name + '_translatable_fields',
            columns,
            self.local_mapper.local_table.schema
        )

        translatable_mapper = sa.orm.mapper(self.translatable_class, table,
            properties={
                'base': sa.orm.relationship(
                    self.local_mapper,
                    uselist=False,
                    backref=sa.orm.backref('translatable_fields',
                        uselist=True,
                        lazy='joined',
                        cascade='all, delete-orphan',
                        order_by=[table.c.language.asc()]
                    )
                )
            }
        )

        self.local_mapper.class_.__translatable_mapper__ = translatable_mapper

        search_mapper = self.search_mapper_creator.create_search_mapper()
        self.local_mapper.class_.__search_mapper__ = search_mapper


class Translatable(object):
    language = 'ru'

    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop('language', None)

    def __getattribute__(self, item):
        attr = super(Translatable, self).__getattribute__(item)

        if isinstance(attr, TranslatableColumn):
            for trans_field in self.translatable_fields:
                if trans_field.language == self.language:
                    return getattr(trans_field, item)

            return None

        return attr

    @property
    def mapper_creator(self):
        return TranslatableMapperCreator(sa.orm.object_mapper(instance=self))

    def create_translatable_fields(self, session):
        trans_table = self.__translatable_mapper__.class_()
        trans_table.base = self
        instance_mapper = sa.orm.object_mapper(trans_table)
        search_vectors = []

        for column in instance_mapper.columns:
            if isinstance(column, DatabaseTranslatableColumn):
                setattr(trans_table, column.name, getattr(self, column.name))

                if column.tsweight:
                    search_vectors.append(sa.func.setweight(
                        sa.func.to_tsvector(unicode(getattr(self, column.name))),
                        column.tsweight
                    ))

        # Setup language
        setattr(trans_table, 'language', self.language)

        # Update search fields
        search_table = self.__search_mapper__.class_()
        search_table.translatable_fields = trans_table

        for count, vector in enumerate(search_vectors):
            if not count:
                search_table.search_vector = vector + ' '
            else:
                search_table.search_vector = search_table.search_vector + vector + ' '

        session.add(trans_table)
        session.add(search_table)

    def write_translatable_fields(self, **kwargs):
        self.language = kwargs['language']
        exist = None

        for trans_fields_item in self.translatable_fields:
            if trans_fields_item.language == self.language:
                exist = trans_fields_item

        if exist:
            for field in kwargs:
                setattr(exist, field, kwargs[field])
        else:
            new_trans_fields = self.__translatable_mapper__.class_(**kwargs)
            tsvectors = []

            for column in self.__translatable_mapper__.columns:
                if isinstance(column, DatabaseTranslatableColumn):
                    setattr(new_trans_fields, column.name, kwargs.get(column.name))

                    if column.tsweight:
                        tsvectors.append(sa.func.setweight(
                            sa.func.to_tsvector(unicode(kwargs.get(column.name))),
                            column.tsweight
                        ))

            new_search_fields = self.__search_mapper__.class_()

            for count, vector in enumerate(tsvectors):
                if not count:
                    new_search_fields.search_vector = vector + ' '
                else:
                    new_search_fields.search_vector = new_search_fields.search_vector + vector + ' '

            new_trans_fields.search_fields.append(new_search_fields)
            self.translatable_fields.append(new_trans_fields)

    @sa.ext.declarative.declared_attr
    def __mapper_cls__(self):
        def map(cls, *args, **kwargs):
            mp = sa.orm.mapper(cls, *args, **kwargs)
            TranslatableMapperCreator(mp).create_translatable_mapper()
            return mp

        return map


def session_handler(session):
    @sa.event.listens_for(session, 'before_flush')
    def before_flush(session, context, instances):
        for instance in TranslatableMapperCreator.translatable_objects(session.new):
            TranslatableMapperCreator(sa.orm.object_mapper(instance=instance))
            instance.create_translatable_fields(session)

    return before_flush
