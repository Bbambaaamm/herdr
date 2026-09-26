const WORDS = new Uint32Array(256);
let index = WORDS.length;

export function secureRandom() {
  const crypto = globalThis.crypto;
  if (!crypto || typeof crypto.getRandomValues !== 'function') {
    throw new Error('secure_random_unavailable');
  }
  if (index >= WORDS.length) {
    crypto.getRandomValues(WORDS);
    index = 0;
  }
  return WORDS[index++] / 4294967296;
}
