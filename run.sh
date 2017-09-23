#!/bin/bash

keywordbot(){
    python3 KeywordBot.py
}

until keywordbot; do
    echo "'keywordbot' crashed with exit code $?. Restarting..." >&2
    sleep 1
done
