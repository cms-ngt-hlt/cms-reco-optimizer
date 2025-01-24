<img width="1144" alt="Screenshot 2023-11-24 alle 09 46 27" src="https://github.com/cms-pixel-autotuning/CA-parameter-tuning/assets/16901146/5bee2244-9afc-46a2-99c6-a75705045442">

# Introduction

This repo has a new `optimize_reco.py` script, modelled on top of `optimize.py` from https://github.com/cms-patatrack/The-Optimizer/tree/main, thought as a wrapper to make the MOPSO work with a generic `cms-sw` reconstruction config in input. 

# First steps

Make sure you have pulled The-Optimizer as a submodule (either using git pull --recursive) or by simply using git pull inside this repository's folder. 
Then follow the instructions at https://github.com/cms-patatrack/The-Optimizer/tree/main and install it by running 
```bash
cd The-Optimizer
pip3 install .
```
Note that you will need to update your `PYTHONPATH` with
```bash
export PYTHONPATH="${PYTHONPATH}:PATH_TO_THEOPTIMIZER_REPO"
```
This can be done automatically by sourcing `extra_setup.sh` once you have created your CMSSW environment.

# Run The-Optimizer

This interface runs the optimizer on top of CMSSW taking a list of parameters to tune, the module they belong to, and a target used to validate against.
`optimize_reco.py` automatically produces a `cmsRun` configuration derived from a provided input configuration (i.e. a `step2.py` or `step.py`).
Let's use as an example the files found in the [examples](./examples) folder which contains the python config file for CMSSW as well as the list of parameters to tune (in a `.csv` file) and the list of lower and upper bounds for those parameters (in a `.json`) file. **Make sure to copy or move the configuration file for CMSSW in the same directory as optimize_reco.py before using it**.

[`hlt_pixel_optimization.py`](./examples/hlt_pixel_optimization.py), generated with:
```bash
cmsDriver.py step2 \
-s L1P2GT,HLT:@relvalRun4,VALIDATION \
--processName HLTX \
--conditions auto:phase2_realistic_T33 \
--datatier GEN-SIM-RECO,MINIAODSIM,NANOAODSIM,DQMIO \
--eventcontent RECOSIM,MINIAODSIM,NANOEDMAODSIM,DQM \
--geometry ExtendedRun4D110 \
--era Phase2C17I13M9 \
--procModifiers alpaka \
--filein file:step2.root \
--fileout file:hlt.root \
--no_exec \
-n -1 \
--python_filename hlt_pixel_optimization.py
```
is a regular CMSSW configuration that runs the HLT reconstruction and validation.

[`params.csv`](./examples/params.csv) contains the list of parameters to be tuned (comma separated)

[`config.json`](./examples/config.json) contains the dictionary of all parameters to be tuned including their lower and upper bounds, as well as their type (in case of vectors, the type of their elements) 

Having these 3 files, The Optimizer is run with the command:
```bash
./optimize_reco.py \
hlt_pixel_optimization.py \
-t hltPhase2PixelTracksSoA \
-v hltPhase2PixelTracks \
--pars examples/params.csv \
-f file:step2.root \
--num_threads 10 \
-p 100 \
-i 10 \
--typedBounds examples/config.json
```
The parameters passed to `optimize_reco.py` are:
- `-t\--tune` gets the name of the module we want to tune (this could be a list but for the moment implemented only for a single module)
- `-v\--validate` is the modules that produces the object on which we want to validate, given in input to the validation
- `--pars` gets the list of parameters that we want to tune with the MOPSO. It can be either a space-separated list passed directy from the command line or a comma-separated list in a `.csv` file
- `-f` to specify the file(s) to be used as input for CMSSW.
- `--numThreads` specifies the number of threads to use in each cmsRun instance
- `-p\--num_particles` the number of agents.
- `-i\--num_iterations` the number of iterations.
- `--typedBounds` takes care of the definition of the upper and lower bounds for the parameters and their types. It expects a `.json` dictionary in the same format as the one shown in the example
    
Executing the command, `optimize_reco.py` will run the following steps:

1. loads the `process` defined in the input config adding to it the `DependencyGraph` `Service` and setting it to run with no source (`EmptySource`) and zero events. The new `process_zero` is then run just to get the graph of the modules used in the config.

2. given the graphs it gets all the modules needed to go from the module(s) `tune` to the module `validate`.

3. define the upper and lower bounds (`ub`/`lb`) that will be parsed to the MOPSO object. 

4. write a new `process_to_run.py` config that is modified in order to get the results of the previous steps and to be able to get the needed params in input from a csv file (the output of the MOPSO basically). This is done by prepending `header.py` and appending  `footer.py`. 

5. the new config takes in input also the number of threads (`--num_threads`), events (`--num_events`) and the input files.

Then, the `process_to_run.py` is the config actually run by the MOPSO and it uses the results from the `optimize_reco.py` to build the `num_particles` different chains to go from (i-th) module(s) `tune` to the (i-th) module `validate` taking care of the tasks definition, of rewriting all the inputs and defining the final validation step (removing the possible output steps).

All of this happens in an ad-hoc folder and one may continue the previous run by specifing in which folder (`--dir`) the script should look for the previous end state and for how many extra iterations `--continuing`. E.g.

```bash
./optimize_reco.py --continuing 10 --dir optimize.step3_pixel_20231123.010104
```
