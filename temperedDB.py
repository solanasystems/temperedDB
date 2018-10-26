#!/usr/bin/env python3
"""-------------------
TEMPER for RaspberryPi
  logging to MySQL
-------------------"""
__version__ = '0.0.3'

import os
import sys
import time
import datetime
import subprocess
import argparse
import json
# installed to "sudo apt-get -y install python3-mysql.connector"
import mysql.connector


#===============================================================================
class Lsql():
    """--------------------------------------
    MySQL control class
    Server infomation setting from JSON file
     and exec command infomation setting
    --------------------------------------"""
    def __init__(self):
        try:
            _fh = open('{}/{}'.format(os.path.dirname(os.path.abspath(__file__)),
                                      'temper.json'
                                     ), 'r')
            _jh = json.load(_fh)
        except FileNotFoundError as exp:
            sys.stderr.write('{}\n'.format(exp))
            sys.stderr.flush()
            exit(-1)
        except IOError as exp:
            sys.stderr.write('IOError:{}\n'.format(exp))
            sys.stderr.flush()
            exit(-1)
        else:
            self.sql_user = _jh['mysql']['user']
            self.sql_passwd = _jh['mysql']['passwd']
            self.sql_host = _jh['mysql']['host']
            self.sql_db = _jh['mysql']['db']
            self.command_pass = _jh['command']['pass']
            self.command_exe = _jh['command']['exe']
            self.command_param = _jh['command']['param']
            self.command = ""
        #===== MySQL Connection try loop =====
        _try_count = 0
        while True:
            if _try_count > 10: #retry回数の上限(10回)を超えたら30分待つ
                _try_count = 0
                time.sleep(1800)
            try:
                self.connection = mysql.connector.connect(
                    user=self.sql_user,
                    passwd=self.sql_passwd,
                    host=self.sql_host,
                    db=self.sql_db) #MySQLサーバーへ接続
                if self.connection.is_connected(): #接続の有効性を検証
                    self.cursor = self.connection.cursor()
                    self.connection.ping(reconnect=True) #タイムアウトで切れないように
                    break
                else:
                    _try_count = _try_count + 1 #接続に失敗していたらretryカウンタをUPして３分後にtry
                    sys.stderr.write('TRY({}/10):mysql connect retry\n'.format(_try_count))
                    sys.stderr.flush()
                    time.sleep(180)
            except mysql.connector.Error as exp: #MySQLの接続で例外が発生
                _try_count = _try_count + 1 #retryカウンタをUPして３分後にtry
                sys.stderr.write("TRY({}/10):{}\n".format(_try_count, exp))
                sys.stderr.flush()
                time.sleep(180)
                continue
        #===== exec command line making =====
        if self.command_pass is None:
            self.command_pass = os.path.dirname(os.path.abspath(__file__))
        elif self.command_exe is None:
            sys.stdout.write("ERROR:json setting error = exec command name not funud\n")
            exit(-1)
        else:
            pass
        self.command = "{}/{} {}".format(self.command_pass, self.command_exe, self.command_param)

#============================================================================
if __name__ == "__main__":

    #=== Confirm start parameter ===
    # -w or --wait option is
    #       setting command exec wait time
    # --version option is displays the version of this  script.
    PARSER = argparse.ArgumentParser(description='tempered')
    PARSER.add_argument('-w', '--wait', metavar='second',
                        nargs='?', const='1', default='30',
                        type=int, help='wait time(=default:30)')
    PARSER.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    ARGS = PARSER.parse_args()

    BTEMP = 0.0
    time.sleep(10)

    L_SQL = Lsql()

    ERROR_COUNT = 0
    try:
        while True:
            if ERROR_COUNT > 10:
                sys.stderr.write("CONNECTION ERROR ReTry 10count OVER!(EXIT)\n")
                exit(-1)
            RES = subprocess.run("sudo {}".format(L_SQL.command),
                                 stdout=subprocess.PIPE,
                                 shell=True,
                                 universal_newlines=True)
            if RES.returncode == 1:
                sys.stderr.write('error temper run\n')
                sys.stderr.flush()
                exit(1)
            elif RES.returncode != 0:
                time.sleep(180)
                ERROR_COUNT = ERROR_COUNT + 1
                continue
            try:
                ATEMP = float(RES.stdout)
            except ValueError:
                time.sleep(180)
                ERROR_COUNT = ERROR_COUNT + 1
                continue
            BTEMP = ATEMP
            COMMAND = 'insert into TEMPER(DATE,TEMPER) values("{}","{}")'.format(
                datetime.datetime.now(), BTEMP)
            try:
                L_SQL.cursor.execute(COMMAND)
                L_SQL.connection.commit()
            except mysql.connector.Error as exp:
                sys.stderr.write('{0}\n'.format(exp))
                sys.stderr.flush()
                del L_SQL
                L_SQL = Lsql()
                ERROR_COUNT = ERROR_COUNT + 1
                continue
            time.sleep(ARGS.wait)
    except KeyboardInterrupt as exp:
        sys.stderr.write('temper.py exit:KeyboardInterrupt({})\n'.format(exp))
        sys.stderr.flush()
        exit(0)
