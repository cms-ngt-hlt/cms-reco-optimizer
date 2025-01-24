#! /usr/bin/env python3
import optimizer
from optimizer import MOPSO
import subprocess
import itertools
from utils import get_metrics, write_csv, parseProcess, spinner, read_csv
from graphs import convert_to_graph, from_modules_to_module
import numpy as np
import uproot
import argparse
import os
import json
import random
import pandas as pd
import shutil
import sys
from pathlib import Path
from termcolor import colored
from functools import partial
from datetime import datetime

#from reco_optimizer import RecoTuner future

import FWCore.ParameterSet.Config as cms

# parsing argument
parser = argparse.ArgumentParser()

allowed_recos = ("tracks","hgcal")

is_continuing = '--continuing' in sys.argv

if not is_continuing:
    parser.add_argument('config', help = "Config to tune.")
## Optimizer parameters
parser.add_argument('-p', '--num_particles', default=100, type=int, action='store',help = "Number of agents to spawn by the MOPSO optimizer.")
parser.add_argument('-i', '--num_iterations', default=100, type=int, action='store',help = "Number of iterations to be run by MOPSO optimizer.")
parser.add_argument('-c', '--continuing', type=str, default=None)
parser.add_argument('-d', '--dir', type=str, action='store', help = "Directory where to continue.", required = is_continuing)  
parser.add_argument('-b', '--bounds', nargs=2,help='Mins',default=(5,5))
parser.add_argument('--typedBounds', nargs=1,help='json file with dictionary for upper,lower and type of params', default=None)
parser.add_argument('--check', action='store_true', help = "Run the config once before the optimizer.")
parser.add_argument('--debug', action='store_true', help = "Debug printouts.")
## cmsRun parameters
parser.add_argument('-t','--tune', nargs='+', help='List of modules to tune.', required = not is_continuing)
parser.add_argument('-v','--validate', type=str, help='Target module to validate.', required = not is_continuing)
parser.add_argument('--pars', nargs='+', help='Parameters to tune. \n These may be given as a list of parameters names or a file with the names separated by a ",".', required = not is_continuing)
parser.add_argument('-j', '--num_threads', default=8, type=int, action='store')
parser.add_argument('-e', '--num_events', default=100, type=int, action='store')
parser.add_argument('-f', '--input_file', nargs='+', default=["file:step2.root"])
parser.add_argument('--reco', nargs='?', choices=allowed_recos,help='Type of reco to be run %s.'%repr(allowed_recos)) # to be implemented
parser.add_argument('-T', '--timing', action='store_true', help = "Add timing/throughput for the pareto front.")

args = parser.parse_args()

# run pixel reconstruction and simple validation
def reco_and_validate(params,config,**kwargs):#,timing=False):

    workdir = os.getcwd() 
    num_particles = len(params)

    # setting up temp folder
    if not os.path.exists('temp'):
        os.mkdir('temp')
    
    # writing current input parameters from mopso
    write_csv('temp/parameters.csv', params)
    validation_result = 'temp/simple_validation.root'
    

    # redirecting outputs to logs
    logfiles = tuple('%s/logs/%s' % (workdir, name) for name in ['process_last_out', 'process_last_err'])
    stdout = open(logfiles[0], 'w')
    stderr = open(logfiles[1], 'w')

    command = ['cmsRun',config,'parametersFile=temp/parameters.csv', 'outputFile=' + validation_result]    
    subprocess.run(command,stdout = stdout, stderr = stderr)
    
    with uproot.open(validation_result) as uproot_file:
        population_fitness = [get_metrics(uproot_file, i) for i in range(num_particles)]

    return population_fitness
  
def print_headers(x):
    print(colored(x,"green",attrs=['bold']))
def print_subheaders(x):
    print(colored(x,"magenta",attrs=['bold']))
def print_warnings(x):
    print(colored(x,"yellow",attrs=['bold']))
def print_errors(x):
    print(colored(x,"red",attrs=['bold']))
def print_bounds(x):
    print("".join([f for f in ["\t-" + k + ": %s"%p+"\n" for k,p in x.items()]]))
def print_logo():
    f= open ('logo.txt','r')
    print(''.join([line for line in f]))

def copy_to_unique(c):

    formatted_date = datetime.now().strftime("%Y%m%d.%H%M%S")
    b = "./optimize."+c.replace(".py","")+"_"+formatted_date #str(random.getrandbits(64))
    os.mkdir(b)
    shutil.copy(c,b+"/"+c)
    shutil.copy("utils.py",b)
    shutil.copy(os.path.basename(__file__),b)
    os.chdir(b)
    

if __name__ == "__main__":
    
    print_logo()
    input_files = [ "file:" + os.path.abspath(f[5:]) if f.startswith("file:") else f for f in args.input_file ]
    start_dir = os.getcwd()
    config_to_run = 'process_to_run.py'
    config_to_graph = 'process_zero.py'

    
    optimizer.FileManager.saving_enabled = True
    objective = optimizer.Objective(objective_functions=partial(reco_and_validate, config = config_to_run),num_objectives=2)
    loglevel = 'DEBUG' if args.debug else 'INFO'
    optimizer.Logger.setLevel(loglevel)

    if args.continuing is not None:

        optimizer.FileManager.working_dir = args.dir + "/checkpoint/"
        optimizer.FileManager.loading_enabled = True

        os.chdir(args.dir)
        print_headers("> Continuing the optimization in folder: %s"%args.dir)

        n_particles = len(read_csv("temp/parameters.csv"))
        pso = MOPSO(objective=objective,
                    lower_bounds=read_csv("lb.csv")[0], upper_bounds=read_csv("ub.csv"))
        pso.optimize(num_iterations=args.num_iterations)
        sys.exit(0)
    
    config_input = args.config
    ## Move to the new hashed folder

    copy_to_unique(config_input)
    workdir = os.getcwd()
    checkdir = workdir + '/checkpoint/'
    if not os.path.exists(checkdir):
        os.mkdir(checkdir)

    optimizer.FileManager.working_dir = checkdir

    modules_to_tune = args.tune
    module_to_valid = args.validate

    print_headers("> Running optimizer on the config: %s"%repr(config_input))
    print_headers("> Working dir: %s"%workdir)
    print("> > Module(s) to tune\t:",repr(modules_to_tune))
    print("> > Module to validate\t:",module_to_valid)
    print("> > Input file(s)\t:",input_files)

    # recotuner = RecoTuner(files = input_files, args)

    print_headers("> Running with 0 events to build the graph")
    dot_to_run = config_input.replace("py","dot")
    process_zero = parseProcess(config_input)
    ## This is just to get the dependecy graph
    process_zero.source = cms.Source("EmptySource",
        numberEventsInRun = cms.untracked.uint32(0),
        firstRun = cms.untracked.uint32(0)
    )

    process_zero.DependencyGraph = cms.Service("DependencyGraph")
    process_zero.DependencyGraph.fileName = cms.untracked.string(dot_to_run)
    process_zero.maxEvents.input = cms.untracked.int32(0)
    with open(config_to_graph,'w') as f:     
        f.write(process_zero.dumpPython() )
        f.write('\n' )

    # redirecting outputs to logs
    os.mkdir("logs")
    logfiles = tuple('%s/logs/%s' % (workdir, name) for name in ['process_zero_out', 'process_zero_err'])
    with open(logfiles[0], 'w') as stdout, open(logfiles[1], 'w') as stderr:
        subprocess.run(['cmsRun', config_to_graph], stderr=stderr, stdout=stdout,check=True)
    
    print("> > Processing the graph in:",dot_to_run)
    process_graph = convert_to_graph(dot_to_run)
    modules_to_modify = from_modules_to_module(process_graph,modules_to_tune,module_to_valid)
    
    print("> > Modules to replicate   :",repr(modules_to_modify))
    

    ## Getting parameter names that could be either
    #  - a list
    #  - an input csv file with a list
    print_headers("> Parameters to tune:")
    if len(args.pars) == 1 and Path(start_dir+"/"+args.pars[0]).is_file():
        par_file = start_dir+"/"+args.pars[0]
        with open(par_file, 'r') as file:
            params = file.read().replace("\n","").split(",")
        print("> > Read from",repr(par_file),": ",params)
    else:
        params = args.pars
        with open('params_to_run.csv',"w") as file:
            file.write("%s"%",".join(args.pars))
        print("> > Read in input:",params,"(saved in params_to_run.csv)")

    # Handling parameter values in input
    ##TODO add a check on bounds being well ordered (min < max)
    print_headers("> Parameter values:")
    params_dict = getattr(process_zero,modules_to_tune[0]).parameters_()

    default_values = {}
    for k in params:
        if k in params_dict:
            default_values[k] = params_dict[k].value() # underlying object wrapped in cms type
        else:
            print_warnings("WARNING: Parameter %s does not exist in module %s! The available parameters are:"%(k,modules_to_tune[0]))
            print_warnings(list(params_dict.keys()))
    print(params_dict)
    if(len(default_values) < 1):
        sys.exit("Error: in module %s none of the parameters %s was found! Aborting."%(modules_to_tune[0],params))
    print_subheaders("> > Default values: ")
    
    #Defining low bounds and high bounds
    lb = []
    ub = []
    dv = []
    print_bounds(default_values)
    if (args.typedBounds is not None):
        with open(start_dir+"/"+args.typedBounds[0], 'r') as file:
            params_bounds = json.loads(file.read())
        print("> > Read from",repr(args.typedBounds[0]),":")
        print_bounds(params_bounds)
        for k in params_bounds.keys():
            dv.append(default_values[k])
            value_type = params_bounds[k]["value_type"]
            if value_type == "int":
                lb_ = params_bounds[k]["down"]
                lb = lb + [int(lb_)] if not hasattr(lb_, "__len__") else lb + [int(j) for j in lb_]
                ub_ = params_bounds[k]["up"]
                ub = ub + [int(ub_)] if not hasattr(ub_, "__len__") else ub + [int(j) for j in ub_]
            elif value_type == "double": 
                lb_ = params_bounds[k]["down"]
                lb = lb + [float(lb_)] if not hasattr(lb_, "__len__") else lb + [float(j) for j in lb_]
                ub_ = params_bounds[k]["up"]
                ub = ub + [float(ub_)] if not hasattr(ub_, "__len__") else ub + [float(j) for j in ub_]
    else:
        params_bounds = dict(zip(["Low","High"],args.bounds))
        for b,w in params_bounds.items():
            print_subheaders("> > %s bounds: "%b)
            if Path(start_dir+"/"+str(w)).is_file():
                with open(start_dir+"/"+w, 'r') as file:
                     params_bounds[b] = json.loads(file.read())
                print("> > Read from",repr(w),":")
                print_bounds(params_bounds[b])
            else:
                w = float(w)
                m = w if b=="High" else 1./w
                params_bounds[b] = {k: np.multiply(v,m).astype(type(v[0])).tolist() if hasattr(v, "__len__") else type(v)(float(v)*m) for k,v in default_values.items()  }
                print("> > From input (factor=%.3f):"%m)
                print_bounds(params_bounds[b])
            sys.stdout.write("\r")
        for f in list(params_bounds["High"].values()):
            ub = ub + f if hasattr(f, "__len__") else ub + [f]
        for f in list(params_bounds["Low"].values()):
            lb = lb + f if hasattr(f, "__len__") else lb + [f]
        for f in list(default_values.values()):
            dv = dv + f if hasattr(f, "__len__") else dv + [f]


    # Dumping value dictionaries for the records
    #pd.DataFrame(default_values).to_json("default_values.json")
    #pd.DataFrame(params_bounds["High"]).to_json("high_values.json")
    #pd.DataFrame(params_bounds["Low"]).to_json("low_values.json")
    # Dumping lower bounds and upper bounds for "continuing option"
    write_csv("lb.csv",lb)
    write_csv("ub.csv",ub)

    with open(config_to_run, 'w') as new:
        
        ## header for inputs params
        with open(start_dir+'/header.py') as add: 
            new.write(add.read())
        
        ## input config to run
        with open(config_input) as add:
            new.write(add.read())
        
        ## footer with the customization for the optimizer
        with open(start_dir+'/footer.py') as add:
            new.write("\n### Optimzer customization\n")

            new.write('process.source.fileNames\t= %s\n'%repr(input_files))
            new.write('process.options.numberOfThreads\t = %d\n\n'%args.num_threads)
            new.write('process.maxEvents.input\t = %d\n'%(args.num_events))
            new.write('tune\t= %s\n'%repr(modules_to_tune)) # remove SwitchProducerCUDA instances, could be better
            new.write('chain\t= %s\n'%repr([ f for f in modules_to_modify if "@" not in f]))
            new.write('params\t= %s\n'%repr(params))
            new.write('target\t= %s\n\n'%repr(module_to_valid))

            new.write(add.read())

    
    if args.check:
        print_headers("> Running once with %d events to test"%args.num_events)
        logfiles = tuple('%s/logs/%s' % (workdir, name) for name in ['process_check_out', 'process_check_err'])
        with open(logfiles[0], 'w') as stdout, open(logfiles[1], 'w') as stderr:
            write_csv("default_values.csv",dv)
            job = subprocess.Popen(['cmsRun', config_to_run, "parametersFile=default_values.csv"], cwd=workdir, stderr=stderr, stdout=stdout)
            job.communicate()
    
    print_headers("> Ready to go, running the optimizer!")
    print("> > Number of agents    :",args.num_particles)
    print("> > Number of iterations:",args.num_iterations)

    pso = MOPSO(objective=objective,lower_bounds=lb, upper_bounds=ub, 
                num_particles=args.num_particles)
    
    pso.optimize(num_iterations=args.num_iterations)
    
    
# run the optimization algorithm
#pso.optimize(history_dir='history', checkpoint_dir='checkpoint')

