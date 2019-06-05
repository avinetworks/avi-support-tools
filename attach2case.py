#!/usr/bin/env python

########################################################################
#
# AVI CONFIDENTIAL
# __________________
#
# [2013] - [2019] Avi Networks Incorporated
# All Rights Reserved.
#
# NOTICE: All information contained herein is, and remains the property
# of Avi Networks Incorporated and its suppliers, if any. The intellectual
# and technical concepts contained herein are proprietary to Avi Networks
# Incorporated, and its suppliers and are covered by U.S. and Foreign
# Patents, patents in process, and are protected by trade secret or
# copyright law, and other laws. Dissemination of this information or
# reproduction of this material is strictly forbidden unless prior written
# permission is obtained from Avi Networks Incorporated.
#
########################################################################

"""
A command-line utility to attach log files to cases on the Avi Networks
portal.

Positional arguments
--------------------
  CASE-NUMBER           case number to attach files to

  FILE                  files to attach to the case

Optional arguments
------------------
  -h, --help
                        show help message and exit

  -c CONFIG, --config CONFIG
                        Path to configuration file (JSON)
                        (default: None)

  -d, --debug
                        Enable HTTP debug (default: False)

  -P, --progress
                        Display progress indicator (default: False)


Configuration file details
--------------------------
All optional command-line arguments may be specified in a config file
that is read at run-time.  The full path to the config file is passed
as the "-c" or "--config" option as described above.

The file format is JSON.  Key names map to the long optional parameter
names in the list above.

Example:
    {
        "progress": true,
        "logging": {
            ... (see below)
        }
    }


Logging
-------
Logging is optionally configured by means of Python's API for
configuring the logging module by dictionary:
https://docs.python.org/2/library/logging.config.html#logging.config.dictConfig

Logging configuration should be included as part of the configuration
file using the key "logging".

Example in JSON:
    {
        "version": 1,
        "handlers": {
            "h": {
                "formatter": "f",
                "class": "logging.StreamHandler",
                "level": 10
            }
        },
        "formatters": {
            "f": {
                "format": "%(asctime)s %(name) %(levelname) %(message)s"
            }
        },
        "root": {
            "level": 10,
            "handlers": [
                "h"
            ]
        }
    }

"""

import os
import sys
import datetime
import time
import urllib
import urllib2
import argparse
import json
import logging
from time import sleep
from logging.config import dictConfig

VERSION = '2.0.5'

CHUNK_SIZE = 50 * 1024 * 1024

CONNECTION_ERROR = 10
VALIDATION_ERROR = 20
AUTHENTICATION_ERROR = 30
ATTACHMENT_IO_ERROR = 40
CASE_LOOKUP_ERROR = 50
SERVER_ERROR = 60
CONFIG_ERROR = 70
UNKNOWN_ERROR = 127

EXIT_CODES = {
    CONNECTION_ERROR:  'CONNECTION ERROR',
    VALIDATION_ERROR:  'VALIDATION ERROR',
    AUTHENTICATION_ERROR:  'AUTHENTICATION ERROR',
    ATTACHMENT_IO_ERROR:  'ATTACHMENT IO ERROR',
    CASE_LOOKUP_ERROR:  'CASE LOOKUP ERROR',
    SERVER_ERROR:  'SERVER ERROR',
    CONFIG_ERROR: 'CONFIGURATION ERROR',
    UNKNOWN_ERROR:  'UNKNOWN ERROR',
}

STATE_FILE = os.path.expanduser(
    '~/.config/avi-networks/case-attachments/oauth.txt')

OAUTH_CLIENT_ID = '3MVG9JZ_r.QzrS7hMLCl6ttT5SrxFJSQe5lACnE69kKOENic9.dLtS7.QDapmZT5p79wiEYDQ.8oAWSb.Ni97'
OAUTH_URL = 'https://cslogin.avinetworks.com/services/oauth2/token'
HOSTNAME = 'https://avi-api.avinetworks.com'
BUCKET = 'avidownloads'
REGION = 'us-west-2'


class Attach2CaseError(Exception):
    def __init__(self, message, code, *args):
        self.message = message
        self.code = code
        super(Attach2CaseError, self).__init__(message, code, *args)


class Attach2Case(object):

    def __init__(self):
        self.settings = self.get_settings()
        self.logger = self.get_logger()
        self.case_number = self.settings['case']
        self.filenames = self.settings['files']
        self._refresh_token = None
        self._access_token = None

        # try to read the refresh token from the state file
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'rb') as fh:
                    self._refresh_token = fh.read()
                return
            except ValueError:
                pass

    def get_settings(self):
        """
        Returns a dictionary of the command-line parameters passed to the
        script, merged with the config file settings, if it exists.

        CLI parameters override config file settings.
        """
        parser = argparse.ArgumentParser(
            description='Attaches files to a case on the Avi Networks portal.')
        parser.add_argument(
            'case', metavar='CASE-NUMBER',
            help='case number to attach files to')
        parser.add_argument(
            'files', metavar='FILE', nargs='+',
            help='files to attach to the case')
        parser.add_argument(
            '-c', '--config',
            help='Path to configuration file (JSON) (default: None)')
        parser.add_argument(
            '-d', '--debug', action='store_true',
            help='Enable HTTP debug (default: False)')
        parser.add_argument(
            '-P', '--progress', action='store_true',
            help='Display progress indicator (default: False)')

        cli_args = vars(parser.parse_args())

        config = {
            'debug': False,
            'progress': False,
        }

        if cli_args.get('config', None):
            if not os.path.exists(cli_args['config']):
                raise Attach2CaseError(
                    '%(config)s does not exist' % cli_args, CONFIG_ERROR)

            with open(cli_args['config']) as fp:
                try:
                    config.update(json.load(fp))
                except Exception as e:
                    raise Attach2CaseError(
                        '%s parse error: %s' % (cli_args['config'], e),
                        CONFIG_ERROR)

        # cli parameters override config file parameters
        config.update(dict([
            (k, v) for k, v in cli_args.iteritems() if v is not None]))

        return config

    def get_oauth_tokens(self):
        """
        Retrieves the refresh and access tokens from the IdP by means of
        remote authorisation
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {
            'response_type': 'device_code',
            'client_id': OAUTH_CLIENT_ID,
        }
        method = 'post'

        request = urllib2.Request(
            OAUTH_URL, headers=headers, data=urllib.urlencode(payload))
        request.get_method = lambda: method.upper()
        response = urllib2.urlopen(request)
        data = json.load(response)

        print '\nThis script needs to be authenticated for future use.'
        print '\nTo continue, please open the URL below in any browser and ' \
            'enter the following code: {}'.format(data['user_code'])
        print data['verification_uri']

        payload = {
            'grant_type': 'device',
            'client_id': OAUTH_CLIENT_ID,
            'code': data['device_code']
        }

        print '\nWaiting for authorization...'
        started = datetime.datetime.now()
        while 1:
            # sleep for the poll interval that the IdP recommends
            time.sleep(data['interval'])

            # the verification code remains active for 10 minutes only
            elapsed = (datetime.datetime.now() - started)
            if elapsed.total_seconds() > 600:
                raise Attach2CaseError(
                    'Authorization step was not completed in time',
                    AUTHENTICATION_ERROR)

            request = urllib2.Request(
                OAUTH_URL, headers=headers, data=urllib.urlencode(payload))
            request.get_method = lambda: method.upper()

            try:
                response = urllib2.urlopen(request)
                data = json.load(response)
                if not os.path.exists(os.path.dirname(STATE_FILE)):
                    os.makedirs(os.path.dirname(STATE_FILE))

                with open(STATE_FILE, 'wb') as fh:
                    fh.write(data['refresh_token'])

                self._refresh_token = data['refresh_token']
                self._access_token = data['access_token']

                print '...done\n'

                return
            except urllib2.HTTPError:
                # keep polling
                pass

    @property
    def refresh_token(self):
        """
        Returns the cached refresh token, or requests the user to
        remotely authorize the script to obtain a new refresh token from
        the IdP
        """
        if not self._refresh_token:
            self.get_oauth_tokens()

        return self._refresh_token

    @property
    def access_token(self):
        """
        Returns the cached access token, or retrieves a new one from the
        IdP by means of the refresh token
        """
        if not self._access_token:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            payload = urllib.urlencode({
                'grant_type': 'refresh_token',
                'client_id': OAUTH_CLIENT_ID,
                'refresh_token': self.refresh_token
            })

            request = urllib2.Request(OAUTH_URL, headers=headers, data=payload)
            request.get_method = lambda: 'POST'

            try:
                response = urllib2.urlopen(request)
                data = json.load(response)
                self._access_token = data['access_token']
            except urllib2.HTTPError:
                # the refresh token has expired or become invalid
                self._refresh_token = None
                self.get_oauth_tokens()

        return self._access_token

    def get_logger(self):
        """
        Sets up the logger with config from the config file if available
        """
        if 'logging' in self.settings:
            try:
                dictConfig(self.settings['logging'])
            except Exception as e:
                raise Attach2CaseError(
                    'Invalid logging configuration: %s' % e, CONFIG_ERROR)
        else:
            logging.basicConfig()

        if self.settings.get('debug', False):
            http_logger = urllib2.HTTPHandler(debuglevel=1)
            https_logger = urllib2.HTTPSHandler(debuglevel=1)
            opener = urllib2.build_opener(http_logger, https_logger)
            urllib2.install_opener(opener)

        return logging.getLogger('attach2case')

    def get_request(self, url, method, headers, payload=None):
        """
        Returns a Request object for the url, method, headers and payload.
        """
        request = urllib2.Request(url, headers=headers, data=payload)
        request.get_method = lambda: method.upper()
        return request

    def get_response(self, request):
        """
        Takes a Request object and retuns the Response object.

        Raises exception for any HTTP status code >= 400.
        """
        try:
            return urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            error_code = SERVER_ERROR
            if e.code in (401, 403):
                error_code = AUTHENTICATION_ERROR
            if e.code in (400, 404):
                error_code = VALIDATION_ERROR
            raise Attach2CaseError(
                u'%s %s\n%s' % (e.code, e.reason, e.read()), error_code)
        except urllib2.URLError as e:
            raise Attach2CaseError(e.reason, CONNECTION_ERROR)
        except Exception as e:
            raise Attach2CaseError(e, CONNECTION_ERROR)

    def initialise_attachment(self, filename):
        """
        Initialises a multipart case attachment upload for the given
        case and filename.

        Returns the attachment presigned chunk URLs from the server.
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.access_token),
        }

        url = '{}/rest/case-attachment/{}/initiate'.format(
            HOSTNAME, self.case_number)

        payload = json.dumps({
            'fileName': os.path.basename(filename),
            'fileSize': os.path.getsize(filename),
            'chunkSize': CHUNK_SIZE,
            'bucket': BUCKET,
            'region': REGION,
            })

        headers['Content-Length'] = len(payload)

        retry = True
        while 1:
            request = self.get_request(url, 'post', headers, payload)
            try:
                response = self.get_response(request)
                return json.load(response)
            except Attach2CaseError as e:
                if retry and e.error_code == AUTHENTICATION_ERROR:
                    retry = False
                    # setting access_token to None forces token refresh
                    self._access_token = None
                    headers['Authorization'] = 'Bearer {}'.format(
                        self.access_token)
                    continue
                raise

    def complete_attachment(self, filename, upload_id, e_tags):
        """
        Initialises a multipart case attachment upload for the given
        filename.

        Returns the attachment presigned chunk URLs from the server.
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer {}'.format(self.access_token),
        }

        url = '{}/rest/case-attachment/{}/complete'.format(
            HOSTNAME, self.case_number)

        payload = json.dumps({
            'filename': os.path.basename(filename),
            'uploadId': upload_id,
            'partETags': e_tags,
            'bucket': BUCKET,
            'region': REGION,
            })

        headers['Content-Length'] = len(payload)

        retry = True
        while 1:
            request = self.get_request(url, 'post', headers, payload)
            try:
                response = self.get_response(request)
                return json.load(response)
            except Attach2CaseError as e:
                if retry and e.error_code == AUTHENTICATION_ERROR:
                    retry = False
                    # setting access_token to None forces token refresh
                    self._access_token = None
                    headers['Authorization'] = 'Bearer {}'.format(
                        self.access_token)
                    continue
                raise

    def upload_chunk(self, url, offset, chunk):
        """
        Uploads a chunk.

        Returns the offset.
        """
        headers = {
            'Content-Type': 'application/offset+octet-stream',
            'Accept': '*/*'
        }

        request = self.get_request(url, 'put', headers, chunk)

        retries = 0
        while 1:
            try:
                response = self.get_response(request)
                break
            except Exception as e:
                retries += 1

                if retries < 4:
                    self.logger.info(
                        'Retrying chunk upload to %s after %d failed attempts '
                        '- last error was: %s' % (url, retries, e))
                    sleep(5)
                else:
                    raise

        status_code = response.getcode()
        if status_code < 200 or status_code >= 300:
            raise Attach2CaseError(
                'Failed to upload attachment chunk: status code %s' %
                status_code, SERVER_ERROR)

        return response.info().getheader('ETag')

    def upload_attachment(self, filename, urls):
        """
        Chunks and uploads filename to URL.
        """
        i = 0
        offset = 0
        e_tags = []

        try:
            size = os.path.getsize(filename)
        except Exception as e:
            raise Attach2CaseError(e, ATTACHMENT_IO_ERROR)

        try:
            with open(filename, 'rb') as fp:
                while offset < size:
                    if self.settings.get('progress', False):
                        # progress indicator
                        sys.stdout.write(
                            '\b\b\b\b%d%%' % ((offset / float(size)) * 100))
                        sys.stdout.flush()

                    fp.seek(offset)
                    chunk = fp.read(CHUNK_SIZE)
                    e_tags.append(self.upload_chunk(
                        urls[i].encode('utf-8'), offset, chunk))

                    offset += len(chunk)
                    i += 1

                if self.settings.get('progress', False):
                    # progress indicator
                    sys.stdout.write(
                        '\b\b\b\b%d%%\n' % ((offset / float(size)) * 100))
                    sys.stdout.flush()
        except Attach2CaseError:
            raise
        except Exception as e:
            raise Attach2CaseError(e, ATTACHMENT_IO_ERROR)

        return e_tags

    def __call__(self):
        exit_code = 0
        for filename in self.filenames:
            try:
                data = self.initialise_attachment(filename)
                e_tags = self.upload_attachment(filename, data['partUrls'])
                self.complete_attachment(filename, data['uploadId'], e_tags)
            except Attach2CaseError as e:
                exit_code = e.code
                self.logger.error(
                    'Error %s (%s) while processing file %s: %s' % (
                        e.code, EXIT_CODES[e.code], filename, e.message))
            except Exception as e:
                self.logger.exception(
                    'Unknown error while processing file %s: %s' % (
                        filename, e))
                exit_code = UNKNOWN_ERROR

        if exit_code:
            sys.exit(exit_code)


if __name__ == '__main__':
    Attach2Case()()
