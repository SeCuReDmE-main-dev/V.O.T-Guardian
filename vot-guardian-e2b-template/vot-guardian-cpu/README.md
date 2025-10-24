# vot-guardian-cpu - E2B Sandbox Template

This repository contains E2B sandbox templates to run your code in a controlled, pre-baked environment.

Prebuilt template aliases you can use right away:

- vot-guardian-cpu-min — Python 3.10.11 + torch==2.1.0 (CPU) + numpy==1.26.4. Fast to launch and ideal as a stable base.
    - Not included: librosa, MindsDB server, ffmpeg. Install per-sandbox if needed.

## Prerequisites

Before you begin, make sure you have:

- An E2B account (sign up at [e2b.dev](https://e2b.dev))
- Your E2B API key (get it from your [E2B dashboard](https://e2b.dev/dashboard))
- Python installed

## Configuration

1. Create a `.env` file in your project root or set the environment variable:

    ```env
    E2B_API_KEY=your_api_key_here
    ```

## Building the Template

```bash
# For development
make e2b:build:dev

# For production
make e2b:build:prod
```

## Using the Template in a Sandbox

Once your template is built, you can use it in your E2B sandbox:

```python
from e2b import AsyncSandbox
import asyncio

async def main():
    # Create a new sandbox instance
    # Recommended: use the prebuilt minimal template alias
    sandbox = await AsyncSandbox.create('vot-guardian-cpu-min')
    
    # Your sandbox is ready to use!
    print('Sandbox created successfully')

# Run the async function
asyncio.run(main())
```

JavaScript example:

```javascript
import { Sandbox } from 'e2b'

const sandbox = await Sandbox.create('vot-guardian-cpu-min')
```

Using the mid template (librosa + libsndfile1):

```python
from e2b import Sandbox
sandbox = Sandbox.create('vot-guardian-cpu-mid')
```

```javascript
import { Sandbox } from 'e2b'
const sandbox = await Sandbox.create('vot-guardian-cpu-mid')
```

Notes:

- Need librosa? Install it on demand inside the sandbox to keep startup fast.
- Need MindsDB server? Prefer a separate service or a dedicated heavier image; the minimal template focuses on reliability and speed.

## CI/CD and Aliases

- Recommended alias for CI: `vot-guardian-cpu-min`
- For audio-heavy tasks without ffmpeg, set alias to `vot-guardian-cpu-mid`
- Set your API key in CI as secret `E2B_API_KEY`.
- Example (Python) snippet for team scripts:

```python
from e2b import Sandbox

# Create sandbox from minimal template alias
sandbox = Sandbox.create('vot-guardian-cpu-min')
print('Sandbox ready:', sandbox.id)
```

Optionally export the alias as an environment variable to switch templates by context:

```bash
export E2B_TEMPLATE_ALIAS=vot-guardian-cpu-min
```

Then in code:

```python
import os
from e2b import Sandbox

alias = os.getenv('E2B_TEMPLATE_ALIAS', 'vot-guardian-cpu-min')
sandbox = Sandbox.create(alias)
```

## Template Structure

- `template.py` - Defines the sandbox template configuration
- `build_dev.py` - Builds the template for development
- `build_prod.py` - Builds the template for production

## Next Steps

1. Customize the template in `template.py` to fit your needs
2. Build the template using one of the methods above
3. Use the template in your E2B sandbox code (consider `vot-guardian-cpu-min` for fastest startup)
4. Check out the [E2B documentation](https://e2b.dev/docs) for more advanced usage

## Template tiers: minimal vs mid vs full

- Minimal (`vot-guardian-cpu-min`): Python 3.10.11 + torch CPU + numpy. Fastest startup, best for general compute. No audio stack.
- Mid (`vot-guardian-cpu-mid`): Minimal + librosa with libsndfile1 only. Adds audio feature extraction without heavy ffmpeg.
- Full (`vot-guardian-cpu`): Adds curated MindsDB runtime deps and heavier system libs. Use when you need an all-in-one environment and can tolerate longer builds.

Optional dependencies policy: install extras like `librosa` or `ffmpeg` on demand inside sandboxes to keep templates lean and CI fast.
