# Crazyflie RL with phoenix-drone-simulation

## Context

This repository allows flying a Crazyflie 2.1 with **phoenix-drone-simulation** and the **Crazyflie API**.

1. First, you need to install phoenix-drone-simulation and run training tests with the simulation environment. **This is the simulation and AI part**.

2. Then, install the Crazyflie API and the cfclient, and perform connection and flight tests with the Crazyflie (CrazyRadio, Lighthouse system, etc.). **This is the robotics and Crazyflie/Hardware setup part**.

3. Finally, connect the Crazyflie API with phoenix-drone-simulation and run model loading and flight tests with the Crazyflie. **This is the Sim2Real part**.

## Setup (On Windows OS)

We first decided to use Windows OS because of the compatibility with the Crazyflie API (USB driver for the USB radio dongle).

*Advice: use a conda virtual environment to install all the python packages in the same place.*

### 1. Setup phoenix-drone-simulation (AI)

*The git repository of phoenix-drone-simulation is already cloned in this repo in order to have the working commit before Cyril's way.*

*Here is the commit before Cyril's way: https://github.com/SvenGronauer/phoenix-drone-simulation/tree/282bcc6a7f7d483e638a07336350809b42eee719 that works with the requirements_crazyapiphoenix.txt file.*

#### Setup Conda Virtual Environment

- Install miniconda3 windows
- Go to bash terminal Windows
- conda create --name phoenix_drone python=3.8
- conda activate phoenix_drone
- conda config --env --add channels conda-forge
- conda install --yes --file requirements_crazyapiphoenix.txt
- conda install --yes pytorch torchvision cpuonly -c pytorch
- cd phoenix-drone-simulation
- pip install -e .

### 2. Setup Crazyflie API (Robotics)

*Note: The git repository of crazyflie-lib-python and crazyflie-fireware are already cloned in this repo to avoid any compatibility issues.*

First install the **Crazyflie lib python**, still in the conda virtual environment.

https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/installation/install/

Install the **Crazyflie client**.

https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/installation/install/

Don't forget to install the **Crazyradio USB driver**.

https://www.bitcraze.io/documentation/repository/crazyradio-firmware/master/building/usbwindows/

When everything is installed, you can *test the connection* with the Crazyflie through the Crazyradio USB dongle and the cfclient.

https://www.bitcraze.io/documentation/repository/crazyflie-clients-python/master/userguides/userguide_client/

```bash
# just run in terminal
cfclient
```

Finally, you can *test the connection* with the Crazyflie with the Crazyradio USB dongle and the API cflib.

https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/user-guides/sbs_connect_log_param/

**Troubleshooting:**

If there's a problem with the USB radio connection, it might be a firmware issue! You need to connect the Crazyflie via USB cable, open the cfclient, and try to reboot or update the firmware.

#### Configure LightHouse Deck

The last step is to configure the Crazyflie to connect to the Lighthouse system for localization.

Configuration video of Crazyflie: [Youtube video - LightHouse Deck](https://www.youtube.com/watch?v=DCEHht72B08)

Once calibration is done, the Lighthouse Deck's information is stored in the Crazyflie. The cfclient can then be closed. It is then possible to execute Python code to fly the Crazyflie such as `/scripts_fly/autonomous/autonomousSequence.py`.

**Other:**

- Reboot le Crazyflie via du code et la radio USB
  - Git clone crazyflie-firmware repo
  - cd crazyflie-firmware/tools/utils/reboot.py
  - Execute some code like this:

    ```python
      """
      Reboot a Crazyflie remotely using a Crazyradio
      """
      import sys
      from cflib.utils.power_switch import PowerSwitch

      # if len(sys.argv) != 2:
      #     print("Error: uri is missing")
      #     print('Usage: {} uri'.format(sys.argv[0]))
      #     sys.exit(-1)

      uri = "radio://0/80/2M/E7E7E7E7E7"
      PowerSwitch(uri).stm_power_cycle()
    ```

## Project Tree

```text
.
├── README.md
├── crazyflie-firmware
├── crazyflie-lib-python
├── phoenix-drone-simulation
└── scripts_fly
    └── autonomous (Scripts to fly the Crazyflie)
        └── autonomousSequence.py
    └── motors (Scripts to test the motors)
        └── ramp.py
    └── connect_log_param.py (test the connection with the Crazyflie)
├── launch.json
├── Reinforcement Learning-Based Control of CrazyFlie 2.X Quadrotor.pdf (Paper)
└── requirements_crazyapiphoenix.txt
```

## Launch

### 1. Run phoenix-drone-simulation (AI)

Python scripts for training and tests are in the `phoenix-drone-simulation/examples/` folder:

- The script `train_with_multi_cores.py` allows training an RL model with the gym environment using multiple cores.
- The script `train_and_charge.py` allows loading a pre-trained model and testing it.
- The `phoenix-drone-simulation/results/` folder contains an example of training results.

### 2. Run Crazyflie API (Robotics)

Python scripts for testing the connection and flight of the Crazyflie are in the`scripts_fly/` folder:

- The script `connect_log_param.py` allows testing the connection with the Crazyflie and retrieving logs and parameters.
- The script `autonomous/autonomousSequence.py` allows flying the Crazyflie with the Lighthouse Deck by defining a flight sequence.

```python
# Change the sequence according to your setup
#             x    y    z  YAW
sequence = [
    (0.0, 0.0, 0.5, 0),
    (0.0, 0.0, 1.0, 0),
    (0.5, -0.5, 1.0, 0),
    (0.5, 0.0, 1.0, 0),
    (0.0, 0.0, 1.0, 0),
    (0.0, 0.0, 0.5, 0),
    (0.0, 0.0, 0.0, 0),
]
```

### 3. Connect Crazyflie API with phoenix-drone-simulation (Sim2Real)

You need to write Python code that connects the Crazyflie API with phoenix-drone-simulation. This code should load a pre-trained model and test it with the Crazyflie. The script is found at `phoenix-drone-simulation/examples/sim2real_hover.py`.

The `sim2real_hover.py` script is almost functional. It's necessary to understand how to send the real drone's observations into the actor-critic and address the following issues:

- Understanding what the 21 other values in obs returned by the gym environment are. In order to fill in the 13 values retrieved from the real drone and send all this to the actor-critic
- What does `action, _, _ = ac.step(obs_tensor)` mean and return?

## TODO

Fix the `sim2real_hover.py` script to connect the Crazyflie API with phoenix-drone-simulation.
