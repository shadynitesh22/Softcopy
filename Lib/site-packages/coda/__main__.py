# -*- coding: utf-8 -*-
#
# Main entry point for coda script
# 
# @author <bprinty@gmail.com>
# ------------------------------------------------


# imports
# -------
import os
import sys
from functools import wraps
import argparse
import json
import coda


# decorators
# ----------
def accumulate(func):
    """
    Accumulate all input file arguments into collection.
    """
    @wraps(func)
    def _(args):
        files = []
        for fi in args.files:
            if os.path.isdir(fi):
                cl = coda.Collection(fi)
                files.extend(cl.files)
            else:
                files.append(coda.File(fi))
        args.collection = coda.Collection(files=files)
        return func(args)
    return _


# args
# ----
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', help='Path to config file to use for default coda options.', default=None)
subparsers = parser.add_subparsers()


# version
# -------
parser_version = subparsers.add_parser('version')
parser_version.set_defaults(func=lambda x: sys.exit(coda.__version__))


# status
# ------
def status(args):
    """
    Check status of running databases and configuration.
    """
    sys.stderr.write('\nDatabase configuration:\n')
    opt = coda.db.session.options
    for key in opt:
        sys.stderr.write('    {}: {}\n'.format(key, opt[key]))
    sys.stderr.write('\nTesting connection ... ')
    try:
        coda.find_one({'thisisatest': 'thisisnotatest'})
        sys.stderr.write('good to go!\n\n')
    except:
        sys.stderr.write('could not connect!\n\n')
    return

parser_status = subparsers.add_parser('status')
parser_status.set_defaults(func=status)


# list
# ----
def listdir(args):
    """
    List tracked files under the user's current directory.
    """
    wd = args.path.replace('/', '\/')
    cl = coda.find({'path': {'$regex': '^' + wd + '.*'}})
    if os.path.isdir(args.path):
        if cl is not None:
            sys.stdout.write('\n'.join(map(str, cl.files)) + '\n')
    else:
        fi = cl[0]
        md = fi.metadata.json()
        if len(md) != 0:
            del md['_id']
            sys.stdout.write(fi.path + '\n')
            sys.stdout.write(json.dumps(md, sort_keys=True, indent=4) + '\n')
        else:
            sys.stdout.write('No metadata found for {}\n'.format(fi.name))
    return

parser_list = subparsers.add_parser('list')
parser_list.add_argument('path', nargs='?', help='Directory to list tracked files for.', default=os.getcwd())
parser_list.set_defaults(func=listdir)


# find
# ----
def find(args):
    """
    Find files with associated keys and metadata.
    """
    cl = coda.find({args.key: args.value})
    if cl is not None:
        sys.stdout.write('\n'.join(map(str, cl.files)) + '\n')
    return

parser_find = subparsers.add_parser('find')
parser_find.add_argument('key', help='Metadata key to search with.')
parser_find.add_argument('value', help='Metadata value to search for.')
parser_find.set_defaults(func=find)


# add
# ---
@accumulate
def add(args):
    """
    Add file to internal database for tracking.
    """
    coda.add(args.collection)
    return

parser_add = subparsers.add_parser('add')
parser_add.add_argument('files', nargs='+', help='File or collection to add to tracking.')
parser_add.set_defaults(func=add)


# delete
# ------
@accumulate
def delete(args):
    """
    Delete file from internal database for tracking.
    """
    coda.delete(args.collection)
    return

parser_delete = subparsers.add_parser('delete')
parser_delete.add_argument('files', nargs='+', help='File or collection to add to tracking.')
parser_delete.set_defaults(func=delete)


# tag 
# ---
@accumulate
def tag(args):
    """
    Tag file with metadata.
    """
    args.collection.metadata[args.key] = args.value
    coda.add(args.collection)
    return

parser_tag = subparsers.add_parser('tag')
parser_tag.add_argument('key', help='Metadata key to tag file with.')
parser_tag.add_argument('value', help='Metadata value to tag file with.')
parser_tag.add_argument('files', nargs='+', help='File or collection to tag with metadata.')
parser_tag.set_defaults(func=tag)


# exec
# ----
def main():
    args = parser.parse_args()
    if args.config:
        coda.db.__user_config__ = args.config
        coda.db.options()
    args.func(args)


if __name__ == "__main__":
    main()

