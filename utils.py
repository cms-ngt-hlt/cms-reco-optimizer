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
    tree = uproot_file['SimpleTrackValidation' + str(id)]['output']
    total_rec = tree['rt'].array()[0]
    total_ass = tree['at'].array()[0]
    total_ass_sim = tree['ast'].array()[0]
    total_dup = tree['dt'].array()[0]
    total_sim = tree['st'].array()[0]
    
    if not total_ass or not total_rec or not total_sim or not total_ass_sim:
        print(f" ### WARNING: Metrics not found for agent {id}")
        return [1.0] * 2
    
    return [1 - total_ass_sim / total_sim, (total_rec - total_ass) / total_rec]

# return string for the metric name used for the csv header
def get_metrics_names():
    return ['1MinusEfficiency', 'FakeDuplicateRate']

# calculate the metrics from validation results in pt and eta bins
def get_binned_metrics(uproot_file, id):
    # pdb.set_trace()
    h_dir_eta = uproot_file['SimpleTrackValidationEtaBins' + str(id)]
    h_dir_pt = uproot_file['SimpleTrackValidationPtBins' + str(id)]
    # histograms vs eta
    h_sim_eta = h_dir_eta['h_st_eta'].values()
    h_ass_sim_eta = h_dir_eta['h_ast_eta'].values()
    h_rec_eta = h_dir_eta['h_rt_eta'].values()
    h_dup_eta = h_dir_eta['h_dt_eta'].values()
    h_ass_eta = h_dir_eta['h_at_eta'].values()
    n_eta_bins = len(h_sim_eta)
    # histograms vs pt
    h_sim_pt = h_dir_pt['h_st_pt'].values()
    h_ass_sim_pt = h_dir_pt['h_ast_pt'].values()
    h_rec_pt = h_dir_pt['h_rt_pt'].values()
    h_dup_pt = h_dir_pt['h_dt_pt'].values()
    h_ass_pt = h_dir_pt['h_at_pt'].values()
    n_pt_bins = len(h_sim_pt)
    
    # metrics vs eta
    metrics_eta = []
    if not h_sim_eta.any() or not h_ass_sim_eta.any() or not h_rec_eta.any() or not h_ass_eta.any() :
        print(f" ### WARNING: Metrics not found for agent {id} in any eta bin")
        metrics_eta = [1.0] * (2 * n_eta_bins)
    else:
        for ib, (i_ast, i_s, i_r, i_d, i_as) in enumerate(zip(h_ass_sim_eta, h_sim_eta, h_rec_eta, h_dup_eta, h_ass_eta)) :
            if not i_s or not i_ast or not i_r or not i_as : 
                metrics_eta += [1.0] * 2
                print(f" ### WARNING: Metrics not found for agent {id} in eta bin {ib}")
            else:
                metrics_eta += [(1 - (i_ast/i_s)), ((i_r - i_as) / i_r)]

    # metrics vs pt
    metrics_pt = []
    if not h_sim_pt.any() or not h_ass_sim_pt.any() or not h_rec_pt.any() or not h_ass_pt.any() :
        print(f" ### WARNING: Metrics not found for agent {id} in any pt bin")
        metrics_pt = [1.0] * (2 * n_pt_bins)
    else:
        for ib, (i_ast, i_s, i_r, i_d, i_as) in enumerate(zip(h_ass_sim_pt, h_sim_pt, h_rec_pt, h_dup_pt, h_ass_pt)) :
            if not i_s or not i_ast or not i_r or not i_as : 
                metrics_pt += [1.0] * 2
                print(f" ### WARNING: Metrics not found for agent {id} in pt bin {ib}")
            else:
                metrics_pt += [(1 - (i_ast/i_s)), ((i_r - i_as) / i_r)]

    # print(" ### INFO DEBUG: ", type(metrics_eta + metrics_pt), metrics_eta + metrics_pt)
    return metrics_eta + metrics_pt

# return string for the metric name used for the csv header
def get_binned_metrics_names():
    return ['1MinusEfficiency_NegEndcap', 'FakeDuplicateRate_NegEndcap', 
            '1MinusEfficiency_Barrel', 'FakeDuplicateRate_Barrel',
            '1MinusEfficiency_PosEndcap', 'FakeDuplicateRate_PosEndcap',
            '1MinusEfficiency_Pt0_3GeV', 'FakeDuplicateRate_Pt0_3GeV',
            '1MinusEfficiency_Pt3_10GeV', 'FakeDuplicateRate_Pt3_10GeV',
            '1MinusEfficiency_Pt10_100GeV', 'FakeDuplicateRate_Pt10_100GeV']

def is_int(value):
    """Check if a string value represents an int."""
    return isinstance(value, (int, np.integer))

def is_float(value):
    """Check if a string value represents a float."""
    return isinstance(value, (float, np.floating))

# read a csv file, return a matrix preserving integer and float types
def read_csv(filename):

    # unpack option helps preserving the type when dealing with mixed type matrices, but requires to transpose back with .T
    matrix = np.array(np.genfromtxt(filename, delimiter=",", dtype=None, unpack=True, ndmin=1), dtype=object).T
    return matrix

# write a matrix to a csv file preserving integer and float types
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
        name = 'SimpleTrackValidation' + str(i)
        setattr(process, name, cms.EDAnalyzer('SimpleTrackValidation',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhiTP = cms.double(3.2),
                maxRapidityTP = cms.double(2.5),
                minHitTP = cms.int32(0),
                minPhiTP = cms.double(-3.2),
                minRapidityTP = cms.double(-2.5),
                pdgIdTP = cms.vint32(),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.85),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(2),
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


def add_validation_binned(process,inputs,target):

    # Here we assume that the process we have given in input has already the 
    # validation and the prevalidation well defined and so we just track
    # back wich hit associator we need to use
    hitassoc = ""
    for f in modules_by_type(process,"TrackAssociatorEDProducer"):
        #print(getattr(f,"label_tr"))
        if getattr(f,"label_tr").value() == target:
            hitassoc = getattr(f,"associator").value()
            break
    
    taskList_eta = []
    taskList_pt = []
    for i,_ in enumerate(inputs):
        
        # All these params may be copied from the MTV defined in the process
        name = 'SimpleTrackValidationEtaBins' + str(i)
        setattr(process, name, cms.EDAnalyzer('SimpleTrackValidationEtaBins',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhiTP = cms.double(3.2),
                maxRapidityTP = cms.double(4.5),
                minHitTP = cms.int32(0),
                minPhiTP = cms.double(-3.2),
                minRapidityTP = cms.double(-4.5),
                pdgIdTP = cms.vint32(),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.9),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(2),
                trackLabels = cms.VInputTag(target + str(i)),
                trackAssociator = cms.untracked.InputTag(hitassoc),
                trackingParticles = cms.InputTag('mix', 'MergedTrackTruth')               
            )
        )

        taskList_eta.append(getattr(process, name))

        # All these params may be copied from the MTV defined in the process
        name = 'SimpleTrackValidationPtBins' + str(i)
        setattr(process, name, cms.EDAnalyzer('SimpleTrackValidationPtBins',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhiTP = cms.double(3.2),
                maxRapidityTP = cms.double(4.5),
                minHitTP = cms.int32(0),
                minPhiTP = cms.double(-3.2),
                minRapidityTP = cms.double(-4.5),
                pdgIdTP = cms.vint32(),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.4),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(2),
                trackLabels = cms.VInputTag(target + str(i)),
                trackAssociator = cms.untracked.InputTag(hitassoc),
                trackingParticles = cms.InputTag('mix', 'MergedTrackTruth')               
            )
        )

        taskList_pt.append(getattr(process, name))

    process.SimpleTrackValidationEtaBinsSeq = cms.Sequence(sum(taskList_eta[1:],taskList_eta[0]))
    process.SimpleTrackValidationPtBinsSeq = cms.Sequence(sum(taskList_pt[1:],taskList_pt[0]))
    process.simpleBinnedValidationPath = cms.EndPath(process.SimpleTrackValidationEtaBinsSeq + process.SimpleTrackValidationPtBinsSeq)
    process.schedule.extend([process.simpleBinnedValidationPath])

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

def expand_process_binned(process,inputs,params,tune,chain,target):
    
    process = remove_outputs(process) #check for all EndPaths 
    process = modules_tuning(process,inputs,params,tune)
    process = add_validation_binned(process,inputs,target)
    process = chain_update(process,inputs,tune,chain+[target])
    
    return process
