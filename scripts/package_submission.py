"""Package portable source and submission assets; exclude local QA and hosting identity."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
ROOT=Path(__file__).resolve().parents[1]
target=ROOT.parent/'ATO_Investigator_Submission.zip'
with ZipFile(target,'w',ZIP_DEFLATED) as z:
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file():continue
        relative=p.relative_to(ROOT)
        if any(part in {'.git','.openai','qa','video-assets','__pycache__','node_modules','.venv'} for part in relative.parts):continue
        if p.name=='.DS_Store' or p.suffix in {'.tar','.gz','.zip'}:continue
        z.write(p,'ato-investigator/'+str(relative))
print(target)
