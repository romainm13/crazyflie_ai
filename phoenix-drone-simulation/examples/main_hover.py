#%%
"""
TODO
"""

############
# IMPORTS
############

# phoenix-drone-simulation IMPORTS
import time
import pprint

import torch
import phoenix_drone_simulation  # necessary to load our custom drone environments
from phoenix_drone_simulation.utils import utils
from phoenix_drone_simulation.algs.model import Model
from phoenix_drone_simulation.utils.mpi_tools import mpi_fork

# Crazyflie IMPORTS
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.crazyflie.syncLogger import SyncLogger
from cflib.utils import uri_helper

############
# GLOBALS
############
time_start_ref = 0

dict_drone_state = {
    "x": 0.0,
    "y": 0.0,
    "z": 0.0,
    "vx": 0.0,
    "vy": 0.0,
    "vz": 0.0,
    "qx": 0.0,
    "qy": 0.0,
    "qz": 0.0,
    "qw": 0.0,
    "wx": 0.0,
    "wy": 0.0,
    "wz": 0.0,
}



########################################################################################################################
########################################################################################################################

# URI to the Crazyflie to connect to
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# Change the sequence according to your setup
#  x    y    z  YAW
sequence = [
    (0.0, 0.0, 0.5, 0),
    (0.0, 0.0, 0.0, 0),
]

def wait_for_position_estimator(scf):
    """
    Cette fonction attend que l'estimateur de position du drone (probablement un filtre de Kalman) 
    stabilise sa prédiction de la position actuelle du drone. 
    
    Elle utilise une "SyncLogger" pour enregistrer les valeurs de variance de l'estimateur de Kalman 
    (kalman.varPX, kalman.varPY, kalman.varPZ) et vérifie si ces valeurs sont stabilisées en dessous d'un certain seuil.
    """
    print('Waiting for estimator to find position...')

    log_config = LogConfig(name='Kalman Variance', period_in_ms=500)
    log_config.add_variable('kalman.varPX', 'float')
    log_config.add_variable('kalman.varPY', 'float')
    log_config.add_variable('kalman.varPZ', 'float')

    # On initialise les historiques des valeurs de variance à 1000
    var_y_history = [1000] * 10
    var_x_history = [1000] * 10
    var_z_history = [1000] * 10

    threshold = 0.001

    with SyncLogger(scf, log_config) as logger:
        for log_entry in logger:
            data = log_entry[1]

            var_x_history.append(data['kalman.varPX'])
            var_x_history.pop(0)
            var_y_history.append(data['kalman.varPY'])
            var_y_history.pop(0)
            var_z_history.append(data['kalman.varPZ'])
            var_z_history.pop(0)

            min_x = min(var_x_history)
            max_x = max(var_x_history)
            min_y = min(var_y_history)
            max_y = max(var_y_history)
            min_z = min(var_z_history)
            max_z = max(var_z_history)

            # print("{} {} {}".
            #       format(max_x - min_x, max_y - min_y, max_z - min_z))

            if (max_x - min_x) < threshold and (
                    max_y - min_y) < threshold and (
                    max_z - min_z) < threshold:
                break


def reset_estimator(scf):
    cf = scf.cf
    cf.param.set_value('kalman.resetEstimation', '1')
    time.sleep(0.1)
    cf.param.set_value('kalman.resetEstimation', '0')

    wait_for_position_estimator(cf)


# x, y, z, vx, vy, vz, qx,qy,qz,qw, ax, ay, az, roll, pitch, yaw
def position_callback(timestamp, data, logconf):
    """
    Get the position of the drone in m ???
    """
    x = data['kalman.stateX']
    y = data['kalman.stateY']
    z = data['kalman.stateZ']
    dict_drone_state["x"] = x
    dict_drone_state["y"] = y
    dict_drone_state["z"] = z        
    # print('Position: ({:.3f}, {:.3f}, {:.3f})'.format(x, y, z))

def velocity_callback(timestamp, data, logconf):
    """
    Get the velocity of the drone in m/s ???
    """
    vx = data['kalman.statePX']
    vy = data['kalman.statePY']
    vz = data['kalman.statePZ']
    dict_drone_state["vx"] = vx
    dict_drone_state["vy"] = vy
    dict_drone_state["vz"] = vz
    # print('Velocity: ({:.3f}, {:.3f}, {:.3f})'.format(vx, vy, vz))
    
def quaternion_callback(timestamp, data, logconf):
    """
    Get the orientation of the drone in quaternion
    """
    qx = data['kalman.q0']
    qy = data['kalman.q1']
    qz = data['kalman.q2']
    qw = data['kalman.q3']
    dict_drone_state["qx"] = qx
    dict_drone_state["qy"] = qy
    dict_drone_state["qz"] = qz
    dict_drone_state["qw"] = qw
    # print('Orientation: (qx={:.3f}, qy={:.3f}, qz={:.3f}, qw={:.3f})'.format(qx, qy, qz, qw))

def gyro_callback(timestamp, data, logconf):
    """
    Get the angular velocity of the drone in degrees/s
    """
    wx = data['gyro.x']
    wy = data['gyro.y']
    wz = data['gyro.z']
    dict_drone_state["wx"] = wx
    dict_drone_state["wy"] = wy
    dict_drone_state["wz"] = wz
    # print('Gyro: ({:.3f}, {:.3f}, {:.3f})'.format(wx, wy, wz))
    print("Time: {}".format(time.time() - time_start_ref))
    pprint.pprint(dict_drone_state)

# def acceleration_callback(timestamp, data, logconf):
#     ax = data['acc.x']
#     ay = data['acc.y']
#     az = data['acc.z']
#     print('Acceleration: ({:.3f}, {:.3f}, {:.3f})'.format(ax, ay, az))

# def angles_callback(timestamp, data, logconf):
#     roll = data['stabilizer.roll']
#     pitch = data['stabilizer.pitch']
#     yaw = data['stabilizer.yaw']
#     print('Angles: (Roll={:.3f}, Pitch={:.3f}, Yaw={:.3f})'.format(roll, pitch, yaw))

def start_position_printing(scf):
    global time_start_ref
    time_start_ref = time.time()
    
    log_conf_pos = LogConfig(name='Position', period_in_ms=500)
    log_conf_pos.add_variable('kalman.stateX', 'float')
    log_conf_pos.add_variable('kalman.stateY', 'float')
    log_conf_pos.add_variable('kalman.stateZ', 'float')
    scf.cf.log.add_config(log_conf_pos)
    log_conf_pos.data_received_cb.add_callback(position_callback)
    log_conf_pos.start()

    log_conf_vel = LogConfig(name='Velocity', period_in_ms=500)
    log_conf_vel.add_variable('kalman.statePX', 'float')   # Velocity in X-axis
    log_conf_vel.add_variable('kalman.statePY', 'float')   # Velocity in Y-axis
    log_conf_vel.add_variable('kalman.statePZ', 'float')   # Velocity in Z-axis
    scf.cf.log.add_config(log_conf_vel)
    log_conf_vel.data_received_cb.add_callback(velocity_callback)
    log_conf_vel.start()
    
    log_conf_quat = LogConfig(name='Quaternion', period_in_ms=500)
    log_conf_quat.add_variable('kalman.q0', 'float')   # Quaternion component 0
    log_conf_quat.add_variable('kalman.q1', 'float')   # Quaternion component 1
    log_conf_quat.add_variable('kalman.q2', 'float')   # Quaternion component 2
    log_conf_quat.add_variable('kalman.q3', 'float')   # Quaternion component 3
    scf.cf.log.add_config(log_conf_quat)
    log_conf_quat.data_received_cb.add_callback(quaternion_callback)
    log_conf_quat.start()
    
    log_conf_gyro = LogConfig(name='Gyro', period_in_ms=500)
    log_conf_gyro.add_variable('gyro.x', 'float')        # Angular velocity in X-axis
    log_conf_gyro.add_variable('gyro.y', 'float')        # Angular velocity in Y-axis
    log_conf_gyro.add_variable('gyro.z', 'float')        # Angular velocity in Z-axis
    scf.cf.log.add_config(log_conf_gyro)
    log_conf_gyro.data_received_cb.add_callback(gyro_callback)
    log_conf_gyro.start()
    
    # log_conf_acc = LogConfig(name='Acceleration', period_in_ms=500)
    # log_conf_acc.add_variable('acc.x', 'float')        # Acceleration in X-axis
    # log_conf_acc.add_variable('acc.y', 'float')        # Acceleration in Y-axis
    # log_conf_acc.add_variable('acc.z', 'float')        # Acceleration in Z-axis
    # scf.cf.log.add_config(log_conf_acc)
    # log_conf_acc.data_received_cb.add_callback(acceleration_callback)
    # log_conf_acc.start()
    
    # log_conf_angles = LogConfig(name='Angles', period_in_ms=500)
    # log_conf_angles.add_variable('stabilizer.roll', 'float')
    # log_conf_angles.add_variable('stabilizer.pitch', 'float')
    # log_conf_angles.add_variable('stabilizer.yaw', 'float')
    # scf.cf.log.add_config(log_conf_angles)
    # log_conf_angles.data_received_cb.add_callback(angles_callback)
    # log_conf_angles.start()
    
    
def run_sequence(scf, sequence):
    cf = scf.cf

    for position in sequence:
        print('Setting position {}'.format(position))
        for i in range(50):
            cf.commander.send_position_setpoint(position[0],
                                                position[1],
                                                position[2],
                                                position[3])
            time.sleep(0.1)

    cf.commander.send_stop_setpoint()
    # Hand control over to the high level commander to avoid timeout and locking of the Crazyflie
    cf.commander.send_notify_setpoint_stop()

    # Make sure that the last packet leaves before the link is closed
    # since the message queue is not flushed before closing
    time.sleep(0.1)

def run_sequence_ai(scf, sequence):
    """
    Cette fonction exécute la séquence de commande sur le drone Crazyflie 
    grâce au modèle de contrôle que vous avez entraîné.
    """
    cf = scf.cf # initialisation de l'objet de contrôle du Crazyflie de l'API Crazyflie
    ac, env = utils.load_actor_critic_and_env_from_disk("results") # chargement du modèle de contrôle
    
    """ What ac looks like
    ac = core.ActorCritic(
            actor_type=conf['actor'],
            observation_space=env.observation_space,
            action_space=env.action_space,
            use_standardized_obs=conf['use_standardized_obs'],
            use_scaled_rewards=conf['use_reward_scaling'],
            use_shared_weights=False,
            ac_kwargs=conf['ac_kwargs']
        )
    model_path = os.path.join(file_name_path, 'torch_save', 'model.pt')
    ac.load_state_dict(torch.load(model_path), strict=False)
    """
    
    # Add PID takeoff here so that the drone is in the air before starting the sequence

    while True:
        # Récupérer l'état actuel du drone depuis le Crazyflie
        # Vous devrez probablement transformer ces données pour les rendre compatibles avec votre modèle
        obs = [
            dict_drone_state["x"], dict_drone_state["y"], dict_drone_state["z"],
            dict_drone_state["qx"], dict_drone_state["qy"], dict_drone_state["qz"], dict_drone_state["qw"],
            dict_drone_state["vx"], dict_drone_state["vy"], dict_drone_state["vz"],
            dict_drone_state["wx"], dict_drone_state["wy"], dict_drone_state["wz"]
        ]
        obs_tensor = torch.as_tensor(obs, dtype=torch.float32)

        # Générer l'action à partir du modèle
        """
        def step(self,
             obs: torch.Tensor
             ) -> tuple:
             
        # Produce action, value, log_prob(action).
        #     If training, this includes exploration noise!

        #     Expects that obs is not pre-processed.

        #     Note:
        #         Training mode can be activated with ac.train()
        #         Evaluation mode is activated by ac.eval()
        
        with torch.no_grad():
            if self.obs_oms:
                # Note: Update RMS in Algorithm.running_statistics() method
                # self.obs_oms.update(obs) if self.training else None
                obs = self.obs_oms(obs)
            v = self.v(obs)
            if self.training:
                a, logp_a = self.pi.sample(obs)
            else:
                a, logp_a = self.pi.predict(obs)

        return a.numpy(), v.numpy(), logp_a.numpy()
        
        What pi looks like
        self.pi = actor_fn(obs_dim=obs_dim,
                           act_dim=act_dim,
                           shared=shared,
                           weight_initialization=weight_initialization,
                           **ac_kwargs['pi'])
                           
        What actor_fn looks like
                           
        """
        action, _, _ = ac.step(obs_tensor)

        # Convertir l'action du modèle en commandes pour le Crazyflie
        # Cette partie dépend de la façon dont votre modèle définit les actions
        # Par exemple, si l'action est une vitesse ou une accélération, convertissez-la en une commande de position ou de vitesse
        command = convert_model_action_to_crazyflie_command(action)

        # Envoyer la commande au Crazyflie
        cf.commander.send_position_setpoint(command[0], command[1], command[2], command[3])

        # Attendre un court moment avant la prochaine itération
        time.sleep(0.1)


if __name__ == '__main__':
    cflib.crtp.init_drivers()
    
    time_start_ref = time.time()

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        reset_estimator(scf)
        start_position_printing(scf)
        # run_sequence(scf, sequence)
        time.sleep(5)
        run_sequence_ai(scf, sequence)

