#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Janusz Kowalczyk'

from time import sleep
from fabric.api import *
from flaskrilio.helpers.common import *
from flaskrilio.helpers.EC2Conn import EC2Conn
from ec2_configuration import CONN_CONFIG, SERVER_TYPES

# tasks:
# http://docs.fabfile.org/en/1.8/tutorial.html
# *- spawn ec2 instance
# *- install dependencies
# *- deploy code
# *- start flaskrilio in background
# *- run behave tests
# *- download junit report
# *- download flaskrilio db
# *- download all the logs (flaskrilio, behave, plain output)

log = setup_console_logger(name="fabfile", level="DEBUG")
log.debug(CONN_CONFIG)

CONN = None # will store connection details
INSTANCES = [] # will hold all created instances
DIST = ""

# the servers where the commands are executed
#env.hosts = []
# the user to use for the remote commands
env.user = CONN_CONFIG['user_name']
# private key used to connect to EC2 instances
env.key_filename = CONN_CONFIG['key_path']


def bring_it_on():
    """A Fabric task, that configures all the instances and runs all the tests"""
    # access global variables
    try:
        execute(pack)
        execute(start_ec2_instances)
        execute(deploy)
        execute(start_flaskrilio)
        execute(test)
        execute(stop_flaskrilio)
    finally:
        try:
            execute(download_results)
        finally:
            execute(terminate_ec2_instances)


def pack():
    # create a new source distribution as tarball
    local('python setup.py sdist --formats=gztar', capture=False)


def deploy():
    global DIST
    # figure out the release name and version
    DIST = local('python setup.py --fullname', capture=True).strip()
    print DIST
    log.debug("Distribution name:%s " % DIST)
    # upload the source tarball to the temporary folder on the server
    print env
    print env.hosts
    print "Sleeping for 30s before proceeding"
    sleep(30)
    put('dist/%s.tar.gz' % DIST, '/tmp/flaskrilio.tar.gz')
    # create a place where we can unzip the tarball, then enter
    # that directory and unzip it
    run('mkdir /tmp/flaskrilio')
    with cd('/tmp/flaskrilio'):
        run('tar xzf /tmp/flaskrilio.tar.gz')
        # now setup the package with our virtual environment's
        # python interpreter
        print "\n\n\n"
        sudo('apt-get install -qq python-setuptools', timeout=60)
        print "\n\n\n"
        sudo('/usr/bin/python %s/setup.py install --quiet' % DIST)
    # now that all is set up, delete the folder again
    #run('rm -rf /tmp/flaskrilio /tmp/flaskrilio.tar.gz')


def start_ec2_instances():
    """Sets up EC2 instances"""
    # access global variables
    global CONN
    global INSTANCES
    #global env

    # pass the CONN_ONFIG as a dict of named parameters
    CONN = EC2Conn(**CONN_CONFIG)
    CONN.connect()

    print "\n\n************************************************************"
    print "Spawning '1' instance. Started @ %s " % (get_datetime())
    INSTANCES = CONN.create_instances(SERVER_TYPES['flaskrilio'], 1)
    print "Instance spawned successfully. Completed @ %s " % (get_datetime())
    print "************************************************************\n\n"

    print "\n\n************************************************************"
    print "Adding tags to instances"
    INSTANCES[0].add_tag('Name', 'flaskrilio-CallConnect-tests')
    print "Instances were tagged successfully"
    print "************************************************************\n\n"

    print "\n\n************************************************************"
    print "Craeted instance (%s) " % (INSTANCES[0].ip_address)
    print "Test runner host is accessible at %s " % (INSTANCES[0].public_dns_name)
    print "************************************************************\n\n"
    env.hosts.append(INSTANCES[0].ip_address)
    print env.hosts
    pass


def terminate_ec2_instances():
    """Terminates all the spawned EC2 instances from the INSTANCES list"""
    global INSTANCES
    print "Terminating all instances"
    for i in INSTANCES:
        print "Termininating instance ID: %s IP: %s PUBLIC_DNS_NAME: %s \n" % (i.id, i.ip_address, i.public_dns_name)
        i.terminate()


def start_flaskrilio():
    global DIST
    cd('/tmp/flaskrilio/%s/flaskrilio' % DIST)
    run('sudo nohup MODE=EC2 flaskriliosrv.py &')


def stop_flaskrilio():
    run('sudo ps eax | grep [p]ython')


def download_results():
    global DIST
    # download ./results folder to the current directory
    get('/tmp/flaskrilio/%s/flaskrilio/reports' % DIST, '%(path)s')


def test():
    global DIST
    run('cd /tmp/flaskrilio/%s/flaskrilio && MODE=EC2 behave -v --junit --junit-directory "./reports"' % DIST)
