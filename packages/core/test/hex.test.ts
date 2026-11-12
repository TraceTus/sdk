import { describe, expect, it } from "vitest";
import { HexError, bytesToHex32, compareBytes, hex32ToBytes, isHex32 } from "../src/index.js";

const BYTES_IN_HASH = 32;

describe("hex of 32 bytes", () => {
  it("round-trips bytes to hex and back", () => {
    const bytes = Uint8Array.from({ length: BYTES_IN_HASH }, (_, index) => index * 7);
    const hex = bytesToHex32(bytes);

    expect(isHex32(hex)).toBe(true);
    expect(hex32ToBytes(hex)).toEqual(bytes);
  });

  it("refuses a byte array that is not 32 bytes long", () => {
    expect(() => bytesToHex32(new Uint8Array(3))).toThrow(HexError);
    expect(() => bytesToHex32(new Uint8Array(33))).toThrow(/expected 32 bytes, got 33/);
  });

  it("recognises only 0x plus 64 lowercase hex digits", () => {
    expect(isHex32(`0x${"ab".repeat(BYTES_IN_HASH)}`)).toBe(true);
    expect(isHex32(`0x${"AB".repeat(BYTES_IN_HASH)}`)).toBe(false);
    expect(isHex32(`0x${"ab".repeat(BYTES_IN_HASH - 1)}`)).toBe(false);
    expect(isHex32("ab".repeat(BYTES_IN_HASH))).toBe(false);
  });
});

describe("byte comparison", () => {
  it("orders by the first differing byte", () => {
    const low = new Uint8Array(BYTES_IN_HASH);
    const high = new Uint8Array(BYTES_IN_HASH);

    high[BYTES_IN_HASH - 1] = 1;

    expect(compareBytes(low, high)).toBe(-1);
    expect(compareBytes(high, low)).toBe(1);
  });

  it("returns zero for equal arrays", () => {
    const bytes = Uint8Array.from({ length: BYTES_IN_HASH }, () => 9);

    expect(compareBytes(bytes, Uint8Array.from(bytes))).toBe(0);
  });

  it("treats a missing byte as zero when an array is shorter", () => {
    const short = new Uint8Array(1);
    const full = new Uint8Array(BYTES_IN_HASH);

    expect(compareBytes(short, full)).toBe(0);
    expect(compareBytes(full, short)).toBe(0);
    full[5] = 1;
    expect(compareBytes(short, full)).toBe(-1);
    expect(compareBytes(full, short)).toBe(1);
  });
});
