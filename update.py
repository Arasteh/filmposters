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
    for batch in itertools.batched(sorted(ids, key=lambda x: int(x[1:])), 50):
        yield from requests.post(
            'https://www.wikidata.org/w/api.php',
            {'action': 'wbgetentities',
             'format': 'json',
             'ids': '|'.join(batch)}
        ).json()['entities'].values()
        print('fetched 50 items, sleep for 2s', file=sys.stderr)
        time.sleep(2)
    print('finished', file=sys.stderr)

image_qualifiers = {
    'designers': 'P170',
    'colors': 'P462',
    'characteristics': 'P1552',
}

def image_summary(claim):
    result = {'image': claim['mainsnak']['datavalue']['value']}
    for name, property in image_qualifiers.items():
        qualifier = [
            x['datavalue']['value']['id']
            for x in claim.get('qualifiers', {}).get(property, {})
        ]
        if qualifier: result[name] = qualifier
    return result

films = {
    item['id']: {
        'id': item['id'],
        'sitelinks': {
            site: link['title']
            for site, link in sorted(item['sitelinks'].items())
            if site == 'fawiki' or site == 'enwiki'
        },
        'labels': {
            lang: label['value']
            for lang, label in sorted(item['labels'].items())
            if lang == 'fa' or lang == 'en'
        },
        'aliases': {
            lang: [x['value'] for x in alias]
            for lang, alias in sorted(item['aliases'].items())
            if lang == 'fa' or lang == 'en'
        },
        'directors': [x['mainsnak']['datavalue']['value']['id']
                      for x in item['claims'].get('P57', [])
                      if 'datavalue' in x['mainsnak']],
        'date': [x['mainsnak']['datavalue']['value']['time']
                 for x in item['claims'].get('P577', [])],
        'imdb': [x['mainsnak']['datavalue']['value']
                 for x in item['claims'].get('P345', [])],
        'posters': [image_summary(poster) for poster in item['claims'].get('P3383', [])],
        'logos': [image_summary(logo) for logo in item['claims'].get('P154', [])],
    }
    for item in wikidata_items(
        x['qid']['value'].split('entity/')[1]
        for x in queryResult.json()['results']['bindings']
    )
}

# designers and directors
secondary = {
    item['id']: {
        'id': item['id'],
        'sitelinks': {
            site: link['title']
            for site, link in sorted(item['sitelinks'].items())
            if site == 'fawiki' or site == 'enwiki'
        },
        'labels': {
            lang: label['value']
            for lang, label in sorted(item['labels'].items())
            if lang == 'fa' or lang == 'en'
        },
    }
    for item in wikidata_items(
        {item
         for film in films.values()
         for poster in film['posters'] + film['logos']
         for name, value in poster.items()
         if name in image_qualifiers
         for item in value} |
        {director
         for film in films.values()
         for director in film['directors']}
    )
}

print(json.dumps({'films': films, 'secondary': secondary}, indent=2, ensure_ascii=False))
