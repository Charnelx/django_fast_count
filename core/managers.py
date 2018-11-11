from django.db.models import Manager


from django.db import connections
from django.db.models.query import QuerySet


class ApproxCountQuerySet(QuerySet):

    """
    Fast 'COUNT' operation for usage on tables with big row's amount.
    Use this just by overriding get_queryset method in model manager class
    to use ApproxCountQuerySet instead of default QuerySet.

    Should work with MySQL => 5.6, Postgres >= 9.4 and any SQLite3 version
    """

    COUNT_METHODS = {
        'mysql': lambda: ApproxCountQuerySet._mysql_count,
        'sqlite3': lambda: ApproxCountQuerySet._sqlite3_count,
        'psycopg2': lambda: ApproxCountQuerySet._postgresql_count
    }

    def _mysql_count(self):
        """
        Accuracy depends on how often 'ANALYZE TABLE' command was run.
        """
        with connections[self.db].cursor() as cursor:
            cursor.execute("SHOW TABLE STATUS LIKE %s", (self.model._meta.db_table,))
            return cursor.fetchall()[0][4]

    def _sqlite3_count(self):
        """
        Accuracy is extremely low! Depends on highest existing rowid.
        rowid could be reset (and thus become closer to real rows count)
        by running 'VACUUM' for some cases. For Django ORM this will almost
        always be just highest ID.
        """
        with connections[self.db].cursor() as cursor:
            cursor.execute(f'SELECT max(rowid) from {self.model._meta.db_table};')
            return cursor.fetchall()[0][0]

    def _postgresql_count(self):
        """
        Accuracy depends on how often 'ANALYZE' command was run.
        """
        with connections[self.db].cursor() as cursor:
            parts = [p.strip('"') for p in self.model._meta.db_table.split('.')]
            if len(parts) == 1:
                cursor.execute(
                    "SELECT reltuples::bigint"
                    " FROM pg_class "
                    "WHERE relname = %s",
                    parts
                    )
            else:
                cursor.execute(
                    "SELECT reltuples::bigint "
                    "FROM pg_class c "
                    "JOIN pg_namespace n "
                    "ON (c.relnamespace = n.oid) "
                    "WHERE n.nspname = %s AND c.relname = %s",
                    parts
                )
            return cursor.fetchall()[0][0]

    def count(self, *args, force_default=False, **kwargs):
        """
        Fast count method realization for case described in ticket #8408
        For details see - https://code.djangoproject.com/ticket/8408#trac-change-19

        MySQL code basis taken from https://www.tablix.org/~avian/blog/archives/2011/07/django_admin_with_large_tables/
        PostgreSQL code basis taken from https://stackoverflow.com/a/23118765
        """
        if self._result_cache is not None:
            return len(self._result_cache)

        db_engine_name = connections[self.db].client.executable_name.lower()
        handler = self.COUNT_METHODS.get(db_engine_name)
        # if query have no constraints, we can get approximated rows count
        # else - use parent method
        if (
                handler and not self.query.where and
                self.query.high_mark is None and
                self.query.low_mark == 0 and
                not self.query.select and
                not self.query.group_by and
                not self.query.distinct and
                not force_default
        ):
            return handler()(self)
        return self.query.get_count(using=self.db)


class TestProfileManager(Manager):

    def get_queryset(self):
        return ApproxCountQuerySet(self.model)