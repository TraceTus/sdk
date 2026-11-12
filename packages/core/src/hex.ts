/** Types and conversions for 32-byte hex, without `as` and without I/O. */

export type Hex32 = `0x${string}`;

const HEX32_PATTERN = /^0x[0-9a-f]{64}$/;
const BYTES_IN_HASH = 32;
const HEX_CHARS_PER_BYTE = 2;
const HEX_PREFIX_LENGTH = 2;
const HEX_RADIX = 16;

export function isHex32(value: string): value is Hex32 {
  return HEX32_PATTERN.test(value);
}

export function bytesToHex32(bytes: Uint8Array): Hex32 {
  if (bytes.length !== BYTES_IN_HASH) {
    throw new HexError("BAD_LENGTH", `expected ${BYTES_IN_HASH} bytes, got ${bytes.length}`);
  }

  let text: Hex32 = "0x";

  for (const byte of bytes) {
    text = `${text}${byte.toString(HEX_RADIX).padStart(HEX_CHARS_PER_BYTE, "0")}`;
  }

  return text;
}

export function hex32ToBytes(hex: Hex32): Uint8Array {
  const bytes = new Uint8Array(BYTES_IN_HASH);

  for (let index = 0; index < BYTES_IN_HASH; index++) {
    const start = HEX_PREFIX_LENGTH + index * HEX_CHARS_PER_BYTE;
    bytes[index] = Number.parseInt(hex.slice(start, start + HEX_CHARS_PER_BYTE), HEX_RADIX);
  }

  return bytes;
}

export function compareBytes(a: Uint8Array, b: Uint8Array): number {
  for (let index = 0; index < BYTES_IN_HASH; index++) {
    const x = a[index] ?? 0;
    const y = b[index] ?? 0;

    if (x !== y) {
      return x < y ? -1 : 1;
    }
  }

  return 0;
}

export class HexError extends Error {
  constructor(
    public readonly code: "BAD_LENGTH",
    message: string,
  ) {
    super(message);
    this.name = "HexError";
  }
}
