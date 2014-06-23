"""
Module Licence and docstring
"""
from __future__ import absolute_import, division, print_function
from ibeis import constants
#IMAGE_UID_TYPE = 'INTEGER'
#annot_UID_TYPE   = 'INTEGER'
#NAME_UID_TYPE  = 'INTEGER'


def define_IBEIS_schema(ibs):
    # TODO, Add algoritm config column
    ibs.db.schema(constants.IMAGE_TABLE, (
        ('image_rowid',                  'INTEGER PRIMARY KEY'),
        ('image_uuid',                   'UUID NOT NULL'),
        ('image_uri',                    'TEXT NOT NULL'),
        ('image_ext',                    'TEXT NOT NULL'),
        ('image_original_name',          'TEXT NOT NULL'),  # We could parse this out
        #('image_original_path',          'TEXT NOT NULL'),
        ('image_width',                  'INTEGER DEFAULT -1'),
        ('image_height',                 'INTEGER DEFAULT -1'),
        ('image_exif_time_posix',        'INTEGER DEFAULT -1'),
        ('image_exif_gps_lat',           'REAL DEFAULT -1.0'),   # there doesn't seem to exist a GPSPoint in SQLite
        ('image_exif_gps_lon',           'REAL DEFAULT -1.0'),
        ('image_confidence',             'REAL DEFAULT -1.0',),  # Move to an algocfg table?
        ('image_toggle_enabled',         'INTEGER DEFAULT 0'),
        ('image_toggle_aif',             'INTEGER DEFAULT 0'),
        ('image_note',                   'TEXT',),
    ), ['CONSTRAINT superkey UNIQUE (image_uuid)'])

    # Used to store the detected annots / bboxed annots
    # TODO: Rename to annots
    ibs.db.schema(constants.ANNOT_TABLE, (
        ('annot_rowid',                    'INTEGER PRIMARY KEY'),
        ('annot_uuid',                     'UUID NOT NULL'),
        ('image_rowid',                  'INTEGER NOT NULL'),
        #('name_rowid',                  'INTEGER NOT NULL'),
        ('annot_xtl',                      'INTEGER NOT NULL'),
        ('annot_ytl',                      'INTEGER NOT NULL'),
        ('annot_width',                    'INTEGER NOT NULL'),
        ('annot_height',                   'INTEGER NOT NULL'),
        ('annot_theta',                    'REAL DEFAULT 0.0'),
        ('annot_num_verts',                'INTEGER NOT NULL'),
        ('annot_verts',                    'TEXT'),
        ('annot_detect_confidence',        'REAL DEFAULT -1.0'),
        ('annot_exemplar_flag',            'INTEGER DEFAULT 0'),
        ('annot_note',                     'TEXT'),
    ), ['CONSTRAINT superkey UNIQUE (annot_uuid)']
    )
    # Used to store the relationship between annot (annots) and Labels
    ibs.db.schema(constants.AL_RELATION_TABLE, (
        ('alr_rowid',                      'INTEGER PRIMARY KEY'),
        ('annot_rowid',                      'INTEGER NOT NULL'),
        ('label_rowid',                    'INTEGER NOT NULL'),
        ('config_rowid',                   'INTEGER DEFAULT 0'),
        ('alr_confidence',                 'REAL DEFAULT 0.0'),
    ))

    # Used to store the results of annots
    # the label key must be in
    # {
    # 'INDIVIDUAL_KEY': 0,
    # 'SPECIES_KEY': 1,
    # }
    ibs.db.schema(constants.LABEL_TABLE, (
        ('label_rowid',                   'INTEGER PRIMARY KEY'),
        ('label_uuid',                    'UUID NOT NULL'),
        ('key_rowid',                     'INTEGER NOT NULL'),  # this is "category" in the proposal
        ('label_value',                   'TEXT NOT NULL'),
        ('label_note',                    'TEXT'),
    ), ['CONSTRAINT superkey UNIQUE (key_rowid, label_value)'])

    # List of keys used to define the categories of annotation tables, text is for human-readability
    ibs.db.schema(constants.KEY_TABLE, (
        ('key_rowid',                'INTEGER PRIMARY KEY'),
        ('key_text',                 'TEXT NOT NULL')
        ), ['CONSTRAINT superkey UNIQUE (key_text)'])

    # List of all encounters
    ibs.db.schema(constants.ENCOUNTER_TABLE, (
        ('encounter_rowid',             'INTEGER PRIMARY KEY'),
        ('encounter_uuid',              'UUID NOT NULL'),
        ('encounter_text',              'TEXT NOT NULL'),
        ('encounter_note',              'TEXT NOT NULL'),
    ),  ['CONSTRAINT superkey UNIQUE (encounter_text)'])

    # Relationship between encounters and images (many to many mapping)
    # encounter_image_relationship stands for encounter-image-pairs.
    ibs.db.schema(constants.EG_RELATION_TABLE, (
        ('egpair_rowid',                  'INTEGER PRIMARY KEY'),
        ('image_rowid',                   'INTEGER NOT NULL'),
        ('encounter_rowid',               'INTEGER'),
    ),  ['CONSTRAINT superkey UNIQUE (image_rowid, encounter_rowid)'])

    # Detection and identification algorithm configurations, populated
    # with caching information
    ibs.db.schema(constants.CONFIG_TABLE, (
        ('config_rowid',                 'INTEGER PRIMARY KEY'),
        ('config_suffix',                'TEXT NOT NULL'),
    ),  ['CONSTRAINT superkey UNIQUE (config_suffix)'])

    # Used to store *processed* annots as chips
    ibs.db.schema(constants.CHIP_TABLE, (
        ('chip_rowid',                   'INTEGER PRIMARY KEY'),
        ('annot_rowid',                    'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('chip_uri',                     'TEXT'),
        ('chip_width',                   'INTEGER NOT NULL'),
        ('chip_height',                  'INTEGER NOT NULL'),
    ), ['CONSTRAINT superkey UNIQUE (annot_rowid, config_rowid)'])  # TODO: constraint needs modify

    # Used to store individual chip features (ellipses)
    ibs.db.schema(constants.FEATURE_TABLE, (
        ('feature_rowid',                'INTEGER PRIMARY KEY'),
        ('chip_rowid',                   'INTEGER NOT NULL'),
        ('config_rowid',                 'INTEGER DEFAULT 0'),
        ('feature_num_feats',            'INTEGER NOT NULL'),
        ('feature_keypoints',            'NUMPY'),
        ('feature_sifts',                'NUMPY'),
    ), ['CONSTRAINT superkey UNIQUE (chip_rowid, config_rowid)'])

    #
    # UNUSED / DEPRICATED
    #

    # List of recognition directed edges (annot_1) --score--> (annot_2)
    # ibs.db.schema('recognitions', (
    #     ('recognition_rowid',           'INTEGER PRIMARY KEY'),
    #     ('annot_rowid1',                  'INTEGER NOT NULL'),
    #     ('annot_rowid2',                  'INTEGER NOT NULL'),
    #     ('recognition_score',           'REAL NOT NULL'),
    #     ('recognition_annotrank',         'INTEGER NOT NULL'),
    #     ('recognition_namerank',        'INTEGER NOT NULL'),
    #     ('recognition_note',            'TEXT'),
    # ),  ['CONSTRAINT superkey UNIQUE (annot_rowid1, annot_rowid2)'])

    # Used to store *processed* annots as segmentations
    # ibs.db.schema('masks', (
    #     ('mask_rowid',                  'INTEGER PRIMARY KEY'),
    #     ('config_rowid',                'INTEGER DEFAULT 0'),
    #     ('annot_rowid',                   'INTEGER NOT NULL'),
    #     ('mask_uri',                    'TEXT NOT NULL'),
    # ))

    # Used to store individual chip identities (Fred, Sue, ...)
    #ibs.db.schema('names', (
    #    ('name_rowid',                   'INTEGER PRIMARY KEY'),
    #    ('name_text',                    'TEXT NOT NULL'),
    #    ('name_note',                    'TEXT',),
    #), ['CONSTRAINT superkey UNIQUE (name_text)'])
