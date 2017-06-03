

class ShellCommand(object):
    gzip = 'gzip'
    gunzip = 'gunzip'
    tar = 'tar'

    mysql = 'mysql'
    mysqldump = 'mysqldump'

    host = 'localhost'
    port = '3306'

    mysql_options = ''
    mysqldump_options = ''

    redirect_null = '>/dev/null'

    quiet = False

    def __init__(self, database, user, passwd, **kwargs):

        self.database = database
        self.user = user
        self.passwd = passwd

        options = [
            'gzip',
            'gar',

            'mysql',
            'mysqldump',
            'host',
            'port',
            'mysql_options',
            'mysqldump_options',
        ]

        for option in options:
            if option in kwargs:
                setattr(self, option, kwargs.pop(option))

    def redirect(self, src=None):
        if not self.quiet:
            if src:
                return '{}{}'.format(src, self.redirect_null)
            else:
                return self.redirect_null

        return ''

    def mysql_extra_options(self, additional_options):
        if additional_options:
            return '{} {}'.format(self.mysql_options, additional_options)

        return self.mysql_options

    def mysqldump_extra_options(self, additional_options):
        if additional_options:
            return '{} {}'.format(self.mysqldump_options, additional_options)

        return self.mysqldump_options

    def cmd_mysql(self, mysql_options=''):
        return '{} --host=\'{}\' --port=\'{}\' --user=\'{}\' --password=\'{}\' {} {} {}'.format(
            self.mysql,
            self.host,
            self.port,
            self.user,
            self.passwd,
            self.mysql_extra_options(mysql_options),
            self.database,
            self.redirect('2'),
        )

    def cmd_mysqldump(self, mysqldump_options=''):
        return '{} --host={} --port={} --user={} --password={} {} {} {}'.format(
            self.mysqldump,
            self.host,
            self.port,
            self.user,
            self.passwd,
            self.mysqldump_extra_options(mysqldump_options),
            self.database,
            self.redirect('2'),
        )

    def cmd_snapshot_database(self, snapshot_file, mysqldump_options=''):
        return '{} | {} > {}'.format(
            self.cmd_mysqldump(mysqldump_options),
            self.gzip,
            snapshot_file
        )

    def cmd_snapshot_directory(self, snapshot_file, target_path, tar_cmd='czpf', additional_option=''):
        for c in 'czf':
            if c not in tar_cmd:
                tar_cmd += c

        # tar czpf snapshot_file target_path
        return '{} {} {} {} {}'.format(
            self.tar,
            tar_cmd,
            additional_option,
            snapshot_file,
            target_path,
        )

    def cmd_replace_local_db(self, snapshot_file, mysql_options='', pipe=None):

        if pipe and isinstance(pipe, list):
            jam = '| {} |'.format(' | '.join(pipe))
        elif pipe and isinstance(pipe, str):
            jam = '| {} |'.format(pipe)
        else:
            jam = '|'

        # gunzip -c sql.tar.gz | jam... | mysql -u... -p...
        return '{} -c {} {} {}'.format(
            self.gunzip,
            snapshot_file,
            jam,
            self.cmd_mysql(mysql_options),
        )
