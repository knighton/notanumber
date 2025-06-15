# notanumber

> *Come with me and you'll be in a world of pure imagination*

Store bytes in fp16 floats through creative abuse of IEEE 754.

## Installation

```bash
pip install notanumber
```

## Quick Start

```python
import notanumber as nn

# Encode data into NaN payloads (default)
data = b"Hello, world!"
encoded = nn.encode(data)
decoded = nn.decode(encoded)
assert decoded == data

# Try other flavors
encoded_zero = nn.encode(data, method='zero')     # 1 bit per float
encoded_inf = nn.encode(data, method='inf')       # 1 bit per float  
encoded_nan = nn.encode(data, method='nan')       # 9 bits per float
encoded_sub = nn.encode(data, method='subnormal') # 10 bits per float

# Auto-detect encoding
decoded = nn.decode(encoded_nan, method='auto')
```

## Methods

We offer four delightful flavors:

| Method | Bits/float | Expansion | Safety | Description |
|--------|------------|-----------|---------|-------------|
| `zero` | 1 | 16x | ★★★★★ | Sign bits of ±0.0 |
| `inf` | 1 | 16x | ★★★★★ | Sign bits of ±∞ |
| `nan` | 9 | 1.78x | ★★★★ | Quiet NaN payloads |
| `subnormal` | 10 | 1.6x | ★ | Subnormal mantissas (plus zero) |

## Usage

### Basic Encoding/Decoding

```python
import notanumber as nn

# Your data
message = b"Pure imagination"

# Encode with NaN (recommended)
encoded = nn.encode(message, method='nan')
print(f"Original: {len(message)} bytes")
print(f"Encoded: {len(encoded)} bytes")

# Decode
decoded = nn.decode(encoded, method='nan')
print(decoded)  # b'Pure imagination'
```

### Direct Method Access

For finer control, use the specific encoding functions:

```python
import notanumber as nn

data = b"Secret message"

# Use specific methods directly
encoded = nn.to_nan(data)
decoded = nn.from_nan(encoded)

# Each method has its pair
zero_encoded = nn.to_zero(data)
zero_decoded = nn.from_zero(zero_encoded)

inf_encoded = nn.to_inf(data)
inf_decoded = nn.from_inf(inf_encoded)

sub_encoded = nn.to_subnormal(data)
sub_decoded = nn.from_subnormal(sub_encoded)
```

### Auto-detection

Let the library detect which encoding was used:

```python
# Encode with any method
encoded = nn.encode(b"Secret", method='inf')

# Auto-detect on decode
decoded = nn.decode(encoded, method='auto')
print(decoded)  # b'Secret'
```

### Working with Files

```python
# Read file
with open('document.pdf', 'rb') as f:
    data = f.read()

# Encode to NaN
encoded = nn.encode(data, method='nan')

# Save encoded data
with open('document.nan', 'wb') as f:
    f.write(encoded)

# Later, restore the file
with open('document.nan', 'rb') as f:
    encoded_data = f.read()
    
decoded = nn.decode(encoded_data, method='auto')

with open('restored.pdf', 'wb') as f:
    f.write(decoded)
```

## Important Notes

### Data Integrity

All methods preserve your data exactly, including null bytes. The encoding/decoding process is fully reversible.

### Memory Considerations

Be mindful of memory usage, especially with the `zero` and `inf` methods which expand data 16x:
- 1 MB → 16 MB
- 100 MB → 1.6 GB

Consider using `nan` (1.78x) or `subnormal` (1.6x) for larger files.

### About Subnormals

The `subnormal` method offers the best storage efficiency (10 bits per float), but comes with risks:

```python
# This is safe
encoded = nn.encode(b"SAFE", method='subnormal')
decoded = nn.decode(encoded, method='subnormal')

# This is DANGEROUS - never do arithmetic on encoded values!
import numpy as np
floats = np.frombuffer(encoded, dtype=np.float16)
result = floats * 1.0  # May flush to zero!
```

Subnormal values (and zero) exist at the edge of floating-point representation and may be "flushed to zero" during computation. Only use them for storage, never for arithmetic.

Note: The "subnormal" method actually uses both subnormal values (mantissa 1-1023) and zero (mantissa 0) to achieve full 10-bit encoding.

## API Reference

### High-level Functions

#### `encode(data: bytes, method: Literal['zero', 'inf', 'nan', 'subnormal'] = 'nan') -> bytes`

Encode bytes into fp16 floats.

**Parameters:**
- `data`: Raw bytes to encode
- `method`: Encoding method (default: `'nan'`)

**Returns:**
- `bytes`: Encoded data as fp16 array

**Raises:**
- `ValueError`: If data is too large (>100MB for safety)

#### `decode(data: bytes, method: Literal['zero', 'inf', 'nan', 'subnormal', 'auto'] = 'auto') -> bytes`

Decode bytes from fp16 floats.

**Parameters:**
- `data`: Encoded fp16 array
- `method`: Decoding method (default: `'auto'` for auto-detection)

**Returns:**
- `bytes`: Original data

### Low-level Functions

#### Zero Encoding
- `to_zero(data: bytes) -> bytes`: Encode using sign bits of zeros
- `from_zero(data: bytes) -> bytes`: Decode from sign bits of zeros

#### Infinity Encoding
- `to_inf(data: bytes) -> bytes`: Encode using sign bits of infinities
- `from_inf(data: bytes) -> bytes`: Decode from sign bits of infinities

#### NaN Encoding
- `to_nan(data: bytes) -> bytes`: Encode using NaN payloads
- `from_nan(data: bytes) -> bytes`: Decode from NaN payloads

#### Subnormal Encoding
- `to_subnormal(data: bytes) -> bytes`: Encode using subnormal mantissas (and zero)
- `from_subnormal(data: bytes) -> bytes`: Decode from subnormal mantissas (and zero)

## Development

```bash
# Clone the repository
git clone https://github.com/knighton/notanumber.git
cd notanumber

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black notanumber tests
ruff check notanumber tests

# Type check
mypy notanumber
```

## License

MIT License. See [LICENSE](LICENSE) file.

## Acknowledgments

*We are the music makers, and we are the dreamers of dreams.*
