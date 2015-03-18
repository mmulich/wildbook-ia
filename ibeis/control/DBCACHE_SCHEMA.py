"""
Module Licence and docstring
"""
from __future__ import absolute_import, division, print_function
from ibeis import constants as const
try:
    from ibeis.control import DBCACHE_SCHEMA_CURRENT
    UPDATE_CURRENT  = DBCACHE_SCHEMA_CURRENT.update_current
    VERSION_CURRENT = DBCACHE_SCHEMA_CURRENT.VERSION_CURRENT
except:
    UPDATE_CURRENT  = None
    VERSION_CURRENT = None
    print("[dbcache] NO DBCACHE_SCHEMA_CURRENT AUTO-GENERATED!")
import utool
import utool as ut
profile = utool.profile


# =======================
# Schema Version 1.0.0
# =======================


@profile
def update_1_0_0(db, ibs=None):
    ##########################
    # SECOND ORDER           #
    ##########################
    # TODO: constraint needs modification
    db.add_table(const.CHIP_TABLE, (
        ('chip_rowid',                   'INTEGER PRIMARY KEY'),
        ('annot_rowid',                  'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('chip_uri',                     'TEXT'),
        ('chip_width',                   'INTEGER NOT NULL'),
        ('chip_height',                  'INTEGER NOT NULL'),
    ),
        superkeys=[('annot_rowid', 'config_rowid',)],
        docstr='''
        Used to store *processed* annots as chips''')

    db.add_table(const.FEATURE_TABLE, (
        ('feature_rowid',                'INTEGER PRIMARY KEY'),
        ('chip_rowid',                   'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('feature_num_feats',            'INTEGER NOT NULL'),
        ('feature_keypoints',            'NUMPY'),
        # Maybe change name to feature_vecs
        ('feature_sifts',                'NUMPY'),
    ),
        superkeys=[('chip_rowid, config_rowid',)],
        docstr='''
        Used to store individual chip features (ellipses)''')


# =======================
# Schema Version 1.0.1
# =======================


@profile
def update_1_0_1(db, ibs=None):
    # When you're ready to make this schema update go live, simply
    # bump ibs.dbcache_version_expected in the controller to '1.0.1'
    db.add_table(const.RESIDUAL_TABLE, (
        ('residual_rowid',               'INTEGER PRIMARY KEY'),
        ('feature_rowid',                'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('residual_vector',              'NUMPY'),
    ),
        # TODO: Remove residual_rowid from being a superkey
        superkeys=[('residual_rowid', 'feature_rowid', 'config_rowid',)],
        docstr='''
        Used to store individual SMK/ASMK residual vectors for features''')
    pass


@profile
def update_1_0_2(db, ibs=None):
    # Change name of feature_sifts to feature_vecs and
    # add new column for feature_forground_weight
    db.modify_table(const.FEATURE_TABLE, (
        ('feature_sifts',   'feature_vecs',             'NUMPY', None),
        (           None,   'feature_forground_weight', 'NUMPY', None),
    ))


@profile
def update_1_0_3(db, ibs=None):
    # Move the forground weight column to a new table
    db.drop_column(const.FEATURE_TABLE, 'feature_forground_weight')

    db.add_table(tablename=const.FEATURE_WEIGHT_TABLE, coldef_list=(
        ('featweight_rowid',            'INTEGER PRIMARY KEY'),
        ('feature_rowid',               'INTEGER NOT NULL'),
        ('config_rowid',                'INTEGER DEFAULT 0'),
        ('featweight_forground_weight', 'NUMPY'),
    ),
        superkeys=[('feature_rowid', 'config_rowid',)],
        docstr='''
        Stores weightings of features based on the forground... etc
        '''
    )

    # Fix the superkeys for the residual table
    db.modify_table(tablename=const.RESIDUAL_TABLE, colmap_list=[],
                    superkeys=[('feature_rowid', 'config_rowid',)],)


def update_1_0_4(db, ibs=None):
    db.modify_table(const.CHIP_TABLE, dependson=const.ANNOTATION_TABLE)
    db.modify_table(const.FEATURE_TABLE, dependson=const.CHIP_TABLE)
    db.modify_table(const.FEATURE_WEIGHT_TABLE, dependson=const.FEATURE_TABLE, shortname='featweight')
    #db.modify_table(const.FEATURE_WEIGHT_TABLE, dependson=[const.FEATURE_TABLE, const.PROBCHIP_TABLE])
    #db.modify_table(const.RESIDUAL_TABLE, dependson=[const.FEATURE_TABLE, const.VOCAB_TABLE])
    #db.modify_table(const.PROBCHIP_TABLE, dependson=[const.CHIP_TABLE])


# ========================
# Valid Versions & Mapping
# ========================


base = const.BASE_DATABASE_VERSION
VALID_VERSIONS = ut.odict([
    #version:   (Pre-Update Function,  Update Function,    Post-Update Function)
    (base   ,    (None,                 None,               None,)),
    ('1.0.0',    (None,                 update_1_0_0,       None,)),
    ('1.0.1',    (None,                 update_1_0_1,       None,)),
    ('1.0.2',    (None,                 update_1_0_2,       None,)),
    ('1.0.3',    (None,                 update_1_0_3,       None,)),
    ('1.0.4',    (None,                 update_1_0_4,       None,)),
])


def test_dbcache_schema():
    """
    test_dbcache_schema

    Example:
        >>> # ENABLE_DOCTEST
        >>> from ibeis.control.DBCACHE_SCHEMA import *  # NOQA
        >>> test_dbcache_schema()

    CommandLine:
        python -m ibeis.control.DBCACHE_SCHEMA --test-test_dbcache_schema
        python -m ibeis.control.DBCACHE_SCHEMA --test-test_dbcache_schema --dump-autogen-schema
        python -m ibeis.control.DBCACHE_SCHEMA --force-incremental-db-update

    """
    from ibeis.control import DBCACHE_SCHEMA
    from ibeis.control import _sql_helpers
    from ibeis import params
    autogenerate = params.args.dump_autogen_schema
    n = utool.get_argval('-n', int, default=-1)
    dbcache = _sql_helpers.get_nth_test_schema_version(DBCACHE_SCHEMA, n=n, autogenerate=autogenerate)
    autogen_cmd = 'python -m ibeis.control.DBCACHE_SCHEMA --force-incremental-db-update --test-test_dbcache_schema --dump-autogen-schema\n'
    autogen_cmd += 'python -m ibeis.control.DBCACHE_SCHEMA --force-incremental-db-update --test-test_dbcache_schema'
    autogen_text = dbcache.get_schema_current_autogeneration_str(autogen_cmd)

    show_diff = ut.get_argflag('--diff')
    num_context_lines = ut.get_argval('--diff', type_=int, default=None)
    show_diff = show_diff or num_context_lines is not None

    from os.path import dirname
    if show_diff:
        autogen_fpath = ut.unixjoin(dirname(__file__), 'DBCACHE_SCHEMA_CURRENT.py')
        if ut.checkpath(autogen_fpath, verbose=True):
            prev_text = ut.read_from(autogen_fpath)
            textdiff = ut.util_str.get_textdiff(prev_text, autogen_text, num_context_lines=num_context_lines)
            ut.print_difftext(textdiff)
    else:
        ut.util_print.print_python_code(autogen_text)
    print(' Run with --dump-autogen-schema to autogenerate latest schema version')


if __name__ == '__main__':
    """
    python -m ibeis.control.DBCACHE_SCHEMA
    python -m ibeis.control.DBCACHE_SCHEMA --allexamples
    """
    import multiprocessing
    multiprocessing.freeze_support()
    import utool as ut
    ut.doctest_funcs()
