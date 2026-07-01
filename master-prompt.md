You are a Senior Software Architect, Senior Python Developer, Desktop Application Engineer, UI/UX Designer, Performance Engineer and QA Engineer.

Your mission is to build an Enterprise-grade Windows Desktop Application (.exe) that can collect Facebook Live comments in real-time from Google Chrome, export CSV files, and provide a beautiful Lucky Wheel for prize drawing.

This application must look and feel like a premium commercial software product, not an open-source hobby project.

======================================================
PROJECT NAME
======================================================

Facebook Live Collector Pro

Enterprise Edition

======================================================
PRIMARY GOAL
======================================================

The application monitors a Facebook Live page that is already opened by the user in Google Chrome.

It collects every new comment in real-time without missing comments as much as technically possible, stores the data efficiently, exports CSV files, and includes a professional Lucky Wheel module.

No login screen.

No complicated setup.

One-click operation.

======================================================
TECH STACK
======================================================

Language

Python 3.12+

Desktop GUI

CustomTkinter

ModernTk

ttkbootstrap

CTkMessagebox

Backend

Python

Automation

Playwright

NOT Selenium.

Data

Pandas

CSV

OpenPyXL

SQLite (temporary cache)

Images

Pillow

Animation

Tkinter Animation

Canvas Animation

Packaging

PyInstaller

Single EXE

Windows 10/11

======================================================
PROJECT STRUCTURE
======================================================

/app

/ui

/components

/services

/facebook

/export

/wheel

/storage

/utils

/assets

/icons

/fonts

/config

/temp

/logs

/main.py

======================================================
APPLICATION DESIGN
======================================================

Create a premium UI.

Glassmorphism

Rounded Corner

Gradient

Blur

Glow Effect

Soft Shadow

Animated Cards

Professional Dashboard

Dark Mode

Modern Typography

Smooth Animation

No old Tkinter appearance.

Make users say

"WOW"

======================================================
MAIN WINDOW
======================================================

Top Navigation

Logo

Application Name

Connection Status

Theme Switch

Settings

------------------------------------------------------

Dashboard Cards

Chrome Status

Facebook Status

Running Time

Total Comments

Unique Users

Employee IDs

Memory Usage

------------------------------------------------------

Center Panel

Live Comment Feed

Auto Scroll

Newest comment highlighted

Animated appearance

------------------------------------------------------

Bottom Toolbar

Start

Pause

Stop

Export Raw CSV

Export Users CSV

Export Employee CSV

Lucky Wheel

Clear Session

======================================================
WORKFLOW
======================================================

STEP 1

User opens Facebook Live in Google Chrome.

STEP 2

Open this application.

STEP 3

Press

CONNECT

STEP 4

Application automatically finds Chrome.

STEP 5

Attach Playwright.

STEP 6

Detect Facebook Live page.

STEP 7

Start monitoring comments.

======================================================
REALTIME COMMENT ENGINE
======================================================

Use Playwright.

Monitor DOM continuously.

Never refresh page.

Never interfere with video playback.

Polling interval

300ms

Detect only NEW comments.

Ignore comments already processed.

Each comment contains

Timestamp

Username

Comment Text

Comment ID (if available)

Profile URL (if available)

======================================================
COMMENT PROCESSING
======================================================

Every comment received should be processed.

Example

John

123456

↓

Save Raw

↓

Extract Employee ID

↓

Update Dashboard

↓

Write CSV

↓

Update Live Feed

======================================================
RAW DATA MODEL
======================================================

Timestamp

Username

Comment

EmployeeID

DetectedTime

Hash

======================================================
EMPLOYEE ID DETECTION
======================================================

Extract employee ID automatically.

Default regex

Only digits

Length

4-10 digits

Example

1234

123456

0009988

Should be configurable in Settings.

======================================================
DUPLICATE DETECTION
======================================================

User duplicate

Keep only first occurrence.

Employee duplicate

Keep only first occurrence.

Raw comments

Store every comment.

======================================================
CSV EXPORT
======================================================

Generate

1.

RawComments.csv

Columns

Timestamp

Username

Comment

EmployeeID

2.

UniqueUsers.csv

Username

First Comment Time

Comment Count

3.

EmployeeIDs.csv

EmployeeID

First User

Time

Duplicate Count

UTF-8

Excel Compatible

======================================================
AUTO SAVE
======================================================

Every 5 seconds

Auto write CSV

Prevent data loss

======================================================
SEARCH
======================================================

Search User

Search Employee ID

Search Comment

Realtime filtering

======================================================
LIVE FEED
======================================================

Newest comment appears on top.

Animated slide.

Color highlight.

Show

Avatar placeholder

Username

Comment

Time

======================================================
STATISTICS
======================================================

Realtime

Total Comments

Comments/sec

Unique Users

Employee IDs

Duplicate Users

Duplicate IDs

Running Time

======================================================
LOG SYSTEM
======================================================

Application Log

Connection

Errors

CSV Saved

Export Finished

Reconnect

======================================================
ERROR HANDLING
======================================================

If Chrome closes

Reconnect automatically.

If Facebook reloads

Reconnect.

If Playwright crashes

Restart automatically.

Never freeze UI.

======================================================
THREADING
======================================================

Separate

UI Thread

Collector Thread

Writer Thread

Export Thread

Wheel Thread

Queue-based architecture.

======================================================
STORAGE
======================================================

Temporary

SQLite

Memory Cache

CSV

Auto Backup

======================================================
SETTINGS
======================================================

Employee ID Regex

CSV Folder

Auto Save Interval

Theme

Language

Animation Speed

======================================================
LUCKY WHEEL MODULE
======================================================

Beautiful full screen wheel.

Modern animation.

Physics rotation.

Glow effects.

Particle effects.

Confetti.

Fireworks.

Winning sound.

======================================================
IMPORT
======================================================

Load

UniqueUsers.csv

or

EmployeeIDs.csv

======================================================
SPIN
======================================================

User presses

SPIN

Wheel rotates.

Random easing animation.

Winner highlighted.

Celebrate.

======================================================
WINNER PANEL
======================================================

Winner Name

Employee ID

Time

Prize

======================================================
REMOVE WINNER
======================================================

Checkbox

Remove winner after draw.

Prevent duplicate winners.

======================================================
WINNER HISTORY
======================================================

Table

Winner

Prize

Time

======================================================
EXPORT WINNER HISTORY
======================================================

WinnerHistory.csv

======================================================
CLEAR SESSION
======================================================

When user presses

CLEAR

Delete

Memory Cache

SQLite

Temporary CSV

Reset Dashboard

Reset Live Feed

======================================================
EXIT
======================================================

When application closes

Stop Playwright

Close Browser Connection

Flush CSV

Close SQLite

Delete temp files

Exit gracefully

======================================================
PERFORMANCE
======================================================

Must support

100,000+

comments

without freezing.

Memory optimized.

Queue architecture.

Lazy rendering.

======================================================
UI REQUIREMENTS
======================================================

Everything animated.

Smooth transitions.

Loading animation.

Modern icons.

Professional typography.

Beautiful buttons.

Hover effects.

Glass cards.

Premium feeling.

Like Microsoft Office + Adobe + Notion.

======================================================
CODE QUALITY
======================================================

Use OOP.

Type Hints.

Dataclasses.

Repository Pattern.

Service Layer.

MVC Architecture.

No duplicated code.

No global variables.

PEP8 compliant.

Document every class.

======================================================
OUTPUT
======================================================

Generate a COMPLETE production-ready project.

Include

Full source code

Folder structure

Assets

Icons

Configuration

README

Requirements.txt

PyInstaller build script

Installer script

Sample CSV

Unit Tests

Error handling

Logging

Production optimization

Everything must be runnable.

Do not generate pseudo code.

Generate real production code.

The final result must be a commercial-quality Windows application that feels like premium enterprise software.