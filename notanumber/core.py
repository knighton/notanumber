"""
notanumber - Store bytes in fp16 floats through creative abuse.

Come with me and you'll be in a world of pure imagination.
Take a look and you'll see into your NaN-based computation.

We offer four delightful flavors:
- Signed zeros (1 bit per float)
- Infinities (1 bit per float)
- NaN payloads (9 bits per float)
- Subnormals (10 bits per float)

There is no life I know to compare with pure imagination.
"""

import struct
from typing import Literal


# IEEE 754 fp16 bit patterns
SIGN_BIT = 0x8000
EXPONENT_MASK = 0x7C00
MANTISSA_MASK = 0x03FF
INF_BITS = 0x7C00
NAN_QUIET = 0x7E00
PAYLOAD_MASK = 0x01FF

# Safety limit: 100MB input
MAX_INPUT_SIZE = 100 * 1024 * 1024


def to_zero(data: bytes) -> bytes:
    """Store data in the sign bits of zeros.

    A little nonsense now and then is relished by the wisest men.
    Each bit gets its very own zero to live in.

    Args:
        data (bytes): Your golden ticket.

    Returns:
        bytes: A field of zeros, each one special.

    Raises:
        ValueError: If the data is too large for safety.
    """
    if len(data) > MAX_INPUT_SIZE:
        raise ValueError(f"Data too large: {len(data)} bytes (max {MAX_INPUT_SIZE})")

    ret = bytearray()

    for byte in data:
        for bit_idx in range(8):
            if byte & (1 << bit_idx):
                ret.extend(struct.pack("<H", SIGN_BIT))  # -0.0
            else:
                ret.extend(struct.pack("<H", 0))  # +0.0

    return bytes(ret)


def from_zero(data: bytes) -> bytes:
    """Extract data from the sign bits of zeros.

    The zeros remember. They always remember.

    Args:
        data (bytes): Zeros with secrets.

    Returns:
        bytes: What was scattered is now gathered.

    Raises:
        ValueError: If someone's been nibbling at our chocolate.
    """
    if len(data) % 2 != 0:
        raise ValueError("Odd number of bytes in fp16 array")

    num_values = len(data) // 2
    if num_values % 8 != 0:
        raise ValueError(f"Array length {num_values} not divisible by 8")

    ret = bytearray()

    for i in range(0, num_values, 8):
        byte = 0
        for j in range(8):
            val = struct.unpack("<H", data[(i + j) * 2 : (i + j + 1) * 2])[0]
            if val == SIGN_BIT:
                byte |= 1 << j
            elif val != 0:
                raise ValueError("Impure zeros detected")
        ret.append(byte)

    return bytes(ret)


def to_inf(data: bytes) -> bytes:
    """Store data in the signs of infinities.

    Where the zeros whisper, the infinities sing.

    Args:
        data (bytes): Finite dreams.

    Returns:
        bytes: Infinite possibilities.

    Raises:
        ValueError: If the data is too large for safety.
    """
    if len(data) > MAX_INPUT_SIZE:
        raise ValueError(f"Data too large: {len(data)} bytes (max {MAX_INPUT_SIZE})")

    ret = bytearray()

    for byte in data:
        for bit_idx in range(8):
            if byte & (1 << bit_idx):
                ret.extend(struct.pack("<H", INF_BITS | SIGN_BIT))  # -inf
            else:
                ret.extend(struct.pack("<H", INF_BITS))  # +inf

    return bytes(ret)


def from_inf(data: bytes) -> bytes:
    """Extract data from the signs of infinities.

    Even infinity has its limits.

    Args:
        data (bytes): Endless values with endings.

    Returns:
        bytes: The finite within the infinite.

    Raises:
        ValueError: If the infinities aren't quite infinite enough.
    """
    if len(data) % 2 != 0:
        raise ValueError("Odd number of bytes in fp16 array")

    num_values = len(data) // 2
    if num_values % 8 != 0:
        raise ValueError(f"Array length {num_values} not divisible by 8")

    ret = bytearray()

    for i in range(0, num_values, 8):
        byte = 0
        for j in range(8):
            val = struct.unpack("<H", data[(i + j) * 2 : (i + j + 1) * 2])[0]
            if (val & EXPONENT_MASK) != INF_BITS:
                raise ValueError("Non-infinity found in the infinity room")
            if (val & MANTISSA_MASK) != 0:
                raise ValueError("A NaN snuck into our infinities")
            if val & SIGN_BIT:
                byte |= 1 << j
        ret.append(byte)

    return bytes(ret)


def to_nan(data: bytes) -> bytes:
    """Store data in NaN payloads.

    In the quiet corners where mathematics goes to rest,
    we find room for nine bits of dreams in each NaN.

    Args:
        data (bytes): Rational data seeking irrational refuge.

    Returns:
        bytes: Your data, quietly not being numbers.

    Raises:
        ValueError: If the data is too large for safety.
    """
    if len(data) > MAX_INPUT_SIZE:
        raise ValueError(f"Data too large: {len(data)} bytes (max {MAX_INPUT_SIZE})")

    # Encode the length first (4 bytes, little-endian)
    data_with_length = struct.pack("<I", len(data)) + data

    ret = bytearray()

    # Process all bytes and pack into 9-bit chunks
    for i in range(0, len(data_with_length) * 8, 9):
        # Collect up to 9 bits
        bits = 0
        for j in range(9):
            byte_idx = (i + j) // 8
            bit_idx = (i + j) % 8
            if byte_idx < len(data_with_length):
                if data_with_length[byte_idx] & (1 << bit_idx):
                    bits |= 1 << j

        # Create NaN with payload
        nan_bits = NAN_QUIET | bits
        ret.extend(struct.pack("<H", nan_bits))

    return bytes(ret)


def from_nan(data: bytes) -> bytes:
    """Extract data from NaN payloads.

    Listen carefully. The NaNs are speaking.

    Args:
        data (bytes): Quiet NaNs with loud secrets.

    Returns:
        bytes: What the numbers wouldn't say.

    Raises:
        ValueError: If someone let actual numbers into the NaN room.
    """
    if len(data) % 2 != 0:
        raise ValueError("Odd number of bytes in fp16 array")

    # Extract all 9-bit payloads
    total_bits = (len(data) // 2) * 9
    result = bytearray((total_bits + 7) // 8)

    bit_pos = 0
    for i in range(0, len(data), 2):
        val = struct.unpack("<H", data[i : i + 2])[0]
        if (val & 0x7E00) != 0x7E00:
            raise ValueError("A number is pretending to be NaN")

        payload = val & PAYLOAD_MASK

        # Unpack 9 bits
        for j in range(9):
            if bit_pos < total_bits:
                byte_idx = bit_pos // 8
                bit_idx = bit_pos % 8
                if payload & (1 << j):
                    result[byte_idx] |= 1 << bit_idx
                bit_pos += 1

    # Extract length and trim
    if len(result) >= 4:
        length = struct.unpack("<I", bytes(result[:4]))[0]
        if length == 0:
            return b""
        if 4 + length <= len(result):
            return bytes(result[4 : 4 + length])

    raise ValueError("Corrupted length header in NaN data")


def to_subnormal(data: bytes) -> bytes:
    """Store data in subnormal values.

    Down, down, down we go, to where the very small things live.
    They're quite fragile. Please don't breathe on them.

    Args:
        data (bytes): Data brave enough to venture to the edge.

    Returns:
        bytes: Your data, smaller than it's ever been.

    Warnings:
        These are not for playing with. Look, but don't touch.

    Raises:
        ValueError: If the data is too large for safety.
    """
    if len(data) > MAX_INPUT_SIZE:
        raise ValueError(f"Data too large: {len(data)} bytes (max {MAX_INPUT_SIZE})")

    # Encode the length first
    data_with_length = struct.pack("<I", len(data)) + data

    ret = bytearray()

    # Process all bytes and pack into 10-bit chunks
    # We use all mantissa values 0-1023 (including zero!)
    total_bits = len(data_with_length) * 8
    for i in range(0, total_bits, 10):
        # Collect up to 10 bits
        bits = 0
        for j in range(10):
            if i + j < total_bits:
                byte_idx = (i + j) // 8
                bit_idx = (i + j) % 8
                if data_with_length[byte_idx] & (1 << bit_idx):
                    bits |= 1 << j

        # Store directly - mantissa can be 0-1023
        ret.extend(struct.pack("<H", bits))

    return bytes(ret)


def from_subnormal(data: bytes) -> bytes:
    """Extract data from subnormal values.

    Gently, gently. They startle easily.

    Args:
        data (bytes): Subnormals holding their breath.

    Returns:
        bytes: Your data, if it survived the journey.

    Raises:
        ValueError: If they've already vanished. I warned you.
    """
    if len(data) % 2 != 0:
        raise ValueError("Odd number of bytes in fp16 array")

    # Pre-allocate result based on number of values
    num_values = len(data) // 2
    total_bits = num_values * 10
    result = bytearray((total_bits + 7) // 8)

    bit_pos = 0
    for i in range(0, len(data), 2):
        val = struct.unpack("<H", data[i : i + 2])[0]

        # Check it's a valid subnormal or zero
        if (val & EXPONENT_MASK) != 0:
            raise ValueError("These aren't subnormal at all")
        if (val & SIGN_BIT) != 0:
            raise ValueError("Wrong kind of small")

        # Extract mantissa (0-1023)
        mantissa = val & MANTISSA_MASK

        # Unpack 10 bits
        for j in range(10):
            byte_idx = bit_pos // 8
            bit_idx = bit_pos % 8
            if byte_idx < len(result):
                if mantissa & (1 << j):
                    result[byte_idx] |= 1 << bit_idx
            bit_pos += 1

    # Extract length and trim
    if len(result) >= 4:
        length = struct.unpack("<I", bytes(result[:4]))[0]
        if length == 0:
            return b""
        if 4 + length <= len(result):
            return bytes(result[4 : 4 + length])

    raise ValueError("Corrupted length header in subnormal data")


def encode(
    data: bytes, method: Literal["zero", "inf", "nan", "subnormal"] = "nan"
) -> bytes:
    """Encode data using your chosen flavor of numerical nonsense.

    So much to see, so much to do.
    So what's wrong with taking the NaN route?

    Args:
        data (bytes): Your offering.
        method {'zero', 'inf', *'nan'*, 'subnormal'}: Your chosen door.

    Returns:
        bytes: Your data, transformed.

    Raises:
        ValueError: If you ask for a door that doesn't exist.
    """
    methods = {
        "zero": to_zero,
        "inf": to_inf,
        "nan": to_nan,
        "subnormal": to_subnormal,
    }

    if method not in methods:
        raise ValueError(f"There is no {method} room")

    return methods[method](data)


def decode(
    data: bytes, method: Literal["zero", "inf", "nan", "subnormal", "auto"] = "auto"
) -> bytes:
    """Decode data from its numerical disguise.

    Everything looks different on the way back.

    Args:
        data (bytes): Disguised data.
        method : {'zero', 'inf', 'nan', 'subnormal', *'auto'*}: Which door did
            you use? I'll check if you forgot.

    Returns:
        bytes: Your data, returned to you.

    Raises:
        ValueError: If I can't tell which door you used.
    """
    if method == "auto":
        if len(data) < 2:
            raise ValueError("I need more than crumbs to work with")

        first = struct.unpack("<H", data[:2])[0]

        if first == 0 or first == SIGN_BIT:
            method = "zero"
        elif (first & EXPONENT_MASK) == INF_BITS and (first & MANTISSA_MASK) == 0:
            method = "inf"
        elif (first & 0x7E00) == 0x7E00:
            method = "nan"
        elif (first & EXPONENT_MASK) == 0:
            method = "subnormal"
        else:
            raise ValueError("This doesn't look like anything I've made")

    methods = {
        "zero": from_zero,
        "inf": from_inf,
        "nan": from_nan,
        "subnormal": from_subnormal,
    }

    if method not in methods:
        raise ValueError(f"There is no {method} room")

    return methods[method](data)


def demo() -> None:
    """Come with me and you'll see a demonstration."""
    print("Welcome, welcome.\n")

    message = b"Pure imagination"
    print(f"Today's special: {message}")
    print(f"{len(message)} bytes of possibility\n")

    print("The menu:")
    print(f"{'Flavor':<10} {'Bits':<6} {'Size':<6} {'Growth':<8}")
    print("-" * 30)

    for method in ["zero", "inf", "nan", "subnormal"]:
        encoded = encode(message, method)
        growth = len(encoded) / len(message)
        bits = {"zero": 1, "inf": 1, "nan": 9, "subnormal": 10}[method]

        print(f"{method:<10} {bits:<6} {len(encoded):<6} {growth:>5.1f}x")

        decoded = decode(encoded, method)
        if decoded != message:
            print("ERROR: Round trip failed!")

    print("\n\nThe automatic door finder:")

    for method in ["zero", "inf", "nan", "subnormal"]:
        test = f"{method[:3]}".encode()
        encoded = encode(test, method)
        decoded = decode(encoded, "auto")
        print(f"  {method}: '{decoded.decode()}'")

    print("\n\nA word of caution about the smallest ones:")

    fragile = b"CAREFUL"
    encoded = encode(fragile, "subnormal")

    print("If you're gentle:")
    decoded = decode(encoded, "subnormal")
    print(f"  Success: {decoded}")

    print("\nIf you're not:")
    print("  (Subnormals may vanish during arithmetic)")

    print("\n\nWe are the music makers,")
    print("and we are the dreamers of dreams.")


if __name__ == "__main__":
    demo()
