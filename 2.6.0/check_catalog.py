from bika.lims import api
catalog = api.get_tool('bika_catalog')
samples = catalog(portal_type='AnalysisRequest', sort_on='created', sort_order='descending')
print('TOTAL SAMPLES: %d' % len(samples))
if samples:
    print('NEWEST: %s %s %s' % (samples[0].id, samples[0].created, samples[0].review_state))
