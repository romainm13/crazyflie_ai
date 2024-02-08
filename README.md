# Crazyflie RL with phoenix-drone-simulation

## Context

Ce repo permet de faire voler un Crazyflie 2.1 avec **phoenix-drone-simulation** et l'**API Crazyflie**.

1. Tout d'abord, il faut installer phoenix-drone-simulation et faire des tests d'entrainement avec l'environnement de simulation. **C'est la partie simulation et IA**.

2. Ensuite, il faut installer l'API Crazyflie et le client cfclient, et faire des tests de connexion et de vol avec le Crazyflie (CrazyRadio, LIghthouse system, etc.). **C'est la partie robotique et setup du Crazyflie/Hardware**.

3. Enfin, il faut connecter l'API Crazyflie avec phoenix-drone-simulation et faire des tests de chargement de modèle et de vol avec le Crazyflie. **C'est la partie Sim2Real**.

***Conseil: utiliser un environnement virtuel conda pour installer tous les packages python au même endroit.***

## Setup (On Windows OS)

We first decided to use Windows OS because of the compatibility with the Crazyflie API (USB driver for the USB radio dongle).

### 1. Setup phoenix-drone-simulation (AI)

*The git repository of phoenix-drone-simulation is already cloned in this repo in order to have the working commit before Cyril's way.*

#### Cyril's way - Gymnasium (NOT WORKING)

- Install miniconda3 windows
- Go to bash terminal Windows
- conda create --name phoenix_drone python=3.8
- conda activate phoenix_drone
- conda config --env --add channels conda-forge
- conda install --yes --file requirements_crazyapiphoenix2.txt
- conda install --yes pytorch torchvision cpuonly -c pytorch
- pip install gymnasium>=0.29.1
- pip install cfclient
- cd phoenix-drone-simulation
- pip install -e .

#### Before Cyril's way (WORKING)

Here is the commit before Cyril's way: https://github.com/SvenGronauer/phoenix-drone-simulation/tree/282bcc6a7f7d483e638a07336350809b42eee719

- Install miniconda3 windows
- Go to bash terminal Windows
- conda create --name phoenix_drone python=3.8
- conda activate phoenix_drone
- conda config --env --add channels conda-forge
- conda install --yes --file requirements_crazyapiphoenix1.txt
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

Si problème de connexion par USB radio c'est peut-être un pb de firmware ! Il faut connecter le crazyflie par cable USB, ouvrir le cfclient, et essayer de reboot ou de mettre à jour le firmware

#### Configure LightHouse Deck

Dernière étape, il faut configurer le Crazyflie pour qu'il puisse se connecter au système Lighthouse pour la localisation.

Vidéo de configuration du Crazyflie: [Youtube video - LightHouse Deck](https://www.youtube.com/watch?v=DCEHht72B08)

Une fois que le calibrage est fait, les infos du LightHouse Deck sont stockées dans le Crazyflie. Le cfclient peut donc être fermé. Il est ensuite possible d'exécuter du code python pour faire voler le Crazyflie tel que `/scripts_fly/autonomous/autonomousSequence.py`.

**Autre:**

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

## Arbre du projet

```bash
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
├── requirements_crazyapiphoenix1.txt (Before Cyril's way, working)
└── requirements_crazyapiphoenix2.txt (Cyril's way, not working)
```

## Launch

### 1. Run phoenix-drone-simulation (AI)

Les scripts python pour l'entrainement et les tests sont dans le dossier `phoenix-drone-simulation/examples/`:

- Le script `train_with_multi_cores.py` permet d'entrainer un modèle de RL avec l'environnement gym avec plusieurs coeurs.
- Le script `train_and_charge.py` permet de charger un modèle pré-entrainé et de le tester.
- Le dossier `phoenix-drone-simulation/results/` contient un exemple de résultat d'entrainement.

### 2. Run Crazyflie API (Robotics)

Les scripts python pour tester la connexion et le vol du Crazyflie sont dans le dossier `scripts_fly/`:

- Le script `connect_log_param.py` permet de tester la connexion avec le Crazyflie et de récupérer les logs et les paramètres.
- Le script `autonomous/autonomousSequence.py` permet de faire voler le Crazyflie avec le LightHouse Deck en définissant une séquence de vol.

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

On doit écrire un code python qui permet de connecter l'API Crazyflie avec phoenix-drone-simulation. Celui-ci doit charger un modèle pré-entrainé et le tester avec le Crazyflie. Le script se trouve à `phoenix-drone-simulation/examples/sim2real_hover.py`.

Le script `sim2real_hover.py` est presque fonctionnel. Il faut juste comprendre comment envoyer les observations du drone réel dans l'actor critic et réponses aux problématiques suivantes:

- Comprendre c’est quoi les 21 autres valeurs dans `obs` renvoyés par l’environnement gym. Afin de remplir les 13 valeurs recupérés du drone réels et envoyer tout ça dans l’actor crtitic
- Qu'est ce que `action, _, _ = ac.step(obs_tensor)` ?

## TODO

Fix the `sim2real_hover.py` script to connect the Crazyflie API with phoenix-drone-simulation.