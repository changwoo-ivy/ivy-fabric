import importlib
import os
import sys

from fabric.api import (
    env,
    get,
    lcd,
    local,
    put,
)

# noinspection PyUnresolvedReferences
from MySQLdb import escape_string

from shutil import (
    copyfile,
    rmtree
)

from tempfile import NamedTemporaryFile


def download(remote_file, local_file=None):
    if not local_file:
        local_file = os.path.basename(remote_file)
    get(remote_file, local_file)


def upload(local_file, remote_file):
    put(local_file, remote_file)


def add_path(directory):
    if directory not in sys.path:
        sys.path.append(directory)


def load_script_module(script):
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'scripts', '{}.py'.format(script))):
        raise ValueError('script \'%s\' not found.' % script)

    return importlib.import_module('scripts.%s' % script)


def run_once(script, function_name, *args, **kwargs):
    m = load_script_module(script)

    if not hasattr(m, function_name):
        raise AttributeError('Module \'%s\' does not have attribute \'%s\'' % (script, function))

    f = getattr(m, function_name)
    if not callable(f):
        raise ValueError('Function \'%s.%s\' is not callable.' % (script, function_name))

    return f(*args, **kwargs)


def run_copy_to_local(script, *args, **kwargs):
    return run_once(script, 'copy2local', *args, **kwargs)


def check_env_attr(attr):
    if not hasattr(env, attr):
        raise AttributeError('env does not have attribute \'%s\'' % attr)


def replace_local_wp(snapshot_file, wp_path):
    local_config = os.path.join(wp_path, 'wp-config.php')
    backup_config = os.path.join(wp_path, '..', 'wp-config.php.' + env.host_string)

    if os.path.exists(local_config):
        copyfile(local_config, backup_config)

    if os.path.exists(wp_path):
        rmtree(wp_path)

    os.mkdir(wp_path)

    with lcd(wp_path):
        cmd = 'tar xf {} --strip=1'.format(snapshot_file)
        local(cmd)

    if os.path.exists(backup_config):
        copyfile(backup_config, local_config)
        os.remove(backup_config)


class TemporaryFile(object):
    def __init__(self):
        self.f = NamedTemporaryFile('w', delete=False)

    def __del__(self):
        if self.f and self.f.name:
            os.remove(self.f.name)

    def write(self, content):
        self.f.write(content)

    def close(self):
        self.f.close()

    @property
    def name(self):
        return self.f.name
