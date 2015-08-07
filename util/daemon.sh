#!/bin/bash

cd /users/matsmelander/Library/LaunchAgents
launchctl unload com.viltstigen.traffic.plist
launchctl list | grep viltstigen
cp /users/matsmelander/Documents/Dev/Traffic/TrafficModel.py /users/matsmelander/Library/Traffic
echo launching...
launchctl load com.viltstigen.traffic.plist
launchctl list | grep viltstigen