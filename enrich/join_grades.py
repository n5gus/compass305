# Adds FL DOE 2026 grades to schools_ccd.json (output of join_ccd.py), matched on the NCES state school number.
# Download SchoolGrades26.xlsx manually from fldoe.org (it blocks scripted downloads).
import pandas as pd, json
g = pd.read_excel('SchoolGrades26.xlsx', header=3, dtype=str)
g = g[g['District Number'] == '13'].set_index('School Number')
S = json.load(open('schools_ccd.json'))
def num(v):
    try: return int(float(v))
    except: return None
for s in S:
    sn = s.get('seasch', '')[-4:] if s.get('seasch') else None
    if sn and sn in g.index:
        r = g.loc[sn]
        if isinstance(r, pd.DataFrame): r = r.iloc[0]
        gr = str(r['Grade 2026']).strip()
        if gr in 'ABCDF' and len(gr) == 1:
            s.update(state_grade=gr, grade_year=2026,
                     reading_pct=num(r['English Language Arts Achievement']),
                     math_pct=num(r['Mathematics Achievement']))
json.dump(S, open('schools.json', 'w'), separators=(',', ':'))
