import numpy as np
from inspect import getmro
import sys
import os
import warnings
from itertools import cycle

spinner = cycle('-/|\\')

def spinning(): ##doesn't work
    print(next(spinner),flush=True,end="")
    os.sleep(0.05)
    sys.stdout.write("\r")

with warnings.catch_warnings():
    warnings.filterwarnings("ignore",category=DeprecationWarning)
    import imp

try:
    from FWCore.ParameterSet.Mixins import _Parameterizable, _ValidatingParameterListBase
    import FWCore.ParameterSet.Config as cms
    from FWCore.ParameterSet.MassReplace import MassSearchReplaceAnyInputTagVisitor
    from HLTrigger.Configuration.common import modules_by_type
except:
    print("Working without CMS modules")

# calculate the metrics from validation results
def get_metrics(uproot_file, id):
    tree = uproot_file['simpleValidation' + str(id)]['output']
    total_rec = tree['rt'].array()[0]
    total_ass = tree['at'].array()[0]
    total_ass_sim = tree['ast'].array()[0]
    total_dup = tree['dt'].array()[0]
    total_sim = tree['st'].array()[0]
    
    if not total_ass or not total_rec or not total_sim or not total_ass_sim:
        print(f" ### WARNING: Metrics not found for agent {id}")
        return [1.0] * 2
    
    return [1 - total_ass_sim / total_sim, (total_rec - total_ass + total_dup) / total_rec]

# return string for the metric name used for the csv header
def get_metrics_names():
    return ['1MinusEfficiency', 'FakeDuplicateRate']

def is_int(value):
    return isinstance(value, (int, np.integer))

# read a csv file, return a matrix
def read_csv(filename):
    matrix = np.genfromtxt(filename, delimiter=",", dtype=None)
    matrix_typed = []
    if matrix.ndim == 2:
        for row in matrix:
            new_row = []
            for el in row:
                typed_element = int(el) if is_int(el) else float(el) 
                new_row.append(typed_element)
            matrix_typed.append(new_row)
    elif matrix.ndim == 1:
        for el in matrix:
            typed_element = int(el) if is_int(el) else float(el) 
            matrix_typed.append([typed_element])
    else:
        matrix_typed = [[int(matrix) if is_int(matrix) else float(matrix)]]

    return matrix_typed

# write a matrix to a csv file
def write_csv(filename, matrix):

    if hasattr(matrix[0], '__len__'):
        fmt = ",".join(["%d" if is_int(vt) else "%f" for vt in matrix[0]])
    else:
        fmt = ",".join(["%d" if is_int(vt) else "%f" for vt in matrix])
    np.savetxt(filename, np.matrix(matrix), fmt=fmt, delimiter=',')

### cmsRun specific helpers

def parseProcess(filename): 
  # from https://github.com/cms-patatrack/patatrack-scripts/blob/master/multirun.py
  # parse the given configuration file and return the `process` object it define
  # the import logic is taken from edmConfigDump
  try:
    handle = open(filename, 'r')
  except:
    print("Failed to open %s: %s" % (filename, sys.exc_info()[1]))
    sys.exit(1)

  # make the behaviour consistent with 'cmsRun file.py'
  sys.path.append(os.getcwd())
  try:
    pycfg = imp.load_source('pycfg', filename, handle)
    process = pycfg.process
  except:
    print("Failed to parse %s: %s" % (filename, sys.exc_info()[1]))
    sys.exit(1)

  handle.close()
  return process

def has_params(typ):
    return _Parameterizable in getmro(typ)

def is_v_input(typ):
    return _ValidatingParameterListBase in getmro(typ)

def chain_update(process,inputs,tune,modules):

    taskList = []
    for i,_ in enumerate(inputs):
        
        replace = {}
        # define replacers for all
        for f in modules + tune:
            replace[f] = MassSearchReplaceAnyInputTagVisitor(f, f+str(i), verbose=False) # True to see all the renamings
            # create new ith module
            if f not in tune: #we have already taken care of the modules to tune
                setattr(process, f + str(i), getattr(process,f).clone()) 

        #apply replacement for all the ith modules, with all the (other) ith modules
        for m in modules:
            module = getattr(process,m + str(i))
            for f in modules + tune:
                if f != m: # not realy needed
                    replace[f].doIt(module, m + str(i))
            taskList.append(module)

        for t in tune:
            taskList.append(getattr(process,t + str(i)))
            
    process.mainTask = cms.Task(*taskList)
    process.mainPath = cms.Path(process.mainTask)

    process.schedule.extend([process.mainPath])
    return process

def remove_outputs(process):

    for s in process.endpaths_():#.keys():   
        process.schedule.remove(getattr(process,s))

    return process

def add_validation(process,inputs,target):

    # Here we assume that the process we have given in input has already the 
    # validation and the prevalidation well defined and so we just track
    # back wich hit associator we need to use
    hitassoc = ""
    for f in modules_by_type(process,"TrackAssociatorEDProducer"):
        #print(getattr(f,"label_tr"))
        if getattr(f,"label_tr").value() == target:
            hitassoc = getattr(f,"associator").value()
            break
    
    taskList = []
    for i,_ in enumerate(inputs):
        
        # All these params may be copied from the MTV defined in the process
        name = 'simpleValidation' + str(i)
        setattr(process, name, cms.EDAnalyzer('SimpleValidation',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhi = cms.double(3.2),
                maxRapidityTP = cms.double(2.5),
                minHitTP = cms.int32(0),
                minPhi = cms.double(-3.2),
                minRapidityTP = cms.double(-2.5),
                pdgIdTP = cms.vint32(),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.9),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(3.5),
                trackLabels = cms.VInputTag(target + str(i)),
                trackAssociator = cms.untracked.InputTag(hitassoc),
                trackingParticles = cms.InputTag('mix', 'MergedTrackTruth')               
            )
        )

        taskList.append(getattr(process, name))

    process.simpleValidationSeq = cms.Sequence(sum(taskList[1:],taskList[0]))
    process.simpleValidationPath = cms.EndPath(process.simpleValidationSeq)
    process.schedule.extend([process.simpleValidationPath])

    return process
    
def modules_tuning(process,inputs,params,tune):
    
    for i, row in enumerate(inputs):
        modules_to_tune = [getattr(process,t).clone() for t in tune]
        for n, p in enumerate(params):
            for m in modules_to_tune:
                this_params = m.parameters_()
                if p in this_params:
                    par = this_params[p]
                    # check if it's a vector of doubles 
                    if is_v_input(type(par)): 
                        # change the list of values
                        l = len(par.value())
                        setattr(m,p,[int(row[n+i]) for i in range(l)]) 
                    else:
                         # change the value
                        setattr(m,p,row[n]) 
        for n,m in zip(tune,modules_to_tune): 
            # append index to the name of module to tune
            setattr(process,n+str(i),m) 
        
    return process
   
def expand_process(process,inputs,params,tune,chain,target):
    
    process = remove_outputs(process) #check for all EndPaths 
    process = modules_tuning(process,inputs,params,tune)
    process = add_validation(process,inputs,target)
    process = chain_update(process,inputs,tune,chain+[target])
    

    return process
            