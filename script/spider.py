#!/bin/env python

import argparse
import datetime
from utils import ip_address, config_file
from packtpub import Packpub
from upload import Upload, SERVICE_DRIVE, SERVICE_DROPBOX, SERVICE_SCP
from database import Database, DB_FIREBASE
from logs import *
from notify import Notify, SERVICE_GMAIL, SERVICE_IFTTT, SERVICE_JOIN

def parse_types(args):
    if args.types is None:
        return [args.type]
    else:
        return args.types

def run(packpub, args, config):
    packpub.run()

    if args.dev:
        log_json(packpub.info)

    log_success('[+] book successfully claimed')

    upload = None
    upload_info = None
    packpub_info = None

    if not args.claimOnly:
        types = parse_types(args)

        packpub.download_ebooks(types)

        if args.extras:
            packpub.download_extras()

        if args.archive:
            raise NotImplementedError('not implemented yet!')

        if args.upload is not None:
            upload = Upload(config, args.upload)
            upload.run(packpub.info['paths'])

        if upload is not None and upload is not SERVICE_DRIVE:
            log_warn('[-] skip store info: missing upload info')
        elif args.store is not None:
            Database(config, args.store, packpub.info, upload.info).store()

    if args.notify:
        if upload is not None:
            upload_info = upload.info

        Notify(config, packpub.info, upload_info, args.notify).run()

def main():
    parser = argparse.ArgumentParser(
        description='Download FREE eBook every day from www.packtpub.com',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        version='2.2.0')

    parser.add_argument('-c', '--config', required=True, help='configuration file')
    parser.add_argument('-d', '--dev', action='store_true', help='only for development')
    parser.add_argument('-e', '--extras', action='store_true', help='download source code (if exists) and book cover')
    parser.add_argument('-u', '--upload', choices=[SERVICE_DRIVE, SERVICE_DROPBOX, SERVICE_SCP], help='upload to cloud')
    parser.add_argument('-a', '--archive', action='store_true', help='compress all file')
    parser.add_argument('-n', '--notify', choices=[SERVICE_GMAIL, SERVICE_IFTTT, SERVICE_JOIN], help='notify after claim/download')
    parser.add_argument('-s', '--store', choices=[DB_FIREBASE], help='store info')
    parser.add_argument('-o', '--claimOnly', action='store_true', help='only claim books (no downloads/uploads)')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--type', choices=['pdf', 'epub', 'mobi'],
        default='pdf', help='specify eBook type')
    group.add_argument('--all', dest='types', action='store_const',
        const=['pdf', 'epub', 'mobi'], help='all eBook types')

    args = parser.parse_args()

    now = datetime.datetime.now()
    log_info('[*] {date} - Fetching today\'s books'.format(date=now.strftime("%Y-%m-%d %H:%M")))

    packtpub = None

    try:
        config = config_file(args.config)

        #ip_address()
        log_info('[*] getting daily free ebook')
        packpub = Packpub(config, args.dev)
        run(packpub, args, config)

    except KeyboardInterrupt:
        log_error('[-] interrupted manually')

    except Exception as e:
        log_debug(e)
        if args.notify:
            Notify(config, None, None, args.notify).sendError(e, 'global')

    log_info('[*] done')

if __name__ == '__main__':
    print ("""
                      __   __              __                                   __
    ____  ____ ______/ /__/ /_____  __  __/ /_        ______________ __      __/ /__  _____
   / __ \/ __ `/ ___/ //_/ __/ __ \/ / / / __ \______/ ___/ ___/ __ `/ | /| / / / _ \/ ___/
  / /_/ / /_/ / /__/ ,< / /_/ /_/ / /_/ / /_/ /_____/ /__/ /  / /_/ /| |/ |/ / /  __/ /
 / .___/\__,_/\___/_/|_|\__/ .___/\__,_/_.___/      \___/_/   \__,_/ |__/|__/_/\___/_/
/_/                       /_/

Download FREE eBook every day from www.packtpub.com
@see github.com/niqdev/packtpub-crawler
        """)
    main()
