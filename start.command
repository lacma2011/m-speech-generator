#!/bin/bash
#
# Voice Generator Launcher for macOS (Double-Click Version)
# This .command file can be double-clicked in macOS Finder
#

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to that directory
cd "$DIR"

# Run the main start script
exec ./start.sh "$@"
