import os
from Utilities.unpyc3_compiler import Unpyc3PythonCompiler


release_dir = os.path.join('Release', 'SimsTikTokMod')

# This function invocation will compile the files found within Scripts/s4cl_sample_mod_scripts, put them inside of a file named s4cl_sample_mod.ts4script, and it will finally place that ts4script file within <Project>/Release/S4CLSampleMod.
Unpyc3PythonCompiler.compile_mod(
    folder_path_to_output_ts4script_to=release_dir,
    names_of_modules_include=('sims_tik_tok_mod',),
    output_ts4script_name='sims_tik_tok_mod'
)
