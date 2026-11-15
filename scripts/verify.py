"""Run reviewed repository check arrays and validate local documentation links."""
import argparse,json,re,subprocess,sys,time
from pathlib import Path
from urllib.parse import unquote

def doc_links(root):
    issues=[]
    pages=[root/n for n in ['README.md','PRD.md','AGENTS.md','CLAUDE.md'] if (root/n).exists()]+list((root/'docs').glob('**/*.md'))
    for page in pages:
        for target in re.findall(r'\]\(([^)]+)\)',page.read_text(encoding='utf-8')):
            target=target.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target):continue
            if not (page.parent/unquote(target)).exists():issues.append(str(page.relative_to(root))+': '+target)
    return issues

def run(root):
    root=Path(root).resolve();manifest=json.loads((root/'ai-toolkit.json').read_text(encoding='utf-8'))
    failures=doc_links(root);results=[dict(name='documentation-links',status='FAIL' if failures else 'PASS',details=failures)]
    for check in manifest.get('checks',[]):
        cmd=[sys.executable if item=='{python}' else item for item in check['command']]
        if not cmd or not all(isinstance(x,str) for x in cmd):raise ValueError('Commands must be nonempty string arrays')
        start=time.monotonic()
        try:
            p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=check.get('timeout',120))
            results.append(dict(name=check['name'],status='PASS' if p.returncode==0 else 'FAIL',seconds=round(time.monotonic()-start,2),command=cmd,output=p.stdout+p.stderr))
        except (OSError,subprocess.TimeoutExpired) as e:
            results.append(dict(name=check['name'],status='FAIL',details=str(e)))
    report=dict(project=manifest['project'],checks=results,target_acceptance='NOT PERFORMED',note='Local checks do not establish browser, deployed-service or model-quality acceptance.')
    out=root/'.verification';out.mkdir(exist_ok=True);(out/'latest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    for r in results:print(r['status'],r['name'])
    return 1 if any(r['status']=='FAIL' for r in results) else 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.')
    raise SystemExit(run(p.parse_args().root))
