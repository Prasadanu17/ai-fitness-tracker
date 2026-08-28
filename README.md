# AI Fitness Tracker

> Train smarter. Move better. Let AI track your workout.

## Overview

**AI Fitness Tracker** is a computer-vision-powered workout analysis system designed to understand human movement through a webcam. It uses pose estimation, joint-angle analysis, exercise-specific movement logic, and repetition tracking to detect and analyze exercises in real time.

The architecture is designed to support multiple exercises rather than being limited to a single movement, with a modular AI Fitness Engine that can be extended with new exercise analyzers.

## What We're Building

The goal is to build an AI-powered fitness system capable of:

- Real-time human pose detection
- Exercise recognition
- Repetition counting
- Joint-angle analysis
- Movement tracking
- Exercise-specific analysis
- Form feedback
- Real-time workout monitoring

## Current Exercises

- 🦵 Squats
- 💪 Bicep Curls
- 🔜 Push-ups
- 🔜 Lunges
- 🔜 Shoulder Press
- 🔜 More exercises

## AI Fitness Engine

The core architecture is:

Webcam  
↓  
MediaPipe Pose Detection  
↓  
33 Body Landmarks  
↓  
Joint Angle Calculation  
↓  
Exercise Analyzer  
↓  
Rep Counter  
↓  
Real-Time Fitness Feedback

## Current Technology

- Python
- OpenCV
- MediaPipe
- NumPy
- Computer Vision
- Pose Estimation

## Project Structure

```text
ai-fitness-tracker/
│
├── ai_engine/
│   ├── pose_engine.py
│   ├── angle_calculator.py
│   ├── rep_counter.py
│   ├── exercise_analyzer.py
│   │
│   └── exercises/
│       ├── bicep_curl.py
│       ├── squat.py
│       └── ...
│
├── models/
│   └── pose_landmarker.task
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── gym_tracker.ipynb