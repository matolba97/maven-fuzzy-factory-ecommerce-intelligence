"""Configure the copied PBIP for this clone; run before Desktop refresh."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
folder=root/'Maven Fuzzy Factory'/'data'/'prepared'
value='"'+str(folder).replace('"','""')+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
path=root/'Maven Fuzzy Factory'/'powerbi'/'Maven Fuzzy Factory.SemanticModel'/'definition'/'expressions.tmdl'
text=path.read_text(encoding='utf-8')
import re
text=re.sub(r'(?m)^expression PreparedFolder = .*$',lambda m:'expression PreparedFolder = '+value,text)
path.write_text(text,encoding='utf-8')
bim=root/'Maven Fuzzy Factory'/'qa'/'model.bim'
model=json.loads(bim.read_text(encoding='utf-8'))
model['model']['expressions'][0]['expression']=value
bim.write_text(json.dumps(model,indent=2),encoding='utf-8')
print('PreparedFolder configured for this clone. Open the PBIP and Refresh.')
