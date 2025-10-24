from e2b import Sandbox

# Create sandbox from minimal template alias
sandbox = Sandbox.create('vot-guardian-cpu-min')
print('Sandbox ready:', sandbox.id)

# Example: run a quick verification
cmd = (
	"python -c \"import torch, numpy as np; "
	"print('Torch:', torch.__version__); "
	"print('Numpy:', np.__version__)\""
)
res = sandbox.run(cmd)
print('Output:', getattr(res, 'stdout', res))
