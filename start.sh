#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT run:app --timeout 120