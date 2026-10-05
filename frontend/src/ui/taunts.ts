/**
 * Mahabharata Ancient Battlefield Taunts & In-Theme Messages
 * At least 25 variants used across errors, rate limits, lockouts, and warnings.
 */

export const MAHABHARATA_TAUNTS = [
  "The formation does not yield to the impatient.",
  "Abhimanyu entered. Abhimanyu did not leave.",
  "Your arrows are spent upon the impenetrable shields of the Kauravas.",
  "Drona watches your hands from the center of the formation.",
  "The seventh circle burns hotter than Gandiva's sacred fire.",
  "The chakras turn only for the disciplined mind.",
  "Karna's chariot wheel sinks deeper into the blood-soaked soil.",
  "Ashwatthama's incantation rejects false utterances.",
  "Dharma bends not to hasty or deceitful strikes.",
  "The conch shell of Panchajanya sounds a grave warning across Kurukshetra.",
  "Bhishma lies upon his bed of arrows, unmoved by your impatience.",
  "You cannot break the Chakravyuha with brute force alone.",
  "Duryodhana smiles as your arrows scatter harmlessly into the dust.",
  "The cosmic order of Dharma watches every keypress.",
  "The celestial archers refuse to aid an undisciplined warrior.",
  "The sound of Gandiva's bowstring mocks your hasty fingers.",
  "You strike too fast; the heavy brass gears of the Chakra refuse to budge.",
  "The sacred seal remains unyielding to mortal curiosity.",
  "A warrior who forgets the ancient alignments is swallowed by the spiral.",
  "Drona's tactical formation tightens around your path.",
  "The sun begins to set upon the fourteenth day; choose your strikes with care.",
  "Sanjaya's divine sight pierces through your attempted shortcuts.",
  "The dust of eighteen akshauhinis blinds those who rush blindly.",
  "Only through profound alignment can the innermost gate be unsealed.",
  "The Chakra steps in rhythm with cosmic law, not your restless fingers.",
  "Dharma rejects the illusion. Offer only that which is true."
];

export function getRandomTaunt(): string {
  const index = Math.floor(Math.random() * MAHABHARATA_TAUNTS.length);
  return MAHABHARATA_TAUNTS[index];
}
