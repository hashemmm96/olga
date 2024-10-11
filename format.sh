#!/usr/bin/env bash

black .
isort --gitignore --profile black .
