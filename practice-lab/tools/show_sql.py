"""Print the expected result of every SQL exercise so wording and results can be reviewed by eye."""
import sys, os, sqlite3, importlib
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','src'))
import curriculum
only=sys.argv[1] if len(sys.argv)>1 else ''
for m in ['sql_l1','sql_l2','sql_l3','sql_l4','sql_l5']:
    if not os.path.exists(os.path.join(HERE,'content',m+'.py')): continue
    mod=importlib.import_module('content.'+m)
    for c in mod.CONCEPTS:
        for e in c['exercises']:
            if e['type']!='sql' or (only and not e['id'].startswith(only)): continue
            con=sqlite3.connect(':memory:'); con.executescript(curriculum.DATASETS[e['dataset']]['setup'])
            rows=None
            for p in [x.strip() for x in e['solution'].split(';') if x.strip()]:
                cur=con.execute(p)
                if cur.description: rows=cur.fetchall(); cols=[d[0] for d in cur.description]
            if e.get('after'):
                cur=con.execute(e['after']); rows=cur.fetchall(); cols=[d[0] for d in cur.description]
            print(e['id'],'|',e['prompt'][:110]); print('   ',cols, len(rows),'rows', rows[:6])
