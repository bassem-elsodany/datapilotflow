/**
 * Text direction detection utilities
 * 
 * Detects whether text should be displayed RTL (Right-to-Left) or LTR (Left-to-Right)
 * based on the predominant script used in the text.
 */

/**
 * Detects if a string contains predominantly RTL (Right-to-Left) characters.
 * 
 * RTL languages include:
 * - Arabic (0600–06FF)
 * - Hebrew (0590–05FF)
 * - Persian/Farsi (0750–077F)
 * - Urdu (uses Arabic script)
 * - Syriac (0700–074F)
 * 
 * @param text - The text to analyze
 * @returns 'rtl' if text is predominantly RTL, 'ltr' otherwise
 */
export function detectTextDirection(text: string): 'rtl' | 'ltr' {
  if (!text || text.trim().length === 0) {
    return 'ltr';
  }

  // RTL Unicode ranges:
  // Arabic: \u0600-\u06FF
  // Arabic Supplement: \u0750-\u077F
  // Arabic Extended-A: \u08A0-\u08FF
  // Hebrew: \u0590-\u05FF
  // Syriac: \u0700-\u074F
  const rtlChars = /[\u0590-\u05FF\u0600-\u06FF\u0700-\u074F\u0750-\u077F\u08A0-\u08FF]/g;

  // Count RTL characters
  const rtlMatches = text.match(rtlChars);
  const rtlCount = rtlMatches ? rtlMatches.length : 0;

  // Count total meaningful characters (excluding spaces, punctuation, numbers)
  const meaningfulChars = text.replace(/[\s\d\p{P}]/gu, '');
  const totalCount = meaningfulChars.length;

  // If more than 30% of meaningful characters are RTL, treat as RTL text
  if (totalCount > 0 && rtlCount / totalCount > 0.3) {
    return 'rtl';
  }

  return 'ltr';
}

/**
 * Gets CSS direction property based on text content
 * 
 * @param text - The text to analyze
 * @returns 'rtl' or 'ltr' CSS direction value
 */
export function getTextDirectionStyle(text: string): React.CSSProperties {
  const direction = detectTextDirection(text);
  return {
    direction,
    textAlign: direction === 'rtl' ? 'right' : 'left',
  };
}

