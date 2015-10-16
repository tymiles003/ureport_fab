from fabric.context_managers import settings, cd
from fabric.operations import run, sudo, put

__author__ = 'kenneth'


REMOTE_ROOT_DIR_PROD = '/var/www/ureport_prod/'
REMOTE_ROOT_DIR_TEST = '/var/www/ureport_test/'

REMOTE_PROD_VIRTUALENV_DIR = '/var/www/.virtualevns/ureport/'
REMOTE_TEST_VIRTUALENV_DIR = '/var/www/.virtualevns/ureport_test/'

REMOTE_USER = 'www-data'

GIT_REPOSITORY = 'https://github.com/rapidpro/ureport.git'


def deploy(to_prod=False, user=None, workon_path=None, source=GIT_REPOSITORY, git_hash=None, root_dir=None,
           prep_server=False, syncdb=False):
    user = user or REMOTE_USER
    if to_prod:
        path = root_dir or REMOTE_ROOT_DIR_PROD
        workon_path = workon_path or REMOTE_PROD_VIRTUALENV_DIR
        ureport_proc_name = 'ureport'
        celery_proc_name = 'ureport_celery'
        settings_file = 'resources/settings/settings.py.example'
    else:
        path = root_dir or REMOTE_ROOT_DIR_TEST
        workon_path = workon_path or REMOTE_TEST_VIRTUALENV_DIR
        ureport_proc_name = 'ureport_test'
        celery_proc_name = 'ureport_celery_test'
        settings_file = 'resources/settings/settings.test.py.example'

    with settings(warn_only=True):
        if run("test -d %s" % path).failed:
            run("git clone %s %s" % (source, path))
            with cd(path):
                run("git config core.filemode false")

    with cd(path):
        run("git stash")
        if not git_hash:
            run("git pull origin master")
        else:
            run("git fetch")
            run("git checkout %s" % git_hash)
        put(local_path=settings_file, remote_path=path+'ureport/settings.py')
        sudo("chown -R %s:%s ." % (user, user))
        sudo("chmod -R ug+rw .")
        run("%sbin/pip install -r pip-freeze.txt" % workon_path)
        run("%sbin/pip install uwsgi" % workon_path)
        if prep_server:
            _prepare_server(user)
        if syncdb:
            run('%sbin/python manage.py syncdb' % workon_path)
    sudo('supervisorct restart %s' % ureport_proc_name)
    sudo('supervisorct restart %s' % celery_proc_name)


def _install_nginx():
    with settings(warn_only=True):
        if sudo("service nginx status").failed:
            sudo("apt-get install nginx")

    put(local_path='resources/nginx/ureport.conf.example', '/etc/nginx/sites-enabled/ureport.conf', use_sudo=True)
    put(local_path='resources/nginx/ureport_test.conf.example', '/etc/nginx/sites-enabled/ureport_test.conf', use_sudo=True)


def _install_redis():
    with settings(warn_only=True):
        if sudo("service redis-server status").failed:
            sudo("apt-get install redis-server")


def _install_postgres():
    with settings(warn_only=True):
        if sudo("service postgresql status").failed:
            sudo("apt-get install postgresql-9.4")
            sudo("apt-get install postgresql-server-dev-9.4")
    put(local_path='resources/postgres/postgres.conf.example', remote_path='/etc/postgresql/9.3/main/pg_hba.conf', use_sudo=True)
    sudo("service postgresql restart")
    run("createdb -Upostgres ureport")
    run("createdb -Upostgres ureport_test")


def _install_supervisor():
    with settings(warn_only=True):
        if sudo("service supervisor status").failed:
            sudo("apt-get install supervisor")

    put(local_path='resources/supervisor/ureport.conf.example', remote_path='/etc/supervisor/conf.d/ureport.conf', use_sudo=True)
    put(local_path='resources/supervisor/celery.conf.example', remote_path='/etc/supervisor/conf.d/celery.conf', use_sudo=True)
    put(local_path='resources/supervisor/ureport_test.conf.example', remote_path='/etc/supervisor/conf.d/ureport_test.conf',
        use_sudo=True)
    put(local_path='resources/supervisor/celery.conf.example', remote_path='/etc/supervisor/conf.d/celery_test.conf',
        use_sudo=True)
    sudo("supervisorctl update")


def _prepare_server(user):
    log_path = '/var/log/ureport'
    with settings(warn_only=True):
        if run('test -d %s' % log_path).failed:
            run('mkdir %s' % log_path)
    sudo('chown -R %s:%s %s' % (user, user, log_path))
    sudo('chmod -R ug+rw %s' % log_path)

    _install_supervisor()
    _install_redis()
    _install_postgres()
    _install_nginx()
