# Copyright 2018 Datera Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shlex
import shutil
import subprocess
import sys

from charmhelpers.core.hookenv import (
    config,
)
from charmhelpers.fetch.archiveurl import (
    ArchiveUrlFetchHandler,
)

from charmhelpers.fetch.giturl import (
    GitUrlFetchHandler,
)

from charmhelpers.payload.archive import (
    extract,
)

from charmhelpers.core.hookenv import (
    log,
)

from charmhelpers.fetch.python import packages

CINDER_BACKUP_FOLDER = '/tmp/cinder'


class DateraException(Exception):
    pass


def dlog(msg):
    log('[cinder-datera] %s' % msg)


def remove():
    dlog("Stating Datera driver removal")
    dest = get_install_dest()
    restore_folder(dest)


def install():
    dlog("Stating Datera driver installation")
    dest = get_install_dest()
    backup_folder(dest)
    if config('install_type') == 'github':
        install_from_github(config('install_url'), config('install_tag'), dest)
    elif config('install_type') == 'archive-url':
        install_from_archive_url(config('install_url'), dest)
    elif config('install_type') == 'archive-local':
        install_from_archive_local(config('install_file'), dest)
    else:
        raise DateraException("Unknown install type {}".format(
            config('install_type')))
    packages.pip_install("dfs_sdk", upgrade=True)


def install_from_github(url, tag, dest):
    dlog("Trying to install from github")
    try:
        handler = GitUrlFetchHandler()
        ddir = handler.install(url, branch=tag)
        if os.path.exists(dest):
            dlog("Removing existing directory at {}".format(dest))
            shutil.rmtree(dest)
        src = os.path.join(ddir, "src", "cinder", "volume", "drivers", "datera")
        dlog("Copying tree. src [{}] dst [{}]".format(src, dest))
        shutil.copytree(src, dest)
    except Exception as e:
        raise DateraException("Could not install from github: {}".format(e))


def install_from_archive_url(url, dest):
    dlog("Trying to install from archive url: {}".format(url))
    try:
        handler = ArchiveUrlFetchHandler()
        ddir = handler.install(url)
        if os.path.exists(dest):
            dlog("Removing existing directory at {}".format(dest))
            shutil.rmtree(dest)
        src = os.path.join(ddir, "src", "cinder", "volume", "drivers", "datera")
        dlog("Copying tree. src [{}] dst [{}]".format(src, dest))
        shutil.copytree(src, dest)
    except Exception as e:
        raise DateraException(
            "Could not install from archive url: {}".format(e))


def install_from_archive_local(archive, dest):
    dlog("Trying to install from archive")
    try:
        ddir = extract(archive)
        if os.path.exists(dest):
            dlog("Removing existing directory at {}".format(dest))
            shutil.rmtree(dest)
        src = os.path.join(ddir, "src", "cinder", "volume", "drivers", "datera")
        dlog("Copying tree. src [{}] dst [{}]".format(src, dest))
        shutil.copytree(src, dest)
    except Exception as e:
        raise DateraException(
            "Could not install from archive url: {}".format(e))


def find_cinder_install():
    """
    Finds the install location of Cinder.  Big caveat is that this only works
    if cinder is available to either the running python or the system python
    (if system != current)
    """
    try:
        import cinder
        return os.path.dirname(cinder.__file__)
    except ImportError:
        try:
            out = exec_cmd("python -c 'import cinder; print(cinder.__file__)'")
            return os.path.dirname(out.rstrip())
        except subprocess.CalledProcessError:
            try:
                out = exec_cmd(
                    "python3 -c 'import cinder; print(cinder.__file__)'")
                return os.path.dirname(out.rstrip())
            except subprocess.CalledProcessError:
                dlog("Could not determine Cinder install location.  Cinder "
                     "must either be installed in the currently running "
                     "python or in the system python")
                raise


def get_install_dest():
    c = find_cinder_install()
    cpath = os.path.join(c, "volume", "drivers")
    dpath = os.path.join(cpath, "datera")
    if not os.path.exists(cpath):
        dpath = os.path.join(c, "cinder", "volume", "drivers", "datera")
    return dpath


def backup_folder(folder):
    p = os.path.dirname(folder.rstrip('/'))
    try:
        shutil.copytree(p, CINDER_BACKUP_FOLDER)
    except OSError as e:
        dlog(e)


def restore_folder(folder):
    p = os.path.dirname(folder.rstrip('/'))
    shutil.rmtree(p)
    shutil.copytree(CINDER_BACKUP_FOLDER, p)


def get_version():
    file = os.path.join(get_install_dest(), 'datera_iscsi.py')
    out = exec_cmd('grep "VERSION = " {}'.format(file))
    parts = out.split(" = ")
    if len(parts) == 2:
        return parts[-1].strip().strip("'").strip('"')
    dlog("Uknown version: {}".format(out))
    return "Unknown"


def exec_cmd(cmd):
    dlog("Executing command: [{}]".format(cmd))
    out = subprocess.check_output(shlex.split(cmd))
    out = out.decode(sys.stdout.encoding)
    dlog("Result: {}".format(out))
    return out
