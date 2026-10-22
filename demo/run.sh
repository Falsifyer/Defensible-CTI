#!/bin/sh
# The whole cycle, one command, fictional data.
#
#   make demo
#
# The chain itself lives in `ctisuite chain`, not in this script: a shell script is not a
# product and cannot be tested without a shell. What is left here is the short way to run
# it from the repository root.
#
# Nothing here is real: NIGHTJAR and SALTWIND do not exist.

set -eu

aqui=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
exec ctisuite chain --dir "$aqui"
