#!/usr/bin/env fish
echo "Hello"
echo $argv[1] | jq '.provider_handoff.circuitId'
sleep  10