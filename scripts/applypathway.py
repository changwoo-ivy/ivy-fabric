import os
import re
from shutil import (
    rmtree,
)

from fabric.api import (
    cd,
    env,
    lcd,
    local,
    run,
)

from shell_command import ShellCommand
from utils import TemporaryFile, check_env_attr, download, escape_string, replace_local_wp


def check_env():
    """
    fabric.api.env 에 원하는 초기값이 다 들어 있는지 체크
    """
    list_of_attributes = [
        # remote
        'remote_url',
        'remote_db_name',
        'remote_db_user',
        'remote_db_pass',
        'remote_wp_path',
        'remote_sql_snapshot',
        'remote_wp_snapshot',

        # local
        'local_db_name',
        'local_db_user',
        'local_db_pass',
        'local_wp_path',
        'local_sql_snapshot',
        'local_wp_snapshot',
    ]

    for attr in list_of_attributes:
        check_env_attr(attr)


def change_local_chmod(directory, dir_perm='755', file_perm='644'):
    """
    로컬 대상 디렉토리에 퍼미션 변경.
    """
    with lcd(directory):
        local('find . -type f -exec chmod %s {} \;' % file_perm)
        local('find . -type d -exec chmod %s {} \;' % dir_perm)


def do_symbolic_links(items):
    """
    지정한 디렉토리와 파일은 삭제하고, 로컬의 다른 경로의 것을 가져와 심볼릭 링크 처리
    """
    for item in items:
        if os.path.exists(item['target']):
            if os.path.isdir(item['target']):
                rmtree(item['target'])

            elif os.path.isfile(item['target']):
                os.remove(item['target'])

        with lcd(os.path.dirname(item['target'])):
            local('ln -s %s %s' % (item['replace'], os.path.basename(item['replace'])))


def update_url(shell, replacement_items, old_string, new_string):
    """
    데이터베이스 안의 내용을 치환.
    """
    if old_string == new_string:
        return

    f = TemporaryFile()
    for item in replacement_items:
        query = "UPDATE `%s` SET `%s` = REPLACE(`%s`, \'%s\', \'%s\');\n" % (
            item['table'],
            item['field'],
            item['field'],
            old_string,
            new_string
        )
        f.write(query)
    f.close()

    local(shell.cmd_mysql() + ' < ' + f.name)


def update_serialized_option_value(shell, option_table, option_name, expr):
    """
    직렬화 된 값 안에서 문자열은 문자열의 길이를 기억하게 되어 있다. 문자열 치환이 직렬화된 값 안에서 일어났다면 문자열의 길이도 변경해야 한다.

    :param shell:
    :param option_table:
    :param option_name:
    :param expr:
    :return:
    """

    def repl(match):
        return 's:%d:\"%s\";' % (len(match.group(2)), match.group(2))

    query = '"SELECT option_value AS \'\' FROM %s WHERE option_name=\'%s\'"' % (option_table, option_name)
    cmd = shell.cmd_mysql(mysql_options='-s -r -e {}'.format(query))
    m = local(cmd, capture=True)

    expr = 's:(\d+):"(%s)";' % expr
    replaced = escape_string(re.sub(expr, repl, m.stdout)).decode('utf-8')

    f = TemporaryFile()
    query = 'UPDATE %s SET option_value=\'%s\' WHERE option_name=\'%s\';' % (option_table, replaced, option_name)
    f.write(query)
    f.close()

    local(shell.cmd_mysql() + ' < ' + f.name)


def copy2local(*args, **kwargs):
    """
    applypathway.org 를 위한 copy2local 스크립트
    """

    if args or kwargs:
        pass

    check_env()

    remote_shell = ShellCommand(database=env.remote_db_name, user=env.remote_db_user, passwd=env.remote_db_pass)
    local_shell = ShellCommand(database=env.local_db_name, user=env.local_db_user, passwd=env.local_db_pass)

    # dump remote database
    run(remote_shell.cmd_snapshot_database(env.remote_sql_snapshot, '--add-drop-table'))

    # copy dumped sql file to local
    download(env.remote_sql_snapshot, env.local_sql_snapshot)

    # MariaDB to MySQL Conversion pipe
    pipe = "sed -e 's/ENGINE=Aria/ENGINE=InnoDB/' -e 's/PAGE_CHECKSUM=1//' -e 's/TRANSACTIONAL=1//'"

    # replace local table
    local(local_shell.cmd_replace_local_db(env.local_sql_snapshot, '', pipe))

    # tar archive remote wordpress
    with cd(os.path.dirname(env.remote_wp_path)):
        run(remote_shell.cmd_snapshot_directory(env.remote_wp_snapshot, os.path.basename(env.remote_wp_path)))

    # copy remote archive to local
    download(env.remote_wp_snapshot, env.local_wp_snapshot)

    # replace the local wp
    replace_local_wp(env.local_wp_snapshot, env.local_wp_path)

    # cleanup remote
    run('rm -f {} {}'.format(env.remote_sql_snapshot, env.remote_wp_snapshot))

    # cleanup local
    local('rm -f {} {}'.format(env.local_sql_snapshot, env.local_wp_snapshot))

    # arrange permissions
    change_local_chmod(env.local_wp_path)

    # some developing plugins are symbolic linked.
    local_mu_plugins = [
        {
            'target':  os.path.join(env.local_wp_path, 'wp-content', 'mu-plugins', 'ivy-mu'),
            'replace': '/home/changwoo/devel/wordpress/mu-plugins/ivy-mu',
        },
        {
            'target':  os.path.join(env.local_wp_path, 'wp-content', 'mu-plugins', 'ivy-mu-loader.php'),
            'replace': '/home/changwoo/devel/wordpress/mu-plugins/ivy-mu-loader.php',
        }
    ]
    do_symbolic_links(local_mu_plugins)

    local_plugins = [
        {
            'target':  os.path.join(env.local_wp_path, 'wp-content', 'plugins', 'applypathway'),
            'replace': '/home/changwoo/devel/wordpress/plugins/applypathway',
        }
    ]
    do_symbolic_links(local_plugins)

    # remote URL strings will be replaced
    replacement_items = [
        {
            'table': 'wp_options',
            'field': 'option_value',
        },
        {
            'table': 'wp_posts',
            'field': 'post_content',
        },
        {
            'table': 'wp_posts',
            'field': 'guid',
        },
        {
            'table': 'wp_postmeta',
            'field': 'meta_value',
        },
        {
            'table': 'wp_usermeta',
            'field': 'meta_value',
        },
    ]
    update_url(local_shell, replacement_items, env.remote_url, 'http://applypathway.local')

    # after replacement, the lengths of replaced strings will be changed.
    # Those change will impact on serialized values. Therefore, update serialized option values
    update_serialized_option_value(local_shell, 'wp_options', 'avada_options', env.remote_url + '.+?')
    update_serialized_option_value(local_shell, 'wp_options', 'fusion_options', 'http://applypathway.local.+?')
