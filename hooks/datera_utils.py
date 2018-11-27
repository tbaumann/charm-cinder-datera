import os
import shutil
import subprocess

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


class DateraException(Exception):
    pass


def dlog(msg):
    log('[cinder-datera] %s' % msg)


def remove():
    dlog("Stating Datera driver removal")


def install():
    dlog("Stating Datera driver installation")
    dest = get_install_dest()
    if config('install_type') == 'github':
        install_from_github(config('install_url'), config('install_tag'), dest)
    elif config('install_type') == 'archive-url':
        install_from_archive_url(config('install_url'), dest)
    elif config('install_type') == 'archive-local':
        install_from_archive_local(config('install_file'), dest)
    else:
        raise DateraException("Unknown install type {}".format(
            config('install_type')))


def install_from_github(url, tag, dest):
    dlog("Trying to install from github")
    try:
        handler = GitUrlFetchHandler()
        ddir = handler.install(url, branch=tag)
        if os.path.exists(dest):
            dlog("Removing existing directory at {}".format(dest))
            shutil.rmtree(dest)
        shutil.copytree(os.path.join(ddir, "src", "datera"), dest)
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
        shutil.copytree(os.path.join(ddir, "src", "datera"), dest)
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
        shutil.copytree(os.path.join(ddir, "src", "datera"), dest)
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
            out = subprocess.check_output(
                "python -c 'import cinder; print(cinder.__file__)'")
            return os.path.dirname(out)
        except subprocess.CalledProcessError:
            try:
                out = subprocess.check_output(
                    "python3 -c 'import cinder; print(cinder.__file__)'")
                return os.path.dirname(out)
            except subprocess.CalledProcessError:
                dlog("Could not determine Cinder install location.  Cinder "
                     "must either be installed in the currently running "
                     "python or in the system python")
                raise


def get_install_dest():
    c = find_cinder_install()
    path = os.path.join(c, "volume", "drivers")
    if not os.path.exists(path):
        path = os.path.join(c, "cinder", "volume", "drivers")
    return path
