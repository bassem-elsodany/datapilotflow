import { testCssSelectors, TestSelectorRequest, TestSelectorResponse } from '@/api/resources/knowledge-source-test';
import { useMutation } from '@tanstack/react-query';

export const useTestCssSelectors = () => {
  return useMutation<TestSelectorResponse, Error, TestSelectorRequest>({
    mutationFn: testCssSelectors,
    onError: (error) => {
      console.error('Failed to test CSS selectors:', error);
    },
  });
};
