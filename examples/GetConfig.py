import sys, os, pdb, json
import pandas as pd

try: main_folder = sys.argv[1]
except: sys.exit(" ### ERROR: Please provide the path to the main folder\n"
    " --> python3 examples/GetConfig.py optimize.hlt_pixel_optimization_20250127.165402")

pareto_filename = f'{main_folder}/checkpoint/checkpoint/pareto_front.csv'
bounds_filename = f'{main_folder}/bounds.json'
output_folder = f'{main_folder}/checkpoint/checkpoint/Configuration'
os.system(f'mkdir -p {output_folder}')

# get the parameters in the pareto front
df = pd.read_csv(pareto_filename)
header = df.keys().to_list()

metric_1 = "1MinusEfficiency"
metric_2 = "FakeDuplicateRate"
vector_cuts = ['phiCuts']
metrics = [item for item in header if metric_1 in item or metric_2 in item]
vars = [item for item in header if item not in metrics]

# get the original config file
cms_base = os.getenv('CMSSW_BASE')
if not cms_base: sys.exit(" ### ERROR: Please run cmsenv before.")
initial_config_file = f'{cms_base}/src/HLTrigger/Configuration/python/HLT_75e33/modules/hltPhase2PixelTracksSoA_cfi.py'
print(f"\n ### INFO: Reading original configuration from\n{initial_config_file}\n")

import importlib.util
import FWCore.ParameterSet.Config as cms

def load_module_from_file(module_name, file_path):
    """Dynamically load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

module = load_module_from_file("myModule", initial_config_file)
hltPhase2PixelTracksSoA = module.hltPhase2PixelTracksSoA

# Save the original configuration (useful to compare with the new one with same formatting)
old_out_name = f"{output_folder}/old_hltPhase2PixelTracksSoA_cfi.py"
with open(f"{old_out_name}", "w") as f:
    f.write("import FWCore.ParameterSet.Config as cms\n\n")
    f.write("hltPhase2PixelTracksSoA = cms.EDProducer(\n")
    f.write(f'    "{hltPhase2PixelTracksSoA.type_()}",\n')

    for param, value in hltPhase2PixelTracksSoA.parameters_().items():
        f.write(f"    {param} = {value},\n")
    
    f.write(")\n\n")
    f.write("_hltPhase2PixelTracksSoASingleIterPatatrack = hltPhase2PixelTracksSoA.clone( minHitsPerNtuplet = 3 )\n\n")
    f.write("from Configuration.ProcessModifiers.singleIterPatatrack_cff import singleIterPatatrack\n")
    f.write("singleIterPatatrack.toReplaceWith(hltPhase2PixelTracksSoA, _hltPhase2PixelTracksSoASingleIterPatatrack)\n")

print(f"\n ### INFO: Saving original configuration to\n{old_out_name}\n")

point = input(" >>> Which point of the pareto front would you like to use? >>> ")

modified_hltPhase2PixelTracksSoA = hltPhase2PixelTracksSoA.clone()

# get types of parameters from bounds json file
with open(bounds_filename, 'r') as file:
    params_bounds = json.loads(file.read())

for var in vars:
    # Remove vector cuts
    if any(vector_cut in var for vector_cut in vector_cuts):
        continue
    else:
        if params_bounds[var]['value_type'] == 'int':
            value = int(df.iloc[int(point)][var])
        else:
            value = round(float(df.iloc[int(point)][var]), 3) # only store 3 digits

        setattr(modified_hltPhase2PixelTracksSoA, var, value)

for vector_cut in vector_cuts:
    if any(vector_cut in var for var in vars):
        len_vector_value = sum([vector_cut in var for var in vars])
        if params_bounds[vector_cut]['value_type'] == 'int':
            vector_value = [int(df.iloc[int(point)][f'{vector_cut}{i}']) for i in range(len_vector_value)]
        else:
            vector_value = [round(float(df.iloc[int(point)][f'{vector_cut}{i}']), 3) for i in range(len_vector_value)]

        setattr(modified_hltPhase2PixelTracksSoA, vector_cut, vector_value)

# Save the modified configuration
new_out_name = f"{output_folder}/new_hltPhase2PixelTracksSoA_cfi.py"
with open(f"{new_out_name}", "w") as f:
    f.write("import FWCore.ParameterSet.Config as cms\n\n")
    f.write("hltPhase2PixelTracksSoA = cms.EDProducer(\n")
    f.write(f'    "{modified_hltPhase2PixelTracksSoA.type_()}",\n')

    for param, value in modified_hltPhase2PixelTracksSoA.parameters_().items():
        f.write(f"    {param} = {value},\n")
    
    f.write(")\n\n")
    f.write("_hltPhase2PixelTracksSoASingleIterPatatrack = hltPhase2PixelTracksSoA.clone( minHitsPerNtuplet = 3 )\n\n")
    f.write("from Configuration.ProcessModifiers.singleIterPatatrack_cff import singleIterPatatrack\n")
    f.write("singleIterPatatrack.toReplaceWith(hltPhase2PixelTracksSoA, _hltPhase2PixelTracksSoASingleIterPatatrack)\n")

print(f"\n ### INFO: Saving modified configuration to\n{new_out_name}\n")
