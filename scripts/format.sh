#!/usr/bin/env bash

black .
fdfind .py -X isort --profile black
