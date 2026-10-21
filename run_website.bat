@echo off
title Launch Be Smart With AI Agency Website
color 0B
echo ===========================================================================
echo       BE SMART WITH AI - OFFICIAL AGENCY & FOUNDER BRAND PORTAL
echo ===========================================================================
echo.
echo Starting local web server on port 3000...
echo Opening http://localhost:3000 in your browser...
echo.

start "" "http://localhost:3000"
python -m http.server 3000
