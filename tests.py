from unittest import TestCase
# noinspection PyUnresolvedReferences
from types import ModuleType, FunctionType

from shell_command import ShellCommand

import re

import utils


class TestShellCommand(TestCase):

    def setUp(self):
        self.cmd = ShellCommand(
            database='wordpress',
            user='user',
            passwd='pass',
            mysql_options='--protocol=tcp',
            mysqldump_options='--single-transaction'
        )

    @staticmethod
    def replace_spaces(string):
        return re.sub(r'\s+', ' ', string)

    def test_redirect(self):
        self.assertEqual(self.cmd.redirect_null, self.cmd.redirect())
        self.assertEqual('1 ' + self.cmd.redirect_null, self.cmd.redirect(1))

    def test_cmd_mysql(self):
        self.assertEqual(
            'mysql --host=localhost --port=3306 --user=user --password=pass ' 
            '--protocol=tcp --column-type-info wordpress 2 > /dev/null',
            self.replace_spaces(self.cmd.cmd_mysql('--column-type-info'))
        )

    def test_cmd_mysqldump(self):
        self.assertEqual(
            'mysqldump --host=localhost --port=3306 --user=user --password=pass '
            '--single-transaction --skip-opt wordpress 2 > /dev/null',
            self.replace_spaces(self.cmd.cmd_mysqldump('--skip-opt'))
        )

    def test_cmd_snapshot_database(self):
        self.assertEqual(
            'mysqldump --host=localhost --port=3306 --user=user --password=pass '
            '--single-transaction wordpress 2 > /dev/null | gzip > snapshot.sql.gz',
            self.replace_spaces(self.cmd.cmd_snapshot_database('snapshot.sql.gz', None))
        )

    def test_cmd_snapshot_directory(self):
        self.assertEqual(
            'tar czpf snapshot.tar.gz public_html',
            self.replace_spaces(self.cmd.cmd_snapshot_directory('snapshot.tar.gz', 'public_html'))
        )

    def test_cmd_replace_local_db(self):
        self.assertEqual(
            'gunzip -c snapshot.sql.gz | '
            'mysql --host=localhost --port=3306 --user=user --password=pass '
            '--protocol=tcp wordpress 2 > /dev/null',
            self.replace_spaces(
                self.cmd.cmd_replace_local_db(
                    snapshot_file='snapshot.sql.gz',
                    mysql_options='',
                    pipe=''
                )
            )
        )

        self.assertEqual(
            'gunzip -c snapshot.sql.gz | sed | pipe-test | '
            'mysql --host=localhost --port=3306 --user=user --password=pass '
            '--protocol=tcp wordpress 2 > /dev/null',
            self.replace_spaces(
                self.cmd.cmd_replace_local_db(
                    snapshot_file='snapshot.sql.gz',
                    mysql_options='',
                    pipe=['sed', 'pipe-test']
                )
            )
        )

        self.assertEqual(
            'gunzip -c snapshot.sql.gz | sed | '
            'mysql --host=localhost --port=3306 --user=user --password=pass '
            '--protocol=tcp wordpress 2 > /dev/null',
            self.replace_spaces(
                self.cmd.cmd_replace_local_db(
                    snapshot_file='snapshot.sql.gz',
                    mysql_options='',
                    pipe='sed'
                )
            )
        )


class TestUtils(TestCase):

    def test_load_script_module(self):

        test_script = utils.load_script_module('test_script')

        self.assertIsInstance(test_script, ModuleType)

        test_func = getattr(test_script, 'test_func')

        self.assertIsInstance(test_func, FunctionType)

        self.assertEqual('Hello, World!', test_func())
