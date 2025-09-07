from collections import defaultdictimport picklefrom sims4.common import get_available_packsimport sims4.logimport sims4.resourcesfrom singletons import DEFAULTlogger = sims4.log.Logger('TuningDependenciesCache')TD_CACHE_FILENAME = 'td_pickle_cache'TD_CACHE_PY_UNOPT_FILENAME = 'td_pickle_cache_py_unopt'TD_FILENAME_EXTENSION = '.tch'TD_CACHE_VERSION = b'version#0001'_wrong_td_cache_version = FalseTEST_LOCAL_CACHE = False
def read_td_cache_from_resource(available_packs=DEFAULT):
    global _wrong_td_cache_version
    if _wrong_td_cache_version:
        return {}
    key_name = None
    key_name = TD_CACHE_FILENAME
    td_cache_combined = defaultdict(set)
    if available_packs is DEFAULT:
        available_packs = get_available_packs()
    logger.info('Available packs: {}', available_packs)
    if TEST_LOCAL_CACHE:
        file_name = None
        file_name = 'C:\\tmp\\ac_bc_cache\\' + TD_CACHE_FILENAME
        for pack in available_packs:
            pack_name = str(pack).replace('Pack.', '')
            pack_file = file_name + '_' + pack_name + TD_FILENAME_EXTENSION
            logger.always('Loading TD cache file {}.'.format(pack_file))
            with open(pack_file, 'rb') as td_cache_file:
                try:
                    resource_version = td_cache_file.read(len(TD_CACHE_VERSION))
                    td_cache = pickle.load(td_cache_file)
                    logger.always('Loaded TD cache with {} entries.', len(td_cache))
                    for (k, v) in td_cache.items():
                        td_cache_combined[k].update(v)
                except pickle.UnpicklingError as exc:
                    logger.exception('Unpickling the Tuning Dependencies cache failed.', exc=exc, level=sims4.log.LEVEL_WARN)
        return td_cache_combined
    for pack in available_packs:
        pack_name = str(pack).replace('Pack.', '')
        pack_key = key_name + '_' + pack_name
        key = sims4.resources.Key.hash64(pack_key, sims4.resources.Types.TD_CACHE)
        loader = sims4.resources.ResourceLoader(key)
        td_cache_file = loader.load()
        logger.info('Loading TD cache {} (key: {}) as file {}.', pack_key, key, td_cache_file)
        if not td_cache_file:
            logger.debug('Failed to load tuning dependencies cache file from the resource loader (key = {})', pack_key)
        else:
            resource_version = td_cache_file.read(len(TD_CACHE_VERSION))
            if resource_version != TD_CACHE_VERSION:
                _wrong_td_cache_version = True
                logger.warn('The Tuning Dependencies cache in the resource manager is from a different version. Current version is {}, resource manager version is {}.\nPack selection hot loading/unloading will be disabled.', TD_CACHE_VERSION, resource_version)
                return {}
            try:
                for (k, v) in pickle.load(td_cache_file).items():
                    td_cache_combined[k].update(v)
            except pickle.UnpicklingError as exc:
                logger.exception('Unpickling the Tuning Dependencies cache failed.', exc=exc, level=sims4.log.LEVEL_WARN)
                return {}
    return td_cache_combined
