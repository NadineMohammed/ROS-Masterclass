#  Session 01 — Robot Distance Sensor Program

## What does this program do?

This program simulates a robot's front distance sensor.  
It reads a **list of distance measurements** (in meters) and decides what the robot should do for each one:

| Distance | Action | Reason |
|----------|--------|--------|
| Less than 0.5m | **STOP** | Obstacle too close |
| 0.5m to 1.0m | **SLOW** | Obstacle nearby |
| More than 1.0m | **MOVE** | Path is clear |

**Example:**  
Input: `[0.3, 1.5, 0.8, 2.0, 0.4]`  
Output: `STOP, MOVE, SLOW, MOVE, STOP`

---

## How does the Robot class work?

The `Robot` class represents a robot with:
- A **name** — to identify the robot
- A **battery level** — to show how much power it has

When created, the robot prints a startup message.  
You then call its method with a list of distances and it processes each one.

---

## What does each method do?

### `__init__(self, name, battery)`
Sets up the robot with a name and battery level when you first create it.

### `decide_action(self, distance)`
Takes a **single distance** value and returns the correct action (`STOP`, `SLOW`, or `MOVE`).  
Also handles errors if the value is negative or not a number.

### `process_sensor_readings(self, distances)`
Takes a **list of distances**, loops through them, calls `decide_action()` for each one, prints the results, and returns the list of actions.

---

## How do I run the code?

Make sure you have Python 3 installed, then run:

```bash
python3 robot.py
```

You will see the robot process 6 different test cases automatically.

---

## What did I learn from using AI?

- How to structure a Python class properly with `__init__` and methods
- How to use a `for` loop to process a list of values
- How to add error handling using `try` / `except` and `raise ValueError`
- How to write clear comments that explain the code
- How AI can help you write a first version quickly, and then you can improve it yourself
