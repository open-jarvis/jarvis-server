#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#

import sys, os


# functions
def print_usage():
	print("Usage: jarvisd <command> <argument>")
	print("")
	print(" command           | argument")
	print("-------------------+-------------------------------------------")
	print(" add-app           | https://github.com/open-jarvis/<app>")
	print(" add-local-app     | /home/user/Downloads/<app>")
	print(" list-apps         | ")
	exit(0)
def do_action(print_str, shell_command, show_output=True, on_fail="failed!", on_success="done!", exit_on_fail=True):
	print(print_str + "... ", end="")
	if not show_output:
		shell_command += " &> /dev/null"
	if not os.system(shell_command) == 0:
		print(on_fail)
		if exit_on_fail:
			exit(1)
	else:
		print(on_success)


# check usage
if len(sys.argv) == 1 or "--help" in sys.argv or "-h" in sys.argv:
	print_usage()


# program
command = sys.argv[1]
argument = sys.argv[2] if len(sys.argv) > 2 else None

if command == "add-app":
	if argument is None:
		print_usage()
	do_action("clone git repository ({})".format(argument.split("/")[-1]), "git clone {} /jarvisd/apps/{}".format(argument, argument.split("/")[-1]))
if command == "add-local-app":
	if argument is None:
		print_usage()
	basename = os.path.basename(argument)
	do_action("copy local app ({})".format(basename), "cp -v {} {}".format(argument, basename))

print("--- done ---")