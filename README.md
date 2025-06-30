# NGT instructions for optimization of Pixel Tracks

This repository: [https://github.com/cms-ngt-hlt/cms-reco-optimizer](https://github.com/cms-ngt-hlt/cms-reco-optimizer)
Currently using a development branch `PixelPatatrackDev`.

Optimizer repository: [https://github.com/cms-patatrack/The-Optimizer](https://github.com/cms-patatrack/The-Optimizer)
Currently using a fork (it contains a transparent but necessary option to include the header in pareto front, used for data visualization and plotting).

<img width="1144" alt="Screenshot 2023-11-24 alle 09 46 27" src="https://github.com/cms-pixel-autotuning/CA-parameter-tuning/assets/16901146/5bee2244-9afc-46a2-99c6-a75705045442">

## Introduction

This repo has a new `optimize_reco.py` script, modelled on top of `optimize.py` from https://github.com/cms-patatrack/The-Optimizer/tree/main, thought as a wrapper to make the MOPSO work with a generic `cms-sw` reconstruction config in input. 

### Installation

We are currently using the `CMSSW_15_0_0_pre3` release, in a branch with SimDoublets developments:
```bash
cmsrel CMSSW_15_0_0_pre3
cd CMSSW_15_0_0_pre3/src
cmsenv
git cms-init
```

[Optional] Add SimDoublets:
```bash
git cms-rebase-topic JanGerritSchulz:jgs_ph2_pixelTracking_addSimDoublets
```

Add the exposed parameters and the validation scripts (**NEW** version binned in eta and pt):
```bash
git cms-rebase-topic cms-ngt-hlt:ev_TheOptimizer
```

Install the container for The Optimizer:
```bash
git clone git@github.com:cms-ngt-hlt/cms-reco-optimizer.git
cd cms-reco-optimizer
git checkout PixelPatatrackDev
```

If you are working on the P5 machines, you will need a specific branch of The Optimizer to deactivate Numba, which is in Luca's fork:
```bash
git clone git@github.com:Parsifal-2045/The-Optimizer.git
cd The-Optimizer
git checkout RemoveNumba
cd ../..
```

Finally, compile:
```bash
scram b -j 12
```
</details>

### Input files

- Single Muon samples

Configuration from the default workflow for "SingleMuPt15Eta0_0p4":
```bash
runTheMatrix.py -w upgrade -l 29690.402 -j 0
```

Configuration from the default workflow for "SingleMuPt15Eta1p7_2p7":
```bash
runTheMatrix.py -w upgrade -l 29689.402 -j 0
```

Run the first two steps:
```bash
cmsRun SingleMuPt15Eta0_0p4_cfi_GEN_SIM.py
cmsRun step2_DIGI_L1TrackTrigger_L1_L1P2GT_DIGI2RAW_HLT.py
```

- TTbar samples

Configuration from the default workflow for "TTbar" without pile-up:
```bash
runTheMatrix.py -w upgrade -l 29634.402 -j 0
```

Run the first two steps:
```bash
cmsRun -n 0 TTbar_14TeV_TuneCP5_cfi_GEN_SIM.py
cmsRun -n 0 step2_DIGI_L1TrackTrigger_L1_L1P2GT_DIGI2RAW_HLT_PU.py
```

### [OPTIONAL] Plot of the SimDoublets before optimizing

To plot the doublets before optimizing the cuts, use the SimDoublets analyzer in `src/Validation/TrackingMCTruth/test`".
Change the input file location and run:
```bash
cmsRun simDoubletsPhase2_TEST.py
cmsRun simDoubletsPhase2_HARVESTING.py
```

In order to remove the pt cut, add this line to `simDoubletsPhase2_TEST.py`
```python
process.simDoubletsProducerPhase2.TrackingParticleSelectionConfig.ptMin = cms.double(0.) 
```

The histograms are stored in the `DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root` file.
You can download the sakura package to plot the distributions with the current cuts. Instructions are taken from [this repo](https://github.com/JanGerritSchulz/sakura/tree/master).

Install the package:
```bash
git clone https://github.com/JanGerritSchulz/sakura.git
cd sakura
```

If you are on a machine where pip install works:
```bash
pip3 install .
```
Otherwise:
```bash
export PYTHONPATH=${PYTHONPATH}:$PWD/sakura
```

Produce the plots:
```bash
makeCutPlots DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root ../Validation/TrackingMCTruth/test/simDoubletsPhase2_TEST.py -d Sakura -n -1 -a simDoubletsAnalyzerPhase2
makeGeneralPlots DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root -d Sakura -n -1
```

# Run The-Optimizer

The **NEW** version of the optimization makes use of metrics binned in eta and pt.

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

[`config.json`](./examples/config.json) contains the dictionary of all parameters to be tuned including their lower and upper bounds, as well as their type (in case of vectors, the type of their elements) 

Having these 2 files, The Optimizer can be run. First, source The Optimizer path from within the `cms-reco-optimizer` folder:

```bash
cd cms-reco-optimizer
export PYTHONPATH=${PYTHONPATH}:$PWD/The-Optimizer
```

Then, start the optimization:
```bash
./optimize_reco.py \
hlt_pixel_optimization.py \
-t hltPhase2PixelTracksSoA \
-v hltPhase2PixelTracks \
-f file:../29634.402_TTbar_14TeV+Run4D110_Patatrack_PixelOnlyAlpaka/step2.root \
--num_threads 32 \
-a 32 \
-i 10 \
-b examples/config.json \
--num_events -1 -o test
```
The parameters passed to `optimize_reco.py` are:
- `-t\--tune`: Name of the module to be tuned
- `-v\--validate`: Name of the modules that produces the object on which we want to validate, given in input to the validation
- `-b\--bounds` json file for the definition of the upper and lower bounds for the parameters and their types. It expects a `.json` dictionary in the same format as the one shown in the example
- `-p` gets the list of parameters that we want to tune with the MOPSO. It can be either a space-separated list passed directy from the command line or a comma-separated list in a `.csv` file
- `-f` to specify the file(s) to be used as input for CMSSW
- `-j\--numThreads` specifies the number of threads to use in each cmsRun instance
- `-a\--num_particles` the number of agents
- `-i\--num_iterations` the number of iterations
- `-o` optional output tag for the foder name
- `-i\--num_iterations` the number of iterations
- `--debug` to run in debug mode (helpful when the error in the subprocess running `cmsRun`)
- `--binned_metrics` activate the binned metrics in eta and pt

<details>
<summary>Executing the command, `optimize_reco.py` will run the following steps:</summary>

1. loads the `process` defined in the input config adding to it the `DependencyGraph` `Service` and setting it to run with no source (`EmptySource`) and zero events. The new `process_zero` is then run just to get the graph of the modules used in the config.

2. given the graphs it gets all the modules needed to go from the module(s) `tune` to the module `validate`.

3. define the upper and lower bounds (`ub`/`lb`) that will be parsed to the MOPSO object. 

4. write a new `process_to_run.py` config that is modified in order to get the results of the previous steps and to be able to get the needed params in input from a csv file (the output of the MOPSO basically). This is done by prepending `header.py` and appending  `footer.py`. 

5. the new config takes in input also the number of threads (`--num_threads`), events (`--num_events`) and the input files.

Then, the `process_to_run.py` is the config actually run by the MOPSO and it uses the results from the `optimize_reco.py` to build the `num_particles` different chains to go from (i-th) module(s) `tune` to the (i-th) module `validate` taking care of the tasks definition, of rewriting all the inputs and defining the final validation step (removing the possible output steps).

All of this happens in an ad-hoc folder and one may continue the previous run by specifing in which folder (`--dir`) the script should look for the previous end state and for how many extra iterations `--continuing`. E.g.

```bash
./optimize_reco.py --continuing 10 --dir optimize.hlt_pixel_optimization_20250228.141239_test
```

</details>

## Plotting the results and validate

This branch also includes scripts for plotting the movement of the particles across different iterations (**NEW** version binned in eta and pt):
```bash
python3 examples/PlotParticles.py  --dir <folder_name>
```

To plot the pareto front (**NEW** version binned in eta and pt):
```bash
python3 examples/PlotMetrics.py --dir <folder_name> --best_efficiency --interactive
```

To validate the new configuration:
```bash
python3 examples/GetConfigAndValidate.py --dir <folder_name> --validate --simdoublets
```
Insert the point number you selected, and run the commands for the validation.

The plot the new configuration install the utils package:
```bash
git clone git@github.com:cms-ngt-hlt/utils.git
```

Create your configuration in `Utils/json/myconfig.json` and run
```bash
python3 plotter.py json/myconfig.json
```

<!-- Or:
```bash
python3 examples/ValidationPlots.py --dir optimize.hlt_pixel_optimization_20250127.165402
``` -->

<!-- [Optional] Compare the metrics obtained fro your point and the default configuration:
```bash
cd optimize.hlt_pixel_optimization_20250306.175419_TTBar_SplitBinnedMetricsNoTPselector_AllScalarCuts
cmsRun -n 0 process_to_run.py parametersFile=checkpoint/checkpoint/Configuration/old_point.csv outputFile=checkpoint/checkpoint/Configuration/old_point.root
cmsRun -n 0 process_to_run.py parametersFile=checkpoint/checkpoint/Configuration/new_point43.csv outputFile=checkpoint/checkpoint/Configuration/new_point43.root
python3 example/PlotPoint.py 
``` -->

<!-- 
cmsDriver.py step2 -s DIGI:pdigi_valid,L1TrackTrigger,L1,L1P2GT,DIGI2RAW,HLT:75e33,VALIDATION --conditions auto:phase2_realistic_T33 --datatier GEN-SIM-DIGI-RAW,DQMIO -n -1 --eventcontent FEVTDEBUGHLT,DQMIO --geometry ExtendedRun4D110 --era Phase2C17I13M9 --procModifiers alpaka --nThreads 1 --filein file:step1.root

cmsDriver.py step5 -s HARVESTING:@trackingOnlyValidation+@HLTMon+postProcessorHLTtrackingSequence --conditions auto:phase2_realistic_T33 --mc --geometry ExtendedRun4D110 --scenario pp --filetype DQM --era Phase2C17I13M9 -n 10 --filein file:step2_DIGI_L1TrackTrigger_L1_L1P2GT_DIGI2RAW_HLT_VALIDATION_inDQM.root 
-->

Command to run the optimizer on ZMM 200PU events
```bash
./optimize_reco.py step2_L1P2GT_HLT_VALIDATION.py -t hltIter0Phase2L3FromL1TkMuonTrackCutClassifier -v hltIter0Phase2L3FromL1TkMuonTrackSelectionHighPurity -f /eos/cms/store/relval/CMSSW_15_1_0_pre2/RelValZMM_14/GEN-SIM-DIGI-RAW/PU_150X_mcRun4_realistic_v1_STD_Run4D110_PU-v1/2580000/ --num_threads 50 -a 200 -i 10 -b config.json  --num_events 10000 -o large_sample
```
