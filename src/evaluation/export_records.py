"""Convert a saved actual facade comparison to agreed metric records."""
import argparse
import json
from pathlib import Path


def export(source,output):
    if output.exists():raise FileExistsError('Metric records already exist')
    s=json.loads(source.read_text());rows=[]
    for trip in s['trips']:
        for name,value in trip['metrics'].items():
            rows.append(dict(run_id=s['run_id'],source_git_sha=s['source_git_sha'],model_name='hist_gradient_boosting',model_family='histogram gradient boosting',variant=s['selected_variant'],decoder=trip['decoder'],partition=s['partition'],fold=None,trip_id=trip['trip_id'],metric=name,value=value,denominator=trip['counts'][name]['denominator'],policy_id='pathsnap-scoring-v0',unavailable_reason='no_eligible_observations' if value is None else None))
    from jsonschema import Draft202012Validator
    schema=json.loads(Path('contracts/artifacts.schema.json').read_text());validator=Draft202012Validator({**schema,'$ref':'#/$defs/ResultRecord'})
    for row in rows:validator.validate(row)
    output.write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in rows))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.source,a.output)
if __name__=='__main__':main()
