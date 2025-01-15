#!/usr/bin/env python3

import requests
import itertools
import time
import json
import sys

queryResult = requests.post('https://query.wikidata.org/bigdata/namespace/wdq/sparql', '''
SELECT DISTINCT ?qid
WHERE {
  ?qid wdt:P495 wd:Q794. # Iran (Q794) is country of origin (P495)
  ?qid wdt:P3383 ?x.     # Item has a film poster (P3383)
}
''', headers={'Content-Type': 'application/sparql-query', 'Accept': 'application/json'})

def wikidata_items(ids):
    for batch in itertools.batched(ids, 50):
        yield from requests.post(
            'https://www.wikidata.org/w/api.php',
            {'action': 'wbgetentities',
             'format': 'json',
             'ids': '|'.join(batch)}
        ).json()['entities'].values()
        print('fetched 50 items, sleep for 2s', file=sys.stderr)
        time.sleep(2)
    print('finished', file=sys.stderr)

films = {
    item['id']: {
        'id': item['id'],
        'sitelinks': {
            site: link['title']
            for site, link in item['sitelinks'].items()
            if site == 'fawiki' or site == 'enwiki'
        },
        'labels': {
            lang: label['value']
            for lang, label in item['labels'].items()
            if lang == 'fa' or lang == 'en'
        },
        'date': [x['mainsnak']['datavalue']['value']['time']
                 for x in item['claims'].get('P577', [])],
        'imdb': [x['mainsnak']['datavalue']['value']
                 for x in item['claims'].get('P345', [])],
        'poster': [{
            'image': poster['mainsnak']['datavalue']['value'],
            'designer': [x['datavalue']['value']['id']
                         for x in poster.get('qualifiers', {}).get('P170', {})],
        } for poster in item['claims'].get('P3383', [])],
        'logo': [x['mainsnak']['datavalue']['value']
                 for x in item['claims'].get('P154', [])],
    }
    for item in wikidata_items(
        sorted(
            (x['qid']['value'].split('entity/')[1]
             for x in queryResult.json()['results']['bindings']),
            key=lambda x: int(x[1:])
        )
    )
}

designers = {
    item['id']: {
        'id': item['id'],
        'sitelinks': {
            site: link['title']
            for site, link in item['sitelinks'].items()
            if site == 'fawiki' or site == 'enwiki'
        },
        'label': {
            lang: label['value']
            for lang, label in item['labels'].items()
            if lang == 'fa' or lang == 'en'
        },
    }
    for item in wikidata_items(
        {designer
         for item in films
         for poster in item['poster']
         for designer in poster['designer']}
    )
}

print(json.dumps({'films': films, 'designers': designers}, indent=2, ensure_ascii=False))
