import numpy as np
from inspect import getmro
import sys
import os
import warnings
from itertools import cycle
import json

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
            # create new ith module only if it doesn't already exist
            if f not in tune and not hasattr(process, f + str(i)):
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
        highPurity = "hltIter0Phase2L3FromL1TkMuonTrackSelectionHighPurity" + str(i)
        classifier = "hltIter0Phase2L3FromL1TkMuonTrackCutClassifier" + str(i)
        setattr(process, highPurity, cms.EDProducer("TrackCollectionFilterCloner",
                copyExtras = cms.untracked.bool(True),
                copyTrajectories = cms.untracked.bool(False),
                minQuality = cms.string('highPurity'),
                originalMVAVals = cms.InputTag(classifier, "MVAValues"),
                originalQualVals = cms.InputTag(classifier, "QualityMasks"),
                originalSource = cms.InputTag("hltL3MuonTracksSelectionFromL1TkMu")
            )
        )
        taskList.append(getattr(process, highPurity))

        assoc = "Phase2tpToL3IOiter0TkHighPurityAssociation" + str(i) 
        setattr(process, assoc, cms.EDProducer("MuonAssociatorEDProducer",
                AbsoluteNumberOfHits_muon = cms.bool(False),
                AbsoluteNumberOfHits_track = cms.bool(False),
                CSClinksTag = cms.InputTag("simMuonCSCDigis","MuonCSCStripDigiSimLinks"),
                CSCsimHitsTag = cms.InputTag("g4SimHits","MuonCSCHits"),
                CSCsimHitsXFTag = cms.InputTag("mix","g4SimHitsMuonCSCHits"),
                CSCwireLinksTag = cms.InputTag("simMuonCSCDigis","MuonCSCWireDigiSimLinks"),
                DTdigiTag = cms.InputTag("simMuonDTDigis"),
                DTdigisimlinkTag = cms.InputTag("simMuonDTDigis"),
                DTrechitTag = cms.InputTag("hltDt1DRecHits"),
                DTsimhitsTag = cms.InputTag("g4SimHits","MuonDTHits"),
                DTsimhitsXFTag = cms.InputTag("mix","g4SimHitsMuonDTHits"),
                EfficiencyCut_muon = cms.double(0.0),
                EfficiencyCut_track = cms.double(0.0),
                GEMdigisimlinkTag = cms.InputTag("simMuonGEMDigis","GEM"),
                GEMsimhitsTag = cms.InputTag("g4SimHits","MuonGEMHits"),
                GEMsimhitsXFTag = cms.InputTag("mix","g4SimHitsMuonGEMHits"),
                NHitCut_muon = cms.uint32(0),
                NHitCut_track = cms.uint32(0),
                PurityCut_muon = cms.double(0.75),
                PurityCut_track = cms.double(0.75),
                ROUList = cms.vstring(
                    'TrackerHitsTIBLowTof',
                    'TrackerHitsTIBHighTof',
                    'TrackerHitsTIDLowTof',
                    'TrackerHitsTIDHighTof',
                    'TrackerHitsTOBLowTof',
                    'TrackerHitsTOBHighTof',
                    'TrackerHitsTECLowTof',
                    'TrackerHitsTECHighTof',
                    'TrackerHitsPixelBarrelLowTof',
                    'TrackerHitsPixelBarrelHighTof',
                    'TrackerHitsPixelEndcapLowTof',
                    'TrackerHitsPixelEndcapHighTof'
                ),
                RPCdigisimlinkTag = cms.InputTag("simMuonRPCDigis","RPCDigiSimLink"),
                RPCsimhitsTag = cms.InputTag("g4SimHits","MuonRPCHits"),
                RPCsimhitsXFTag = cms.InputTag("mix","g4SimHitsMuonRPCHits"),
                ThreeHitTracksAreSpecial = cms.bool(False),
                UseGrouped = cms.bool(True),
                UseMuon = cms.bool(False),
                UsePixels = cms.bool(True),
                UseSplitting = cms.bool(True),
                UseTracker = cms.bool(True),
                acceptOneStubMatchings = cms.bool(False),
                associatePixel = cms.bool(True),
                associateRecoTracks = cms.bool(True),
                associateStrip = cms.bool(True),
                associatorByWire = cms.bool(False),
                crossingframe = cms.bool(False),
                dumpDT = cms.bool(False),
                dumpInputCollections = cms.untracked.bool(False),
                ignoreMissingTrackCollection = cms.untracked.bool(True),
                includeZeroHitMuons = cms.bool(True),
                inputCSCSegmentCollection = cms.InputTag("cscSegments"),
                inputDTRecSegment4DCollection = cms.InputTag("dt4DSegments"),
                links_exist = cms.bool(True),
                phase2TrackerSimLinkSrc = cms.InputTag("simSiPixelDigis","Tracker"),
                pixelSimLinkSrc = cms.InputTag("simSiPixelDigis","Pixel"),
                rejectBadGlobal = cms.bool(True),
                simtracksTag = cms.InputTag("g4SimHits"),
                simtracksXFTag = cms.InputTag("mix","g4SimHits"),
                stripSimLinkSrc = cms.InputTag("simSiStripDigis"),
                tpRefVector = cms.bool(True),
                tpTag = cms.InputTag("TPmu"),
                tracksTag = cms.InputTag(target + str(i)),
                useGEMs = cms.bool(True),
                usePhase2Tracker = cms.bool(True)
            )           
        )
        taskList.append(getattr(process, assoc))

        # All these params may be copied from the MTV defined in the process
        name = 'SimpleTrackValidation' + str(i)
        setattr(process, name, cms.EDAnalyzer('SimpleTrackValidation',
                chargedOnlyTP = cms.bool(True),
                intimeOnlyTP = cms.bool(False),
                invertRapidityCutTP = cms.bool(False),
                lipTP = cms.double(30.0),
                maxPhiTP = cms.double(3.2),
                maxRapidityTP = cms.double(2.4),
                minHitTP = cms.int32(0),
                minPhiTP = cms.double(-3.2),
                minRapidityTP = cms.double(-2.4),
                pdgIdTP = cms.vint32(13,-13),
                ptMaxTP = cms.double(1e+100),
                ptMinTP = cms.double(0.85),
                signalOnlyTP = cms.bool(True),
                stableOnlyTP = cms.bool(False),
                tipTP = cms.double(2),
                trackLabels = cms.VInputTag(target + str(i)),
                associatormap = cms.InputTag('Phase2tpToL3IOiter0TkHighPurityAssociation' + str(i)),
                trackingParticles = cms.InputTag('mix', 'MergedTrackTruth')               
            )
        )

        taskList.append(getattr(process, name))

    process.simpleValidationSeq = cms.Sequence(sum(taskList[1:],taskList[0]))
    process.simpleValidationPath = cms.EndPath(process.simpleValidationSeq)
    process.TPMuPath = cms.EndPath(process.TPmu_seq)
    process.schedule.extend([process.TPMuPath])
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
    
# Helper to recursively get/set parameter by path (e.g., 'filterPSet.maxChi2.value')
def get_nested_param(obj, path):
    parts = path.split('.')
    for p in parts:
        if hasattr(obj, p):
            obj = getattr(obj, p)
        elif isinstance(obj, dict) and p in obj:
            obj = obj[p]
        else:
            return None
    return obj

def set_nested_param(obj, path, value):
    parts = path.split('.')
    for p in parts[:-1]:
        if hasattr(obj, p):
            obj = getattr(obj, p)
        elif isinstance(obj, dict) and p in obj:
            obj = obj[p]
        else:
            return False
    last = parts[-1]
    if hasattr(obj, last):
        setattr(obj, last, value)
        return True
    elif isinstance(obj, dict) and last in obj:
        obj[last] = value
        return True
    return False

def modules_tuning(process,inputs,params,tune,value_types=None):
    # value_types: dict mapping param name to 'int' or 'double' (from config)
    for i, row in enumerate(inputs):
        modules_to_tune = [getattr(process,t).clone() for t in tune]
        col = 0
        for n, p in enumerate(params):
            for m in modules_to_tune:
                par = get_nested_param(m, p)
                if par is not None:
                    vtype = value_types[p] if value_types and p in value_types else None
                    # Handle vector vs scalar
                    if is_v_input(type(par)):
                        # Assign each element from consecutive columns
                        length = len(par)
                        vals = row[col:col+length]
                        if vtype == "int":
                            for idx in range(length):
                                par[idx] = int(vals[idx])
                        else:
                            for idx in range(length):
                                par[idx] = float(vals[idx])
                        col += length
                    else:
                        val = row[col]
                        if vtype == "int":
                            set_nested_param(m, p, int(val))
                        else:
                            set_nested_param(m, p, float(val))
                        col += 1
        for n,m in zip(tune,modules_to_tune):
            setattr(process,n+str(i),m)
    return process
   
def expand_process(process,inputs,params,tune,chain,target):

    process = remove_outputs(process) #check for all EndPaths 
    
    with open("bounds.json") as bounds_file:
        bounds = json.load(bounds_file)
    value_types = extract_value_types(bounds)
        
    process = modules_tuning(process,inputs,params,tune,value_types)
    process = add_validation(process,inputs,target)
    process = chain_update(process,inputs,tune,chain+[target])
    
    return process

def expand_process_binned(process,inputs,params,tune,chain,target):
    
    process = remove_outputs(process) #check for all EndPaths 
    process = modules_tuning(process,inputs,params,tune)
    process = add_validation_binned(process,inputs,target)
    process = chain_update(process,inputs,tune,chain+[target])
    
    return process

# Recursively extract all parameter paths from a module or PSet
# Returns a list of dot-separated parameter paths (including nested ones)
def extract_param_paths(obj, prefix=""):
    paths = []
    # Try to get parameters_() if available (for modules/PSets)
    if hasattr(obj, 'parameters_'):
        params = obj.parameters_()
    elif isinstance(obj, dict):
        params = obj
    else:
        return paths
    for k, v in params.items():
        path = f"{prefix}.{k}" if prefix else k
        # If v is a PSet or similar, recurse
        if hasattr(v, 'parameters_') or isinstance(v, dict):
            paths.extend(extract_param_paths(v, path))
        else:
            paths.append(path)
    return paths

def extract_value_types(config_dict):
    """Extracts a dict mapping parameter name to value_type from the config dict."""
    return {k: v.get("value_type", "double") for k, v in config_dict.items()}
