import childespy
# Get all collections in the CHILDES database
collections = childespy.get_collections()

# Get all transcripts in the "childes" collection
transcripts = childespy.get_transcripts(collection = "Eng-na")
# Get all utterances where a specific child is the target
utterances = childespy.get_utterances(target_child="Adam")
print(utterances.head())











#!/usr/bin/env python3
"""
Writes a small sbatch script requesting 1 CPU + 1 GPU, then submits it
with sbatch. Run this from inside a Slurm job (e.g. launched by
launch_python.sh) or directly from a login node.
"""

import os
import subprocess

HOME = os.path.expanduser("~")
script_path = os.path.join(HOME, "gpu_job.sh")

script_contents = """#!/bin/bash
#SBATCH --account=def-yourpiname   # <-- replace with your CCDB account
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=1
#SBATCH --gpus-per-node=h100:1
#SBATCH --mem=4G
#SBATCH --job-name=gpu_test
#SBATCH --output=%x-%j.out

module load python/3.11
module load cuda

echo "Running on node: $(hostname)"
nvidia-smi
"""

with open(script_path, "w") as f:
    f.write(script_contents)

# sbatch scripts need to be executable to be safely run, though sbatch
# itself only requires read permission. Setting +x is good practice.
os.chmod(script_path, 0o755)

result = subprocess.run(
    ["sbatch", script_path],
    capture_output=True,
    text=True,
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)