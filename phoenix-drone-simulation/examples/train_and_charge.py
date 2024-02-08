#%%
"""
Run a charged model in order to do new simulations without re training the model

Date of creation : 6 Dec 2023
Author : May Ouir
"""

import argparse
import numpy as np
import psutil
import sys
import gym
import getpass
import time
import torch
import os

# local imports:
import phoenix_drone_simulation  # necessary to load our custom drone environments
from phoenix_drone_simulation.utils import utils
from phoenix_drone_simulation.algs.model import Model
from phoenix_drone_simulation.utils.mpi_tools import mpi_fork


def load(path):
    ac, env = utils.load_actor_critic_and_env_from_disk(path)
    env.render()

    while True:
        obs = env.reset()
        done = False
        while not done:
            obs = torch.as_tensor(obs, dtype=torch.float32)
            print(len(obs))
            """
            CEST QUOI ???
            obs1 => len 34
            tensor([ 0.1517, -0.1014,  0.7906, 
                    -0.0621, -0.2208,  0.9557,  0.1843, 
                    -0.0740, -0.0744,  0.0141, 
                    -1.1069,  0.5897, -0.0228,  
                    => len(13)
                    
                    0.1260,  0.1128,  0.1044, 0.1088,  0.1506, -0.1037,  0.7914, -0.0616, -0.2203,  0.9562,  0.1828,
                    -0.0420, -0.0778, -0.0045, -1.5940,  0.8912,  0.0711,  0.1260,  0.1128,
                    0.1044,  0.1088])
                    => len(21)
            
            problemes : 
            - self.drone.last_action keske c
            - recuperer velocité, omega du drone (loggers, ou autre)
            - tester un code ou on envoie positions et quaternions au drone et voir s’il fonctionne bien
            
            [xyz, quat, vel, omega, self.drone.last_action]
            => x,y,z,qx,qy,qz,qw,vx,vy,vz,wx,wy,wz,ax,ay,az
            """
            
            action, value, *_ = ac(obs)
            """ 
            ASKIP PLUS DE PRECISION AVEC LES VITESSES D'ANGLES ET PAS LES QUATERNNIONS
            action1
            [-0.25160342 -1.2137517   1.8812376   1.2599485 ]
            
            
            value1
            -0.5725346
            """

            obs, reward, done, info = env.step(action)
            """
            obs1
            [ 0.15058725 -0.10372084  0.79136231 -0.06164107 -0.22028772  0.95617587
            0.18276052 -0.04198639 -0.07780789 -0.00451437 -1.59400648  0.891225
            0.07107269 -0.25160342 -1.21375167  1.88123763  1.25994849  0.15253136
            -0.09931793  0.78611686 -0.06933538 -0.22983558  0.95301647  0.18473717
            -0.09393453 -0.08087872 -0.03733906 -2.0877499   1.20156427  0.04073993
            -0.25160342 -1.21375167  1.88123763  1.25994849]
            obs2
            [ 0.15253136 -0.09931793  0.78611686 -0.06933538 -0.22983558  0.95301647
            0.18473717 -0.09393453 -0.08087872 -0.03733906 -2.0877499   1.20156427
            0.04073993  1.15681481  0.36707526  1.61116135  1.01162064  0.15708264
            -0.10033072  0.78720816 -0.07411877 -0.23816287  0.95102757  0.18256892
            -0.09173888 -0.14206726 -0.05664869 -1.85811858  0.86778706  0.13724549
            -0.25160342 -1.21375167  1.88123763  1.25994849]
            reward1
            -0.2785667154935864
            reward2
            -0.27893273378302286
            done1
            False
            done2
            False
            info1
            {'xyz_limit': array([ 0.15183851, -0.10186234,  0.790356  ]), 'rpy': array([-0.48358286,  0.04665813,  2.74922141]), 'xzy_dot': array([-2.1886025 ,  1.10309111,  0.06070756]), 'cost': 1.0}
            info2
            {'xyz_limit': array([ 0.15090252, -0.10311101,  0.78979777]), 'rpy': array([-0.50295863,  0.05462907,  2.74586927]), 'xzy_dot': array([-1.835605  ,  0.77734189,  0.08867307]), 'cost': 1.0}
            """
            
            time.sleep(1/60)
            if done:
                obs = env.reset()
            
if __name__ == "__main__":
    path = "results"
    load(path)