# LabGym Command Line Interface (CLI) Guide

This guide details the command syntax, configuration contract, parameter precedence, and options for the headless command-line interface (CLI) in LabGym.

**Entry points:** `LabGym` remains the desktop GUI command. `labgym-cli` is the headless command-line interface for training, testing, and inference. Use `LabGym` to open the graphical application; use `labgym-cli` with a subcommand for scripted and HPC workflows.

---

## 1. Architecture & Subcommand Structure

The LabGym CLI is organized into nested subcommands reflecting canonical actions and targets:

* `labgym-cli train categorizer`
* `labgym-cli train detector`
* `labgym-cli test categorizer`
* `labgym-cli test detector`
* `labgym-cli infer`

Launch the desktop GUI with the separate `LabGym` command:
```bash
LabGym
```

### 3-Tier Precedence Hierarchy
Workflows can be driven purely by inline CLI flags, by a YAML workflow file (`-c` / `--config`), or a combination:
$$\text{Built-in Defaults} \quad\longrightarrow\quad \text{Workflow YAML } (\texttt{-c} \text{ / } \texttt{--config}) \quad\longrightarrow\quad \text{Inline CLI Overrides}$$

* Inline flags default to `None` so omitted flags never override YAML settings.
* Paired Boolean flags (e.g. `--use-detector` and `--no-use-detector`) allow explicit override in either direction while preserving YAML defaults when omitted.
* CLI options use kebab-case (`--data-path`), mapping directly to snake_case (`data_path`) in YAML and Python.

### Workflow Configuration vs. Persistent Application Preferences
The `--config` / `-c` flag specifies a **per-command workflow (job) configuration file** written in YAML.

* **Workflow Configuration (`--config`)**: A job-specific, hermetic YAML document defining the exact parameters, inputs, models, and outputs for a single headless execution. It is designed for reproducible scripted runs, automated analysis pipelines, and cluster submissions.
* **Persistent Application Preferences**: LabGym GUI settings or system-level preferences stored across sessions are **not** loaded, modified, or referenced by the headless CLI. The CLI operates completely independently of persistent GUI state, relying solely on built-in command defaults, the specified workflow YAML file, and explicit command-line flags.

---

## 2. Command Reference

### `labgym-cli train categorizer`
Headless training for behavior classification sub-networks (Pattern Recognizer, Animation Analyzer, or CombNet).

* **Syntax**:
  ```bash
  labgym-cli train categorizer --config <file.yaml> [inline-overrides]
  ```

* **Required Parameters**:
  * `--data-path` (`data_path`): Path to training examples dataset directory
  * `--model-path` (`model_path`): Destination directory for the trained model

* **Key Options**:
  * `--network-type` (`network_type`): `combnet` (default), `pattern_recognizer`, `animation_analyzer`, or `combined_network`
  * `--out-path` (`out_path`): Directory for training logs and reports
  * `--out-folder` (`out_folder`): Cache directory for prepared frames
  * `--dim-conv` (`dim_conv`): Input size for Pattern Recognizer (default: 64)
  * `--dim-tconv` (`dim_tconv`): Input size for Animation Analyzer (default: 32)
  * `--channel` (`channel`): Image channels, 1 or 3 (default: 1)
  * `--time-step` (`time_step`): Frames per behavioral sequence (default: 15)
  * `--level-conv` (`level_conv`): Complexity level for Pattern Recognizer 1–5 (default: 2)
  * `--level-tconv` (`level_tconv`): Complexity level for Animation Analyzer 1–5 (default: 1)
  * `--aug-methods` (`aug_methods`): List of augmentation methods (e.g. `"random rotation"`, `"horizontal flipping"`)
  * `--augvalid` / `--no-augvalid`: Validate augmentation data (default: True)
  * `--include-bodyparts` / `--no-include-bodyparts`: Include body part contours (default: True)
  * `--std` (`std`): Standard deviation threshold parameter for body parts (default: 0.0)
  * `--background-free` / `--no-background-free`: Exclude background from calculations (default: True)
  * `--black-background` / `--no-black-background`: Use black background (default: True)
  * `--behavior-mode` (`behavior_mode`): Mode 0 (standard), 1 (basic interactive), 2 (advanced interactive), 3 (static images)
  * `--social-distance` (`social_distance`): Social interaction distance threshold (default: 0.0)
  * `--color-costar` / `--no-color-costar`: Render supporting actors in RGB scale (default: False)
  * `--training-onfly` / `--no-training-onfly`: Train on the fly without pre-caching frames (default: False)

### `labgym-cli train detector`
Headless training for Detectron2 object detection models.

* **Syntax**:
  ```bash
  labgym-cli train detector --config <file.yaml> [inline-overrides]
  ```

* **Required Parameters**:
  * `--path-to-annotation` (`path_to_annotation`): Path to COCO JSON annotation file
  * `--path-to-trainingimages` (`path_to_trainingimages`): Directory containing training images
  * `--model-path` (`model_path`): Destination directory for the trained detector

* **Key Options**:
  * `--iteration-num` (`iteration_num`): Number of training iterations (default: 200)
  * `--inference-size` (`inference_size`): Image frame resizing dimension for inference (default: 480)

### `labgym-cli test categorizer`
Headless evaluation of a trained behavior classifier against ground-truth data.

* **Syntax**:
  ```bash
  labgym-cli test categorizer --config <file.yaml> [inline-overrides]
  ```

* **Required Parameters**:
  * `--groundtruth-path` (`groundtruth_path`): Path to ground-truth testing dataset folder
  * `--model-path` (`model_path`): Path to trained Categorizer directory

* **Key Options**:
  * `--result-path` (`result_path`): Directory to write evaluation metrics and confusion matrices

### `labgym-cli test detector`
Headless evaluation of a trained object detector against annotated testing images.

* **Syntax**:
  ```bash
  labgym-cli test detector --config <file.yaml> [inline-overrides]
  ```

* **Required Parameters**:
  * `--path-to-annotation` (`path_to_annotation`): Path to COCO JSON annotation file
  * `--path-to-testingimages` (`path_to_testingimages`): Directory containing test images
  * `--model-path` (`model_path`): Path to trained Detector directory
  * `--result-path` (`result_path`): Directory to write detection test results

### `labgym-cli infer`
Headless animal tracking and behavior classification on videos or static images.

> **Model Metadata Inheritance**: Architecture hyperparameters (`dim_conv`, `dim_tconv`, `channel`, `time_step`) and preprocessing settings (`background_free`, `black_background`, `behavior_mode`, `social_distance`, `color_costar`) are authoritative inside the trained Categorizer model's `model_parameters.txt` and are inherited automatically during inference.

* **Syntax**:
  ```bash
  labgym-cli infer --config <file.yaml> [inline-overrides]
  ```

* **Required Parameters**:
  * `--path-to-videos` (`path_to_videos`): One or more video file paths or directories
  * `--result-path` (`result_path`): Directory to write tracking and classification results

* **Model Selection**:
  * `--path-to-categorizer` (`path_to_categorizer`): Path to trained Categorizer directory
  * `--path-to-detector` (`path_to_detector`): Path to trained Detector directory
  * `--use-detector` / `--no-use-detector`: Enable or disable detector-based tracking (default: False)

* **Analysis Options**:
  * `--framewidth` (`framewidth`): Target image resizing width in pixels
  * `--background-path` (`background_path`): Path to background reference image (for background subtraction)
  * `--delta` (`delta`): Delta trigger threshold (default: 10000.0)
  * `--animal-kinds` (`animal_kinds`): List of animal categories recognized by the detector
  * `--animal-to-include` (`animal_to_include`): Specific animals to include in output reports
  * `--behavior-to-include` (`behavior_to_include`): Behaviors to quantify (default: `['all']`)
  * `--detector-batch` (`detector_batch`): Batch size for detector processing (default: 1)
  * `--detection-threshold` (`detection_threshold`): Detection confidence threshold 0.0–1.0 (default: 0.0)
  * `--animal-number` (`animal_number`): Total animal count (positive integer) for all inference modes, or animal-kind-to-count mapping (e.g. `{"mouse": 2, "fly": 1}`) when detector inference is enabled (`--use-detector` / `use_detector: true`). Structured mappings are rejected without detector inference.
  * `--decode-animalnumber` / `--no-decode-animalnumber`: Extract animal counts from video filenames
  * `--autofind-t` / `--no-autofind-t`: Automatically detect optical stimulation trigger start time (default: False)
  * `--t` (`t`): Analysis start offset in seconds (default: 0.0)
  * `--duration` (`duration`): Analysis duration in seconds (default: 0.0 = full video)
  * `--decode-t` / `--no-decode-t`: Extract start time from video filenames
  * `--ex-start` (`ex_start`): Extraction start frame number (default: 0)
  * `--ex-end` (`ex_end`): Extraction end frame number
  * `--decode-extraction` / `--no-decode-extraction`: Extract start/end frames from filenames
  * `--stable-illumination` / `--no-stable-illumination`: Illumination stability flag (default: True)
  * `--ID-colors` (`ID_colors`): List of RGB color tuples for animal IDs
  * `--parameter-to-analyze` (`parameter_to_analyze`): Kinematic parameters to quantify
  * `--uncertain` (`uncertain`): Probability difference gap for uncertainty threshold (default: 0.0)
  * `--min-length` (`min_length`): Minimum behavior duration in frames
  * `--show-legend` / `--no-show-legend`: Render behavior legends on output videos (default: True)
  * `--normalize-distance` / `--no-normalize-distance`: Normalize distances by contour size (default: True)
  * `--correct-id` / `--no-correct-id`: Apply ID correction heuristics (default: False)
  * `--specific-behaviors` (`specific_behaviors`): Custom behavior definition mapping

---

## 3. Configuration YAML Examples

### Categorizer Training (`train_categorizer.yaml`)
```yaml
# labgym-cli train categorizer -c train_categorizer.yaml
data_path: "~/data/behavior_examples"
model_path: "~/models/categorizer_combnet"
network_type: "combnet"
out_path: "~/logs/categorizer_training"

# Architecture dimensions
dim_conv: 64
dim_tconv: 32
channel: 1
time_step: 15
level_conv: 2
level_tconv: 1

# Preprocessing & Augmentation
training_onfly: false
augvalid: true
include_bodyparts: true
std: 0.0
background_free: true
black_background: true
behavior_mode: 0
social_distance: 0.0
```

### Detector Training (`train_detector.yaml`)
```yaml
# labgym-cli train detector -c train_detector.yaml
path_to_annotation: "~/data/annotations/train_coco.json"
path_to_trainingimages: "~/data/training_images"
model_path: "~/models/detector_mouse"
iteration_num: 1000
inference_size: 480
```

### Model Evaluation (`test_categorizer.yaml`)
```yaml
# labgym-cli test categorizer -c test_categorizer.yaml
groundtruth_path: "~/data/groundtruth_examples"
model_path: "~/models/categorizer_combnet"
result_path: "~/results/categorizer_eval"
```

### Detector Evaluation (`test_detector.yaml`)
```yaml
# labgym-cli test detector -c test_detector.yaml
path_to_annotation: "~/data/annotations/test_coco.json"
path_to_testingimages: "~/data/test_images"
model_path: "~/models/detector_mouse"
result_path: "~/results/detector_eval"
```

### Behavioral Inference (`infer.yaml`)
```yaml
# labgym-cli infer -c infer.yaml
path_to_videos:
  - "~/videos/session_1.mp4"
  - "~/videos/session_2.mp4"
result_path: "~/results/inference_run_1"

# Trained models
path_to_categorizer: "~/models/categorizer_combnet"
path_to_detector: "~/models/detector_mouse"
use_detector: true

# Run parameters
detector_batch: 2
animal_kinds:
  - "mouse"
duration: 120.0
show_legend: true
normalize_distance: true
```

---

## 4. High-Performance Computing (SLURM) Example

Below is an example job script for submitting a headless training run on an HPC cluster:

```bash
#!/bin/bash
#SBATCH --job-name=labgym_train
#SBATCH --output=logs/labgym_%j.out
#SBATCH --error=logs/labgym_%j.err
#SBATCH --time=04:00:00
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G

module load python/3.10
source ~/envs/labgym/bin/activate

labgym-cli train categorizer \
  --config train_categorizer.yaml \
  --data-path ~/data/behavior_dataset \
  --model-path ~/models/combnet_run \
  --level-conv 3
```

---

## 5. Exit Codes & Output Streams

The LabGym CLI adheres to POSIX process exit conventions:

* **Exit Code `0`**: Workflow succeeded.
* **Exit Code `1`**: Runtime scientific execution failure (e.g. underlying computation or model exception).
* **Exit Code `2`**: Configuration, syntax, or validation error (e.g. missing/unreadable YAML file, unknown keys, invalid types, out-of-range bounds, incompatible parameter combinations, or missing required arguments).
* **Standard Output (`stdout`)**: Informational human-readable workflow progress, success confirmations, and successful command help output (`--help` / `-h`).
* **Standard Error (`stderr`)**: Error messages, validation diagnostics, and error usage output (syntax or argument errors).
