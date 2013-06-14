#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Get in the car, our Delorian is waiting!
from __future__ import print_function, with_statement
from time import sleep, time as unix_timestamp
from shutil import copy2 as copy_file
import os, sys, yaml

def config_is_valid(config):
    """This will check if the config file you provided is valid or not."""
    # It has to be a dictionary, of course
    if isinstance(config, dict):
        # It has to have these three keys
        if set(['trigger', 'backups_dir', 'files']).issubset(config.keys()):
            trigger = config['trigger']
            # Backups dir has to exist and be a directory
            if os.path.exists(config['backups_dir']) and os.path.isdir(config['backups_dir']):
                # trigger has to be a valid trigger and files a list of files
                if trigger in ('time_amount', 'copies_per_day', 'hourly', 'daily') and isinstance(config['files'], list):
                    valid = True
                    # let's check if the files (or directories) exist
                    for file in config['files']:
                        if not os.path.exists(file):
                            valid = False
                            break
                    if valid:
                        # Finally, the config has to have a config key named after the trigger value specified (except for hourly and daily)
                        if trigger not in ('hourly', 'daily'):
                            if trigger in config.keys():
                                return True
                        else:
                            return True
    # If we're here there was something wrong in the config file
    return False

def load_config():
    """Load the config.yml file."""
    # Does the config file exist?
    config_file = os.path.dirname(os.path.abspath(__file__)) + '/config.yml'
    if os.path.exists(config_file):
        try:
            # Open, read and check if the config file is valid, if it is return it
            with open(config_file) as f:
                data = f.read()
            config = yaml.load(data)
            if config_is_valid(config):
                return config
        # We should notice the user if we don't have permissions to access the files
        except IOError, e:
            if e.errno == 13:
                print('Permission denied trying to access the specified files. Check their permissions.')
        except:
            pass
        print('The config.yml you provided is not valid.')
    else:
        print('config.yml does not exist! you must provide a config file.')
    return False
    
def run_trigger(config):
    """Runs the specified trigger."""
    trigger = config['trigger']
    if trigger not in ('hourly', 'daily'):
        trigger_conf = config[trigger]
    
    if trigger == 'time_amount':
        try:
            if not isinstance(trigger_conf, int):
                time_amount = int(trigger_conf)
            else:
                time_amount = trigger_conf
        except:
            print('Error: invalid value given for "time_amount" key in config file. Waiting an integer, %s given.' % trigger_conf.__class__)
            sys.exit()
        sleep(time_amount)
    elif trigger == 'copies_per_day':
        try:
            if not isinstance(trigger_conf, int):
                copies_per_day = int(trigger_conf)
            else:
                copies_per_day = trigger_conf
        except:
            print('Error: invalid value given for "copies_per_day" key in config file. Waiting an integer, %s given.' % trigger_conf.__class__)
            sys.exit()
        sleep(86400 / copies_per_day)
    elif trigger == 'hourly':
        sleep(3600)
    elif trigger == 'daily':
        sleep(86400)
        
def run_backup(config):
    """Performs the copy of the desired files recursively."""
    # Should we copy hidden files and directories?
    copy_hidden = False if not 'backup_hidden_files' in config.keys() else config['backup_hidden_files']
    # Dir where copies will be stored: /your/given/backup/root/backup_timestamp
    backups_dir = config['backups_dir'] + ('' if config['backups_dir'][-1] == '/' else '/') + 'backup_' + str(int(unix_timestamp())) + '/'
    # It's impossible there is already a directory with this timestamp unless you're a time traveler
    # but even though we should check
    if os.path.exists(backups_dir):
        print('Error: backup directory for this timestamp already exist.')
        sys.exit()
    else:
        # Create the directory
        try:
            os.makedirs(backups_dir)
        except:
            print('Error: permission denied. I can\'t create files under ' + config['backups_dir'])
            sys.exit()
    try:
        for file in config['files']:
            # If file is a directory and does not end with / then add it
            if os.path.isdir(file):
                if file[-1] != '/':
                    file += '/'
            # We want to get the file or directory name
            file_name = filter(None, file.split('/'))[-1]
            if os.path.isdir(file):
                dir_name = backups_dir + file_name + '/'
                os.makedirs(dir_name)
                for dirname, dirnames, filenames in os.walk(file):
                    if dirname[-1] != '/':
                        dirname += '/'
                    current_dir = dirname.replace(file, dir_name)
                    # Create the directories under the current directory
                    for directory in dirnames:
                        directory = current_dir + directory + '/'
                        if not (filter(None, directory.split('/'))[-1][0] == '.' and not copy_hidden):
                            os.makedirs(directory.replace(file, dir_name))
                    # Copy the files under the current directory
                    for filename in filenames:
                        filename = dirname + filename
                        if not (filter(None, directory.split('/'))[-1][0] == '.' and not copy_hidden):
                            copy_file(filename, current_dir)
                    # We won't gopy .git directories
                    if '.git' in dirnames:
                        dirnames.remove('.git')
                    # If copy hidden files is not enabled we will discard those files
                    if not copy_hidden:
                        dirnames = [d for d in dirnames if d[0] != '.']
            else:
                copy_file(file, backups_dir)
    except:
        print('Unexpected error. Stoping execution.')
        sys.exit()

def run():
    # Load config and exit if it wasn't valid
    config = load_config()
    if not config:
        sys.exit()
    while True:
        try:
            run_backup(config)
            run_trigger(config)
        except KeyboardInterrupt:
            print('\nProgram terminated.')
            sys.exit()
        except:
            pass
        
if __name__ == '__main__':
    run()