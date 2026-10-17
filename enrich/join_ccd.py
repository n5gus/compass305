import json,math,re
S=json.load(open('schools.json'))
c23={r['ncessch']:r for r in json.load(open('ccd.json'))['results']}
c21={r['ncessch']:r for r in json.load(open('ccd2021.json'))['results']}
def toks(n): return set(re.findall(r'[a-z]{3,}',n.lower()))-{'school','senior','high','middle','elementary','center','academy','the','and','charter','community'}
def km(a,b,c,d): return 6371*2*math.asin(math.sqrt(math.sin(math.radians(c-a)/2)**2+math.cos(math.radians(a))*math.cos(math.radians(c))*math.sin(math.radians(d-b)/2)**2))
m=0
for s in S:
    if s['type']!='public': continue
    best=None
    for r in c23.values():
        if not r['latitude']: continue
        d=km(s['lat'],s['lon'],r['latitude'],r['longitude'])
        ov=len(toks(s['name'])&toks(r['school_name']))
        if (d<0.3 and ov>=1) or (d<0.08):
            sc=ov-d
            if not best or sc>best[0]: best=(sc,r)
    if not best: continue
    r=best[1]; m+=1; o=c21.get(r['ncessch'],{})
    s['seasch']=r['seasch']; s['charter']=bool(r['charter'])
    s['student_teacher_ratio']=round(r['enrollment']/r['teachers_fte'],1) if r['enrollment'] and r['teachers_fte'] else None
    s['magnet']=bool(o['magnet']) if o.get('magnet') is not None else None
    s['title_i']=o.get('title_i_status') in (1,2,3,4,5) if o.get('title_i_status') is not None else None
print('matched',m,'of',sum(x['type']=='public' for x in S))
json.dump(S,open('schools_ccd.json','w'))
