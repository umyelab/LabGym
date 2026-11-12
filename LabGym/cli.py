'''
Copyright (C)
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
'''

import argparse
import json
import logging
import os
import sys
import yaml

logger = logging.getLogger(__name__)

class CLIConfigError(Exception):
    """Raised when CLI or YAML configuration validation fails."""
    pass


TRAIN_CATEGORIZER_DEFAULTS = {
    'network_type': 'combnet',
    'out_path': None,
    'out_folder': None,
    'dim_conv': 64,
    'dim_tconv': 32,
    'channel': 1,
    'time_step': 15,
    'level_conv': 2,
    'level_tconv': 1,
    'aug_methods': [],
    'augvalid': True,
    'include_bodyparts': True,
    'std': 0.0,
    'background_free': True,
    'black_background': True,
    'behavior_mode': 0,
    'social_distance': 0.0,
    'color_costar': False,
    'training_onfly': False,
}
REQUIRED_TRAIN_CATEGORIZER_KEYS = {'data_path', 'model_path'}
ALLOWED_TRAIN_CATEGORIZER_KEYS = set(TRAIN_CATEGORIZER_DEFAULTS.keys()) | REQUIRED_TRAIN_CATEGORIZER_KEYS

AUG_METHOD_MAP = {
    'random rotation': 'random rotation',
    'horizontal flipping': 'horizontal flipping',
    'vertical flipping': 'vertical flipping',
    'random brightening': 'random brightening',
    'random dimming': 'random dimming',
    'random shearing': 'random shearing',
    'random rescaling': 'random rescaling',
    'random deletion': 'random deletion',
    'rotation': 'random rotation',
    'flipping': 'horizontal flipping',
    'brightening': 'random brightening',
    'dimming': 'random dimming',
    'shearing': 'random shearing',
    'rescaling': 'random rescaling',
    'deletion': 'random deletion',
}

TRAIN_DETECTOR_DEFAULTS = {
    'iteration_num': 200,
    'inference_size': 480,
}
REQUIRED_TRAIN_DETECTOR_KEYS = {'path_to_annotation', 'path_to_trainingimages', 'model_path'}
ALLOWED_TRAIN_DETECTOR_KEYS = set(TRAIN_DETECTOR_DEFAULTS.keys()) | REQUIRED_TRAIN_DETECTOR_KEYS

TEST_CATEGORIZER_DEFAULTS = {
    'result_path': None,
}
REQUIRED_TEST_CATEGORIZER_KEYS = {'groundtruth_path', 'model_path'}
ALLOWED_TEST_CATEGORIZER_KEYS = set(TEST_CATEGORIZER_DEFAULTS.keys()) | REQUIRED_TEST_CATEGORIZER_KEYS

TEST_DETECTOR_DEFAULTS = {}
REQUIRED_TEST_DETECTOR_KEYS = {'path_to_annotation', 'path_to_testingimages', 'model_path', 'result_path'}
ALLOWED_TEST_DETECTOR_KEYS = set(TEST_DETECTOR_DEFAULTS.keys()) | REQUIRED_TEST_DETECTOR_KEYS

INFER_DEFAULTS = {
    'path_to_categorizer': None,
    'path_to_detector': None,
    'use_detector': False,
    'background_path': None,
    'framewidth': None,
    'delta': 10000.0,
    'animal_kinds': ['animal'],
    'animal_to_include': [],
    'behavior_to_include': ['all'],
    'detector_batch': 1,
    'detection_threshold': 0.0,
    'decode_animalnumber': False,
    'animal_number': None,
    'autofind_t': False,
    'decode_t': False,
    't': 0.0,
    'duration': 0.0,
    'decode_extraction': False,
    'ex_start': 0,
    'ex_end': None,
    'stable_illumination': True,
    'animal_vs_bg': 0,
    'ID_colors': [(255, 255, 255)],
    'parameter_to_analyze': [],
    'uncertain': 0.0,
    'min_length': None,
    'show_legend': True,
    'normalize_distance': True,
    'correct_ID': False,
    'specific_behaviors': {},
}
REQUIRED_INFER_KEYS = {'path_to_videos', 'result_path'}
ALLOWED_INFER_KEYS = (
    set(INFER_DEFAULTS.keys())
    | REQUIRED_INFER_KEYS
    | {'correct_id', 'id_colors'}
)

PATH_KEYS = {
    'data_path', 'model_path', 'out_path', 'out_folder',
    'path_to_annotation', 'path_to_trainingimages', 'path_to_testingimages',
    'groundtruth_path', 'result_path', 'path_to_categorizer', 'path_to_detector',
    'background_path'
}


def parse_json_or_val(v):
    if v is None:
        return None
    if isinstance(v, str) and (v.startswith('{') or v.startswith('[')):
        try:
            return json.loads(v)
        except Exception:
            pass
    return v


def validate_types_and_ranges(command_name, config):
    for path_key in PATH_KEYS:
        if path_key in config and config[path_key] is not None:
            val = config[path_key]
            if isinstance(val, bool) or not isinstance(val, str) or not val.strip():
                raise CLIConfigError(
                    f"Parameter '{path_key}' must be a non-empty string path (got {type(val).__name__}: {val!r})."
                )

    if 'path_to_videos' in config and config['path_to_videos'] is not None:
        val = config['path_to_videos']
        if isinstance(val, bool) or not isinstance(val, list) or len(val) == 0:
            raise CLIConfigError(
                f"Parameter 'path_to_videos' must be a non-empty list of video paths (got {val!r})."
            )
        for item in val:
            if isinstance(item, bool) or not isinstance(item, str) or not item.strip():
                raise CLIConfigError(
                    f"Items in 'path_to_videos' must be non-empty string paths (got {item!r})."
                )

    pos_int_keys = [
        'dim_conv', 'dim_tconv', 'iteration_num', 'inference_size', 'detector_batch',
        'framewidth', 'min_length'
    ]
    for key in pos_int_keys:
        if key in config and config[key] is not None:
            val = config[key]
            if isinstance(val, bool) or not isinstance(val, int) or val <= 0:
                raise CLIConfigError(
                    f"Parameter '{key}' for '{command_name}' must be a positive integer (got {val!r})."
                )

    non_neg_int_keys = ['time_step', 'ex_start', 'ex_end']
    for key in non_neg_int_keys:
        if key in config and config[key] is not None:
            val = config[key]
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise CLIConfigError(
                    f"Parameter '{key}' for '{command_name}' must be a non-negative integer (got {val!r})."
                )

    if config.get('ex_start') is not None and config.get('ex_end') is not None:
        if config['ex_end'] < config['ex_start']:
            raise CLIConfigError(
                f"Parameter 'ex_end' ({config['ex_end']}) must be greater than or equal to 'ex_start' ({config['ex_start']})."
            )

    if 'channel' in config and config['channel'] is not None:
        val = config['channel']
        if isinstance(val, bool) or not isinstance(val, int) or val not in (1, 3):
            raise CLIConfigError(
                f"Parameter 'channel' must be 1 or 3 (got {val!r})."
            )

    if 'animal_vs_bg' in config and config['animal_vs_bg'] is not None:
        val = config['animal_vs_bg']
        if isinstance(val, bool) or not isinstance(val, int) or val not in (0, 1, 2):
            raise CLIConfigError(
                f"Parameter 'animal_vs_bg' must be 0, 1, or 2 "
                f"(0=animal brighter than background, 1=animal darker, 2=hard to tell; got {val!r})."
            )

    for level_key in ['level_conv', 'level_tconv']:
        if level_key in config and config[level_key] is not None:
            val = config[level_key]
            if isinstance(val, bool) or not isinstance(val, int) or not (1 <= val <= 5):
                raise CLIConfigError(
                    f"Parameter '{level_key}' must be an integer between 1 and 5 (got {val!r})."
                )

    if 'network_type' in config and config['network_type'] is not None:
        val = config['network_type']
        valid_nets = {'combnet', 'pattern_recognizer', 'animation_analyzer', 'combined_network'}
        if isinstance(val, bool) or not isinstance(val, str) or val not in valid_nets:
            raise CLIConfigError(
                f"Invalid network_type '{val}'. Choose from: {sorted(valid_nets)}."
            )

    if 'behavior_mode' in config and config['behavior_mode'] is not None:
        val = config['behavior_mode']
        if isinstance(val, bool) or not isinstance(val, int) or not (0 <= val <= 3):
            raise CLIConfigError(
                f"Parameter 'behavior_mode' must be an integer between 0 and 3 (got {val!r})."
            )

    list_str_keys = [
        'aug_methods', 'animal_kinds', 'animal_to_include',
        'behavior_to_include', 'parameter_to_analyze'
    ]
    for key in list_str_keys:
        if key in config and config[key] is not None:
            val = config[key]
            if isinstance(val, bool) or not isinstance(val, list):
                raise CLIConfigError(
                    f"Parameter '{key}' for '{command_name}' must be a list of strings (got {type(val).__name__}: {val!r})."
                )
            for item in val:
                if isinstance(item, bool) or not isinstance(item, str):
                    raise CLIConfigError(
                        f"Items in '{key}' for '{command_name}' must be strings (got {item!r})."
                    )

    if 'aug_methods' in config and config['aug_methods'] is not None:
        for item in config['aug_methods']:
            if item not in AUG_METHOD_MAP:
                raise CLIConfigError(
                    f"Invalid augmentation method '{item}'. Choose from: {sorted(set(AUG_METHOD_MAP.values()))}."
                )

    float_keys = ['std', 'social_distance', 't', 'duration', 'delta']
    for key in float_keys:
        if key in config and config[key] is not None:
            val = config[key]
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
                raise CLIConfigError(
                    f"Parameter '{key}' must be a non-negative float (got {val!r})."
                )

    for thresh_key in ['detection_threshold', 'uncertain']:
        if thresh_key in config and config[thresh_key] is not None:
            val = config[thresh_key]
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not (0.0 <= float(val) <= 1.0):
                raise CLIConfigError(
                    f"Parameter '{thresh_key}' must be between 0.0 and 1.0 (got {val!r})."
                )

    bool_keys = [
        'training_onfly', 'augvalid', 'include_bodyparts', 'background_free', 'black_background',
        'color_costar', 'use_detector', 'decode_animalnumber', 'autofind_t', 'decode_t',
        'decode_extraction', 'stable_illumination', 'show_legend', 'normalize_distance',
        'correct_ID', 'correct_id'
    ]
    for key in bool_keys:
        if key in config and config[key] is not None:
            val = config[key]
            if not isinstance(val, bool):
                raise CLIConfigError(
                    f"Parameter '{key}' must be a boolean True/False (got {type(val).__name__}: {val!r})."
                )

    if 'ID_colors' in config and config['ID_colors'] is not None:
        val = config['ID_colors']
        if isinstance(val, bool) or not isinstance(val, (list, tuple)):
            raise CLIConfigError(
                f"Parameter 'ID_colors' must be a list of color entries (got {type(val).__name__}: {val!r})."
            )

    if 'specific_behaviors' in config and config['specific_behaviors'] is not None:
        val = config['specific_behaviors']
        if isinstance(val, bool) or not isinstance(val, dict):
            raise CLIConfigError(
                f"Parameter 'specific_behaviors' must be a dictionary (got {type(val).__name__}: {val!r})."
            )

    if 'animal_number' in config and config['animal_number'] is not None:
        val = config['animal_number']
        if isinstance(val, bool):
            raise CLIConfigError(
                f"Parameter 'animal_number' must be a positive integer or dictionary (got {val!r})."
            )
        if isinstance(val, int):
            if val <= 0:
                raise CLIConfigError(
                    f"Parameter 'animal_number' must be a positive integer (got {val!r})."
                )
        elif isinstance(val, dict):
            for k, v in val.items():
                if not isinstance(k, str) or not k.strip():
                    raise CLIConfigError(
                        f"Animal kinds in 'animal_number' dictionary must be non-empty strings (got {k!r})."
                    )
                if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
                    raise CLIConfigError(
                        f"Animal counts in 'animal_number' dictionary must be positive integers (got {v!r} for '{k}')."
                    )
        else:
            raise CLIConfigError(
                f"Parameter 'animal_number' must be a positive integer or dictionary (got {type(val).__name__}: {val!r})."
            )

    if command_name == "labgym-cli infer":
        if isinstance(config.get('animal_number'), dict) and not config.get('use_detector'):
            raise CLIConfigError(
                "Structured 'animal_number' mapping is only supported when detector inference is enabled ('--use-detector'). "
                "For non-detector inference, specify a single positive integer."
            )
        if config.get('use_detector') and config.get('animal_vs_bg', 0) != 0:
            raise CLIConfigError(
                "Parameter 'animal_vs_bg' applies only to background-subtraction inference. "
                "With detector inference enabled ('--use-detector'), leave 'animal_vs_bg' at the default 0."
            )

    if command_name == "labgym-cli train categorizer":
        net_type = config.get('network_type', 'combnet')
        if config.get('training_onfly'):
            if config.get('aug_methods'):
                raise CLIConfigError(
                    "On-the-fly training ('training_onfly') does not support augmentation settings ('aug_methods')."
                )
            if config.get('augvalid') is False:
                raise CLIConfigError(
                    "On-the-fly training ('training_onfly') does not support '--no-augvalid' / 'augvalid: false'."
                )
            if config.get('out_folder') is not None:
                raise CLIConfigError(
                    "On-the-fly training ('training_onfly') does not support caching frames to 'out_folder'."
                )
        if net_type == 'pattern_recognizer' and config.get('color_costar'):
            raise CLIConfigError(
                "Option '--color-costar' / 'color_costar' is not supported for 'pattern_recognizer'."
            )
        if config.get('behavior_mode', 0) >= 3 and net_type != 'pattern_recognizer':
            raise CLIConfigError(
                f"behavior_mode={config['behavior_mode']} (static images) is only supported when network_type is 'pattern_recognizer' (got '{net_type}')."
            )


def resolve_config(command_name, defaults, allowed_keys, required_keys, config_path, cli_args_dict):
    """Resolve config from defaults, YAML file, and CLI overrides."""
    resolved = defaults.copy()

    if config_path is not None:
        expanded_config = os.path.expanduser(config_path)
        if not os.path.isfile(expanded_config):
            raise CLIConfigError(f"Specified configuration file not found: '{config_path}'")
        try:
            with open(expanded_config, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            raise CLIConfigError(f"Error reading YAML file '{config_path}': {e}")

        if yaml_data is not None:
            if not isinstance(yaml_data, dict):
                raise CLIConfigError(
                    f"Configuration file '{config_path}' must contain a key-value mapping (YAML dictionary)."
                )
            unknown_keys = set(yaml_data.keys()) - allowed_keys
            if unknown_keys:
                raise CLIConfigError(
                    f"Unknown configuration key(s) in '{config_path}' for command '{command_name}': "
                    f"{', '.join(sorted(unknown_keys))}"
                )
            for k, v in yaml_data.items():
                resolved[k] = v

    for k, v in cli_args_dict.items():
        if k not in ['config', 'action', 'target', 'func'] and v is not None:
            resolved[k] = v

    if 'correct_id' in resolved:
        resolved['correct_ID'] = resolved.pop('correct_id')
    if 'id_colors' in resolved:
        resolved['ID_colors'] = resolved.pop('id_colors')

    for pk in PATH_KEYS:
        if pk in resolved and isinstance(resolved[pk], str) and not isinstance(resolved[pk], bool):
            resolved[pk] = os.path.expanduser(resolved[pk])

    if 'path_to_videos' in resolved and resolved['path_to_videos'] is not None:
        val = resolved['path_to_videos']
        if isinstance(val, str) and not isinstance(val, bool):
            resolved['path_to_videos'] = [os.path.expanduser(val)]
        elif isinstance(val, list):
            resolved['path_to_videos'] = [
                os.path.expanduser(item) if isinstance(item, str) and not isinstance(item, bool) else item
                for item in val
            ]

    if 'specific_behaviors' in resolved and isinstance(resolved['specific_behaviors'], str):
        resolved['specific_behaviors'] = parse_json_or_val(resolved['specific_behaviors'])
    if 'ID_colors' in resolved and isinstance(resolved['ID_colors'], str):
        resolved['ID_colors'] = parse_json_or_val(resolved['ID_colors'])
    if 'animal_number' in resolved and isinstance(resolved['animal_number'], str):
        val_str = resolved['animal_number'].strip()
        if val_str.startswith('{') or val_str.startswith('['):
            resolved['animal_number'] = parse_json_or_val(val_str)
        else:
            try:
                resolved['animal_number'] = int(val_str)
            except ValueError:
                pass

    validate_types_and_ranges(command_name, resolved)

    missing = [rk for rk in required_keys if resolved.get(rk) is None]
    if missing:
        raise CLIConfigError(
            f"Missing required parameter(s) for '{command_name}': {', '.join(sorted(missing))}. "
            f"Please supply via --config YAML or explicit inline options."
        )

    return resolved


def add_common_config_arg(parser):
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help="Path to YAML workflow configuration file specifying settings."
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="labgym-cli",
        description="LabGym CLI: Headless command-line interface for training, testing, and behavioral inference."
    )
    subparsers = parser.add_subparsers(dest="action", help="Available actions")

    train_parser = subparsers.add_parser("train", help="Train categorizers or detectors")
    train_sub = train_parser.add_subparsers(dest="target", help="Target network to train", required=False)

    p_train_cat = train_sub.add_parser("categorizer", help="Train behavior classifier (Pattern Recognizer, CombNet, etc.)")
    add_common_config_arg(p_train_cat)
    p_train_cat.add_argument("--data-path", type=str, default=None, help="Path to training examples dataset")
    p_train_cat.add_argument("--model-path", type=str, default=None, help="Path to output model directory")
    p_train_cat.add_argument("--network-type", type=str, choices=['combnet', 'pattern_recognizer', 'animation_analyzer', 'combined_network'], default=None, help="Type of network architecture")
    p_train_cat.add_argument("--out-path", type=str, default=None, help="Output path for logs/reports")
    p_train_cat.add_argument("--out-folder", type=str, default=None, help="Target folder for caching prepared frames")
    p_train_cat.add_argument("--dim-conv", type=int, default=None, help="Input dimension for Pattern Recognizer")
    p_train_cat.add_argument("--dim-tconv", type=int, default=None, help="Input dimension for Animation Analyzer")
    p_train_cat.add_argument("--channel", type=int, choices=[1, 3], default=None, help="Channel depth (1 or 3)")
    p_train_cat.add_argument("--time-step", type=int, default=None, help="Time steps/frames per behavior sequence")
    p_train_cat.add_argument("--level-conv", type=int, default=None, help="Complexity level of Pattern Recognizer (1-5)")
    p_train_cat.add_argument("--level-tconv", type=int, default=None, help="Complexity level of Animation Analyzer (1-5)")
    p_train_cat.add_argument("--aug-methods", type=str, nargs="+", default=None, help="List of augmentation methods")
    p_train_cat.add_argument("--augvalid", action=argparse.BooleanOptionalAction, default=None, help="Validate augmentation data")
    p_train_cat.add_argument("--include-bodyparts", action=argparse.BooleanOptionalAction, default=None, help="Include body parts in calculations")
    p_train_cat.add_argument("--std", type=float, default=None, help="Standard deviation parameter for body parts")
    p_train_cat.add_argument("--background-free", action=argparse.BooleanOptionalAction, default=None, help="Exclude background")
    p_train_cat.add_argument("--black-background", action=argparse.BooleanOptionalAction, default=None, help="Use black background")
    p_train_cat.add_argument("--behavior-mode", type=int, default=None, help="Behavior mode selection")
    p_train_cat.add_argument("--social-distance", type=float, default=None, help="Social distance threshold")
    p_train_cat.add_argument("--color-costar", action=argparse.BooleanOptionalAction, default=None, help="Keep supporting actors in color")
    p_train_cat.add_argument("--training-onfly", action=argparse.BooleanOptionalAction, default=None, help="Train using on-the-fly behavior generator")
    p_train_cat.set_defaults(func=handle_train_categorizer)

    p_train_det = train_sub.add_parser("detector", help="Train object detector (Detectron2)")
    add_common_config_arg(p_train_det)
    p_train_det.add_argument("--path-to-annotation", type=str, default=None, help="Path to COCO JSON annotation file")
    p_train_det.add_argument("--path-to-trainingimages", type=str, default=None, help="Path to training images folder")
    p_train_det.add_argument("--model-path", type=str, default=None, help="Path to output model directory")
    p_train_det.add_argument("--iteration-num", type=int, default=None, help="Number of training iterations")
    p_train_det.add_argument("--inference-size", type=int, default=None, help="Inference image frame size")
    p_train_det.set_defaults(func=handle_train_detector)

    test_parser = subparsers.add_parser("test", help="Evaluate models headlessly")
    test_sub = test_parser.add_subparsers(dest="target", help="Target model to test", required=False)

    p_test_cat = test_sub.add_parser("categorizer", help="Evaluate behavior classifier")
    add_common_config_arg(p_test_cat)
    p_test_cat.add_argument("--groundtruth-path", type=str, default=None, help="Path to ground-truth testing dataset")
    p_test_cat.add_argument("--model-path", type=str, default=None, help="Path to trained categorizer directory")
    p_test_cat.add_argument("--result-path", type=str, default=None, help="Path to output test results")
    p_test_cat.set_defaults(func=handle_test_categorizer)

    p_test_det = test_sub.add_parser("detector", help="Evaluate object detector")
    add_common_config_arg(p_test_det)
    p_test_det.add_argument("--path-to-annotation", type=str, default=None, help="Path to COCO JSON annotation file")
    p_test_det.add_argument("--path-to-testingimages", type=str, default=None, help="Path to testing images directory")
    p_test_det.add_argument("--model-path", type=str, default=None, help="Path to trained detector directory")
    p_test_det.add_argument("--result-path", type=str, default=None, help="Path to output test results")
    p_test_det.set_defaults(func=handle_test_detector)

    infer_parser = subparsers.add_parser("infer", help="Execute animal tracking and behavior classification on videos or images")
    add_common_config_arg(infer_parser)
    infer_parser.add_argument("--path-to-videos", type=str, nargs="+", default=None, help="Path(s) to video files or directory")
    infer_parser.add_argument("--result-path", type=str, default=None, help="Path to write inference results")
    infer_parser.add_argument("--path-to-categorizer", type=str, default=None, help="Path to trained categorizer directory")
    infer_parser.add_argument("--path-to-detector", type=str, default=None, help="Path to trained detector directory")
    infer_parser.add_argument("--use-detector", action=argparse.BooleanOptionalAction, default=None, help="Use detector for animal tracking")
    infer_parser.add_argument("--background-path", type=str, default=None, help="Path to background image")
    infer_parser.add_argument("--framewidth", type=int, default=None, help="Target resizing width for frames")
    infer_parser.add_argument("--delta", type=float, default=None, help="Optogenetics stimulation delta trigger threshold")
    infer_parser.add_argument("--animal-kinds", type=str, nargs="+", default=None, help="Animal categories in detector")
    infer_parser.add_argument("--animal-to-include", type=str, nargs="+", default=None, help="Animals to keep in outputs")
    infer_parser.add_argument("--behavior-to-include", type=str, nargs="+", default=None, help="Behaviors to categorize")
    infer_parser.add_argument("--detector-batch", type=int, default=None, help="Detection processing batch size")
    infer_parser.add_argument("--detection-threshold", type=float, default=None, help="Detection confidence threshold")
    infer_parser.add_argument("--decode-animalnumber", action=argparse.BooleanOptionalAction, default=None, help="Extract animal count from video filenames")
    infer_parser.add_argument("--animal-number", type=str, default=None, help="Animal count or mapping")
    infer_parser.add_argument("--autofind-t", action=argparse.BooleanOptionalAction, default=None, help="Auto-calculate optogenetics trigger")
    infer_parser.add_argument("--decode-t", action=argparse.BooleanOptionalAction, default=None, help="Extract start times from filenames")
    infer_parser.add_argument("--t", type=float, default=None, help="Start time offset in seconds")
    infer_parser.add_argument("--duration", type=float, default=None, help="Total analysis window in seconds")
    infer_parser.add_argument("--decode-extraction", action=argparse.BooleanOptionalAction, default=None, help="Extract start/end frame times")
    infer_parser.add_argument("--ex-start", type=int, default=None, help="Extraction start frame number")
    infer_parser.add_argument("--ex-end", type=int, default=None, help="Extraction end frame number")
    infer_parser.add_argument("--stable-illumination", action=argparse.BooleanOptionalAction, default=None, help="Illumination stability")
    infer_parser.add_argument(
        "--animal-vs-bg",
        type=int,
        default=None,
        help="Animal vs background contrast for background subtraction: 0=brighter (default), 1=darker, 2=hard to tell",
    )
    infer_parser.add_argument("--ID-colors", type=str, default=None, help="Colormap sequence mapping IDs to colors")
    infer_parser.add_argument("--parameter-to-analyze", type=str, nargs="+", default=None, help="Kinematic parameters to extract")
    infer_parser.add_argument("--uncertain", type=float, default=None, help="Uncertainty threshold")
    infer_parser.add_argument("--min-length", type=int, default=None, help="Minimum behavior length in frames")
    infer_parser.add_argument("--show-legend", action=argparse.BooleanOptionalAction, default=None, help="Render behavior legend overlays")
    infer_parser.add_argument("--normalize-distance", action=argparse.BooleanOptionalAction, default=None, help="Normalize metrics relative to contour sizes")
    infer_parser.add_argument("--correct-id", action=argparse.BooleanOptionalAction, default=None, help="Run ID correction heuristics")
    infer_parser.add_argument("--specific-behaviors", type=str, default=None, help="Specific behavior definitions JSON")
    infer_parser.set_defaults(func=handle_infer)

    return parser


def handle_train_categorizer(args):
    config = resolve_config(
        command_name="labgym-cli train categorizer",
        defaults=TRAIN_CATEGORIZER_DEFAULTS,
        allowed_keys=ALLOWED_TRAIN_CATEGORIZER_KEYS,
        required_keys=REQUIRED_TRAIN_CATEGORIZER_KEYS,
        config_path=args.config,
        cli_args_dict=vars(args)
    )

    data_path = config['data_path']
    model_path = config['model_path']
    out_path = config.get('out_path')
    out_folder = config.get('out_folder')

    if not os.path.exists(data_path):
        raise CLIConfigError(f"Training data directory not found: '{data_path}'")
    if not os.path.isdir(data_path):
        raise CLIConfigError(f"Training data path must be a directory: '{data_path}'")

    if config.get('training_onfly'):
        train_sub = os.path.join(data_path, 'train')
        val_sub = os.path.join(data_path, 'validation')
        if not os.path.isdir(train_sub) or not os.path.isdir(val_sub):
            raise CLIConfigError(
                f"On-the-fly training requires both 'train' and 'validation' subdirectories in '{data_path}'."
            )
    else:
        valid_exts = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        found_images = [
            f for f in os.listdir(data_path)
            if os.path.splitext(f)[1].lower() in valid_exts and os.path.isfile(os.path.join(data_path, f))
        ]
        if not found_images:
            raise CLIConfigError(
                f"No supported image files found in '{data_path}'. Supported extensions: {', '.join(sorted(valid_exts))}."
            )

    if os.path.isfile(model_path):
        raise CLIConfigError(f"Model path must be a directory, not an existing file: '{model_path}'")

    if out_path and os.path.isfile(out_path):
        raise CLIConfigError(f"Output path must be a directory, not an existing file: '{out_path}'")

    if out_folder and os.path.isfile(out_folder):
        raise CLIConfigError(f"Output folder must be a directory, not an existing file: '{out_folder}'")

    if config.get('aug_methods'):
        config['aug_methods'] = [AUG_METHOD_MAP[m] for m in config['aug_methods']]

    os.makedirs(model_path, exist_ok=True)
    if out_path:
        os.makedirs(out_path, exist_ok=True)
    if out_folder:
        os.makedirs(out_folder, exist_ok=True)

    print(f"Starting headless Categorizer training ({config['network_type']})...", file=sys.stdout)

    from LabGym.categorizer import Categorizers
    CA = Categorizers()

    net_type = config['network_type']
    onfly = config['training_onfly']

    if net_type == 'pattern_recognizer':
        if onfly:
            CA.train_pattern_recognizer_onfly(
                data_path, model_path, out_path=out_path,
                dim=config['dim_conv'], channel=config['channel'], time_step=config['time_step'],
                level=config['level_conv'], include_bodyparts=config['include_bodyparts'],
                std=config['std'], background_free=config['background_free'],
                black_background=config['black_background'], behavior_mode=config['behavior_mode'],
                social_distance=config['social_distance']
            )
        else:
            CA.train_pattern_recognizer(
                data_path, model_path, out_path=out_path,
                dim=config['dim_conv'], channel=config['channel'], time_step=config['time_step'],
                level=config['level_conv'], aug_methods=config['aug_methods'], augvalid=config['augvalid'],
                include_bodyparts=config['include_bodyparts'], std=config['std'],
                background_free=config['background_free'], black_background=config['black_background'],
                behavior_mode=config['behavior_mode'], social_distance=config['social_distance'],
                out_folder=out_folder
            )
    elif net_type == 'animation_analyzer':
        if onfly:
            CA.train_animation_analyzer_onfly(
                data_path, model_path, out_path=out_path,
                dim=config['dim_tconv'], channel=config['channel'], time_step=config['time_step'],
                level=config['level_tconv'], include_bodyparts=config['include_bodyparts'],
                std=config['std'], background_free=config['background_free'],
                black_background=config['black_background'], behavior_mode=config['behavior_mode'],
                social_distance=config['social_distance'], color_costar=config['color_costar']
            )
        else:
            CA.train_animation_analyzer(
                data_path, model_path, out_path=out_path,
                dim=config['dim_tconv'], channel=config['channel'], time_step=config['time_step'],
                level=config['level_tconv'], aug_methods=config['aug_methods'], augvalid=config['augvalid'],
                include_bodyparts=config['include_bodyparts'], std=config['std'],
                background_free=config['background_free'], black_background=config['black_background'],
                behavior_mode=config['behavior_mode'], social_distance=config['social_distance'],
                color_costar=config['color_costar'], out_folder=out_folder
            )
    else:
        if onfly:
            CA.train_combnet_onfly(
                data_path, model_path, out_path=out_path,
                dim_tconv=config['dim_tconv'], dim_conv=config['dim_conv'], channel=config['channel'],
                time_step=config['time_step'], level_tconv=config['level_tconv'], level_conv=config['level_conv'],
                include_bodyparts=config['include_bodyparts'], std=config['std'],
                background_free=config['background_free'], black_background=config['black_background'],
                behavior_mode=config['behavior_mode'], social_distance=config['social_distance'],
                color_costar=config['color_costar']
            )
        else:
            CA.train_combnet(
                data_path, model_path, out_path=out_path,
                dim_tconv=config['dim_tconv'], dim_conv=config['dim_conv'], channel=config['channel'],
                time_step=config['time_step'], level_tconv=config['level_tconv'], level_conv=config['level_conv'],
                aug_methods=config['aug_methods'], augvalid=config['augvalid'],
                include_bodyparts=config['include_bodyparts'], std=config['std'],
                background_free=config['background_free'], black_background=config['black_background'],
                behavior_mode=config['behavior_mode'], social_distance=config['social_distance'],
                color_costar=config['color_costar'], out_folder=out_folder
            )

    print("Categorizer training completed successfully.", file=sys.stdout)


def handle_train_detector(args):
    config = resolve_config(
        command_name="labgym-cli train detector",
        defaults=TRAIN_DETECTOR_DEFAULTS,
        allowed_keys=ALLOWED_TRAIN_DETECTOR_KEYS,
        required_keys=REQUIRED_TRAIN_DETECTOR_KEYS,
        config_path=args.config,
        cli_args_dict=vars(args)
    )

    path_to_annotation = config['path_to_annotation']
    path_to_trainingimages = config['path_to_trainingimages']
    model_path = config['model_path']

    if not os.path.exists(path_to_annotation):
        raise CLIConfigError(f"Annotation file not found: '{path_to_annotation}'")
    if not os.path.isfile(path_to_annotation):
        raise CLIConfigError(f"Annotation path must be a file: '{path_to_annotation}'")

    try:
        with open(path_to_annotation, 'r', encoding='utf-8') as f:
            anno_data = json.load(f)
    except Exception as e:
        raise CLIConfigError(f"Error reading annotation file '{path_to_annotation}': {e}")

    if not isinstance(anno_data, dict):
        raise CLIConfigError(f"Annotation file '{path_to_annotation}' must contain a JSON object.")

    if 'images' not in anno_data or not isinstance(anno_data['images'], list):
        raise CLIConfigError(
            f"Annotation file '{path_to_annotation}' must contain an 'images' list."
        )

    if 'annotations' not in anno_data or not isinstance(anno_data['annotations'], list):
        raise CLIConfigError(
            f"Annotation file '{path_to_annotation}' must contain an 'annotations' list."
        )

    if 'categories' not in anno_data or not isinstance(anno_data['categories'], list) or len(anno_data['categories']) == 0:
        raise CLIConfigError(
            f"Annotation file '{path_to_annotation}' must contain a non-empty 'categories' list."
        )

    has_positive_id = False
    for idx, cat in enumerate(anno_data['categories']):
        if not isinstance(cat, dict):
            raise CLIConfigError(
                f"Item {idx} in 'categories' of '{path_to_annotation}' must be a dictionary."
            )
        if 'id' not in cat or isinstance(cat['id'], bool) or not isinstance(cat['id'], int):
            raise CLIConfigError(
                f"Category item {idx} in '{path_to_annotation}' must have an integer 'id' (got {cat.get('id')!r})."
            )
        if 'name' not in cat or isinstance(cat['name'], bool) or not isinstance(cat['name'], str) or not cat['name'].strip():
            raise CLIConfigError(
                f"Category item {idx} in '{path_to_annotation}' must have a non-empty string 'name'."
            )
        if cat['id'] > 0:
            has_positive_id = True

    if not has_positive_id:
        raise CLIConfigError(
            f"Annotation file '{path_to_annotation}' must contain at least one category with 'id' > 0."
        )

    if not os.path.exists(path_to_trainingimages):
        raise CLIConfigError(f"Training images directory not found: '{path_to_trainingimages}'")
    if not os.path.isdir(path_to_trainingimages):
        raise CLIConfigError(f"Training images path must be a directory: '{path_to_trainingimages}'")

    if os.path.isfile(model_path):
        raise CLIConfigError(f"Model path must be a directory, not an existing file: '{model_path}'")

    if os.path.exists(model_path):
        raise CLIConfigError(
            f"Model directory already exists: '{model_path}'. Detector training requires a path to a new directory."
        )

    parent_dir = os.path.dirname(model_path)
    if parent_dir and os.path.isfile(parent_dir):
        raise CLIConfigError(f"Parent path of model directory is a file: '{parent_dir}'")

    print(
        f"Starting headless Detector training (Iterations: {config['iteration_num']}, Inference Size: {config['inference_size']})...",
        file=sys.stdout
    )

    from LabGym.detector import Detector
    DT = Detector()
    DT.train(
        path_to_annotation,
        path_to_trainingimages,
        model_path,
        config['iteration_num'],
        config['inference_size']
    )
    print("Detector training completed successfully.", file=sys.stdout)


def handle_test_categorizer(args):
    config = resolve_config(
        command_name="labgym-cli test categorizer",
        defaults=TEST_CATEGORIZER_DEFAULTS,
        allowed_keys=ALLOWED_TEST_CATEGORIZER_KEYS,
        required_keys=REQUIRED_TEST_CATEGORIZER_KEYS,
        config_path=args.config,
        cli_args_dict=vars(args)
    )

    groundtruth_path = config['groundtruth_path']
    model_path = config['model_path']
    result_path = config['result_path']

    if not os.path.exists(groundtruth_path):
        raise CLIConfigError(f"Ground-truth dataset directory not found: '{groundtruth_path}'")
    if not os.path.isdir(groundtruth_path):
        raise CLIConfigError(f"Ground-truth dataset path must be a directory: '{groundtruth_path}'")
    if not os.path.exists(model_path):
        raise CLIConfigError(f"Categorizer model directory not found: '{model_path}'")
    if not os.path.isdir(model_path):
        raise CLIConfigError(f"Categorizer model path must be a directory: '{model_path}'")
    param_path = os.path.join(model_path, 'model_parameters.txt')
    if not os.path.isfile(param_path):
        raise CLIConfigError(
            f"Categorizer model parameters file not found in '{model_path}'. Expected 'model_parameters.txt'."
        )

    import pandas as pd
    try:
        parameters = pd.read_csv(param_path)
    except Exception as e:
        raise CLIConfigError(f"Error reading Categorizer model parameters in '{param_path}': {e}")

    required_cat_test_fields = ['classnames', 'time_step', 'network', 'inner_code', 'background_free']
    for field in required_cat_test_fields:
        if field not in parameters or len(parameters[field]) == 0 or pd.isna(parameters[field][0]):
            raise CLIConfigError(
                f"Malformed Categorizer model parameters in '{param_path}': missing required field '{field}'."
            )

    classnames = [str(x) for x in list(parameters['classnames']) if pd.notna(x)]
    if not classnames:
        raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'classnames' is empty.")

    if result_path:
        os.makedirs(result_path, exist_ok=True)

    print(f"Starting headless Categorizer testing on '{groundtruth_path}'...", file=sys.stdout)
    from LabGym.categorizer import Categorizers
    CA = Categorizers()
    CA.test_categorizer(groundtruth_path, model_path, result_path=result_path)
    print("Categorizer testing completed successfully.", file=sys.stdout)


def handle_test_detector(args):
    config = resolve_config(
        command_name="labgym-cli test detector",
        defaults=TEST_DETECTOR_DEFAULTS,
        allowed_keys=ALLOWED_TEST_DETECTOR_KEYS,
        required_keys=REQUIRED_TEST_DETECTOR_KEYS,
        config_path=args.config,
        cli_args_dict=vars(args)
    )

    path_to_annotation = config['path_to_annotation']
    path_to_testingimages = config['path_to_testingimages']
    model_path = config['model_path']
    result_path = config['result_path']

    if not os.path.exists(path_to_annotation):
        raise CLIConfigError(f"Annotation file not found: '{path_to_annotation}'")
    if not os.path.isfile(path_to_annotation):
        raise CLIConfigError(f"Annotation path must be a file: '{path_to_annotation}'")
    if not os.path.exists(path_to_testingimages):
        raise CLIConfigError(f"Testing images directory not found: '{path_to_testingimages}'")
    if not os.path.isdir(path_to_testingimages):
        raise CLIConfigError(f"Testing images path must be a directory: '{path_to_testingimages}'")
    if not os.path.exists(model_path):
        raise CLIConfigError(f"Detector model directory not found: '{model_path}'")
    if not os.path.isdir(model_path):
        raise CLIConfigError(f"Detector model path must be a directory: '{model_path}'")

    for text_file in ['model_parameters.txt', 'config.yaml']:
        fpath = os.path.join(model_path, text_file)
        if not os.path.isfile(fpath):
            raise CLIConfigError(
                f"Detector model directory '{model_path}' is missing required file: '{text_file}'."
            )
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                f.read()
        except Exception as e:
            raise CLIConfigError(f"Error reading Detector model file '{fpath}': {e}")

    weights_file = os.path.join(model_path, 'model_final.pth')
    if not os.path.isfile(weights_file):
        raise CLIConfigError(
            f"Detector model directory '{model_path}' is missing required file: 'model_final.pth'."
        )
    try:
        with open(weights_file, 'rb') as f:
            f.read(1024)
    except Exception as e:
        raise CLIConfigError(f"Error reading Detector model file '{weights_file}': {e}")

    os.makedirs(result_path, exist_ok=True)

    print(f"Starting headless Detector testing on '{path_to_testingimages}'...", file=sys.stdout)
    from LabGym.detector import Detector
    DT = Detector()
    DT.test(
        path_to_annotation,
        path_to_testingimages,
        model_path,
        result_path
    )
    print("Detector testing completed successfully.", file=sys.stdout)


def load_categorizer_metadata(path_to_categorizer):
    if not os.path.isdir(path_to_categorizer):
        raise CLIConfigError(f"Categorizer model directory not found: '{path_to_categorizer}'")

    param_path = os.path.join(path_to_categorizer, 'model_parameters.txt')
    if not os.path.isfile(param_path):
        raise CLIConfigError(
            f"Categorizer model parameters file not found in '{path_to_categorizer}'. Expected 'model_parameters.txt'."
        )

    import pandas as pd
    import matplotlib as mpl

    try:
        parameters = pd.read_csv(param_path)
    except Exception as e:
        raise CLIConfigError(f"Error reading Categorizer parameters in '{param_path}': {e}")

    required_cols = [
        'classnames', 'channel', 'time_step', 'network',
        'inner_code', 'std', 'background_free', 'black_background',
        'behavior_kind', 'social_distance'
    ]
    for col in required_cols:
        if col not in parameters or len(parameters[col]) == 0 or pd.isna(parameters[col][0]):
            raise CLIConfigError(
                f"Malformed Categorizer model parameters in '{param_path}': missing required field '{col}'."
            )

    classnames = [str(x) for x in list(parameters['classnames']) if pd.notna(x)]
    if not classnames:
        raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'classnames' is empty.")

    try:
        categorizer_type = int(parameters['network'][0])
    except (ValueError, TypeError):
        raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'network' must be an integer.")

    if categorizer_type not in (0, 1, 2):
        raise CLIConfigError(
            f"Malformed Categorizer model parameters in '{param_path}': invalid 'network' value {categorizer_type} (expected 0, 1, or 2)."
        )

    if categorizer_type in (0, 2):
        if 'dim_conv' not in parameters or pd.isna(parameters['dim_conv'][0]):
            raise CLIConfigError(
                f"Malformed Categorizer model parameters in '{param_path}': missing required architecture field 'dim_conv'."
            )
        try:
            dim_conv = int(parameters['dim_conv'][0])
        except (ValueError, TypeError):
            raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'dim_conv' must be an integer.")
    else:
        dim_conv = int(parameters['dim_conv'][0]) if ('dim_conv' in parameters and pd.notna(parameters['dim_conv'][0])) else 0

    if categorizer_type in (1, 2):
        if 'dim_tconv' not in parameters or pd.isna(parameters['dim_tconv'][0]):
            raise CLIConfigError(
                f"Malformed Categorizer model parameters in '{param_path}': missing required architecture field 'dim_tconv'."
            )
        try:
            dim_tconv = int(parameters['dim_tconv'][0])
        except (ValueError, TypeError):
            raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'dim_tconv' must be an integer.")
        if 'color_code' not in parameters or pd.isna(parameters['color_code'][0]):
            raise CLIConfigError(
                f"Malformed Categorizer model parameters in '{param_path}': missing required field 'color_code'."
            )
        try:
            color_costar = (int(parameters['color_code'][0]) == 0)
        except (ValueError, TypeError):
            raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'color_code' must be an integer.")
    else:
        dim_tconv = int(parameters['dim_tconv'][0]) if ('dim_tconv' in parameters and pd.notna(parameters['dim_tconv'][0])) else 0
        if 'color_code' in parameters and pd.notna(parameters['color_code'][0]):
            try:
                color_costar = (int(parameters['color_code'][0]) == 0)
            except (ValueError, TypeError):
                raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': 'color_code' must be an integer.")
        else:
            color_costar = False

    try:
        channel = int(parameters['channel'][0])
        length = int(parameters['time_step'][0])
        inner_code = int(parameters['inner_code'][0])
        std = int(parameters['std'][0])
        background_free_val = int(parameters['background_free'][0])
        black_background_val = int(parameters['black_background'][0])
        behavior_mode = int(parameters['behavior_kind'][0])
        social_distance = float(parameters['social_distance'][0])
    except (ValueError, TypeError) as e:
        raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': invalid numeric value ({e}).")

    if channel not in (1, 3):
        raise CLIConfigError(f"Malformed Categorizer model parameters in '{param_path}': invalid channel {channel} (expected 1 or 3).")

    if length < 3 and behavior_mode < 3:
        length = 3

    animation_analyzer = (categorizer_type == 2)
    include_bodyparts = (inner_code == 0)
    background_free = (background_free_val == 0)
    black_background = not (black_background_val == 1)
    if behavior_mode == 2 and social_distance == 0:
        social_distance = float('inf')

    complete_colors = list(mpl.colors.cnames.values())
    colors = [['#ffffff', c] for c in complete_colors]
    behaviornames_and_colors = {}
    for behavior_name in classnames:
        idx = classnames.index(behavior_name)
        if idx < len(colors):
            behaviornames_and_colors[behavior_name] = colors[idx]
        else:
            behaviornames_and_colors[behavior_name] = ['#ffffff', '#ffffff']

    return {
        'classnames': classnames,
        'dim_conv': dim_conv,
        'dim_tconv': dim_tconv,
        'channel': channel,
        'length': length,
        'animation_analyzer': animation_analyzer,
        'include_bodyparts': include_bodyparts,
        'std': std,
        'background_free': background_free,
        'black_background': black_background,
        'behavior_mode': behavior_mode,
        'social_distance': social_distance,
        'color_costar': color_costar,
        'behaviornames_and_colors': behaviornames_and_colors,
    }


def load_detector_metadata(path_to_detector):
    if not os.path.isdir(path_to_detector):
        raise CLIConfigError(f"Detector model directory not found: '{path_to_detector}'")

    param_path = os.path.join(path_to_detector, 'model_parameters.txt')
    if not os.path.isfile(param_path):
        raise CLIConfigError(
            f"Detector model parameters file not found in '{path_to_detector}'. Expected 'model_parameters.txt'."
        )

    try:
        with open(param_path, 'r', encoding='utf-8') as f:
            detector_dict = json.load(f)
    except Exception as e:
        raise CLIConfigError(f"Error reading Detector model parameters in '{param_path}': {e}")

    if not isinstance(detector_dict, dict):
        raise CLIConfigError(f"Malformed Detector model parameters in '{param_path}': must be a JSON object.")

    if 'animal_mapping' not in detector_dict:
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': missing required field 'animal_mapping'."
        )
    animal_mapping = detector_dict['animal_mapping']
    if not isinstance(animal_mapping, dict) or not animal_mapping:
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': 'animal_mapping' must be a non-empty dictionary."
        )

    if 'inferencing_framesize' not in detector_dict:
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': missing required field 'inferencing_framesize'."
        )
    val = detector_dict['inferencing_framesize']
    if isinstance(val, bool):
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': 'inferencing_framesize' cannot be a boolean."
        )
    try:
        inferencing_framesize = int(val)
    except (ValueError, TypeError):
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': 'inferencing_framesize' must be an integer."
        )
    if inferencing_framesize <= 0:
        raise CLIConfigError(
            f"Malformed Detector model parameters in '{param_path}': 'inferencing_framesize' must be a positive integer."
        )

    return {
        'animal_mapping': animal_mapping,
        'inferencing_framesize': inferencing_framesize,
    }


def resolve_media_paths(paths, behavior_mode):
    if behavior_mode == 3:
        valid_exts = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
    else:
        valid_exts = {'.avi', '.mpg', '.mpeg', '.wmv', '.mp4', '.mkv', '.m4v', '.mov'}

    media_type = "image" if behavior_mode == 3 else "video"
    resolved = []
    for p in paths:
        if os.path.isdir(p):
            found = [
                os.path.join(p, f) for f in os.listdir(p)
                if os.path.splitext(f)[1].lower() in valid_exts
            ]
            found.sort()
            if not found:
                raise CLIConfigError(f"No valid {media_type} files found in directory: '{p}'")
            resolved.extend(found)
        elif os.path.isfile(p):
            ext = os.path.splitext(p)[1].lower()
            if ext not in valid_exts:
                supported = ", ".join(sorted(valid_exts))
                raise CLIConfigError(
                    f"Unsupported {media_type} file format: '{p}'. Supported extensions: {supported}"
                )
            resolved.append(p)
        else:
            raise CLIConfigError(f"Specified media path does not exist: '{p}'")

    deduped = list(dict.fromkeys(resolved))
    if not deduped:
        raise CLIConfigError(f"No valid {media_type} files found for inference.")
    return deduped


def rollup_behavior_summaries(result_path, behaviornames_and_colors, use_detector=False, animal_kinds=None):
    """Aggregate per-video behavior summaries at the result root (GUI parity)."""
    import pandas as pd

    folders = [i for i in os.listdir(result_path) if os.path.isdir(os.path.join(result_path, i))]
    folders.sort()
    if not use_detector:
        for behavior_name in behaviornames_and_colors:
            all_summary = []
            for folder in folders:
                individual_summary = os.path.join(result_path, folder, behavior_name, 'all_summary.xlsx')
                if os.path.exists(individual_summary):
                    all_summary.append(pd.read_excel(individual_summary))
            if len(all_summary) >= 1:
                all_summary = pd.concat(all_summary, ignore_index=True)
                all_summary.to_excel(
                    os.path.join(result_path, behavior_name + '_summary.xlsx'),
                    float_format='%.2f',
                    index_label='ID/parameter'
                )
    else:
        for animal_name in animal_kinds:
            for behavior_name in behaviornames_and_colors:
                all_summary = []
                for folder in folders:
                    individual_summary = os.path.join(
                        result_path, folder, behavior_name, animal_name + '_all_summary.xlsx'
                    )
                    if os.path.exists(individual_summary):
                        all_summary.append(pd.read_excel(individual_summary))
                if len(all_summary) >= 1:
                    all_summary = pd.concat(all_summary, ignore_index=True)
                    all_summary.to_excel(
                        os.path.join(result_path, animal_name + '_' + behavior_name + '_summary.xlsx'),
                        float_format='%.2f',
                        index_label='ID/parameter'
                    )


def handle_infer(args):
    config = resolve_config(
        command_name="labgym-cli infer",
        defaults=INFER_DEFAULTS,
        allowed_keys=ALLOWED_INFER_KEYS,
        required_keys=REQUIRED_INFER_KEYS,
        config_path=args.config,
        cli_args_dict=vars(args)
    )

    path_to_categorizer = config['path_to_categorizer']
    path_to_detector = config['path_to_detector']
    use_detector = config['use_detector']
    result_path = config['result_path']

    if use_detector and not path_to_detector:
        raise CLIConfigError("Option '--use-detector' requires '--path-to-detector' to be specified.")

    if path_to_categorizer:
        cat_meta = load_categorizer_metadata(path_to_categorizer)
    else:
        cat_meta = {
            'classnames': [],
            'dim_conv': 64,
            'dim_tconv': 32,
            'channel': 1,
            'length': 15,
            'animation_analyzer': False,
            'include_bodyparts': True,
            'std': 0,
            'background_free': True,
            'black_background': True,
            'behavior_mode': 0,
            'social_distance': 0.0,
            'color_costar': False,
            'behaviornames_and_colors': {},
        }

    behavior_mode = cat_meta['behavior_mode']

    if path_to_detector:
        det_meta = load_detector_metadata(path_to_detector)
        if config['animal_kinds'] == ['animal'] and det_meta['animal_mapping']:
            animal_kinds = [str(v) for v in det_meta['animal_mapping'].values()]
        else:
            animal_kinds = list(config['animal_kinds'])
    else:
        animal_kinds = list(config['animal_kinds'])

    animal_to_include = list(config['animal_to_include']) if config['animal_to_include'] else list(animal_kinds)

    behavior_to_include = list(config['behavior_to_include'])
    if not path_to_categorizer:
        behavior_to_include = []
    elif not behavior_to_include or behavior_to_include == ['all']:
        behavior_to_include = list(cat_meta['behaviornames_and_colors'].keys())
    else:
        for b in behavior_to_include:
            if b not in cat_meta['classnames']:
                raise CLIConfigError(
                    f"Behavior '{b}' not found in Categorizer model. Available: {cat_meta['classnames']}"
                )

    input_paths = resolve_media_paths(config['path_to_videos'], behavior_mode)

    if behavior_mode == 3 and (not path_to_categorizer or not path_to_detector):
        raise CLIConfigError("Static image inference (behavior_mode=3) requires both Categorizer and Detector.")

    os.makedirs(result_path, exist_ok=True)
    print(f"Starting headless behavioral inference on {len(input_paths)} file(s)...", file=sys.stdout)

    if behavior_mode == 3:
        from LabGym.analyzebehavior_dt import AnalyzeAnimalDetector
        AAD = AnalyzeAnimalDetector()
        detector_batch = max(1, config['detector_batch'])
        AAD.analyze_images_individuals(
            path_to_detector, input_paths, result_path, animal_kinds,
            path_to_categorizer=path_to_categorizer, generate=False,
            animal_to_include=animal_to_include, behavior_to_include=behavior_to_include,
            names_and_colors=cat_meta['behaviornames_and_colors'], imagewidth=config['framewidth'],
            dim_conv=cat_meta['dim_conv'], channel=cat_meta['channel'],
            detection_threshold=config['detection_threshold'], uncertain=config['uncertain'],
            background_free=cat_meta['background_free'], black_background=cat_meta['black_background'],
            social_distance=0
        )
    else:
        import pandas as pd
        from LabGym.tools import plot_events

        all_events = {}
        event_data = {}
        all_time = []

        if use_detector:
            for animal_name in animal_kinds:
                all_events[animal_name] = {}
            detector_batch = max(1, config['detector_batch'])

        categorize_behavior = (path_to_categorizer is not None)

        for video_path in input_paths:
            filename = os.path.splitext(os.path.basename(video_path))[0].split('_')
            animal_num = config['animal_number']
            t_val = config['t']
            ex_start_val = config['ex_start']
            ex_end_val = config['ex_end']

            if config['decode_animalnumber']:
                if use_detector:
                    animal_num = {}
                    number = [x[1:] for x in filename if len(x) > 1 and x[0] == 'n']
                    for a, animal_name in enumerate(animal_kinds):
                        if a < len(number) and number[a].isdigit():
                            animal_num[animal_name] = int(number[a])
                        else:
                            animal_num[animal_name] = 1
                else:
                    for x in filename:
                        if len(x) > 1 and x[0] == 'n' and x[1:].isdigit():
                            animal_num = int(x[1:])
            elif animal_num is None:
                if use_detector:
                    animal_num = {animal_name: 1 for animal_name in animal_kinds}
                else:
                    animal_num = 1
            elif isinstance(animal_num, int):
                if use_detector:
                    animal_num = {animal_name: animal_num for animal_name in animal_kinds}
            elif isinstance(animal_num, dict):
                animal_num = {animal_name: int(animal_num.get(animal_name, 1)) for animal_name in animal_kinds}

            if config['decode_t']:
                for x in filename:
                    if len(x) > 1 and x[0] == 'b':
                        try:
                            t_val = float(x[1:])
                        except ValueError:
                            pass

            if config['decode_extraction']:
                for x in filename:
                    if len(x) > 2:
                        if x[:2] == 'xs' and x[2:].isdigit():
                            ex_start_val = int(x[2:])
                        if x[:2] == 'xe' and x[2:].isdigit():
                            ex_end_val = int(x[2:])

            if not use_detector:
                from LabGym.analyzebehavior import AnalyzeAnimal
                AA = AnalyzeAnimal()
                AA.prepare_analysis(
                    video_path, result_path, animal_num, delta=config['delta'],
                    names_and_colors=cat_meta['behaviornames_and_colors'], framewidth=config['framewidth'],
                    stable_illumination=config['stable_illumination'], dim_tconv=cat_meta['dim_tconv'],
                    dim_conv=cat_meta['dim_conv'], channel=cat_meta['channel'],
                    include_bodyparts=cat_meta['include_bodyparts'], std=cat_meta['std'],
                    categorize_behavior=categorize_behavior, animation_analyzer=cat_meta['animation_analyzer'],
                    path_background=config['background_path'], autofind_t=config['autofind_t'],
                    t=t_val, duration=config['duration'], ex_start=ex_start_val, ex_end=ex_end_val,
                    length=cat_meta['length'], animal_vs_bg=config['animal_vs_bg']
                )
                if behavior_mode == 0:
                    AA.acquire_information(background_free=cat_meta['background_free'], black_background=cat_meta['black_background'])
                    AA.craft_data()
                    interact_all = False
                else:
                    AA.acquire_information_interact_basic(background_free=cat_meta['background_free'], black_background=cat_meta['black_background'])
                    interact_all = True

                if path_to_categorizer is not None:
                    AA.categorize_behaviors(path_to_categorizer, uncertain=config['uncertain'], min_length=config['min_length'])

                AA.annotate_video(config['ID_colors'], behavior_to_include, show_legend=config['show_legend'], interact_all=interact_all)
                AA.export_results(normalize_distance=config['normalize_distance'], parameter_to_analyze=config['parameter_to_analyze'])

                if path_to_categorizer is not None:
                    for n in AA.event_probability:
                        all_events[len(all_events)] = AA.event_probability[n]
                    if len(all_time) < len(AA.all_time):
                        all_time = AA.all_time
            else:
                from LabGym.analyzebehavior_dt import AnalyzeAnimalDetector
                AAD = AnalyzeAnimalDetector()
                AAD.prepare_analysis(
                    path_to_detector, video_path, result_path, animal_num, animal_kinds, behavior_mode,
                    names_and_colors=cat_meta['behaviornames_and_colors'], framewidth=config['framewidth'],
                    dim_tconv=cat_meta['dim_tconv'], dim_conv=cat_meta['dim_conv'], channel=cat_meta['channel'],
                    include_bodyparts=cat_meta['include_bodyparts'], std=cat_meta['std'],
                    categorize_behavior=categorize_behavior, animation_analyzer=cat_meta['animation_analyzer'],
                    t=t_val, duration=config['duration'], length=cat_meta['length'], social_distance=cat_meta['social_distance']
                )
                if behavior_mode == 1:
                    AAD.acquire_information_interact_basic(
                        batch_size=detector_batch, background_free=cat_meta['background_free'], black_background=cat_meta['black_background']
                    )
                else:
                    AAD.acquire_information(
                        batch_size=detector_batch, background_free=cat_meta['background_free'], black_background=cat_meta['black_background'],
                        color_costar=cat_meta['color_costar']
                    )
                if behavior_mode != 1:
                    AAD.craft_data()

                if path_to_categorizer is not None:
                    AAD.categorize_behaviors(path_to_categorizer, uncertain=config['uncertain'], min_length=config['min_length'])

                if config['correct_ID']:
                    AAD.correct_identity(config['specific_behaviors'])

                AAD.annotate_video(animal_to_include, config['ID_colors'], behavior_to_include, show_legend=config['show_legend'])
                AAD.export_results(normalize_distance=config['normalize_distance'], parameter_to_analyze=config['parameter_to_analyze'])

                if path_to_categorizer is not None:
                    for animal_name in animal_kinds:
                        if animal_name in AAD.event_probability:
                            for n in AAD.event_probability[animal_name]:
                                all_events[animal_name][len(all_events[animal_name])] = AAD.event_probability[animal_name][n]
                    if len(all_time) < len(AAD.all_time):
                        all_time = AAD.all_time

        if path_to_categorizer is not None and all_time:
            max_length = len(all_time)
            if not use_detector:
                for n in all_events:
                    event_data[len(event_data)] = all_events[n] + [['NA', -1]] * (max_length - len(all_events[n]))
                if event_data:
                    all_events_df = pd.DataFrame(event_data, index=all_time)
                    all_events_df.to_excel(os.path.join(result_path, 'all_events.xlsx'), float_format='%.2f', index_label='time/ID')
                    plot_events(result_path, event_data, all_time, cat_meta['behaviornames_and_colors'], behavior_to_include, width=0, height=0)
            else:
                for animal_name in animal_to_include:
                    if animal_name in all_events:
                        for n in all_events[animal_name]:
                            event_data[len(event_data)] = all_events[animal_name][n] + [['NA', -1]] * (max_length - len(all_events[animal_name][n]))
                        event_data[len(event_data)] = [['NA', -1]] * max_length
                if event_data:
                    del event_data[len(event_data) - 1]
                    all_events_df = pd.DataFrame(event_data, index=all_time)
                    all_events_df.to_excel(os.path.join(result_path, 'all_events.xlsx'), float_format='%.2f', index_label='time/ID')
                    plot_events(result_path, event_data, all_time, cat_meta['behaviornames_and_colors'], behavior_to_include, width=0, height=0)

        if path_to_categorizer is not None:
            rollup_behavior_summaries(
                result_path,
                cat_meta['behaviornames_and_colors'],
                use_detector=use_detector,
                animal_kinds=animal_kinds,
            )

    print("Inference completed successfully.", file=sys.stdout)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()

    if len(argv) == 0:
        parser.print_help(file=sys.stdout)
        return 0

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return e.code

    if args.action in ['train', 'test'] and getattr(args, 'target', None) is None:
        print(f"Error: 'labgym-cli {args.action}' requires a target (e.g. 'categorizer' or 'detector').", file=sys.stderr)
        return 2

    if not hasattr(args, 'func'):
        parser.print_help(file=sys.stderr)
        return 2

    try:
        args.func(args)
        return 0
    except CLIConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except NotImplementedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Execution Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
