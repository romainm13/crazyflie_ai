"""

Some simple logging functionality, inspired by rllab's logging.

Logs to a tab-separated-values file (path/to/output_directory/progress.txt)

Source:
    https://github.com/openai/spinningup/blob/master/spinup/utils/logx.py

"""
import joblib
import torch
import os.path as osp
import time
import atexit
import os
import gym
import numpy as np
import json
from torch.utils.tensorboard import SummaryWriter
import warnings
from phoenix_drone_simulation.utils.mpi_tools import proc_id, mpi_statistics_scalar, mpi_print


DEBUG = 10
INFO = 20
WARN = 30
ERROR = 40
DISABLED = 50

MIN_LEVEL = 20


def set_level(level: int):
    """
    Set logging threshold on current logger.
    """
    global MIN_LEVEL
    MIN_LEVEL = level


def debug(msg, *args):
    if MIN_LEVEL <= DEBUG:
        mpi_print(f'DEBUG:\t{msg % args}')


def info(msg, *args):
    if MIN_LEVEL <= INFO:
        mpi_print(f'INFO:\t{msg % args}')


def warn(msg, *args):
    if MIN_LEVEL <= WARN and proc_id() == 0:
        warnings.warn(colorize(f'WARN:\t{msg % args}', 'yellow'))


def error(msg, *args):
    if MIN_LEVEL <= ERROR:
        mpi_print(colorize(f'ERROR:\t{msg % args}', 'red'))


color2num = dict(
    gray=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    crimson=38
)


class ConverterJSON(object):
    """ Convert obj to a version which can be serialized with JSON.
    Use the ConverterJSON class that keeps track of recursive dependencies.
    """
    def __init__(self):
        self.dumped_objs = []  # track dumped objects to avoid recursive loops

    def convert_json(self, obj, depth=0):
        """ Convert obj to a version which can be serialized with JSON. """
        if depth > 5:
            return 'max_convert_depth_reached'
        if is_json_serializable(obj):
            return obj
        else:
            if isinstance(obj, dict):
                return {self.convert_json(k): self.convert_json(v, depth=depth + 1)
                        for k, v in obj.items()}

            elif isinstance(obj, tuple):
                return (self.convert_json(x) for x in obj)

            elif isinstance(obj, list):
                return [self.convert_json(x) for x in obj]

            elif hasattr(obj, '__name__') and not ('lambda' in obj.__name__):
                return self.convert_json(obj.__name__)

            # check if obj is a class:
            elif hasattr(obj, '__dict__') and obj.__dict__:
                if obj in self.dumped_objs:
                    return 'Already dumped elsewhere (stop recursion)'
                else:
                    self.dumped_objs.append(obj)
                    obj_dict = {self.convert_json(k): self.convert_json(v, depth=depth + 1)
                                for k, v in obj.__dict__.items()}
                return {str(obj): obj_dict}
            return str(obj)


def is_json_serializable(v):
    try:
        json.dumps(v)
        return True
    except:
        return False


def filter_values_in_dict(dic):
    """ Drop keys from dictionary which are not int, float, bool or str."""
    cleared_dict = dict()
    for (k, v) in dic.items():
        if isinstance(v, int) or isinstance(v, float) \
                or isinstance(v, str) or isinstance(v, bool):
            cleared_dict[k] = v
        if isinstance(v, dict):
            filtered = filter_values_in_dict(v)
            # cleared_dict.update(**filtered)
    print(cleared_dict)
    # raise NotImplementedError
    return cleared_dict


def colorize(string, color, bold=False, highlight=False):
    """
    Colorize a string.

    This function was originally written by John Schulman.
    """
    attr = []
    num = color2num[color]
    if highlight: num += 10
    attr.append(str(num))
    if bold: attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)


def setup_logger_kwargs(
        exp_name='vpg',
        seed=None,
        base_dir='/var/tmp/',
        datestamp=True,
        level=1,
        use_tensor_board=True,
        verbose=True
) -> dict:
    """
    Sets up the output_dir for a logger and returns a dict for logger kwargs.
    If no seed is given and datestamp is false,
    ::
        output_dir = data_dir/exp_name
    If a seed is given and datestamp is false,
    ::
        output_dir = data_dir/exp_name/exp_name_s[seed]
    If datestamp is true, amend to
    ::
        output_dir = data_dir/YY-MM-DD_exp_name/YY-MM-DD_HH-MM-SS_exp_name_s[seed]
    You can force datestamp=True by setting ``FORCE_DATESTAMP=True`` in
    ``spinup/user_config.py``.
    Args:
        exp_name (string): Name for experiment.
        seed (int): Seed for random number generators used by experiment.
        base_dir (string): Path to folder where results should be saved.
        datestamp (bool): Whether to include a date and timestamp in the
            name of the save directory.
    Returns:
        logger_kwargs, a dict containing output_dir and exp_name.
    """
    # Make base path
    if datestamp:
        relpath = time.strftime("%Y-%m-%d__%H-%M-%S")
    else:
        relpath = ''

    if seed is not None:
        subfolder = '_'.join(['seed', str(seed).zfill(5)])
        relpath = os.path.join(relpath, subfolder)

    logger_kwargs = dict(log_dir=os.path.join(base_dir, exp_name, relpath),
                         exp_name=exp_name,
                         level=level,
                         use_tensor_board=use_tensor_board,
                         verbose=verbose)
    return logger_kwargs


class Logger:
    """
    A general-purpose logger.

    Makes it easy to save diagnostics, hyper-parameter configurations, the
    state of a training run, and the trained model.
    """

    def __init__(self,
                 log_dir,
                 output_fname='progress.csv',
                 debug: bool = False,
                 exp_name=None,
                 level: int = 1,  # verbosity level
                 use_tensor_board=True,
                 verbose=True):
        """
        Initialize a Logger.

        Args:
            log_dir (string): A directory for saving results to. If
                ``None``, defaults to a temp directory of the form
                ``/tmp/experiments/somerandomnumber``.

            output_fname (string): Name for the tab-separated-value file
                containing metrics logged throughout a training run.
                Defaults to ``progress.txt``.

            exp_name (string): Experiment name. If you run multiple training
                runs and give them all the same ``exp_name``, the plotter
                will know to group them. (Use case: if you run the same
                hyperparameter configuration with multiple random seeds, you
                should give them all the same ``exp_name``.)
        """
        self.log_dir = log_dir
        self.debug = debug if proc_id() == 0 else False
        self.level = level
        # only the MPI root process is allowed to print information to console
        self.verbose = verbose if proc_id() == 0 else False

        if proc_id() == 0:
            os.makedirs(self.log_dir, exist_ok=True)
            self.output_file = open(osp.join(self.log_dir, output_fname), 'w')
            atexit.register(self.output_file.close)
            print(colorize(f"Logging data to {self.output_file.name}",
                           'cyan', bold=True))
        else:
            self.output_file = None

        self.epoch = 0
        self.first_row = True
        self.log_headers = []
        self.log_current_row = {}
        self.exp_name = exp_name
        self.torch_saver_elements = None

        # Setup tensor board logging if enabled and MPI root process
        self.summary_writer = SummaryWriter(os.path.join(self.log_dir, 'tb')) \
            if use_tensor_board and proc_id() == 0 else None

    def close(self):
        """Close opened output files immediately after training in order to
        avoid number of open files overflow. Avoids the following error:
        OSError: [Errno 24] Too many open files
        """
        if proc_id() == 0:
            self.output_file.close()

    def debug(self, msg, color='yellow'):
        """Print a colorized message to stdout."""
        if self.debug:
            print(colorize(msg, color, bold=False))

    @classmethod
    def info(cls, msg, *args):
        info(msg, *args)

    def log(self, msg, color='green'):
        """Print a colorized message to stdout."""
        if self.verbose and self.level > 0:
            print(colorize(msg, color, bold=False))

    def log_tabular(self, key, val):
        """
        Log a value of some diagnostic.

        Call this only once for each diagnostic quantity, each iteration.
        After using ``log_tabular`` to store values for each diagnostic,
        make sure to call ``dump_tabular`` to write them out to file and
        stdout (otherwise they will not get saved anywhere).
        """
        if self.first_row:
            self.log_headers.append(key)
        else:
            assert key in self.log_headers, "Trying to introduce a new key %s that you didn't include in the first iteration" % key
        assert key not in self.log_current_row, "You already set %s this iteration. Maybe you forgot to call dump_tabular()" % key
        self.log_current_row[key] = val

    def save_config(self, config: dict, file_name='config.json'):
        r"""Log an experiment configuration.
        Call this once at the top of your experiment, passing in all important
        config vars as a dict. This will serialize the config to JSON, while
        handling anything which can't be serialized in a graceful way (writing
        as informative a string as possible).
        """
        self.save_dict_to_disk(dic=config, file_name=file_name)

    def save_dict_to_disk(self, dic: dict, file_name: str, console_print=True):
        r"""Dumps a dictionary to the disk.
        Note: Only root process logs configurations!
        """
        assert isinstance(dic, dict), f'Got {type(dic)} but expected dict'
        if proc_id() == 0:  # only root process is allowed to log...
            # Use ConverterJSON class to keep track of recursive dependencies:
            config_json = ConverterJSON().convert_json(dic)
            if self.exp_name is not None:
                config_json['exp_name'] = self.exp_name

            output = json.dumps(config_json, separators=(',', ':\t'), indent=4,
                                sort_keys=True)
            if console_print and self.verbose and self.level > 0:
                print(colorize('Run with config:', color='yellow', bold=True))
                print(output)
            with open(osp.join(self.log_dir, file_name), 'w') as out:
                out.write(output)

    def save_env_config(self, env: gym.Env, file_name='env_config.json'):
        r"""Save configuration of environment to disk."""
        assert isinstance(env, gym.Env)
        all_env_locals = env.unwrapped.__dict__.copy()
        self.save_dict_to_disk(all_env_locals, file_name, console_print=False)

    def save_state(self, state_dict, itr=None):
        """
        Saves the state of an experiment.

        To be clear: this is about saving *state*, not logging diagnostics.
        All diagnostic logging is separate from this function. This function
        will save whatever is in ``state_dict``---usually just a copy of the
        environment---and the most recent parameters for the model you
        previously set up saving for with ``setup_tf_saver``.

        Call with any frequency you prefer. If you only want to maintain a
        single state and overwrite it at each call with the most recent
        version, leave ``itr=None``. If you want to keep all of the states you
        save, provide unique (increasing) values for 'itr'.

        Args:
            state_dict (dict): Dictionary containing essential elements to
                describe the current state of training.

            itr: An int, or None. Current iteration of training.
        """
        if proc_id() ==0:
            fname = 'state.pkl' if itr is None else 'state%d.pkl' % itr
            try:
                joblib.dump(state_dict, osp.join(self.log_dir, fname))
            except:
                self.log('Warning: could not pickle state_dict.', color='red')
            if hasattr(self, 'torch_saver_elements'):
                self.torch_save(itr)

    @classmethod
    def set_level(cls, level: int):
        set_level(level=level)

    def setup_torch_saver(self, what_to_save):
        """
        Set up easy model saving for a single PyTorch model.

        Because PyTorch saving and loading is especially painless, this is
        very minimal; we just need references to whatever we would like to
        pickle. This is integrated into the logger because the logger
        knows where the user would like to save information about this
        training run.

        Args:
            what_to_save: Any PyTorch model or serializable object containing
                PyTorch models.
        """
        self.torch_saver_elements = what_to_save

    def torch_save(self, itr=None):
        """
        Saves the PyTorch model (or models).
        """
        if proc_id() == 0:
            self.log('Save model to disk...')
            assert self.torch_saver_elements is not None,\
                "First have to setup saving with self.setup_torch_saver"
            fpath = 'torch_save'
            fpath = osp.join(self.log_dir, fpath)
            fname = 'model' + ('%d' % itr if itr is not None else '') + '.pt'
            fname = osp.join(fpath, fname)
            os.makedirs(fpath, exist_ok=True)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # We are using a non-recommended way of saving PyTorch models,
                # by pickling whole objects (which are dependent on the exact
                # directory structure at the time of saving) as opposed to
                # just saving network weights. This works sufficiently well
                # for the purposes of Spinning Up, but you may want to do
                # something different for your personal PyTorch project.
                # We use a catch_warnings() context to avoid the warnings about
                # not being able to save the source code.
                torch.save(self.torch_saver_elements, fname)
            torch.save(self.torch_saver_elements.state_dict(), fname)
            self.log('Done.')

    def dump_tabular(self) -> None:
        """
        Write all of the diagnostics from the current iteration.

        Writes both to stdout, and to the output file.
        """
        if proc_id() == 0:
            vals = list()
            self.epoch += 1
            # Print formatted information into console
            # Adapted from:
            # https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/logger.py
            # Create strings for printing
            key2str = {}
            tag = None
            for (key, value) in self.log_current_row.items():
                vals.append(value)
                if isinstance(value, float):
                    # Align left
                    value_str = f"{value:<8.3g}"
                else:
                    value_str = str(value)

                if key.find("/") > 0:  # Find tag and add it to the dict
                    tag = key[: key.find("/") + 1]
                    key2str[self._truncate(tag)] = ""
                # add tab to tag from key
                if tag is not None and tag in key:
                    key = str("   " + key)

                key2str[self._truncate(key)] = self._truncate(value_str)

            # Find max widths
            if len(key2str) == 0:
                warnings.warn("Tried to write empty key-value dict")
                return
            else:
                key_width = max(map(len, key2str.keys()))
                val_width = max(map(len, key2str.values()))

            # Print out the data
            dashes = "-" * (key_width + val_width + 7)
            print(dashes) if self.verbose and self.level > 0 else None
            for key, value in key2str.items():
                key_space = " " * (key_width - len(key))
                val_space = " " * (val_width - len(value))
                print(f"| {key}{key_space} | {value}{val_space} |") \
                    if self.verbose and self.level > 0 else None
            print(dashes) if self.verbose and self.level > 0 else None

            # Write into the output file (can be any text file format, e.g. CSV)
            if self.output_file is not None:
                if self.first_row:
                    self.output_file.write(",".join(self.log_headers) + "\n")
                self.output_file.write(",".join(map(str, vals)) + "\n")
                self.output_file.flush()

            if self.summary_writer is not None:
                [self.summary_writer.add_scalar(k, v, global_step=self.epoch)
                 for (k, v) in zip(self.log_headers, vals)]
                # Flushes the event file to disk. Call this method to make sure
                # that all pending events have been written to disk.
                self.summary_writer.flush()

        # free logged information in all processes...
        self.log_current_row.clear()
        self.first_row = False

    @classmethod
    def _truncate(cls, string: str, max_length: int = 23) -> str:
        return string[: max_length - 3] + "..." if len(string) > max_length else string


class EpochLogger(Logger):
    """
    A variant of Logger tailored for tracking average values over epochs.

    Typical use case: there is some quantity which is calculated many times
    throughout an epoch, and at the end of the epoch, you would like to
    report the average / std / min / max value of that quantity.

    With an EpochLogger, each time the quantity is calculated, you would
    use

    .. code-block:: python

        epoch_logger.store(NameOfQuantity=quantity_value)

    to load it into the EpochLogger's state. Then at the end of the epoch, you
    would use

    .. code-block:: python

        epoch_logger.log_tabular(NameOfQuantity, **options)

    to record the desired values.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epoch_dict = dict()

    def dump_tabular(self):
        super().dump_tabular()
        # Check if all values from dict are dumped -> prevent memory overflow
        for k, v in self.epoch_dict.items():
            if len(v) > 0:
                print(f'epoch_dict: key={k} was not logged.')
            # assert len(v) > 0, f'epoch_dict: key={k} was not logged.'

    def get_stats(self, key, with_min_and_max=False):
        assert key in self.epoch_dict, f'key={key} not in dict'
        v = self.epoch_dict[key]
        vals = np.concatenate(v) if isinstance(v[0], np.ndarray) and len(
            v[0].shape) > 0 else v
        return mpi_statistics_scalar(vals, with_min_and_max=with_min_and_max)

    def store(self, **kwargs):
        """
        Save something into the epoch_logger's current state.

        Provide an arbitrary number of keyword arguments with numerical
        values.
        """
        for k, v in kwargs.items():
            if not (k in self.epoch_dict.keys()):
                self.epoch_dict[k] = []
            self.epoch_dict[k].append(v)

    def log_tabular(self, key, val=None, min_and_max=False, std=False):
        """
        Log a value or possibly the mean/std/min/max values of a diagnostic.

        Args:
            key (string): The name of the diagnostic. If you are logging a
                diagnostic whose state has previously been saved with
                ``store``, the key here has to match the key you used there.

            val: A value for the diagnostic. If you have previously saved
                values for this key via ``store``, do *not* provide a ``val``
                here.

            min_and_max (bool): If true, log min and max values of the
                diagnostic over the epoch.

            std (bool): If true, do log the standard deviation
                of the diagnostic over the epoch.
        """
        if val is not None:
            super().log_tabular(key, val)
        else:
            stats = self.get_stats(key, min_and_max)
            if min_and_max or std:
                super().log_tabular(key + '/Mean', stats[0])
            else:
                super().log_tabular(key, stats[0])
            if std:
                super().log_tabular(key + '/Std', stats[1])
            if min_and_max:
                super().log_tabular(key + '/Min', stats[2])
                super().log_tabular(key + '/Max', stats[3])
        self.epoch_dict[key] = []
