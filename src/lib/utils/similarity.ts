/**
 * Calculates the similarity between two strings (0 to 1).
 * 1 = exact match, 0 = no match.
 * Based on the Sørensen–Dice coefficient.
 */
export function compareTwoStrings(first: string, second: string): number {
	const firstStr = first.replace(/\s+/g, '').toLowerCase();
	const secondStr = second.replace(/\s+/g, '').toLowerCase();

	if (firstStr === secondStr) return 1;
	if (firstStr.length < 2 || secondStr.length < 2) return 0;

	const firstBigrams = new Map<string, number>();
	for (let i = 0; i < firstStr.length - 1; i++) {
		const bigram = firstStr.substring(i, i + 2);
		const count = firstBigrams.has(bigram) ? firstBigrams.get(bigram)! + 1 : 1;
		firstBigrams.set(bigram, count);
	}

	let intersectionSize = 0;
	for (let i = 0; i < secondStr.length - 1; i++) {
		const bigram = secondStr.substring(i, i + 2);
		const count = firstBigrams.has(bigram) ? firstBigrams.get(bigram)! : 0;

		if (count > 0) {
			firstBigrams.set(bigram, count - 1);
			intersectionSize++;
		}
	}

	return (2.0 * intersectionSize) / (firstStr.length + secondStr.length - 2);
}
