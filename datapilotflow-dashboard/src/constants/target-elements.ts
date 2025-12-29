/**
 * Default target elements for new configurations
 */
export const DEFAULT_TARGET_ELEMENTS = ['main', 'article'] as const;

/**
 * Creates target elements options dynamically
 * No predefined list - users can add any elements they want
 * @param existingElements - Elements that are already selected
 * @returns Array of target element options (empty array for completely dynamic system)
 */
export const createTargetElementsOptions = (existingElements: string[] = []) => {
  // Return only the elements that are already selected
  // This allows the MultiSelect to work with creatable mode
  return existingElements.map(element => ({
    value: element,
    label: element
  }));
};

/**
 * Validates if an element name is a valid HTML element
 * @param element - The element name to validate
 * @returns boolean indicating if the element is valid
 */
export const isValidHTMLElement = (element: string): boolean => {
  // Basic validation - element should be alphanumeric and start with a letter
  return /^[a-zA-Z][a-zA-Z0-9]*$/.test(element) && element.length > 0;
};
