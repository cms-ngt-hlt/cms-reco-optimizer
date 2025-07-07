import sys, os, pdb, json
import pandas as pd
import numpy as np

'''
To run:
    python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402
    python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402 --num 1000
    python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402 --validate
    python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402 --simdoublets
    python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402 --point 0
'''

if __name__ == "__main__" :

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--dir",              dest="dir",             default=None,      help='Name for the input directory',         type=str           )
    parser.add_option("--validate",         dest="validate",        default=None,      help='Run the validation on hltPhase2Pixel', action='store_true')
    parser.add_option("--simdoublets",      dest="simdoublets",     default=None,      help='Run the validation on SimDoublets',    action='store_true')
    parser.add_option("--point",            dest="point",           default=None,      help='Selected point for validation',        type=int           )
    parser.add_option("--num",              dest="num",             default=100,       help='Number of events',                     type=int           )
    (options, args) = parser.parse_args()

    step1_path = '/eos/cms/store/relval/CMSSW_15_0_0_pre3/RelValTTbar_14TeV/GEN-SIM-DIGI-RAW/PU_141X_mcRun4_realistic_v3_STD_Run4D110_PU-v2/2580000/01b8c5dd-42a1-46b7-8607-f4c990ba3ab3.root' # [TO BE CHANGED]
    step2_path = '/eos/cms/store/relval/CMSSW_15_0_0_pre3/RelValTTbar_14TeV/GEN-SIM-DIGI-RAW/PU_141X_mcRun4_realistic_v3_STD_Run4D110_PU-v2/2580000/01b8c5dd-42a1-46b7-8607-f4c990ba3ab3.root' # [TO BE CHANGED]

    if not options.dir:
        sys.exit(" ### ERROR: Please provide the path to the main folder\n"
        " --> python3 examples/GetConfigAndValidate.py --dir optimize.hlt_pixel_optimization_20250127.165402")

    main_folder = options.dir

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
    print(f"\n ### INFO: Reading original configuration from\n{initial_config_file}")

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

    if options.point: config = options.point
    else: config = input(" >>> Which point of the pareto front would you like to use [number or 'default']? >>> ")

    if not config == 'default':
        point = int(config)

        old_line = []
        new_line = []
        fmt = []
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
                    value = int(df.iloc[point][var])
                    fmt.append('%d')
                else:
                    value = round(float(df.iloc[point][var]), 3) # only store 3 digits
                    fmt.append('%f')
                
                old_line.append(getattr(modified_hltPhase2PixelTracksSoA, var).value())
                setattr(modified_hltPhase2PixelTracksSoA, var, value)
                new_line.append(value)

        for vector_cut in vector_cuts:
            if any(vector_cut in var for var in vars):
                len_vector_value = sum([vector_cut in var for var in vars])
                if params_bounds[vector_cut]['value_type'] == 'int':
                    vector_value = [int(df.iloc[point][f'{vector_cut}{i}']) for i in range(len_vector_value)]
                    fmt.append(['%d']*len(vector_value))
                else:
                    vector_value = [round(float(df.iloc[point][f'{vector_cut}{i}']), 3) for i in range(len_vector_value)]
                    fmt.append(['%f']*len(vector_value))

                old_line.append(getattr(modified_hltPhase2PixelTracksSoA, vector_cut).value())
                setattr(modified_hltPhase2PixelTracksSoA, vector_cut, vector_value)
                new_line.append(vector_value)

        # Save the modified configuration
        new_producer_name = f'new_point{point}_hltPhase2PixelTracksSoA'
        new_out_name = f"{output_folder}/new_point{point}_hltPhase2PixelTracksSoA_cfi.py"
        with open(f"{new_out_name}", "w") as f:
            f.write("import FWCore.ParameterSet.Config as cms\n\n")
            f.write(f"{new_producer_name} = cms.EDProducer(\n")
            f.write(f'    "{modified_hltPhase2PixelTracksSoA.type_()}",\n')

            for param, value in modified_hltPhase2PixelTracksSoA.parameters_().items():
                f.write(f"    {param} = {value},\n")
            
            f.write(f")\n\n")
            f.write(f"_{new_producer_name}SingleIterPatatrack = {new_producer_name}.clone( minHitsPerNtuplet = 3 )\n\n")
            f.write(f"from Configuration.ProcessModifiers.singleIterPatatrack_cff import singleIterPatatrack\n")
            f.write(f"singleIterPatatrack.toReplaceWith({new_producer_name}, _{new_producer_name}SingleIterPatatrack)\n")

        print(f"\n ### INFO: Saving modified configuration to\n{new_out_name}")

        print(f"\n ### INFO: These are the default values:\n{old_line}")
        np.savetxt(f"{output_folder}/old_point.csv", np.matrix(old_line), fmt=fmt, delimiter=',')

        print(f"\n ### INFO: This is the line you have selected:\n{new_line}")
        np.savetxt(f"{output_folder}/new_point{point}.csv", np.matrix(new_line), fmt=fmt, delimiter=',')

    ######################################################
    # Prepare the validation with the new config
    ######################################################

    if options.validate:

        if not config == 'default':
            folder = f'new_point{point}'
            # Copy new module to base CMSSW folder
            copy_path = f'{cms_base}/src/HLTrigger/Configuration/python/HLT_75e33/modules/'
            print(f"\n ### INFO: Copying {new_out_name} to {copy_path}")
            os.system(f'cp {new_out_name} {copy_path}')
        else:
            folder = 'default'

        print(f"\n ### INFO: Producing step2 configuration in {output_folder}/{folder}")
        os.system(f'mkdir -p {output_folder}/{folder}')

        # Produce step 2 configuration
        print(f"\n ### INFO: Preparing step2 configuration")
        python_step2 = f'{output_folder}/{folder}/step2_DIGI_L1TrackTrigger_L1_L1P2GT_DIGI2RAW_HLT_VALIDATION.py'
        command = f'cmsDriver.py step2 -s L1P2GT,HLT:75e33,VALIDATION'
        command += f' --conditions auto:phase2_realistic_T33 --datatier GEN-SIM-DIGI-RAW,DQMIO -n {options.num} --no_exec'
        command += f' --processName HLTX --eventcontent FEVTDEBUGHLT,DQMIO --geometry ExtendedRun4D110 --era Phase2C17I13M9 --procModifiers alpaka'
        command += f' --python_filename {python_step2}'
        command += f' --filein file:{step1_path} --fileout file:step2.root'
        print(command)
        os.system(f'{command}')

        if not config == 'default':
            # Modify the configuration to take the new module
            custom_lines = [
                f"from HLTrigger.Configuration.HLT_75e33.modules.new_point{point}_hltPhase2PixelTracksSoA_cfi import {new_producer_name}\n",
                f"process.hltPhase2PixelTracksSoA = {new_producer_name}.clone()\n"
            ]

            with open(python_step2, "r") as file:
                lines = file.readlines()
            for i, line in enumerate(lines):
                if "# customisation of the process." in line:
                    lines.insert(i + 1, "".join(custom_lines))
                    break
            with open(python_step2, "w") as file:
                file.writelines(lines)

        print(f"\n ### INFO: Preparing step5 configuration")
        python_step5 = f'{output_folder}/{folder}/step5_HARVESTING.py'
        command = f'cmsDriver.py step5 -s HARVESTING:@trackingOnlyValidation+@HLTMon+postProcessorHLTtrackingSequence'
        command += f' --conditions auto:phase2_realistic_T33 --mc -n -1 --no_exec'
        command += f' --geometry ExtendedRun4D110 --scenario pp --filetype DQM --era Phase2C17I13M9'
        command += f' --python_filename {python_step5}'
        command += f' --filein file:step2_inDQM.root'
        print(command)
        os.system(f'{command}')

        print(f"\n >>>>>>>>>>>> To run the hltPhase2Pixel validation \n")
        print(f"    cd {output_folder}/{folder}")
        print(f"    cmsRun -n 0 step2_DIGI_L1TrackTrigger_L1_L1P2GT_DIGI2RAW_HLT_VALIDATION.py")
        print(f"    cmsRun step5_HARVESTING.py")
        print(f"    makeTrackValidationPlots.py DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root")

    ######################################################
    # Prepare the plots of simDoublets with the new config
    ######################################################
    
    if options.simdoublets:

        if not config == 'default':
            folder = f'new_point{point}'
        else:
            folder = 'default'

        # Modify analyzer with current config
        initial_config_file = f'{cms_base}/src/Validation/TrackingMCTruth/test/simDoubletsPhase2_TEST.py'
        os.system(f'mkdir -p {output_folder}/{folder}')
        os.system(f'mkdir -p {output_folder}/{folder}/SimDoublets')
        
        if not config == 'default':

            custom_lines = f'# From optimized configuration\n'
            for var in vars:
                # Remove vector cuts
                if any(vector_cut in var for vector_cut in vector_cuts):
                    continue
                else:
                    if params_bounds[var]['value_type'] == 'int':
                        value = int(df.iloc[point][var])
                        custom_lines += f'process.simDoubletsAnalyzerPhase2.{var} = cms.int32({value})\n'
                    else:
                        value = round(float(df.iloc[point][var]), 3) # only store 3 digits
                        custom_lines += f'process.simDoubletsAnalyzerPhase2.{var} = cms.double({value})\n'
                    
                    old_line.append(getattr(modified_hltPhase2PixelTracksSoA, var).value())
                    setattr(modified_hltPhase2PixelTracksSoA, var, value)
                    new_line.append(value)
            for vector_cut in vector_cuts:
                if any(vector_cut in var for var in vars):
                    len_vector_value = sum([vector_cut in var for var in vars])
                    if params_bounds[vector_cut]['value_type'] == 'int':
                        vector_value = [int(df.iloc[point][f'{vector_cut}{i}']) for i in range(len_vector_value)]
                        custom_lines += f'process.simDoubletsAnalyzerPhase2.{vector_cut} = cms.vint32({vector_value})\n'
                    else:
                        vector_value = [round(float(df.iloc[point][f'{vector_cut}{i}']), 3) for i in range(len_vector_value)]
                        custom_lines += f'process.simDoubletsAnalyzerPhase2.{vector_cut} = cms.vint32({vector_value})\n'

            # Read default analyzer
            with open(initial_config_file, "r") as file:
                default_lines = file.readlines()
            
            new_lines = ''
            for i, line in enumerate(default_lines):
                # Modify input files
                if "inputFile =" in line:
                    new_lines += f'inputFile = "{step2_path}"'
                # Modify number of events
                elif "    input = cms.untracked.int32(-1)," in line:
                    new_lines += f'    input = cms.untracked.int32({options.num}),\n'
                # Add new config
                elif "process.simDoubletsProducerPhase2.TrackingParticleSelectionConfig.ptMin = cms.double(0.)" in line:
                    new_lines += line+'\n'
                    if not config == 'default':
                        new_lines += custom_lines+'\n'
                else:
                    new_lines += line

            new_config_file = f'simDoubletsPhase2_new_point{point}_TEST.py'
            new_config_path = f'{output_folder}/{folder}/SimDoublets/{new_config_file}'
            print(f"\n ### INFO: Creating analyzer {new_config_path}")
            with open(new_config_path, "w") as file:
                file.writelines(map(str, new_lines))
            
        else:
            new_config_file = 'simDoubletsPhase2_TEST.p'
            new_config_path = f'{output_folder}/{folder}/SimDoublets/{new_config_file}'
            os.system(f'cp {initial_config_file} {new_config_path}')
            print(f"\n ### INFO: Copy default analyzer in {new_config_path}")

        harvesting_file = f'{cms_base}/src/Validation/TrackingMCTruth/test/simDoubletsPhase2_HARVESTING.py'
        os.system(f'cp {harvesting_file} {output_folder}/{folder}/SimDoublets/simDoubletsPhase2_HARVESTING.py')
        print(f"\n ### INFO: Copy harvester to {output_folder}/{folder}/SimDoublets/simDoubletsPhase2_HARVESTING.py")

        print(f"\n >>>>>>>>>>>> To run the SimDoublets validation \n")
        print(f"    cd {output_folder}/{folder}/SimDoublets")
        print(f"    cmsRun -n 0 {new_config_file}")
        print(f"    cmsRun simDoubletsPhase2_HARVESTING.py")
        print(f"    makeCutPlots DQM_V0001_R000000001__Global__CMSSW_X_Y_Z__RECO.root {new_config_file} -d Sakura -n -1 -a simDoubletsAnalyzerPhase2 -d ./")
