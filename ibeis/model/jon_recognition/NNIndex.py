from __future__ import division, print_function
# Standard
from itertools import izip, chain, imap
from os.path import join, normpath, split, exists
# Science
import numpy as np
import pyflann
# UTool
import utool
# IBEIS
from ibeis.dev import params
(print, print_, printDBG, rrr, profile) = utool.inject(
    __name__, '[nnindex]', DEBUG=False)


def get_flann_fpath(data, cache_dir=None, uid='', flann_params=None):
    cache_dir = '.' if cache_dir is None else cache_dir
    # Generate a unique filename for data and flann parameters
    fparams_uid = utool.remove_chars(str(flann_params.values()), ', \'[]')
    data_uid = utool.hashstr_arr(data, 'dID')  # flann is dependent on the data
    flann_suffix = '_' + fparams_uid + '_' + data_uid + '.flann'
    # Append any user labels
    flann_fname = 'flann_index_' + uid + flann_suffix
    flann_fpath = normpath(join(cache_dir, flann_fname))
    return flann_fpath


def precompute_flann(data, cache_dir=None, uid='', flann_params=None,
                     force_recompute=False):
    """ Tries to load a cached flann index before doing anything """
    print('[flann] precompute_flann(%r): ' % uid)
    flann_fpath = get_flann_fpath(data, cache_dir, uid, flann_params)
    flann = pyflann.FLANN()
    load_success = False
    # Load the index if it exists
    if exists(flann_fpath) and not force_recompute:
        try:
            flann.load_index(flann_fpath, data)
            print('[flann]...flann cache hit')
            load_success = True
        except Exception as ex:
            print('[flann] ...cannot load index')
            print('[flann] ...caught ex=\n%r' % (ex,))
    # Rebuild the index otherwise
    if not load_success:
        with utool.Timer('compute FLANN'):
            flann.build_index(data, **flann_params)
        print('[flann] save_index(%r)' % split(flann_fpath)[1])
        flann.save_index(flann_fpath)
    return flann


def get_flann_uid(ibs, cid_list):
    feat_uid   = ibs.cfg.feat_cfg.get_uid()
    sample_uid = utool.hashstr_arr(cid_list, 'dcids')
    uid = '_' + sample_uid + feat_uid
    return uid


def aggregate_descriptors(ibs, cid_list):
    """ Aggregates descriptors with inverted information
     Return agg_index to(2) -> desc (descriptor)
                               cid (chip uid)
                               fx (feature index w.r.t. cid)
    """
    with utool.Timer('[nnindex] aggregate descriptors'):
        fid_list = ibs.get_chip_fids(cid_list)
        desc_list = ibs.get_feat_desc(fid_list)
        # For each descriptor create a (cid, fx) pair indicating its
        # chip id and the feature index in that chip id.
        _ax2_cid = ([cid] * nFeat for (cid, nFeat) in
                    izip(cid_list, imap(len, desc_list)))
        _ax2_fx = (xrange(nFeat) for nFeat in imap(len, desc_list))
        # flatten iterators with mondofast python magic
        ax2_cid = np.array(list(chain.from_iterable(_ax2_cid)))
        ax2_fx  = np.array(list(chain.from_iterable(_ax2_fx)))
        try:
            # Stack into giant numpy array for efficient indexing.
            ax2_desc = np.vstack(desc_list)
        except MemoryError as ex:
            with utool.Indenter('[mem error]'):
                utool.print_exception(ex, 'not enough space for inverted index')
                print('len(cid_list) = %r' % (len(cid_list),))
            raise
    return ax2_desc, ax2_cid, ax2_fx


def build_flann_inverted_index(ibs, cid_list):
    ax2_desc, ax2_cid, ax2_fx = aggregate_descriptors(ibs, cid_list)
    # Build/Load the flann index
    flann_uid = get_flann_uid(ibs, cid_list)
    flann_params = {'algorithm': 'kdtree', 'trees': 4}
    precomp_kwargs = {'cache_dir': ibs.cachedir,
                      'uid': flann_uid,
                      'flann_params': flann_params,
                      'force_recompute': params.args.nocache_flann}
    flann = precompute_flann(ax2_desc, **precomp_kwargs)
    return ax2_cid, ax2_fx, ax2_desc, flann


class NNIndex(object):
    """ Nearest Neighbor (FLANN) Index Class """
    def __init__(nn_index, ibs, cid_list):
        print('[ds] building NNIndex object')
        ax2_cid, ax2_fx, ax2_desc, flann = build_flann_inverted_index(ibs,
                                                                      cid_list)
        # Agg Data
        nn_index.ax2_cid  = ax2_cid
        nn_index.ax2_fx   = ax2_fx
        nn_index.ax2_data = ax2_desc
        nn_index.flann = flann

    def __getstate__(nn_index):
        """ This class it not pickleable """
        printDBG('get state NNIndex')
        #if 'flann' in nn_index.__dict__ and nn_index.flann is not None:
            #nn_index.flann.delete_index()
            #nn_index.flann = None
        # This class is not pickleable
        return None

    def __del__(nn_index):
        """ Ensure flann is propertly removed """
        printDBG('deleting NNIndex')
        if getattr(nn_index, 'flann', None) is not None:
            nn_index.flann.delete_index()
            nn_index.flann = None


def tune_flann(data, **kwargs):
    flann = pyflann.FLANN()
    #num_data = len(data)
    flann_atkwargs = dict(algorithm='autotuned',
                          target_precision=.01,
                          build_weight=0.01,
                          memory_weight=0.0,
                          sample_fraction=0.001)
    flann_atkwargs.update(kwargs)
    suffix = repr(flann_atkwargs)
    badchar_list = ',{}\': '
    for badchar in badchar_list:
        suffix = suffix.replace(badchar, '')
    print(flann_atkwargs)
    tuned_params = flann.build_index(data, **flann_atkwargs)
    utool.myprint(tuned_params)
    out_file = 'flann_tuned' + suffix
    utool.write_to(out_file, repr(tuned_params))
    flann.delete_index()
    return tuned_params


#def __tune():
    #tune_flann(sample_fraction=.03, target_precision=.9, build_weight=.01)
    #tune_flann(sample_fraction=.03, target_precision=.8, build_weight=.5)
    #tune_flann(sample_fraction=.03, target_precision=.8, build_weight=.9)
    #tune_flann(sample_fraction=.03, target_precision=.98, build_weight=.5)
    #tune_flann(sample_fraction=.03, target_precision=.95, build_weight=.01)
    #tune_flann(sample_fraction=.03, target_precision=.98, build_weight=.9)

    #tune_flann(sample_fraction=.3, target_precision=.9, build_weight=.01)
    #tune_flann(sample_fraction=.3, target_precision=.8, build_weight=.5)
    #tune_flann(sample_fraction=.3, target_precision=.8, build_weight=.9)
    #tune_flann(sample_fraction=.3, target_precision=.98, build_weight=.5)
    #tune_flann(sample_fraction=.3, target_precision=.95, build_weight=.01)
    #tune_flann(sample_fraction=.3, target_precision=.98, build_weight=.9)

    #tune_flann(sample_fraction=1, target_precision=.9, build_weight=.01)
    #tune_flann(sample_fraction=1, target_precision=.8, build_weight=.5)
    #tune_flann(sample_fraction=1, target_precision=.8, build_weight=.9)
    #tune_flann(sample_fraction=1, target_precision=.98, build_weight=.5)
    #tune_flann(sample_fraction=1, target_precision=.95, build_weight=.01)
    #tune_flann(sample_fraction=1, target_precision=.98, build_weight=.9)

# Look at /flann/algorithms/dist.h for distance clases

#distance_translation = {"euclidean"        : 1,
                        #"manhattan"        : 2,
                        #"minkowski"        : 3,
                        #"max_dist"         : 4,
                        #"hik"              : 5,
                        #"hellinger"        : 6,
                        #"chi_square"       : 7,
                        #"cs"               : 7,
                        #"kullback_leibler" : 8,
                        #"kl"               : 8,
                        #"hamming"          : 9,
                        #"hamming_lut"      : 10,
                        #"hamming_popcnt"   : 11,
                        #"l2_simple"        : 12,}

# MAKE SURE YOU EDIT index.py in pyflann

#flann_algos = {
    #'linear'        : 0,
    #'kdtree'        : 1,
    #'kmeans'        : 2,
    #'composite'     : 3,
    #'kdtree_single' : 4,
    #'hierarchical'  : 5,
    #'lsh'           : 6, # locality sensitive hashing
    #'kdtree_cuda'   : 7,
    #'saved'         : 254, # dont use
    #'autotuned'     : 255,
#}

#multikey_dists = {
    ## Huristic distances
    #('euclidian', 'l2')        :  1,
    #('manhattan', 'l1')        :  2,
    #('minkowski', 'lp')        :  3, # I guess p is the order?
    #('max_dist' , 'linf')      :  4,
    #('l2_simple')              : 12, # For low dimensional points
    #('hellinger')              :  6,
    ## Nonparametric test statistics
    #('hik','histintersect')    :  5,
    #('chi_square', 'cs')       :  7,
    ## Information-thoery divergences
    #('kullback_leibler', 'kl') :  8,
    #('hamming')                :  9, # xor and bitwise sum
    #('hamming_lut')            : 10, # xor (sums with lookup table;if nosse2)
    #('hamming_popcnt')         : 11, # population count (number of 1 bits)
#}


 #Hamming distance functor - counts the bit differences between two strings -
 #useful for the Brief descriptor
 #bit count of A exclusive XOR'ed with B

#flann_distances = {"euclidean"        : 1,
                   #"manhattan"        : 2,
                   #"minkowski"        : 3,
                   #"max_dist"         : 4,
                   #"hik"              : 5,
                   #"hellinger"        : 6,
                   #"chi_square"       : 7,
                   #"cs"               : 7,
                   #"kullback_leibler" : 8,
                   #"kl"               : 8 }

#pyflann.set_distance_type('hellinger', order=0)
