#!/usr/bin/env python3

import requests
import itertools
import time
import json
import sys
import hashlib

queryResult = requests.post('https://query.wikidata.org/bigdata/namespace/wdq/sparql', '''
SELECT DISTINCT ?qid
WHERE {
  ?qid wdt:P495 wd:Q794. # Iran (Q794) is country of origin (P495)
  ?qid wdt:P3383 ?x.     # Item has a film poster (P3383)
}
''', headers={
  'Content-Type': 'application/sparql-query',
  'Accept': 'application/json',
  'User-Agent': 'UpdateBot/0.0 (https://github.com/Arasteh/filmposters)',
})

def wikidata_items(ids):
    for batch in itertools.batched(sorted(ids, key=lambda x: int(x[1:])), 50):
        yield from requests.post(
            'https://www.wikidata.org/w/api.php',
            {'action': 'wbgetentities',
             'format': 'json',
             'ids': '|'.join(batch)},
            headers = {'User-Agent': 'UpdateBot/0.0 (https://github.com/Arasteh/filmposters)'}
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
    name = claim['mainsnak']['datavalue']['value'].replace(' ', '_')
    hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:2]
    result = {'image': name, 'hash': hash}
    for name, property in image_qualifiers.items():
        qualifier = [
            x['datavalue']['value']['id']
            for x in claim.get('qualifiers', {}).get(property, {})
        ]
        if qualifier: result[name] = qualifier
    return result

with open('ia.tsv') as f: ia = [
    data in (l.split('\t') for l in f.read().strip('\n').split('\n'))
    if data[1].startswith('Q')
]
ia_grouped = itertools.groupby(ia, lambda x: x[1])
ia_designers = {d for a, b, c, d, e in ia if d.startswith('Q')}

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
        **({'ia': ia_grouped[item['id']]} if item['id'] in ia_grouped else {}),
    }
    for item in wikidata_items(
        {
            x['qid']['value'].split('entity/')[1]
            for x in (queryResult.json()['results']['bindings'])
        } | {
            'Q6054055', 'Q6082474', 'Q87193819', 'Q24905261', 'Q131455075',
            'Q88384815',
        } | set(ia_grouped.keys())
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
         for director in film['directors']} |
        ia_designers
    )
}

print(json.dumps({'films': films, 'secondary': secondary}, indent='\t', ensure_ascii=False))
