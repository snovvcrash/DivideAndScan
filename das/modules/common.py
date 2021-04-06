#!/usr/bin/env python3

__author__ = '@snovvcrash'
__site__ = 'https://github.com/snovvcrash/DivideAndScan'
__version__ = '0.1.2'

import time
from datetime import datetime, timedelta

BANNER = """\
\033[0;37m -----------------------------------------------------------------------------------------------
\033[0;37m|\033[1;31m  ________  \033[0;37m.__      .__    .___        \033[1;31m_____\033[0;37m              .__\033[1;31m__________\033[0;37m   \033[1;31m                    |
\033[0;37m|\033[1;31m  \\______ \\ \033[0;37m|__|__  _|__| __| _/____   \033[1;31m/  _  \\\033[0;37m   ____    __| _\033[1;31m/   _____/\033[0;37m ____ _____    ____   \033[1;31m |
\033[0;37m|\033[1;31m   |    |  \\\033[0;37m|  \\  \\/ /  |/ __ |/ __ \\ \033[1;31m/  /_\\  \\\033[0;37m /    \\  / __ |\033[1;31m\\_____  \\\033[0;37m_/ ___\\\\__  \\  /    \\   \033[1;31m|
\033[0;37m|\033[1;31m   |    `   \\\033[0;37m  |\\   /|  / /_/ \\  ___/\033[1;31m/    |    \\\033[0;37m   |  \\/ /_/ |\033[1;31m/        \\\033[0;37m  \\___ / __ \\|   |  \\  \033[1;31m|
\033[0;37m|\033[1;31m  /_______  /\033[0;37m__| \\_/ |__\\____ |\\___  >\033[1;31m____|__  /\033[0;37m___|  /\\____ \033[1;31m/_______  /\033[0;37m\\___  >____  /___|  /  \033[1;31m|
\033[0;37m|\033[1;31m          \\/\033[0;37m                 \\/    \\/        \033[1;31m\\/\033[0;37m     \\/      \\/       \033[1;31m\\/\033[0;37m     \\/     \\/     \\/   \033[1;31m|
\033[0;37m|\033[1;31m  {\033[0;38;5;252m%s\033[0m\033[1;31m}            \033[1;31m{\033[0;38;5;252m%s\033[0m\033[1;31m}             \033[1;31m{\033[0;38;5;252mv%s\033[0m\033[1;31m}  |
\033[1;31m -----------------------------------------------------------------------------------------------\033[0m\
""" % (__author__, __site__, __version__)

SEP = '#############################################'


def print_info(msg):
	"""
	Print info message.

	:param msg: the message to print
	:type msg: str
	"""
	print(f'[\033[1;34m*\033[0m] {msg}')


def print_success(msg):
	"""
	Print success message.

	:param msg: the message to print
	:type msg: str
	"""
	print(f'[\033[1;32m+\033[0m] {msg}')


def print_error(msg):
	"""
	Print error message.

	:param msg: the message to print
	:type msg: str
	"""
	print(f'[\033[1;31m-\033[0m] {msg}')


def print_cmd(msg, parallel=None):
	"""
	Print command which is being executed.

	:param msg: the message to print
	:type msg: str
	"""
	if parallel:
		print(f'[CMD] ({datetime.now().strftime("%d/%m %H:%M:%S")}) <{parallel}> {msg}')
	else:
		print(f'\033[0;36m[\033[1;35mCMD\033[0;36m] \033[0;36m(\033[0;32m{datetime.now().strftime("%d/%m %H:%M:%S")}\033[0;36m) {msg}\033[0m')


def print_separator(msg, prefix):
	"""
	Print a message wrapped into dividers.

	:param msg: the message to print
	:type msg: str
	:param prefix: the prefix string, intended to be a counter when moving to next separated item
	:type prefix: str
	"""
	print(f'\033[0;31m{SEP} \033[0;32m({prefix}) \033[1;32m{msg}\033[0;31m {SEP}\033[0m')


def start_timer():
	"""
	Start runtime counter.

	:return: current time at the start of the DivideAndScan
	:rtype: float
	"""
	timestart = time.time()
	print(f'DivideAndScan {__version__} initiated at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n')
	return timestart


def stop_timer(timestart):
	"""
	Stop runtime counter and print the elapsed time.

	:param timestart: start time of DivideAndScan
	:type timestart: float
	"""
	print(f'\nDivideAndScan done at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} with elapsed time {timedelta(seconds=time.time() - timestart)}')
