import subprocess
from pathlib import Path

def write_sbatch_file(njobs,config):
        """
        Write a SLURM batch file for the given job index.

        :param baseconfig: The base configuration dictionary.
        :param job_index: The index of the job for which to write the batch file.
        """

        tpath = str(Path(config['config_folder'],'config_block_'))
        block_config_path = '"'+tpath+'${SLURM_ARRAY_TASK_ID}.yaml"'
        sbatch_content = (
            "#!/bin/bash\n"
            '#SBATCH --account=def-eporte2\n'
            '#SBATCH --gres=gpu:1\n'
            '#SBATCH --cpus-per-task=1\n'
            '#SBATCH --mem-per-cpu=3G\n'
            '#SBATCH --time=1:00:00\n'
            f"#SBATCH --array=0-{njobs}\n"
            '\n'
            'module load python/3.11.5\n'
            'source /home/mpelland/PREDICTENV/bin/activate\n'
            'export PYTHONPATH="/home/mpelland/links/projects/def-eporte2/mpelland/predictability/Code:$PYTHONPATH"\n'
            '\n'
            f"python /home/mpelland/links/projects/def-eporte2/mpelland/predictability/Code/remote_main.py {block_config_path} 'score'\n"
        )

        sbatch_filename = str(Path(config["config_folder"], "submit_scoring.sh"))
        with open(sbatch_filename, 'w') as sbatch_file:
            sbatch_file.write(sbatch_content)

def launch_sbatch_job(config,job_name):
    """
    Launch the SLURM batch job using the generated batch file.

    :param config: The configuration dictionary.
    """
    sbatch_filename = str(Path(config["config_folder"], job_name))
    result = subprocess.run(
        ["sbatch", sbatch_filename],
        capture_output=True,
        text=True
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    print("return code:", result.returncode)